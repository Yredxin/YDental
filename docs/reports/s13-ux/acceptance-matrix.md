# S13 UX 验收矩阵

当前IN_PROGRESS；SOURCE/PURE、MODEL、HTTP/RPC、BROWSER、独立已提交RO/文件字节与逐页视觉分列。没有以基线或旧候选代本轮PASS。

|UX|实现位置|状态|
|---|---|---|
|01|ydental_reporting/models/ydental_reporting_presentation.py、views、zh_CN；文书用途层次|实现中，待动态|
|02|reporting授权选择器；settlement._patient_options；documents授权源患者查询；inventory过滤|实现中，待动态|
|03|settlement/ydental_print_service、print模板及zh_CN|实现中，待PDF|
|04|print公共QWeb及A4/80mm|实现中，待逐页|
|05|label100x70纸型及lab来源呈现|实现中，待QR/PDF|
|06|print公共层次、正常原件链|实现中，待逐页|
|07|frontend产品SCSS与局部表滚动|实现中，待两视口|
|08|settlement按需办理；followup终态表单条件|实现中，待正负例|

## 流程

|流程|实际覆盖|当前结论|
|---|---|---|
|UX-F1|报表选择、分摊、回源、返回；1073与新来源分核|NOT_RUN|
|UX-F2|旧SHA、部分收款、批准待退、实退、多账分摊新文件|NOT_RUN|
|UX-F3|旧label93与214当前、新100×70 QR被动定位|NOT_RUN|
|UX-F4|医生/结算/仓库普通业务信息查询|NOT_RUN|
|UX-F5|查看/进入/取消无经济变化、新源合法办理、closed后台拒|NOT_RUN|

## 逐项软件断言

|TC|预期与实际关注点|当前层级/结论|证据|
|---|---|---|---|
|UX-T01|12指标中文业务呈现，公式/key保持|SOURCE实现；动态NOT_RUN|候选a711d1e|
|UX-T02|USD0.01及发生/录入/生成时区分列|SOURCE实现；动态NOT_RUN|候选a711d1e|
|UX-T03|授权法人店币种/非法组合真实拒|SOURCE实现；动态NOT_RUN|候选a711d1e|
|UX-T04|三岗位业务搜索、同名、无结果、分页、最小读取|SOURCE实现；动态NOT_RUN|候选a711d1e|
|UX-T05|期间/当前账单群/当地日UTC边界|SOURCE契约保持；动态NOT_RUN|S12指标字典|
|UX-T06|分页/CSV/源集合/返回条件与明确上限拒|SOURCE实现；动态NOT_RUN|候选a711d1e|
|UX-T07|各受影响类别读/导出四组合与单份批量|HTTP/RPC NOT_RUN|待本候选|
|UX-T08|跨店公司/撤权旧页/附件/下载重核|HTTP/RPC NOT_RUN|待本候选|
|UX-T09|四结构A4各1页/80mm无裁切空页|PDF逐页NOT_RUN|待正常生成|
|UX-T10|长表/长正文/跨页表头/中文无缺失|PDF逐页NOT_RUN|待正常生成|
|UX-T11|100×70单张/QR解码/最小9pt/无副作用|PDF+QR+RO NOT_RUN|待正常生成|
|UX-T12|草稿/摘录/完整/作者/状态/用途不失真|PDF逐页NOT_RUN|待正常生成|
|UX-T13|1366×768、1440×900实际root无溢出|本轮BROWSER NOT_RUN|旧before仅对照|
|UX-T14|查看进入取消不改费库款审批责任|BROWSER+RO NOT_RUN|待本候选|
|UX-T15|改动办理普通有权新源正例/审批执行分开|BROWSER+独立提交NOT_RUN|待独立合成源|
|UX-T16|closed只读历史原因/直POST仍409/非终态正常|SOURCE修复；HTTP/BROWSER NOT_RUN|待本候选|
|UX-T17|全旧原件SHA/新版本/缺件不重生|baseline37附件保持；本轮post NOT_RUN|upgrade-initial-baseline/pre|
|UX-T18|旧账/分摊/价/退款/lot253/未完责任|完整即时pre成功；post NOT_RUN|upgrade-initial-pre|
|UX-T19|本改动失败及重复安全恢复|适用动态NOT_RUN；既有一致性证据分列|待本候选|
|UX-T20|最终候选必要限定升级/加载pre/post/退出及差异|即时pre成功；升级NOT_RUN|9429908d…|
|UX-T21|未实现者固定候选源码/全部PDF/两视口/实际提交|独立SOURCE局部修复复核；总验收NOT_RUN|acceptance私有材料|
|UX-T22|真实入口/效果包/同步读回/37OPEN/边界收口|IN_PROGRESS|本计划/summary|

NOT_RUN未冒PASS；SOURCE局部检查不能代动态、原始文件或最终独立结论。
