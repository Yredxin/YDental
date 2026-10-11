import { Component, onWillStart, useRef, useState } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { _t } from "@web/core/l10n/translation";

export class ClinicPlan extends Component {
    static template = "ydental_space.Plan";
    static props = ["*"];

    setup() {
        this.orm = useService("orm");
        this.action = useService("action");
        this.notification = useService("notification");
        this.canvas = useRef("canvas");
        this.state = useState({ floors: [], data: null, selected: null, zoom: 1,
            mode: "select", dirty: {}, polygon: [], drawing: null, busy: false });
        this.drag = null;
        onWillStart(async () => {
            this.state.floors = await this.orm.searchRead("ydental.space.floor", [], ["name"]);
            const floorId = this.props.action.params?.floor_id || this.state.floors[0]?.id;
            if (floorId) {
                await this.load(floorId);
            }
        });
        // Pointer handlers belong to the SVG template; Owl removes them on destroy.
        // There are no global subscriptions, timers or synthetic runtime colors.
    }

    async run(callback) {
        this.state.busy = true;
        try {
            await callback();
        } catch (error) {
            this.notification.add(error.data?.message || error.message, { type: "danger", sticky: true });
        } finally {
            this.state.busy = false;
        }
    }

    async load(floorId) {
        this.state.data = await this.orm.call("ydental.space.floor", "action_snapshot", [[Number(floorId)]]);
        this.state.selected = null;
        this.state.dirty = {};
        this.state.polygon = [];
    }

    async changeFloor(event) {
        if (Object.keys(this.state.dirty).length) {
            this.notification.add(_t("Save or reload the current floor before switching."), { type: "warning" });
            event.target.value = this.state.data.floor.id;
            return;
        }
        await this.run(() => this.load(event.target.value));
    }

    point(event) {
        const canvas = this.canvas.el;
        const point = canvas.createSVGPoint();
        point.x = event.clientX;
        point.y = event.clientY;
        return point.matrixTransform(canvas.getScreenCTM().inverse());
    }

    objects() {
        const data = this.state.data;
        return data ? [...data.areas.map((value) => ({ ...value, kind: "area" })),
            ...data.stations.map((value) => ({ ...value, kind: "station" })),
            ...data.items.map((value) => ({ ...value, kind: "item" }))] : [];
    }

    selected() {
        return this.objects().find((object) => `${object.kind}:${object.id}` === this.state.selected);
    }

    transform(object) {
        return `translate(${object.ydental_x} ${object.ydental_y}) rotate(${object.ydental_angle} ${object.ydental_width / 2} ${object.ydental_height / 2})`;
    }

    points(object) {
        return (object.ydental_points || []).map((point) => point.join(",")).join(" ");
    }

    select(event, object) {
        if (this.state.mode !== "select") {
            return;
        }
        event.stopPropagation();
        this.state.selected = `${object.kind}:${object.id}`;
        if (this.state.data.writable && !this.state.busy) {
            const point = this.point(event);
            this.drag = { object, x: point.x, y: point.y,
                startX: object.ydental_x, startY: object.ydental_y };
            this.canvas.el.setPointerCapture(event.pointerId);
        }
    }

    pointerDown(event) {
        if (!this.state.data.writable || this.state.busy) {
            return;
        }
        const point = this.point(event);
        if (this.state.mode === "rect") {
            this.state.drawing = { x: point.x, y: point.y, width: 1, height: 1 };
            this.canvas.el.setPointerCapture(event.pointerId);
        } else if (this.state.mode === "polygon") {
            this.state.polygon.push([point.x, point.y]);
        } else {
            this.state.selected = null;
        }
    }

    pointerMove(event) {
        const point = this.point(event);
        if (this.drag) {
            this.updateGeometry(this.drag.object, { ydental_x: this.drag.startX + point.x - this.drag.x,
                ydental_y: this.drag.startY + point.y - this.drag.y });
        } else if (this.state.drawing) {
            this.state.drawing.width = point.x - this.state.drawing.x;
            this.state.drawing.height = point.y - this.state.drawing.y;
        }
    }

    async pointerUp() {
        this.drag = null;
        if (this.state.drawing) {
            const drawing = this.state.drawing;
            this.state.drawing = null;
            if (Math.abs(drawing.width) < 10 || Math.abs(drawing.height) < 10) {
                return;
            }
            await this.createArea({ ydental_shape: "rect", ydental_x: Math.min(drawing.x, drawing.x + drawing.width),
                ydental_y: Math.min(drawing.y, drawing.y + drawing.height),
                ydental_width: Math.abs(drawing.width), ydental_height: Math.abs(drawing.height) });
        }
    }

    async finishPolygon() {
        if (this.state.polygon.length < 3) {
            this.notification.add(_t("Select at least three polygon corners."), { type: "warning" });
            return;
        }
        const points = this.state.polygon;
        const x = Math.min(...points.map((point) => point[0]));
        const y = Math.min(...points.map((point) => point[1]));
        await this.createArea({ ydental_shape: "polygon", ydental_x: x, ydental_y: y,
            ydental_width: Math.max(...points.map((point) => point[0])) - x,
            ydental_height: Math.max(...points.map((point) => point[1])) - y,
            ydental_points: points.map((point) => [point[0] - x, point[1] - y]) });
    }

    async createArea(values) {
        await this.run(async () => {
            await this.saveDirty();
            const parent = this.selected();
            await this.orm.create("ydental.space.area", [{ ...this.defaults(), ...values,
                name: _t("New area"), parent_id: parent?.kind === "area" ? parent.id : false }]);
            await this.load(this.state.data.floor.id);
            this.state.mode = "select";
        });
    }

    defaults() {
        return { ydental_floor_id: this.state.data.floor.id,
            ydental_store_id: this.state.data.floor.ydental_store_id[0] };
    }

    updateGeometry(object, values) {
        const list = this.state.data[{ area: "areas", station: "stations", item: "items" }[object.kind]];
        Object.assign(list.find((entry) => entry.id === object.id), values);
        const key = `${object.kind}:${object.id}`;
        this.state.dirty[key] = { kind: object.kind, id: object.id,
            values: { ...this.state.dirty[key]?.values, ...values } };
    }

    changeGeometry(event, field) {
        const value = Number(event.target.value);
        if (Number.isFinite(value)) {
            const selected = this.selected();
            const values = { [field]: value };
            if (selected.ydental_shape === "polygon" && ["ydental_width", "ydental_height"].includes(field)) {
                const axis = field === "ydental_width" ? 0 : 1;
                values.ydental_points = selected.ydental_points.map((point) => point.map((coordinate, index) =>
                    index === axis ? coordinate * value / selected[field] : coordinate));
            }
            this.updateGeometry(selected, values);
        }
    }

    async saveDirty() {
        const changes = Object.values(this.state.dirty);
        if (changes.length) {
            const result = await this.orm.call("ydental.space.floor", "action_save_geometry", [
                [this.state.data.floor.id], this.state.data.floor.ydental_version, changes]);
            this.state.data.floor.ydental_version = result.version;
            this.state.dirty = {};
        }
    }

    async save() {
        await this.run(async () => {
            await this.saveDirty();
            await this.load(this.state.data.floor.id);
            this.notification.add(_t("Floor saved."), { type: "success" });
        });
    }

    dragResource(event, resource) {
        event.dataTransfer.setData("text/plain", String(resource.id));
    }

    async dropResource(event) {
        event.preventDefault();
        if (!this.state.data.writable || this.state.busy) {
            return;
        }
        const resource = this.state.data.resources.find((entry) => entry.id === Number(event.dataTransfer.getData("text/plain")));
        if (!resource) {
            return;
        }
        const point = this.point(event);
        const selected = this.selected();
        const kinds = { chair: "care", imaging: "exam", pharmacy: "pharmacy", settlement: "settlement" };
        if (kinds[resource.ydental_kind] && selected?.kind !== "area" && selected?.kind !== "station") {
            this.notification.add(_t("Select an area or workstation before placing equipment."), { type: "warning" });
            return;
        }
        await this.run(async () => {
            await this.saveDirty();
            let stationId = selected?.kind === "station" ? selected.id : false;
            if (!stationId && kinds[resource.ydental_kind]) {
                [stationId] = await this.orm.create("ydental.space.station", [{ ...this.defaults(),
                    name: resource.name, ydental_area_id: selected.id, ydental_kind: kinds[resource.ydental_kind],
                    ydental_callable: resource.ydental_kind !== "settlement", ydental_x: point.x, ydental_y: point.y,
                    ydental_item_ids: [[0, 0, { ...this.defaults(), name: resource.name,
                        ydental_resource_id: resource.id, ydental_x: point.x, ydental_y: point.y }]] }]);
            } else {
                await this.orm.create("ydental.space.item", [{ ...this.defaults(), name: resource.name,
                    ydental_resource_id: resource.id, ydental_station_id: stationId,
                    ydental_x: point.x, ydental_y: point.y }]);
            }
            await this.load(this.state.data.floor.id);
        });
    }

    async configure() {
        const selected = this.selected();
        if (!selected) {
            return;
        }
        await this.run(async () => {
            await this.saveDirty();
            await this.action.doAction({ type: "ir.actions.act_window", res_model: `ydental.space.${selected.kind}`,
                res_id: selected.id, views: [[false, "form"]], target: "new" },
            { onClose: () => this.run(() => this.load(this.state.data.floor.id)) });
        });
    }

    async newFloor() {
        await this.action.doAction({ type: "ir.actions.act_window", res_model: "ydental.space.floor",
            views: [[false, "form"]], target: "new" }, { onClose: async () => {
            this.state.floors = await this.orm.searchRead("ydental.space.floor", [], ["name"]);
            if (this.state.floors.length) {
                await this.run(() => this.load(this.state.floors.at(-1).id));
            }
        } });
    }
}

registry.category("actions").add("ydental_space.plan", ClinicPlan);
