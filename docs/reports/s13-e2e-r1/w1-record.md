# E2E-W1 阶段记录

计划：YD-S13-E2E-R1 / 1.1。状态：**PARTIAL；W1 门槛尚未全部满足**。本记录由新建 C-W1 维护；A 的原始观察、B 的独立复测和主控裁定分别保存，不将未经复核的观察计为产品缺陷。

## 承接和边界

- 主控判定 [W0 限定准出](w0-record.md)。起始产品候选 `83d5a002ee29dbb10177c773a81f7c2acae8b583`，报告基线 HEAD `6b28f5ed4192610e9bbb535f6013d08f66ba85a6`，分支 `codex/s13-e2e-r1`。具体 W1 实测版本、运行范围与环境须按实际运行记录，不以此代签。
- W0 已验证合成目标身份、合法管理员表单入口及历史保护，并记录用户对内网环境的确认。W0 的客户端拦截、旧权限拒绝、保护证据及其限制继续保留；旧经济、库存、文书、附件、审计及未完成责任不得覆盖或盲目重放。
- W1 使用新的 A、B、C 团队及本阶段独立运行范围；所有业务写入由主控协调。各账号使用独立浏览器 Context 正常表单登录，结束关闭；密码、认证材料和 Session 不纳入本记录或公开报告。

## W1 门槛

| 门槛 | 状态 | 实际证据和限制 |
|---|---|---|
| 11 个指定账号的存在性、合法创建或冲突处理 | IN_PROGRESS | 第一账号已创建，配置不完整；其余待现场执行与独立读回 |
| 每个账号正常表单登录及实际 UID、员工、门店、岗位权限 | IN_PROGRESS | 11 个账号已独立表单登录；当前店、岗位授权仍待配置和验证 |
| A/B 门店、区域、工位、人员安排及合法容量 | IN_PROGRESS | 两门店已独立读回，其余待配置与验证 |
| 测试项目、价格版本、药品与耗材主数据及合法初始批次 | NOT_RUN | 待记录真实配置与来源 |
| 明确标记的合成患者和必要数据 | IN_PROGRESS | 患者 1644 已建档，后续流程待 W2 |
| W1 独立复核、保护、资源收尾与阶段准出 | PARTIAL | B 已独立终验和停止核查；可售、耗材库存及部分业务权限仍未验证 |

## A 原始发现

**OBSERVED，等待 B 独立复核。** A/B 的只读调查显示 UID 2 有 Odoo 系统管理员权限，但不属于 YDental 集团管理组；不能仅凭系统管理员身份认定其拥有该业务授权。UID 5 为既有正常 provider 中的集团管理者。A 在本阶段实际使用 UID 5 正常表单登录，已认证 RPC 返回 YDental 集团管理组为 true、`res.users` 创建权限为 false；访问管理页 GET 返回 200。独立 Context/browser 关闭，浏览器及服务退出码均为 0；这些事实来自 A，尚不代表 UAT 账号已创建或 W1 通过。

- A 原始证据 `.local/s13-e2e-r1/w1/a-group-manager/result.json` SHA-256 `fc49ff8362eaa1940a430b03b0a3fc0ca5ff6c7bff2381b13cdd9fb0386c8d53`；C 实际核对文件 SHA。原结果 `system_group` 字段为采集器命名，A 的客户端源码实际调用的是 `ydental_access.ydental_group_manager`，不能将该值误记为 Odoo 系统管理员组。
- 两项请求被测试客户端拦截，原因和请求未采集，保留 UNKNOWN；不能作为服务端拒绝或整个页面通过的证据。是否产生认证或审计提交及其独立保护读回待 B 核实；本观察不能替代账号初始化。
- **OBSERVED／待提交读回：** A 以 UID 5 正常表单登录，执行首次门店动作，请求 HTTP 200 返回 ID 541。客户端两项拦截为 UNKNOWN；browser 与服务退出码均 0。该结果只标记 `REQUEST_ACCEPTED_NEEDS_READBACK`，B 的独立物理读回尚在进行；不得判已提交、产品通过或安全重复。
  原始目录 `.local/s13-e2e-r1/w1/step-20261027T073713-86845002e71f/` 中 `result.json` SHA-256 `e7394fc7440b0907854255790064b510d22bd6368bf98fa4cd452f9690a2e658`，`intent.json` SHA-256 `17e2a5c5fd161fbd7565036b0013b74fc7d77f98577cfd67b411498d11960086`；C 已实际核对文件 SHA，运行事实来自 A。

## B 独立复测和主控裁定

**进行中。** B 独立登录后只读保护核查报告：相对 P13 基线，145 业务表的旧行保全，审计新增 9 条（W0 六条及本次 UID 5 三条）；13 技术表、7 附加保护区及 83 引用／80 文件保全，11 个 UAT 账号仍不存在。另有本次进程、端口退出及日志核查；具体查询与保护结论来自 B，不据此代称 UAT 登录或账号创建通过。

- 私有原件 `.local/s13-e2e-r1/b-w1/after-group-manager-protection.json` SHA-256 `63b515d9221216f675ba0d3ec21e5d9832b38ac5dc094439532c4a829360b984`；`after-group-manager-independent.json` SHA-256 `889b0995c431708955e74f6e21e949807c387edad4d287c01ab0b1776d83477d`。C 独立核对文件 SHA；现场读取与业务结论来自 B。
- **A 店独立已提交读回：** B 新建物理 RO/RR 连接证实门店 ID 541 已创建，company 1、时区 Asia/Shanghai；membership 2525 关联现有 UID 5 与员工 1。旧记录无改删，技术与附件投影保持，新增五条正常审计。此次物理读回确认该门店的持久结果；A 原 HTTP 结果和两项客户端拦截 UNKNOWN 仍分别保留，不扩大为 W1 整体通过。
- 该读回私有保护证据 `.local/s13-e2e-r1/b-w1/after-store-a-protection.json` SHA-256 `5e474bebaba99972242d7a9f7dd3bfbc338c6d562b16a57b257671d54bde7dac`；对应步骤的 `independent.json` SHA-256 `c6419a5aa57798488b631053ac63330c63ebb0688a8307e1955fe8c5afe8bf55`。C 已核对文件 SHA；数据库查询与业务结论来自 B。
- B 店 542 已独立读回提交，步骤 `step-20261027T074005-7dea6736044f/independent.json` SHA-256 `ef327a22745249667b77b025717fd4f843f5d93997e82890910a383e92c11ca5`。首个账号 `uat_admin` 已创建：UID 1541、员工 1497、A 店会员 2527；尚无密码、管理员组或业务 grant，不代表账号配置或登录完成。独立读回 `step-20261027T074341-5a692660f96a/independent.json` SHA-256 `35a9c5904b8d8874ae0df93ebd2c478d6826cafeea462e8c19c01691c2a4578e`。两文件均位于 `.local/s13-e2e-r1/w1/`，C 已核对其实际 SHA；现场查询结论来自 B。
- B 后续新物理只读事务独立确认十个账号及其 A 店关联已提交；均仅基础组、无业务 grant 和密码。下列原件均位于 `.local/s13-e2e-r1/w1/` 的对应步骤目录，C 已核对文件 SHA；人员状态不代表岗位权限或正常登录已验收。

  | 账号 | UID／员工／会员 | 步骤目录与 `independent.json` SHA-256 |
  |---|---|---|
  | `uat_manager_a` | 1542／1498／2528 | `step-20261027T074549-7842b4995aa3` / `8ad997d96deb7d865e3b973b334c15bb115c8a88c777ab6d09dc417f7771f17b` |
  | `uat_frontdesk_a` | 1543／1499／2529 | `step-20261027T074746-34426872db3c` / `ba2469c2846675bebe35c82f9a52c2caaf08e2af178c130bf80c11b265105210` |
  | `uat_doctor_a` | 1544／1500／2530 | `step-20261027T074915-0ab248e99561` / `02731b9fb31ddb6129b1f26ea4c99614ebdddd45d7384735e1b0708ef7f4b79e` |
  | `uat_exam_a` | 1545／1501／2531 | `step-20261027T075045-b65e167ddbb1` / `3e2358e167836005e5f5ff0ebb03b93502dd2e115ad0e215ae30567fcdb32fbb` |
  | `uat_pharmacy_a` | 1546／1502／2532 | `step-20261027T075157-3734eabcf7a1` / `9143b8b7fa1cff3233efdb8d9dd9c506ae2d7f1c1ada86849b34594308a07b6f` |
  | `uat_stock_a` | 1547／1503／2533 | `step-20261027T075308-ec79ed8bfc3e` / `f9b154c6a8892cc837f3ebbe0d2806bd64f625c223df388b8d905c713ea4ec88` |
  | `uat_cashier_a` | 1548／1504／2534 | `step-20261027T075416-b6f2ca181ee9` / `4c7018400b4181c89a70f81d4f8d7f0751cb499d80c775398b3495f296db4535` |
  | `uat_approver_a` | 1549／1505／2535 | `step-20261027T075529-40e178bf5637` / `3e1541aa5c2305832ebeb7108531275d9450fbffa8a2e423e12888177f68de7f` |
  | `uat_cross_store` | 1550／1506／2536 | `step-20261027T075650-c39bacf83841` / `cf2581cc68eadf6bd6a162cee369c0d016d7a991357f55209040277cac451153` |
  | `uat_denied` | 1551／1507／2537 | `step-20261027T075801-921ef384fea0` / `c38381eea6dd55531c05758d9286aeca8321282c6c9b64f89358165e232eddb1` |

  店长及前台步骤具有全保护投影；医生及之后步骤为目标用户、员工、会员、组、公司及审计定向读回，不将定向证据扩大为全保护通过。
- `uat_admin` 的 B 店会员 2538 沿用员工 1497；`uat_cross_store` 的 B 店会员 2539 沿用员工 1506，均由 B 定向独立读回提交。对应步骤 `step-20261027T075915-02818fd3e8c4/independent.json` SHA-256 `baefe6ff240512bae59006dc2177248506716d7b9cd07d045f89c4a36a159ef7`、`step-20261027T080151-5b91c1b609c3/independent.json` SHA-256 `408c8ed90a94ed74bcc2deae417b3814de5796a9a5aed488fa0a423acdcc49e9`；C 已核对原件哈希。11 个账号均已创建，密码、业务授权与正常登录仍待完成。
- **风险／提交待核：** A 在收到暂停指令前，对 `uat_admin` UID 1541 发出了唯一密码设置请求，步骤目录 `step-20261027T080447-17e5e9cdae57`；B 正独立只读核实该请求是否提交，不能根据此条认定设置成功或登录通过。此前“密码未设”为创建时点事实。请求值曾作为 `write_stdin` 工具参数传入；PTY 无回显不能证明工具会话记录未保存输入，是否持久记录为 UNKNOWN。固定密码后续操作暂停；此处不读取或记录请求参数、密码或密码哈希。
- B 随后独立只读检查 UID 1541 的写入元数据并确认本次服务停止；结合 HTTP 200 仍不能证明密码值已提交或可登录，故该请求结果维持 **UNKNOWN**，没有读取密码或密码哈希，也没有独立验收闸口回执。证据 `.local/s13-e2e-r1/b-w1/password-admin-readback-unknown.json` SHA-256 `d4ea408787ac3c1043e4f70c1514f127e6aaab4926bc877cc1921ad752c3c4e9`；C 已核对文件 SHA，查询事实来自 B。
- 当前未确认工具有不记录输入的秘密接口；主控已向用户询问安全传递方式或约束调整。固定密码设置和相关登录继续暂停，A 只处理独立的 `web.base.url` 收尾；不得把 HTTP 或元数据推断成账号登录成功。
- 后续用户明确允许本次合成测试账号密码保存在工具／会话记录中；此确认之后按该范围继续，公开报告和截图仍不重复密码。原先工具输入及其是否持久记录的 UNKNOWN 保留。B 准备独立正常表单验证 `uat_admin`；原密码请求结果尚未由登录解决，不能预先判通过。
- 后续 B 用新 Context 实际正常表单登录 `uat_admin`，获得 UID 1541，确认三个管理员组并取得管理页 GET 200；本次实际当前门店显示未选择，两个门店仅为可选关联，不能写作当前店已选。两项测试客户端拦截仍为 UNKNOWN。首次非 PTY 输入 EOF、退出 1 且未登录；随后唯一实际登录运行退出 0，原失败保留。独立登录结果 `.local/s13-e2e-r1/w1/b-admin-login/result.json` SHA-256 `465f56862bf62668dd1532d0f6ed697fcb5d293326c3836a9f5560a3424a8c40`；原密码步骤的 `independent.json` SHA-256 `eacf6991cbc0a5940f486898a0a3e7fcf75eead743081340c694247da4a2ff7e`，C 已核对两文件 SHA。此次实际登录及 B 的独立读回支持该账号当前密码和身份可用，原先提交 UNKNOWN 是当时事实，不倒签。
- 系统管理员本次登录再次将 `web.base.url` 原生改为本次回环 18511；阶段收尾须恢复先前值并独立读回，不把当前状态写成已经恢复。
- B 独立正常表单登录 `uat_manager_a`，实际 UID 1542，A 店会员存在，但当前店未选、无管理员组、业务 grant 或店长任命；仅登录事实成立，岗位权限尚未配置和验收。密码步骤独立回执 `.local/s13-e2e-r1/w1/step-20261027T081448-fa1e4e593937/independent.json` SHA-256 `f6812d82022b16d7103da7d380a1b44b7d94ef6e6f4d8be13791337d895b09c5`；登录结果 `.local/s13-e2e-r1/b-w1/login-uat_manager_a/result.json` SHA-256 `c6ece3f497c76230ec7e24e949241452ade9834d04e9a4538c2b47998721d9c0`。C 已核对文件 SHA，操作和结论来自 B。
- B 随后分别使用独立 Context 的真实登录表单验证 `uat_frontdesk_a` UID 1543、`uat_doctor_a` UID 1544、`uat_exam_a` UID 1545；A 店会员存在，当前店未选，均无管理员组或业务 grant，不能将登录通过冒充岗位权限通过。各自登录结果在 `.local/s13-e2e-r1/b-w1/login-<账号>/result.json`，SHA-256 依次为 `769afc4da9b9b857919048b32419c87a2e659608cdc5cc94b1c032ce8400ac7b`、`a9d7889d8cfd6b47c4a216fd879bc4ad3c0342f0d111edba91c12c6386b083de`、`28c5a9dcb00af0e04ab58dce0165149ba11442aeff4d9f8c9518a46d18da0a0f`。相应步骤的独立提交回执依次为 `.local/s13-e2e-r1/w1/step-20261027T082827-8c3920f6698b/independent.json` SHA-256 `d8343efffe68fafc037b4d6000d946c89c4fcfa7132fbda47bd708ee242a461b`、`step-20261027T082959-fe03d42543eb/independent.json` SHA-256 `d88a61af2ef756b9d5a420275874f42158ae105251c8e85052c0cf412181a6ed`、`step-20261027T083131-23418deee22e/independent.json` SHA-256 `642f09b5756db5039dbebc308418bd022f8b04beb77d3c0113840b96f1c5bd8f`。C 核对六文件哈希；现场操作和结论来自 B。
- B 继续独立正常表单登录 `uat_pharmacy_a` UID 1546、`uat_stock_a` UID 1547、`uat_cashier_a` UID 1548、`uat_approver_a` UID 1549；均有 A 店会员、当前店未选、无业务 grant，登录通过不等于岗位通过。C 已核对各私有结果和独立回执文件 SHA；现场事实来自 B。

  | 账号 | `b-w1/login-<账号>/result.json` SHA-256 | `w1/<步骤>/independent.json` 步骤及 SHA-256 |
  |---|---|---|
  | `uat_pharmacy_a` | `30d773060dea6cc456a721bf8503fa23c6304398bc6ea24fe59e7a311724445f` | `step-20261027T083320-b0f5d1359add` / `2cbe170b088a06305ec4ab3ed962c3770a3f23f629852451bc4f2425c799d350` |
  | `uat_stock_a` | `42691ad8ca3972416f8e1aa6886bc203636d3f18cb430a1a53f66ed1e4529d18` | `step-20261027T083504-3e562174f5bb` / `d6f099172beb8527177b72ac2ee529b068dbaf3b2fef94f51a7d7ff6b4171509` |
  | `uat_cashier_a` | `cb7dacaa421448aa9072cf1c896d76a7d9e910ffeccb29cf23182537bbf238ae` | `step-20261027T083647-9db56702e585` / `8274eb47f55c8a97d63d49304735d9dc65b46adcdb3a359623e34a44cfb79899` |
  | `uat_approver_a` | `332457192e82105de63a378af9a0390181129ccb27d30638d0f4882f4fe47cc8` | `step-20261027T083814-4aad1f2bf8c1` / `60f1fbf907497e33ecc88e13eec34b00c73429dbdcd710f13ba1cfa51d7514df` |
- B 最后独立真实表单登录 `uat_cross_store` UID 1550（关联 A/B 店）与 `uat_denied` UID 1551（关联 A 店），两者当前店均未选、无业务 grant。至此 11/11 账号以计划指定的初始口令实际登录，但当前店及岗位权限尚未验收，不能宣称 W1 准出。登录结果分别为 `.local/s13-e2e-r1/b-w1/login-uat_cross_store/result.json` SHA-256 `1d1a4795bbbc7f9a992cf0136a82c169db386c03e1c32b753de5717847d31ac7` 与 `login-uat_denied/result.json` SHA-256 `8608d40889bf15c1fc56ad203f01e7fd1d30d90e97fa01fb16b9c3d461abf5c7`；相应步骤独立回执分别为 `.local/s13-e2e-r1/w1/step-20261027T083925-c47e90de8fee/independent.json` SHA-256 `f9f60846dbd15b5a4190a31356d056959774ee8bc1c870c65a39cd041e5d1416` 与 `step-20261027T084041-b1f319ee40ed/independent.json` SHA-256 `c1649f5cec30727897558be8b21c5c3cfd992ae19db65292b7f2a223a4037675`。C 核对四文件 SHA，执行与身份结论来自 B。
- 后续 B 新物理只读独立证实授权提交：`uat_admin` A/B 店各有 `personnel`、`space`、`capacity`、`price`、`medical` 的 write；`uat_manager_a` 在 A 店有前四类 write，且已任命为店长；`uat_frontdesk_a` A 店有 `frontdesk` write；`uat_doctor_a` A 店有 `medical` write。以上各项无额外 grant；早先“无 grant／未任命”为对应登录时点事实。此为已提交配置读回，不能代替实际岗位菜单及权限正负向测试。

  | 动作 | `.local/s13-e2e-r1/w1/<步骤>/independent.json` 目录与 SHA-256 |
  |---|---|
  | admin A 店 grant | `step-20261027T084239-adbad88d06eb` / `924ff5c7fa5d47c9ed9daec7f7c97add0a917c1b1a35e49f973322af15566d6e` |
  | admin B 店 grant | `step-20261027T084348-a30f406d69e2` / `61c25fcda48bc67f50ee72dd9d1c576863e011616be8731b7927427f1f3049af` |
  | manager A 店 grant | `step-20261027T084439-257e3978350f` / `6d76521f8748f340398350619e17060b73ad92f26eb58072b3655f8b4e1b7e71` |
  | manager 店长任命 | `step-20261027T084520-c7cd6a1ae6d9` / `731d4d7b675a4644f49b4a788081f07534015c8a5a9cb1a0c7d991ec15e31f2d` |
  | frontdesk A 店 grant | `step-20261027T084611-d0e05128e4c5` / `50b30b19b4539b9869d85999cab11f5e997d829bbe6051d2cc1c01609b187454` |
  | doctor A 店 grant | `step-20261027T084719-944d8b1b5fcf` / `d95d54edfc78c3d4b1c76c15711c283a09c90df5a859bcd4d557cf894c8349bb` |
  | exam A 店 `exam` write | `step-20261027T084810-5aed8030766a` / `a64bd2c419f9cbfbe6dc13f1372ad7addb2e49dd71fbea18703e6b5108548276` |
  | pharmacy A 店 `pharmacy` write | `step-20261027T084847-fed8e96de1be` / `fe542055fee7603a685aaeacbab6d3b764b9337f08aef128fc3469b04a78e219` |
  | stock A 店 `warehouse` write | `step-20261027T084935-e7929df4515e` / `a6686acaf3dffb5447f7c887299f249ae0a35cc066e46d0ce05526163eac1aea` |
  | cashier A 店 `settlement` write | `step-20261027T085018-82bd2671b5d7` / `2d41f37deb37feafe6f95214e080b9f202dd6f7d82b6e319a357375cac749293` |
  | approver A 店 `finance_approval` write | `step-20261027T085057-b4e44d4e141e` / `97e49618f12642dc0ae6501500ec3fdb576701260708e532f3b3788c2bf31590` |
  | cross_store A 店 `medical` write | `step-20261027T085132-4f9d66333226` / `f02f20fe21c5f61adc26cee1cf3001bb1f21531d7ed521cbee290e0ab3443181` |
  | cross_store B 店 `medical` read | `step-20261027T085302-b7b1c11a3da4` / `7d308de20afd0ebf77dc21c890499121262fd78cb265ca40d483b7bba6e4f368` |

  C 已核对十三份回执 SHA；数据库查询和授权结论来自 B。审批账号未获结算 write，`uat_denied` 仍无业务 grant；B 报告已配置授权与矩阵一致。上述仅证明配置提交，不冒岗位菜单和业务权限实测。
- **审批人员工作台前置：** 首轮审批账号结算页 HTTP 403，经 B 独立复现确认为配置前置缺失：该工作台需要 `settlement:read`，该权限允许查看本店患者、费用、账单及收退款信息。主控仅给 A 店 UID 1549 补 read，原 `finance_approval:write` 保留、未授 `settlement:write`；审计 77093。首次通用核验脚本误断言全部 grant 等于新增项而退出失败，原失败保留；B 后续独立核完整授权集合。步骤回执 `.local/s13-e2e-r1/w1/step-20261027T103015-dbd6c73748bc/independent.json` SHA-256 `006c3de9a4183b119611f659671e1fe13a5dc082dc072572ef7fc67ac4a6e27f`。
- B 随后以该审批账号新 Context 正常表单登录、切 A，结算页 GET 200，审计 77094–77096；回执 `.local/s13-e2e-r1/w1/step-20261027T103105-3de35393ee1c/independent.json` SHA-256 `004c3f26a78d50d363c2f392886190278205b024101a1c047544de717360dd4b`。前述 403 与核验脚本失败不能抹除，不计入确认产品 BUG；该页面检查不冒退款或自批负例通过。
- A 报告 11 账号均实际登录并切 A，跨店账号另切 B；店长供给页、管理员价格页、前台患者页、医生／药房治疗页、检查页、仓库页、结算页及跨店两店治疗页取得 HTTP 200，denied 患者页取得服务端 403。B 逐批核审计及资源关闭，独立回执 `step-20261027T102646-c2ad4964da02/independent.json` SHA-256 `f4c8011b1fb34d5f77b75c46e1254866d6a00c9b3c814d892497733e66d24db6`、`step-20261027T102752-e5eecf8005ef/independent.json` SHA-256 `23d33e32090dbe571eac44c33f7149bd985ad0670bf2e442efd336f6c609c660`。C 已核本段四份文件 SHA；页面状态不代表岗位业务流、跨店写或撤权通过。
- 后续授权范围调整：B 独立核检查审核需要 `group_manager`、`medical` 与 `exam` write 及本店目录映射；主控为本计划内初始化仅向 `uat_admin` 的 A 店增加 `exam` write，B 店不增加。B 独立读回 A 店原五类权限保留、B 店原五类不变，UID 5 留审计 76200。回执 `.local/s13-e2e-r1/w1/step-20261027T093954-a374a54c0902/independent.json` SHA-256 `e61e0daf27eeb9e6878eba296168f7cb8dff77a9c513d01ffd1aefe7055a7fbb`，C 已核对文件哈希；实际目录与检查审核仍待通过，不能由授权读回代签。
- A 报告授权阶段操作完成：11 个账号已实际登录，A 店经理已任命；授权操作时页面实际当前店是既有店 1，动作目标则明确指定本次 A/B 店。不能将页面店 1 改记为新店或将配置读回冒作岗位菜单、工位能力已验。
- **保护投影变化：** B 的阶段快照发现四条旧 mutex 行各仅 `revision` 增加 12；与授权前快照相比，授权前该四行无变化，12 笔授权各有独立回执且时间相符。静态源码显示每次 grant 经 `_all_locks` 更新四锁；上述证据支持将变化分类为正常授权锁计数，但逐笔动态因果未直接观察，不能写成全部旧行不变。13 技术表、83 引用／80 文件保持；系统管理员登录导致的 `web.base.url` 变化仍按已知事实单列。
- 阶段保护原件 `.local/s13-e2e-r1/b-w1/protection-uiexplore.json` SHA-256 `34806bf14cc8bb0cdd982367efa5639652c50e5bec7ac037cdf77439b60f43e0`；C 已核对文件 SHA。投影对比、时间和源码判断来自 B。
- **能力页面探索：** 首次点击 New 后表单未显示，原因是测试客户端拦截；不能写为服务端拒绝。原步骤 `.local/s13-e2e-r1/w1/step-20261027T090202-2da78da13606/result.json` SHA-256 `0fed8aa3a512bd55ac55cff97b9c46d588c5398adabf3d68c0420ef2c537ec11`。第二次仅允许原生空 `default_get`／`onchange` 后显示 name／code／active 空表单，未保存；结果 `step-20261027T090604-8b93851b850e/result.json` SHA-256 `d757c65de2c749c12314919fc0dc7d0649363e00ff52c9e557a5c6e720d5ac2e`。B 只读核无新能力且服务停止，证据 `.local/s13-e2e-r1/b-w1/ui-form2-independent.json` SHA-256 `f52b29dcc205f9b03329eec4ccb0413ed1abe8cf88a424e6d1cd4ef7098e0efc`；C 核对三原件哈希，运行和读回结论分别来自 A、B。
- 四项能力的真实 UI 写入工具仍待 B 独立审查，尚未执行写入；空表单不代表能力、区域或工位已配置。
- 后续 A 通过真实 UI 分四笔提交能力，B 新物理只读独立确认 `care` 559、`panorama` 560、`cbct` 561、`pharmacy` 562 均 active，创建人 UID 1541。四事务非原子；检查项目的 `exam_family` 此时尚为 NULL、未验收，不能将创建能力等同检查配置完成。其他五项客户端拦截保留 UNKNOWN；此前 mutex 计数和 `web.base.url` 已知变化继续单列。
- 该能力步骤独立读回 `.local/s13-e2e-r1/w1/step-20261027T091217-3d5780bd3298/independent.json` SHA-256 `dc89edf020f8d59cc844bdf8d687ca84c360b6b9acde218f20c2376c7e79bd0a`，保护快照 `.local/s13-e2e-r1/b-w1/protection-capabilities.json` SHA-256 `a3f0920b70a0882aadb1c9103247e0da33565f02180ad6cf5c76b2b82a4446a5`。C 已核对两原件哈希；UI 操作及物理查询结论分别来自 A、B。前一段未执行写入是历史时点，不反签。
- **楼层探索与首批失败：** UID 1541 的真实 session 3916 切换到 A 店并留下审计，查询当时 A 店楼层为 0。首批运行 Node 退出 2，测试客户端拦截 `store.web_name_search`，没有观察到 Save；不是服务端拒绝。B 独立只读确认两个目标楼层均不存在，楼层创建为 `definitive_no_commit`；另一个 session 3917 切 A 及审计 76035–76038 实际已提交，不能把整个运行写成无持久副作用。
- 独立回执 `.local/s13-e2e-r1/w1/step-20261027T091700-760737c2afd0/independent.json` SHA-256 `26ae8149e1dedf50978e6288e6c04ecbd6f4e92d815322f97f6c0b9eacf61074`，C 已核对文件哈希。B 已审查修正候选：仅允许只读 autocomplete；原失败保留，后续执行和楼层创建尚不能由本记录推定。
- 随后 A 完成两笔楼层创建，B 新物理只读事务独验 A 店 541 的 floor 279、B 店 542 的 floor 280 均为 version 1、创建人 UID 1541。此前三轮 Node 退出 2 的工具拦截保留；每轮均独立核楼层未提交后才续行，不反签为通过。独立回执 `.local/s13-e2e-r1/w1/step-20261027T092403-ca161606faa3/independent.json` SHA-256 `b0c82d7a2f661a9fef33d03863b5184d8d0b8f1a00253fdc1e1ebe9c7d4c006e`，静止保护 `.local/s13-e2e-r1/b-w1/protection-floors.json` SHA-256 `bf4d87c4d6cf54635e05a667c09f9646e285f88c33b4e957332c569637010043`；C 核对原件哈希，查询结论来自 B。
- 保护中原生 supply mutex `revision` 增加 2，与源码及两次楼层创建吻合，但没有逐事务动态跟踪，不能将推断写成直接因果实测。
- **区域创建：** 首轮 Node 退出 2，测试 route 未放行默认 `parent_id`／prefix；B 确认四个目标区域无提交，但切店与审计实际已提交。修正后 B 独立目标读回 A 店 care 1197、exam 1198、pharmacy 1199 和 B 店 care 1200，店、楼层、用途、坐标与创建 UID 正确；floor 279 的 version 从 1 到 4，floor 280 从 1 到 2。独立回执 `.local/s13-e2e-r1/w1/step-20261027T093103-41f6fb621b19/independent.json` SHA-256 `eb68f67973cc1ddc074fe685f125956dbbc104860c1a9a68f29d505a2cfef516`，C 已核对文件哈希。此轮为目标读回，未重采全历史保护；首次失败不判产品拒绝。
- **工位创建：** A 经实际 UI 创建六工位，B 定向独立读回 A 店治疗 1334／1335、全景 1336、CBCT 1337、药房 1338 及 B 店治疗 1339，能力分别为 559／559／560／561／562／559，归属、active 与 callable 正确；A 楼层版本 4→9、B 楼层 2→3。七项测试客户端拦截保留，员工能力与资质仍待配置。独立回执 `.local/s13-e2e-r1/w1/step-20261027T093420-1d2c4e677f73/independent.json` SHA-256 `ee39702de9cbb2577e3538b42cdac5b8efc282979559046a18f837bdf9d57ff9`，C 已核对文件哈希。此轮未重采全历史保护，不以工位创建冒充实际岗位接诊通过。
- **人员能力配置：** B 独立只读确认 doctor UID 1544 关联能力 559，exam UID 1545 关联 560／561，pharmacy UID 1546 关联 562，cross UID 1550 关联 559；合成职称和 UID 1541 的审计已记录。检查人员的实际检查资格尚未授权，能力关联不等于资格或工位接诊验收。独立回执 `.local/s13-e2e-r1/w1/step-20261027T093649-a90f78f46af4/independent.json` SHA-256 `5b79b4d615c528b6d2f3058140f84e65b4d5e22564cbd1941ef6992141094994`。
- 静止全保护 `.local/s13-e2e-r1/b-w1/protection-profiles.json` SHA-256 `911094fccb7ad120a4923bf27bb4dee0aaa35ac83b8897300fe955fa389c94cd`：历史 supply slot／assignment／disposition 保持，技术表与 83 附件引用一致；supply mutex revision 810→824 单列，未逐事务归因。C 已核对两份原件 SHA，数据库查询及保护结论来自 B。
- **服务目录：** A 实际 UI 创建四项，B 的 RO/RR 独立读回 catalog 715–718，分别对应 care／exam／exam／medicine 与能力 559–562，UOM 1；对应独立服务产品及变体 1132–1135，并有原生审计。检查资格码不等于资格已授，目录创建亦不证明价格、费用或库存业务通过。
- 独验回执 `.local/s13-e2e-r1/w1/step-20261027T094318-e6fdd31a18a0/independent.json` SHA-256 `7974d01343991e5ef3327173fc990a55bef4ebd618a900a8cbfde96b2a1c0c6d`；静止保护 `.local/s13-e2e-r1/b-w1/protection-catalogs.json` SHA-256 `7a207682bea5890c56ea1a4918dfc333d10cb883397bc4e6ad1d7a2dda4529cf`。B 报告旧行无删改、技术与 83 引用／80 文件一致，既有 mutex 变化分列；未提交库存或费用。C 已核对两份原件 SHA，操作及独立查询结论分别来自 A、B。
- **门店目录映射：** A 通过真实 UI 创建五项后，B 独立目标读回 mapping 1267–1271，分别为 A 店治疗／全景／CBCT／药房及 B 店治疗；店、目录、报告区、执行区、active、version 1 与创建 UID 1541 符合，存在 accepted 审计和切店记录。区域能力由有效工位计算，预检已确认对应工位，因此无需额外写入区域能力。回执 `.local/s13-e2e-r1/w1/step-20261027T094702-2ac181962912/independent.json` SHA-256 `a08f97f6c9a0f010c51ef6b5b45a1946822a49a3ab32b5564e2dd4ba3fdd3935`，C 已核对文件 SHA。此轮为目标读回，不冒全历史保护。
- **门店价目：** A 通过真实 UI 创建五项，B 独立读回价目 347–351 均 published／version 4，A 店金额 600／80／80／10、B 店 600，原生规则、币种和 UTC 有效期符合。旧价目及旧规则原行、技术表与附件保持；本次价格配置不代表费用已确认或结算已验。独立回执 `.local/s13-e2e-r1/w1/step-20261027T094923-81e9385712e3/independent.json` SHA-256 `f8e05fba83d6f11657427b66affea94a0e594f2e2dc1f63d9e1bc51013dc79eb`，保护快照 `.local/s13-e2e-r1/b-w1/protection-prices.json` SHA-256 `1ff58c695f7c9081188cfb718cb28889caa093563197c2f156942ca8aeb4300b`；C 已核对原件哈希，业务和保护结论来自 B。
- **OBSERVED／待 B 复核：** A 观察到检查资质网页授权入口可能缺失。B 正独立检查，现有证据不足以认定产品缺陷或通过，也不得据此伪造资质。
- **补充：** B 后续使用 UID 1541 独立正常表单登录、切换 A 店并访问 `/ydental/exam` HTTP 200；页面有 family 审核与 template 绑定，未见正常资质授权入口。源码显示有受控服务 handler 而模型 ACL 只读；B 和主控将该发现确认为产品缺陷，登记见下方 E2E-BUG-001。两项测试客户端拦截非服务端拒绝，不能扩大结论。原步骤 `.local/s13-e2e-r1/w1/step-20261027T095216-5a5648fbcb82/` 的 `result.json` SHA-256 `73245d4c122fd12a3724e6054b5f3c40dbd97a4077104ddcebd9b3dec54ac2d4`、`independent.json` SHA-256 `c5aad71b563f390095e78d8d170a7e8dbdf3d004a61a96911cd135e00f5cdaa2`，C 核对文件哈希。前述 OBSERVED／待复核为历史时点。
- **演示策略与开放区：** B 目标独立读回两店 demo 策略 279／280 及开放区 1222–1225 的真实提交与来源事件；该证据不证明容量可售。回执 `.local/s13-e2e-r1/w1/step-20261027T095335-3a8d420caad9/independent.json` SHA-256 `8a787a6e83a92b6b6171dbc80fa9678fdd35403fdbd6e62fbfbe7c3ffa8e3344`，C 已核对文件哈希。
- B 独立核对 `web.base.url` 收尾和保护，证据 `.local/s13-e2e-r1/b-w1/url-restore-independent.json` SHA-256 `432ce52a1f7c6ab80f7fb398f462696159597dc037c8e84538a07482b8461fda`，`.local/s13-e2e-r1/b-w1/protection-finalhold.json` SHA-256 `9eef42711b057fcb807a5e6da57c807c80be42d8d8b4198c5767d7ed10837d04`；C 实际核对两文件哈希。浏览器进程组因缺 PID 未被独立证明退出，不扩写为完整浏览器进程收尾通过。
- 管理员业务授权和 `web.base.url` 的最终恢复及读回尚待完成；不以账号创建代替授权、登录或 W1 准出。
- 私有保护快照 `.local/s13-e2e-r1/b-w1/protection-allaccounts.json` SHA-256 `7e496d3aa2f6c0a2d3fd22556e5191664f47413eedf6cf6a916f7bacd4f232b4` 为写入并发时的 RO/RR 快照；后续停写全保护 `.local/s13-e2e-r1/b-w1/protection-afteradminjoin.json` SHA-256 `0941f2bb86acde100bcbc726f37b1790c79f5fb2b864493b751f9382d7b280b7` 固定于 admin B 店关联后、cross B 店关联前，不能替代 cross B 店关联后的全保护复核。C 已核对两原件哈希。
- B 首次保护采证汇总因 datetime 序列化失败而退出 1；原失败与完整快照 SHA-256 `536af93b81811153479c0dbde61b7818d899ac6ffba59edb9b97f630b707690b` 保留。另以新事务独立核查提交，没有重放；B 报告旧数据、技术和附件保全。该失败不能反签为成功，后续读回与原失败分开。
- B 独立定位与复核仍需保留产品、操作、数据、环境、需求歧义或 UNKNOWN 的依据。未复现不自动认定 A 错误，也不自动记 PASS。必要时主控定向复验并记录裁定。

## 正式产品缺陷与回归

| BUG-ID | 来源与独立验证 | 影响／严重级别 | 原因与修复 | 复验／状态 |
|---|---|---|---|---|
| E2E-BUG-001 | A 观察检查资质授权入口可能缺失；B 独立实际浏览器与源码确认，证据见上 | W1 初始化及 W3 合法检查资格；严重级别待主控评定 | 正常网页授权入口缺失；更深根因尚未证实。D 独立 worktree 源提交 `c4863f8e6bdaccbb5302cb3f3d3bbd73f0099c6d`；活动分支固定候选 `181c8619fe11e97fddc710991a97f84d804fe2a4` | 主控据已测范围判 **FIXED_VERIFIED**；HTTP 自动化测试未运行，撤权及临床执行仍待后续，不代表完整 E2E 通过 |

B 审查确认既有 exam 页面要求 exam／medical 读取权限，未为人员管理员额外扩权；活动分支候选不是 main 合并。操作错误、环境错误和 UNKNOWN 分别计数，原始证据不删除。产品问题计数目前 1 个 FIXED_VERIFIED（限定已测范围）；修复提交或静态检查不能替代实际复验。

- 候选限定加载 `-u ydental_exam`：首次系统 Python 缺 `psycopg2` 退出 1，未连接数据库或进行预检；随后项目 venv 唯一实际升级退出 0。B 独立回执 `.local/s13-e2e-r1/w1/exam-upgrade-once/independent.json` SHA-256 `51cbb5c309a1051bde3cb18dca120c9679eeadaadeea8d0d40b94def01a9400d`，C 已核对原件哈希；失败与成功不得合并反签。
- 实际差异分层：目标 exam 模板 1596 的 `arch_db` 改变；存在级联依赖；settlement 1602 的 `arch_prev` 变化但 `arch_db` 不变；25 行 `ir_access` 和 1 行 `res_groups` 仅 `write_date` 变化。旧 NULL 导致 source fee 约束未添加的警告保留，前后约束相同。仍须正负浏览器及结算影响回归，E2E-BUG-001 保持 OPEN。
- **panorama 资格首次真实提交：** 最终候选的表单请求 HTTP 200 后出现 `PlaywrightError`，前端结果为 UNKNOWN、错误首因未知；B 随后用新物理 RO/RR 独立读回唯一资格 ID 1（A 店 541、人员 UID 1545、限定合成码、UTC 日期、授权者 UID 1541）及 accepted 审计 76861，已提交，禁止盲目重放。回执 `.local/s13-e2e-r1/w1/step-20261027T100510-4a82f420eeb3/independent.json` SHA-256 `334b096948c47de5f4c54b49a2d27ba8fa0c7d67d17893ad56fc566f16a628a2`，C 已核对原件哈希。真实已提交不等于浏览器修复通过；CBCT 资格仍待定位。
- **CBCT 资格：** 后续真实表单返回 HTTP 200 且页面 reload，B 新物理读回唯一资格 ID 2、A 店 541、人员 UID 1545、限定合成码及日期、授权者 UID 1541，accepted 审计 76865。回执 `.local/s13-e2e-r1/w1/step-20261027T100608-53429601ea05/independent.json` SHA-256 `b3ece42284e78f1f287f486bc48744845804d5f74b99f1ffd0199dc326570dce`，C 已核对文件哈希。实际检查使用待 W3；该结果不抹除 panorama 的 `PlaywrightError` 与前端 UNKNOWN。
- **检查 family 与模板：** A 经真实 UI 四次提交，B 新物理只读核能力 560 审核为 panorama、561 审核为 CBCT，demo active 模板 37 绑定目录 716、模板 38 绑定目录 717，来源 UID 1541、accepted 审计 76869–76872。回执 `.local/s13-e2e-r1/w1/step-20261027T100644-cb3eb358e38d/independent.json` SHA-256 `315e86e14edd8f6ac8cb666471cfac4e231f28543740c3a5f42bc4591522f3b4`，C 已核文件哈希。模板无耗材，本次为配置提交，不冒实际检查已做。
- **BUG-001 负向及影响面回归：** UID 1545 无 personnel 时资质表单不可见，已认证 HTTP 请求取得 403；UID 1541 自授表单不列本人，已认证 HTTP 请求取得 403。B 分别确认无负向资格或 receipt，但未观察到独立 denial 审计。页面观察与 HTTP 拒绝分层，不将直接 HTTP 请求写为正常 UI 负例。相应独立回执 `.local/s13-e2e-r1/w1/step-20261027T101108-7c0048687d71/independent.json` SHA-256 `859dce64246c1b430ca9cf55e995358d29ccd86a748281a210b07ce0edd3fad5` 与 `step-20261027T101228-7959d1a6a80f/independent.json` SHA-256 `8bb6f0685b5916b441f19b69d8f9b783216b2557a943b7f4cb699e9100a74517`。
- 结算 UID 1548 正常进入 A 店后 GET 200、main／search 表单各 1，没有业务 POST；B 核审计 76910–76912 和进程停止。回执 `.local/s13-e2e-r1/w1/step-20261027T101330-c65ac2fb13da/independent.json` SHA-256 `5bcfe10bb821100fd0977f9037f93c90687567cc3644fe504e6c27fcf4c6c3a0`。C 已核以上三份回执 SHA；该检查不证明旧约束成立或 W5 通过，BUG-001 仍 OPEN，旧 scope、跨店及独立验收待完成。
- **后续 BUG-001 限定独立验收：** B 使用新浏览器在固定候选 `181c8619fe11e97fddc710991a97f84d804fe2a4` 以 UID 1541 进入 A 店，HTTP 200 看到资格表单、人员 1545 可选而本人不可选；审计 76917–76920。回执 `.local/s13-e2e-r1/w1/step-20261027T101541-ff28f92a6ab7/independent.json` SHA-256 `77621c2e47e73424a372686ea0567f51a293cb27e8928d05948f9eec59739df4`。
- A 的真实 CBCT 表单提交与 B 读回、自授／无权 HTTP 403、真实旧 A 页切 B 后 HTTP 409 且无目标副作用、结算只读 GET 200、family／template 回归分别成立；旧页 409 独立回执 `.local/s13-e2e-r1/w1/step-20261027T101449-1615fdf575f7/independent.json` SHA-256 `62597107cadc2963f00455bb55a8274ffdf37d4fbd25493747a253b5e51cac72`。C 已核对两份新增回执 SHA 和当前 HEAD；前段 OPEN 是历史时点。panorama 原 `PlaywrightError`／UNKNOWN 不抹除，撤权、临床执行及 HTTP 自动化测试仍未运行，不能冒完整 E2E PASS。
- **排班与供给部分提交：** 浏览器运行报错，首因 UNKNOWN；B 物理独验 A 店前四个安排和 slot 1229–1232 已 published，药房 slot 1233 为 draft、未发布，B 店安排及 slot 不存在；事件 5116–5128 来源 actor UID 1541。回执 `.local/s13-e2e-r1/w1/step-20261027T100818-ee8a56389dee/independent.json` SHA-256 `cda01d8461d2611fcab723a717f4e9d11a687783b926ca22a27fb02fc73f1da9`，C 已核对文件哈希。已提交部分禁止重跑；后续仅安全接续该 draft 和 B 店唯一新目标，demo 实际可售尚未验收。
- **后续排班安全接续：** B 独立只读确认已有 A 药房 draft 1233 已发布，唯一创建的 B 店安排 5 及 slot 1234 已发布，事件 5129–5132；没有将先前已提交的安排重跑。回执 `.local/s13-e2e-r1/w1/step-20261027T100941-e024d41aeb3b/independent.json` SHA-256 `6f9554b620e7ceff9b708c358f6aeae1d530bf09bb4e971adbc852ed645390c9`，C 已核文件 SHA；published 不证明 demo 可售。
- **药房 slot 原浏览器 Error 复核：** B 实际只读页面发现原筛选器同时匹配同名区域汇总行及工位行；主控新 Context 独立定向复验 `step-20261027T101153-c81c1dfbd123` 确认两行以及工位 slot 1233，B 核本次停止及审计 76904–76906。两次页面均有两项客户端拦截；因原错误正文缺失，主控裁定原发现仍为 UNKNOWN，不强行分类误操作或反签 PASS。独立回执 `.local/s13-e2e-r1/w1/step-20261027T101153-c81c1dfbd123/independent.json` SHA-256 `78b56c02681024fb12f2fc531bbf32f2d6f114abc996868b131a7c030d713a86`，C 已核对文件 SHA。
- **A 店库存初始化：** 仓库员 UID 1547 经真实 UI 操作后，B 独立核 warehouse 100／`E2A01`、config 99、7 类位置及原生新增 13 个 location／8 个 picking type，审计 76925；本步骤尚未入库。独立回执 `.local/s13-e2e-r1/w1/step-20261027T101741-a64b55f07f07/independent.json` SHA-256 `c7d5220ef9481eff00ef73d314ccbf3e4ecf932e3e2045a6856c793f37378899`。
- B 前后逐行保护核查：旧价目、组值、技术和 83 附件引用一致；partner 1 的 `write_uid`／`write_date` 与 inventory mutex 发生变化，必须保留，不能声称全部旧行不变。私有快照 `.local/s13-e2e-r1/b-w1/protection-preinventory.json` SHA-256 `6d37062a3f51d1f305fcc2f60326206dc3bff58074a4692f0abb9d5c62408c4d`、`protection-postinventory.json` SHA-256 `1089a839445a91d7359c3eeee93d0e29f218a97f243502842a6903c3c1ffebba`；C 已核对回执和两快照 SHA，业务与保护判断来自 B。
- **合成药品与初始库存：** medicine product／template 1136，代码 `E2ER1-MED-01`，单位和步长 1；A 店 lot／batch 278 到期 2027-12-31。仓库员 UID 1547 经真实 UI 对唯一来源 `E2ER1-20261027-A-MED-RECEIVE-01` 入库 10 单位；B 独立读回 event 754、move 754、line 1201，供应商位置 1297→药房 1293、quant 707 为 -10／708 为 +10、审计 76943／76944。该接收已提交，禁止重放；W4 的分次发药 4＋2 未执行。
- 该 move 价值为 0、`price_unit` 为 NULL、无 `account_move`；event 的 `synthetic=False`，不得伪称 true。本次合成范围来自隔离环境与命名。独立回执 `.local/s13-e2e-r1/w1/step-20261027T102126-168ee1be2d6c/independent.json` SHA-256 `4139d0ccc3592eb82422ecf813c2836434fa219ca86615d69d28a18f6477b32d`；前后私有保护快照 `.local/s13-e2e-r1/b-w1/protection-prereceive.json` SHA-256 `16d930213503eeba48dec44e0c13903dd17e56fadda7c5d46b7c345fa09c3b74` 与 `protection-postreceive.json` SHA-256 `2022a677f570896a0a5f08d4a7dc640751e4246601e8d5a10605d2982094dc08`。C 已核对三份哈希，独立业务与保护结论来自 B。
- **药品费源与耗材主数据：** B 独立读回 A 店演示收费 link 2，将 SKU 1136 关联 catalog 718 和价目 350，单位 1、`demo_confirmation`，UID 1541 审计 76949；这是费源配置，不是实际费用。回执 `.local/s13-e2e-r1/w1/step-20261027T102248-2cabdffaa06c/independent.json` SHA-256 `696f444ddb68a32ae18bc547272ceb5eb67c9e9dbdf4b2ed1f5dcdf202611241`。
- A 经真实 UI 建立耗材 product 1137／`E2ER1-MAT-01` 与 A 店 lot／batch 279（到期 2027-12-31），B 核 UID 1547 审计 76960；尚无耗材入库、move line 或 quant。回执 `.local/s13-e2e-r1/w1/step-20261027T102417-866d5dd4baac/independent.json` SHA-256 `da68b347f5e2274566e3fc61c0fe22250d815e6bf35c3b8384d4e52e5b464413`。C 已核两份回执 SHA，不能把主数据创建冒作耗材库存或耗用通过。
- **合成患者：** 前台真实创建患者 1644／`P00001644`，A 店关系 1673，无真实出生或联系资料，尚未报到。独立回执 `.local/s13-e2e-r1/w1/step-20261027T102526-cefef2d2f24c/independent.json` SHA-256 `8cec8922efc80a59ca70f2ded121f75c43b1dcc843a896dae3ddf19d8e68f0b9`，C 已核文件 SHA；W2 仍须全新团队实际执行后续流程。

## W1 最终交接

主控依据 A 阶段事实和 B 独立终验裁定 **W1 PARTIAL**，未通过全部准出；后续不依赖未完成条件的验收可以安全接续。A 摘要 `.local/s13-e2e-r1/w1/a-w1-summary.md` SHA-256 `547ba2f7dea514edbc127e404b3d222cc3199a9c17d8c1a922ad24c88ae87857`；B 终验 `.local/s13-e2e-r1/b-w1/w1-independent-final.json` SHA-256 `e6eff901788bc0abc0e7f632a4d3621a46457592633727342cafdbfbb8d64214`；B 逐行保护 `.local/s13-e2e-r1/b-w1/protection-w1final.json` SHA-256 `4af16b99182d5052c5bfb87224df80219d04d67760b4b1d6615d985d729a3884`。C 已核对三份文件 SHA；执行事实、独立查询及阶段裁定分别来自 A、B 和主控。

| 账号／UID | 独立登录及已读回权限摘要 |
|---|---|
| `uat_admin`／1541 | 实际表单登录；A 店 personnel、space、capacity、price、medical、exam write，B 店前五类 write；管理员组已核 |
| `uat_manager_a`／1542 | 实际表单登录；A 店 personnel、space、capacity、price write，已任命店长 |
| `uat_frontdesk_a`／1543 | 实际表单登录；A 店 frontdesk write |
| `uat_doctor_a`／1544 | 实际表单登录；A 店 medical write，能力 559 |
| `uat_exam_a`／1545 | 实际表单登录；A 店 exam write，能力 560／561，两个检查资格已独立读回 |
| `uat_pharmacy_a`／1546 | 实际表单登录；A 店 pharmacy write，能力 562 |
| `uat_stock_a`／1547 | 实际表单登录；A 店 warehouse write |
| `uat_cashier_a`／1548 | 实际表单登录；A 店 settlement write |
| `uat_approver_a`／1549 | 实际表单登录；A 店 finance_approval write、settlement read，无 settlement write |
| `uat_cross_store`／1550 | 实际表单登录；A 店 medical write、B 店 medical read，能力 559 |
| `uat_denied`／1551 | 实际表单登录；无业务 grant，患者页取得服务端 403 |

各账号初始登录时当前店未选；后续 A 报告 11 人均实际切 A，跨店另切 B，页面状态、审计和其限制详见前文。菜单 GET 不代岗位业务、跨店写、撤权、自批或临床执行通过。

- 固定对象：A／B 店 541／542、楼层 279／280、区域 1197–1200、工位 1334–1339、能力 559–562、目录 715–718、价目 347–351、已发布 slot 1229–1234、资格 1／2 和检查模板 37／38。实际可售容量仍 UNKNOWN。
- 药品 1136／批次 278 的 10 单位真实接收 event／move 754 已提交，来源唯一，**禁止重放**；耗材 1137／批次 279 仅主数据，无库存。不能将 W4 发药、耗材耗用或 W5 结算写成通过。
- E2E-BUG-001 为候选 `181c8619fe11e97fddc710991a97f84d804fe2a4` 上已测范围 FIXED_VERIFIED，panorama 的原始前端 Error／UNKNOWN、排班原浏览器 Error／UNKNOWN、客户端拦截、旧 NULL 约束警告及 HTTP 自动化、撤权和临床执行未验均保留。
- B 最终独核目标库 OID／cluster、11 个 active 账号、11 员工及 13 个 active 会员和授权矩阵；lot 278 在药房 +10／供应商 -10，lot 279 无 quant；`web.base.url` 恢复 18411、无 freeze，18511 停止且无其他目标连接。83 附件引用与 P13 相同；旧投影无删行，但存在 ACL／组时间戳、partner 1 元数据、五个 mutex revision 和升级造成的 7 个技术表差异（含 exam `arch_db`、settlement `arch_prev`），既有 NULL 约束警告保留。不得写作全库零差异。
- 11 个账号为已授权的跨阶段连续测试暂保持 active；计划最终结束时须按用户要求停用登录并保护身份、审计。账号关闭尚未执行。
- W2 只能在主控裁定前置满足后由**全新** A／B／C 团队接续固定对象、合法账号和证据；每个账号重新建立独立浏览器 Context，不继承 W1 Session。已提交动作的状态未知时先独立读回，不盲目重试。
