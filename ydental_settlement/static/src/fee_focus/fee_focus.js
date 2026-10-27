import { registry } from "@web/core/registry";
import { Interaction } from "@web/public/interaction";

/** Reveal the original focused trace without taking over table navigation. */
export class SettlementFeeFocus extends Interaction {
    static selector = '.o_ydental_settlement_lookup[data-dl-scope="settlement-lookup"] '
        + '.o_ydental_settlement_fee_scroll';
    static selectorHas = ".o_ydental_settlement_fee_table";

    start() {
        this.view = this.el.ownerDocument.defaultView;
        this.frame = 0;
        this.stopped = false;
        this.registerCleanup(() => this.stop());
        try {
            this.removeFocusIn = this.addListener(this.el, "focusin", (event) => {
                this.queueReveal(event.target);
            });
            this.removeFocusOut = this.addListener(this.el, "focusout", () => {
                this.cancelReveal();
            });
        } catch (error) {
            this.stop();
            console.warn("YDental fee table kept its native focus behavior.", error);
        }
    }

    cancelReveal() {
        this.view?.cancelAnimationFrame(this.frame);
        this.frame = 0;
    }

    stop() {
        this.stopped = true;
        this.cancelReveal();
        this.removeFocusIn?.();
        this.removeFocusOut?.();
        this.removeFocusIn = undefined;
        this.removeFocusOut = undefined;
    }

    queueReveal(target) {
        this.cancelReveal();
        if (this.stopped || !target.matches(
            'summary.o_ydental_settlement_disclosure'
            + '[data-dl-actions="settlement-readonly-actions"]'
        ) || target.closest(".o_ydental_settlement_fee_table")?.parentElement !== this.el) {
            return;
        }
        // Let the native focus transfer and its scrolling finish first.
        this.frame = this.view.requestAnimationFrame(() => {
            this.frame = this.view.requestAnimationFrame(() => {
                this.frame = 0;
                try {
                    this.reveal(target);
                } catch (error) {
                    this.stop();
                    console.warn("YDental fee table kept its native focus behavior.", error);
                }
            });
        });
    }

    reveal(target) {
        if (this.stopped || !this.el.isConnected || !target.isConnected
            || target.ownerDocument.activeElement !== target
            || !this.el.contains(target) || !target.getClientRects().length
            || this.el.scrollWidth <= this.el.clientWidth) {
            return;
        }
        const container = this.el.getBoundingClientRect();
        const box = target.getBoundingClientRect();
        const scale = container.width / this.el.offsetWidth;
        if (!Number.isFinite(scale) || scale <= 0) {
            return;
        }
        const style = this.view.getComputedStyle(target);
        const ring = Math.max(0,
            (parseFloat(style.outlineWidth) || 0)
            + (parseFloat(style.outlineOffset) || 0)
        ) * scale;
        const left = container.left + this.el.clientLeft * scale;
        const right = left + this.el.clientWidth * scale;
        // Oversized controls retain native reading rather than oscillating.
        if (box.width + ring * 2 > right - left) {
            return;
        }
        let delta = 0;
        if (box.left - ring < left) {
            delta = box.left - ring - left;
        } else if (box.right + ring > right) {
            delta = box.right + ring - right;
        }
        if (Math.abs(delta) <= 0.5) {
            return;
        }
        const maximum = this.el.scrollWidth - this.el.clientWidth;
        const next = Math.max(0, Math.min(maximum, this.el.scrollLeft + delta / scale));
        // This is the only write: no focus, DOM, root or vertical scroll change.
        this.el.scrollLeft = next;
    }
}

registry.category("public.interactions").add(
    "ydental_settlement.fee_focus", SettlementFeeFocus
);
