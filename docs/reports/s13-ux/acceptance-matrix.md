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

UX-F1—F5与UX-T01—T22均为待验证；逐项最终预期/实际/证据/层级由固定候选结果补齐，不能将总TODO当PASS。
