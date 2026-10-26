// Browser projections preserve all original text and hrefs; dynamic UTC is typed.
exports.projection = () => {
    const m = document.querySelector('main.o_ydental_reporting');
    const box = e => {
        const s = getComputedStyle(e);
        return {tag:e.tagName, class:e.className, text:e.textContent.trim(),
            rect:e.getBoundingClientRect().toJSON(), style:Object.fromEntries([
                'marginTop','marginBottom','paddingTop','paddingRight','paddingBottom',
                'paddingLeft','rowGap','columnGap','display','fontSize','lineHeight',
                'color','backgroundColor','borderTopColor','borderTopWidth','overflowX',
                'overflowY','whiteSpace','overflowWrap','minWidth','tableLayout'
            ].map(k => [k,s[k]]))};
    };
    const links = el => [...el.querySelectorAll('a')].map(a => ({
        text:a.textContent.trim(),href:a.getAttribute('href')}));
    const details = el => [...el.querySelectorAll('details')].map(d => ({
        summary:d.querySelector('summary').textContent.trim(),
        text:d.textContent,open:d.open}));
    return {path:location.pathname, query:[...new URL(location.href).searchParams]
        .filter(([k])=>k!=='revision'), title:m.querySelector('h1').textContent,
        scope:[...m.querySelector('.o_ydental_reporting_scope').children]
            .map(e=>e.textContent), links:links(m), details:details(m),
        cards:[...m.querySelectorAll('.o_ydental_reporting_source_card')].map(e=>({
            title:e.querySelector('h2').textContent,
            paragraphs:[...e.querySelectorAll(':scope > p')].map(p=>p.textContent),
            facts:[...e.querySelectorAll('dt,dd')].map(f=>({tag:f.tagName,text:f.textContent})),
            tables:[...e.querySelectorAll('table')].map(t=>({
                headers:[...t.querySelectorAll('th')].map(c=>c.textContent),
                rows:[...t.querySelectorAll('tbody tr')].map(tr=>({
                    cells:[...tr.cells].map(c=>c.textContent),links:links(tr)}))})),
            links:links(e), trace:e.querySelector('pre').textContent})),
        markers:[...m.querySelectorAll('[data-dl-actions]')].map(e=>({
            tag:e.tagName,text:e.textContent.trim(),scope:e.dataset.dlActions})),
        layout:{rootFont:getComputedStyle(document.documentElement).fontSize,
            viewport:{width:innerWidth,height:innerHeight,dpr:devicePixelRatio},
            root:{client:document.documentElement.clientWidth,
                scroll:document.documentElement.scrollWidth},
            main:box(m),modules:[...m.children].map(box),
            cards:[...m.querySelectorAll('.o_ydental_reporting_source_card')].map(e=>({
                card:box(e),children:[...e.children].map(box)})),
            targets:[...m.querySelectorAll('a,summary,dt,dd,th,td,pre')].map(box),
            tables:[...m.querySelectorAll('.o_ydental_reporting_table_wrap')].map(e=>({
                wrapper:box(e),client:e.clientWidth,scroll:e.scrollWidth,
                table:box(e.querySelector('table'))}))}};
};

exports.semantic = value => {
    const copy=structuredClone(value);
    delete copy.layout; delete copy.markers;
    // Third scope paragraph is exactly the native query_at_utc field.
    copy.scope[2]=copy.scope[2].replace(/\d{4}-\d\d-\d\d \d\d:\d\d:\d\d/,'<NATIVE_QUERY_AT_UTC>');
    copy.details.forEach(x=>delete x.open);
    return copy;
};
