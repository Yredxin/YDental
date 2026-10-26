"""Build one private P9 viewing package from original PNG bytes only."""
from pathlib import Path
import json, hashlib, os, zipfile, datetime
from PIL import Image
r=Path.cwd();base=r/'.local/dl-p9';ev=base/'testing/evidence';out=base/'viewing'
out.mkdir(mode=0o700,exist_ok=True)
def sha(raw):return hashlib.sha256(raw).hexdigest()
def rawjson(v):return (json.dumps(v,ensure_ascii=False,indent=2)+'\n').encode()
selected=[]
def pick(client,suffix):
 result=json.loads((ev/client/'result.json').read_text());entries=[x for x in result['screenshots'] if Path(x['file']).name.endswith(suffix)]
 assert len(entries)==1,(client,suffix,len(entries))
 x=entries[0];p=r/x['file'];b=p.read_bytes();assert sha(b)==x['sha256'] and len(b)==x['bytes']
 with Image.open(p) as im:im.load();assert im.format=='PNG'
 selected.append({'member':f'images/{len(selected)+1:03d}-{client}-{p.name}','source_client':client,'browser_layer_status':result['status'],'source_result_sha256':sha((ev/client/'result.json').read_bytes()),'raw_metadata':x,'source_file':x['file'],'bytes':len(b),'sha256':sha(b),'pixels_edited':False})
for engine,before in [('chromium','before-chromium-v1'),('webkit','before-webkit-v2')]:
 for client in (before,f'after-{engine}-main-v1'):
  for suffix in ('1440x900-query.png','390x844-query.png','320x800-query.png','1440x900-management-expanded.png','320x800-management-expanded.png','1440x900-original-trace.png','actual-preview-page.png'):pick(client,suffix)
 for client,suffix in [(f'after-{engine}-required-v1','actual-required-natural-focused-source.png'),(f'after-{engine}-stress-v1','text-spacing-390.png'),(f'after-{engine}-long-v1','long-labels-320.png'),(f'after-{engine}-nojs-v1','nojs-320-summary.png'),(f'after-{engine}-zoom-preview-v2','native200-preview-version.png'),(f'after-{engine}-zoom-preview-v2','rootfont200-preview-version.png'),(f'after-{engine}-branches-v1','rich-320-management.png')]:pick(client,suffix)
pick('after-chromium-p1-narrow-v1','320-source-popup.png');pick('after-webkit-p1-narrow-v1','320-template-popup.png');pick('after-chromium-p1-narrow-v1','320-natural-Tab-ring-after-normal-scroll.png');pick('after-webkit-p1-narrow-v1','320-natural-Tab-ring-after-normal-scroll.png');pick('after-chromium-busy-v2','real-busy-search.png');pick('after-webkit-busy-v2','real-busy-preview.png')
measures=[]
for client in sorted({x['source_client'] for x in selected}):
 for p in sorted((ev/client).glob('*.json')):
  if p.name.startswith(('spacing-','text-spacing-','long-spacing-')):
   measures.append({'source':str(p.relative_to(r)),'sha256':sha(p.read_bytes()),'data':json.loads(p.read_text())})
readme='''# YDental DL-P9 私有只读效果包\n\nr2修正r1 README的before失败计数（实际2个），追加320两选择器弹层和同一自然Tab焦点正常滚动后的完整外圈原图；r1原字节保持，不反签其错误计数。\n\nPlan YD-S13-DL-P9 / 1.0。产品5f8f154；实际before ee15b39（产品P8），after7d02a16（只多状态文档）。\n\n只含原始PNG、截图元数据/空间测量、README和清单。不是可登录网页或用户已亲手验收；无原件PDF/DB/凭据/session/配置/程序/字体，不上传Public。\n\nimages按索引唯一命名；SCREENSHOTS.json列实际engine、角色、候选、视口、scrollY、root字号及原图SHA。前后同角色/条件/视口，scrollY分别记录，不称像素对齐。SPACING.json包含实际layout盒及computed；文字字形ink不当标签gap精度。\n\n正常/main、旧原件追溯/管理、required、无JS、真实busy为实际页面。长值、文本间距覆盖及rich/empty/previous分支为明确内存组件，不冒真实业务。native200与rootfont200分列。文本间距覆盖仅测试；不含修复CSS。\n\n真实busy图Chrome搜索/WK预览已实际捕捉spinner和status，不拦请求。WebKit stress-v1完整browser层/原图/native0已成，但外层wrapper终止143、Node退出UNKNOWN；保留分层，不反签整个wrapper成功。两个before失败与两个busy-v1普通工具失败原件另保本机，未覆盖。\n\nP8按钮内部、P1选择器JS/内部、原form合同/iframe正文/表格列单元padding保持；继承三块只顶层外距。320根Chrome345/WK333本轮前后同，旧根限制不冒已修复。\n\n推荐先对照1440/390/320查询，再看管理/追溯与预览，然后看键盘required、真实busy、两种放大和明确压力组件。最终技术及完整保护以三报告及未实现者收据为准。所有PNG未裁切、重采样或编辑。\n'''
members={'README.md':readme.encode(),'SCREENSHOTS.json':rawjson(selected),'SPACING.json':rawjson(measures)}
for x in selected:members[x['member']]=(r/x['source_file']).read_bytes()
manifest=[{'path':n,'bytes':len(b),'sha256':sha(b)} for n,b in members.items()]
members['MANIFEST.json']=rawjson({'nonself_members':manifest,'manifest_excludes_itself':True})
date=datetime.datetime.now(datetime.UTC).strftime('%Y%m%d');target=out/f'S13-DL-P9-view-only-{date}-r2.zip'
with target.open('xb') as stream:
 with zipfile.ZipFile(stream,'w',zipfile.ZIP_DEFLATED,compresslevel=9) as z:
  for n,b in members.items():z.writestr(n,b)
target.chmod(0o400)
with zipfile.ZipFile(target) as z:
 assert z.testzip() is None and set(z.namelist())==set(members)
 for n,b in members.items():assert z.read(n)==b
receipt={'status':'P9_PRIVATE_VIEWING_PACKAGE_CONSTRUCTED_NOT_INDEPENDENT_ACCEPTANCE','file':str(target.relative_to(r)),'bytes':target.stat().st_size,'sha256':sha(target.read_bytes()),'members':len(members),'original_PNG_count':len(selected),'measurement_records':len(measures),'pixels_edited':False,'public_upload':False}
p=out/'constructor-r2-result.json'
with os.fdopen(os.open(p,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600),'wb') as f:f.write(rawjson(receipt))
print(json.dumps(receipt))
