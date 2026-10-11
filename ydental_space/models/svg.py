import math
import re

from lxml import etree


SVG_NS = 'http://www.w3.org/2000/svg'
TAGS = {'svg', 'g', 'path', 'rect', 'circle', 'ellipse', 'line', 'polyline', 'polygon', 'title', 'desc'}
ATTRIBUTES = {'viewBox', 'width', 'height', 'x', 'y', 'x1', 'x2', 'y1', 'y2', 'cx', 'cy',
              'r', 'rx', 'ry', 'd', 'points', 'fill', 'stroke', 'stroke-width', 'opacity',
              'fill-opacity', 'stroke-opacity', 'fill-rule', 'stroke-linecap', 'stroke-linejoin', 'transform'}


def sanitize_svg(value, limit):
    """Reject dangerous XML and non-whitelisted SVG, rebuild without namespaces.

    No CSS, references, images, entities, links, scripts or active elements survive.
    The byte bound applies before parsing, with additional node/text limits.
    """
    if not isinstance(value, str) or len(value.encode('utf-8')) > limit:
        raise ValueError('size')
    parser = etree.XMLParser(resolve_entities=False, no_network=True, load_dtd=False,
                             huge_tree=False, remove_comments=True, remove_pis=True)
    try:
        root = etree.fromstring(value.encode('utf-8'), parser)
    except (etree.XMLSyntaxError, ValueError) as error:
        raise ValueError('xml') from error
    if root.getroottree().docinfo.doctype:
        raise ValueError('doctype')
    clean = None
    count = 0

    def rebuild(node):
        nonlocal count
        count += 1
        if count > 5000 or not isinstance(node.tag, str):
            raise ValueError('nodes')
        tag = etree.QName(node)
        if tag.namespace not in (None, SVG_NS) or tag.localname not in TAGS:
            raise ValueError('element')
        result = etree.Element('{%s}%s' % (SVG_NS, tag.localname), nsmap={None: SVG_NS} if node is root else None)
        for key, raw in node.attrib.items():
            if key not in ATTRIBUTES or len(raw) > 20000 or any(
                token in raw.lower() for token in ('url', ':', '&', '<', '>', 'expression', 'javascript')
            ):
                raise ValueError('attribute')
            if key in ('fill', 'stroke') and not re.fullmatch(r'#[0-9a-fA-F]{3,8}|[a-zA-Z]+', raw):
                raise ValueError('paint')
            result.set(key, raw)
        if node.text and node.text.strip():
            if tag.localname not in ('title', 'desc') or len(node.text) > 1000:
                raise ValueError('text')
            result.text = node.text
        for child in node:
            result.append(rebuild(child))
        return result

    clean = rebuild(root)
    if etree.QName(clean).localname != 'svg':
        raise ValueError('root')
    try:
        box = [float(part) for part in clean.get('viewBox', '').replace(',', ' ').split()]
        dimensions = [float(clean.get(key, '0')) for key in ('width', 'height')]
    except ValueError as error:
        raise ValueError('dimensions') from error
    if len(box) != 4 or not all(math.isfinite(number) and abs(number) <= 100000 for number in box) or any(
        not math.isfinite(number) or not 0 < number <= 10000 for number in dimensions + box[2:]
    ):
        raise ValueError('dimensions')
    return etree.tostring(clean, encoding='unicode')
