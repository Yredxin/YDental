# DL-P9 文书主页面间距与留白实施结果

[CODEX-FINAL] YD-S13-DL-P9 / 1.0

技术：待最终独立本地总签（已成分层结果见矩阵）
同步：SYNC_PENDING
用户亲手效果：待确认
完成范围：文书主页面间距与留白；继承三块仅外距；非全站
完整S13、后续页面、合并部署生产：未启用

[完整用户计划](../../execution/S13_DL_P9_IMPLEMENTATION_PLAN.md) · [P9-T01—12矩阵](acceptance-matrix.md) · [脱敏证据索引](evidence-index.md)。

## 固定候选与连续实施

- 从clean P8报告`756df60286d078a4243f87c885dc7a10de1f9b8b`正常建立`codex/s13-dl-p9-documents-spacing-r1`；P8产品`bd8411d4ef50014caddff7128f0c9cf4fe42f122`、唯一回执6406133603及P1—P8、P5 PARTIAL、旧包/失败/UNKNOWN保持，不reset/clean/强推/从文档main重建。P9是用户新增需求，不重开P8。
- 准备/本轮真实before `ee15b39f23bf30af737d86888355c24152d0991c`（产品仍P8）。产品固定 **5f8f15416521486f156e2932dd0b577c25d970f9**；实际唯一print-u及after运行 **7d02a16c429993e36971ce065bf78d56a4d72fb8**，只多状态文档，产品/当时工具字节一致。最终报告及已执行工具发布另单列，产品未再变。core `f0c5a9b42f544e7f18dc6c8e1c93b957837e0bcb`及既有synth OID2171423/cluster7694897083368259627/原filestore保持，无新库/克隆/改名。
- W0实际原生合成视图1618+扩展1621、en_US/zh_CN完整arch与已安装扩展已核，XPath仍`//details[@name='document_template_review']` before，三个继承details直接main子节点。无wrapper，字段/form边界/label关联/顺序/条件/权限/全部提交参数完整冻结；仅class/root marker剥离后两XML全canonical exact，原生翻译主123occ/116unique、继承38/36顺序全文同。
- W1/W2只7个addon文件：两XML、一个局部spacing SCSS、manifest最后单资产，以及三旧SCSS恰7处冲突间距声明删除。P8共享_actions.scss、documents_actions.scss及P1JS/内部控件/浮层算法、iframe正文/PDF、表格列/单元padding不改，无产品JS/后端/ACL/schema或全站主题变化。原native bundle实际549570B / SHA256 `d41e31b2236f34b0881001a892b9470ff63a2dac701fa1050280bc1034256f96`，GET及preview POST实际computed生效。
- root主控/唯一产品、报告、状态写者和运行调度；runtime_p9运行/保护工具及before服务，testing_p9测试工具/双引擎before，acceptance_p9未实现产品或相应工具者独立审查。同OS不冒隔离。测试和运行线程先后返回新的“Selected model is at capacity”，原事实保留，未换模型/agent/入口或重试线程；root接续其已准备工具并执行after/必要加载及普通工具修复，独立验收仍由acceptance_p9完成。不是单线程换称谓自签。

## 间距责任表（16px根字号，双引擎实测及独立复核）

|关系/明确layout边界|唯一负责人|目标/保持项|
|---|---|---|
|前模块border底→后模块border顶|后模块`spacing_module` leading margin|1.5rem；前模块bottom0；页头到页面上缘原1rem保持|
|搜索section border底→preview form border顶|preview form leading margin|1.5rem；hidden busy无盒，无泛化查询grid|
|query label盒底→可见input/trigger盒顶|query_field flex gap|.5rem；标签/字段margin0；P1内部padding/弹层保持|
|并列字段/字段最后一行→preview按钮|原query_preview grid gap|1rem已有合格值保持|
|query按钮→说明/busy|说明或状态leading margin|.75rem；bottom0，hidden不占位|
|已有header/query/originals卡片边界→内容|原卡片padding|桌面1.5rem；原45rem断点及以下1rem；每层一次|
|原header标题/用途/导航/说明、originals标题/说明/表格/分页|原容器gap与已清零子margin|1rem合格值保持，不把所有子组加24|
|预览标题/两追溯/iframe外框/生成form|明确preview容器gap|1rem；各直接子margin0；iframe内文及属性不改|
|版本label文字布局盒→原select|原label标记spacing_field flex gap|.5rem；标签不改关联/顺序|
|版本label组→生成按钮；管理字段/动作|原form标记spacing_form gap|1rem；隐藏字段不参与布局|
|目标summary底→第一正文盒顶|正文leading margin；原件dl保原margin|.75rem；只open后出现|
|旧查看/下载同组动作盒之间|原read_actions flex gap|.75rem已有合格值保持|
|读动作组底→打印details顶|打印details leading margin|.75rem；正文到打印按钮.75rem由正文bottom负责|
|原件追溯dt底→自己的dd顶|dd leading margin|.25rem；dl gap0；下一dt leading margin.75rem，首dt0|
|管理summary→说明→第一form|说明leading .75rem / form leading1rem|不叠默认p margin；两独立管理form之间后form leading1.5rem|
|继承临床/失败/同意三块外距|仅各顶层details spacing_module margin|1.5rem；内部所有样式/字段/动作冻结|

空间变化允许目标纵向位移、可用宽度和自然换行，不要求目标rect与P8全部相同。冻结映射：原form边界/label关联/字段顺序/type/name/value/action/method/target、csrf/revision/key/operation、hidden/required/disabled/权限/时机；P8按钮内部与spinner、P1JS及控件内部、iframe正文/PDF、表格列/单元padding、继承三块内部；库存/报表/结算与全局主题不改。


## 实证与允许空间变化

真实Chromium156.0.8078.4及WebKit27.2 WPE，本轮各自before与after均采1366×768、1440×900、768×1024、390×844、320×800。标签字段6→8px、搜索选择0→24px、模块16→24px；已有grid字段/动作16px、read动作12px、卡片24/16px保持。展开正文12px、版本/管理字段组16px、两独立管理form24px实测。匿名flex文字标签记录computed gap8及控件margin0，不把字形ink当8px布局盒精度。目标纵向位移/可用宽度/自然换行获准，冻结内部样式和数据另作strict比较。

两engine原生200%（native2/root16）与独立根字号200%（native1/root32）分列；首GET zoom层和后补readonly preview/版本组/五原写入口自然Tab分层。required实际键盘source focusVisible/2px外圈/无祖先裁切；320两P1 popup确认取消与边界实际成立、无POST。首自然Tab按钮贴视口边的原样本不称完整环全显；正常scroll后保持同active、无refocus的完整环可达另实测。原P1 JS/ARIA/native fallback/pageshow/reset源码合同及P8无影响行为精确复用，不声称重写控件。

真实trusted submit搜索与preview两engine busy宽高同，spinner不遮label、status到对应form12px、任务24px、内容流式下移；Chrome搜索/WK预览原PNG实际含busy。两engine真javaScriptEnabled=false同context正常认证、native select/summary/旧件读取/Tab可用。长中文label、混排说明及192字符hash组件五view首末可达；明确用户文本覆盖line-height1.6（至少1.5）、段后2em、字距.12em、词距.16em在1366/390/320成立，中文无词间空格不虚报词距效果。仅测试、不改默认、不注入修复CSS、不宣称整站WCAG/实机/屏读通过。

普通doctor9/store1无exportwrite：菜单/原GET查询图标文字Enter各单请求、原来源选择、显式preview、追溯、30+17旧原件分页保持；完整preview源只有一个精确原生提取UTC字段不同，全文prefix/suffix字节same。旧309→attachment15810，view/download实文件均57306B / SHA256 `b2d813eb1e4477aeb40810550f7fbd184a524aabc8be1cd1599441d70fe4a4e3`。Chrome viewer601B壳另与正常same-session真bytes分开；WebKit为实际native Download。none17两engine旧95 pdf_view/download真实各403（4读拒绝），空源disabled/说明保留；无临时grant或历史撤权全链重演。

写入口仅展开/收起/焦点及actual loaded QWeb无网络内存序列化。rich/empty/previous/result分支为原生loaded模板组件，不冒实际业务成功；closed details无正文空洞，无preview/result无占位。继承三块内部全冻结并与before actual computed逐项同。库存P7、原print页、报表、P1浮层有限样本strict同；结算仅`forms[8].fields[10].actual_utc`是原operation=pay文本框由controller91/模板145 `now_utc()`生成的渲染默认时间，精确原值保留，未支付/退款，其余样本same。320根本轮Chrome345/WK333前后各same，根因UNKNOWN/既有未改区限制保留，不冒全页零溢出或顺手修复。

## 加载、最终完整保护与收尾

唯一必要print-u即时完整pre `42fb99ef…`→实际exit0/ERROR0/noNative `9a135c5c…`→即时完整post `183144b3…`，未实现者独立全分类 `36b3a5543cb713e9517428242d83f1afaf2eb67f0cc99447735061a9839e935f`。仅25access/group69 write_date及8类原生技术元数据，39views只有主1618/继承1621 active arch改变、主arch_prev精确原before EN；其余37active arch、原4依赖逐值同。不为后续纯工具/报告再次-u。

最终root snapshot `23885cd2ffaae838a4519795531dfb7fdb99015b579db1ecd997b5cf2b5f8ed4`；未实现者独立新physical **465527** RO/RR/rollbackidle/closed，完整145业务/13技术/九区与root逐值exact，同事务4deps+83附件引用/80真实路径/80不同SHA逐引用真实bytes/size/SHA全保，三原生共享引用不删。最终独立保护 **0e86f0a1411a260fe0bcc728a764c32aeb732e42b5d3fd6daa0dae3f397d2816**。旧17812audit逐行保，新205=201accepted正常认证/读取+4旧PDF读denied；原category export拒绝不冒bulk export。金额库存/身份作者价源/责任/schema/config/原件保持，旧AR1303、lot253收10/用2/余8是来源保护事实；新业务原件/PDF生成/打印/模板创建审核发布/签署/经济库存/继承业务均0。

after owned run `20261026T021012Z-d241867b77e3` 于 **2026-10-26T02:30:15.610853Z** 正常stop/foreground0/child0/signull/groupstopped，before亦正常0。独立OS **7e5d6e7c6bc63baaeb0639e28a74b24e8b93c436777b3bfce89c233fdbda0f4c** 核2owned/34native浏览器0、owner/端口18411和12/profile/已知进程空，freshRO465768其它target连接[]。未动共享主服务，不为报告复开。

## 包、失败与限制

最终私有0400 **r2**包 `.local/dl-p9/viewing/S13-DL-P9-view-only-20261026-r2.zip`：**5,039,889B / SHA256 9796854834e8a350d7ab618bb4a6c6d68a8a486dd82fe4bbe0499603f7e8529e**，52成员/48原PNG/152空间测量。r1原4,756,055B/b3ee8f…保留；r2修r1 README误写before失败数3（实际2），追加320弹层/同active正常scroll完整环4图，未编辑原图、不覆盖r1或P8包。包只原PNG/README/索引/manifest，无PDF/DB/秘密/session/config/program/font，不上传Public。

34actual clients=29 Node0/4 Node2/1 NodeUNKNOWN，34native浏览器均0；236唯一原PNG路径/181不同SHA逐源字节和解码核。4失败为before WebKit登录导航竞态、before不存在角色alias，以及两busy-v1 popup滚动等待；普通工具定向修复，原件/原退出保留。WebKit stress-v1完整17浏览器断言/8图/native0/contexts正常已获独立浏览器层签，但外层shell143、Node退出UNKNOWN/原因UNKNOWN，不反签整个wrapper成功，不为补报告重放已成层。所有禁止业务POST及预拦截guard0。

原生准入独占文件/dirty或候选preflight在native dispatch前拒绝、比较工具iframe投影shape和索引wrapper误计、结算时间字段误认refund等离线工具错误保留；正常修正而非产品改变、没有未知写提交重试。最终工具源码发布已实际执行的私有变体，源/依赖/argv/退出逐client固定；不是把所有client冒成同一最终工具文件运行。

用户亲手效果、真实OS IME/屏读/设备/Safari/iOS、正式临床财务政策、完整S13/负载恢复/组合扫码/真实患者资金外部通道/生产均未启用。技术签署和截图不代用户效果。

## 普通岗位7步复现

1. 在正常有效运行窗口，普通医生登录并选自己的授权门店，从菜单进入“文书与原件”。
2. 用患者姓名或业务号查询，观察搜索与来源选择分为两个任务组；用Enter或查询按钮执行原GET。
3. 打开来源及正文模板选择器，确认或取消，再显式预览；不要生成原件。
4. 只读展开来源/模板追溯，观察summary到正文及预览/前版选择/生成按钮的分组；仅Tab聚焦生成按钮。
5. 展开旧原件追溯，查看/下载同一旧文件，使用原前后页；不请求打印。
6. 仅展开/收起页尾模板管理、导出及继承入口，观察字段/说明/按钮间隔，不提交任何业务。
7. 在320/390窄屏及两种200%下检查分组、弹层、键盘焦点和长表局部横读。服务已正常收尾；复现须当前正常新准入，不能恢复旧时间/STOP或把服务器127地址当远端用户入口。

## 同步与停止

本地最终总签及正常commit/push、main两必要路由、#37唯一P9最终结果/旧10评论、#37OPEN/#36CLOSED实际读回另按已发生事实更新。未同步不写SYNCED；不循环自嵌未来自身hash，不为元数据重复软件/数据库/包验收。

P9交付后停止。后续报表/结算/库存或其它页面推广、完整S13、合并部署生产未启用。
