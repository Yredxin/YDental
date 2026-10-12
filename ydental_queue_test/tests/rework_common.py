from types import SimpleNamespace

from odoo import fields

from .common import key, make_slot


def mixed_fixture(cls):
    """Real S02/S03/S05 mapping, one reporting area, distinct execution subareas."""
    root = cls.root
    store = cls.stores[0]
    floor = cls.stations[0][0].ydental_floor_id
    area = root['ydental.space.area'].create({'name': 'S06A Synthetic mixed reporting',
        'ydental_store_id': store.id, 'ydental_floor_id': floor.id, 'ydental_reporting': True,
        'ydental_purpose': 'care', 'ydental_missed_limit': 2})
    stations, execution_areas, mappings = [], [], []
    for index in (2, 3, 0):
        cap = cls.capabilities[index]
        execution = root['ydental.space.area'].create({'name': cap.name + ' Execution A',
            'ydental_store_id': store.id, 'ydental_floor_id': floor.id, 'parent_id': area.id})
        child = root['ydental.space.area'].create({'name': cap.name + ' lawful descendant',
            'ydental_store_id': store.id, 'ydental_floor_id': floor.id, 'parent_id': execution.id})
        station = root['ydental.space.station'].create({'name': cap.name + ' Mixed Chair A',
            'ydental_store_id': store.id, 'ydental_floor_id': floor.id, 'ydental_area_id': child.id,
            'ydental_kind': 'exam' if index in (2, 3) else 'care',
            'ydental_add_capability_ids': [fields.Command.set(cap.ids)]})
        make_slot(cls, cls.group, station, cls.start, cls.end, total=90)
        mapping = cls.group._operate('mapping', {'catalog_id': cls.catalogs[index].id,
            'area_id': area.id, 'execution_area_id': execution.id}, key())
        stations.append(station)
        execution_areas.append(execution)
        mappings.append(root['ydental.intake.mapping'].browse(mapping['id']))
    wrong_area = root['ydental.space.area'].create({'name': 'S06A Cleaning Execution B',
        'ydental_store_id': store.id, 'ydental_floor_id': floor.id, 'parent_id': area.id})
    wrong = root['ydental.space.station'].create({'name': 'S06A Cleaning Wrong Execution Chair B',
        'ydental_store_id': store.id, 'ydental_floor_id': floor.id, 'ydental_area_id': wrong_area.id,
        'ydental_add_capability_ids': [fields.Command.set(cls.capabilities[0].ids)]})
    cls.group.env['ydental.supply.service']._operate('business', {'area_id': area.id,
        'state': 'open', 'reason': 'S06A synthetic mixed capability validation'}, key())
    return SimpleNamespace(area=area, stations=stations, execution_areas=execution_areas,
                           mappings=mappings, wrong=wrong, wrong_area=wrong_area)
