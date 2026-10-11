import { Component } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { session } from "@web/session";

export class YDentalStoreStatus extends Component {
    static template = "ydental_access.StoreStatus";
    static props = {};

    setup() {
        this.storeName = session.ydental_store_name;
        this.executionStoreId = session.ydental_execution_store_id;
    }
}

registry.category("systray").add("ydental_access.store_status", {
    Component: YDentalStoreStatus,
    isDisplayed: () => session.ydental_store_name !== undefined,
}, { sequence: 20 });
