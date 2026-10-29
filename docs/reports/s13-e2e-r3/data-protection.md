# R3 数据保护与责任

W0 对历史合成目标 `ydental_s11_synth_20261023_01`（OID `2171423`，cluster `7694897083368259627`）新采 RO/RR 基线：158 表、94214 行非敏感字段和539文件与 R2 终态对应采集范围一致，SHA-256 `898ecb25717caf121e6a0ec510abec051310d7bc2b28f947c86d9f9de308286d`。该事实不证明敏感字段、未纳入表或缺失旧前像；UNKNOWN 保持 UNKNOWN。

旧 19 账号 inactive，旧10个时段 suspended，处置45–55、57 pending；旧文书515–519只读，负责人 inactive。W0 核 task908／913／916 pending；旧原件、已提交金额、治疗、处方、库存和审计不允许重放或覆盖。BUG-002 历史目标模块升级 NOT_RUN，未手工重置互斥 revision。

本轮新患者1652、task917、event367及唯一 fee362=600 为真实已提交合成业务，禁止重复执行；原 execution559 interrupted、续接560 verify；doc520 pending/v2，作者1563、负责人1564、editor null，版本985由1563创建、986由1564作合成补记。新 D1 正常离职后新 slot1240 suspended、disposition59 pending，原生 tracking、审计及通知保留，不清除或自动完成。

W2 在转派、补记及无权负例后独立比较所采158表及589文件，临床来源、执行、费用、库存、任务等原有记录在所记录范围未发生非法变化；另有新用户登录的讨论成员及原生消息、审计和技术 mutex revision 变化，不能描述为全库零变化。转派请求原响应正文 UNKNOWN，但独立读回和 accepted 审计确认已提交，不得重试。详细前后影响及 SHA 见 [W2](phase-W2.md)。

W4 已独立确认新 UID1561–1563 正常停用及其原生 tracking 与待办联动；UID1564 仍承担待完善文书责任，UID1565 为唯一有效店长，均 active，后续处置待用户决定，见 [W4](phase-W4.md)。历史旧 Session 是否失效、最初 hold Context 是否正常关闭、266 个不可见序列和未经采集数据仍 UNKNOWN；不可用事后哈希补成旧前像。
