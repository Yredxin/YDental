// Bounded P13 UI reads. Never activates the original bill submitter.
const fs=require('node:fs'),path=require('node:path'),crypto=require('node:crypto'),assert=require('node:assert/strict'),{execFileSync}=require('node:child_process');
const root=process.cwd(),argv=process.argv.slice(2),arg=n=>{const i=argv.indexOf('--'+n);return i<0?undefined:argv[i+1]},label=arg('label'),run=arg('run-id'),engine=arg('engine'),stage=arg('stage'),mode=arg('mode'),alias=arg('role')||'settlement',nojs=arg('js')==='off';
assert(/^[A-Za-z0-9_-]{1,60}$/.test(label));
const out=path.join(root,'.local/dl-p13/testing/evidence',label);fs.mkdirSync(out,{mode:0o700,recursive:true});
const hash=f=>crypto.createHash('sha256').update(fs.readFileSync(f)).digest('hex'),sha=b=>crypto.createHash('sha256').update(b).digest('hex');
function save(name,value){const f=path.join(out,name),raw=typeof value==='string'||Buffer.isBuffer(value)?value:JSON.stringify(value,null,2);fs.writeFileSync(f,raw,{flag:'wx',mode:0o600});return{file:path.relative(root,f),bytes:fs.statSync(f).size,sha256:hash(f)}}
const python=path.join(root,'../.venv/bin/python');
const binding=JSON.parse(execFileSync(python,['-c',"import sys,json;from pathlib import Path;sys.path.insert(0,str(Path.cwd()/'scripts/s13_dl_p13'));from http_client import owned_service;sys.path.insert(0,str(Path.cwd()/'scripts/s13_dl_p12'));import browser_client;browser_client.import_browser();print(json.dumps(owned_service(sys.argv[1])))",run],{encoding:'utf8'}));
const live=()=>execFileSync(python,['-c',"import sys;from pathlib import Path;sys.path.insert(0,str(Path.cwd()/'scripts/s13_dl_p13'));from http_client import owned_service;owned_service(sys.argv[1])",run]);
const base='http://127.0.0.1:18411',driver=path.join(root,'.local/s11/operations/clock-operator-users-ui-c981cd0-attempt15-runtime-snapshot/playwright/driver/package'),pw=require(driver);
const sample=JSON.parse(fs.readFileSync(arg('sample-file'))),views=[[1366,768],[1440,900],[768,1024],[390,844],[320,800]];
const r={status:'INCOMPLETE',label,engine,stage,mode,javascript_enabled:!nojs,binding,source_sha256:hash(__filename),requests:[],responses:[],screenshots:[],cases:[],findings:[],business_write_attempts:[],external_blocks:[],credentials_or_request_bodies_recorded:false,live_bill_submission:false,user_hand_effect:'PENDING'};
(async()=>{let browser,context,page,proc,profile,worker,logged=false;
const settle=async(p=page)=>{await p.waitForTimeout(160);if(!nojs)await p.evaluate(()=>document.fonts.ready)};
async function shot(name,p=page,layer='ACTUAL_AUTHENTICATED_PRODUCT_BROWSER'){
 live();assert.equal(await p.locator('input[type=password]').count(),0);await settle(p);
 const f=path.join(out,String(r.screenshots.length+1).padStart(3,'0')+'-'+name+'.png');assert(!fs.existsSync(f));let captureRect=null;
 if(engine==='chromium'){const c=await context.newCDPSession(p),x=await c.send('Page.captureScreenshot',{format:'png',fromSurface:true,captureBeyondViewport:false});fs.writeFileSync(f,Buffer.from(x.data,'base64'),{flag:'wx',mode:0o600});await c.detach()}
 else if(nojs){captureRect={x:0,y:0,...p.viewportSize()};const impl=p._connection.toImpl(p),x=await impl.delegate._session.send('Page.snapshotRect',{...captureRect,coordinateSystem:'Viewport',omitDeviceScaleFactor:false,format:'png'});fs.writeFileSync(f,Buffer.from(x.dataURL.split(',')[1],'base64'),{flag:'wx',mode:0o600})}
 else await p.screenshot({path:f,fullPage:false,timeout:20000});
 fs.chmodSync(f,0o600);const b=fs.readFileSync(f),physical=p.viewportSize();assert.equal(b.readUInt32BE(16),physical.width);assert.equal(b.readUInt32BE(20),physical.height);
 const v={file:path.relative(root,f),sha256:hash(f),bytes:b.length,width:b.readUInt32BE(16),height:b.readUInt32BE(20),captureRect,physicalViewport:physical,layer,candidate:binding.candidate_commit,image_pixels_edited:false,viewport:await p.evaluate(()=>({width:innerWidth,height:innerHeight,dpr:devicePixelRatio,rootFont:getComputedStyle(document.documentElement).fontSize,scrollX,scrollY}))};r.screenshots.push(v);return v;
}
async function zoom(p,width,height,kind){
 await p.bringToFront();async function native(factor){
  if(engine==='webkit')return require(path.join(root,'.local/dl-p3/tools/webkit_finite_zoom_bridge.cjs')).setOwnedPageZoom(p,context,factor);
  await worker.evaluate(async factor=>{const [tab]=await chrome.tabs.query({active:true,currentWindow:true});await chrome.tabs.setZoom(tab.id,factor)},factor);
  let actual;for(let i=0;i<30;i++){actual=await p.evaluate(()=>devicePixelRatio);if(actual===factor)break;await p.waitForTimeout(100)}assert.equal(actual,factor);
  const c=await context.newCDPSession(p),v=(await c.send('Page.getLayoutMetrics')).cssVisualViewport;await c.detach();assert.equal(v.zoom,factor);
 }
 await native(1);await p.setViewportSize({width,height});await p.evaluate(()=>document.documentElement.style.fontSize='');
 if(kind==='native200')await native(2);if(kind==='root200')await p.evaluate(()=>document.documentElement.style.fontSize='200%');await settle(p);
 const actual=await p.evaluate(()=>({width:innerWidth,height:innerHeight,dpr:devicePixelRatio,rootFont:getComputedStyle(document.documentElement).fontSize})),factor=kind==='native200'?2:1;
 assert(Math.abs(actual.width-width/factor)<=1&&Math.abs(actual.height-height/factor)<=1);assert.equal(actual.dpr,factor);assert.equal(actual.rootFont,kind==='root200'?'32px':'16px');return actual;
}
async function login(){
 const file=path.join(root,'.local/s11/new-target-tests/roles.json'),st=fs.lstatSync(file);assert(st.isFile()&&!st.isSymbolicLink()&&st.uid===process.getuid()&&(st.mode&0o777)===0o600);const account=JSON.parse(fs.readFileSync(file)).users[alias];assert(account);r.actor={alias,uid:account.id};
 // Normal same-context CSRF/password login. Native values remain in memory.
 const login=await context.request.get(base+'/web/login?db=ydental_s11_synth_20261023_01');assert.equal(login.status(),200);
 const csrf=await page.evaluate(html=>new DOMParser().parseFromString(html,'text/html').querySelector('form.oe_login_form [name=csrf_token]').value,await login.text());
 const response=await context.request.post(base+'/web/login',{form:{login:account.login,password:account.password,csrf_token:csrf,db:'ydental_s11_synth_20261023_01',redirect:'/ydental/access'},maxRedirects:0});assert.equal(response.status(),303);logged=true;
 const info=await context.request.post(base+'/web/session/get_session_info',{data:{jsonrpc:'2.0',method:'call',params:{},id:1}});assert.equal((await info.json()).result.uid,account.id);
 await page.goto(base+'/ydental/access',{waitUntil:'domcontentloaded'});const switchForm=page.locator('form').filter({has:page.locator('[name=operation][value=switch]')});await switchForm.locator('[name=store_id]').selectOption(String(sample.store_id||1));
 const switchButton=switchForm.locator('button[type=submit]');await switchButton.evaluate(e=>e.scrollIntoView({block:'center'}));const switchBox=await switchButton.boundingBox();assert(switchBox);await Promise.all([page.waitForNavigation({waitUntil:'domcontentloaded'}),page.mouse.click(switchBox.x+switchBox.width/2,switchBox.y+switchBox.height/2)]);await settle();
 r.login_layer='NORMAL_SAME_CONTEXT_PASSWORD_CSRF_STORE_SELECTION_NO_SESSION_COPY';
}
try{
 if(engine==='webkit'){
  const manifest=path.join(root,'.local/dl-p1/evidence/webkit-engine-native-source-manifest.json');assert.equal(hash(manifest),JSON.parse(fs.readFileSync(path.join(root,'.local/dl-p1/webkit-manifest-binding.json'))).sha256);for(const f of JSON.parse(fs.readFileSync(manifest)).browser_files)assert.equal(hash(path.join(root,'.local/dl-p1',f.path)),f.sha256);
  r.engine_manifest_sha256=hash(manifest);browser=await pw.webkit.launch(require(path.join(root,'.local/dl-p3/verification/webkit_plugins_environment.cjs')).launchOptions(root));context=await browser.newContext({viewport:{width:1366,height:768},locale:'zh-CN',javaScriptEnabled:!nojs,acceptDownloads:false});
 }else{
  profile=path.join(out,'owned-temporary-profile');fs.mkdirSync(profile,{mode:0o700});const ext=path.join(root,'.local/dl-p1/zoom-extension');context=await pw.chromium.launchPersistentContext(profile,{headless:true,channel:'chromium',executablePath:path.join(root,'.local/s11/browsers/chromium-1248/chrome-linux64/chrome'),viewport:{width:1366,height:768},locale:'zh-CN',javaScriptEnabled:!nojs,acceptDownloads:false,args:['--disable-extensions-except='+ext,'--load-extension='+ext],env:{...process.env,LD_LIBRARY_PATH:path.join(root,'.local/s11/browser-deps/root/usr/lib/x86_64-linux-gnu'),FONTCONFIG_FILE:path.join(root,'.local/s12/fontconfig/fonts.conf'),FONTCONFIG_PATH:path.join(root,'.local/s12/fontconfig')}});browser=context.browser();worker=context.serviceWorkers()[0]||await context.waitForEvent('serviceworker');
 }
 r.actual_engine_version=browser.version();r.driver_version=require(path.join(driver,'package.json')).version;proc=browser._connection.toImpl(browser)?.options?.browserProcess?.process;if(proc){r.native_main_lifecycle={pid:proc.pid,executable:proc.spawnfile};proc.once('exit',(exitCode,signalCode)=>Object.assign(r.native_main_lifecycle,{exitCode,signalCode}))}
 context.setDefaultTimeout(20000);context.on('response',x=>r.responses.push({path:new URL(x.url()).pathname,method:x.request().method(),status:x.status()}));
 await context.route('**/*',route=>{
  const req=route.request(),u=new URL(req.url()),op=new URLSearchParams(req.postData()||'').get('operation');
  if(!['data:','about:','blob:'].includes(u.protocol)&&u.origin!==base){r.external_blocks.push({protocol:u.protocol,host:u.host});return route.abort()}
  if(u.pathname.startsWith('/ydental/'))r.requests.push({method:req.method(),path:u.pathname,...(u.pathname==='/ydental/access/action'?{operation:op}:{})});
  if(/\/pdf\/|\/originals\/generate|\/bill-original\/|\/csv(?:$|\/)/.test(u.pathname)||(req.method()==='POST'&&u.pathname.startsWith('/ydental/')&&!(u.pathname==='/ydental/access/action'&&op==='switch'))){r.business_write_attempts.push({path:u.pathname,method:req.method(),operation:op,preintercept_only_not_backend_denial:true});return route.abort()}
  return route.continue();
 });
 page=context.pages()[0]||await context.newPage();await login();
 await require('./browser_panel.cjs').run({root,base,context,page,browser,engine,stage,mode,nojs,alias,sample,views,arg,r,save,shot,zoom,settle,sha,hash,live});
 assert.equal(r.business_write_attempts.length,0);assert.equal(r.external_blocks.length,0);r.status='P13_UI_EVIDENCE_RECORDED';
}catch(error){r.status='FAILED_NO_AUTOMATIC_REPLAY';r.error={class:error.constructor.name,message:String(error.message).slice(0,1800)};r.stack=String(error.stack).split('\n').slice(0,8)}
finally{
 if(context){if(logged)try{r.logout_status=(await context.request.post(base+'/web/session/destroy',{data:{jsonrpc:'2.0',method:'call',params:{},id:9}})).status()}catch(error){r.logout_error=error.constructor.name}try{await context.close();r.context_normal_close=true}catch(error){r.context_close_error=error.constructor.name}}
 if(browser)try{await browser.close();r.browser_normal_close=true}catch(error){r.browser_close_error=error.constructor.name}
 if(proc&&proc.exitCode===null)await new Promise(resolve=>{proc.once('exit',resolve);setTimeout(resolve,3000)});
 if(profile&&r.context_normal_close){fs.rmSync(profile,{recursive:true});r.owned_profile_removed=true}
 r.finished_at_utc=new Date().toISOString();save('result.json',r);process.stdout.write(JSON.stringify({status:r.status,cases:r.cases.length,findings:r.findings.length,png:r.screenshots.length})+'\n');process.exitCode=r.status==='P13_UI_EVIDENCE_RECORDED'?0:2;
}
})();
