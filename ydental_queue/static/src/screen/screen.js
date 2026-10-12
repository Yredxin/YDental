export class QueueScreen {
    constructor(root, token) {
        this.root = root;
        this.token = token;
        this.version = -1;
        this.lastId = 0;
        this.connected = false;
        this.running = false;
    }
    async request(suffix = '') {
        const response = await fetch('/ydental/queue/screen/data' + suffix, {
            headers: {Authorization: 'Bearer ' + this.token}, cache: 'no-store',
        });
        if (!response.ok) {
            this.root.querySelector('tbody').replaceChildren();
            this.root.dataset.denied = 'yes';
            throw new Error('screen_denied');
        }
        return response.json();
    }
    async snapshot() {
        const data = await this.request();
        // An overlapping delayed HTTP response cannot lower the visible version.
        if (data.version < this.version) { return; }
        this.version = data.version;
        this.lastId = data.last_id;
        this.connected = true;
        this.root.dataset.version = String(data.version);
        this.root.dataset.business = data.business;
        this.root.querySelector('[data-day]').textContent = data.business_date;
        this.root.querySelector('[data-business]').textContent = this.root.querySelector('[data-label-' + data.business + ']').textContent;
        const body = this.root.querySelector('tbody');
        body.replaceChildren();
        for (const row of data.rows) {
            const tr = document.createElement('tr');
            for (const value of [row.number, row.name, row.state, row.station]) {
                const td = document.createElement('td'); td.textContent = value; tr.append(td);
            }
            body.append(tr);
        }
        // Voice is opt-in. Initial/reconnect/gap snapshots never replay calls.
        this.rows = data.rows;
    }
    async notice(event) {
        if (!Number.isInteger(event.version) || event.version <= this.version) { return; }
        const contiguous = this.connected && event.version === this.version + 1;
        const previous = new Set((this.rows || []).filter(r => r.state === 'calling').map(r => r.number + '/' + r.station));
        await this.snapshot();
        if (contiguous && this.root.querySelector('[data-voice]').checked && 'speechSynthesis' in window) {
            for (const row of this.rows.filter(r => r.state === 'calling')) {
                if (!previous.has(row.number + '/' + row.station)) {
                    window.speechSynthesis.speak(new SpeechSynthesisUtterance(this.voiceText(row)));
                }
            }
        }
    }
    voiceText(row) { return row.number + ' / ' + row.station; }
    async reconnect() { this.connected = false; await this.snapshot(); }
    async tick() {
        if (this.running) { return; }
        this.running = true;
        try {
            if (!this.connected) { await this.reconnect(); }
            const data = await this.request('?last_id=' + this.lastId);
            this.lastId = data.last_id;
            for (const event of data.events) { await this.notice(event); }
            this.root.querySelector('[data-status]').textContent = '';
        } catch {
            this.connected = false;
            this.root.querySelector('[data-status]').textContent = this.root.querySelector('[data-unavailable]').textContent;
        } finally { this.running = false; }
    }
}
const root = document.querySelector('.o_ydental_queue_screen');
if (root) {
    const fragment = new URLSearchParams(window.location.hash.slice(1));
    const token = fragment.get('token') || sessionStorage.getItem('ydental_screen_token') || '';
    if (token) { sessionStorage.setItem('ydental_screen_token', token); }
    history.replaceState(null, '', window.location.pathname);
    const screen = new QueueScreen(root, token);
    // DOM events exercise the same version/reconnect path as the native bus feed.
    root.addEventListener('ydental:version', e => { screen.notice(e.detail).catch(() => { screen.connected = false; }); });
    root.addEventListener('ydental:reconnect', () => { screen.reconnect().catch(() => { screen.connected = false; }); });
    window.addEventListener('online', () => { screen.connected = false; });
    screen.tick();
    window.setInterval(() => screen.tick(), 2000);
    // Periodic full reconciliation also covers missed notifications / day rollover.
    window.setInterval(() => { screen.connected = false; }, 15000);
}
