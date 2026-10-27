// Finite DL-P12 settlement-readonly browser client. Normal authentication and read-only GET only.
const fs=require('node:fs'),path=require('node:path'),crypto=require('node:crypto'),assert=require('node:assert/strict'),{execFileSync}=require('node:child_process');
const root=process.cwd(),argv=process.argv.slice(2),arg=n=>{const i=argv.indexOf('--'+n);return i<0?undefined:argv[i+1]},label=arg('label'),run=arg('run-id'),engine=arg('engine'),stage=arg('stage'),mode=arg('mode'),alias=arg('role')||'settlement',nojs=mode==='nojs'||arg('js')==='off';
assert(/^[A-Za-z0-9_-]{1,60}$/.test(label));
const out=path.join(root,'.local/dl-p12-rwd/testing/evidence',label);fs.mkdirSync(out,{mode:0o700,recursive:true});
const hash=f=>crypto.createHash('sha256').update(fs.readFileSync(f)).digest('hex'),sha=b=>crypto.createHash('sha256').update(b).digest('hex');
function save(name,v){const f=path.join(out,name),raw=typeof v==='string'||Buffer.isBuffer(v)?v:JSON.stringify(v,null,2);fs.writeFileSync(f,raw,{flag:'wx',mode:0o600});return{file:path.relative(root,f),bytes:fs.statSync(f).size,sha256:hash(f)}}
const binding=JSON.parse(execFileSync(path.join(root,'../.venv/bin/python'),['-c',"import sys,json;from pathlib import Path;sys.path.insert(0,str(Path.cwd()/'scripts/s13_dl_p12_rwd'));from http_client import owned_service;sys.path.insert(0,str(Path.cwd()/'scripts/s13_dl_p12'));import browser_client;browser_client.import_browser();print(json.dumps(owned_service(sys.argv[1])))",run],{encoding:'utf8'}));
const base='http://127.0.0.1:18411',driver=path.join(root,'.local/s11/operations/clock-operator-users-ui-c981cd0-attempt15-runtime-snapshot/playwright/driver/package'),pw=require(driver),views=[[1366,768],[1440,900],[768,1024],[390,844],[320,800]],form='.o_ydental_settlement_search_form',main='main.o_ydental_settlement',actions='[data-dl-actions="settlement-readonly-actions"]';
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
const live=()=>execFileSync(path.join(root,'../.venv/bin/python'),['-c',"import sys;from pathlib import Path;sys.path.insert(0,str(Path.cwd()/'scripts/s13_dl_p12_rwd'));from http_client import owned_service;owned_service(sys.argv[1])",run]);
const settle=async(p=page)=>{await p.waitForTimeout(220);if(!nojs)await p.evaluate(()=>document.fonts.ready)};
async function ready(){await page.locator(form).waitFor({state:'visible'});await settle()}
async function shot(name,p=page,layer='ACTUAL_PRODUCT_BROWSER'){live();assert.equal(await p.locator('input[type=password]').count(),0);await p.evaluate(()=>getSelection()?.removeAllRanges());await settle(p);const f=path.join(out,String(r.screenshots.length+1).padStart(3,'0')+'-'+name+'.png');assert(!fs.existsSync(f));if(engine==='chromium'){const c=await context.newCDPSession(p),v=await c.send('Page.captureScreenshot',{format:'png',fromSurface:true,captureBeyondViewport:false});fs.writeFileSync(f,Buffer.from(v.data,'base64'),{flag:'wx',mode:0o600});await c.detach()}else if(nojs){const impl=p._connection.toImpl(p),v=await p.evaluate(()=>({x:0,y:0,width:innerWidth,height:innerHeight})),data=await impl.delegate._session.send('Page.snapshotRect',{...v,coordinateSystem:'Viewport',omitDeviceScaleFactor:false,format:'png'});fs.writeFileSync(f,Buffer.from(data.dataURL.split(',')[1],'base64'),{flag:'wx',mode:0o600})}else await p.screenshot({path:f,fullPage:false,timeout:20000});fs.chmodSync(f,0o600);const raw=fs.readFileSync(f),v={file:path.relative(root,f),sha256:hash(f),bytes:raw.length,width:raw.readUInt32BE(16),height:raw.readUInt32BE(20),layer,actor:r.actor,candidate:binding.candidate_commit,image_pixels_edited:false,viewport:await p.evaluate(()=>({width:innerWidth,height:innerHeight,rootFont:getComputedStyle(document.documentElement).fontSize,dpr:devicePixelRatio,scrollX,scrollY,rootClient:document.documentElement.clientWidth,rootScroll:document.documentElement.scrollWidth}))};r.screenshots.push(v);return v}
async function scroll(e){await e.evaluate(e=>e.scrollIntoView({block:'center',inline:'nearest'}));await settle()}
async function click(e){if(!nojs)return e.click({noWaitAfter:true});await scroll(e);const b=await e.boundingBox();assert(b);await page.mouse.click(b.x+b.width/2,b.y+b.height/2)}
async function nav(fn,report=true){await Promise.all([page.waitForNavigation({waitUntil:'domcontentloaded',timeout:40000}),fn()]);if(report)await ready();else await settle()}
async function login(){const f=path.join(root,'.local/s11/new-target-tests/roles.json'),st=fs.lstatSync(f);assert(st.isFile()&&!st.isSymbolicLink()&&st.uid===process.getuid()&&(st.mode&0o777)===0o600);const account=JSON.parse(fs.readFileSync(f)).users[alias];assert(account);r.actor={alias,uid:account.id};if(nojs){const login=await context.request.get(base+'/web/login?db=ydental_s11_synth_20261023_01'),csrf=await page.evaluate(s=>new DOMParser().parseFromString(s,'text/html').querySelector('form.oe_login_form [name=csrf_token]').value,await login.text());const resp=await context.request.post(base+'/web/login',{form:{login:account.login,password:account.password,csrf_token:csrf,db:'ydental_s11_synth_20261023_01',redirect:'/ydental/access'},maxRedirects:0});assert.equal(resp.status(),303);r.login_layer='NORMAL_CSRF_PASSWORD_SAME_NOJS_CONTEXT'}else{await page.goto(base+'/web/login?db=ydental_s11_synth_20261023_01&redirect=%2Fydental%2Faccess',{waitUntil:'domcontentloaded'});await page.locator('body[is-ready="true"]').waitFor({state:'attached',timeout:30000});const f=page.locator('form.oe_login_form');await f.locator('[name=login]').fill(account.login);await f.locator('[name=password]').fill(account.password);const[response]=await Promise.all([page.waitForResponse(x=>new URL(x.url()).pathname==='/web/login'&&x.request().method()==='POST'),f.locator('button[type=submit]').click()]);assert.equal(response.status(),303);await page.waitForURL(base+'/ydental/access',{waitUntil:'domcontentloaded',timeout:40000});r.login_layer='NORMAL_BROWSER_CSRF_PASSWORD'}logged=true;const identity=await context.request.post(base+'/web/session/get_session_info',{data:{jsonrpc:'2.0',method:'call',params:{},id:1}});assert.equal((await identity.json()).result.uid,account.id);await page.goto(base+'/ydental/access',{waitUntil:'domcontentloaded'});const f2=page.locator('form').filter({has:page.locator('[name=operation][value=switch]')});await f2.locator('[name=store_id]').selectOption(String(sample.store_id||1));await nav(()=>click(f2.locator('button[type=submit]')),false);if(!['permissions','bypass'].includes(mode))await nav(()=>click(page.locator('nav a[href="/ydental/settlement"]')))}
async function focusSample(e){return e.evaluate(e=>{const c=getComputedStyle(e),b=e.getBoundingClientRect(),o=parseFloat(c.outlineWidth)+parseFloat(c.outlineOffset),clippers=[];for(let p=e.parentElement;p;p=p.parentElement){const s=getComputedStyle(p);if(['hidden','clip','auto','scroll'].includes(s.overflowX)||['hidden','clip','auto','scroll'].includes(s.overflowY)){const r=p.getBoundingClientRect();clippers.push({class:p.className,overflowX:s.overflowX,overflowY:s.overflowY,left:r.left+p.clientLeft,right:r.left+p.clientLeft+p.clientWidth,top:r.top+p.clientTop,bottom:r.top+p.clientTop+p.clientHeight})}}return{tag:e.tagName,name:e.name,text:e.textContent.trim(),active:e===document.activeElement,focusVisible:e.matches(':focus-visible'),outline:c.outline,offset:c.outlineOffset,scrollMarginBlockStart:c.scrollMarginBlockStart,scrollMarginBlockEnd:c.scrollMarginBlockEnd,scrollMarginInlineStart:c.scrollMarginInlineStart,scrollMarginInlineEnd:c.scrollMarginInlineEnd,box:b.toJSON(),viewport:{width:innerWidth,height:innerHeight},outline_reachable:b.left-o>=-1&&b.right+o<=innerWidth+1&&b.top-o>=-1&&b.bottom+o<=innerHeight+1,not_clipped:clippers.every(p=>(!['hidden','clip','auto','scroll'].includes(p.overflowX)||b.left-o>=p.left-1&&b.right+o<=p.right+1)&&(!['hidden','clip','auto','scroll'].includes(p.overflowY)||b.top-o>=p.top-1&&b.bottom+o<=p.bottom+1)),clippers}})}
async function fixtureReach(p,selector){
    const values=await p.locator(selector).evaluateAll(xs=>xs.filter(e=>e.getClientRects().length).map(e=>{
        const textNodes=[],walk=document.createTreeWalker(e,NodeFilter.SHOW_TEXT);
        for(let n=walk.nextNode();n;n=walk.nextNode())if(n.textContent.trim())textNodes.push(n);
        const snap=end=>{
            const t=end?textNodes.at(-1):textNodes[0];if(!t)return null;
            e.scrollIntoView({block:end?'end':'start',inline:'nearest',behavior:'instant'});
            let offset=end?t.length-1:0;while(/\s/u.test(t.textContent[offset]))offset+=end?-1:1;
            const range=document.createRange();range.setStart(t,offset);range.setEnd(t,offset+1);
            const observe=()=>{
                const b=range.getBoundingClientRect(),clippers=[];
                for(let a=e;a;a=a.parentElement){const c=getComputedStyle(a),ab=a.getBoundingClientRect();
                    if(['auto','scroll','hidden','clip'].includes(c.overflowX)||['auto','scroll','hidden','clip'].includes(c.overflowY))
                        clippers.push({class:a.className,ox:c.overflowX,oy:c.overflowY,l:ab.left+a.clientLeft,r:ab.left+a.clientLeft+a.clientWidth,t:ab.top+a.clientTop,b:ab.top+a.clientTop+a.clientHeight});}
                return {char:t.textContent[offset],box:b.toJSON(),viewport:{width:innerWidth,height:innerHeight},scroll:{x:scrollX,y:scrollY},
                    visible:b.left>=-1&&b.right<=innerWidth+1&&b.top>=-1&&b.bottom<=innerHeight+1,
                    not_clipped:clippers.every(c=>(!['auto','scroll','hidden','clip'].includes(c.ox)||b.left>=c.l-1&&b.right<=c.r+1)&&(!['auto','scroll','hidden','clip'].includes(c.oy)||b.top>=c.t-1&&b.bottom<=c.b+1)),clippers};
            };
            const initial=observe(),adjustments=[];
            // Read actual text using ordinary local/window scrolling. No CSS,
            // font, text, geometry or visibility threshold is changed.
            if(!initial.visible||!initial.not_clipped){
                for(let a=e.parentElement;a;a=a.parentElement){
                    const c=getComputedStyle(a),ab=a.getBoundingClientRect(),b=range.getBoundingClientRect(),before={x:a.scrollLeft,y:a.scrollTop};
                    if(['auto','scroll'].includes(c.overflowX)&&a.scrollWidth>a.clientWidth+1&&(b.left<ab.left+a.clientLeft||b.right>ab.left+a.clientLeft+a.clientWidth))
                        a.scrollLeft+=(b.left+b.right)/2-(ab.left+a.clientLeft+a.clientWidth/2);
                    if(['auto','scroll'].includes(c.overflowY)&&a.scrollHeight>a.clientHeight+1&&(b.top<ab.top+a.clientTop||b.bottom>ab.top+a.clientTop+a.clientHeight))
                        a.scrollTop+=(b.top+b.bottom)/2-(ab.top+a.clientTop+a.clientHeight/2);
                    if(before.x!==a.scrollLeft||before.y!==a.scrollTop)adjustments.push({target:a.className,before,after:{x:a.scrollLeft,y:a.scrollTop}});
                }
                const b=range.getBoundingClientRect(),before={x:scrollX,y:scrollY};
                const dx=b.left<0||b.right>innerWidth?(b.left+b.right-innerWidth)/2:0;
                const dy=b.top<0||b.bottom>innerHeight?(b.top+b.bottom-innerHeight)/2:0;
                if(dx||dy){window.scrollBy({left:dx,top:dy,behavior:'instant'});adjustments.push({target:'WINDOW_NORMAL_SCROLL',requested:{dx,dy},before,after:{x:scrollX,y:scrollY}});}
            }
            return {initial,adjustments,...observe()};
        };
        return {tag:e.tagName,class:e.className,text:e.textContent,fontFamily:getComputedStyle(e).fontFamily,
            client:{width:e.clientWidth,height:e.clientHeight},scroll:{width:e.scrollWidth,height:e.scrollHeight},first:snap(false),last:snap(true)};
    }));
    const observed={selector,layer:'ACTUAL_LOADED_QWEB_MEMORY_COMPONENT_TEXT_RANGE',values,
        no_repair_CSS_or_text_changes:true,ordinary_scroll_adjustments_recorded:true};
    const index=r.range_observations||0;r.range_observations=index+1;
    save('component-endpoints-observation-'+index+'.json',observed);
    assert(values.every(v=>v.first&&v.last&&v.first.visible&&v.last.visible&&v.first.not_clipped&&v.last.not_clipped),'Explicit component endpoints reachable without clipping');
    return values;
}
async function setZoomOn(target,factor){await target.bringToFront();if(engine==='webkit')return require(path.join(root,'.local/dl-p3/tools/webkit_finite_zoom_bridge.cjs')).setOwnedPageZoom(target,context,factor);await worker.evaluate(async factor=>{const[t]=await chrome.tabs.query({active:true,currentWindow:true});await chrome.tabs.setZoom(t.id,factor)},factor);await target.waitForFunction(f=>devicePixelRatio===f,factor);const c=await context.newCDPSession(target),v=(await c.send('Page.getLayoutMetrics')).cssVisualViewport;await c.detach();assert.equal(v.zoom,factor);return v}
async function focusThreePhasePNG(p,phase,before) {
    const started=new Date().toISOString(),cdp=await context.newCDPSession(p),result=await cdp.send('Page.captureScreenshot',{format:'png',fromSurface:true,captureBeyondViewport:false});await cdp.detach();
    const file=path.join(out,'phase-'+phase+'.png');fs.writeFileSync(file,Buffer.from(result.data,'base64'),{flag:'wx',mode:0o600});
    const raw=fs.readFileSync(file),facts={file:path.relative(root,file),sha256:hash(file),bytes:raw.length,width:raw.readUInt32BE(16),height:raw.readUInt32BE(20),layer:'EXPLICIT_LOADED_QWEB_FOCUS_LIVE_PHASE_DIAGNOSTIC',image_pixels_edited:false,actor:r.actor,candidate:binding.candidate_commit,started,finished:new Date().toISOString(),sampleBeforeCapture:before,note:'Live asynchronous browser capture; no frozen geometry or pixel editing'};
    r.screenshots.push(facts);return facts;
}

async function naturalTarget(target,p){const seed=await target.evaluateHandle(e=>{const all=[...document.querySelectorAll('a[href],button,input:not([type=hidden]),select,textarea,summary,[tabindex]')].filter(x=>!x.disabled&&x.tabIndex>=0&&x.getClientRects().length&&getComputedStyle(x).visibility!=='hidden'),i=all.indexOf(e);if(i>0)return{element:all[i-1],key:'Tab'};if(i>=0&&i+1<all.length)return{element:all[i+1],key:'Shift+Tab'};throw Error('No natural keyboard seed')});const key=await seed.evaluate(s=>s.key),origin=await seed.evaluate(s=>({tag:s.element.tagName,name:s.element.name||null,role:s.element.getAttribute('role')}));await seed.evaluate(s=>s.element.focus());await p.keyboard.press(key);assert(await target.evaluate(e=>e===document.activeElement),'Natural '+key+' reaches original target');const geometry=async()=>({observed_at:new Date().toISOString(),focus:await focusSample(target),local:await target.evaluate(e=>{const a=e.closest('.o_ydental_settlement_fee_scroll');return a?{scrollLeft:a.scrollLeft,scrollTop:a.scrollTop,client:a.clientWidth,scroll:a.scrollWidth}:null})});const nativeImmediate=await geometry(),diagnose=mode==='focus-diagnostic'&&(await target.textContent()).includes('账单1')&&(await p.evaluate(()=>innerWidth))===390;if(diagnose)await focusThreePhasePNG(p,'native-immediate',nativeImmediate);if(!nojs)await Promise.race([p.evaluate(()=>new Promise(resolve=>requestAnimationFrame(()=>requestAnimationFrame(resolve)))),p.waitForTimeout(3000).then(()=>{throw Error('Bounded native focus rAF timeout')})]);await p.waitForTimeout(250);const nativeSettled=await geometry(),nativeBeforeHelper=nativeSettled.focus;if(diagnose)await focusThreePhasePNG(p,'native-settled',nativeSettled);await target.evaluate(e=>e.scrollIntoView({block:'center',inline:'nearest'}));await p.waitForTimeout(150);const afterHelper=await geometry(),value=afterHelper.focus;if(diagnose)await focusThreePhasePNG(p,'after-helper',afterHelper);save('natural-target-observation-'+(r.focus_observations||[]).length+'.json',{origin,key,nativeImmediate,nativeSettled,nativeBeforeHelper,afterHelper,value});(r.focus_observations??=[]).push({origin,key,nativeImmediate,nativeSettled,nativeBeforeHelper,afterHelper,value});if(stage==='after')assert(value.active&&value.focusVisible&&value.outline_reachable&&value.not_clipped);else if(!(value.active&&value.focusVisible&&value.outline_reachable&&value.not_clipped))(r.before_findings??=[]).push({type:'BEFORE_FOCUS_REACH',value});await seed.dispose();return{explicit_seed:origin,natural_key:key,focus:value}}
async function reachableTargets(p,tag,selector){await p.bringToFront();const records=[];for(const e of await p.locator(selector).all()){const keyboard=await naturalTarget(e,p),range=await e.evaluate(e=>{const labels=e.querySelector('.o_ydental_reporting_main_action_label')||e,walk=document.createTreeWalker(labels,NodeFilter.SHOW_TEXT),nodes=[];for(let n=walk.nextNode();n;n=walk.nextNode())if(n.textContent.trim())nodes.push(n);const first=nodes[0],last=nodes.at(-1),ends=[];for(const [kind,node,offset]of [['first',first,0],['last',last,last.length-1]]){e.scrollIntoView({block:kind==='first'?'start':'end',inline:'nearest'});const r=document.createRange();r.setStart(node,offset);r.setEnd(node,offset+1);const b=r.getBoundingClientRect();ends.push({kind,character:node.textContent[offset],box:b.toJSON(),visible:b.left>=-1&&b.right<=innerWidth+1&&b.top>=-1&&b.bottom<=innerHeight+1})}return ends});if(stage==='after')assert(range.every(x=>x.visible));else if(!range.every(x=>x.visible))(r.before_findings??=[]).push({type:'BEFORE_TEXT_ENDPOINT',range});records.push({tag:await e.evaluate(e=>e.tagName),text:(await e.textContent()).trim(),href:await e.getAttribute('href'),keyboard,endpoints:range});await e.evaluate(e=>e.scrollIntoView({block:'center',inline:'nearest'}));}save(tag+'-target-reachability.json',records);check(tag+'-actual-natural-Tab-focus-and-first-last-reachability',{count:records.length,layer:p===page?'ACTUAL_BROWSER':'LOADED_QWEB_COMPONENT'});return records}

const tools=require('../s13_dl_p12/browser_settlement.cjs');
const scope='[data-dl-scope="settlement-lookup"]',search=scope+' [data-dl-region="search"]';
const targets=scope+' button,'+scope+' a,'+scope+' summary';
const count=()=>r.requests.filter(x=>x.method==='GET'&&x.path==='/ydental/settlement').length;
const dirOf=f=>path.dirname(path.join(root,f));
const projection=async(name,p=page)=>{
    const v=await p.evaluate(tools.projection);save(name+'-projection.json',v);
    const unit=parseFloat(v.layout.viewport.rootFont),width=v.layout.viewport.width;
    const expectedPadding=unit*(width<=544?1:1.5);
    const spacing={name,rootFont:unit,label_input_gap:parseFloat(v.layout.label.style.gap),
        input_button_gap:parseFloat(v.layout.form.style.gap),lookup_module_gap:parseFloat(v.layout.lookup.style.gap),
        fee_section_gap:parseFloat(v.layout.overview.style.gap),container_padding:v.layout.lookup.style.padding,
        expected:{label:unit*.5,form:unit,modules:unit*1.5,container:expectedPadding}};
    assert.equal(spacing.label_input_gap,unit*.5);assert.equal(spacing.input_button_gap,unit);
    assert.equal(spacing.lookup_module_gap,unit*1.5);assert.equal(spacing.fee_section_gap,unit*1.5);
    // RWD has new local responsive padding owners; capture actual values here.
    save(name+'-spacing-owners.json',spacing);
    if(p===page&&stage==='after'&&arg('before-result')) {
        const f=path.join(dirOf(arg('before-result')),name+'-projection.json');
        if(fs.existsSync(f)) {
            const old=JSON.parse(fs.readFileSync(f));
            assert.deepEqual(tools.semantic(v),tools.semantic(old),'Exact native semantic/whole frozen suffix except declared native defaults');
            assert(v.layout.root.scroll<=old.layout.root.scroll+1,'No new root overflow');
            check('exact-before-after-'+name,{before_file:path.relative(root,f),old_root:old.layout.root,new_root:v.layout.root});
        }
    }
    return v;
};
async function open(href='/ydental/settlement') {
    const response=await page.goto(base+href,{waitUntil:'domcontentloaded'});
    assert.equal(response.status(),200);await ready();return response;
}
async function captureSections(prefix,p=page) {
    for(const [kind,selector]of [['search',search],['context',scope+' [data-dl-region="selected-patient"]'],...['today','history','pending'].map(k=>[k,scope+' [data-fee-kind="'+k+'"]'])]) {
        await p.locator(selector).evaluate(e=>e.scrollIntoView({block:'start',inline:'nearest'}));
        await shot(prefix+'-'+kind,p,p===page?'ACTUAL_PRODUCT_BROWSER':'ACTUAL_LOADED_QWEB_MEMORY_COMPONENT');
    }
}
async function querySelect() {
    await open();const initial=await projection('initial-unselected');
    assert.equal(initial.form.method,'get');assert.equal(initial.form.action,'/ydental/settlement');
    assert.deepEqual(initial.form.fields.map(x=>x.name),['q']);assert.equal(initial.form.fields[0].maxlength,'100');
    assert(!initial.query.some(([k])=>k==='patient_id'));assert.equal(initial.other_stores.length,0);
    const number=sample.business_number||initial.fees.flatMap(x=>x.rows)[0]?.[1]||initial.candidates[0]?.text.split('·').at(-1).trim();
    assert(number,'Existing ordinary candidate sample required');r.sample_business_number=number;
    let n=count();const input=page.locator(form+' [name="q"]');await input.fill(number);await input.press('Tab');await page.waitForTimeout(150);
    assert.equal(count(),n);assert.deepEqual((await page.evaluate(tools.projection)).fees,initial.fees);
    await nav(()=>input.press('Enter'));assert.equal(count(),n+1);
    const searched=await projection('searched-number-unselected');assert.deepEqual(searched.query,[['q',number]]);
    assert(searched.candidates.length);assert(searched.candidate_count<=30);assert.deepEqual(searched.fees,initial.fees);
    const candidate=searched.candidates[0],u=new URL(candidate.href,base);assert.deepEqual([...u.searchParams.keys()],['patient_id']);
    const name=candidate.text.split('·')[0].trim();
    await nav(()=>click(page.locator(search+' li a').first()));
    const selected=await projection('selected-patient');assert.deepEqual(selected.query,[...u.searchParams]);
    assert.equal(selected.form.fields[0].value,'');assert.equal(selected.other_stores.length,1);
    r.selected_href=candidate.href;r.patient_id=u.searchParams.get('patient_id');
    r.selected_name=name;r.selected_business_number=number;
    check('ordinary-menu-GET-Enter-q-only-explicit-candidate-selection',{number,candidate,GET_enter_count:1,candidate_page_limit:30,typing_requests:0});
    return selected;
}
async function emptyAndName() {
    const field=page.locator(form+' [name=q]');const n=count();
    const q='P12无匹配<&"测试';await field.fill(q);assert.equal(count(),n);
    await nav(()=>click(page.locator(form+' button[type=submit]')));assert.equal(count(),n+1);
    const empty=await projection('empty-candidates-unselected');assert.deepEqual(empty.query,[['q',q]]);
    assert.equal(empty.candidates.length,0);assert.equal(empty.other_stores.length,0);
    assert.equal(empty.form.fields[0].value,q);assert.equal(await page.locator(search+' script').count(),0);
    await captureSections('empty-candidates');
    await page.locator(form+' [name=q]').fill(r.selected_name);await nav(()=>click(page.locator(form+' button[type=submit]')));
    const name=await projection('name-search-unselected');assert(name.candidates.length);assert(!name.query.some(([k])=>k==='patient_id'));
    check('button-one-GET-new-search-clears-selection-Chinese-safe-echo-and-name',{query:q,GET_button_count:1,empty_candidates_not_fee_settlement:true});
    await open(r.selected_href);
}
async function traces(p=page,prefix='actual') {
    for(let i=0;i<await p.locator(scope+' details').count();i++) {
        const d=p.locator(scope+' details').nth(i),s=d.locator('summary');await s.evaluate(e=>e.scrollIntoView({block:'center',inline:'nearest'}));
        if(await d.evaluate(e=>e.open))await s.press('Enter');
        const n=count();await s.focus();await s.press('Enter');assert(await d.evaluate(e=>e.open));assert.equal(count(),n);
        await projection(prefix+'-trace-'+i,p);await shot(prefix+'-trace-'+i,p,p===page?'ACTUAL_PRODUCT_BROWSER':'ACTUAL_LOADED_QWEB_MEMORY_COMPONENT');
        assert.equal(await s.locator('svg').count(),0,'Native disclosure has no second arrow');
        await s.press('Space');assert(!await d.evaluate(e=>e.open));
        const b=await d.boundingBox(),sb=await s.boundingBox();assert(Math.abs(b.height-sb.height)<2,'Closed trace has no content hole');
    }
    check(prefix+'-native-details-Enter-Space-no-GET');
}
async function nativeTableReading(p=page,prefix='actual') {
    const observations=[];
    for(const table of await p.locator(scope+' .o_ydental_settlement_fee_scroll').all()) {
        await table.evaluate(e=>e.scrollIntoView({block:'center',inline:'nearest'}));await table.focus();
        const observe=()=>table.evaluate(e=>({left:e.scrollLeft,client:e.clientWidth,scroll:e.scrollWidth,windowX:scrollX,active:e===document.activeElement,focusVisible:e.matches(':focus-visible'),rootClient:document.documentElement.clientWidth,rootScroll:document.documentElement.scrollWidth}));
        const index=observations.length,initial=await observe();save(prefix+'-table-'+index+'-native-initial.json',initial);
        const drive=async(key,edge,label)=>{
            const steps=[];let final=await observe();
            for(let i=0;i<60;i++) {
                const reached=edge==='left'?final.left<=1:final.left>=final.scroll-final.client-1;
                if(reached)break;
                const before=final;await p.keyboard.press(key);await p.waitForTimeout(120);final=await observe();steps.push({key,before,after:final});
            }
            save(prefix+'-table-'+index+'-'+label+'.json',{key,edge,steps,final,helper_scroll_reset_used:false});
            assert(final.active&&final.focusVisible&&final.windowX===initial.windowX&&final.rootScroll<=initial.rootScroll,'Native local reading retains original table focus and root overflow');
            assert(edge==='left'?final.left<=1:final.left>=final.scroll-final.client-1,'Bounded trusted arrow reading reaches actual '+edge+' boundary');
            return final;
        };
        const width=await drive('ArrowLeft','left','native-left-start');
        const pictures=p===page||(prefix.includes('long-mixed-values')&&prefix.endsWith('-320'));
        if(pictures)await shot(prefix+'-table-'+index+'-left-edge',p,p===page?'ACTUAL_PRODUCT_BROWSER':'ACTUAL_LOADED_QWEB_MEMORY_COMPONENT');
        const right=await drive('ArrowRight','right','native-right');
        if(width.scroll>width.client+2)assert(right.left>width.left);
        if(pictures)await shot(prefix+'-table-'+index+'-right-edge',p,p===page?'ACTUAL_PRODUCT_BROWSER':'ACTUAL_LOADED_QWEB_MEMORY_COMPONENT');
        const left=await drive('ArrowLeft','left','native-left-final');
        assert(left.left<=right.left&&left.left<=1);observations.push({initial,normalization:'TRUSTED_ARROWLEFT_ONLY_NO_SCROLLLEFT_ASSIGNMENT',before:width,right,left});
    }
    save(prefix+'-native-table-arrow-keys.json',observations);check(prefix+'-native-local-table-read',{tables:observations.length});
}
async function continuousKeyboard(p=page,prefix='actual') {
    const all=await p.locator(scope+' input:not([type="hidden"]),'+scope+' button,'+scope+' a,'+scope+' summary,'+scope+' [tabindex="0"]').all();
    const visible=[];for(const e of all)if(await e.isVisible()&&await e.evaluate(e=>e.tabIndex>=0&&!e.disabled))visible.push(e);
    assert(visible.length>=2);
    const seedBefore=await p.evaluate(()=>({x:scrollX,y:scrollY,activeTag:document.activeElement.tagName,rootScroll:document.documentElement.scrollWidth,rootClient:document.documentElement.clientWidth}));
    save(prefix+'-continuous-seed-setup.json',{strategy:'VERIFIED_FRESH_DOCUMENT_TOP_THEN_EXPLICIT_ORIGINAL_Q_FOCUS',before:seedBefore,JavaScript_scroll_assignment:false,arbitrary_ControlHome_recovery_claimed:false});
    assert(seedBefore.y<=1,'The caller must provide the observed fresh-document start before explicit q seed');await visible[0].focus();
    await p.evaluate(()=>{window.__p12ContinuousKeys=[];window.addEventListener('keydown',e=>window.__p12ContinuousKeys.push({key:e.key,shift:e.shiftKey,trusted:e.isTrusted,tag:e.target.tagName,name:e.target.name||null,href:e.target.getAttribute('href')}),true)});
    const records=[];
    for(let i=0;i<visible.length;i++) {
        const e=visible[i];if(i)await p.keyboard.press('Tab');
        assert(await e.evaluate(e=>e===document.activeElement),'Continuous native Tab order '+i);
        await p.waitForTimeout(100);const nativeImmediate=await focusSample(e);if(!nojs)if(!nojs)await Promise.race([p.evaluate(()=>new Promise(resolve=>requestAnimationFrame(()=>requestAnimationFrame(resolve)))),p.waitForTimeout(3000).then(()=>{throw Error('Bounded native focus rAF timeout')})]);await p.waitForTimeout(250);const native=await focusSample(e),steps=[];
        if(stage==='after')for(let n=0;n<24;n++) {
            const current=await focusSample(e);if(current.outline_reachable&&current.not_clipped)break;
            const b=current.box,clip=current.clippers.find(c=>c.class.includes('o_ydental_settlement_fee_scroll'));
            let key;
            if(clip&&(b.left<clip.left+6||b.right>clip.right-6))key=b.left<clip.left+6?'ArrowLeft':'ArrowRight';
            else if(b.left<6||b.right>current.viewport.width-6)key=b.left<6?'ArrowLeft':'ArrowRight';
            else key=b.top<6?'ArrowUp':'ArrowDown';
            await p.keyboard.press(key);await p.waitForTimeout(80);steps.push({key,before:current,after:await focusSample(e)});
        }
        const final=await focusSample(e);records.push({index:i,tag:await e.evaluate(e=>e.tagName),text:(await e.textContent()).trim(),nativeImmediate,native,settle_policy:'100MS_THEN_JS_ON_2RAF_AND_EXTERNAL_250MS',steps,final});save(prefix+'-continuous-keyboard-step-'+i+'.json',records.at(-1));
        if(stage==='after'){assert(native.active&&native.focusVisible&&native.outline_reachable&&native.not_clipped,'Settled native original fit target fully visible before recovery '+i);assert(final.active&&final.focusVisible&&final.outline_reachable&&final.not_clipped,'Keyboard-only original target fully reachable '+i);}
    }
    await p.keyboard.press('Shift+Tab');assert(await visible.at(-2).evaluate(e=>e===document.activeElement));
    const events=await p.evaluate(()=>window.__p12ContinuousKeys);
    const trustObservation=nojs?'NOT_OBSERVED_EXPECTED_JS_DISABLED':'OBSERVED_ALL_TRUSTED_REQUIRED';
    save(prefix+'-continuous-native-keyboard.json',{layer:p===page?'ACTUAL_NORMAL_ROLE_BROWSER':'EXPLICIT_LOADED_COMPONENT_BROWSER',explicit_seed:'first original q field',records,events,event_trust_observation:trustObservation,native_input_transport:'ENGINE_NATIVE_KEYBOARD_PRESS',anchor_helper_scroll_used:false,native_Tab_automatic_full_visibility_claimed:false});
    if(nojs)assert.equal(events.length,0,'No page listener callback runs in the JS-disabled context');
    else assert(events.length&&events.every(e=>e.trusted));
    await shot(prefix+'-continuous-keyboard-final',p,p===page?'ACTUAL_PRODUCT_BROWSER':'ACTUAL_LOADED_QWEB_MEMORY_COMPONENT');
    check(prefix+'-continuous-native-Tab-ShiftTab-and-keyboard-only-reach',{controls:visible.length,helper_scroll_used:false});
}
async function otherStores() {
    const a=page.locator(scope+' a[href^="/ydental/settlement/other-stores/"]');assert.equal(await a.count(),1);
    const href=await a.getAttribute('href'),response=await page.goto(base+href,{waitUntil:'domcontentloaded'});assert.equal(response.status(),200);await settle();
    const value=await genericSnapshot();save('other-store-target.json',value);await shot('actual-other-store-minimal-summary');
    assert.equal(await page.locator('[data-dl-actions="settlement-readonly-actions"]').count(),0);
    if(stage==='after'&&arg('before-result'))assert.deepEqual(value,JSON.parse(fs.readFileSync(path.join(dirOf(arg('before-result')),'other-store-target.json'))));
    check('original-other-store-entry-real-GET',{href,status:response.status(),no_store_switch:true,no_business_submit:true});
    await page.goBack({waitUntil:'domcontentloaded'});await ready();assert.equal(new URL(page.url()).pathname,'/ydental/settlement');
}
async function operations() {
    const forms=await page.locator('details[name="settlement-operation"] form').count();assert(forms>0);
    const first=page.locator('details[name="settlement-operation"]').first(),s=first.locator(':scope > summary');
    await s.evaluate(e=>e.scrollIntoView({block:'center'}));await s.press('Enter');assert(await first.evaluate(e=>e.open));
    assert(await first.locator('form button[type=submit]').isEnabled());
    await shot('first-original-operation-readonly-expanded');
    const cancel=first.locator(':scope > a');const href=await cancel.getAttribute('href');assert(href.startsWith('/ydental/settlement'));
    await nav(()=>click(cancel));assert.equal(r.business_write_requests,0);
    check('original-operation-fields-enabled-expand-and-native-cancel-only',{forms,cancel_href:href,business_submit:false});
}
async function families() {
    const v=await page.locator(scope).evaluate(m=>({
        controls:[...m.querySelectorAll('button,a,summary')].map(e=>({tag:e.tagName,class:e.className,text:e.textContent.trim(),marker:e.dataset.dlActions,
            svg:[...e.querySelectorAll('svg')].map(s=>({icon:s.dataset.icon,ariaHidden:s.getAttribute('aria-hidden'),focusable:s.getAttribute('focusable'),tabindex:s.getAttribute('tabindex')}))})),
        headings:[...m.querySelectorAll('h2 svg')].length,
        summaryDisplay:[...m.querySelectorAll('summary')].map(e=>getComputedStyle(e).display)}));
    if(stage==='after') {
        assert(v.controls.every(x=>x.marker==='settlement-readonly-actions'));
        assert(v.controls.filter(x=>x.tag==='BUTTON').every(x=>x.class.includes('primary')&&x.svg.length===1));
        assert(v.controls.filter(x=>x.tag==='SUMMARY').every(x=>x.class.includes('disclosure')&&!x.svg.length));
        assert(v.controls.every(x=>x.svg.every(s=>s.ariaHidden==='true'&&s.focusable==='false'&&s.tabindex!=='0')));
        assert(v.headings<=2);assert(v.summaryDisplay.every(x=>x==='list-item'));
    }
    save('loaded-action-families.json',v);
    const body=[];
    for(const e of await page.locator(scope+' h2,'+scope+' p,'+scope+' label,'+scope+' th,'+scope+' td,'+scope+' .o_ydental_settlement_page_boundary').all())if(await e.isVisible())body.push(contrast(await e.evaluate(computed)));
    save('actual-body-text-contrast-samples.json',body);
    save('actual-accessibility-tree.txt',await page.locator(scope).ariaSnapshot());
    check('loaded-action-families-native-text-AX-and-SVG',{controls:v.controls.length});
}
async function layout() {
    await querySelect();
    for(const [width,height]of views){await page.setViewportSize({width,height});await settle();await projection('selected-'+width);await captureSections('selected-'+width);}
    await page.setViewportSize({width:320,height:800});await traces();await nativeTableReading();
    await reachableTargets(page,'actual-selected-320',targets);await families();
    await page.setViewportSize({width:1366,height:768});await otherStores();await operations();await emptyAndName();
}
async function zooms() {
    await querySelect();await setZoomOn(page,2);assert.equal(await page.evaluate(()=>getComputedStyle(document.documentElement).fontSize),'16px');
    await projection('native200');await captureSections('native200');await traces(page,'native200');await reachableTargets(page,'native200',targets);await nativeTableReading(page,'native200');
    await setZoomOn(page,1);await page.evaluate(()=>document.documentElement.style.fontSize='200%');assert.equal(await page.evaluate(()=>getComputedStyle(document.documentElement).fontSize),'32px');
    await projection('rootfont200');await captureSections('rootfont200');await traces(page,'rootfont200');await reachableTargets(page,'rootfont200',targets);await nativeTableReading(page,'rootfont200');
    check('two-separate-actual-browser-200-percent-modes');
}
async function noJS() {
    await querySelect();await traces();await page.setViewportSize({width:320,height:800});await nativeTableReading();await captureSections('noJS-320');
    await open(r.selected_href);save('noJS-fresh-document-entry.json',await page.evaluate(()=>({x:scrollX,y:scrollY,activeTag:document.activeElement.tagName})));await continuousKeyboard(page,'noJS-320');
    const button=page.locator(form+' button'),link=page.locator(search+' li a').first();
    await button.focus();await page.keyboard.press('Tab');assert(await link.evaluate(e=>e===document.activeElement));
    await emptyAndName();check('normal-authentication-same-JS-disabled-context-native-GET-link-details-keyboard',{session_copied:false});
}
async function permissions() {
    const allowed=alias!=='none';const response=await page.goto(base+'/ydental/settlement',{waitUntil:'domcontentloaded'});assert.equal(response.status(),allowed?200:403);
    if(!allowed){save('real-no-source-permission-denial.json',{status:response.status(),body:await page.locator('body').innerText(),guard_blocks:r.guard_blocks||[]});await shot('actual-no-source-403');const other=await page.goto(base+'/ydental/settlement/other-stores/'+(sample.selected_patient_id||655),{waitUntil:'domcontentloaded'});assert.equal(other.status(),403);save('real-no-source-other-store-denial.json',{status:other.status(),body:await page.locator('body').innerText(),actual_backend_response:true,guard_blocks:r.guard_blocks||[]});await shot('actual-no-source-other-store-403');check('real-no-source-main-and-other-store-403',{temporary_grants:0,preinterception:false});return;}
    await ready();
    const cases=[['invalid-text','/ydental/settlement?patient_id=not-a-number',400],['invalid-negative','/ydental/settlement?patient_id=-1',400],['unknown-patient','/ydental/settlement?patient_id=2147483647',403]];
    if(sample.unrelated_patient_id){cases.push(['unrelated-patient','/ydental/settlement?patient_id='+sample.unrelated_patient_id,403]);cases.push(['unrelated-other-store-summary','/ydental/settlement/other-stores/'+sample.unrelated_patient_id,403]);}else throw Error('T06 requires an existing cross-store unrelated patient sample independently verified read-only');
    for(const [name,url,status]of cases){const res=await page.goto(base+url,{waitUntil:'domcontentloaded'});assert.equal(res.status(),status);save('permission-'+name+'.json',{path:url,status:res.status(),body:await page.locator('body').innerText(),actual_backend_response:true,temporary_grants:0});await shot('actual-'+name+'-'+status);}
    check('real-native-backend-denials-no-client-substitute',{cases,temporary_grants:0});
}
async function genericSnapshot() {
    return page.locator('body').evaluate(body=>{
        const m=body.querySelector('main')||body;
        const keys=['display','fontSize','fontWeight','lineHeight','color','backgroundColor','borderColor','borderWidth','borderRadius','padding','margin','gap','minHeight'];
        const clone=m.cloneNode(true),defaults=[];
        for(const e of [clone,...clone.querySelectorAll('[data-revision]')])if(e.hasAttribute('data-revision'))e.setAttribute('data-revision','<PRIVATE_NATIVE_REVISION>');
        const queried=clone.querySelector('.o_ydental_reporting_scope > p:nth-of-type(3)');if(queried){const matches=[...queried.innerHTML.matchAll(/\d{4}-\d\d-\d\d \d\d:\d\d:\d\d/g)];if(matches.length!==1)throw Error('Unique native query_at_utc field required');defaults.push({field:'report.filters.query_at_utc',value:matches[0][0]});queried.innerHTML=queried.innerHTML.replace(matches[0][0],'<NATIVE_QUERY_AT_UTC>');}
        for(const x of clone.querySelectorAll('input'))if(['csrf_token','revision','key'].includes(x.name))x.setAttribute('value','<PRIVATE_NATIVE_BINDING>');
        return {html:clone.outerHTML,nodes:[m,...m.querySelectorAll('*')].map(e=>({tag:e.tagName,style:Object.fromEntries(keys.map(k=>[k,getComputedStyle(e)[k]]))})),p12:m.querySelectorAll('[data-dl-actions="settlement-readonly-actions"]').length,defaults};
    });
}
async function bypass() {
    const paths=alias==='warehouse'?['/ydental/inventory']:alias==='doctor'?['/ydental/documents']:alias==='group_manager'?['/ydental/reports?metric=collections&date_from=2026-10-01&date_to=2026-10-26&store_ids=1&page=1','/ydental/patients']:['/ydental/settlement?patient_id=2147483647'];
    for(let i=0;i<paths.length;i++) {
        const url=paths[i],res=await page.goto(base+url,{waitUntil:'domcontentloaded'});await settle();
        const value=await genericSnapshot();assert.equal(value.p12,0);const name='bypass-'+alias+'-'+i;
        save(name+'.json',{status:res.status(),...value});await shot(name);
        if(stage==='after'&&arg('before-result')){const old=JSON.parse(fs.readFileSync(path.join(dirOf(arg('before-result')),name+'.json')));assert.deepEqual({...value,status:res.status(),defaults:[]},{...old,defaults:[]});}
        check('limited-unaffected-bypass-'+i,{url,status:res.status(),business_submit:false});
        if(alias==='group_manager'&&i===0) {
            const a=page.locator('.o_ydental_reporting_table_wrap tbody a').first();assert(await a.count());const href=await a.getAttribute('href');await page.goto(base+href,{waitUntil:'domcontentloaded'});await settle();
            const source=await genericSnapshot();assert.equal(source.p12,0);save('bypass-report-source.json',source);await shot('bypass-report-source');
            if(stage==='after'&&arg('before-result')){
                const old=JSON.parse(fs.readFileSync(path.join(dirOf(arg('before-result')),'bypass-report-source.json')));
                assert.deepEqual({...source,defaults:[]},{...old,defaults:[]});
            }
        }
    }
}

async function states(p=page) {
    const values=[];
    for(const kind of ['primary','secondary','quiet','disclosure']) {
        const target=p.locator(scope+' button,'+scope+' a,'+scope+' summary');
        const candidates=await target.all();let selected;
        for(const e of candidates)if((await e.getAttribute('class')||'').includes(kind)){selected=e;break;}
        assert(selected,'Rendered action family '+kind+' required');
        await selected.evaluate(e=>e.scrollIntoView({block:'center',inline:'nearest'}));await p.mouse.move(0,0);
        values.push({kind,state:'default',value:contrast(await selected.evaluate(computed),kind!=='quiet')});
        await selected.hover();values.push({kind,state:'hover',value:contrast(await selected.evaluate(computed),kind!=='quiet')});
        const b=await selected.boundingBox();await p.mouse.move(b.x+b.width/2,b.y+b.height/2);await p.mouse.down();
        values.push({kind,state:'active',value:contrast(await selected.evaluate(computed),kind!=='quiet')});
        await p.mouse.move(0,0);await p.mouse.up();await p.keyboard.press('Tab');await selected.focus();
        values.push({kind,state:'focus',value:contrast(await selected.evaluate(computed),kind!=='quiet',true)});
    }
    save('four-action-families-four-actual-states.json',values);check('four-action-families-four-states-text4.5-boundary-focus3',{layer:p===page?'ACTUAL_PRODUCT_BROWSER':'ACTUAL_LOADED_QWEB_MEMORY_COMPONENT'});
}
async function componentRanges(p,name) {
    const selector=scope+' h2,'+scope+' label,'+scope+' p,'+scope+' li a,'+scope+' th,'+scope+' td';
    for(const d of await p.locator(scope+' details').all())if(!await d.evaluate(e=>e.open))await d.locator('summary').press('Enter');
    const ranges=await fixtureReach(p,selector);save(name+'-component-ranges.json',ranges);
}
async function components() {
    await querySelect();
    const fixtureFile=arg('fixture-file');assert(fixtureFile);const fixture=JSON.parse(fs.readFileSync(fixtureFile));
    assert.equal(fixture.components.length,4);assert.equal(fixture.database_writes,false);assert.equal(fixture.rollback_performed,true);
    const assetBindings=await page.locator('head link[rel=stylesheet],head style').evaluateAll(xs=>xs.map(e=>{
        const clone=e.cloneNode(true);if(e.tagName==='LINK')clone.setAttribute('href',e.href);
        return {tag:e.tagName,href:e.tagName==='LINK'?e.href:null,loaded:e.tagName==='STYLE'||e.sheet!==null,html:clone.outerHTML};
    }));
    assert(assetBindings.length&&assetBindings.every(x=>x.loaded));
    assert(assetBindings.filter(x=>x.href).every(x=>new URL(x.href).origin===base),'Only actual same-origin product CSS is copied');
    const styles=assetBindings.map(x=>x.html).join('\n');save('component-product-css-asset-bindings.json',assetBindings);
    r.fixture_input={file:fixtureFile,sha256:hash(fixtureFile),loaded_candidate:fixture.candidate_commit,layer:fixture.layer};
    for(const item of fixture.components) {
        assert.equal(sha(item.html),item.html_sha256);assert.equal(item.business_records_created,0);
        const p=await context.newPage(),cssResponses=[];p.on('response',response=>{if(response.request().resourceType()==='stylesheet')cssResponses.push(response)});
        await p.setContent('<!doctype html><html lang="zh-CN"><head><meta charset="utf-8">'+styles+'</head><body><main class="container py-4 o_ydental_settlement">'+item.html+'</main></body></html>',{waitUntil:'load'});
        await settle(p);
        const actualCSS=[];for(const response of cssResponses){assert.equal(response.status(),200);const bytes=await response.body();actualCSS.push({url:response.url(),status:response.status(),bytes:bytes.length,sha256:sha(bytes)});}
        assert.equal(actualCSS.length,assetBindings.filter(x=>x.href).length);
        const cssFacts=await p.locator(scope).evaluate(e=>({display:getComputedStyle(e).display,padding:getComputedStyle(e).padding,font:getComputedStyle(e).fontSize,background:getComputedStyle(e).backgroundColor,links:[...document.querySelectorAll('head link[rel=stylesheet]')].map(e=>({href:e.href,loaded:e.sheet!==null}))}));
        assert.equal(cssFacts.display,'grid');assert.equal(cssFacts.background,'rgb(255, 251, 246)');assert(cssFacts.links.every(x=>x.loaded));
        save('fixture-'+item.name+'-actual-product-css.json',{assets:actualCSS,computed:cssFacts,style_injection_or_repair:false,head_link_hrefs_resolved_against_original_product_page:true});
        await p.route('**/*',route=>route.abort());
        await p.locator('a').evaluateAll(xs=>xs.forEach(e=>e.addEventListener('click',event=>event.preventDefault())));
        const original=await p.evaluate(tools.projection);
        assert.equal(original.candidate_count,item.patient_options.rows.length);assert.equal(original.form.fields[0].value,item.search_term);
        assert.deepEqual(original.candidates,item.patient_options.rows.map(x=>({text:x.name+' · '+x.number,href:'/ydental/settlement?patient_id='+x.id})));
        for(const expected of item.expected_fees) {
            const actual=original.fees.find(x=>x.kind===expected.kind);assert.equal(actual.rows.length,expected.row_count);
            if(expected.row_count)for(let i=0;i<expected.original_cell_values.length;i++)assert(actual.rows[0][i].includes(expected.original_cell_values[i]));
            if(item.paged)assert.deepEqual(actual.pages[0].links.map(x=>x.href),[expected.expected_previous_href,expected.expected_next_href]);
            else assert.equal(actual.pages.length,0);
        }
        if(item.paged)assert.deepEqual(original.search_pages.map(x=>x.href),[item.expected_search_previous_href,item.expected_search_next_href]);
        for(const [width,height]of views) {
            await p.setViewportSize({width,height});await settle(p);await projection('fixture-'+item.name+'-'+width,p);
            await captureSections('fixture-'+item.name+'-'+width,p);await componentRanges(p,'fixture-'+item.name+'-'+width);
            await reachableTargets(p,'fixture-'+item.name+'-'+width,targets);await nativeTableReading(p,'fixture-'+item.name+'-'+width);
            if(width===320){
                const k=await context.newPage(),responses=[];k.on('response',x=>{if(x.request().resourceType()==='stylesheet')responses.push(x)});
                await k.setViewportSize({width:320,height:800});
                await k.setContent('<!doctype html><html lang="zh-CN"><head><meta charset="utf-8">'+styles+'</head><body><main class="container py-4 o_ydental_settlement">'+item.html+'</main></body></html>',{waitUntil:'load'});await settle(k);
                const actual=[];for(const response of responses){assert.equal(response.status(),200);const bytes=await response.body();actual.push({url:response.url(),status:response.status(),bytes:bytes.length,sha256:sha(bytes)});}
                assert.deepEqual(actual,actualCSS,'Fresh keyboard component uses identical actual product stylesheet bytes');
                const start=await k.evaluate(()=>({x:scrollX,y:scrollY,rootFont:getComputedStyle(document.documentElement).fontSize,rootScroll:document.documentElement.scrollWidth,rootClient:document.documentElement.clientWidth}));
                save('fixture-'+item.name+'-fresh-keyboard-document.json',{layer:'LOADED_QWEB_MEMORY_COMPONENT_NEW_DOCUMENT',source_html_sha256:item.html_sha256,actualCSS:actual,start,real_identity_or_permission_claimed:false,helper_scroll_used:false});assert.equal(start.y,0);
                await k.locator('a').evaluateAll(xs=>xs.forEach(e=>e.addEventListener('click',event=>event.preventDefault())));
                await continuousKeyboard(k,'fixture-'+item.name+'-320-fresh');await k.close();
            }
        }
        if(item.name==='empty-unselected') {
            await p.setViewportSize({width:1366,height:768});await setZoomOn(p,2);
            assert.equal(await p.evaluate(()=>getComputedStyle(document.documentElement).fontSize),'16px');
            await projection('fixture-empty-unselected-native200',p);
            await p.locator(search).evaluate(e=>e.scrollIntoView({block:'start',inline:'nearest'}));await shot('fixture-empty-unselected-native200-search',p,'ACTUAL_LOADED_QWEB_MEMORY_COMPONENT_NEW_ZOOM_SAMPLE_NO_BEFORE');
            await p.locator(search+' > .o_ydental_settlement_empty').evaluate(e=>e.scrollIntoView({block:'center',inline:'nearest'}));await shot('fixture-empty-unselected-native200-empty',p,'ACTUAL_LOADED_QWEB_MEMORY_COMPONENT_NEW_ZOOM_SAMPLE_NO_BEFORE');
            await setZoomOn(p,1);await p.evaluate(()=>document.documentElement.style.fontSize='200%');
            assert.equal(await p.evaluate(()=>getComputedStyle(document.documentElement).fontSize),'32px');
            await projection('fixture-empty-unselected-rootfont200',p);
            await p.locator(search).evaluate(e=>e.scrollIntoView({block:'start',inline:'nearest'}));await shot('fixture-empty-unselected-rootfont200-search',p,'ACTUAL_LOADED_QWEB_MEMORY_COMPONENT_NEW_ZOOM_SAMPLE_NO_BEFORE');
            await p.locator(search+' > .o_ydental_settlement_empty').evaluate(e=>e.scrollIntoView({block:'center',inline:'nearest'}));await shot('fixture-empty-unselected-rootfont200-empty',p,'ACTUAL_LOADED_QWEB_MEMORY_COMPONENT_NEW_ZOOM_SAMPLE_NO_BEFORE');
            await p.evaluate(()=>document.documentElement.style.fontSize='');await setZoomOn(p,1);
            check('loaded-empty-both-actual-zoom-modes-new-samples',{before_claimed:false});
        }
        await traces(p,'fixture-'+item.name);
        if(item.name==='two-way-pagination'&&stage==='after'){await states(p);await paginationEvents(p,item.name);}
        if(item.long_text) {
            await p.setViewportSize({width:1366,height:768});await setZoomOn(p,2);
            assert.equal(await p.evaluate(()=>getComputedStyle(document.documentElement).fontSize),'16px');
            await projection('fixture-'+item.name+'-native200',p);await componentRanges(p,'fixture-'+item.name+'-native200');
            await reachableTargets(p,'fixture-'+item.name+'-native200',targets);await captureSections('fixture-'+item.name+'-native200',p);
            await setZoomOn(p,1);await p.evaluate(()=>document.documentElement.style.fontSize='200%');
            assert.equal(await p.evaluate(()=>getComputedStyle(document.documentElement).fontSize),'32px');
            await projection('fixture-'+item.name+'-rootfont200',p);await componentRanges(p,'fixture-'+item.name+'-rootfont200');
            await reachableTargets(p,'fixture-'+item.name+'-rootfont200',targets);await captureSections('fixture-'+item.name+'-rootfont200',p);
            await p.evaluate(()=>document.documentElement.style.fontSize='');
        }
        for(const fault of ['missing-SVG','missing-CSS']) {
            const f=await context.newPage();await f.setContent('<!doctype html><html lang="zh-CN"><head>'+(fault==='missing-CSS'?'':styles)+'</head><body><main class="container py-4 o_ydental_settlement">'+item.html+'</main></body></html>',{waitUntil:'load'});await settle(f);
            if(fault==='missing-SVG')await f.locator('svg').evaluateAll(xs=>xs.forEach(e=>e.remove()));
            assert((await f.locator(scope+' button,'+scope+' a,'+scope+' summary').allTextContents()).every(x=>x.trim().length));
            const summary=f.locator(scope+' summary').first();if(await summary.count()){await summary.press('Enter');assert(await summary.evaluate(e=>e.parentElement.open));await summary.press('Space');}
            await shot('fixture-'+item.name+'-'+fault,f,'EXPLICIT_FAULT_COMPONENT');await f.close();
        }
        await p.close();check('loaded-QWeb-explicit-component-'+item.name,{real_identity_or_authorization_claimed:false,business_created:0});
    }
}


async function clickPoint(target,kind) {
    await target.evaluate(e=>e.scrollIntoView({block:'center',inline:'nearest'}));
    return target.evaluate((e,kind)=>{
        const b=e.getBoundingClientRect();let x,y,glyph=null;
        if(kind==='icon') {
            const child=e.querySelector('svg');if(!child)throw Error('Expected original SVG target');
            const c=child.getBoundingClientRect();x=c.left+c.width/2;y=c.top+c.height/2;
        } else if(kind==='text') {
            const child=e.querySelector('.o_ydental_settlement_action_label')||e.querySelector('span')||e;
            const walk=document.createTreeWalker(child,NodeFilter.SHOW_TEXT);let node;
            for(let n=walk.nextNode();n;n=walk.nextNode())if(n.textContent.trim()){node=n;break;}
            if(!node)throw Error('Original action needs visible text');
            const offset=node.textContent.search(/\S/u),range=document.createRange();range.setStart(node,offset);range.setEnd(node,offset+1);
            const c=range.getBoundingClientRect();if(c.width<=0||c.height<=0)throw Error('Original first text glyph has no positive Range');
            x=c.left+c.width/2;y=c.top+c.height/2;glyph={character:node.textContent[offset],rect:c.toJSON(),owner_tag:node.parentElement.tagName};
            const hit=document.elementFromPoint(x,y);if(!(hit===node.parentElement||node.parentElement.contains(hit)))throw Error('Text click did not hit the original glyph owner');
        } else {
            for(const fy of [.5,.25,.75,.15,.85])for(const fx of [.04,.96,.1,.9,.25,.75,.5]) {
                const xx=b.left+b.width*fx,yy=b.top+b.height*fy;
                if(document.elementFromPoint(xx,yy)===e){x=xx;y=yy;break;}
            }
            if(x===undefined)throw Error('Original control has no empty padding point');
        }
        const hit=document.elementFromPoint(x,y);
        if(!(hit===e||e.contains(hit)))throw Error('Hit test escaped original control');
        return {x,y,kind,glyph,tag:e.tagName,text:e.textContent.trim(),href:e.getAttribute('href'),hit_tag:hit.tagName,hit_class:typeof hit.className==='string'?hit.className:null,box:b.toJSON()};
    },kind);
}
async function clickedEvent(p,target,kind,{component=false}={}) {
    const events=[],listener=message=>{if(message.text().startsWith('P12_TRUSTED_ACTION:'))events.push(JSON.parse(message.text().slice('P12_TRUSTED_ACTION:'.length)))};
    p.on('console',listener);
    await target.evaluate((e,component)=>e.addEventListener('click',event=>{
        if(component)event.preventDefault();
        console.debug('P12_TRUSTED_ACTION:'+JSON.stringify({isTrusted:event.isTrusted,tag:e.tagName,text:e.textContent.trim(),href:e.getAttribute('href'),form_action:e.form?.getAttribute('action')||null,form_method:e.form?.method||null,hit_tag:event.target.tagName,original_control_in_composed_path:event.composedPath().includes(e),composed_path_tags:event.composedPath().filter(x=>x.tagName).map(x=>x.tagName),default_prevented:event.defaultPrevented,component_prevent_default:component}));
    },{once:true}),component);
    const point=await clickPoint(target,kind);const before=r.requests.length;
    if(component)await p.mouse.click(point.x,point.y);else await nav(()=>p.mouse.click(point.x,point.y),point.href===null||!point.href.includes('/other-stores/'));
    await p.waitForTimeout(100);p.off('console',listener);
    assert.equal(events.length,1);assert(events[0].isTrusted&&events[0].original_control_in_composed_path);
    if(component){assert(events[0].component_prevent_default&&events[0].default_prevented);assert.equal(r.requests.length,before,'Component event must not dispatch actual business GET');}
    return {point,event:events[0],component};
}
async function actionEvents() {
    await querySelect();const records=[];
    for(const kind of ['icon','text','blank']) {
        await open();await page.locator(form+' [name=q]').fill(r.selected_business_number);
        const n=count(),target=page.locator(form+' button'),value=await clickedEvent(page,target,kind);
        assert.equal(count(),n+1);const v=await page.evaluate(tools.projection);
        assert.deepEqual(v.query,[['q',r.selected_business_number]]);assert.equal(v.other_stores.length,0);assert(v.candidates.length);
        records.push({family:'primary_search',kind,one_original_GET:true,candidates_only:true,...value});
    }
    for(const kind of ['text','blank']) {
        await open('/ydental/settlement?q='+encodeURIComponent(r.selected_business_number));
        const target=page.locator(search+' li a').first();assert.equal(await target.locator('svg').count(),0);
        const href=await target.getAttribute('href'),n=count(),value=await clickedEvent(page,target,kind);
        assert.equal(count(),n+1);assert.equal(new URL(page.url()).searchParams.get('patient_id'),new URL(href,base).searchParams.get('patient_id'));
        records.push({family:'quiet_patient_candidate',kind,one_original_GET:true,...value});
    }
    for(const kind of ['icon','text','blank']) {
        await open(r.selected_href);const target=page.locator(scope+' a[href^="/ydental/settlement/other-stores/"]');
        const href=await target.getAttribute('href'),n=r.requests.filter(x=>x.path.startsWith('/ydental/settlement/other-stores/')).length;
        const value=await clickedEvent(page,target,kind);
        assert.equal(r.requests.filter(x=>x.path.startsWith('/ydental/settlement/other-stores/')).length,n+1);
        assert.equal(new URL(page.url()).pathname,href);assert.equal(r.responses.filter(x=>x.path===href).at(-1).status,200);
        records.push({family:'quiet_other_store_minimal_summary',kind,one_original_GET:true,no_store_switch:true,...value});
    }
    save('actual-icon-text-blank-original-GET-events.json',records);await shot('actual-other-store-event-target');
    check('actual-primary-quiet-icon-text-blank-one-original-GET',{cases:records.length,business_submit:false});
}
async function paginationEvents(p,name) {
    const links=[];for(const a of await p.locator(scope+' a').all())if((await a.getAttribute('class')||'').includes('secondary'))links.push(a);
    assert.equal(links.length,8,'Two candidate and six fee previous/next original links');const values=[];
    for(const a of links)for(const kind of ['icon','text','blank'])values.push({fixture:name,...await clickedEvent(p,a,kind,{component:true})});
    save('component-pagination-icon-text-blank-events.json',{layer:'EXPLICIT_LOADED_QWEB_COMPONENT_TRUSTED_EVENTS_NOT_HTTP',values,actual_GET_success_claimed:false,real_multipage_business_claimed:false});
    check('loaded-component-secondary-eight-links-icon-text-blank-original-anchor',{cases:values.length,actual_GET_success_claimed:false});
}

async function touchOriginalHistory(){
    assert.equal(engine,'chromium');r.touch_layer='CHROMIUM_CDP_EMULATED_TRUSTED_TOUCH_NOT_PHYSICAL_DEVICE';
    await open('/ydental/settlement?patient_id='+sample.selected_patient_id);await page.bringToFront();await page.setViewportSize({width:390,height:844});await page.waitForTimeout(300);
    const v=await page.evaluate(()=>({width:innerWidth,height:innerHeight,font:getComputedStyle(document.documentElement).fontSize,dpr:devicePixelRatio}));assert.deepEqual(v,{width:390,height:844,font:'16px',dpr:1});
    const region=page.locator(scope+' [data-fee-kind="history"] .o_ydental_settlement_fee_scroll');await region.evaluate(e=>e.scrollIntoView({block:'center',inline:'nearest'}));await region.focus();
    for(let i=0;i<100;i++){if(await region.evaluate(e=>e.scrollLeft)<=.5)break;await page.keyboard.press('ArrowLeft');await page.waitForTimeout(30);}
    await region.evaluate(e=>{window.__a04TouchEvents=[];for(const type of ['touchstart','touchmove','touchend','touchcancel'])e.addEventListener(type,event=>window.__a04TouchEvents.push({type,trusted:event.isTrusted,touches:event.touches.length,prevented:event.defaultPrevented}),{passive:true})});
    const observe=()=>region.evaluate(e=>({left:e.scrollLeft,top:e.scrollTop,max:e.scrollWidth-e.clientWidth,rootX:scrollX,rootY:scrollY,active:document.activeElement.tagName,clip:e.getBoundingClientRect().toJSON()}));
    const before=await observe(),header=await region.locator('th').last().boundingBox(),box=await region.boundingBox();assert(header&&box);
    const x=box.x+box.width-20,y=Math.max(box.y+8,Math.min(box.y+35,833)),distance=Math.min(180,box.width-70),cdp=await context.newCDPSession(page);
    await cdp.send('Emulation.setTouchEmulationEnabled',{enabled:true,maxTouchPoints:1});await cdp.send('Input.dispatchTouchEvent',{type:'touchStart',touchPoints:[{x,y,id:0,radiusX:1,radiusY:1,force:.5}]});
    for(let i=1;i<=12;i++){await cdp.send('Input.dispatchTouchEvent',{type:'touchMove',touchPoints:[{x:x-distance*i/12,y,id:0,radiusX:1,radiusY:1,force:.5}]});await page.waitForTimeout(35);}
    await cdp.send('Input.dispatchTouchEvent',{type:'touchEnd',touchPoints:[]});await page.waitForTimeout(500);await cdp.send('Emulation.setTouchEmulationEnabled',{enabled:false});await cdp.detach();
    const after=await observe(),events=await page.evaluate(()=>window.__a04TouchEvents);r.touch_observation={layer:r.touch_layer,setup:{actual_viewport:v,initial_horizontal_keyboard_to_zero:true,pan_within_original_table_header:true},before,after,events,observed_horizontal_pan:after.left>before.left,real_hardware_or_WebKit_touch_claimed:false};save('emulated-touch-original-history.json',r.touch_observation);await shot('emulated-touch-original-history');assert(events.length&&events.every(e=>e.trusted));assert.equal(after.rootX,before.rootX);assert.equal(after.rootY,before.rootY);if(after.left>before.left)check('trusted-Chromium-emulated-touch-local-horizontal-pan',{real_device:false});
}
async function a04Lifecycle(p,item){
    assert(!nojs);const result=await Promise.race([p.evaluate(async html=>{
        const I=odoo.loader.modules.get('@ydental_settlement/fee_focus/fee_focus').SettlementFeeFocus;
        const {Colibri}=odoo.loader.modules.get('@web/public/colibri'),{Scope}=odoo.loader.modules.get('@odoo/owl');
        const frame=document.createElement('iframe');frame.style.width='768px';frame.style.height='1024px';frame.style.position='fixed';frame.style.top='0';frame.style.left='0';document.body.append(frame);
        const d=frame.contentDocument,styles=[...document.querySelectorAll('head link[rel=stylesheet],head style')].map(e=>{const c=e.cloneNode(true);if(e.tagName==='LINK')c.href=e.href;return c.outerHTML}).join('\n');
        d.open();d.write('<!doctype html><html><head>'+styles+'</head><body><main class="container py-4 o_ydental_settlement">'+html+'</main></body></html>');d.close();await d.fonts.ready;await new Promise(resolve=>setTimeout(resolve,300));
        const el=d.querySelector('[data-fee-kind="pending"] .o_ydental_settlement_fee_scroll'),summary=el.querySelector('summary');summary.parentElement.open=true;
        const core={env:{services:{}},createInteractionScope:()=>new Scope({pluginManager:{}})},records=[];
        const native=Object.getOwnPropertyDescriptor(Element.prototype,'scrollLeft');let writes=[];
        Object.defineProperty(el,'scrollLeft',{configurable:true,get(){return native.get.call(this)},set(value){writes.push({value,at:performance.now()});native.set.call(this,value)}});
        const wait=()=>new Promise(resolve=>setTimeout(resolve,100)),geometry=()=>({local:el.scrollLeft,rootX:frame.contentWindow.scrollX,rootY:frame.contentWindow.scrollY,active:d.activeElement===summary,frameRect:el.getBoundingClientRect().toJSON(),summaryRect:summary.getBoundingClientRect().toJSON()});
        const C=new Colibri(core,I,el);await C.start();
        summary.focus({preventScroll:true});await wait();writes=[];C.interaction.queueReveal(summary);await wait();records.push({name:'already_complete_no_scrollLeft_write',actual_writes:[...writes],passed:writes.length===0,geometry:geometry()});
        native.set.call(el,36);writes=[];const before=geometry();C.interaction.queueReveal(summary);await wait();const after=geometry();records.push({name:'only_needed_local_horizontal_write',before,after,actual_writes:[...writes],passed:writes.length===1&&after.local<before.local&&after.rootX===before.rootX&&after.rootY===before.rootY&&after.active});
        native.set.call(el,36);writes=[];C.interaction.queueReveal(summary);C.interaction.cancelReveal();await wait();records.push({name:'explicit_cancel_method_cancels_two_frames',actual_writes:[...writes],frame:C.interaction.frame,passed:writes.length===0&&C.interaction.frame===0});
        native.set.call(el,36);writes=[];el.focus({preventScroll:true});summary.focus({preventScroll:true});el.focus({preventScroll:true});await wait();records.push({name:'actual_focusin_then_focusout_event_cancels_two_frames',actual_writes:[...writes],frame:C.interaction.frame,region_active:d.activeElement===el,passed:writes.length===0&&C.interaction.frame===0&&d.activeElement===el});
        native.set.call(el,36);writes=[];C.interaction.queueReveal(summary);C.destroy();await wait();records.push({name:'actual_colibri_cleanup_cancels_pending_frames',actual_writes:[...writes],frame:C.interaction.frame,stopped:C.interaction.stopped,cleanups:C.cleanups.length,passed:writes.length===0&&C.interaction.stopped&&C.interaction.frame===0&&C.cleanups.length===0});
        let adds=0,removes=0;const add=el.addEventListener.bind(el),remove=el.removeEventListener.bind(el);el.addEventListener=(...args)=>{adds++;return add(...args)};el.removeEventListener=(...args)=>{removes++;return remove(...args)};
        const F=new Colibri(core,I,el),originalAdd=F.addListener.bind(F);let calls=0;F.addListener=(...args)=>{calls++;if(calls===2)throw Error('EXPLICIT_A04_COMPONENT_SECOND_LISTENER_INITIALIZATION_FAILURE');return originalAdd(...args)};await F.start();
        const failedStart={name:'initialization_failure_removes_first_real_listener',adds,removes,stopped:F.interaction.stopped,first:F.interaction.removeFocusIn===undefined,second:F.interaction.removeFocusOut===undefined,passed:adds===1&&removes>=1&&F.interaction.stopped};F.destroy();records.push(failedStart);
        delete el.scrollLeft;frame.remove();return{layer:'EXPLICIT_COMPONENT_REAL_LOADED_PRODUCT_CLASS_REAL_COLIBRI_AND_REAL_OWL_SCOPE',ordinary_role_or_native_keyboard_claimed:false,metadata:'actual Colibri class; minimal services env and actual Owl Scope; controlled initialization failure only in component',module:'@ydental_settlement/fee_focus/fee_focus',records};
    },item.html),p.waitForTimeout(10000).then(()=>{throw Error('Bounded component lifecycle timeout')})]);
    save('actual-class-Colibri-lifecycle.json',result);assert(result.records.every(x=>x.passed),'Actual loaded class lifecycle and no-jump component branches');check('actual-class-Colibri-lifecycle-components',{count:result.records.length,layer:result.layer});
}

async function a04Components() {
    r.javascript_enabled=!nojs;r.component_startup='ORIGINAL_AUTHENTICATED_GET_FULL_DOCUMENT_WITH_ONLY_LOOKUP_REPLACED_IN_MEMORY_NORMAL_FRONTEND_BUNDLE_STARTUP';
    await open('/ydental/settlement?patient_id='+sample.selected_patient_id);
    const fixture=JSON.parse(fs.readFileSync(arg('fixture-file')));assert.equal(fixture.database_writes,false);assert.equal(fixture.rollback_performed,true);
    const suite=arg('a04-suite')||'strict', normal='selected-three-sections';r.a04_suite=suite;r.cases=[];
    const complete=v=>v.focus.active&&v.focus.focusVisible&&v.focus.outline_reachable&&v.focus.not_clipped;
    async function normalComponent(item,width,height,zoomKind='normal'){
        assert.equal(sha(item.html),item.html_sha256);
        const p=await context.newPage(),assets=[],pageErrors=[],consoleErrors=[];p.on('pageerror',e=>pageErrors.push({class:e.constructor.name,message:String(e.message).slice(0,500)}));p.on('console',e=>{if(e.type()==='error')consoleErrors.push({type:e.type(),location:e.location(),message:String(e.text()).slice(0,300)})});
        const lazyFaults=[];if(suite==='fault')await p.route('**/web/assets/**/web.assets_frontend_lazy*.js',route=>{lazyFaults.push({path:new URL(route.request().url()).pathname,kind:'EXPLICIT_STATIC_RESOURCE_FAILURE_NOT_PERMISSION_OR_BUSINESS_RESPONSE'});return route.abort('failed')});p.__a04Requests=[];p.on('request',x=>p.__a04Requests.push({at:new Date().toISOString(),path:new URL(x.url()).pathname,method:x.method(),resource:x.resourceType()}));p.on('response',x=>{if(['script','stylesheet'].includes(x.request().resourceType()))assets.push(x)});
        await p.setViewportSize({width,height});
        let replaced=0;
        await p.route(base+'/ydental/settlement?patient_id='+sample.selected_patient_id,async route=>{
            const response=await route.fetch();assert.equal(response.status(),200);
            const body=await page.evaluate(({html,replacement,lookupOnly})=>{const d=new DOMParser().parseFromString(html,'text/html'),old=d.querySelector('[data-dl-scope="settlement-lookup"]'),t=d.createElement('template');if(!old)throw Error('Unique original lookup missing');t.innerHTML=replacement;if(t.content.children.length!==1)throw Error('One loaded lookup required');const replacementRoot=t.content.firstElementChild;if(lookupOnly){const main=old.closest('main.o_ydental_settlement');if(!main)throw Error('Original settlement main missing');main.replaceChildren(replacementRoot);}else old.replaceWith(replacementRoot);return '<!doctype html>\n'+d.documentElement.outerHTML},{html:await response.text(),replacement:item.html,lookupOnly:suite==='paired'});
            // Full HTML carries native CSRF/session-related fields only in
            // memory; it is never written, logged or packaged.
            replaced++;await route.fulfill({response,body});
        });
        await p.bringToFront();await p.goto(base+'/ydental/settlement?patient_id='+sample.selected_patient_id,{waitUntil:'load'});assert.equal(replaced,1);await p.bringToFront();await p.waitForTimeout(1000);save('bootstrap-'+r.cases.length+'-'+item.name+'-'+width+'-'+zoomKind+'.json',{pageErrors,consoleErrors,jsOffConfigured:nojs,state:await p.evaluate(()=>({bodyClass:document.body.className,ready:document.body.getAttribute('is-ready'),documentState:document.readyState,hasOdoo:!!window.odoo,hasLoader:!!window.odoo?.loader,modules:window.odoo?.loader?[...odoo.loader.modules.keys()].filter(k=>k.includes('fee_focus')):[],scripts:[...document.scripts].map(s=>({src:s.src?new URL(s.src).pathname:null,type:s.type,async:s.async,defer:s.defer,inlineCharacters:s.src?0:s.textContent.length,hasOdooBootstrap:s.textContent.includes('odoo')}))}))});
        if(!nojs&&suite!=='fault'){await p.locator('body[is-ready="true"]').waitFor({state:'attached'});await p.waitForFunction(()=>!!odoo?.loader?.modules?.get('@ydental_settlement/fee_focus/fee_focus'));}
        await settle(p);await p.bringToFront();
        if(!nojs)await setZoomOn(p,1);await p.evaluate(()=>document.documentElement.style.fontSize='');if(zoomKind==='native200')await setZoomOn(p,2);
        if(zoomKind==='root200')await p.evaluate(()=>document.documentElement.style.fontSize='200%');
        await p.waitForTimeout(250);const actualViewport=await p.evaluate(()=>({width:innerWidth,height:innerHeight,rootFont:getComputedStyle(document.documentElement).fontSize,dpr:devicePixelRatio})),expectedFactor=zoomKind==='native200'?2:1;assert(Math.abs(actualViewport.width-width/expectedFactor)<=1&&Math.abs(actualViewport.height-height/expectedFactor)<=1,'Actual viewport must match stated independent zoom mode');assert.equal(actualViewport.rootFont,zoomKind==='root200'?'32px':'16px');assert.equal(actualViewport.dpr,expectedFactor);save('viewport-'+r.cases.length+'-'+item.name+'-'+width+'-'+zoomKind+'.json',{requested:{width,height,zoomKind},actual:actualViewport,native_reset_before_every_new_JS_on_page:true,root_font_reset_before_independent_mode:true});
        const loaded=[];for(const x of assets){if(!x.url().includes('/web/assets/'))continue;assert.equal(x.status(),200);const b=await x.body();loaded.push({path:new URL(x.url()).pathname,status:x.status(),resource:x.request().resourceType(),bytes:b.length,sha256:sha(b),contains_normal_A04_module:b.includes(Buffer.from('@ydental_settlement/fee_focus/fee_focus'))});}
        const registration=nojs?'NOT_EXECUTED_JS_DISABLED':await p.evaluate(()=>{const m=odoo.loader.modules.get('@ydental_settlement/fee_focus/fee_focus'),g=odoo.loader.modules.get('@web/core/registry')?.registry;return{loaded:!!m,registered:!!m&&m.SettlementFeeFocus===g?.category('public.interactions').get('ydental_settlement.fee_focus'),selector:m?.SettlementFeeFocus.selector,module_keys:Object.keys(m||{})}});
        if(!nojs&&suite!=='fault'){assert(registration.loaded&&registration.registered);assert(loaded.some(x=>x.contains_normal_A04_module));}if(suite==='fault'){save('explicit-lazy-resource-failure.json',{layer:'BROWSER_FIXTURE_NORMAL_HEAD_STATIC_LAZY_BUNDLE_ABORTED',lazyFaults,registration,pageErrors,consoleErrors,bodyready:await p.locator('body').getAttribute('is-ready'),backend_permission_denial_claimed:false});assert(lazyFaults.length>0&&!registration.loaded);}
        save('summary-AX-'+r.cases.length+'-'+item.name+'-'+width+'-'+zoomKind+'.json',{layer:'LOADED_QWEB_BROWSER_FIXTURE_NORMAL_FRONTEND',kind:suite==='paired'?'LOOKUP_ONLY_PAIRED_COMPONENT':'FULL_ORIGINAL_BODY_LOOKUP_REPLACEMENT',summaries:await p.locator(scope+' summary').evaluateAll(xs=>xs.map(e=>({tag:e.tagName,text:e.textContent.trim(),role:e.getAttribute('role'),ariaLabel:e.getAttribute('aria-label')}))),nativeAX:await p.locator(scope).ariaSnapshot()});return{p,loaded,registration};
    }
    async function oneCase(p,kind,opened,tag,exact36=false){
        const region=p.locator(scope+' [data-fee-kind="'+kind+'"] .o_ydental_settlement_fee_scroll'),summary=region.locator('summary').first();
        const observe=async()=>({at:new Date().toISOString(),focus:await focusSample(summary),local:await region.evaluate(e=>({left:e.scrollLeft,top:e.scrollTop,client:e.clientWidth,scroll:e.scrollWidth,active:e===document.activeElement,rootX:scrollX,rootY:scrollY})),contract:await summary.evaluate(e=>({tag:e.tagName,href:e.getAttribute('href'),tabindex:e.getAttribute('tabindex'),name:e.textContent.trim(),open:e.parentElement.open,tableMinWidth:getComputedStyle(e.closest('table')).minWidth,columns:[...e.closest('table').rows[0].cells].map(c=>({width:c.getBoundingClientRect().width,padding:getComputedStyle(c).padding})),ancestors:(()=>{const a=[];for(let n=e;n;n=n.parentElement){const s=getComputedStyle(n);if(['auto','scroll','hidden','clip'].includes(s.overflowX)||['auto','scroll','hidden','clip'].includes(s.overflowY))a.push({tag:n.tagName,class:n.className,box:n.getBoundingClientRect().toJSON(),client:n.clientWidth,scroll:n.scrollWidth,scrollLeft:n.scrollLeft,overflowX:s.overflowX,overflowY:s.overflowY});}return a})()}))});
        // Initial seed is the original region. Entering/opening the original
        // summary happens with trusted Tab/Enter/Shift+Tab, never .focus() on
        // the summary that is the acceptance target.
        if(tag.startsWith('paired-lookup-only-')){await summary.focus();const already=await summary.evaluate(e=>e.parentElement.open);if(already!==opened)await summary.press('Enter');await region.focus();}else{await region.focus();await p.keyboard.press('Tab');assert(await summary.evaluate(e=>e===document.activeElement));const isOpen=await summary.evaluate(e=>e.parentElement.open);if(isOpen!==opened)await p.keyboard.press('Enter');assert.equal(await summary.evaluate(e=>e.parentElement.open),opened);await p.keyboard.press('Shift+Tab');assert(await region.evaluate(e=>e===document.activeElement));}
        if(!nojs)await p.evaluate(()=>{window.__a04NativeKeys=[];document.addEventListener('keydown',e=>window.__a04NativeKeys.push({key:e.key,trusted:e.isTrusted,prevented:e.defaultPrevented}),{capture:true,once:false})});
        const initial=await observe(),arrows=[];
        for(let i=0;i<100;i++){const before=await observe();if(before.local.left>=before.local.scroll-before.local.client-1)break;await p.keyboard.press('ArrowRight');await p.waitForTimeout(90);arrows.push({key:'ArrowRight',before:before.local,after:(await observe()).local});}
        const retained=await observe();assert(retained.local.active);assert(retained.local.left>=retained.local.scroll-retained.local.client-1);
        if(exact36){assert.equal(retained.local.scroll-retained.local.client,36);assert.equal(retained.local.left,36);}
        const node=await summary.elementHandle(),networkStart=p.__a04Requests.length;await p.keyboard.press('Tab');const immediate=await observe();await p.waitForTimeout(100);const ms100=await observe();await p.waitForTimeout(300);const settled=await observe();await p.waitForTimeout(700);const stable1000=await observe();
        const identity=await node.evaluate(e=>({same_active:e===document.activeElement,still_connected:e.isConnected}));await node.dispose();
        const data={tag,kind,opened,setup_seed:tag.startsWith('paired-lookup-only-')?'EXACT_ORIGINAL_DIAGNOSTIC_SEED_summary_focus_then_Enter_then_region_focus_BEFORE_CRITICAL_ARROW_AND_TAB':'ORIGINAL_REGION_SEED_then_TRUSTED_TAB_ENTER_SHIFTTAB',layer:'LOADED_QWEB_BROWSER_FIXTURE_NORMAL_FRONTEND_STARTUP',javascript_enabled:!nojs,initial,arrows,retained,immediate,ms100,settled,stable1000,identity,native_pass:complete(settled)&&complete(stable1000),no_focus_or_recovery_helper_after_Tab:true,network_during_focus:p.__a04Requests.slice(networkStart),keys:nojs?'NOT_OBSERVED_JS_DISABLED':await p.evaluate(()=>window.__a04NativeKeys)};
        save(tag+'-strict-native-Tab.json',data);await shot(tag+'-strict-native-Tab',p,data.layer);r.cases.push({tag,kind,opened,native_pass:data.native_pass,strict_file:tag+'-strict-native-Tab.json'});
        assert(identity.same_active&&identity.still_connected);assert.equal(data.network_during_focus.length,0,'Focus visibility adjustment performs no network requests');assert.equal(stable1000.contract.tag,'SUMMARY');assert.equal(stable1000.contract.href,null);assert.equal(stable1000.contract.tabindex,null);
        assert.equal(initial.contract.name,stable1000.contract.name);assert.deepEqual(initial.contract.columns,stable1000.contract.columns);
        // Post-capture control checks cannot change the strict result above.
        const controls=[];for(const key of ['Enter','Space','Shift+Tab','Tab','ArrowRight','ArrowLeft']){const b=await observe();await p.keyboard.press(key);await p.waitForTimeout(220);controls.push({key,before:b,after:await observe()});}
        const rb=await region.boundingBox();await p.mouse.move(rb.x+rb.width/2,Math.min((await p.evaluate(()=>innerHeight))-5,rb.y+rb.height/2));const wheelBefore=await observe();await p.mouse.wheel(300,0);await p.waitForTimeout(400);const wheelAfter=await observe();
        const rest1=await observe();await p.waitForTimeout(500);const rest2=await observe();
        const controlsResult={controls,wheel:{before:wheelBefore,after:wheelAfter},rest_without_input:{before:rest1,after:rest2},not_a_repair_of_strict_capture:true};save(tag+'-postcapture-controls.json',controlsResult);
        assert(controls[0].after.contract.open!==controls[0].before.contract.open,'Original Enter toggles');assert.equal(controls[1].after.contract.open,controls[1].before.contract.open===false,'Original Space toggles');
        assert(controls[2].after.local.active&&!controls[2].after.focus.active,'ShiftTab returns original region');assert(controls[3].after.focus.active,'Tab returns same original summary');
        if(retained.local.scroll>retained.local.client){if(controls[4].before.local.left<retained.local.scroll-retained.local.client-.5)assert(controls[4].after.local.left>controls[4].before.local.left,'Original ArrowRight free after enhancer');if(controls[5].before.local.left>.5)assert(controls[5].after.local.left<controls[5].before.local.left,'Original ArrowLeft free after enhancer');if(wheelBefore.local.left<retained.local.scroll-retained.local.client-.5)assert(wheelAfter.local.left>wheelBefore.local.left,'Original horizontal wheel remains free');}
        assert.equal(rest1.local.left,rest2.local.left,'No repeated idle jump');
        if(!nojs&&suite!=='fault')assert(data.native_pass,'JS-on original focused summary whole text and full focus ring after stable native Tab');
        return data;
    }
    const normalItem=fixture.components.find(x=>x.name===normal);
    if(suite==='strict'){
        for(const opened of [true,false]){const x=await normalComponent(normalItem,768,1024);save('strict-'+opened+'-assets.json',{assets:x.loaded,registration:x.registration,source_html_sha256:normalItem.html_sha256,raw_response_not_saved:true});await oneCase(x.p,'pending',opened,'pending768-'+(opened?'open':'closed'),true);await x.p.close();}
    }else if(suite==='fault'){const x=await normalComponent(normalItem,768,1024);await oneCase(x.p,'pending',true,'missing-lazy-pending768-open',true);const fallback=await x.p.locator(scope).evaluate(e=>({text:e.textContent,form:{method:e.querySelector('form').method,action:e.querySelector('form').getAttribute('action'),maxlength:e.querySelector('[name=q]').getAttribute('maxlength')},candidates:[...e.querySelectorAll('li a')].map(a=>({tag:a.tagName,href:a.getAttribute('href'),text:a.textContent.trim()})),summary:[...e.querySelectorAll('summary')].map(s=>({tag:s.tagName,name:s.textContent.trim()}))}));save('missing-lazy-native-fallback-contract.json',{layer:'BROWSER_FIXTURE_NATIVE_FALLBACK',...fallback,required_A04_native_pass_claimed:false});assert(fallback.form.method==='get'&&fallback.form.action==='/ydental/settlement'&&fallback.form.maxlength==='100'&&fallback.candidates.length&&fallback.summary.every(s=>s.tag==='SUMMARY'&&s.name==='来源追溯'));await x.p.close();check('missing-lazy-native-Chinese-controls-and-semantics-retained',{mandatory_full_focus_still_failed:true});
    }else if(suite==='paired'){const x=await normalComponent(normalItem,768,1024);save('paired-lookup-only-normal-assets.json',{assets:x.loaded,registration:x.registration,source_html_sha256:normalItem.html_sha256,body_layer:'EXPLICIT_LOOKUP_ONLY_COMPONENT_MATCH_ORIGINAL_BASELINE_MAIN_STRUCTURE',original_business_controls_removed_only_in_memory_fixture_not_product:true,raw_response_not_saved:true});await oneCase(x.p,'pending',true,'paired-lookup-only-pending768-open',true);await x.p.close();
    }else if(suite==='instrumented'){const x=await normalComponent(normalItem,768,1024);await x.p.evaluate(()=>{window.__a04Writes=[];const e=document.querySelector('[data-fee-kind="pending"] .o_ydental_settlement_fee_scroll'),native=Object.getOwnPropertyDescriptor(Element.prototype,'scrollLeft');Object.defineProperty(e,'scrollLeft',{configurable:true,get(){return native.get.call(this)},set(value){window.__a04Writes.push({value,at:performance.now(),activeTag:document.activeElement?.tagName,stack:String(new Error().stack).split('\n').slice(0,8)});native.set.call(this,value)}})});await oneCase(x.p,'pending',true,'instrumented-pending768-open',true);const writes=await x.p.evaluate(()=>window.__a04Writes);save('instrumented-normal-product-scrollLeft-writes.json',{layer:'DIAGNOSTIC_PASSTHROUGH_OWN_SCROLLLEFT_SETTER_OBSERVATION',normal_bundle_startup:true,product_reveal_not_called_by_test:true,geometry_or_native_keys_not_modified:true,writes});assert(writes.length>=1&&writes.some(x=>x.stack.some(line=>line.includes('reveal'))));await x.p.close();
    }else if(suite==='lifecycle'){const x=await normalComponent(normalItem,1366,768);await a04Lifecycle(x.p,normalItem);await x.p.close();
    }else if(suite==='impact'){
        for(const item of fixture.components.filter(x=>['selected-three-sections','long-mixed-values'].includes(x.name))){
            for(const [width,height,zoomKind]of [...views.map(([w,h])=>[w,h,'normal']),[1366,768,'native200'],[1366,768,'root200']]){
                if(arg('a04-filter')==='repaired-tail'&&item.name==='selected-three-sections'&&zoomKind!=='root200')continue;const x=await normalComponent(item,width,height,zoomKind),tag=item.name+'-'+width+'-'+zoomKind;
                save(tag+'-assets.json',{assets:x.loaded,registration:x.registration,source_html_sha256:item.html_sha256,raw_response_not_saved:true});
                for(const kind of ['today','history','pending'])for(const opened of [false,true])await oneCase(x.p,kind,opened,tag+'-'+kind+'-'+opened,false);
                await x.p.close();
            }
        }
        const empty=fixture.components.find(x=>x.name==='empty-unselected'),x=await normalComponent(empty,320,800);assert.equal(await x.p.locator(scope+' .o_ydental_settlement_fee_scroll').count(),0);await shot('empty-normal-no-fee-table',x.p,'LOADED_QWEB_BROWSER_FIXTURE_EMPTY');await x.p.close();
    }else throw Error('Unknown A04 component suite');
    r.required_strict_failures=r.cases.filter(x=>!x.native_pass);
    if(suite!=='fault')assert.equal(r.required_strict_failures.length,0,'All original native whole-focus criteria must pass, including JS-off');
    if(suite==='fault')check('A04-fault-native-controls-semantics-observed',{count:r.cases.length,mandatory_full_focus_pass:false,required_strict_failures:r.required_strict_failures.length});else check('A04-'+suite+'-original-full-focus-criteria',{count:r.cases.length,javascript_enabled:!nojs});
}

try{if(engine==='webkit'){const manifest=path.join(root,'.local/dl-p1/evidence/webkit-engine-native-source-manifest.json');assert.equal(hash(manifest),JSON.parse(fs.readFileSync(path.join(root,'.local/dl-p1/webkit-manifest-binding.json'))).sha256);for(const f of JSON.parse(fs.readFileSync(manifest)).browser_files)assert.equal(hash(path.join(root,'.local/dl-p1',f.path)),f.sha256);r.engine_manifest_sha256=hash(manifest);browser=await pw.webkit.launch(require(path.join(root,'.local/dl-p3/verification/webkit_plugins_environment.cjs')).launchOptions(root));context=await browser.newContext({viewport:{width:1366,height:768},locale:'zh-CN',javaScriptEnabled:!nojs,acceptDownloads:false})}else if(['zoom','components','rwd','rwd-real'].includes(mode)){profile=path.join(out,'owned-temporary-profile');fs.mkdirSync(profile,{mode:0o700});const ext=path.join(root,'.local/dl-p1/zoom-extension');context=await pw.chromium.launchPersistentContext(profile,{headless:true,channel:'chromium',executablePath:path.join(root,'.local/s11/browsers/chromium-1248/chrome-linux64/chrome'),viewport:{width:1366,height:768},locale:'zh-CN',javaScriptEnabled:!nojs,acceptDownloads:false,args:['--disable-extensions-except='+ext,'--load-extension='+ext],env:{...process.env,LD_LIBRARY_PATH:path.join(root,'.local/s11/browser-deps/root/usr/lib/x86_64-linux-gnu'),FONTCONFIG_FILE:path.join(root,'.local/s12/fontconfig/fonts.conf'),FONTCONFIG_PATH:path.join(root,'.local/s12/fontconfig')}});browser=context.browser();worker=context.serviceWorkers()[0]||await context.waitForEvent('serviceworker')}else{browser=await pw.chromium.launch({headless:true,executablePath:path.join(root,'.local/s11/browsers/chromium-1248/chrome-linux64/chrome'),env:{...process.env,LD_LIBRARY_PATH:path.join(root,'.local/s11/browser-deps/root/usr/lib/x86_64-linux-gnu'),FONTCONFIG_FILE:path.join(root,'.local/s12/fontconfig/fonts.conf'),FONTCONFIG_PATH:path.join(root,'.local/s12/fontconfig')}});context=await browser.newContext({viewport:{width:1366,height:768},locale:'zh-CN',javaScriptEnabled:!nojs,acceptDownloads:false})}
r.actual_engine_version=browser.version();r.driver_version=require(path.join(driver,'package.json')).version;proc=browser._connection.toImpl(browser)?.options?.browserProcess?.process;if(proc){r.native_main_lifecycle={pid:proc.pid,executable:proc.spawnfile};proc.once('exit',(exitCode,signalCode)=>Object.assign(r.native_main_lifecycle,{exitCode,signalCode}))}context.setDefaultTimeout(nojs?12000:20000);context.on('response',x=>r.responses.push({path:new URL(x.url()).pathname,method:x.request().method(),status:x.status()}));context.on('requestfailed',x=>r.failures.push({path:new URL(x.url()).pathname,resource:x.resourceType(),error:x.failure()?.errorText}));await context.route('**/*',route=>{const req=route.request(),u=new URL(req.url()),op=new URLSearchParams(req.postData()||'').get('operation');if(!['data:','about:','blob:'].includes(u.protocol)&&u.origin!==base){(r.external_blocks??=[]).push({protocol:u.protocol,host:u.host});return route.abort()}if(u.pathname.startsWith('/ydental/'))r.requests.push({method:req.method(),path:u.pathname,query:[...u.searchParams].filter(([k])=>k!=='revision'),...(u.pathname==='/ydental/access/action'?{operation:op}:{})});if((/\/pdf\/|\/originals\/generate|\/bill-original\/|\/csv(?:$|\/)/.test(u.pathname))||(req.method()==='POST'&&u.pathname.startsWith('/ydental/')&&!((u.pathname==='/ydental/access/action'&&op==='switch')))){r.business_write_requests++;(r.guard_blocks??=[]).push({path:u.pathname,operation:op});return route.abort()}return route.continue()});page=context.pages()[0]||await context.newPage();page.on('pageerror',e=>(r.page_errors??=[]).push({class:e.constructor.name,message:String(e.message).slice(0,600)}));await login();
if(['rwd','rwd-real'].includes(mode))await require('./browser_rwd.cjs').run({page,context,engine,stage,mode,nojs,sample,base,root,scope,views,out,r,arg,save,shot,hash,sha,live,settle,ready,open,querySelect,setZoomOn,focusSample,check,projection});else if(mode==='touch')await touchOriginalHistory();else if(mode==='layout')await layout();else if(mode==='zoom')await zooms();else if(mode==='nojs')await noJS();else if(mode==='permissions')await permissions();else if(mode==='bypass')await bypass();else if(mode==='components')await a04Components();else if(mode==='events')await actionEvents();else if(mode==='keyboard'){r.selected_href='/ydental/settlement?patient_id='+sample.selected_patient_id;await open(r.selected_href);const selected=await projection('keyboard-selected-context');assert(selected.selected.includes(sample.business_number));r.keyboard_entry='NORMAL_ORIGINAL_SELECTED_GET_NO_ALL_STORE_DATE_COMPARISON';await page.setViewportSize({width:320,height:800});await continuousKeyboard(page,'real-320');await traces();await nativeTableReading();}else if(mode==='states'){await querySelect();await families();await states();}else throw Error('Unknown P12 mode');
assert.equal(r.business_write_requests,0);assert.equal((r.guard_blocks||[]).length,0);assert.equal((r.external_blocks||[]).length,0);r.status=['rwd','rwd-real'].includes(mode)?'P12_RWD_MATRIX_RECORDED':mode==='touch'?(r.touch_observation.observed_horizontal_pan?'P12_A04_EMULATED_TOUCH_PAN_OBSERVED_PASS':'P12_A04_EMULATED_TOUCH_PAN_NOT_OBSERVED'):arg('a04-suite')==='fault'?'P12_A04_FAULT_FALLBACK_OBSERVED_NATIVE_A04_FAIL':'P12_A04_TARGETED_SUITE_PASS';
}catch(error){r.status='FAILED_NO_AUTOMATIC_REPLAY';r.error={class:error.constructor.name,message:String(error.message).slice(0,2200)};r.stack=String(error.stack).split('\n').slice(0,12)}finally{if(context){if(logged)try{r.logout_status=(await context.request.post(base+'/web/session/destroy',{data:{jsonrpc:'2.0',method:'call',params:{},id:9}})).status()}catch(e){r.logout_error=e.constructor.name}try{await context.close();r.context_normal_close=true}catch(e){r.context_close_error=e.constructor.name}}if(browser)try{await browser.close();r.browser_normal_close=true}catch(e){r.browser_close_error=e.constructor.name}if(proc&&proc.exitCode===null)await new Promise(resolve=>{proc.once('exit',resolve);setTimeout(resolve,3000)});if(profile&&r.context_normal_close){fs.rmSync(profile,{recursive:true});r.owned_profile_removed=true}r.finished_at_utc=new Date().toISOString();save('result.json',r);process.stdout.write(JSON.stringify({status:r.status,checks:r.checks.length,screenshots:r.screenshots.length})+'\n');process.exitCode=(r.status.endsWith('_PASS')||r.status==='P12_RWD_MATRIX_RECORDED')?0:2}})();
