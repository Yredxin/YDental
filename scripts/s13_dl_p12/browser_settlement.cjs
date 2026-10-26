// Exact original fee values and write controls, with presentation measured separately.
exports.projection = () => {
    const main = document.querySelector('main.o_ydental_settlement');
    const lookup = main.querySelector('[data-dl-scope="settlement-lookup"]');
    const search = lookup.querySelector('[data-dl-region="search"]');
    const form = search.querySelector('form');
    const keys = ['display','fontFamily','fontSize','fontWeight','lineHeight','color',
        'backgroundColor','borderColor','borderWidth','borderRadius','padding',
        'margin','gap','rowGap','columnGap','minWidth','minHeight','overflowX',
        'overflowY','tableLayout','inlineSize','scrollPaddingInline'];
    const styles = e => Object.fromEntries(keys.map(k => [k,getComputedStyle(e)[k]]));
    const text = e => e.textContent.trim();
    const box = e => ({tag:e.tagName,class:e.className,text:text(e),
        rect:e.getBoundingClientRect().toJSON(),style:styles(e)});
    const links = e => [...e.querySelectorAll('a')].map(a => ({text:text(a),href:a.getAttribute('href')}));
    const fields = f => [...f.elements].filter(e => e.name).map(e => ({
        tag:e.tagName,name:e.name,type:e.type,required:e.required,disabled:e.disabled,
        value:['csrf_token','revision','key'].includes(e.name)?'<PRIVATE_NATIVE_BINDING>':e.value,
        maxlength:e.getAttribute('maxlength')}));
    const frozen = [];
    let side = 'prefix';
    for (const child of main.children) {
        if(child===lookup){side='suffix';continue;}
        const clone = child.cloneNode(true);
        const dynamic = [];
        for(const input of clone.querySelectorAll('input')) {
            if(['csrf_token','revision','key'].includes(input.name))input.setAttribute('value','<PRIVATE_NATIVE_BINDING>');
            if(input.name==='actual_utc'){
                dynamic.push({operation:input.closest('form').querySelector('[name="operation"]').value,value:input.value});
                input.setAttribute('value','<NATIVE_ACTUAL_UTC_DEFAULT>');
            }
        }
        frozen.push({side,html:clone.outerHTML,dynamic_actual_utc:dynamic,
            nodes:[child,...child.querySelectorAll('*')].map(e => ({
                tag:e.tagName,class:e.className,text:e.children.length?null:text(e),style:styles(e)}))});
    }
    return {
        query:[...new URL(location.href).searchParams],
        form:{method:form.method,action:form.getAttribute('action'),fields:fields(form),data:[...new FormData(form)]},
        candidates:links(search.querySelector('ul')),candidate_count:search.querySelectorAll('li').length,
        search_pages:links(search.querySelector('nav')),search_page_text:text(search.querySelector('nav')),
        selected:text(lookup.querySelector('[data-dl-region="selected-patient"]')),
        other_stores:links(lookup.querySelector('[data-dl-region="selected-patient"]')),
        fees:[...lookup.querySelectorAll('[data-fee-kind]')].map(s => ({
            kind:s.dataset.feeKind,title:text(s.querySelector('h2')),
            headers:[...s.querySelectorAll('th')].map(e => ({text:text(e),scope:e.getAttribute('scope')})),
            rows:[...s.querySelectorAll('tbody tr')].map(tr => [...tr.cells].map(text)),
            traces:[...s.querySelectorAll('details')].map(d => ({summary:text(d.querySelector('summary')),text:text(d),open:d.open})),
            pages:[...s.querySelectorAll('nav')].map(n => ({text:text(n),links:links(n)})),
            messages:[...s.querySelectorAll(':scope > p')].map(text)})),
        operation_forms:[...main.querySelectorAll('details[name="settlement-operation"] form')].map(f => ({
            action:f.getAttribute('action'),method:f.method,
            fields:fields(f).map(e => e.name==='actual_utc'?{...e,value:'<NATIVE_ACTUAL_UTC_DEFAULT>'}:e)})),
        frozen,
        layout:{viewport:{width:innerWidth,height:innerHeight,dpr:devicePixelRatio,rootFont:getComputedStyle(document.documentElement).fontSize,scrollX,scrollY},
            root:{client:document.documentElement.clientWidth,scroll:document.documentElement.scrollWidth},
            lookup:box(lookup),search:box(search),form:box(form),label:box(form.querySelector('label')),
            input:box(form.querySelector('input')),button:box(form.querySelector('button')),
            search_children:[...search.children].map(box),lookup_children:[...lookup.children].map(box),
            overview:box(lookup.querySelector('[data-dl-region="fee-overview"]')),
            sections:[...lookup.querySelectorAll('[data-fee-kind]')].map(s => ({kind:s.dataset.feeKind,section:box(s),children:[...s.children].map(box)})),
            traces:[...lookup.querySelectorAll('details')].map(d => ({details:box(d),summary:box(d.querySelector('summary')),children:[...d.children].map(box)})),
            controls:[...lookup.querySelectorAll('button,a,summary')].map(box),
            tables:[...lookup.querySelectorAll('.o_ydental_settlement_fee_scroll')].map(s => ({box:box(s),client:s.clientWidth,scroll:s.scrollWidth,table:box(s.querySelector('table')),cells:[...s.querySelectorAll('th,td')].map(box)}))}
    };
};

exports.semantic = value => {
    const x=structuredClone(value);
    delete x.layout;
    for(const part of x.frozen)delete part.dynamic_actual_utc;
    for(const fee of x.fees)for(const trace of fee.traces)delete trace.open;
    return x;
};
