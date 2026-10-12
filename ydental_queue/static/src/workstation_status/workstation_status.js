import { Component, useProps } from '@odoo/owl';
import { registry } from '@web/core/registry';
import { session } from '@web/session';

export class YDentalWorkstationStatus extends Component {
    static template = 'ydental_queue.WorkstationStatus';
    props = useProps({});

    setup() {
        this.position = session.ydental_workstation;
    }
}

registry.category('systray').add('ydental_queue.workstation', {
    Component: YDentalWorkstationStatus,
    isDisplayed: () => Boolean(session.ydental_workstation),
}, { sequence: 21 });
