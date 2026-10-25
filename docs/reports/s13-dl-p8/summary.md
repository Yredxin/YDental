# DL-P8 文书主页面动作控件与SVG实施结果

YD-S13-DL-P8 / 1.0；当前实施中，必需动态与独立验收尚未完成，不能据此声明技术完成或同步成功。用户亲手效果待确认。

[完整用户计划](../../execution/S13_DL_P8_IMPLEMENTATION_PLAN.md)。产品承接P7最终9f5ce462（实际产品52d5422），正常创建`codex/s13-dl-p8-documents-actions-icons-r1`，未reset/clean/强推/从文档main重建。P1—P7交付及P5 PARTIAL、旧包/失败/UNKNOWN保持；P8后停止，不启报表/结算/其它页面、完整S13/实机/政策/真实患者资金或外部通道/合并部署生产。

## 目标控件与冻结边界

静态定义25个呈现节点=9button/7summary/7a/2h2；循环行产生多份真实控件，不混算。P1两动态combobox是字段，不纳入动作按钮；现有`ydental_document_consent_page`继承的临床集合、设备故障和同意上传/核验入口及表格亦保持，不新增P8 opt-in。

|族|定义|变体|图标|提交边界|
|---|---:|---|---|---|
|搜索|1button|secondary|search前置|原GET/q/Enter/P1 busy|
|显式预览|1button|primary|无|允许原POST preview已有来源HTML|
|生成并留存|1button|primary|无|禁止live generate，仅焦点/内存合同|
|查看/下载旧件|2button|quiet/secondary|查看后置arrow-right|允许旧pdf_view/download，实际bytes单列|
|打印请求|1button|secondary|无|禁止live print_request|
|创建未审核模板/记录审核|2button|各表单primary|无|禁止live template_create/template_review/publish|
|ZIP导出|1button|secondary|无|禁止live export|
|2源追溯/操作追溯/原件追溯/打印/模板/导出|7summary|disclosure|无|原生marker/name/条件/Enter/Space|
|五工作区链接|5a|quiet|无|原href及两分组/顺序|
|前/后页|2a|secondary|chevron-left/right|原q/page/首末span|
|查询/原件两区域标题|2h2|原标题|list|原标题文字/层级/关联|

允许变更仅class、元素opt-in、静态SVG、原词span/translation边界及目标动作专属CSS。全部原字段/action/method/target/type/name/value/csrf/revision/key/operation/required/disabled/权限/顺序/P1JS/iframe/PDF/后端保持。GET与preview POST同一主模板元素opt-in，不以pathname误门控。

## 实施与验证进度

工具准备01590374c6306f66e03b2d2449971b363b2dd44c，产品仍P7。全新scope与独立pre已实际采成；产品暂存在私有目录等待before补采。最终固定候选、适用12项、原件读取字节、完整独立保护、私有包、正常收尾和远端读回将按实际结果补入。
