function startReporting() {
    const form = document.querySelector('.o_ydental_reporting_filters');
    if (!form || form.dataset.ydentalMetricBound === "true") {
        return;
    }
    form.dataset.ydentalMetricBound = "true";
    form.elements.metric.addEventListener('change', () => {
        const query = new URLSearchParams({
            metric: form.elements.metric.value,
            date_from: form.elements.date_from.value,
            date_to: form.elements.date_to.value,
        });
        window.location.assign(`/ydental/reports?${query.toString()}`);
    });
}

if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', startReporting);
} else {
    startReporting();
}
