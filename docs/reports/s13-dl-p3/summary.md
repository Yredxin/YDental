# DL-P3：已保存原件列表、状态、分页与只读追溯

`[CODEX-FINAL] YD-S13-DL-P3 / 1.0`

技术：IN_PROGRESS；同步：NOT_YET_SYNCED。此为本地实施记录，尚非最终验收结论。
用户亲手效果：待确认；P3启用不代表P1/P2已获亲手验收。
完整S13未完成，#37保持OPEN，#36保持CLOSED；P4—P6、生产和产品合并未启用。

## 范围、承接与固定候选

按用户本会话交付的[完整计划](../../execution/S13_DL_P3_IMPLEMENTATION_PLAN.md)连续实施W0—W4，沿用[杏陶暖白设计语言](../../design/YDENTAL_DESIGN_LANGUAGE_V1.md)。只改文书页已保存原件列表至分页/空态；Operation accepted/Operation trace、P1/P2区域、预览/生成、管理/导出、打印请求子树、后台原件/ACL/PDF与共用网站页头冻结。

活动分支`codex/s13-dl-p3-documents-originals-r1`从现场合法P2报告HEAD `1d3fe088c029e0d9562325b2895a64ac31945b71`承接；开工工作树干净，未假定旧P1补记仍未提交，未reset/clean/强推或从main重建。P2产品`a0b33c14c121f2a489fdcf7abc529999fd15c1dd`与旧回执6391318665、P1旧产品/报告/回执6384111913保持。main仅必要文档路由。

|对象|实际锚点|
|---|---|
|初准备|2cfd141adb04b3929af411d9a835fa4165d1bb72；阶段适配/完整计划，addon仍P2|
|工具普通修复|3a30457a8e0f7b3e491e8446f4e04b1284aa47ff；独立检查发现tuple.exists，前向改两个Path检查|
|真实前态执行|d4a94d0eee832cadf82d3c089afd53308b4096b2；仅CURRENT记录补充，产品仍P2|
|最终产品/执行|待冻结与实际验证|
|core|f0c5a9b42f544e7f18dc6c8e1c93b957837e0bcb，未改|

真实团队：root主控/环境/集成/报告/权限定向HTTP；documents唯一4产品文件写者；tester私有工具和真实浏览器；acceptance未实现产品或测试工具，独立源码、实际图/请求/bytes、完整新物理RO和同步验收。同OS共享，不冒隔离。适用[矩阵](acceptance-matrix.md)与[证据索引](evidence-index.md)区分各层级。

## 字段、历史状态与文案映射

SOURCE基于当前锁定`ydental_print/models/ydental_print_original_service.py::_original_workbench`、`_original_snapshot_status`及controller，原件模型`_order='id desc'`，不是重新按生成时间排序。完整授权后计数，30/页，保持现行页码钳制和`search_url`以urlencode保留q/page。

|字段/内容|原实际来源与保留语义|
|---|---|
|patient_name/patient_number|original.patient_id当前主档name/ydental_number；不是冻结历史姓名/号声明|
|title|kind_labels按原件kind投影文书用途；不是source_facts.frozen_title|
|version|原件自身version，不冒来源版本|
|status|原件冻结source_facts经既有_snapshot_status投影，非当前工单/账务状态；无稳定状态键时中性呈现原文字|
|generated_at|str(original.generated_at)，明确UTC；非就诊/治疗时间或文件mtime|
|synthetic|template_facts['synthetic']；适用审核/签署限制保持默认可见|
|id|原件原ID，保持表单original_id及展开追溯；用户无需手填|
|trace|原服务14键、原值、原顺序完整保留；键标签辅助阅读，不解析翻译后的状态字符串|

trace原序：pdf_sha256、original_id、previous_original_id、source_model、source_id、source_version、source_sha256、template_sha256、layout_version、template、template_version、frozen_title、details、versions。hash只视觉换行，原值/复制文字不插字或截断。QWeb转义，不用t-raw/innerHTML、不新增追溯接口/JS/可执行链接。

旧93生成draft与工单214当前sent分属历史与当前，旧95/96/99范围和版本不改；文件已保存不等于临床全部完成或已签署，不为截图改名、模板、状态或数据。

## 实证、文件与权限

待最终候选实际完成后填写。SOURCE、PURE、MODEL/HTTP、BROWSER、原生AX和独立已提交RO各列，不互冒。P1门店/revision/撤权固定证据按未变后台源码复用，P3只做受影响单份查看/下载的定向正负例，不称重跑P1全套。

## 保护与服务事实

唯一目标`ydental_s11_synth_20261023_01 / OID2171423 / cluster7694897083368259627`及原filestore。运行前root完整RO145业务表/13技术表/83实际文件，与P2最终九个保护区段逐值全同；未实现者另用新物理RO/RR backend77211独立全采并匹配，实际rollback idle/closed。83为现场承接数量，不是永久硬编码。65内部+2外部旧原件和金额/库存/审计/责任保护，最终以收口完整核验为准。

固定旧来源1073＋前批230＝1303，P3经济库存贡献0；不能把所有未来查询总额硬编码1303。lot253收10用2余8与历史未完责任不重放、不假完成。正常访问/拒绝审计、必要技术元数据和明确授权恢复fence按事实分类，不称全库物理零diff。

P3新自有资源scope至2026-10-25T12:51:43UTC，未改旧scope或STOP；有效期限不表示服务在线。末服务终态待实际正常收尾后补。

## 首失败、普通修复、UNKNOWN和未验证

- 新工具首系统python缺psycopg2，改用既有项目venv，7项阶段边界PURE通过；不冒业务测试。
- 新P3父目录mkdir -p继承775触发原private检查，修自有新目录为700，未放宽检查；首probe只读完成但receipt未写，随后fresh probe/完整baseline成功。
- 独立源码发现新stage owner表达式tuple.exists，真实加载前前向修复；正常start要求完全clean，原CURRENT补记正常提交后重新绑定准入，未绕过原检查。
- GitHub已读取大正文保存因E2BIG未能创建shell，改为同一已读取内容分块本地保存，未改服务入口。
- before-v1实际读取47授权原件/2页；截图工具匹配既有第二个table而strict失败，正常关闭，无业务提交；工具改唯一原件表定位后定向补采，旧失败保留。
- 原before追溯工具未检查相邻DD，10个空previous_original_id误吃下一DT；原result保留。已补只47个实际授权原件的14键源事实RO(backend79010/RR/rollback closed)，结合原all_cell_texts建立明确纠正派生，不冒before DOM重采；产品只语义保留空dd容器，False仍空文本。
- 历史Native139、Firefox中文tofu、WebKit初始化404及其他UNKNOWN保持；不追溯确诊，也不因新成功倒签根因。
- 自动化浏览器不冒用户亲手、真实屏幕阅读器/OS输入法/设备验收。WebKit不等于真实Safari/iOS。正式政策、生产、负载/恢复和完整S13未启用。

## 私有包、普通角色复现、同步与停止

待实际包/独立验收/同步读回后填写；原始截图、旧PDF复制、凭据/provider、原始请求及完整保护证据不上传Public。包校验不单独证明业务正确性或全部原始数据库证据。
