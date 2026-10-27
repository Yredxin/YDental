// RWD observations keep ordinary controls separate from strict A04 table focus.
const fs=require('node:fs'), path=require('node:path'), assert=require('node:assert/strict');
const geometry=require('./browser_geometry.cjs');
exports.run=async env=>{
    const {page,context,engine,stage,mode,nojs,sample,base,root,scope,views,r,arg,
        save,shot,sha,settle,open,querySelect,setZoomOn,fixtureReach,check}=env;
    r.rwd_cases=[];r.rwd_findings=[];
    const isBefore=stage==='before',suite=arg('rwd-suite')||'all';
    const configurations=()=>suite==='smoke'?[[320,800,'native200'],[320,800,'root200']]:
        suite==='boundaries'?[[767,900,'normal'],[768,1024,'normal'],[320,800,'normal'],[321,800,'normal']]:
        isBefore?[...views.map(v=>[...v,'normal']),[390,844,'root200'],[1366,768,'native200']]:
        views.flatMap(v=>['normal','native200','root200'].map(k=>[...v,k]));
    async function measure(p,tag,keyboard=true){
        const initial=await p.locator(scope).evaluate(e=>({
            lookup:{box:e.getBoundingClientRect().toJSON(),padding:getComputedStyle(e).padding,
                gap:getComputedStyle(e).gap,font:getComputedStyle(e).fontSize},
            viewport:{width:innerWidth,height:innerHeight,dpr:devicePixelRatio,
                rootFont:getComputedStyle(document.documentElement).fontSize,
                rootClient:document.documentElement.clientWidth,rootScroll:document.documentElement.scrollWidth},
            sections:[...e.querySelectorAll('[data-fee-kind]')].map(s=>({kind:s.dataset.feeKind,
                table:s.querySelector('table')?{tag:s.querySelector('table').tagName,
                    width:s.querySelector('table').getBoundingClientRect().width,
                    headers:[...s.querySelectorAll('th')].map(c=>({text:c.textContent.trim(),scope:c.getAttribute('scope')})),
                    cells:[...s.querySelectorAll('tbody tr')].map(tr=>[...tr.cells].map(c=>c.textContent.trim()))}:null})),
            form:{method:e.querySelector('form').method,action:e.querySelector('form').getAttribute('action'),
                fields:[...e.querySelector('form').elements].map(x=>({name:x.name,type:x.type,maxlength:x.getAttribute('maxlength'),box:x.getBoundingClientRect().toJSON(),fontSize:getComputedStyle(x).fontSize,minBlockSize:getComputedStyle(x).minBlockSize,padding:getComputedStyle(x).padding}))},
            summaries:[...e.querySelectorAll('summary')].map(s=>({tag:s.tagName,role:s.getAttribute('role'),tabindex:s.getAttribute('tabindex'),text:s.textContent.trim()}))
        }));
        const controls=[]; const nodes=await p.locator(scope+' button,'+scope+' a,'+scope+' summary').all();
        for(let i=0;i<nodes.length;i++){
            const target=nodes[i];if(!await target.isVisible())continue;
            // This is a reachability observation; strict A04 has its own untouched precondition.
            await target.evaluate(e=>e.scrollIntoView({block:'center',inline:'nearest'}));
            await p.waitForTimeout(80);const before=await target.evaluate(geometry.observe);
            let focus=null;
            if(keyboard){
                const seed=await target.evaluateHandle(e=>{
                    const all=[...document.querySelectorAll('a[href],button,input,select,textarea,summary,[tabindex]')]
                        .filter(x=>!x.disabled&&x.tabIndex>=0&&x.getClientRects().length&&getComputedStyle(x).visibility!=='hidden');
                    const index=all.indexOf(e);if(index>0)return {node:all[index-1],key:'Tab'};
                    if(index>=0&&index+1<all.length)return {node:all[index+1],key:'Shift+Tab'};
                    throw Error('No native keyboard predecessor');
                });
                const key=await seed.evaluate(s=>s.key);await seed.evaluate(s=>s.node.focus());
                await p.keyboard.press(key);await p.waitForTimeout(300);
                focus=await target.evaluate(geometry.observe);await seed.dispose();
                // No post-Tab scrolling or focus helper precedes this measurement.
            }
            const record={index:i,before,focus,layer:'HELPER_SCROLL_REACHABILITY_THEN_ISOLATED_PREDECESSOR_SEED_NATIVE_KEY'};controls.push(record);
            const issue=[];record.viewportHeightExceeded=before.box.height>before.viewport.height;
            if(!before.boxFit.viewport||!before.boxFit.ancestors)issue.push('CONTROL_BOX_HORIZONTAL_CLIP');
            if(!before.textFit)issue.push('CONTROL_TEXT_HORIZONTAL_CLIP');
            if(parseFloat(before.style.fontSize)<parseFloat(before.viewport.rootFont)-.1)issue.push('CONTROL_TEXT_BELOW_1REM');
            if(before.box.height<parseFloat(before.viewport.rootFont)*2.75-.5)issue.push('CONTROL_HEIGHT_BELOW_2_75REM');
            if(focus&&(!focus.focused||!focus.focusVisible||!focus.focusFit.viewport||!focus.focusFit.ancestors))issue.push('NATIVE_FOCUS_CLIP');
            if(issue.length)r.rwd_findings.push({tag,index:i,text:before.text,tableLocal:before.tableLocal,issue});
            const family=before.tag==='SUMMARY'?'trace':before.tag==='BUTTON'?'search':/other-stores/.test(before.href||'')?'other-store':target&&await target.evaluate(e=>!!e.closest('nav'))?'pager':'candidate';
            r.rwd_focus_shot_families??=[];const key=tag+'-'+family;
            if(focus&&!r.rwd_focus_shot_families.includes(key)){
                await shot(tag+'-'+i+'-'+family+'-isolated-native-focus',p,
                    'EXACT_POST_ISOLATED_NATIVE_KEY_NO_REPAIR_NOT_CONTINUOUS_TAB');
                r.rwd_focus_shot_families.push(key);
            }
            if(focus){
                await p.keyboard.press('Shift+Tab');await p.waitForTimeout(60);
                record.shiftBack=await p.evaluate(()=>({tag:document.activeElement.tagName,
                    text:document.activeElement.textContent.trim(),name:document.activeElement.getAttribute('name')}));
                await p.keyboard.press('Tab');await p.waitForTimeout(180);
                record.returnTab=await target.evaluate(geometry.observe);
                if(!record.returnTab.focused)r.rwd_findings.push({tag,index:i,text:before.text,
                    tableLocal:before.tableLocal,issue:['SHIFTTAB_TAB_ORIGINAL_IDENTITY_FAILED']});
            }
        }
        const text=await p.locator(scope).evaluate(e=>[...e.querySelectorAll('p,li,label,h2,h3,th,td')]
            .filter(x=>x.getClientRects().length).map(x=>({tag:x.tagName,text:x.textContent.trim(),
                font:getComputedStyle(x).fontSize,lineHeight:getComputedStyle(x).lineHeight,
                box:x.getBoundingClientRect().toJSON(),padding:getComputedStyle(x).padding})));
        const v={tag,layer:mode==='rwd-real'?'ACTUAL_AUTHENTICATED_PRODUCT_GET':'LOADED_QWEB_BROWSER_FIXTURE_NORMAL_FRONTEND',
            javascript_enabled:!nojs,initial,controls,text};save(tag+'-geometry.json',v);
        r.rwd_cases.push({tag,layer:v.layer,geometry_file:tag+'-geometry.json',viewport:initial.viewport,
            controls:controls.length,findings:r.rwd_findings.filter(x=>x.tag===tag).length});
        return v;
    }
    async function zoom(p,width,height,kind){
        await p.bringToFront();await setZoomOn(p,1);await p.setViewportSize({width,height});
        await p.evaluate(()=>document.documentElement.style.fontSize='');
        if(kind==='native200')await setZoomOn(p,2);
        if(kind==='root200')await p.evaluate(()=>document.documentElement.style.fontSize='200%');
        await settle(p);const actual=await p.evaluate(()=>({width:innerWidth,height:innerHeight,
            dpr:devicePixelRatio,rootFont:getComputedStyle(document.documentElement).fontSize}));
        const factor=kind==='native200'?2:1;
        assert(Math.abs(actual.width-width/factor)<=1&&Math.abs(actual.height-height/factor)<=1,
            'Actual native effective viewport matches requested mode');
        assert.equal(actual.dpr,factor);assert.equal(actual.rootFont,kind==='root200'?'32px':'16px');
        return actual;
    }
    async function screenshotTop(p,tag){await p.locator(scope).evaluate(e=>e.scrollIntoView({block:'start',inline:'nearest'}));await shot(tag+'-lookup-top',p,mode==='rwd-real'?'ACTUAL_AUTHENTICATED_PRODUCT_GET':'LOADED_QWEB_BROWSER_FIXTURE_NORMAL_FRONTEND');}
    if(mode==='rwd-real'){
        await querySelect();
        const selectedConfigurations=configurations();
        for(const [w,h,k]of selectedConfigurations){
            await zoom(page,w,h,k);const tag='real-'+w+'-'+k;
            await screenshotTop(page,tag);await measure(page,tag,suite!=='boundaries');
        }
        if(nojs){
            // Actual GET query and explicit patient selection, with page JS truly disabled.
            await setZoomOn(page,1);await page.setViewportSize({width:390,height:844});
            await page.evaluate(()=>document.documentElement.style.fontSize='');
            await open(r.selected_href);await measure(page,'real-nojs-query-explicit-selection');
            const summary=page.locator(scope+' summary').first();
            if(await summary.count()){await summary.focus();const b=await summary.evaluate(e=>e.parentElement.open);
                await page.keyboard.press('Enter');assert.equal(await summary.evaluate(e=>e.parentElement.open),!b);
                await page.keyboard.press('Space');assert.equal(await summary.evaluate(e=>e.parentElement.open),b);
                save('real-nojs-native-details.json',{Enter:true,Space:true,hasOdoo:await page.evaluate(()=>!!window.odoo),
                    js_disabled_in_context:true});}
        }
    }else{
        const fixture=JSON.parse(fs.readFileSync(arg('fixture-file')));
        assert.equal(fixture.database_writes,false);assert.equal(fixture.rollback_performed,true);
        const configs=configurations();
        const tasks=fixture.components.filter(x=>x.name==='selected-three-sections').flatMap(item=>configs.map(c=>({item,c})));
        for(const name of (suite==='all'?['long-mixed-values','empty-unselected']:[])){
            const item=fixture.components.find(x=>x.name===name);assert(item);
            for(const c of (isBefore?[[320,800,'normal'],[390,844,'root200']]:[[320,800,'normal'],[390,844,'normal'],[320,800,'root200'],[390,844,'native200']]))tasks.push({item,c});
        }
        for(const {item,c:[w,h,k]}of tasks){
            assert.equal(sha(item.html),item.html_sha256);const p=await context.newPage();let replaced=0;const assets=[];
            p.on('response',x=>{if(['script','stylesheet'].includes(x.request().resourceType()))assets.push(x)});
            await p.route(base+'/ydental/settlement?patient_id='+sample.selected_patient_id,async route=>{
                const response=await route.fetch();assert.equal(response.status(),200);
                const body=await page.evaluate(({html,replacement})=>{const d=new DOMParser().parseFromString(html,'text/html'),old=d.querySelector('[data-dl-scope="settlement-lookup"]'),t=d.createElement('template');t.innerHTML=replacement;
                    if(!old||t.content.children.length!==1)throw Error('Exact one loaded lookup replacement required');old.replaceWith(t.content.firstElementChild);return '<!doctype html>\n'+d.documentElement.outerHTML;},{html:await response.text(),replacement:item.html});
                replaced++;await route.fulfill({response,body});
            });
            await p.setViewportSize({width:w,height:h});await p.bringToFront();
            await p.goto(base+'/ydental/settlement?patient_id='+sample.selected_patient_id,{waitUntil:'load'});
            assert.equal(replaced,1);if(!nojs)await p.waitForFunction(()=>!!window.odoo?.loader?.modules?.get('@ydental_settlement/fee_focus/fee_focus'));
            await zoom(p,w,h,k);const tag='fixture-'+item.name+'-'+w+'-'+k;
            const loaded=[];for(const response of assets){const b=await response.body();loaded.push({path:new URL(response.url()).pathname,
                status:response.status(),bytes:b.length,sha256:sha(b),kind:response.request().resourceType()});}
            save(tag+'-loaded-css-js.json',{loaded,item_html_sha256:item.html_sha256,
                context_js_enabled:!nojs,hasOdoo:await p.evaluate(()=>!!window.odoo),
                feeFocusLoaded:await p.evaluate(()=>!!window.odoo?.loader?.modules?.get('@ydental_settlement/fee_focus/fee_focus'))});
            await screenshotTop(p,tag);await measure(p,tag);
            if(item.name==='long-mixed-values'){
                await p.locator(scope+' details').evaluateAll(xs=>xs.forEach(e=>e.open=true));
                await measure(p,tag+'-expanded',false);
                if(!isBefore){
                    const textSpacingCSS=scope+' *{line-height:1.5!important;letter-spacing:.12em!important;word-spacing:.16em!important}'+scope+' p{margin-bottom:2em!important}';
                    const injected=await p.evaluate(css=>{const style=document.createElement('style');
                        style.dataset.rwdTestOnly='text-spacing';style.textContent=css;document.head.appendChild(style);
                        const first=document.querySelector('[data-dl-scope=\"settlement-lookup\"] button');
                        return {styleConnected:style.isConnected,ruleCount:style.sheet.cssRules.length,
                            letterSpacing:getComputedStyle(first).letterSpacing,lineHeight:getComputedStyle(first).lineHeight};},textSpacingCSS);
                    save(tag+'-textspacing-injection.json',{layer:'TEST_ONLY_SYNCHRONOUS_STYLE_INSTRUMENTATION',contextJSDisabled:nojs,injected});
                    await screenshotTop(p,tag+'-textspacing');await measure(p,tag+'-textspacing');
                    try{await fixtureReach(p,scope+' a,'+scope+' button,'+scope+' summary,'+scope+' td');}
                    catch(error){r.rwd_findings.push({tag:tag+'-textspacing',issue:['TEXT_ENDPOINT_REACH_FAILURE'],message:String(error.message)});}
                }
            }
            // Local table horizontal reachability observes actual end positions; business columns are retained.
            const horizontal=[];for(const area of await p.locator(scope+' .o_ydental_settlement_fee_scroll').all()){
                await area.focus();const initial=await area.evaluate(e=>({left:e.scrollLeft,max:e.scrollWidth-e.clientWidth}));
                await p.keyboard.press('End');for(let i=0;i<80;i++){
                    const s=await area.evaluate(e=>({left:e.scrollLeft,max:e.scrollWidth-e.clientWidth}));if(s.left>=s.max-1)break;
                    await p.keyboard.press('ArrowRight');await p.waitForTimeout(30);
                }
                horizontal.push({initial,final:await area.evaluate(e=>({left:e.scrollLeft,max:e.scrollWidth-e.clientWidth,
                    headers:[...e.querySelectorAll('th')].map(x=>x.textContent.trim()),
                    tableTag:e.querySelector('table').tagName,rootX:scrollX}))});
            }save(tag+'-local-horizontal-read.json',horizontal);
            await p.close();
        }
    }
    check('RWD-matrix-recorded',{cases:r.rwd_cases.length,findings:r.rwd_findings.length,
        ordinary_vs_A04:'Table summary native focus failures remain independently visible; strict36 is separate'});
};
