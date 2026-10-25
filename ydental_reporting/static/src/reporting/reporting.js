function startReporting() {
    const form = document.querySelector('.o_ydental_reporting_filters');
    if (!form || form.dataset.ydentalMetricBound === "true") {
        return;
    }
    form.dataset.ydentalMetricBound = "true";
    let metricNavigationPending = false;
    let navigationTimeout;
    const restoreNavigation = () => {
        clearTimeout(navigationTimeout);
        metricNavigationPending = false;
    };
    // Tab confirmation may focus another form control before the original GET has departed.
    // Prevent a following Enter from replacing that navigation with form data.
    form.addEventListener('submit', (event) => {
        if (metricNavigationPending) {
            event.preventDefault();
        }
    }, true);
    window.addEventListener('pageshow', restoreNavigation);
    form.addEventListener('reset', restoreNavigation);
    form.elements.metric.addEventListener('change', () => {
        if (metricNavigationPending) {
            return;
        }
        const query = new URLSearchParams({
            metric: form.elements.metric.value,
            date_from: form.elements.date_from.value,
            date_to: form.elements.date_to.value,
        });
        metricNavigationPending = true;
        // Canceled navigation must leave the still-open form usable again.
        navigationTimeout = setTimeout(restoreNavigation, 15000);
        try {
            window.location.assign(`/ydental/reports?${query.toString()}`);
        } catch (error) {
            restoreNavigation();
            throw error;
        }
    });
}

if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', startReporting);
} else {
    startReporting();
}
