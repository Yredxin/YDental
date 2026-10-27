# W7 A 独立证据检查（进行中）

2026-10-27 UTC，W7 全新 A 线程检查活动分支、阶段材料和部分私有原始回执；未启动浏览器、未连接数据库、未提交业务，未执行账号收尾。本记录是证据检查，不代替独立实际业务重放或最终保护验证。

现场 `codex/s13-e2e-r1` HEAD 为 `dca4e1d2821b20df7b4b940d28d461270c310225`，tree 为 `4c09b0c5207f5a5c342ad3ccb63f2a51db2e5bad`。工作树含 `CURRENT_TASK.md` 修改及本报告目录未跟踪文件。`4e3ad4722c10aba1420984c628a3345b111bba3b..dca4e1d` 代码差异为 lab action XML 与 settlement 合成配置、绑定及测试，涉及 11 文件；这是源码差异检查，不代表 W3/W4 网页业务已经在最终候选重测。

## 对原始回执的抽样摘要核对

以下 SHA-256 由本线程重新计算，均与对应阶段记录所列值一致；本次仅核文件身份，不单凭摘要验证业务状态。

| 私有原件（均在 `.local/s13-e2e-r1/`） | SHA-256 |
|---|---|
| `w3-exam-once/result.json` | `4615a1148f31c6619cf98b3703d072ad8b86eb745c1f7134213dc37021db5466` |
| `w4-pharmacy2-once/result.json` | `6f60f1e1df17418447ac3821850d267663c5188d3034884085b7b5f67abb5fa2` |
| `w4-negative-pharmacy-once/result.json` | `dbd860c02f8b3ef0cdbfa742be9b007636265c89e978190415031d0203ebc64e` |
| `w5-settlement-upgrade-once/result.json` | `139a7fee17e1d3b06d0245e8a112695a079079b689e308f35dce4ad441e47392` |
| `w5-synthetic-actions-bind-once/result.json` | `4af6297aa8eeb1308a3f56284ad8f6ba79dd44c9bd6b46d7a533df2b71938ca7` |
| `w5-bill-740-once/result.json` | `8c1db9ff2ddf29ce064046e1488914f20d4325dec28e1b2abef3d35828d26e75` |
| `w5-multibill-270-once/result.json` | `4c18fd807d451b7605bee8dca0c63a6e86f8beba9662608e0419a5cacb5f5a04` |
| `w5-multibill-200-once/result.json` | `21df64ed3149404e0b792265f6adc0bda5a3cffc1076c54521f8773452017989` |
| `b-w6-final/double-post-exit.json` | `42d5ed02b11f8420d758f04978d3d513114a3d8cae6b98a064739840431ddc8a` |
| `b-w6-final/qualification-final.json` | `3df99dc7356baf7de7b0f6bef608619899b2e49e3017fdccefcf952170520438` |
| `w6-final-unqualified-call-once/result.json` | `b142742f5edaf4d6d13715719d4e263b1a32ebb8ce3e5873b5c4260f2906e73a` |

## 当前证据范围与缺口

- W0 为基于用户内网确认的限定准出；网络公网可达性未独立证明，原权限拒绝及客户端拦截保留。W1–W6 阶段记录的阶段性结论为 PARTIAL 或限定结果，必须以各报告的后续增量为准，不能照抄其初始化矩阵里的旧 `IN_PROGRESS`／`NOT_RUN`。
- W3 的患者耗材实际消耗、不同医生承担草稿和完成责任仍未证明；W4 无权发药服务端拒绝、同源重复请求未验。W6 无资质叫号真实返回通用 `no_eligible_waiting`，资格筛选原因属于结合现场和源码的推断，B 未独立浏览器重复提交。
- W5 的旧历史原件实际重印、PDF 视觉与物理出纸未验；升级前 16 项旧 URL／menu／view 缺紧邻完整前像，26 项复杂字段未直接比较，历史技术保护为 UNKNOWN。W5 多笔真实账务、W4 两笔发药及其他已提交业务不得重放。
- W6 后续补验已取得过号返回等待、单候选故障撤呼、停接人工追加及未使用现场资格取消返额的限定证据；多人位移、cron 自动清理时延和其他返额来源仍未验。跨店直接写服务端权限拒绝、复诊联系及厂商／人工外加工仍未完成；退款本人审批的确切拒因 UNKNOWN。现有断网仅为患者表单浏览器离线模拟，不冒物理网络故障。
- 各阶段的浏览器、MODEL、HTTP、源代码、独立物理读回和独立浏览器证据分别记录；W3／W4 较早候选证据与最终候选证据不能拼成最终候选全通过。P12 的历史 JS-off FAIL 不重判。

## 演示材料建议

该计划结束时 11 个测试账号须停用，服务也须停止；因此下列路径仅为既有合成资料的只读演示索引，后续真实演示需要另行授权的演示窗口、安全启用或轮换账号、重新启动隔离服务、确认当地业务日与门店。不是现有在线入口承诺。已完成收款、退款、发药、检查和出账不得点击重做。

1. 前台用 A 店合成患者 `1647`／`P00001647` 在 `/ydental/intake` 查阅患者和到店；该任务及历史关系按实际状态展示。
2. 医生在 `/ydental/clinical?document_id=509` 查看草稿来源与未完成责任，不能将 pending 当作已签署；检查员在 `/ydental/exam/result/49` 查看全景结果，CBCT task `888` 仍待完成。
3. 药房查看处方 `31` 的 6 单位、已发 4＋2；原批次 `278` 药房剩 4，另有 1 单位退回隔离待核，禁止重复发药或放行。
4. 收银在 `/ydental/settlement?patient_id=1647` 查看 invoice `169` 原出账 740 USD、500＋240 合成收款、refund `12` 的 100；invoice `174`／`175` 原额 270／200、payment `33` 分摊 270／30，`175` 剩 170。显示权限以重新启用后的实际配置为准，禁止再次提交付款或退款。
5. `/ydental/reports` 查阅实际日期和明细来源。病历／处方／检查 PDF 原件 `310`–`312`、账单原件 `1` 可按权限查看；仅本轮原件的响应字节比对已验，旧店历史重印不以此代替。
6. 待办演示只读核对检查 `899`／队列 `558`、过号后等待 `901`／队列 `559`、B 店追加任务 `903`／队列 `560` 和 permit `1`；医生文书 `514`、CBCT `888`、续诊 `900` 等责任不应被标为完成。复诊 `283` 为 to_notify，内部 activity `215` 未完成；没有实际联系或发送通知。具体可见内容与重新启用后的授权和业务日期有关。

以上步骤中的账号实际 UID、员工和角色见 [W1 记录](w1-record.md)；账号停用与全部权限终态应以 W7 独立最终读回为准。

## W6 后续结果的独立摘要复核

本线程再次读取更新后的 [W6 记录](w6-final-record.md) 与活动状态，并重新计算以下八份原始文件 SHA-256，均与该记录及交接状态一致。此为独立文件摘要核查，不冒数据库重新读取、浏览器操作或独立重放。

| 私有原件（均在 `.local/s13-e2e-r1/`） | SHA-256 |
|---|---|
| `b-w6-final/queue-extra-missed-post-exit.json` | `b3045f73008867010ab9c004bd7731c8d076f19e4c5523cdbe26cdf7887548b8` |
| `b-w6-final/queue-extra-post-cancel2.json` | `c8c2b8af649129828671a1488252c18dd6ac306c9337d940068d0e19e5cd2d35` |
| `b-w6-final/queue-extra-fault-final.json` | `0e522ab13f2a34ba37e4cc60349d9762726d97510cd792e0479b008123a5798b` |
| `b-w6-final/append-final.json` | `3c77c11fb5939b7050f6d91ef834923fa8f217fb6bd7c045df6375b91be80e8d` |
| `b-w6-final/followup-final.json` | `670a61982b4d44d56f5b6da555f1a00de949cba6b2215ae41f9528a3e2198052` |
| `b-w6-final/lab-vendor-final.json` | `beada5d3d09cc15dc05215e7b5fd3a83a4ffe3efd33a2206d92be02ac828b4db` |
| `w6-final-queue-missed-once/result.json` | `2daa1e532f7ee68bf873e63374133db4ac356207649c93699bef71561dd56f1e` |
| `w6-final-followup-create-once/result.json` | `8e41a99c6679f2070e9f3afb55ee1cf4e7a30cd816be1e5c6969014f6a520d33` |

场景边界：`559` 过号后 waiting／missed 1，仅一候选，未证明后移两人；正常新进入触发自然超时清理，未证明 cron 时延；未使用资格 `576` 取消返现场额 1，仅证明该来源及状态；B 店追加 permit `1` 已实际提交、队列 `560` 等待，权限和营业恢复但新增策略 `282` 等测试数据保留。复诊 `283` 尚未联系；合成 partner `3376` 已创建而 vendor 草稿未保存，外加工和潜在通知通道未执行，不构成产品拒绝或加工 PASS。

## W7 收尾及 A 限定结论

首次启动账号停用工具使用系统 Python 时，在导入 `psycopg2` 处失败，未进入数据库或创建一次性运行目录；B 独立读回11账号仍 active、URL 未变及无目标连接。随后按项目虚拟环境启动已审工具：UID 2、非 sudo、正常 Odoo ORM 尝试归档11账号，但事务内保护断言检查到受保护对象变化，Odoo exit 1，未到提交标记；B 独立读回账号和 URL 均为前态，证据 SHA-256 `dede02b42bc348c9a4fedc637ceea2b5dadec7f9617bf3750b2e567815eee1fb`。这些失败均保留，不称账号已停用。

为定位影响，经过主控安排及独立工具审查，两次仅诊断、明确 rollback 的事务均正常返回 `ROLLBACK_RETURNED`。第二次事务内读回 10 条测试供给 slot `1229`–`1238` 的状态、原因、版本和写入元数据发生变化；12 个 discuss channel member 被移除，11 个测试用户 partner 写入元数据变化并新增11条审计。上述是诊断事务内观察而非已提交事实；是否全部回滚以 B 终验为准。源码表明 `res.users` 的 `active` 写会触发供给联动，因此不能为停用账号损坏现有预约及未完成责任；事务回滚不保证 PostgreSQL sequence 数值不变。一次 `scope` denied 调用链发生在用户搜索时的 partner 访问域检查；未绕过该拒绝。

按主控结论，密码轮换会触发安全通知，本计划禁止外部通知，未执行密码轮换或关闭通知。11 账号在最近独立只读检查时仍 active，**停用登录目标尚未完成**；不得将其称为已停用或演示窗口已准备好。

单独的 URL 恢复工具经 B 审查后由 A 使用 UID 2 非 sudo 正常 ORM 单次执行：返回 Odoo exit 0，事件 `PRECHECK_OK`、`COMMIT_STARTED`、`COMMIT_RETURNED`，私有运行配置已删除；日志 SHA-256 `a8df89854a440161f1a0284962b2354745584f77345a4087a47243293d5e9aff`。工具事务内核其他配置参数摘要及 freeze 不变。B 最终独立读回 URL 已为 18411、freeze 未设、11 账号均 active，目标连接和 prepared transaction 均 0、18511 无监听；回执 SHA-256 `8bdb72b2ff0c1c06d77f8b0e67cf1b1af0c21a6c7c98377448a9f502e5d13585`，细节见 [W7 B 独立复核](w7-independent-review.md)。

本 A 检查固定候选和阶段材料、抽核回执摘要及只读演示索引；没有在 W7 复演历史经济／库存业务。由于必测场景缺口、最终候选不同阶段的证据限制、历史技术前像 UNKNOWN 及账号停用未完成，本次不能签全通过。独立业务终验、W7 保护结果和整体裁定须由 B、C 与主控按各自证据完成。
