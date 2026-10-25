// Finite P7 visual/semantic client. Never clicks inventory confirm or scan.
const fs = require('node:fs');
const path = require('node:path');
const crypto = require('node:crypto');
const assert = require('node:assert/strict');
const {execFileSync} = require('node:child_process');
const root = process.cwd(), args = process.argv.slice(2);
const arg = name => {const i=args.indexOf('--'+name);return i<0?undefined:args[i+1];};
const label = arg('label'), run = arg('run-id'), engine = arg('engine');
const stage = arg('stage'), mode = arg('mode'), nojs = mode === 'nojs';
assert(/^[A-Za-z0-9_-]{1,60}$/.test(label));
const output = path.join(root, '.local/dl-p7/evidence', label);
fs.mkdirSync(output, {mode: 0o700, recursive: true});
const hash = file => crypto.createHash('sha256').update(fs.readFileSync(file)).digest('hex');
function save(name, value) {
    const target = path.join(output, name);
    const raw = typeof value === 'string' ? value : JSON.stringify(value, null, 2);
    fs.writeFileSync(target, raw, {flag: 'wx', mode: 0o600});
    return {file: path.relative(root, target), bytes: fs.statSync(target).size, sha256: hash(target)};
}
const binding = JSON.parse(execFileSync(path.join(root, '../.venv/bin/python'), ['-c',
    "import sys,json;from pathlib import Path;sys.path.insert(0,str(Path.cwd()/'scripts/s13_dl_p7'));from http_client import owned_service;import browser_client;browser_client.import_browser();print(json.dumps(owned_service(sys.argv[1])))", run], {encoding: 'utf8', cwd: root}));
const driver = path.join(root, '.local/s11/operations/clock-operator-users-ui-c981cd0-attempt15-runtime-snapshot/playwright/driver/package');
const pw = require(driver), base = 'http://127.0.0.1:18411';
const samples = JSON.parse(fs.readFileSync(path.join(root, arg('sample-file'))));
const search = 'form[action="/ydental/inventory"]';
const views = [[1366,768], [1440,900], [768,1024], [390,844], [320,800]];
const optin = '[data-dl-actions="inventory-actions"]';
const r = {status: 'INCOMPLETE', binding, stage, mode, engine, checks: [], requests: [],
    responses: [], failures: [], screenshots: [], user_hand_verified: false,
    source_sha256: hash(__filename), business_actions: 0,
    actual_OS_IME_screenreader_device: 'NOT_RUN', tokens_or_request_bodies_recorded: false};
const check = (name, facts = {}) => r.checks.push({check: name, passed: true, ...facts});
const gets = () => r.requests.filter(x => x.method === 'GET' && x.path === '/ydental/inventory').length;
const projection = () => {
    const main = document.querySelector('main.o_ydental_inventory');
    if (!main) throw Error('Actual inventory root missing');
    const secret = ['csrf_token', 'key', 'revision'];
    const field = e => ({tag:e.tagName, name:e.name, type:e.type,
        value:secret.includes(e.name)?'<PRIVATE_BINDING>':e.value,
        required:e.required, disabled:e.disabled, min:e.min, max:e.max,
        step:e.step, maxlength:e.maxLength,
        options:e.options?[...e.options].map(o=>({value:o.value,text:o.textContent,disabled:o.disabled,selected:o.selected})):null});
    const forms = [...main.querySelectorAll('form')].map(f=>({action:f.getAttribute('action'),
        method:f.getAttribute('method'), target:f.getAttribute('target'),
        fields:[...f.elements].filter(e=>e.name).map(field),
        submitters:[...f.querySelectorAll('button,input[type=submit]')].map(e=>({tag:e.tagName,
            type:e.getAttribute('type'), name:e.getAttribute('name'), value:e.getAttribute('value'),
            disabled:e.disabled,text:e.textContent.trim()}))}));
    return {forms, operations:[...main.querySelectorAll('details[name="inventory-operation"]')].map(e=>({
        name:e.getAttribute('name'), summary:e.querySelector('summary').textContent.trim(),
        actions:[...e.querySelectorAll('form')].map(f=>f.getAttribute('action'))})),
        lots:[...main.querySelectorAll('tr[data-lot]')].map(e=>({id:e.dataset.lot,idAttribute:e.id,
            cells:[...e.cells].map(c=>c.textContent.trim()), flags:e.querySelector('[data-flags]')?.dataset.flags})),
        headers:[...main.querySelectorAll('th')].map(e=>e.textContent.trim()),
        events:[...main.querySelectorAll('article[data-event]')].map(e=>({id:e.dataset.event,idAttribute:e.id,
            state:e.querySelector('[data-state]')?.dataset.state,
            text:e.querySelector('[data-dl-region="source-summary"]')?.textContent.replace(/\s+/g,' ').trim(),
            link:e.querySelector('a[href*="event_id="]')?.getAttribute('href')})),
        nav:[...main.querySelectorAll('nav a')].map(e=>({text:e.textContent.trim(),href:e.getAttribute('href')})),
        query:[...new URL(location.href).searchParams], fragment:location.hash};
};
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
(async()=>{
    let browser, context, page, nativeProcess, profile, logged=false, worker;
    const live = () => execFileSync(path.join(root,'../.venv/bin/python'),['-c',
        "import sys;from pathlib import Path;sys.path.insert(0,str(Path.cwd()/'scripts/s13_dl_p7'));from http_client import owned_service;owned_service(sys.argv[1])",run],{cwd:root});
    async function settle(target=page) {await target.waitForTimeout(100);await target.evaluate(()=>document.fonts.ready.then(()=>new Promise(r=>requestAnimationFrame(()=>requestAnimationFrame(r)))));}
    async function shot(name,target=page) {
        live();assert.equal(await target.locator('input[type=password]').count(),0);
        await settle(target);
        const dest=path.join(output,name+'.png');assert(!fs.existsSync(dest),'Screenshot path must be unique: '+name);await target.screenshot({path:dest,fullPage:false,timeout:20000});fs.chmodSync(dest,0o600);
        const value={file:path.relative(root,dest),sha256:hash(dest),bytes:fs.statSync(dest).size,
            layer:target===page?'ACTUAL_PRODUCT_BROWSER':'COMPONENT_BROWSER',
            viewport:await target.evaluate(()=>({innerWidth,innerHeight,rootFont:getComputedStyle(document.documentElement).fontSize,
                dpr:devicePixelRatio,scrollY,rootClient:document.documentElement.clientWidth,rootScroll:document.documentElement.scrollWidth}))};
        r.screenshots.push(value);return value;
    }
    async function snap(name) {const value=await page.evaluate(projection);save(name+'-projection.json',value);return value;}
    async function navigate(action) {await Promise.all([page.waitForNavigation({waitUntil:'domcontentloaded',timeout:40000}),action()]);await page.locator(search).waitFor({state:'visible'});await settle();}
    async function openInventory() {await page.goto(base+'/ydental/inventory',{waitUntil:'networkidle',timeout:40000});await page.locator(search).waitFor({state:'visible'});await settle();}
    async function normalLogin(alias, inventoryMenu=true) {
        const provider=path.join(root,'.local/s11/new-target-tests/roles.json'),info=fs.lstatSync(provider);
        assert(info.isFile()&&!info.isSymbolicLink()&&info.uid===process.getuid()&&(info.mode&0o777)===0o600);
        const account=JSON.parse(fs.readFileSync(provider)).users[alias];assert(account);
        if(nojs) {
            const login=await context.request.get(base+'/web/login?db=ydental_s11_synth_20261023_01');
            const csrf=await page.evaluate(html=>new DOMParser().parseFromString(html,'text/html').querySelector('form.oe_login_form [name=csrf_token]').value,await login.text());
            const response=await context.request.post(base+'/web/login',{form:{login:account.login,password:account.password,csrf_token:csrf,db:'ydental_s11_synth_20261023_01',redirect:'/ydental/access'},maxRedirects:0});
            assert.equal(response.status(),303);logged=true;
            r.login={uid:account.id,layer:'NORMAL_CSRF_PASSWORD_HTTP_SAME_NOJS_CONTEXT',session_copied:false,login_UI_noJS:'EXISTING_LIMITATION'};
        } else {
            await page.goto(base+'/web/login?db=ydental_s11_synth_20261023_01',{waitUntil:'networkidle',timeout:40000});
            await page.locator('body[is-ready="true"]').waitFor({state:'attached',timeout:30000});
            const form=page.locator('form.oe_login_form');
            await form.locator('[name=login]').fill(account.login);await form.locator('[name=password]').fill(account.password);
            const [,response]=await Promise.all([page.waitForNavigation({waitUntil:'domcontentloaded',timeout:40000}),page.waitForResponse(x=>new URL(x.url()).pathname==='/web/login'&&x.request().method()==='POST'),form.locator('button[type=submit]').click()]);
            assert.equal(response.status(),303);logged=true;
            await page.locator('.o_web_client').waitFor({state:'visible',timeout:30000});
            await page.waitForFunction(()=>window.odoo?.isReady===true,undefined,{timeout:30000});
            // Backend messaging can keep network connections open after UI ready.
            r.login={uid:account.id,layer:'NORMAL_BROWSER_CSRF_PASSWORD_LOGIN',session_copied:false};
        }
        const identity=await context.request.post(base+'/web/session/get_session_info',{data:{jsonrpc:'2.0',method:'call',params:{},id:1}});
        assert.equal((await identity.json()).result.uid,account.id);logged=true;
        await page.goto(base+'/ydental/access',{waitUntil:'domcontentloaded'});
        const switcher=page.locator('form').filter({has:page.locator('[name=operation][value=switch]')});
        await switcher.locator('[name=store_id]').selectOption(String(samples.store_id||1));
        await Promise.all([page.waitForNavigation({waitUntil:'domcontentloaded'}),switcher.locator('button[type=submit]').click()]);
        if(inventoryMenu)await navigate(()=>page.locator('nav a[href="/ydental/inventory"]').click());
        return account.id;
    }
    async function controls(condition,pictures=true) {
        const baseline=await page.evaluate(projection), start=gets();
        const details=page.locator('details[name="inventory-operation"]');
        const families=[];
        for(let i=0;i<await details.count();i++) {
            const d=details.nth(i),s=d.locator('summary');
            await s.focus();await s.press('Enter');assert.notEqual(await d.getAttribute('open'),null);
            const summary=await s.evaluate(computed);
            const buttons=d.locator('button');
            const submits=[];
            for(let j=0;j<await buttons.count();j++) {
                const b=buttons.nth(j);await b.focus();await page.keyboard.press('Tab');await page.keyboard.press('Shift+Tab');
                assert(await b.evaluate(e=>e===document.activeElement));
                const value=await b.evaluate(computed);
                if(stage==='after')contrast(value,true,true);
                submits.push(value);
            }
            const cancel=d.locator('a[href]');
            const links=[];
            for(let j=0;j<await cancel.count();j++)links.push(await cancel.nth(j).evaluate(computed));
            families.push({summary,submits,cancel:links});
            await s.focus();await s.press('Space');assert.equal(await d.getAttribute('open'),null);
        }
        assert.equal(gets(),start);assert.deepEqual((await page.evaluate(projection)).forms,baseline.forms);
        const query=page.locator(search+' button'), scan=page.locator('form[action="/ydental/inventory/scan"] button');
        const source=page.locator('article[data-event] a[href*="event_id="]').first();
        const firstDetail=details.first();
        if(await firstDetail.count()) {
            await firstDetail.locator('summary').focus();
            await firstDetail.locator('summary').press('Enter');
        }
        const controls=[['query',query],['scan',scan],['source',source],
            ['page',page.locator('[data-dl-region="pagination"] a').first()],
            ['summary',firstDetail.locator('summary')],
            ['cancel',firstDetail.locator('a[href]').first()],
            ['confirm',firstDetail.locator('button').first()]];
        const samplesOut=[];
        for(const [name,target] of controls) {
            if(!await target.count())continue;
            await target.scrollIntoViewIfNeeded();await page.mouse.move(0,0);await target.evaluate(e=>e.blur());await page.waitForTimeout(180);
            const states={normal:await target.evaluate(computed)};
            await target.hover();await page.waitForTimeout(180);states.hover=await target.evaluate(computed);
            if(stage==='after'&&condition==='1440x900'&&['query','page','source','summary'].includes(name))await shot(condition+'-'+name+'-hover');
            const rect=await target.boundingBox();await page.mouse.move(rect.x+rect.width/2,rect.y+rect.height/2);await page.mouse.down();await page.waitForTimeout(180);
            states.active=await target.evaluate(computed);await page.mouse.move(0,0);await page.mouse.up();
            await target.focus();await page.keyboard.press('Tab');await page.keyboard.press('Shift+Tab');await page.waitForTimeout(180);
            states.focus=await target.evaluate(computed);
            if(stage==='after')for(const [state,value] of Object.entries(states)) {
                contrast(value,!['source','cancel'].includes(name),state==='focus');
                for(const icon of value.svg) {
                    assert.equal(icon.ariaHidden,'true');assert.equal(icon.focusable,'false');assert.equal(icon.tabindex,null);
                    assert.equal(icon.viewBox,'0 0 24 24');assert.equal(icon.forbidden.length,0);assert.equal(icon.eventAttributes.length,0);
                    assert(icon.width>0&&icon.height>0);
                }
            }
            if(pictures)await shot(condition+'-'+name+'-focus');
            samplesOut.push({name,states});
        }
        if(await firstDetail.count()) {
            await firstDetail.locator('summary').focus();
            await firstDetail.locator('summary').press('Space');
        }
        const data={condition,visible_families:families.length,families,controls:samplesOut,
            viewport:await page.evaluate(()=>({innerWidth,innerHeight,dpr:devicePixelRatio,rootFont:getComputedStyle(document.documentElement).fontSize,rootScroll:document.documentElement.scrollWidth,rootClient:document.documentElement.clientWidth}))};
        assert(data.viewport.rootScroll<=data.viewport.rootClient+1,'New root horizontal overflow');
        save(condition+'-controls.json',data);
        check('visible-families-native-open-focus-close-no-submit-'+condition,{families:families.length,all_form_fields_preserved:true,no_GET_or_POST:true});
        if(pictures&&await details.count()) {
            const d=details.first(),s=d.locator('summary');await s.focus();await s.press('Enter');
            await shot(condition+'-expanded-summary');
            const button=d.locator('button').first();await button.focus();await shot(condition+'-expanded-confirm-focus');
            await s.focus();await s.press('Space');
        }
        if(pictures){await query.scrollIntoViewIfNeeded();await shot(condition+'-search');}
    }
    try {
        if(engine==='webkit') {
            const manifest=path.join(root,'.local/dl-p1/evidence/webkit-engine-native-source-manifest.json');
            assert.equal(hash(manifest),JSON.parse(fs.readFileSync(path.join(root,'.local/dl-p1/webkit-manifest-binding.json'))).sha256);
            for(const item of JSON.parse(fs.readFileSync(manifest)).browser_files)assert.equal(hash(path.join(root,'.local/dl-p1',item.path)),item.sha256);
            r.engine_manifest_sha256=hash(manifest);
            browser=await pw.webkit.launch(require(path.join(root,'.local/dl-p3/verification/webkit_plugins_environment.cjs')).launchOptions(root));
            context=await browser.newContext({viewport:{width:1366,height:768},locale:'zh-CN',javaScriptEnabled:!nojs});
        } else if(mode==='zoom') {
            profile=path.join(output,'owned-temporary-profile');fs.mkdirSync(profile,{mode:0o700});
            const extension=path.join(root,'.local/dl-p1/zoom-extension');
            context=await pw.chromium.launchPersistentContext(profile,{headless:true,channel:'chromium',
                executablePath:path.join(root,'.local/s11/browsers/chromium-1248/chrome-linux64/chrome'),
                locale:'zh-CN',viewport:{width:1366,height:768},args:['--disable-extensions-except='+extension,'--load-extension='+extension],
                env:{...process.env,LD_LIBRARY_PATH:path.join(root,'.local/s11/browser-deps/root/usr/lib/x86_64-linux-gnu'),FONTCONFIG_FILE:path.join(root,'.local/s12/fontconfig/fonts.conf'),FONTCONFIG_PATH:path.join(root,'.local/s12/fontconfig')}});
            browser=context.browser();worker=context.serviceWorkers()[0]||await context.waitForEvent('serviceworker');
        } else {
            browser=await pw.chromium.launch({headless:true,executablePath:path.join(root,'.local/s11/browsers/chromium-1248/chrome-linux64/chrome'),
                env:{...process.env,LD_LIBRARY_PATH:path.join(root,'.local/s11/browser-deps/root/usr/lib/x86_64-linux-gnu'),FONTCONFIG_FILE:path.join(root,'.local/s12/fontconfig/fonts.conf'),FONTCONFIG_PATH:path.join(root,'.local/s12/fontconfig')}});
            context=await browser.newContext({viewport:{width:1366,height:768},locale:'zh-CN',javaScriptEnabled:!nojs});
        }
        r.actual_engine_version=browser.version();r.playwright_version=require(path.join(driver,'package.json')).version;
        const implementation=browser._connection.toImpl(browser);
        if(implementation?.options?.browserProcess?.process) {
            nativeProcess=implementation.options.browserProcess.process;
            r.native_main_lifecycle={pid:nativeProcess.pid,executable:nativeProcess.spawnfile};
            nativeProcess.once('exit',(code,signal)=>Object.assign(r.native_main_lifecycle,{exitCode:code,signalCode:signal}));
        }
        context.setDefaultTimeout(25000);
        context.on('response',response=>r.responses.push({path:new URL(response.url()).pathname,method:response.request().method(),status:response.status()}));
        context.on('requestfailed',request=>r.failures.push({path:new URL(request.url()).pathname,resource:request.resourceType(),error:request.failure()?.errorText}));
        const routeGuard=route=>{
            const request=route.request(),url=new URL(request.url());
            if(!['data:','about:','blob:'].includes(url.protocol)&&url.origin!==base){(r.external_blocks||=[]).push({origin:url.origin});return route.abort();}
            if(url.pathname.startsWith('/ydental/'))r.requests.push({method:request.method(),path:url.pathname,query:[...url.searchParams].filter(([k])=>k!=='revision')});
            const operation=new URLSearchParams(request.postData()||'').get('operation');
            if(/\/pdf\/|\/originals\//.test(url.pathname)||request.method()==='POST'&&url.pathname.startsWith('/ydental/')&&!(url.pathname==='/ydental/access/action'&&operation==='switch')) {
                (r.guard_blocks||=[]).push({method:request.method(),path:url.pathname});return route.abort();
            }
            return route.continue();
        };
        await context.route('**/*',routeGuard);
        page=context.pages()[0]||await context.newPage();
        await normalLogin(samples.ordinary_role_alias||'warehouse');
        const initial=await snap('initial');r.initial=initial;
        assert.equal(initial.headers.length,9);assert.deepEqual(initial.forms[0].fields.map(f=>f.name),['q']);
        assert.equal(initial.forms[0].method,'get');
        assert.deepEqual(initial.events.map(e=>Number(e.id)),samples.real_source_first_ids);
        check('ordinary-menu-original-GET-and-nine-columns',{visible_operations:initial.operations.length});
        if(mode==='main'||mode==='nojs') {
            for(const [name,target] of [['icon','svg'],['text','span'],['Enter',null]]) {
                const q=page.locator(search+' [name=q]'), before=gets();await q.fill(samples.product_name);await q.press('Tab');await page.waitForTimeout(100);assert.equal(gets(),before);
                const button=page.locator(search+' button');
                const click=target&&await button.locator(target).count()?button.locator(target).first():button;
                await navigate(()=>name==='Enter'?q.press('Enter'):click.click());
                assert.deepEqual([...new URL(page.url()).searchParams],[['q',samples.product_name]]);
                assert.equal(gets(),before+1);check('query-'+name+'-single-original-GET',{actual_icon_target:target==='svg'&&await button.locator('svg').count()>0});
            }
            await openInventory();
            for(const target of ['span','svg']) {
                const before=await snap('before-source-'+target), link=page.locator('article[data-event] a[href*="event_id="]').first();
                const href=await link.getAttribute('href'), parsed=new URL(href,base);
                const click=await link.locator(target).count()?link.locator(target).first():link;
                const actualTag=await click.evaluate(e=>e.tagName.toLowerCase());
                const count=gets();await navigate(()=>click.click());
                const located=await snap('located-source-'+target);
                assert.deepEqual(located.query,[['event_id',before.events[0].id]]);assert.equal(located.fragment,parsed.hash);
                assert.deepEqual(located.lots,before.lots);assert.equal(gets(),count+1);
                check('source-'+target+'-original-GET-anchor',{href,requested_child_tag:target,actual_clicked_tag:actualTag,actual_child_target:actualTag===target});
                await navigate(()=>page.goBack({waitUntil:'domcontentloaded'}));
            }
            await openInventory();
            let next=page.locator('nav a').filter({hasText:/下一|Next/}).first();
            if(await next.count()) {
                const first=await snap('before-page2'), before=gets();await navigate(()=>next.click());
                const second=await snap('page2');assert.deepEqual(second.events.map(e=>Number(e.id)),samples.real_source_second_ids);
                assert.deepEqual(second.lots,first.lots);assert.equal(gets(),before+1);
                const prev=page.locator('nav a').filter({hasText:/上一|Previous/}).first();await navigate(()=>prev.click());
                assert.deepEqual((await page.evaluate(projection)).events,first.events);check('actual-source-forward-back-GET-pages',{first:first.events.length,second:second.events.length});
            }
            for(const [width,height] of views) {
                await page.setViewportSize({width,height});await controls(width+'x'+height,true);
            }
            const d=page.locator('details[name="inventory-operation"]').first();
            if(await d.count()) {
                await d.locator('summary').focus();await d.locator('summary').press('Enter');
                const cancel=d.locator('a[href]').first();
                if(await cancel.count()) {
                    const href=await cancel.getAttribute('href'), before=gets();await navigate(()=>cancel.click());
                    assert.equal(new URL(page.url()).pathname,new URL(href,base).pathname);assert.equal(gets(),before+1);check('actual-cancel-original-navigation-no-business-POST',{href});
                }
            }
        } else if(mode==='zoom') {
            if(engine==='webkit')r.native_zoom=await require(path.join(root,'.local/dl-p3/tools/webkit_finite_zoom_bridge.cjs')).setOwnedPageZoom(page,context,2);
            else {
                await worker.evaluate(async()=>{const[t]=await chrome.tabs.query({active:true,currentWindow:true});await chrome.tabs.setZoom(t.id,2)});
                await page.waitForFunction(()=>devicePixelRatio===2);
                r.native_zoom=await context.newCDPSession(page).then(s=>s.send('Page.getLayoutMetrics')).then(v=>v.cssVisualViewport);
                assert.equal(r.native_zoom.zoom,2);
            }
            assert.equal(await page.evaluate(()=>getComputedStyle(document.documentElement).fontSize),'16px');
            await controls('native200',true);check('actual-native200-root16',{metrics:r.native_zoom});
            if(engine==='webkit')await require(path.join(root,'.local/dl-p3/tools/webkit_finite_zoom_bridge.cjs')).setOwnedPageZoom(page,context,1);
            else {await worker.evaluate(async()=>{const[t]=await chrome.tabs.query({active:true,currentWindow:true});await chrome.tabs.setZoom(t.id,1)});await page.waitForFunction(()=>devicePixelRatio===1);}
            await page.evaluate(()=>document.documentElement.style.fontSize='200%');
            assert.equal(await page.evaluate(()=>getComputedStyle(document.documentElement).fontSize),'32px');
            await controls('rootfont200',true);check('independent-rootfont200-native100',{rootFont:'32px'});
        }
        if(mode==='fixtures') {
            assert.equal(stage,'after');
            const markup=await page.evaluate(()=>({
                styles:[...document.querySelectorAll('link[rel=stylesheet]')].map(e=>e.outerHTML).join(''),
                query:document.querySelector('form[action="/ydental/inventory"] button').outerHTML,
                scan:document.querySelector('form[action="/ydental/inventory/scan"] button').outerHTML,
                source:document.querySelector('article[data-event] a[href*="event_id="]').outerHTML,
                next:document.querySelector('[data-dl-region="pagination"] a')?.outerHTML,
                disclosure:document.querySelector('details[name="inventory-operation"] summary').outerHTML
            }));
            const fixture=await context.newPage();
            await fixture.setContent('<!doctype html><html lang="zh-CN"><head>'+markup.styles+'</head><body><main class="o_ydental_inventory"><h1>组件夹具：长文字、禁用与处理中；非真实办理</h1><section data-component="controls"></section></main></body></html>');
            await fixture.evaluate(markup=>{
                const parent=document.querySelector('[data-component=controls]');
                for(const [name,html] of Object.entries(markup)) {
                    if(name==='styles'||!html)continue;
                    const holder=document.createElement(name==='disclosure'?'details':'div');holder.dataset.fixture=name;
                    holder.innerHTML=html;const target=holder.firstElementChild;
                    if(target.tagName==='BUTTON')target.type='button';
                    if(target.tagName==='A')target.setAttribute('href','#component-link');
                    const label=target.querySelector('.o_ydental_inventory_action_label')||target;
                    label.textContent='【组件长文字】'+('查询来源、取消返回与原办理确认完整中文'.repeat(5))+'末端';
                    parent.append(holder);
                }
                const original=parent.querySelector('button');
                for(const [state,variant] of [['default',null],['disabled',null],['busy',null],['danger','o_ydental_inventory_action_danger']]) {
                    const b=original.cloneNode(true);b.dataset.fixtureState=state;
                    if(state==='disabled')b.disabled=true;
                    if(state==='busy')b.setAttribute('aria-busy','true');
                    if(variant){b.classList.remove('o_ydental_inventory_action_primary');b.classList.add(variant);}
                    b.querySelector('.o_ydental_inventory_action_label').textContent='【仅组件】状态矩阵同文案';
                    parent.append(b);
                }
            },markup);
            for(const [width,height] of views) {
                await fixture.setViewportSize({width,height});await settle(fixture);
                const measurements=await fixture.locator(optin).evaluateAll(xs=>xs.map(e=>({
                    text:e.textContent,rect:e.getBoundingClientRect().toJSON(),client:e.clientWidth,scroll:e.scrollWidth,
                    disabled:e.disabled,ariaBusy:e.getAttribute('aria-busy'),font:getComputedStyle(e).fontSize,
                    label:e.querySelector('.o_ydental_inventory_action_label')?.getBoundingClientRect().toJSON(),
                    icon:e.querySelector('svg')?.getBoundingClientRect().toJSON()})));
                assert(measurements.length>=8);
                assert(measurements.every(v=>v.rect.width>0&&v.rect.height>0&&v.scroll<=v.client+1));
                assert(await fixture.evaluate(()=>document.documentElement.scrollWidth<=document.documentElement.clientWidth+1));
                save('fixture-'+width+'-computed.json',measurements);
                await fixture.locator('[data-fixture=query]').scrollIntoViewIfNeeded();await shot('fixture-long-'+width,fixture);
                await fixture.locator('[data-fixture-state=danger]').scrollIntoViewIfNeeded();await shot('fixture-states-'+width,fixture);
                check('explicit-component-long-disabled-busy-danger-'+width,{layer:'COMPONENT_BROWSER',no_product_state_claim:true});
            }
            await fixture.setViewportSize({width:1366,height:768});
            const stateSamples=[];
            for(const name of ['default','disabled','busy','danger']) {
                const control=fixture.locator('[data-fixture-state='+name+']');
                const states={normal:await control.evaluate(computed)};
                await control.hover();await fixture.waitForTimeout(180);states.hover=await control.evaluate(computed);
                if(name!=='disabled') {
                    const rect=await control.boundingBox();await fixture.mouse.move(rect.x+rect.width/2,rect.y+rect.height/2);await fixture.mouse.down();await fixture.waitForTimeout(180);
                    states.active=await control.evaluate(computed);await fixture.mouse.move(0,0);await fixture.mouse.up();
                    await control.focus();await fixture.keyboard.press('Tab');await fixture.keyboard.press('Shift+Tab');await fixture.waitForTimeout(180);
                    states.focus=await control.evaluate(computed);
                }
                for(const [state,value] of Object.entries(states))contrast(value,true,state==='focus');
                const geometries=Object.values(states).map(x=>x.rect);
                assert(geometries.every(x=>Math.abs(x.width-geometries[0].width)<.5&&Math.abs(x.height-geometries[0].height)<.5));
                stateSamples.push({name,states});
            }
            const baseGeometry=stateSamples[0].states.normal.rect;
            assert(stateSamples.every(x=>Math.abs(x.states.normal.rect.width-baseGeometry.width)<.5&&Math.abs(x.states.normal.rect.height-baseGeometry.height)<.5));
            save('component-states-computed-and-contrast.json',stateSamples);
            check('component-default-disabled-busy-danger-four-states-no-size-jump',{layer:'COMPONENT_BROWSER',disabled_focus_native_omitted:true});
            if(arg('fixture-file')) {
                const filename=path.join(root,arg('fixture-file'));
                const loaded=JSON.parse(fs.readFileSync(filename));
                assert.equal(loaded.status,'P7_LOADED_QWEB_CONTROLS_MEMORY_PASS');
                assert.equal(loaded.business_creations,0);assert.equal(loaded.details.length,13);
                const qwebPage=await context.newPage();
                await qwebPage.setContent('<!doctype html><html lang="zh-CN"><head>'+markup.styles+'</head><body><main class="o_ydental_inventory"><h1>全部13族原生QWeb内存组件</h1><section data-component="controls"></section></main></body></html>');
                await qwebPage.evaluate(items=>{
                    const region=document.querySelector('[data-component=controls]');
                    region.replaceChildren();
                    for(const [i,item] of items.entries()) {
                        const wrapper=document.createElement('section');wrapper.dataset.qwebFamily=String(i);
                        const h=document.createElement('h2');h.textContent='【原生QWeb内存组件】'+item.name;wrapper.append(h);
                        const fragment=new DOMParser().parseFromString(item.html,'text/html');
                        const details=fragment.querySelector('details');if(!details)throw Error('Missing QWeb family details');
                        if([...details.querySelectorAll('input')].some(e=>['csrf_token','key','revision'].includes(e.name)&&e.value))throw Error('Fixture retained a private binding');
                        wrapper.append(details);region.append(wrapper);
                    }
                },loaded.details);
                const outcomes=[];
                for(let i=0;i<13;i++) {
                    const group=qwebPage.locator('[data-qweb-family="'+i+'"]'), detail=group.locator('details'), summary=detail.locator('summary');
                    await summary.focus();await summary.press('Enter');assert.notEqual(await detail.getAttribute('open'),null);
                    const contracts=await detail.locator('form').evaluateAll(forms=>forms.map(form=>{
                        const clone=form.cloneNode(true);
                        const submitters=[...form.querySelectorAll('button,input[type=submit]')];
                        const copies=[...clone.querySelectorAll('button,input[type=submit]')];
                        return {action:form.getAttribute('action'),method:form.getAttribute('method'),
                            fields:[...form.elements].filter(e=>e.name).map(e=>({tag:e.tagName,name:e.name,type:e.type,value:e.value,required:e.required,disabled:e.disabled})),
                            base_equal:JSON.stringify([...new FormData(form)])===JSON.stringify([...new FormData(clone)]),
                            submitters:submitters.map((b,j)=>({tag:b.tagName,type:b.getAttribute('type'),name:b.getAttribute('name'),value:b.getAttribute('value'),disabled:b.disabled,
                                equal:JSON.stringify([...new FormData(form,b)])===JSON.stringify([...new FormData(clone,copies[j])])})),
                            submit_event_dispatched:false,network_request_sent:false};
                    }));
                    assert(contracts.length&&contracts.every(x=>x.base_equal&&x.submitters.every(v=>v.equal)));
                    for(const button of await detail.locator('button').all()) {
                        await button.focus();assert(await button.evaluate(e=>e===document.activeElement));
                        const value=await button.evaluate(computed);contrast(value,true);
                        assert(value.text.trim());
                    }
                    if(i===0||i===8||i===12)await shot('component-QWeb-family-'+i+'-expanded',qwebPage);
                    await summary.focus();await summary.press('Space');assert.equal(await detail.getAttribute('open'),null);
                    outcomes.push({name:loaded.details[i].name,contracts,native_open_close:true});
                }
                save('all-13-QWeb-memory-family-contracts.json',{fixture_sha256:hash(filename),outcomes,
                    layer:'ACTUAL_LOADED_QWEB_MEMORY_COMPONENT',real_authorization_or_business_execution:false});
                check('all-13-loaded-QWeb-family-FormData-native-semantics',{families:13,layer:'QWEB_MEMORY_BROWSER_COMPONENT'});
                await qwebPage.close();
            }
            const before=gets();
            assert.equal(await fixture.locator('[data-fixture-state=disabled]').isDisabled(),true);
            assert.equal(await fixture.locator('[data-fixture-state=busy]').getAttribute('aria-busy'),'true');
            const baseControls=await fixture.locator(optin).evaluateAll(xs=>xs.map(e=>({tag:e.tagName,text:e.textContent})));
            await fixture.locator('svg').evaluateAll(xs=>xs.forEach(e=>e.remove()));
            assert.deepEqual(await fixture.locator(optin).evaluateAll(xs=>xs.map(e=>({tag:e.tagName,text:e.textContent}))),baseControls);
            await fixture.setViewportSize({width:390,height:844});await fixture.locator('[data-fixture=query]').scrollIntoViewIfNeeded();await shot('fixture-SVG-absent-readable',fixture);
            await fixture.locator('link[rel=stylesheet]').evaluateAll(xs=>xs.forEach(e=>e.remove()));
            const active=fixture.locator('[data-fixture=query] button');await active.focus();assert(await active.evaluate(e=>e===document.activeElement));
            assert.deepEqual(await fixture.locator(optin).evaluateAll(xs=>xs.map(e=>({tag:e.tagName,text:e.textContent}))),baseControls);
            await shot('fixture-styles-absent-native-focus',fixture);
            assert.equal(gets(),before);check('explicit-SVG-and-CSS-absent-readable-native-elements',{layer:'COMPONENT_BROWSER',no_business_requests:true});
            await fixture.close();
            await page.emulateMedia({reducedMotion:'reduce'});
            const reduced=await page.locator(search+' button').evaluate(computed);save('actual-reduced-motion.json',reduced);
            assert(await page.evaluate(()=>matchMedia('(prefers-reduced-motion: reduce)').matches));
            check('actual-reduced-motion-media',{transition:reduced.style.transitionDuration});
            if(engine==='chromium') {
                await page.emulateMedia({forcedColors:'active'});assert(await page.evaluate(()=>matchMedia('(forced-colors: active)').matches));
                const q=page.locator(search+' [name=q]');await q.focus();await q.press('Tab');
                const focus=await page.locator(search+' button').evaluate(computed);assert(focus.focusVisible&&focus.style.outlineStyle!=='none');
                save('actual-forced-colors-focus.json',focus);await shot('actual-forced-colors-focus');check('actual-forced-colors-native-focus');
            } else check('forced-colors-WebKit',{support:'UNSUPPORTED_MEDIA_EMULATION_NOT_CLAIMED'});
        }
        if(mode==='bypass') {
            const primaryContext=context,primaryPage=page;
            for(const [name,alias,url] of [
                ['catalog','group_manager','/ydental/inventory/catalog'],
                ['P5-settlement','settlement','/ydental/settlement?patient_id=655'],
                ['P4-report','reader','/ydental/reports'],
                ['P1-documents','doctor','/ydental/documents?q=P00001313'],
                ['inventory-reader','reader','/ydental/inventory'],
                ['inventory-none','no_permission','/ydental/inventory']]) {
                // Existing normal roles only; no permissions are added or removed.
                const roles=JSON.parse(fs.readFileSync(path.join(root,'.local/s11/new-target-tests/roles.json'))).users;
                const selected=name==='inventory-none'?samples.no_permission_alias:alias;assert(roles[selected]);
                context=await browser.newContext({locale:'zh-CN',viewport:{width:1366,height:768}});
                await context.route('**/*',routeGuard);page=await context.newPage();logged=false;
                // Normal login helper's menu opens inventory, so use a direct existing
                // ordinary login/store flow and permit an expected no-source rejection.
                await normalLogin(selected,false);
                const response=await page.goto(base+url,{waitUntil:'networkidle',timeout:40000});
                const snapshot=await page.evaluate(()=>{
                    const main=document.querySelector('main');
                    const style=e=>Object.fromEntries(['display','fontFamily','fontSize','lineHeight','color','backgroundColor','borderColor','padding','gap','overflowX','overflowY'].map(k=>[k,getComputedStyle(e)[k]]));
                    return {heading:[...(main||document).querySelectorAll('h1')].map(e=>({text:e.textContent,style:style(e)})),
                        controls:[...(main||document).querySelectorAll('button,a,summary,input:not([type=hidden]),select,th,td')].map(e=>({tag:e.tagName,
                            text:e.tagName==='INPUT'?null:e.textContent,class:e.className,name:e.name||null,type:e.type||null,
                            value:e.type==='password'?'<OMITTED>':e.value??null,disabled:e.disabled??null,style:style(e)})),
                        P7scope:document.querySelectorAll('[data-dl-actions="inventory-actions"]').length,
                        P7class:[...document.querySelectorAll('.o_ydental_inventory_action,.o_ydental_inventory_disclosure,.o_ydental_inventory_icon')].length,
                        operations:document.querySelectorAll('details[name="inventory-operation"]').length};
                });
                if(name==='inventory-reader')assert.equal(snapshot.operations,0);
                else if(name==='inventory-none'){assert.equal(response.status(),403);assert.equal(snapshot.P7scope,0);assert.equal(snapshot.P7class,0);}
                else {assert.equal(snapshot.P7scope,0);assert.equal(snapshot.P7class,0);}
                save(name+'-projection.json',snapshot);
                assert.equal(await page.locator('input[type=password]').count(),0);
                await shot(name+'-readonly');check('actual-readonly-role-bypass-'+name,{status:response.status(),no_business_actions:true});
                await context.request.post(base+'/web/session/destroy',{data:{jsonrpc:'2.0',method:'call',params:{},id:9}});await context.close();
            }
            context=primaryContext;page=primaryPage;logged=true;
        }
        if(stage==='after'&&mode==='main') {
            const contracts=await page.evaluate(()=>{
                return [...document.querySelectorAll('form[action="/ydental/inventory/action"],form[action="/ydental/inventory/scan"]')].map(form=>{
                    const clone=form.cloneNode(true);
                    const all=form.querySelectorAll('input,select,textarea');
                    const targets=clone.querySelectorAll('input,select,textarea');
                    all.forEach((e,i)=>{targets[i].value=e.value;if('checked' in e)targets[i].checked=e.checked;});
                    const submitters=[...form.querySelectorAll('button,input[type=submit]')];
                    const candidate=[...clone.querySelectorAll('button,input[type=submit]')];
                    const base=JSON.stringify([...new FormData(form)]),copied=JSON.stringify([...new FormData(clone)]);
                    const matches=submitters.map((button,i)=>{
                        const original=JSON.stringify([...new FormData(form,button)]),duplicate=JSON.stringify([...new FormData(clone,candidate[i])]);
                        return {tag:button.tagName,type:button.getAttribute('type'),name:button.getAttribute('name'),
                            value:button.getAttribute('value'),disabled:button.disabled,formdata_equal_in_memory:original===duplicate};
                    });
                    return {action:form.getAttribute('action'),method:form.getAttribute('method'),
                        original_connected:form.isConnected,clone_connected:clone.isConnected,
                        base_formdata_equal_in_memory:base===copied,submitters:matches,
                        event_dispatched:false,network_sent:false,token_values_or_hashes_recorded:false};
                });
            });
            assert(contracts.length>0&&contracts.every(x=>x.base_formdata_equal_in_memory&&x.submitters.every(s=>s.formdata_equal_in_memory)));
            save('detached-memory-FormData-contracts.json',contracts);
            check('detached-memory-FormData-submitters-no-submit-no-network',{forms:contracts.length,layer:'MEMORY_COMPONENT',business_execution_claimed:false});
        }
        if(stage==='after'&&mode==='main') {
            const manifest=await page.locator(optin).evaluateAll(xs=>xs.map(e=>({tag:e.tagName,text:e.textContent.trim(),class:e.className,svg:[...e.querySelectorAll('svg')].map(s=>s.dataset.icon)})));
            assert(manifest.length>0);save('optin-controls-manifest.json',manifest);
            const cdp=engine==='chromium'?await context.newCDPSession(page):null;
            if(cdp) {
                const ax=await cdp.send('Accessibility.getFullAXTree');
                assert(await page.evaluate(ax=>{const text=JSON.stringify(ax);return[...document.querySelectorAll('input[type=hidden]')].filter(e=>['csrf_token','key'].includes(e.name)&&e.value.length>16).every(e=>!text.includes(e.value))},ax));
                save('native-AX-not-screenreader.json',ax);check('actual-native-AX-hidden-icons-not-screenreader');
            }
        }
        assert.equal((r.guard_blocks||[]).length,0,'Unexpected blocked request is a failure, not product refusal');
        assert(!r.requests.some(x=>x.method==='POST'&&x.path.startsWith('/ydental/inventory')));
        r.status='P7_'+stage.toUpperCase()+'_'+engine.toUpperCase()+'_'+mode.toUpperCase()+'_PASS';
    } catch(error) {
        r.status='FAILED_NO_AUTOMATIC_REPLAY';r.error={class:error.constructor.name,message:String(error.message).slice(0,2000)};
        r.stack=String(error.stack).split('\n').slice(0,10);
    } finally {
        if(context) {
            if(logged)try{r.logout_status=(await context.request.post(base+'/web/session/destroy',{data:{jsonrpc:'2.0',method:'call',params:{},id:9}})).status();}catch(e){r.logout_error=e.constructor.name;}
            try{await context.close();r.context_normal_close=true;}catch(e){r.context_close_error=e.constructor.name;}
        }
        if(browser)try{await browser.close();r.browser_normal_close=true;}catch(e){r.browser_close_error=e.constructor.name;}
        if(nativeProcess&&nativeProcess.exitCode===null)await new Promise(resolve=>{nativeProcess.once('exit',resolve);setTimeout(resolve,3000)});
        if(profile&&r.context_normal_close){fs.rmSync(profile,{recursive:true});r.owned_profile_removed=true;}
        r.finished_at_utc=new Date().toISOString();save('result.json',r);
        process.stdout.write(JSON.stringify({status:r.status,checks:r.checks.length,screenshots:r.screenshots.length})+'\n');
        process.exitCode=r.status.endsWith('_PASS')?0:2;
    }
})();
