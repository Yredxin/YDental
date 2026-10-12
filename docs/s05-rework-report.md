# S05修正交付报告｜YD-N1 R1

来源：用户本次明确执行#29 [GPT-REVIEW6115823569](https://github.com/Yredxin/YDental/issues/29#issuecomment-6115823569)，只修三个BLOCKER。已完整读取该最新评论，继续当前S05会话/分支；原#23/#29授权和S04前置不重做，没有从撤销旧计划、旧四份文档或上一聊天补需求。Codex自测交付申请不是GPT技术PASS、用户验收或生产发布。

## 固定链和状态

- 原最终：`76335d9902cee8e8c24173f0b01fd9ba8b606a5c`，全部原报告、失败/补交证据保持原样。
- 修正product：`754cc331386e8294225c6579c9b4daa555160f92`。
- 最终test：`68cbcdc3c5a7c0e16a8389e89a6ba44e9086bfc2`；product→test仅新增/加强测试及验证脚本，产品tree不变。
- final：本报告和证据所属文档提交，完整SHA固定在#29修正交付评论；test→final仅AGENTS/文档/脱敏证据。
- 分支`codex/s05-intake-r1-20261011`、origin Yredxin/YDental，开工HEAD76335d9、无未提交内容；不重建分支、不强推。
- 用户授权的Project执行状态已在产品实施前从待启用改为返工；完整读回仅该字段变化，原生Status仍Todo、其他条目/字段/视图/workflow/Issue状态不变。#29保持OPEN，交付不自动转待复核。见[evidence/s05-rework/project-state.json](evidence/s05-rework/project-state.json)。

## 三项修正与验收断言

|BLOCKER|产品修正|实际验证|
|---|---|---|
|B1集团目录|集团内部session+live身份写catalog，不依赖本店price等级；读取例外只给catalog/native product；门店mapping/price/review/publish/snapshot保持price-write|group price-none建/改/停目录及native同步、跨店可见且价目600不改；非group price writer可维护价目/映射但拒目录；前台/医生/只读拒目录；撤group下一HTTP拒；仅目录group的mapping RPC读也拒|
|B2预约营业日|独立资格按S03店时区比较slot日与当前日；不新增早到分钟限制、不查可售余额、不重新acquire|reservation/phone同UTC日但Honolulu前一当地日拒绝，预约当地日九小时早到且可售0成功用原claim；timed referral目标明日报到今天拒/次日早到通过；HTTP同日数小时早到通过，未来拒无position/合成queue和容量变化|
|B3可信转诊|普通HTTP/_operate拒绝；固定private hook默认关闭；test-only冻结typed permit；取消目标company_ids门槛；真实来源分类与actor/源目标引用审计|same-company及第二legal company的timed/untimed可信源成功；来源doctor只有A公司/A店，不加入目标company/membership；timed目标预约、untimed受理时现场；普通目标reserve/cancel/task/mapping/price/切店拒；目标停用/映射停用/停接/末额无半建，untimed现场满受理不半建；medical/exam审计分支|

没有新增字段；原字段字典继续适用，权限/动作以[s05-rework-contracts.md](s05-rework-contracts.md)定向替代。安全自复核见[s05-rework-security-review.md](s05-rework-security-review.md)。原S03容量账本、锁序、S04真实merge、价格快照、position切换和13组竞争设计保留。原S05-T01—T13全部随原25项业务回归；新增4模型+4 HTTP/RPC，共21模型+12 HTTP=33项业务。

## 最终隔离环境与验证

核心固定`f0c5a9b42f544e7f18dc6c8e1c93b957837e0bcb`，本地20.0 fork；核心`.venv/bin/python`，不冒称核对同SHA官方上游。最终全新库`ydental_s05_test_20261012014755_f53e6686`，127.0.0.1:5432/odoo、cluster7694897083368259627，独立配置/data_dir/日志、OID创建记录、精确dbfilter、HTTP18115、0cron、SMTP禁用、进程外发限制。没有接管旧库、改既有服务/核心/odoo-12/系统依赖、安全控制或生产参数。

|验证|已执行命令/证据|结果|
|---|---|---|
|install|`../.venv/bin/python scripts/s05.py install --db DB --port 18115`|PASS：0 fail / 0 error / 35，exit0|
|upgrade|同runner upgrade|PASS：0 fail / 0 error / 33，exit0|
|真实数据库并发|同runner probe；原13组双连接保留，只改T11可信源调用/前提|PASS：13/13双连接，deadlocks=0，守恒/单位置/canonical通过，exit0|
|Firefox|同runner guarded serve +已有进程本地Playwright/Firefox/GTK执行scripts/s05_browser.py|PASS：Firefox155.0，35/35、0 pageerror、11张截图，exit0|
|隔离负向|`../.venv/bin/python scripts/test_s05_guard.py`|PASS：5/5，exit0|
|翻译|同runner export原生POT与zh_CN比对|PASS：268/268、missing0，exit0|
|静态|compileall、git diff --check及完整odoo-security模式扫查|PASS：exit0|

安装数含2项Odoo原生加载检查；不把合成queue或server source当S06/S08真实联调。跨法人和预约日是独立真实事务/HTTP测试，不冒称新增真实临床场景。13组探针继续含异区报到、stop两交错、cancel/consume两交错、重复取消、改期末额、转诊末额、merge/预约和登记两交错、调价/恢复；有限RR序列化重试、deadlock直接失败。

## 保留失败链

1. 返工首库20261012013438_94a0919d，test7971ece：install255、tests=null。新增PO词条缺Odoo模块/来源metadata导致翻译导入失败；补metadata后新库重跑。
2. 第二库20261012013618_f785d7ad，test6babbbb：install1，1 fail/1 error/34。新增模型夹具漏模拟2032当地日开区、目标营业状态变更漏version；HTTP新场景已通过。只补测试前提，不放松产品约束。
3. 后续新库20261012013829_0c92732c：install0/0/34通过；再收窄catalog读取例外到专用来源，新增仅目录group RPC负向。
4. 新库20261012014035_3871be5a：install0/0/35通过；最后加强测试使UTC日相同/当地日不同、Firefox实际表单显示拒绝，并保持源doctor仅A membership，最终全量运行见上表。

5. 新库20261012014258_d02a1bc7的首次返工Firefox在29个已通过检查后失败：医生只读intake页没有写表单令牌，测试helper取空。目录price-none、未来报到拒绝实际表单与同日早到均已通过；只修改脚本从正常门店会话页取令牌，再重跑最终新库全量验证。

原76335d9及其之前失败链完整保留在docs/evidence/s05，不覆盖；本次新增证据位于docs/evidence/s05-rework，原始日志/配置/凭据只留私有run，GitHub只放合成摘要/哈希/截图。

## 用户效果复看与边界

1. 集团目录专用账号在price=none时进入目录页，可以建/改/停服务及同步原生产品；看不到本店维护/快照按钮，伪造请求仍拒。
2. 同一门店当地日的已有预约，虽提前数小时且可售0仍报到成功；明日预约今天有真实到店也拒绝进入受理位置，待预约营业日再报。
3. 普通医生HTTP不能直接发起两种转诊。真实S08入口未连接，当前只由guarded test server permit模拟已完成来源，验证跨法人目标受理；不给来源医生增加目标company/membership。

本次自建预览在验证后已核对PID/config并退出；复看可用`scripts/s05.py serve --db DB --port 18115`，访问/ydental/intake和/ydental/intake/prices。运行预览仅允许记录的S05新库；合成访问材料只在私有.local/DB/access.json，不在GitHub。最终20261012T015215824296的35项PASS及11张截图已固定；人工另查看目录price-none、未来报到表单拒绝、医生无发起入口三张截图，结果与断言一致。截图为虚拟资料，Firefox使用默认sandbox，保留原失败材料，不关闭安全设置。

正式价格锁价/承诺价仍待业务发布，demo_confirmation及容量demo参数不变。真实S06 waiting/calling/叫号/租约、S08治疗/医嘱来源、S09/S10/S12和生产部署/迁移/50会话性能均NOT_RUN或待所属阶段。没有生产部署或生产回滚；候选代码和所有合成库保留，不能卸载删历史业务。

完成后只写#29“[CODEX] S05修正交付与复核申请”并逐字读回，停止等待GPT复核，不关闭Issue、不改Project其他字段/不转待复核、不进入S06。
