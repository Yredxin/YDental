// Original first bill panel only. FormData stays local; no bill activation.
const fs=require('node:fs'),path=require('node:path'),assert=require('node:assert/strict');
const geometry=require('./browser_geometry.cjs');
const panelSelector='details[name="settlement-operation"]:has(form input[name="operation"][value="bill"])';
const secretNames=['csrf_token','revision','key'];
exports.panelSelector=panelSelector;
exports.formContract=form=>{
    const secret=new Set(['csrf_token','revision','key']),button=form.querySelector('button[type="submit"]');
    if(!button||button.form!==form)throw Error('Original named-form submitter missing');
    const values=[];
    for(const e of form.elements){
        if(!e.name||e.disabled)continue;
        if(['button','reset','submit','image'].includes(e.type)&&e!==button)continue;
        if(['checkbox','radio'].includes(e.type)&&!e.checked)continue;
        values.push([e.name,e.value]);
    }
    const actual=[...new FormData(form,button)];
    if(actual.length!==values.length||actual.some((v,i)=>v[0]!==values[i][0]||v[1]!==values[i][1]))
        throw Error('Native FormData differs from successful original DOM controls');
    const fields=[...form.elements].filter(e=>e.name).map(e=>({tag:e.tagName,name:e.name,type:e.type,
        value:secret.has(e.name)?'<PRIVATE_NATIVE_VALUE_NOT_RECORDED>':e.value,
        checked:e.type==='checkbox'?e.checked:undefined,disabled:e.disabled,required:e.required,
        min:e.getAttribute('min'),step:e.getAttribute('step'),maxlength:e.getAttribute('maxlength'),
        formOwnerPreserved:e.form===form,formOrder:[...form.elements].indexOf(e)}));
    const hiddenOrder=fields.filter(x=>x.type==='hidden').map(x=>x.name);
    if(JSON.stringify(hiddenOrder)!==JSON.stringify(['csrf_token','revision','key','output','operation']))
        throw Error('Original token and operation order changed');
    return {method:form.method,action:form.getAttribute('action'),fields,
        serialized:actual.map(([name,value])=>({name,value:secret.has(name)?'<PRIVATE_NATIVE_VALUE_NOT_RECORDED>':value})),
        native_dom_values_exact:true,native_secret_values_equal_in_memory_only:true,
        secret_values_or_per_field_digests_recorded:false,submission_performed:false,
        submitter:{tag:button.tagName,type:button.type,name:button.getAttribute('name'),
            text:button.textContent.trim(),disabled:button.disabled,formOwnerPreserved:button.form===form}};
};
exports.run=async env=>{
    const {page,context,root,base,engine,stage,mode,nojs,alias,sample,views,arg,r,save,shot,zoom,settle,sha}=env;
    const before=stage==='before';
    const panel=p=>p.locator(panelSelector);
    async function openURL(p,url){const response=await p.goto(base+url,{waitUntil:'load'});await settle(p);return response;}
    async function contract(p,tag){
        const f=panel(p).locator('form').filter({has:p.locator('input[name=operation][value=bill]')}),value=await f.evaluate(exports.formContract);
        assert.equal(value.method,'post');assert.equal(value.action,'/ydental/settlement/action');
        assert.equal(value.fields.find(x=>x.name==='operation').value,'bill');
        assert.equal(value.fields.find(x=>x.name==='output').value,'html');
        const discount=value.fields.find(x=>x.name==='discount'),reason=value.fields.find(x=>x.name==='reason');
        assert(discount&&reason);assert.equal(discount.type,'number');assert.equal(discount.min,'0');assert.equal(discount.step,'0.01');assert.equal(reason.maxlength,'300');
        assert(value.fields.filter(x=>x.name==='fee_ids').every(x=>x.type==='checkbox'));
        assert(!value.submitter.disabled&&value.submitter.formOwnerPreserved);
        value.cancel=await panel(p).locator('a').evaluate(e=>({href:e.getAttribute('href'),formAncestor:!!e.closest('form'),text:e.textContent.trim()}));
        assert(!value.cancel.formAncestor);
        if(!before&&arg('before-result')&&mode!=='components'){
            const oldFile=path.join(path.dirname(arg('before-result')),tag+'-native-form-contract.json');
            if(fs.existsSync(oldFile)){
                const old=JSON.parse(fs.readFileSync(oldFile));
                // Cross-request comparison includes only already-redacted tokens.
                // Actual nonce equality is asserted solely inside each current DOM.
                for(const key of ['method','action','fields','serialized','submitter','cancel'])
                    assert.deepEqual(JSON.parse(JSON.stringify(value[key])),old[key],'Original redacted contract field '+key);
                value.before_redacted_contract_exact=true;
                value.cross_request_native_secret_equality_claimed=false;
            }
        }
        save(tag+'-native-form-contract.json',value);return value;
    }
    async function fieldsInteract(p,tag){
        const f=panel(p).locator('form').filter({has:p.locator('input[name=operation][value=bill]')});await contract(p,tag+'-default');
        assert(await f.locator('[name=fee_ids]').evaluateAll(xs=>xs.every(x=>!x.checked)),'Original default fees unchecked');
        const first=f.locator('input[type=checkbox][name=fee_ids]').first();
        if(await first.count()){
            await first.focus();await p.keyboard.press('Space');assert(await first.isChecked());
            await f.locator('[name=discount]').fill('1.23');await f.locator('[name=reason]').fill('P13只读表单序列化测试，不提交');
            const selected=await contract(p,tag+'-selected');assert.equal(selected.serialized.filter(x=>x.name==='fee_ids').length,1);if(!before)await shot(tag+'-native-checkbox-selected-no-submit',p);
            await first.focus();await p.keyboard.press('Space');assert(!await first.isChecked());
            await f.locator('[name=discount]').fill('0');await f.locator('[name=reason]').fill('');
            await contract(p,tag+'-restored');
            if(!before){
                const label=await first.evaluateHandle(e=>e.labels[0]);await label.evaluate(e=>e.scrollIntoView({block:'center',inline:'nearest'}));
                const b=await label.evaluate(e=>e.getBoundingClientRect().toJSON());assert(b.width>0&&b.height>0);await p.mouse.click(b.x+b.width/2,b.y+b.height/2);assert(await first.isChecked(),'Original associated-label native activation');
                await p.mouse.click(b.x+b.width/2,b.y+b.height/2);assert(!await first.isChecked());await label.dispose();
                save(tag+'-native-label-click.json',{checkbox_original_label_association:true,whole_label_native_click_toggled_and_restored:true,bill_submit_activated:false});
            }
        }
    }
    async function segment(p,e,tag){
        return await e.evaluate(el=>{
            const originalActive=document.activeElement;
            const walk=document.createTreeWalker(el,NodeFilter.SHOW_TEXT),nodes=[];
            for(let n=walk.nextNode();n;n=walk.nextNode())if(n.textContent.trim())nodes.push(n);
            const ends=[];
            for(const [kind,n]of [['first',nodes[0]],['last',nodes.at(-1)]]){
                el.scrollIntoView({block:kind==='first'?'start':'end',inline:'nearest'});
                let index=kind==='first'?0:n?.length-1;
                if(n){while(/\s/u.test(n.textContent[index]))index+=kind==='first'?1:-1;
                    const range=document.createRange();range.setStart(n,index);range.setEnd(n,index+1);
                    const b=range.getBoundingClientRect();if(b.top<0||b.bottom>innerHeight)window.scrollBy({top:(b.top+b.bottom-innerHeight)/2,behavior:'instant'});
                    const box=range.getBoundingClientRect(),clippers=[];
                    for(let p=n.parentElement;p;p=p.parentElement){const c=getComputedStyle(p),b=p.getBoundingClientRect();
                        if(['auto','scroll','hidden','clip'].includes(c.overflowX)||['auto','scroll','hidden','clip'].includes(c.overflowY))
                            clippers.push({tag:p.tagName,class:p.className,x:c.overflowX,y:c.overflowY,left:b.left+p.clientLeft,right:b.left+p.clientLeft+p.clientWidth,top:b.top+p.clientTop,bottom:b.top+p.clientTop+p.clientHeight});}
                    const ancestorFit=clippers.every(c=>(!['auto','scroll','hidden','clip'].includes(c.x)||box.left>=c.left-1&&box.right<=c.right+1)&&(!['auto','scroll','hidden','clip'].includes(c.y)||box.top>=c.top-1&&box.bottom<=c.bottom+1));
                    ends.push({kind,char:n.textContent[index],box:box.toJSON(),visible:box.left>=-1&&box.right<=innerWidth+1&&box.top>=-1&&box.bottom<=innerHeight+1,ancestorFit,clippers,originalActivePreserved:document.activeElement===originalActive});}
            }
            return {ends,rootX:scrollX,elementHeight:el.getBoundingClientRect().height,viewportHeight:innerHeight,
                layer:'ORDINARY_SEGMENTED_TEXT_READ_ALLOWED_ONLY_IN_P13_NOT_STRICT_P12',activeOwner:el===document.activeElement,originalActivePreserved:document.activeElement===originalActive,originalActive:{tag:originalActive?.tagName,name:originalActive?.getAttribute('name')}};
        });
    }
    async function observe(p,tag,continuous=true){
        const target=panel(p),summary=target.locator(':scope > summary');
        await summary.evaluate(e=>e.scrollIntoView({block:'start',inline:'nearest'}));
        const closedBefore=await target.evaluate(e=>({open:e.open,box:e.getBoundingClientRect().toJSON(),summaryBox:e.querySelector('summary').getBoundingClientRect().toJSON(),padding:getComputedStyle(e).padding}));
        await summary.focus();if(await target.evaluate(e=>e.open))await p.keyboard.press('Enter');
        assert(!await target.evaluate(e=>e.open));await shot(tag+'-closed',p);
        await p.keyboard.press('Enter');assert(await target.evaluate(e=>e.open));
        await p.keyboard.press('Space');assert(!await target.evaluate(e=>e.open));
        await p.keyboard.press('Enter');assert(await target.evaluate(e=>e.open));
        await settle(p);await shot(tag+'-open',p);
        const initial=await target.evaluate(e=>({open:e.open,class:e.className,scope:e.dataset.dlScope,
            box:e.getBoundingClientRect().toJSON(),padding:getComputedStyle(e).padding,gap:getComputedStyle(e).gap,
            viewport:{width:innerWidth,height:innerHeight,dpr:devicePixelRatio,rootFont:getComputedStyle(document.documentElement).fontSize,rootClient:document.documentElement.clientWidth,rootScroll:document.documentElement.scrollWidth},
            labels:[...e.querySelectorAll('label')].map(x=>({text:x.textContent.trim(),box:x.getBoundingClientRect().toJSON(),padding:getComputedStyle(x).padding,gap:getComputedStyle(x).gap,minBlockSize:getComputedStyle(x).minBlockSize,fontSize:getComputedStyle(x).fontSize})),
            form:{box:e.querySelector('form').getBoundingClientRect().toJSON(),gap:getComputedStyle(e.querySelector('form')).gap},
            cssLoaded:[...document.querySelectorAll('link[rel=stylesheet]')].map(x=>({path:new URL(x.href).pathname,loaded:!!x.sheet}))}));
        const controls=await target.locator('summary,input:not([type=hidden]),button,a').all(),records=[],familyShots=new Set();
        for(let i=0;i<controls.length;i++){
            const e=controls[i];if(!await e.isVisible())continue;
            if(i===0)await summary.focus();else if(continuous)await p.keyboard.press('Tab');
            else await e.focus();
            await p.waitForTimeout(180);const native=await e.evaluate(geometry.observe);assert(native.focused,'Original native Tab order '+i);
            const record={index:i,native,continuous_native_Tab:continuous&&i>0,entry:i===0?'INITIAL_ORIGINAL_SUMMARY_PROGRAMMATIC_SEED_THEN_NATIVE_ENTER_SPACE':continuous?'CONTINUOUS_ENGINE_NATIVE_TAB':'EXPLICIT_ORIGINAL_FOCUS_SEED'};
            const clickOwner=native.name==='fee_ids'?native.associatedLabel:null;
            if(clickOwner){
                const handle=await e.evaluateHandle(x=>x.labels[0]);record.checkboxLabel=await handle.evaluate(geometry.observe);await handle.dispose();
                if(!record.checkboxLabel.boxFit.viewport||!record.checkboxLabel.boxFit.ancestors||!record.checkboxLabel.textFit)
                    r.findings.push({tag,index:i,type:'LABEL_HORIZONTAL_BOX_OR_TEXT_CLIP',labelGeometry:record.checkboxLabel});
                if(!before&&parseFloat(record.checkboxLabel.style.fontSize)<parseFloat(native.viewport.rootFont)-.1)
                    r.findings.push({tag,index:i,type:'LABEL_TEXT_BELOW_1REM'});
            }
            const targetHeight=clickOwner?clickOwner.box.height:native.box.height;
            const rootFont=parseFloat(native.viewport.rootFont),largeTextOwner=(clickOwner?clickOwner.box.height:native.box.height)>native.viewport.height;
            const oversizedFocusBox=native.box.height+native.ring*2>native.viewport.height;
            const focusHorizontal=native.box.left-native.ring>=-1&&native.box.right+native.ring<=native.viewport.width+1;
            const focusVertical=native.box.top-native.ring>=-1&&native.box.bottom+native.ring<=native.viewport.height+1;
            const horizontal=native.boxFit.viewport&&native.boxFit.ancestors&&native.textFit;
            const focus=native.focusVisible&&native.focusFit.viewport&&native.focusFit.ancestors;
            if(!horizontal)r.findings.push({tag,index:i,type:'HORIZONTAL_BOX_OR_TEXT_CLIP',name:native.name,text:native.text});
            if(!before&&parseFloat(native.style.fontSize)<rootFont-.1&&native.name!=='fee_ids')r.findings.push({tag,index:i,type:'TEXT_BELOW_1REM'});
            if(!before&&targetHeight<rootFont*2.75-.5)r.findings.push({tag,index:i,type:'TARGET_HEIGHT_BELOW_2_75REM',targetHeight});
            if(!native.focusVisible||!native.focusFit.ancestors||!focusHorizontal||(!focusVertical&&!oversizedFocusBox))r.findings.push({tag,index:i,type:'FOCUS_NOT_FULLY_VISIBLE_NATIVE',name:native.name,geometry:native});
            if(largeTextOwner||oversizedFocusBox){const owner=clickOwner?await e.evaluateHandle(x=>x.labels[0]):await e.elementHandle();record.segmented=await segment(p,owner,tag+'-'+i);await owner.dispose();
                if(!record.segmented.ends.every(x=>x.visible&&x.ancestorFit&&x.originalActivePreserved)||!record.segmented.originalActivePreserved||record.segmented.rootX!==0)r.findings.push({tag,index:i,type:'P13_SEGMENTED_READ_NOT_REACHABLE'});
                record.largeTextOwner=largeTextOwner;record.oversizedFocusBox=oversizedFocusBox;record.simultaneous_whole_outline_required=!oversizedFocusBox;record.P12_old_criterion_changed=false;
            }
            const family=native.name||native.tag;
            if(!familyShots.has(family)){await shot(tag+'-'+i+'-'+family+'-native-focus',p);familyShots.add(family);}
            records.push(record);
        }
        // Reverse traversal changes no fee, input, submitter or cancellation state.
        const reverse=[];
        for(let i=controls.length-2;i>=0;i--){await p.keyboard.press('Shift+Tab');await p.waitForTimeout(40);reverse.push({index:i,original_active:await controls[i].evaluate(e=>e===document.activeElement)});}
        assert(reverse.every(x=>x.original_active),'Original ShiftTab order');
        const value={tag,layer:mode==='components'?'EXPLICIT_LOADED_QWEB_FIXTURE_NORMAL_FRONTEND':'ACTUAL_NORMAL_ROLE_GET',javascript_enabled:!nojs,closedBefore,initial,records,reverse,
            summary_native_Enter_Space:true,submit_activated:false,P13_segmented_contract_not_applied_to_P12:true};
        save(tag+'-geometry.json',value);r.cases.push({tag,geometry_file:tag+'-geometry.json',controls:records.length,viewport:initial.viewport,findings:r.findings.filter(x=>x.tag===tag).length});
    }
    async function cancel(p,tag){const a=panel(p).locator('a'),href=await a.getAttribute('href');assert(href.startsWith('/ydental/settlement'));
        await a.evaluate(e=>e.scrollIntoView({block:'center',inline:'nearest'}));const b=await a.boundingBox();assert(b);
        const [response]=await Promise.all([p.waitForNavigation({waitUntil:'domcontentloaded'}),p.mouse.click(b.x+b.width/2,b.y+b.height/2)]);
        assert.equal(response.status(),200);assert.equal(new URL(p.url()).pathname,'/ydental/settlement');save(tag+'-cancel.json',{href,status:response.status(),method:'GET',bill_submission:false});}
    const configurations=()=>arg('suite')==='smoke'?[[320,800,'native200'],[320,800,'root200']]:
        before?[...views.map(v=>[...v,'normal']),[1366,768,'native200'],[320,800,'native200'],[320,800,'root200']]:
        views.flatMap(v=>['normal','native200','root200'].map(k=>[...v,k]));
    if(['actual','keyboard'].includes(mode)){
        const response=await openURL(page,'/ydental/settlement?patient_id='+sample.selected_patient_id);assert.equal(response.status(),200);assert.equal(await panel(page).count(),1);
        await panel(page).locator(':scope > summary').focus();await page.keyboard.press('Enter');await fieldsInteract(page,'actual');
        for(const [w,h,kind]of configurations()){await zoom(page,w,h,kind);await observe(page,'actual-'+w+'-'+kind);}
        await cancel(page,'actual');
        if(arg('suite')!=='smoke'){
            await zoom(page,1366,768,'normal');await openURL(page,'/ydental/settlement');assert.equal(await panel(page).count(),1);
            await panel(page).locator(':scope > summary').focus();await page.keyboard.press('Enter');await contract(page,'actual-unselected-many-default');
            for(const [w,h]of [[1366,768],[320,800]]){await zoom(page,w,h,'normal');await observe(page,'actual-unselected-many-'+w+'-normal');}
            await cancel(page,'actual-unselected-many');
        }
    }else if(mode==='components'){
        const fixture=JSON.parse(fs.readFileSync(arg('fixture-file')));assert.equal(fixture.database_writes,false);assert.equal(fixture.rollback_performed,true);
        for(const item of fixture.components){
            if(!item.html){save('condition-'+item.name+'.json',{layer:'LOADED_QWEB_CONDITION_ONLY',name:item.name,rendered_panel:false,real_backend_denial_claimed:false});continue;}
            for(const [w,h,kind]of configurations()){
                assert.equal(sha(item.html),item.html_sha256);const p=await context.newPage();let replaced=0;const assets=[];
                p.on('response',x=>{if(['script','stylesheet'].includes(x.request().resourceType()))assets.push(x)});
                await p.route(base+'/ydental/settlement?patient_id='+sample.selected_patient_id,async route=>{
                    const response=await route.fetch();assert.equal(response.status(),200);
                    const body=await page.evaluate(({html,replacement,selector})=>{
                        const d=new DOMParser().parseFromString(html,'text/html'),old=d.querySelector(selector),t=d.createElement('template');t.innerHTML=replacement;
                        if(!old||t.content.children.length!==1)throw Error('One native bill panel replacement required');
                        // Same-response native secrets remain only in memory.
                        const next=t.content.firstElementChild;
                        for(const name of ['csrf_token','revision','key']){const a=old.querySelector('[name="'+name+'"]'),b=next.querySelector('[name="'+name+'"]');if(a&&b)b.setAttribute('value',a.value);}
                        old.replaceWith(next);return '<!doctype html>'+d.documentElement.outerHTML;
                    },{html:await response.text(),replacement:item.html,selector:panelSelector});
                    replaced++;await route.fulfill({response,body});
                });
                await p.setViewportSize({width:w,height:h});await p.bringToFront();await p.goto(base+'/ydental/settlement?patient_id='+sample.selected_patient_id,{waitUntil:'load'});assert.equal(replaced,1);
                await zoom(p,w,h,kind);const tag='fixture-'+item.name+'-'+w+'-'+kind;
                const loaded=[];for(const response of assets){const raw=await response.body();loaded.push({path:new URL(response.url()).pathname,status:response.status(),kind:response.request().resourceType(),bytes:raw.length,sha256:sha(raw)})}
                save(tag+'-assets.json',{loaded,html_sha256:item.html_sha256,native_secret_values_saved:false,context_JS_enabled:!nojs});
                await panel(p).locator(':scope > summary').focus();await p.keyboard.press('Enter');await contract(p,tag);
                await observe(p,tag);await p.close();
            }
        }
    }else if(mode==='conditions'){
        const response=await openURL(page,'/ydental/settlement'+(sample.no_fee_patient_id?'?patient_id='+sample.no_fee_patient_id:''));
        save('actual-condition.json',{status:response.status(),role:alias,bill_panels:await panel(page).count(),source_permission_denial_substituted:false});await shot('actual-condition');
    }else if(mode==='bypass'){
        const paths=alias==='warehouse'?['/ydental/inventory']:alias==='doctor'?['/ydental/documents']:alias==='group_manager'?['/ydental/reports?metric=collections&date_from=2026-10-01&date_to=2026-10-26&store_ids=1&page=1']:['/ydental/settlement?patient_id='+sample.selected_patient_id];
        for(let i=0;i<paths.length;i++){const response=await openURL(page,paths[i]);const value=await page.locator('main').evaluate(e=>({billScope:e.querySelectorAll('[data-dl-scope="settlement-bill-panel"]').length,
            lookup:e.querySelector('[data-dl-scope="settlement-lookup"]')?.outerHTML||null,
            other_operations:[...e.querySelectorAll('details[name="settlement-operation"]')].filter(x=>!x.querySelector('form input[name="operation"][value="bill"]')).map(x=>({summary:x.querySelector('summary')?.textContent.trim(),classes:x.className,style:getComputedStyle(x).padding}))}));
            save('bypass-'+i+'.json',{status:response.status(),...value});await shot('bypass-'+i);}
    }else if(mode==='states'){
        await openURL(page,'/ydental/settlement?patient_id='+sample.selected_patient_id);await panel(page).locator(':scope > summary').focus();await page.keyboard.press('Enter');
        const actions=[['summary',panel(page).locator(':scope > summary')],['confirm',panel(page).locator('button[type=submit]')],['cancel',panel(page).locator('a')]];
        const values=[];
        for(const [name,a]of actions){
            await a.evaluate(e=>e.scrollIntoView({block:'center',inline:'nearest'}));await page.mouse.move(0,0);await settle(page);
            values.push({name,state:'default',value:await a.evaluate(geometry.observe)});const b=await a.boundingBox();assert(b);
            await page.mouse.move(b.x+b.width/2,b.y+b.height/2);await settle(page);values.push({name,state:'hover',value:await a.evaluate(geometry.observe)});
            await page.mouse.down();values.push({name,state:'active',value:await a.evaluate(geometry.observe)});await shot('state-'+name+'-active');
            await page.mouse.move(0,0);await page.mouse.up();
            // No click/Enter/Space on the original confirmation submitter.
            const seed=await a.evaluateHandle(el=>{const all=[...document.querySelectorAll('a[href],summary,button,input:not([type=hidden])')].filter(e=>!e.disabled&&e.getClientRects().length),i=all.indexOf(el);return all[i-1]});await seed.evaluate(e=>e.focus());await page.keyboard.press('Tab');await seed.dispose();
            values.push({name,state:'focus',value:await a.evaluate(geometry.observe)});await shot('state-'+name+'-focus');
        }
        await contract(page,'states-final');save('actual-action-states.json',{values,confirm_activation:false});
    }else throw Error('Unknown P13 browser mode');
};
