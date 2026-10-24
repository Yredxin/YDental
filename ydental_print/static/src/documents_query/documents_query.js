import { normalize } from "@web/core/l10n/utils";
import { reposition } from "@web/core/position/utils";
import { registry } from "@web/core/registry";
import { addLoadingEffect } from "@web/core/utils/ui";
import { Interaction } from "@web/public/interaction";

let nextInstance = 0;

/** Local enhancement: the original select is the only submitted field. */
class DocumentQuerySelect {
    constructor(interaction, select, instance) {
        this.interaction = interaction;
        this.select = select;
        this.document = select.ownerDocument;
        this.instance = instance;
        this.removers = [];
        this.opened = false;
        this.active = -1;
        this.buffer = "";
        this.bufferTime = 0;
        this.composing = false;
        this.busy = false;
        this.description = select.getAttribute("aria-describedby") || "";
        this.originalHidden = select.hidden;
        this.label = select.labels?.[0];
        this.originalFor = this.label?.htmlFor;
    }

    listen(target, event, callback, options) {
        this.removers.push(this.interaction.addListener(target, event, callback, options));
    }

    mount() {
        const id = `${this.instance}-${this.select.name}`;
        this.trigger = this.document.createElement("button");
        this.trigger.type = "button";
        this.trigger.id = `${id}-trigger`;
        this.trigger.className = "o_ydental_print_query_trigger";
        this.trigger.setAttribute("role", "combobox");
        this.trigger.setAttribute("aria-haspopup", "listbox");
        this.trigger.setAttribute("aria-autocomplete", "none");
        this.trigger.setAttribute("aria-expanded", "false");
        this.trigger.setAttribute("aria-controls", `${id}-list`);
        this.trigger.setAttribute("aria-required", String(this.select.required));
        this.trigger.setAttribute("aria-describedby", this.description);
        if (this.label) {
            this.trigger.setAttribute("aria-labelledby", `${this.label.id} ${id}-value`);
        }
        this.valueLabel = this.document.createElement("span");
        this.valueLabel.id = `${id}-value`;
        const chevron = this.document.createElement("span");
        chevron.className = "o_ydental_print_query_chevron";
        chevron.setAttribute("aria-hidden", "true");
        chevron.textContent = "⌄";
        this.trigger.append(this.valueLabel, chevron);

        this.error = this.document.createElement("p");
        this.error.id = `${id}-error`;
        this.error.className = "o_ydental_print_query_error";
        this.error.setAttribute("role", "alert");
        this.error.hidden = true;
        this.error.textContent = this.interaction.el.querySelector(
            "[data-ydental-query-message=required]"
        ).textContent.trim();

        this.boundary = this.document.createElement("div");
        this.boundary.className = "o_ydental_dl_v1 o_ydental_print_query_boundary";
        this.boundary.dataset.dlScope = "documents-query";
        this.boundary.dataset.dlPortal = "boundary";
        this.boundary.dataset.dlInstance = this.instance;
        this.boundary.setAttribute("aria-hidden", "true");
        this.popup = this.document.createElement("div");
        this.popup.className = "o_ydental_dl_v1 o_ydental_print_query_popup";
        this.popup.dataset.dlScope = "documents-query";
        this.popup.dataset.dlPortal = "true";
        this.popup.dataset.dlInstance = this.instance;
        this.popup.hidden = true;
        this.popup.id = `${id}-list`;
        this.popup.setAttribute("role", "listbox");
        if (this.label) {
            this.popup.setAttribute("aria-labelledby", this.label.id);
        }
        this.options = Array.from(this.select.options).map((option, index) => {
            const item = this.document.createElement("div");
            item.id = `${id}-option-${index}`;
            item.className = "o_ydental_print_query_option";
            item.setAttribute("role", "option");
            item.setAttribute("aria-disabled", String(option.disabled));
            const label = this.document.createElement("span");
            label.textContent = option.textContent.trim();
            const marker = this.document.createElement("span");
            marker.className = "o_ydental_print_query_marker";
            marker.setAttribute("aria-hidden", "true");
            marker.textContent = "✓";
            item.append(label, marker);
            this.popup.append(item);
            this.listen(item, "pointerdown", (event) => {
                // Keep virtual focus on the combobox; do not steal outside clicks.
                if (event.pointerType === "mouse") {
                    event.preventDefault();
                }
            });
            this.listen(item, "pointermove", (event) => {
                if (event.pointerType !== "touch" && !option.disabled) {
                    this.setActive(index);
                }
            });
            this.listen(item, "click", () => {
                if (!option.disabled) {
                    this.setActive(index);
                    this.close(true);
                    this.trigger.focus({ preventScroll: true });
                }
            });
            return { item, option, search: normalize(option.textContent.trim()) };
        });

        this.listen(this.trigger, "click", () => {
            if (this.opened) {
                this.close(false);
            } else {
                this.open();
            }
        });
        this.listen(this.trigger, "keydown", (event) => this.onKeydown(event));
        this.listen(this.trigger, "compositionstart", () => { this.composing = true; });
        this.listen(this.trigger, "compositionend", (event) => {
            this.composing = false;
            if (event.data) {
                this.find(event.data);
            }
        });
        this.listen(this.select, "change", () => this.sync());
        this.listen(this.select, "invalid", (event) => {
            event.preventDefault();
            this.close(false);
            this.error.hidden = false;
            this.trigger.setAttribute("aria-invalid", "true");
            this.trigger.setAttribute("aria-describedby", `${this.description} ${this.error.id}`);
            this.trigger.focus();
        });
        this.listen(this.document, "pointerdown", (event) => {
            if (!this.contains(event.target)) {
                this.close(true);
            }
        });
        this.listen(this.document, "focusin", (event) => {
            if (!this.contains(event.target)) {
                this.close(true);
            }
        });
        // Closing on viewport movement preserves the confirmed value and avoids
        // a detached floating panel, including visual viewport / zoom changes.
        this.listen(window, "resize", () => this.close(false));
        this.listen(window, "scroll", (event) => {
            if (!this.popup.contains(event.target)) {
                this.close(false);
            }
        }, true);
        if (window.visualViewport) {
            this.listen(window.visualViewport, "resize", () => this.close(false));
            this.listen(window.visualViewport, "scroll", () => this.close(false));
        }
        if (this.select.form) {
            this.listen(this.select.form, "reset", () => {
                this.close(false);
                this.interaction.waitForTimeout(() => this.sync(), 0);
            });
        }
        this.sync();
        this.observer = new MutationObserver(() => this.sync());
        this.observer.observe(this.select, { attributes: true, attributeFilter: ["disabled"] });
        this.select.after(this.trigger, this.error);
        this.document.body.append(this.boundary, this.popup);
        if (this.label) {
            this.label.htmlFor = this.trigger.id;
        }
        // Only hide the native interaction after every enhancement is ready.
        this.select.hidden = true;
    }

    contains(target) {
        return this.trigger.contains(target) || this.popup.contains(target);
    }

    setBusy(busy) {
        this.busy = busy;
        this.sync();
    }

    sync() {
        this.trigger.disabled = this.select.disabled || this.busy;
        this.trigger.setAttribute("aria-disabled", String(this.trigger.disabled));
        if (this.trigger.disabled) {
            this.close(false);
        }
        const selected = this.select.selectedIndex;
        this.valueLabel.textContent = this.select.selectedOptions[0]?.textContent.trim() || "";
        this.options.forEach(({ item }, index) => {
            item.setAttribute("aria-selected", String(index === selected));
        });
        if (this.select.validity.valid) {
            this.error.hidden = true;
            this.trigger.removeAttribute("aria-invalid");
            this.trigger.setAttribute("aria-describedby", this.description);
        }
    }

    open() {
        if (this.select.disabled || this.busy || this.opened) {
            return;
        }
        this.opened = true;
        this.popup.hidden = false;
        this.trigger.setAttribute("aria-expanded", "true");
        this.popup.style.maxHeight = "20rem";
        const gutter = parseFloat(getComputedStyle(this.trigger).fontSize) * 0.75;
        this.popup.style.width = `${Math.max(0, Math.min(
            this.trigger.getBoundingClientRect().width,
            this.document.documentElement.clientWidth - gutter * 2
        ))}px`;
        const solution = reposition(this.popup, this.trigger, {
            position: "bottom-start", container: this.boundary,
            margin: gutter / 2, flip: true, shrink: true,
        });
        this.popup.dataset.placement = solution.direction;
        this.setActive(this.select.selectedIndex);
    }

    setActive(index) {
        if (index < 0 || !this.options[index] || this.options[index].option.disabled) {
            return;
        }
        this.active = index;
        this.options.forEach(({ item }, optionIndex) => {
            item.classList.toggle("o_ydental_print_query_active", optionIndex === index);
        });
        const item = this.options[index].item;
        this.trigger.setAttribute("aria-activedescendant", item.id);
        // Scroll the popup only, never the document or another page container.
        const bounds = this.popup.getBoundingClientRect();
        const row = item.getBoundingClientRect();
        if (row.bottom > bounds.bottom) {
            this.popup.scrollTop += row.bottom - bounds.bottom;
        } else if (row.top < bounds.top) {
            this.popup.scrollTop -= bounds.top - row.top;
        }
    }

    close(commit) {
        if (!this.opened) {
            return;
        }
        const previous = this.select.value;
        if (commit && this.active >= 0) {
            this.select.selectedIndex = this.active;
        }
        this.opened = false;
        this.popup.hidden = true;
        this.trigger.setAttribute("aria-expanded", "false");
        this.trigger.removeAttribute("aria-activedescendant");
        this.options.forEach(({ item }) => item.classList.remove("o_ydental_print_query_active"));
        this.buffer = "";
        this.sync();
        if (this.select.value !== previous) {
            this.select.dispatchEvent(new Event("input", { bubbles: true }));
            this.select.dispatchEvent(new Event("change", { bubbles: true }));
        }
    }

    find(text) {
        if (!this.opened) {
            this.open();
        }
        const now = Date.now();
        const fragment = normalize(text);
        this.buffer = now - this.bufferTime < 800 ? this.buffer + fragment : fragment;
        this.bufferTime = now;
        const repeated = [...this.buffer].every((letter) => letter === this.buffer[0]);
        const query = repeated ? this.buffer[0] : this.buffer;
        const start = repeated ? this.active + 1 : 0;
        const indices = this.options.map((_, index) => (start + index) % this.options.length);
        const match = indices.find((index) => !this.options[index].option.disabled &&
            this.options[index].search.includes(query));
        if (match !== undefined) {
            this.setActive(match);
        }
    }

    onKeydown(event) {
        if (event.isComposing || this.composing || event.keyCode === 229) {
            if (event.key === "Enter") {
                event.preventDefault();
            }
            return;
        }
        if (event.key === "Tab") {
            this.close(true);
            return; // Native Tab and Shift+Tab must leave naturally.
        }
        if (event.key === "Escape" && this.opened) {
            event.preventDefault();
            event.stopPropagation();
            this.close(false);
            return;
        }
        const keys = ["ArrowDown", "ArrowUp", "Home", "End", "Enter", " "];
        if (keys.includes(event.key)) {
            event.preventDefault();
            if (!this.opened) {
                this.open();
                if (event.key === "Home" || event.key === "End") {
                    this.move(event.key === "Home" ? "first" : "last");
                }
            } else if (["Enter", " "].includes(event.key)) {
                this.close(true);
            } else {
                this.move({ ArrowDown: "next", ArrowUp: "previous", Home: "first", End: "last" }[event.key]);
            }
            return;
        }
        if (event.key.length === 1 && !event.ctrlKey && !event.metaKey && !event.altKey) {
            event.preventDefault();
            this.find(event.key);
        }
    }

    move(direction) {
        const enabled = this.options.map((row, index) => row.option.disabled ? -1 : index)
            .filter((index) => index >= 0);
        const current = enabled.indexOf(this.active);
        const next = direction === "first" ? 0 : direction === "last" ? enabled.length - 1 :
            Math.max(0, Math.min(enabled.length - 1, current + (direction === "next" ? 1 : -1)));
        this.setActive(enabled[next]);
    }

    destroy() {
        this.removers.forEach((remove) => remove());
        this.popup?.remove();
        this.boundary?.remove();
        this.observer?.disconnect();
        this.trigger?.remove();
        this.error?.remove();
        this.select.hidden = this.originalHidden;
        if (this.label) {
            this.label.htmlFor = this.originalFor;
        }
    }
}

export class DocumentsQuery extends Interaction {
    static selector = '.o_ydental_dl_v1[data-dl-scope="documents-query"]:not([data-dl-portal])';

    start() {
        const instance = `ydental-documents-query-${++nextInstance}`;
        this.el.dataset.dlInstance = instance;
        const search = this.el.querySelector('input[name="q"]');
        let composing = false;
        this.addListener(search, "compositionstart", () => { composing = true; });
        this.addListener(search, "compositionend", () => { composing = false; });
        this.addListener(search, "keydown", (event) => {
            if (event.key === "Enter" && (composing || event.isComposing || event.keyCode === 229)) {
                event.preventDefault();
            }
        });
        const widgets = [];
        for (const select of this.el.querySelectorAll("select[data-ydental-query-select]")) {
            const widget = new DocumentQuerySelect(this, select, instance);
            try {
                widget.mount();
                widgets.push(widget);
                this.registerCleanup(() => widget.destroy());
            } catch (error) {
                // A partially mounted enhancement must not strand a hidden field.
                widget.destroy();
                console.warn("YDental document selector kept its native fallback.", error);
            }
        }
        for (const form of this.el.querySelectorAll("form[data-ydental-query-form]")) {
            this.prepareSubmission(form, widgets);
        }
    }

    prepareSubmission(form, widgets) {
        const button = form.querySelector('button[type="submit"]');
        const originallyDisabled = button.disabled;
        const status = this.el.querySelector(
            `[data-ydental-query-busy="${form.dataset.ydentalQueryForm}"]`
        );
        let removeLoading;
        const restore = () => {
            if (removeLoading) {
                removeLoading();
                removeLoading = undefined;
            }
            button.disabled = originallyDisabled;
            form.removeAttribute("aria-busy");
            status.hidden = true;
            for (const widget of widgets.filter((item) => item.select.form === form)) {
                widget.setBusy(false);
            }
        };
        this.addListener(form, "submit", (event) => {
            if (form.getAttribute("aria-busy") === "true" || originallyDisabled) {
                event.preventDefault();
                return;
            }
            if (event.defaultPrevented) {
                return;
            }
            // Native constraint validation precedes the submit event. Only the
            // unnamed button is disabled; every real request field stays enabled.
            form.setAttribute("aria-busy", "true");
            status.hidden = false;
            removeLoading = addLoadingEffect(button);
            for (const widget of widgets.filter((item) => item.select.form === form)) {
                widget.close(false);
                widget.setBusy(true);
            }
            // Respect a later normal submit listener which cancels navigation.
            queueMicrotask(() => {
                if (event.defaultPrevented) {
                    restore();
                }
            });
        });
        this.addListener(window, "pageshow", restore);
        this.addListener(form, "reset", restore);
        this.registerCleanup(restore);
    }
}

registry.category("public.interactions").add("ydental_print.documents_query", DocumentsQuery);
