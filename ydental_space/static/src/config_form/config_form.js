import { registry } from "@web/core/registry";
import { RelationalModel } from "@web/model/relational_model/relational_model";
import { Record } from "@web/model/relational_model/record";
import { formView } from "@web/views/form/form_view";

class SpaceRecord extends Record {
    _getChanges(changes, options) {
        const values = super._getChanges(changes, options);
        if (this.resModel.startsWith("ydental.space.") &&
            "ydental_version" in this.fields && Object.keys(values).length) {
            // Send the displayed version even when the readonly field is unchanged.
            // The server checks it under lock; refreshing here would hide conflicts.
            values.ydental_version = this.data.ydental_version;
        }
        return values;
    }
}

class SpaceModel extends RelationalModel {
    static Record = SpaceRecord;
}

registry.category("views").add("ydental_space_form", { ...formView, Model: SpaceModel });
