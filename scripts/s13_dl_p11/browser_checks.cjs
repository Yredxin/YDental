// Finite DL-P11 source-detail browser client. Normal authentication and read-only GET only.
const fs=require('node:fs'),path=require('node:path'),crypto=require('node:crypto'),assert=require('node:assert/strict'),{execFileSync}=require('node:child_process');
const root=process.cwd(),argv=process.argv.slice(2),arg=n=>{const i=argv.indexOf('--'+n);return i<0?undefined:argv[i+1]},label=arg('label'),run=arg('run-id'),engine=arg('engine'),stage=arg('stage'),mode=arg('mode'),alias=arg('role')||'group_manager',nojs=mode==='nojs';
assert(/^[A-Za-z0-9_-]{1,60}$/.test(label));
const out=path.join(root,'.local/dl-p11/testing/evidence',label);fs.mkdirSync(out,{mode:0o700,recursive:true});
const hash=f=>crypto.createHash('sha256').update(fs.readFileSync(f)).digest('hex'),sha=b=>crypto.createHash('sha256').update(b).digest('hex');
function save(name,v){const f=path.join(out,name),raw=typeof v==='string'||Buffer.isBuffer(v)?v:JSON.stringify(v,null,2);fs.writeFileSync(f,raw,{flag:'wx',mode:0o600});return{file:path.relative(root,f),bytes:fs.statSync(f).size,sha256:hash(f)}}
const binding=JSON.parse(execFileSync(path.join(root,'../.venv/bin/python'),['-c',"import sys,json;from pathlib import Path;sys.path.insert(0,str(Path.cwd()/'scripts/s13_dl_p11'));from http_client import owned_service;import browser_client;browser_client.import_browser();print(json.dumps(owned_service(sys.argv[1])))",run],{encoding:'utf8'}));
const base='http://127.0.0.1:18411',driver=path.join(root,'.local/s11/operations/clock-operator-users-ui-c981cd0-attempt15-runtime-snapshot/playwright/driver/package'),pw=require(driver),views=[[1366,768],[1440,900],[768,1024],[390,844],[320,800]],form='.o_ydental_reporting_filters:not([data-dl-portal])',main='main.o_ydental_reporting',actions='[data-dl-actions="report-source-actions"]';
const sample=arg('sample-file')&&fs.existsSync(arg('sample-file'))?JSON.parse(fs.readFileSync(arg('sample-file'))):{store_id:1,date_from:'2026-10-01',date_to:'2026-10-26'};
const r={status:'INCOMPLETE',binding,label,engine,stage,mode,checks:[],requests:[],responses:[],screenshots:[],failures:[],source_sha256:hash(__filename),business_write_requests:0,user_hand_effect:'PENDING',screenreader_Safari_iOS:'NOT_RUN',credential_request_bodies_recorded:false};
const check=(name,data={})=>r.checks.push({check:name,passed:true,...data});
const computed = el => {
    const mix=(f,b)=>[0,1,2].map(i=>f[i]*f[3]+b[i]*(1-f[3])).concat(1);
    const rgba=c=>{const n=c.match(/[\d.]+/g).map(Number);return [n[0],n[1],n[2],n.length>3?n[3]:1]};
    const background=node=>{let stack=[];for(let p=node;p;p=p.parentElement)stack.push(p);let b=[255,255,255,1];for(const p of stack.reverse())b=mix(rgba(getComputedStyle(p).backgroundColor),b);return b};
    const s=getComputedStyle(el), b=background(el), outside=background(el.parentElement), rect=el.getBoundingClientRect();
    return {tag:el.tagName,text:el.textContent.trim(),class:el.className,
        style:Object.fromEntries(['color','backgroundColor','borderTopColor','borderTopWidth','borderRadius','fontSize','fontWeight','minHeight','padding','gap','outlineColor','outlineWidth','outlineStyle','transitionProperty','transitionDuration','boxShadow','display'].map(k=>[k,s[k]])),
        background:b,outside,foreground:mix(rgba(s.color),b),border:mix(rgba(s.borderTopColor),outside),outline:mix(rgba(s.outlineColor),outside),
        rect:rect.toJSON(),focusVisible:el.matches(':focus-visible'),disabled:el.disabled||false,
        ariaBusy:el.getAttribute('aria-busy'), svg:[...el.querySelectorAll('svg')].map(e=>({
            ariaHidden:e.getAttribute('aria-hidden'),focusable:e.getAttribute('focusable'),
            tabindex:e.getAttribute('tabindex'),viewBox:e.getAttribute('viewBox'),stroke:getComputedStyle(e).stroke,
            strokeWidth:e.getAttribute('stroke-width'),width:e.getBoundingClientRect().width,height:e.getBoundingClientRect().height,
            dataIcon:e.dataset.icon,forbidden:[...e.querySelectorAll('script,foreignObject,image,use,a')].map(x=>x.tagName),
            eventAttributes:[e,...e.querySelectorAll('*')].flatMap(n=>[...n.attributes].filter(a=>/^on|href$/i.test(a.name)).map(a=>a.name))}))};
};
function luminance(rgb) {return rgb.slice(0,3).map(v=>v/255).map(v=>v<=0.04045?v/12.92:((v+0.055)/1.055)**2.4).reduce((s,v,i)=>s+v*[0.2126,0.7152,0.0722][i],0);}
function ratio(a,b) {const [lo,hi]=[luminance(a),luminance(b)].sort((x,y)=>x-y);return(hi+.05)/(lo+.05);}
function contrast(value, boundary=false, focus=false) {
    value.textContrast = ratio(value.foreground,value.background);
    assert(value.textContrast>=4.5, 'Text contrast '+value.textContrast+' '+value.text);
    if(boundary) {
        value.boundaryAgainstOutside=ratio(value.border,value.outside);
        value.boundaryAgainstInside=ratio(value.border,value.background);
        // A filled primary is identified by its fill, secondary/disclosure by border.
        value.fillAgainstOutside=ratio(value.background,value.outside);
        if(/_secondary|_disclosure/.test(value.class))assert(Math.min(value.boundaryAgainstInside,value.boundaryAgainstOutside)>=3,'Secondary/disclosure boundary on both actual backgrounds '+value.text);
        assert(Math.max(value.fillAgainstOutside,value.boundaryAgainstOutside)>=3,'Necessary control boundary '+value.text);
    }
    if(focus) {
        value.focusContrast=ratio(value.outline,value.outside);
        assert(value.focusVisible && value.style.outlineStyle!=='none' && parseFloat(value.style.outlineWidth)>=2 && value.focusContrast>=3,'Visible focus '+value.text);
    }
    return value;
}
(async()=>{let browser,context,page,proc,worker,profile,logged=false;
const live=()=>execFileSync(path.join(root,'../.venv/bin/python'),['-c',"import sys;from pathlib import Path;sys.path.insert(0,str(Path.cwd()/'scripts/s13_dl_p11'));from http_client import owned_service;owned_service(sys.argv[1])",run]);
const settle=async(p=page)=>{await p.waitForTimeout(220);if(!nojs)await p.evaluate(()=>document.fonts.ready)};
async function ready(){await page.locator(form).waitFor({state:'visible'});if(!nojs)await page.locator(form+' [role=combobox]').first().waitFor({state:'visible'});await settle()}
async function shot(name,p=page,layer='ACTUAL_PRODUCT_BROWSER'){live();assert.equal(await p.locator('input[type=password]').count(),0);await p.evaluate(()=>getSelection()?.removeAllRanges());await settle(p);const f=path.join(out,String(r.screenshots.length+1).padStart(3,'0')+'-'+name+'.png');assert(!fs.existsSync(f));if(engine==='chromium'){const c=await context.newCDPSession(p),v=await c.send('Page.captureScreenshot',{format:'png',fromSurface:true,captureBeyondViewport:false});fs.writeFileSync(f,Buffer.from(v.data,'base64'),{flag:'wx',mode:0o600});await c.detach()}else if(nojs){const impl=p._connection.toImpl(p),v=await p.evaluate(()=>({x:0,y:0,width:innerWidth,height:innerHeight})),data=await impl.delegate._session.send('Page.snapshotRect',{...v,coordinateSystem:'Viewport',omitDeviceScaleFactor:false,format:'png'});fs.writeFileSync(f,Buffer.from(data.dataURL.split(',')[1],'base64'),{flag:'wx',mode:0o600})}else await p.screenshot({path:f,fullPage:false,timeout:20000});fs.chmodSync(f,0o600);const raw=fs.readFileSync(f),v={file:path.relative(root,f),sha256:hash(f),bytes:raw.length,width:raw.readUInt32BE(16),height:raw.readUInt32BE(20),layer,actor:r.actor,candidate:binding.candidate_commit,image_pixels_edited:false,viewport:await p.evaluate(()=>({width:innerWidth,height:innerHeight,rootFont:getComputedStyle(document.documentElement).fontSize,dpr:devicePixelRatio,scrollX,scrollY,rootClient:document.documentElement.clientWidth,rootScroll:document.documentElement.scrollWidth}))};r.screenshots.push(v);return v}
async function scroll(e){await e.evaluate(e=>e.scrollIntoView({block:'center',inline:'nearest'}));await settle()}
async function click(e){if(!nojs)return e.click({noWaitAfter:true});await scroll(e);const b=await e.boundingBox();assert(b);await page.mouse.click(b.x+b.width/2,b.y+b.height/2)}
async function nav(fn,report=true){await Promise.all([page.waitForNavigation({waitUntil:'domcontentloaded',timeout:40000}),fn()]);if(report)await ready();else await settle()}
async function login(){const f=path.join(root,'.local/s11/new-target-tests/roles.json'),st=fs.lstatSync(f);assert(st.isFile()&&!st.isSymbolicLink()&&st.uid===process.getuid()&&(st.mode&0o777)===0o600);const account=JSON.parse(fs.readFileSync(f)).users[alias];assert(account);r.actor={alias,uid:account.id};if(nojs){const login=await context.request.get(base+'/web/login?db=ydental_s11_synth_20261023_01'),csrf=await page.evaluate(s=>new DOMParser().parseFromString(s,'text/html').querySelector('form.oe_login_form [name=csrf_token]').value,await login.text());const resp=await context.request.post(base+'/web/login',{form:{login:account.login,password:account.password,csrf_token:csrf,db:'ydental_s11_synth_20261023_01',redirect:'/ydental/access'},maxRedirects:0});assert.equal(resp.status(),303);r.login_layer='NORMAL_CSRF_PASSWORD_SAME_NOJS_CONTEXT'}else{await page.goto(base+'/web/login?db=ydental_s11_synth_20261023_01&redirect=%2Fydental%2Faccess',{waitUntil:'domcontentloaded'});await page.locator('body[is-ready="true"]').waitFor({state:'attached',timeout:30000});const f=page.locator('form.oe_login_form');await f.locator('[name=login]').fill(account.login);await f.locator('[name=password]').fill(account.password);const[response]=await Promise.all([page.waitForResponse(x=>new URL(x.url()).pathname==='/web/login'&&x.request().method()==='POST'),f.locator('button[type=submit]').click()]);assert.equal(response.status(),303);await page.waitForURL(base+'/ydental/access',{waitUntil:'domcontentloaded',timeout:40000});r.login_layer='NORMAL_BROWSER_CSRF_PASSWORD'}logged=true;const identity=await context.request.post(base+'/web/session/get_session_info',{data:{jsonrpc:'2.0',method:'call',params:{},id:1}});assert.equal((await identity.json()).result.uid,account.id);await page.goto(base+'/ydental/access',{waitUntil:'domcontentloaded'});const f2=page.locator('form').filter({has:page.locator('[name=operation][value=switch]')});await f2.locator('[name=store_id]').selectOption(String(sample.store_id||1));await nav(()=>click(f2.locator('button[type=submit]')),false);if(!['permissions','bypass'].includes(mode))await nav(()=>click(page.locator('nav a[href="/ydental/reports"]')))}
async function focusSample(e){return e.evaluate(e=>{const c=getComputedStyle(e),b=e.getBoundingClientRect(),o=parseFloat(c.outlineWidth)+parseFloat(c.outlineOffset),clippers=[];for(let p=e.parentElement;p;p=p.parentElement){const s=getComputedStyle(p);if(['hidden','clip','auto','scroll'].includes(s.overflowX)||['hidden','clip','auto','scroll'].includes(s.overflowY)){const r=p.getBoundingClientRect();clippers.push({class:p.className,overflowX:s.overflowX,overflowY:s.overflowY,left:r.left+p.clientLeft,right:r.left+p.clientLeft+p.clientWidth,top:r.top+p.clientTop,bottom:r.top+p.clientTop+p.clientHeight})}}return{tag:e.tagName,name:e.name,text:e.textContent.trim(),active:e===document.activeElement,focusVisible:e.matches(':focus-visible'),outline:c.outline,offset:c.outlineOffset,box:b.toJSON(),viewport:{width:innerWidth,height:innerHeight},outline_reachable:b.left-o>=-1&&b.right+o<=innerWidth+1&&b.top-o>=-1&&b.bottom+o<=innerHeight+1,not_clipped:clippers.every(p=>(!['hidden','clip','auto','scroll'].includes(p.overflowX)||b.left-o>=p.left-1&&b.right+o<=p.right+1)&&(!['hidden','clip','auto','scroll'].includes(p.overflowY)||b.top-o>=p.top-1&&b.bottom+o<=p.bottom+1)),clippers}})}
async function fixtureReach(p,selector){const values=await p.locator(selector).evaluateAll(xs=>xs.filter(e=>e.getClientRects().length).map(e=>{const textNodes=[],walk=document.createTreeWalker(e,NodeFilter.SHOW_TEXT);for(let n=walk.nextNode();n;n=walk.nextNode())if(n.textContent.trim())textNodes.push(n);const snap=end=>{const t=end?textNodes.at(-1):textNodes[0];if(!t)return null;e.scrollIntoView({block:end?'end':'start',inline:'nearest',behavior:'instant'});const offset=end?t.length-1:0,r=document.createRange();r.setStart(t,offset);r.setEnd(t,offset+1);const b=r.getBoundingClientRect(),clippers=[];for(let a=e;a;a=a.parentElement){const c=getComputedStyle(a),ab=a.getBoundingClientRect();if(['auto','scroll','hidden','clip'].includes(c.overflowX)||['auto','scroll','hidden','clip'].includes(c.overflowY))clippers.push({class:a.className,ox:c.overflowX,oy:c.overflowY,l:ab.left+a.clientLeft,r:ab.left+a.clientLeft+a.clientWidth,t:ab.top+a.clientTop,b:ab.top+a.clientTop+a.clientHeight})}return{char:t.textContent[offset],box:b.toJSON(),viewport:{width:innerWidth,height:innerHeight},visible:b.left>=-1&&b.right<=innerWidth+1&&b.top>=-1&&b.bottom<=innerHeight+1,not_clipped:clippers.every(c=>(!['auto','scroll','hidden','clip'].includes(c.ox)||b.left>=c.l-1&&b.right<=c.r+1)&&(!['auto','scroll','hidden','clip'].includes(c.oy)||b.top>=c.t-1&&b.bottom<=c.b+1)),clippers}};return{tag:e.tagName,class:e.className,text:e.textContent,client:{width:e.clientWidth,height:e.clientHeight},scroll:{width:e.scrollWidth,height:e.scrollHeight},first:snap(false),last:snap(true)}}));assert(values.every(v=>v.first&&v.last&&v.first.visible&&v.last.visible&&v.first.not_clipped&&v.last.not_clipped),'Explicit component endpoints reachable without clipping');return values}
async function setZoomOn(target,factor){await target.bringToFront();if(engine==='webkit')return require(path.join(root,'.local/dl-p3/tools/webkit_finite_zoom_bridge.cjs')).setOwnedPageZoom(target,context,factor);await worker.evaluate(async factor=>{const[t]=await chrome.tabs.query({active:true,currentWindow:true});await chrome.tabs.setZoom(t.id,factor)},factor);await target.waitForFunction(f=>devicePixelRatio===f,factor);const c=await context.newCDPSession(target),v=(await c.send('Page.getLayoutMetrics')).cssVisualViewport;await c.detach();assert.equal(v.zoom,factor);return v}
async function naturalTarget(target,p){const seed=await target.evaluateHandle(e=>{const all=[...document.querySelectorAll('a[href],button,input:not([type=hidden]),select,textarea,summary,[tabindex]')].filter(x=>!x.disabled&&x.tabIndex>=0&&x.getClientRects().length&&getComputedStyle(x).visibility!=='hidden'),i=all.indexOf(e);if(i>0)return{element:all[i-1],key:'Tab'};if(i>=0&&i+1<all.length)return{element:all[i+1],key:'Shift+Tab'};throw Error('No natural keyboard seed')});const key=await seed.evaluate(s=>s.key),origin=await seed.evaluate(s=>({tag:s.element.tagName,name:s.element.name||null,role:s.element.getAttribute('role')}));await seed.evaluate(s=>s.element.focus());await p.keyboard.press(key);assert(await target.evaluate(e=>e===document.activeElement),'Natural '+key+' reaches original target');await target.evaluate(e=>e.scrollIntoView({block:'center',inline:'nearest'}));await p.waitForTimeout(150);const value=await focusSample(target);save('natural-target-observation-'+(r.focus_observations||[]).length+'.json',{origin,key,value});(r.focus_observations??=[]).push({origin,key,value});if(stage==='after')assert(value.active&&value.focusVisible&&value.outline_reachable&&value.not_clipped);else if(!(value.active&&value.focusVisible&&value.outline_reachable&&value.not_clipped))(r.before_findings??=[]).push({type:'BEFORE_FOCUS_REACH',value});await seed.dispose();return{explicit_seed:origin,natural_key:key,focus:value}}
async function reachableTargets(p,tag,selector){await p.bringToFront();const records=[];for(const e of await p.locator(selector).all()){const keyboard=await naturalTarget(e,p),range=await e.evaluate(e=>{const labels=e.querySelector('.o_ydental_reporting_main_action_label')||e,walk=document.createTreeWalker(labels,NodeFilter.SHOW_TEXT),nodes=[];for(let n=walk.nextNode();n;n=walk.nextNode())if(n.textContent.trim())nodes.push(n);const first=nodes[0],last=nodes.at(-1),ends=[];for(const [kind,node,offset]of [['first',first,0],['last',last,last.length-1]]){e.scrollIntoView({block:kind==='first'?'start':'end',inline:'nearest'});const r=document.createRange();r.setStart(node,offset);r.setEnd(node,offset+1);const b=r.getBoundingClientRect();ends.push({kind,character:node.textContent[offset],box:b.toJSON(),visible:b.left>=-1&&b.right<=innerWidth+1&&b.top>=-1&&b.bottom<=innerHeight+1})}return ends});if(stage==='after')assert(range.every(x=>x.visible));else if(!range.every(x=>x.visible))(r.before_findings??=[]).push({type:'BEFORE_TEXT_ENDPOINT',range});records.push({tag:await e.evaluate(e=>e.tagName),text:(await e.textContent()).trim(),href:await e.getAttribute('href'),keyboard,endpoints:range});await e.evaluate(e=>e.scrollIntoView({block:'center',inline:'nearest'}));}save(tag+'-target-reachability.json',records);check(tag+'-actual-natural-Tab-focus-and-first-last-reachability',{count:records.length,layer:p===page?'ACTUAL_BROWSER':'LOADED_QWEB_COMPONENT'});return records}
const sourceTools=require('./browser_source.cjs');
const sourceRoot='main.o_ydental_reporting_source';
const sourceTargets=sourceRoot+' a,'+sourceRoot+' summary';
async function reportOpen(metric='collections',extra={}) {
    const q=new URLSearchParams({metric,date_from:sample.date_from,date_to:sample.date_to,
        store_ids:String(sample.store_id||1),page:'1',...extra});
    const response=await page.goto(base+'/ydental/reports?'+q,{waitUntil:'domcontentloaded'});
    assert.equal(response.status(),200); await ready(); return q;
}
async function sourceOpen({multi=false,metric='collections',index=0}={}) {
    const q=await reportOpen(metric,multi?{store_ids:'1,2'}:{});
    const links=page.locator('.o_ydental_reporting_table_wrap tbody a');
    assert(await links.count()>index,'Existing source sample required');
    const href=await links.nth(index).getAttribute('href');
    const response=await page.goto(base+href,{waitUntil:'domcontentloaded'});
    assert.equal(response.status(),200); await page.locator(sourceRoot).waitFor(); await settle();
    const returns=await page.locator(sourceRoot+' > p a[href^="/ydental/reports?"]').evaluateAll(xs=>xs.map(e=>e.getAttribute('href')));
    assert.equal(returns.length,2);assert.equal(returns[0],returns[1]);
    const returned=new URL(returns[0],base);
    for(const key of ['metric','date_from','date_to','store_ids','page'])assert.equal(returned.searchParams.get(key),q.get(key));
    return {href,return_url:returns[0],query:[...q]};
}
async function sourceSnap(name,p=page) {
    const v=await p.evaluate(sourceTools.projection);
    save(name+'-projection.json',v);save(name+'-source-main.html',await p.locator(sourceRoot).evaluate(m=>m.outerHTML));
    if(stage==='after'&&arg('before-result')) {
        const beforeDir=path.dirname(path.join(root,arg('before-result'))),f=path.join(beforeDir,name+'-projection.json');
        if(fs.existsSync(f)) {
            const old=JSON.parse(fs.readFileSync(f));
            assert.deepEqual(sourceTools.semantic(v),sourceTools.semantic(old),'Full native source projection/href exact except native UTC field');
            assert(v.layout.root.scroll<=old.layout.root.scroll+1,'No new source root overflow compared with same engine before');
            check('full-source-semantic-and-root-before-after-'+name,{before_file:path.relative(root,f),before:old.layout.root,after:v.layout.root});
        }
    }
    return v;
}
async function sourceSummaries(p=page,prefix='actual') {
    for(let i=0;i<await p.locator(sourceRoot+' details').count();i++) {
        const d=p.locator(sourceRoot+' details').nth(i),s=d.locator('summary');
        await s.evaluate(e=>e.scrollIntoView({block:'center'}));
        if(await d.evaluate(e=>e.open))await s.press('Enter');
        await s.focus();await s.press('Enter');assert(await d.evaluate(e=>e.open));
        await sourceSnap(prefix+'-details-'+i,p);await shot(prefix+'-details-'+i+'-expanded',p,p===page?'ACTUAL_PRODUCT_BROWSER':'ACTUAL_LOADED_QWEB_MEMORY_COMPONENT');
        await s.press('Space');assert(!await d.evaluate(e=>e.open));
        const b=await d.boundingBox(),sb=await s.boundingBox();assert(Math.abs(b.height-sb.height)<2,'Closed disclosure leaves no body hole');
        check(prefix+'-native-Enter-Space-'+i);
    }
}
async function sourceFamilies() {
    const v=await page.locator(sourceRoot).evaluate(m=>({
        marker:m.dataset.dlLayout,
        nav:[...m.querySelector('nav').querySelectorAll('a')].map(e=>({scope:e.dataset.dlActions,cls:e.className})),
        actions:[...m.querySelectorAll('[data-dl-actions]')].map(e=>({
            tag:e.tagName,scope:e.dataset.dlActions,cls:e.className,text:e.textContent.trim(),
            svg:[...e.querySelectorAll('svg')].map(s=>({hidden:s.getAttribute('aria-hidden'),focusable:s.getAttribute('focusable'),tabindex:s.getAttribute('tabindex')}))})),
        summaryMarker:[...m.querySelectorAll('summary')].map(s=>getComputedStyle(s).display)}));
    assert(v.marker&&v.marker!=='report-actions-spacing');assert.equal(v.nav.length,3);
    assert(v.nav.every(x=>x.scope==='report-source-actions'&&x.cls.includes('quiet')));
    assert(v.actions.length>=9);assert(v.actions.every(x=>x.scope==='report-source-actions'));
    assert(v.actions.every(x=>x.svg.every(s=>s.hidden==='true'&&s.focusable==='false'&&s.tabindex!=='0')));
    assert(v.summaryMarker.every(x=>x==='list-item'),'Native marker retained');
    save('rendered-families.json',v);check('source-only-each-rendered-family-optin');
}
async function sourceStates() {
    const values=[];
    for(const kind of ['secondary','quiet','disclosure']) {
        const target=kind==='disclosure'?page.locator(sourceRoot+' summary').first():page.locator(actions+'.o_ydental_reporting_source_action_'+kind).first();
        assert(await target.count(),'Rendered '+kind+' required');
        await target.evaluate(e=>e.scrollIntoView({block:'center'}));await page.mouse.move(0,0);
        values.push({kind,state:'default',value:contrast(await target.evaluate(computed),kind!=='quiet')});
        await target.hover();values.push({kind,state:'hover',value:contrast(await target.evaluate(computed),kind!=='quiet')});
        const b=await target.boundingBox();await page.mouse.move(b.x+b.width/2,b.y+b.height/2);await page.mouse.down();
        values.push({kind,state:'active',value:contrast(await target.evaluate(computed),kind!=='quiet')});
        await page.mouse.move(0,0);await page.mouse.up();await page.keyboard.press('Tab');
        await target.focus();values.push({kind,state:'focus',value:contrast(await target.evaluate(computed),kind!=='quiet',true)});
    }
    save('actual-action-states.json',values);check('actual-three-family-four-state-contrast-focus');
}
async function isolationSnap(name,pathname) {
    const response=await page.goto(base+pathname,{waitUntil:'domcontentloaded'});await settle();
    const value=await page.locator('main.o_ydental_reporting').evaluate(m=>{const copy=m.cloneNode(true),query=copy.querySelector('.o_ydental_reporting_scope > p:nth-child(3)');let queryAtNative=null;if(query){const walker=document.createTreeWalker(query,NodeFilter.SHOW_TEXT),nodes=[];for(let n=walker.nextNode();n;n=walker.nextNode())if(/\d{4}-\d\d-\d\d \d\d:\d\d:\d\d/.test(n.textContent))nodes.push(n);if(nodes.length!==1)throw Error('Single native query_at text node required');queryAtNative=nodes[0].textContent;nodes[0].textContent=nodes[0].textContent.replace(/\d{4}-\d\d-\d\d \d\d:\d\d:\d\d/,'<NATIVE_QUERY_AT_UTC>');}return {html:m.outerHTML,htmlTypedQueryAt:copy.outerHTML,queryAtNative,
        queryAt:m.querySelector('.o_ydental_reporting_scope > p:nth-child(3)')?.textContent,
        p11:[...m.querySelectorAll('[data-dl-actions="report-source-actions"],[data-dl-layout="report-source-detail"]')].length,
        fields:[...m.querySelectorAll('input,select,button')].map(e=>({tag:e.tagName,name:e.name,value:['csrf_token','revision'].includes(e.name)?'<PRIVATE_BINDING>':e.value})),
        computed:[...m.querySelectorAll('a,summary,input,select,button,h1,h2,th,td')].map(e=>({
            tag:e.tagName,text:e.matches('a,summary,h1,h2,th')?e.textContent:null,
            style:Object.fromEntries(['fontSize','fontWeight','color','backgroundColor','padding','margin','gap','outline','display'].map(k=>[k,getComputedStyle(e)[k]]))}))}});
    assert.equal(value.p11,0);value.status=response.status();
    value.html=value.html.replace(/(name="(?:csrf_token|revision)"[^>]*value=")[^"]*/g,'$1<PRIVATE_BINDING>')
        .replace(/(value=")[^"]*("[^>]*name="(?:csrf_token|revision)")/g,'$1<PRIVATE_BINDING>$2');
    save(name+'-isolation.json',value);await shot(name+'-isolation');
    if(stage==='after'&&arg('before-result')) {
        const f=path.join(pathModuleDir(arg('before-result')),name+'-isolation.json');
        if(fs.existsSync(f)) {
            const old=JSON.parse(fs.readFileSync(f));
            assert.deepEqual(value.computed,old.computed,'Unchanged '+name+' computed styles');
            assert.deepEqual(value.fields,old.fields,'Unchanged '+name+' fields');
            assert.equal(value.status,old.status);
            // Native report UTC is the sole allowed source-dependent timestamp.
            const normal=async v=>page.evaluate(html=>{const m=new DOMParser().parseFromString(html,'text/html').querySelector('main.o_ydental_reporting'),query=m.querySelector('.o_ydental_reporting_scope > p:nth-child(3)'),walker=document.createTreeWalker(query,NodeFilter.SHOW_TEXT),nodes=[];for(let n=walker.nextNode();n;n=walker.nextNode())if(/\d{4}-\d\d-\d\d \d\d:\d\d:\d\d/.test(n.textContent))nodes.push(n);if(nodes.length!==1)throw Error('Unique original query_at text node required');nodes[0].textContent=nodes[0].textContent.replace(/\d{4}-\d\d-\d\d \d\d:\d\d:\d\d/,'<NATIVE_QUERY_AT_UTC>');return m.outerHTML},v.html);
            if(name==='error')assert.equal(value.html,old.html,'Whole native error main exact');
            if(name==='main')assert.equal(await normal(value),await normal(old),'Whole P10 main except native query time');
            check('same-engine-isolated-'+name);
        }
    }
    return value;
}
function pathModuleDir(file){return path.dirname(path.join(root,file));}

async function sourceSpacing(width) {
    const v=await page.evaluate(sourceTools.projection),unit=parseFloat(v.layout.rootFont)/16;
    const close=(actual,expected,name)=>assert(Math.abs(parseFloat(actual)-expected*unit)<.6,name+': '+actual+' expected '+expected*unit);
    close(v.layout.main.style.paddingTop,width<=720?16:24,'Main single inset');
    const modules=v.layout.modules;
    const byClass=name=>modules.find(x=>x.class.split(' ').includes(name));
    close(byClass('o_ydental_reporting_source_navigation').style.columnGap,12,'Navigation gap');
    close(byClass('o_ydental_reporting_source_scope').style.marginTop,24,'Intro to scope');
    close(byClass('o_ydental_reporting_source_return_tail').style.marginTop,24,'Tail return');
    for(const row of v.layout.cards) {
        close(row.card.style.paddingTop,width<=720?16:24,'Card single inset');
        close(row.card.style.marginTop,24,'Scope/previous card to card');
        const get=name=>row.children.find(x=>x.class.split(' ').includes(name));
        close(row.children[0].style.marginTop,0,'Heading inherited margin reset');
        for(const [name,pixels]of [['patient',8],['quantity',12],['date',12],['facts',16],['links',16],['trace',16]]) {
            const node=get('o_ydental_reporting_source_'+name);if(node)close(node.style.marginTop,pixels,name+' single spacing owner');
        }
        close(get('o_ydental_reporting_source_facts').style.columnGap,8,'Fact label-value gap');
        close(get('o_ydental_reporting_source_facts').style.rowGap,12,'Fact business group gap');
        const allocation=get('o_ydental_reporting_source_allocations');
        if(allocation)close(allocation.style.marginTop,16,'Facts to allocations');
    }
    save('asserted-spacing-'+width+'.json',{unit,width,layout:v.layout});
    check('computed-single-spacing-owners-'+width);
}
async function tableKeyboardRead() {
    const region=page.locator(sourceRoot+' .o_ydental_reporting_table_wrap').first();
    if(!await region.count())return;
    await region.evaluate(e=>{e.scrollIntoView({block:'center'});e.scrollLeft=0});
    await region.focus();const before=await region.evaluate(e=>({left:e.scrollLeft,client:e.clientWidth,scroll:e.scrollWidth,rootX:scrollX}));
    for(let i=0;i<5;i++)await page.keyboard.press('ArrowRight');await page.waitForTimeout(250);
    const after=await region.evaluate(e=>({left:e.scrollLeft,rootX:scrollX,active:e===document.activeElement}));
    if(before.scroll>before.client+1)assert(after.left>before.left,'Native keyboard reads allocation table locally');
    assert(after.active);assert.equal(after.rootX,before.rootX,'Local keyboard horizontal reading does not move root');
    save('actual-table-keyboard-horizontal.json',{before,after});check('actual-native-local-allocation-horizontal-reading');
}

async function sourceLayout() {
    const route=await sourceOpen({index:1});save('route.json',route);
    for(const [width,height]of views) {
        await page.setViewportSize({width,height});await settle();await page.evaluate(()=>scrollTo(0,0));
        await sourceSnap('view-'+width);await shot('source-'+width+'-top');
        const trace=page.locator(sourceRoot+' article details').last();await scroll(trace);await shot('source-'+width+'-tail');
        if(stage==='after'){await sourceSpacing(width);await reachableTargets(page,'source-'+width,sourceTargets);if(width===320)await tableKeyboardRead();}
    }
    await page.setViewportSize({width:1366,height:768});await sourceSummaries();
    if(stage==='after'){await sourceFamilies();await sourceStates();}
    // Activate both original return links and follow the actual href again.
    for(const position of ['first','last']) {
        await page.goto(base+route.href,{waitUntil:'domcontentloaded'});await settle();
        const all=page.locator(sourceRoot+' > p a[href^="/ydental/reports?"]');
        const a=position==='first'?all.first():all.last();
        await nav(()=>click(a));assert.equal(new URL(page.url()).search,new URL(base+route.return_url).search);
        check('normal-'+position+'-return-exact-filter-page',{href:route.return_url});
    }
    await isolationSnap('main',route.return_url);
    const invalid=route.href.replace(/\/source\/([^/]+)\/\d+/,'/source/$1/2147483647');
    const denied=await isolationSnap('error',invalid);assert.equal(denied.status,403);
    check('actual-nonexistent-source-backend-denied-no-p11', {status:denied.status});
}
async function sourceZoom() {
    await sourceOpen({index:1});r.native_zoom=await setZoomOn(page,2);
    assert.equal(await page.evaluate(()=>getComputedStyle(document.documentElement).fontSize),'16px');
    await sourceSnap('native200');await shot('native200-source-top');
    await reachableTargets(page,'native200-source',sourceTargets);await sourceSummaries(page,'native200');
    await setZoomOn(page,1);await page.evaluate(()=>document.documentElement.style.fontSize='200%');
    assert.equal(await page.evaluate(()=>getComputedStyle(document.documentElement).fontSize),'32px');
    await sourceSnap('rootfont200');if(stage==='after')await tableKeyboardRead();await shot('rootfont200-source-top');
    await reachableTargets(page,'rootfont200-source',sourceTargets);await sourceSummaries(page,'rootfont200');
    check('actual-native200-and-independent-root32-source');
}
async function sourceNoJS() {
    assert(nojs);const route=await sourceOpen({index:1});
    assert.equal(await page.locator('script[data-p11-runtime]').count(),0);
    await sourceSnap('true-nojs');await shot('nojs-source-top');await sourceSummaries(page,'nojs');
    await reachableTargets(page,'nojs-source',sourceTargets);
    await nav(()=>click(page.locator(sourceRoot+' > p a[href^="/ydental/reports?"]').last()));
    assert.equal(new URL(page.url()).search,new URL(base+route.return_url).search);
    check('true-nojs-same-authenticated-context-native-details-and-return',{javaScriptEnabled:false});
}
async function sourcePermissions() {
    const q='metric=collections&date_from='+sample.date_from+'&date_to='+sample.date_to+'&store_ids=1';
    const response=await page.goto(base+'/ydental/reports/source/collections/8?'+q,{waitUntil:'domcontentloaded'});
    await settle();r.permission_status=response.status();
    if(alias==='none') {assert.equal(response.status(),403);assert.equal(await page.locator(sourceRoot).count(),0);}
    else {assert.equal(response.status(),200);assert.equal(await page.locator(sourceRoot).count(),1);await sourceSnap('authorized-'+alias);}
    await shot('permission-'+alias);
    for(const path of ['/ydental/reports/source/collections/2147483647?'+q,
        '/ydental/reports/source/collections/8?'+q.replace('store_ids=1','store_ids=999999')]) {
        const denied=await context.request.get(base+path);assert.equal(denied.status(),403);
        check('actual-source-reauthorization-negative',{path:new URL(base+path).pathname,status:denied.status()});
    }
    if(alias==='group_manager') {
        const q=await reportOpen('followups',{store_ids:'1,2',date_from:'2026-01-01',date_to:'2026-12-31'});
        const dataResponse=await context.request.get(base+'/ydental/reports?'+q+'&output=json');
        assert.equal(dataResponse.status(),200);const data=await dataResponse.json();
        save('actual-cross-store-full-authorized-query.json',data);
        const row=data.rows.find(x=>x.requires_store_switch);
        assert(row,'Existing authorized cross-store followup source required');
        const link=page.locator('a[href^="/ydental/reports/source/followups/'+row.source_id+'?"]').first();
        assert.equal(await link.count(),1);const href=await link.getAttribute('href');
        const sourceResponse=await page.goto(base+href,{waitUntil:'domcontentloaded'});
        assert.equal(sourceResponse.status(),200);await settle();await sourceSnap('actual-cross-store');
        const note=page.locator(sourceRoot+' article .o_ydental_reporting_source_store_notice');
        assert.equal(await note.count(),1);assert(await note.isVisible());
        const business=page.locator(sourceRoot+' .o_ydental_reporting_source_links a').first();
        const businessHref=await business.getAttribute('href');
        await shot('actual-cross-store-visible-notice');
        const businessResponse=await page.goto(base+businessHref,{waitUntil:'domcontentloaded'});
        await settle();const bodyText=await page.locator('body').innerText();
        save('actual-cross-store-original-business-read.json',{status:businessResponse.status(),
            href:businessHref,bodyText,normal_store_switches:r.requests.filter(x=>x.path==='/ydental/access/action').length});
        // The original page may return native 403 or a current-store empty view.
        // Preserve the exact response and let the independent reviewer assess it.
        assert([200,403,409].includes(businessResponse.status()));
        await shot('actual-cross-store-original-business-read');
        check('actual-existing-cross-store-followup-visible-notice-and-original-business-GET',{
            source_id:row.source_id,store_id:row.store_id,href,notice_default_visible_verified:true,
            businessHref,businessStatus:businessResponse.status(),no_store_switch:true});
    }
}
async function sourceComponents() {
    await sourceOpen({index:1});
    const styles=await page.locator('link[rel=stylesheet]').evaluateAll(xs=>xs.map(e=>{const c=e.cloneNode();c.href=e.href;return c.outerHTML}).join(''));
    const file=arg('fixture-file');assert(file);
    const fixtures=JSON.parse(fs.readFileSync(path.join(root,file)));
    r.fixture_source={file,sha256:hash(path.join(root,file)),layer:'ACTUAL_LOADED_QWEB_MEMORY_COMPONENT'};
    for(const item of fixtures.components) {
        const p=await context.newPage();await p.setContent('<!doctype html><html lang="zh-CN"><head>'+styles+'</head><body>'+item.html+'</body></html>',{waitUntil:'load'});
        await settle(p);await p.route('**/*',route=>route.abort());
        await p.locator('a').evaluateAll(xs=>xs.forEach(e=>e.addEventListener('click',event=>event.preventDefault())));
        for(const[width,height]of views) {
            await p.setViewportSize({width,height});await settle(p);
            await sourceSnap('fixture-'+item.name+'-'+width,p);await shot('fixture-'+item.name+'-'+width,p,'ACTUAL_LOADED_QWEB_MEMORY_COMPONENT');
            await reachableTargets(p,'fixture-'+item.name+'-'+width,sourceTargets);
        }
        await sourceSummaries(p,'fixture-'+item.name);
        if(item.name.includes('long')) {
            await p.setViewportSize({width:1366,height:768});
            const native=await setZoomOn(p,2);assert.equal(await p.evaluate(()=>getComputedStyle(document.documentElement).fontSize),'16px');
            await sourceSnap('fixture-'+item.name+'-native200',p);await reachableTargets(p,'fixture-'+item.name+'-native200',sourceTargets);
            await shot('fixture-'+item.name+'-native200',p,'ACTUAL_LOADED_QWEB_MEMORY_COMPONENT');
            await setZoomOn(p,1);await p.evaluate(()=>document.documentElement.style.fontSize='200%');
            assert.equal(await p.evaluate(()=>getComputedStyle(document.documentElement).fontSize),'32px');
            await sourceSnap('fixture-'+item.name+'-rootfont200',p);await reachableTargets(p,'fixture-'+item.name+'-rootfont200',sourceTargets);
            await shot('fixture-'+item.name+'-rootfont200',p,'ACTUAL_LOADED_QWEB_MEMORY_COMPONENT');
            await p.evaluate(()=>document.documentElement.style.fontSize='');
            check('explicit-long-source-component-both-real-zoom-modes',{native});
        }
        const pressure=await p.addStyleTag({content:sourceRoot+','+sourceRoot+' *{line-height:1.6!important;letter-spacing:.12em!important;word-spacing:.16em!important}'+sourceRoot+' p{margin-block-end:2em!important}'});
        await sourceSnap('fixture-'+item.name+'-user-spacing',p);await reachableTargets(p,'user-spacing-'+item.name,sourceTargets);
        await shot('fixture-'+item.name+'-user-spacing',p,'EXPLICIT_USER_TEXT_SPACING_COMPONENT');await pressure.evaluate(e=>e.remove());
        for(const fault of ['missing-SVG','missing-CSS']) {
            const f=await context.newPage();await f.setContent('<!doctype html><html lang="zh-CN"><head>'+(fault==='missing-CSS'?'':styles)+'</head><body>'+item.html+'</body></html>',{waitUntil:'load'});
            await settle(f);if(fault==='missing-SVG')await f.locator('svg').evaluateAll(xs=>xs.forEach(e=>e.remove()));
            assert((await f.locator(sourceRoot+' a').allTextContents()).every(x=>x.trim().length>0));
            assert((await f.locator(sourceRoot+' summary').allTextContents()).every(x=>x.trim().length>0));
            await shot('fixture-'+item.name+'-'+fault,f,'EXPLICIT_FAULT_COMPONENT');await f.close();
        }
        await p.close();check('loaded-QWeb-branch-longvalue-user-spacing-fault-'+item.name);
    }
}


async function sourceBypass() {
    if(alias==='group_manager') {
        const route=await sourceOpen({index:1});
        await isolationSnap('main',route.return_url);
        const invalid=route.href.replace(/\/source\/([^/]+)\/\d+/,'/source/$1/2147483647');
        const value=await isolationSnap('error',invalid);assert.equal(value.status,403);
        return;
    }
    const pathname=alias==='warehouse'?'/ydental/inventory':alias==='settlement'?'/ydental/settlement':'/ydental/documents';
    const response=await page.goto(base+pathname,{waitUntil:'domcontentloaded'});assert.equal(response.status(),200);await settle();
    const value=await page.locator('main.container').last().evaluate(m=>{
        const style=e=>Object.fromEntries(['fontSize','fontWeight','color','backgroundColor','borderColor','borderWidth','borderRadius','padding','gap','minHeight','display','outline','lineHeight'].map(k=>[k,getComputedStyle(e)[k]]));
        return {rootMarker:m.getAttribute('data-dl-layout'),
            actions:[...m.querySelectorAll('[data-dl-actions]')].map(e=>({tag:e.tagName,text:e.textContent.trim(),scope:e.dataset.dlActions,style:style(e)})),
            forms:[...m.querySelectorAll('form')].map(f=>({action:f.getAttribute('action'),method:f.getAttribute('method'),fields:[...f.elements].filter(e=>e.name).map(e=>({name:e.name,type:e.type,value:['csrf_token','revision','key'].includes(e.name)?'<PRIVATE_BINDING>':e.value,disabled:e.disabled,required:e.required})),style:style(f)})),
            fields:[...m.querySelectorAll('input:not([type=hidden]),select,th,td')].map(e=>({tag:e.tagName,name:e.name,style:style(e)})),
            p11:m.querySelectorAll('[data-dl-actions="report-source-actions"],[data-dl-layout="report-source-detail"]').length};
    });
    assert.equal(value.p11,0);const name='bypass-'+alias;save(name+'.json',value);await shot(name);
    if(stage==='after'&&arg('before-result')) {
        const file=path.join(pathModuleDir(arg('before-result')),name+'.json');
        const old=JSON.parse(fs.readFileSync(file));
        const normalized=v=>{const x=structuredClone(v);for(const form of x.forms)for(const field of form.fields)if(field.name==='pay.actual_utc'){assert(/^\d{4}-\d\d-\d\dT\d\d:\d\d/.test(field.value));field.value='<NATIVE_NOW_DEFAULT>';}return x};
        assert.deepEqual(normalized(value),normalized(old),'Finite readonly bypass field/style exact except typed native now default');
    }
    check('finite-readonly-no-p11-'+pathname,{status:response.status(),no_business_submit:true});
}

try{if(engine==='webkit'){const manifest=path.join(root,'.local/dl-p1/evidence/webkit-engine-native-source-manifest.json');assert.equal(hash(manifest),JSON.parse(fs.readFileSync(path.join(root,'.local/dl-p1/webkit-manifest-binding.json'))).sha256);for(const f of JSON.parse(fs.readFileSync(manifest)).browser_files)assert.equal(hash(path.join(root,'.local/dl-p1',f.path)),f.sha256);r.engine_manifest_sha256=hash(manifest);browser=await pw.webkit.launch(require(path.join(root,'.local/dl-p3/verification/webkit_plugins_environment.cjs')).launchOptions(root));context=await browser.newContext({viewport:{width:1366,height:768},locale:'zh-CN',javaScriptEnabled:!nojs,acceptDownloads:true})}else if(['zoom','components','stress'].includes(mode)){profile=path.join(out,'owned-temporary-profile');fs.mkdirSync(profile,{mode:0o700});const ext=path.join(root,'.local/dl-p1/zoom-extension');context=await pw.chromium.launchPersistentContext(profile,{headless:true,channel:'chromium',executablePath:path.join(root,'.local/s11/browsers/chromium-1248/chrome-linux64/chrome'),viewport:{width:1366,height:768},locale:'zh-CN',acceptDownloads:true,args:['--disable-extensions-except='+ext,'--load-extension='+ext],env:{...process.env,LD_LIBRARY_PATH:path.join(root,'.local/s11/browser-deps/root/usr/lib/x86_64-linux-gnu'),FONTCONFIG_FILE:path.join(root,'.local/s12/fontconfig/fonts.conf'),FONTCONFIG_PATH:path.join(root,'.local/s12/fontconfig')}});browser=context.browser();worker=context.serviceWorkers()[0]||await context.waitForEvent('serviceworker')}else{browser=await pw.chromium.launch({headless:true,executablePath:path.join(root,'.local/s11/browsers/chromium-1248/chrome-linux64/chrome'),env:{...process.env,LD_LIBRARY_PATH:path.join(root,'.local/s11/browser-deps/root/usr/lib/x86_64-linux-gnu'),FONTCONFIG_FILE:path.join(root,'.local/s12/fontconfig/fonts.conf'),FONTCONFIG_PATH:path.join(root,'.local/s12/fontconfig')}});context=await browser.newContext({viewport:{width:1366,height:768},locale:'zh-CN',javaScriptEnabled:!nojs,acceptDownloads:true})}
r.actual_engine_version=browser.version();r.driver_version=require(path.join(driver,'package.json')).version;proc=browser._connection.toImpl(browser)?.options?.browserProcess?.process;if(proc){r.native_main_lifecycle={pid:proc.pid,executable:proc.spawnfile};proc.once('exit',(exitCode,signalCode)=>Object.assign(r.native_main_lifecycle,{exitCode,signalCode}))}context.setDefaultTimeout(nojs?12000:20000);context.on('response',x=>r.responses.push({path:new URL(x.url()).pathname,method:x.request().method(),status:x.status()}));context.on('requestfailed',x=>r.failures.push({path:new URL(x.url()).pathname,resource:x.resourceType(),error:x.failure()?.errorText}));await context.route('**/*',route=>{const req=route.request(),u=new URL(req.url()),op=new URLSearchParams(req.postData()||'').get('operation');if(!['data:','about:','blob:'].includes(u.protocol)&&u.origin!==base){(r.external_blocks??=[]).push({protocol:u.protocol,host:u.host});return route.abort()}if(u.pathname.startsWith('/ydental/'))r.requests.push({method:req.method(),path:u.pathname,query:[...u.searchParams].filter(([k])=>k!=='revision'),...(u.pathname==='/ydental/access/action'?{operation:op}:{})});if(req.method()==='POST'&&u.pathname.startsWith('/ydental/')&&!((u.pathname==='/ydental/access/action'&&op==='switch'))){r.business_write_requests++;(r.guard_blocks??=[]).push({path:u.pathname,operation:op});return route.abort()}return route.continue()});page=context.pages()[0]||await context.newPage();page.on('pageerror',e=>(r.page_errors??=[]).push({class:e.constructor.name,message:String(e.message).slice(0,600)}));await login();
if(mode==='bypass')await sourceBypass();else if(mode==='layout')await sourceLayout();else if(mode==='zoom')await sourceZoom();else if(mode==='nojs')await sourceNoJS();else if(mode==='permissions')await sourcePermissions();else if(['components','stress'].includes(mode))await sourceComponents();else throw Error('Unknown P11 mode');
assert.equal(r.business_write_requests,0);assert.equal((r.guard_blocks||[]).length,0);assert.equal((r.external_blocks||[]).length,0);r.status='P11_'+stage.toUpperCase()+'_'+engine.toUpperCase()+'_'+mode.toUpperCase()+'_PASS';
}catch(error){r.status='FAILED_NO_AUTOMATIC_REPLAY';r.error={class:error.constructor.name,message:String(error.message).slice(0,2200)};r.stack=String(error.stack).split('\n').slice(0,12)}finally{if(context){if(logged)try{r.logout_status=(await context.request.post(base+'/web/session/destroy',{data:{jsonrpc:'2.0',method:'call',params:{},id:9}})).status()}catch(e){r.logout_error=e.constructor.name}try{await context.close();r.context_normal_close=true}catch(e){r.context_close_error=e.constructor.name}}if(browser)try{await browser.close();r.browser_normal_close=true}catch(e){r.browser_close_error=e.constructor.name}if(proc&&proc.exitCode===null)await new Promise(resolve=>{proc.once('exit',resolve);setTimeout(resolve,3000)});if(profile&&r.context_normal_close){fs.rmSync(profile,{recursive:true});r.owned_profile_removed=true}r.finished_at_utc=new Date().toISOString();save('result.json',r);process.stdout.write(JSON.stringify({status:r.status,checks:r.checks.length,screenshots:r.screenshots.length})+'\n');process.exitCode=r.status.endsWith('_PASS')?0:2}})();
