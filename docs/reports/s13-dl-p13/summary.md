# DL-P13｜首个出账办理面板

**TECHNICALLY_COMPLETE（仅限定P13） / SYNC_PENDING / STOPPED**。未实现者本地总签已实际成立，远端全文/refs/评论读回尚待收口。计划 [YD-S13-DL-P13 / 1.0](../../execution/YDental_DL_P13_Settlement_First_Bill_Panel_Plan_v1.md)；[十二项验收](acceptance-matrix.md) · [原件及SHA](evidence-index.md)。本报告只评价本P13，P12仍PARTIAL，用户亲手效果待确认。

唯一产品范围是 `/ydental/settlement` 第一个 `details[name="settlement-operation"]`、`operation=bill`。它现在使用已有杏陶暖白动作，费用标签可换行，折扣与原因随宽度排成两列或一列，确认和取消有独立间距。没有增加业务功能或产品JS。

|原控件|呈现/语义|行为保护|
|---|---|---|
|Select fees to bill summary|共享disclosure，保留原生marker/Enter/Space/details分组|打开仍仅展开，不表示已出账|
|每个fee_ids|原生checkbox及整个原label点击区|原value/顺序、默认不选；无全选/清空/实时计算|
|discount / reason|原number / 单行text，局部字段组|原0/min0/step.01/maxlength300、标签/业务值不改|
|生成原生过账账单|共享primary，原type=submit仍合法可用|只测focus/hover/非激活mouse-down；不在live提交|
|取消并返回查阅|共享quiet，仍在form外|原GET href及条件保持|

只改3个addon文件：原模板的首bill呈现标记及有限wrapper、manifest注册一个新SCSS、`settlement_bill_panel.scss`。未改共享mixin/颜色定义/图标、controller/model/ACL/schema/费用公式/core。剥去明确列举的呈现后全业务XML C14N exact；完整lookup前缀及首bill后缀byte exact、594个其它旧addon文件exact；75条编译selector arm全限本唯一root。已安装EN/ZH全合成模板按同白名单还原也与before exact。

|固定候选|值|
|---|---|
|业务基线/旧P12报告|4e3e3aa1027286de473044d23f54d5faa81c9384|
|before工具/运行|850d9554891db166a47e6db23e1f02db9b5123b8|
|产品/唯一必要模块加载|83d5a002ee29dbb10177c773a81f7c2acae8b583|
|首后态工具/失败窗口|ec50407c91d9084b37ba5be95e42933e13efa2ba|
|后态实际主工具/运行|42e6bd84a5ab0cc194e64db75fd4bfba88e79618|
|最终工具发布（仅SOURCE/PURE）|3d5ecabdfdfe451df21f8f79d3a57c6268d60700|
|新分支|codex/s13-dl-p13-settlement-bill-panel-r1|

没有从main重建产品，没有reset/clean/强推。产品之后的执行工具提交只补label逐行Range和跨JSON相同序列化形态比较；最后3d5工具发布将已实际使用的wheel-v3/supplement-v5叶模块逐byte整合到有限enum分发器，仅作SOURCE/PURE检查、不重开运行。产品三文件一直保持83d字节。actual每次运行另有精确source/argv/退出/原图SHA，不能以一个最终工具HEAD反签全部执行源。

间距的唯一责任者如下（rem随根字号变大）。

|owner|值/职责|
|---|---|
|首bill details|≥1024有效CSS宽1.5rem；768—1023为1.25rem；481—767为1rem；≤480为.75rem，保原外层页面padding|
|共享action/disclosure|原.625em 1em；≤480只本面板水平.75em；正文1rem/min2.75rem，窄确认100%宽可增高|
|form|展开顶margin .75rem；fee组/字段组/submit三组gap1.5rem|
|fee_group / fees|标题到费项及同组fee gap .75rem；label自身padding .75rem，独立点击区|
|fields / field|字段间1rem、标签到input .5rem；input原生类型、完整宽度/min2.75rem|
|cancel|form外独立margin-top .75rem，无重复父子gap|

精确media为max-width `calc(64rem - 1px)`、`calc(48rem - 1px)`、`30rem`；媒体rem按初始字号决定，根字号200%另增大内部rem，不把两种放大混写。Flex基准28rem，空间不足自然单列；没有固定裁切高度、根overflow:hidden、强制缩字/缩放或viewport缩放禁令。

|物理测试视口|正常CSS宽 / 卡片px|原生200%有效CSS宽 / 卡片px|独立root200卡片px|
|---|---|---|---|
|1366×768|1366 /24|683 /16|48|
|1440×900|1440 /24|720 /16|48|
|768×1024|768 /20|384 /12|40|
|390×844|390 /12|195 /12|24|
|320×800|320 /12|160 /12|24|

普通正文/控件16px，root200为32px；操作目标最小44/88px。checkbox原生glyph20/40px，完整label承担最小点击目标，不能把glyph冒44px。原生单行reason的长值通过caret/内部横读，不能把其空textRects冒整段值同屏。

验收分层：真实普通岗位GET、原生开合/checkbox/Tab/ShiftTab/取消与未发网FormData；长8费用/正常2费用/空与无write的已加载QWeb内存组件另标，不冒真实身份或后台权限拒绝。实际nonce值只在同页内存逐值比FormData，跨请求只比脱敏业务合同；不保存nonce或单字段摘要。无实际POST bill，不证明已实际出账，原合法能力靠SOURCE/loaded/native submitter合同保持。

前态198张原PNG与319raw完整保留：root16正文14px、常规操作约37px、取消原inline盒高约16px（不是字号）、面板旧8px12px；极窄/放大圈viewport缺口真实记录。不能由个别截图说所有按钮被裁。后态核心矩阵如下，Node0只表采证结束，真实盒/字/圈另判。

|engine / 页面JS|实际岗位GET几何case|明确loaded组件case|原生Tab初态外圈viewport附加指标|
|---|---:|---:|---|
|Chromium on|17|30|0失败|
|Chromium 真off|17|30|0失败；其中actual客户端外层退出另列UNKNOWN|
|WebKit on|17|30|10+44初态FAIL保|
|WebKit 真off|17|30|10+44初态FAIL保|

每个组合包括5视口×normal/native200/root200共15；actual再加未选患者多费项1366/320两个代表；组件为normal2费项/long8费项各15，不冒实际持久费用。核心188case/1816控件、876checkbox label、34190逐行Range、244分段owner，独立0679重算横盒/文字/自身label border/裁切祖先/1rem/2.75rem/原Tab与ShiftTab次序均符合，原初态108附加FAIL单列。默认字号16px，root200为32px；普通input实高46/90px；checkbox glyph20/40、完整label点击区≥44/88px。所有核心根横宽未由本面板新增溢出。

60个真正closed computed均open=false，details高度−summary−上下padding−border精确0；原closedBefore对象188个实际open=true全保，不拿它们冒闭态。WebKit closed form仍可能返回布局rect，不能据此推断可见或占洞。C/W真off原生closed Tab跳至面板外、ShiftTab回原summary，原字段内存不变。

完整后态动作5客户端60次computed状态观察，正文最小对比5.496:1、焦点outline对外背景最小7.061:1；默认字体16px/600、圆角10px、padding10px16px，与原共享mixin一致。确认白字rgb(148,81,58)背景，quiet rgb(126,67,47)透明并保下划线；原marker与native语义保持，不添加SVG。它不是全站WCAG、屏读或实机验收。

真实有权岗位可见原合法表单；两engine实际只读角色GET200保lookup且无bill，原无费患者GET200无bill，缺读取权角色真实GET403。另有loaded空/无write分支，明确不代真实权限；没有执行bill POST权限负例。P11原有来源链接、P9文书/库存/报表只读旁路实际GET，P13 scope=0；首bill后其它操作的原class/summary/padding未污染，P12 lookup DOM有限对照与完整SOURCE冻结一致。

FormData共15 before（14actual+1states）、230 after（43actual GET+5states+182明确loaded组件）逐页内存验证成功控件/value/order/原submitter；动态nonce只同页比，跨请求只比脱敏合同。长reason300字经原生Home/End内部横读、整值保留并恢复空；可访问名称/label原关联真实核，不能冒屏读。没有live bill或其它业务提交。

部分WebKit长列表、窄屏及放大场景，两JS路径都有原生Tab初始普通输入框下缘/外圈viewport裁切。原8 finding、图、独立c149初判完整保；独立重读P13原条文808e澄清：P13 T05要求完整可达、T06要求原生次序，一次Tab自动全圈是P12 A04专项，不能将collector附加严格指标新增为P13硬门槛。原初态与普通wheel保原焦点后的可达实证分列，不将后图冒初图，不借超高label豁免普通input，不改collector门槛/产品外圈。没有实际执行CSS诊断变体，也没有为该附加断言改输入框外观。

原主矩阵108个key均有补证：104项实际可信gutter wheel（64×1轮、40×2轮）后完整同屏，4项在前一target正常wheel后本次原生Tab已完整、steps0/prior_wheel_targets明录（两unique场景×两JS），不冒原前置已PASS。104项整份补证初态geometry与原矩阵逐对象digest完全相同；108均保原active/value/整FormData内存等值、根X0、真实祖先及完整盒/外圈。另未实现者本人8项真off实跑，初态与原8完全同位，wheel后全圈同屏。独立82bb/58416实签可达，不借超高例外，不程序refocus/恢复滚动、不预先方向键、不改原collector阈值。

P13超视口高label要求完整内容经正常纵滚首末可达，glyph本体仍须完整焦点；普通低于视口的控件最终须完整盒/字/圈同屏。这仅属P13原计划，不回填P12旧严格验收。P12 lookup、fee_focus.js、RWD及三表策略均冻结，原A04真off仍36→36/left26/clip50 FAIL，JS-on已成增强和超高候选旧限制、全部UNKNOWN保持在原三报告及旧唯一回执6422670245。

完整保护已由未实现者新physical869346真实RO/RR/rollbackclosed独核：目标OID2171423/cluster7694897083368259627，全部145业务/13技术/九区exact root final34cad49b，83引用/80真实路径/三共享逐字节/size/SHA保全，六依赖和原身份作者价源/未完责任保持，同事务其它target connections=[]。

旧31622审计逐row保（含18818/25819/27673历史层），本阶段新增941正常认证/读取/旁路，总32563；before窗口160、唯一-u后窗口781分列。-u后除audit外其它144业务/13技术/七区exact。唯一必要-u native0/ERROR0：20access/1group只原生write_date，7技术表元数据及唯一1602 primary首bill arch_db/arch_prev呈现变更已逐字段独核；1620 extension及其它实际模板源保持，不是权限/成员变化或业务文书模板发布。不是全库物理零差。

65派生cache仅CSS15844→15845（618808B/SHA7d5f8b41efde7925d5717c7627f519e03724fef423010fc6996a691e7e389416），其余64/原JS15839保持；与83业务附件保护分开。54个原生浏览器均exit0/signull/context及browser正常close；Node46×0、7×2普通工具失败、1退出UNKNOWN分别保。3owned全部normal0/configremoved，末STOP **2026-10-27T05:09:12.780241Z**；4只读QWeb shell及唯一-u均0，新P13 ERROR/CRITICAL0。原共享服务未动，之后没有为报告重开app/DB/browser。经济/库存/原件PDF/打印签署/新持久费用事件新增0。

失败及UNKNOWN按原层保留：

|事实|处理/实际界限|
|---|---|
|首XML工作稿21个空白byte恢复不一致|SOURCE断言失败，产品固定/加载前修原源码；白名单/门槛不改，后全XML exact|
|已知CURRENT未提交导致start guard2；随后归档不存在marker1|在spawn前拒绝，无app；正常提交/fresh绑定后启动，原收据保|
|首after Node2：内存checked:undefined与before JSON省略key|仅双方JSON同形后exact比；原页内FormData逐值门槛不变，15份PURE shape核与真实after均另证|
|四docs/P11客户端Node2：两层main导致strict selector错误|只修采证选业务main并定向补4目的，后实际原source GET200；不改产品|
|两Chromeoff states鼠标探针未完成|一次原native拖动序列，一次混用CDP release与PW pressed状态，均exact owned graceful收尾/Node2/native0；原测量UNKNOWN保，末v5全纯CDP pointer实际12state/7PNG/Node0，未激活confirm|
|Chromeoff actual full外层143/Node exit UNKNOWN|原session46166退出143，wrapper结果缺失不补造；原17case/137PNG、native1595828实际0/close/profile removed/三PID gone完整独核6f291；不由rawstatus推Node0、不盲重拍|
|108原生Tab初态圈viewport附加FAIL|全原件/原判保，P13原可达要求以104实际wheel+4前序wheel已显独证；绝不更新P12 A04|
|closedBefore命名对象实际open|188原对象全保；60新真closed computed+原PNG另证，不能冒旧对象是闭态|
|离线命令路径/计数/依赖小误差|root/offline-helper-notes及acceptance/offline-helper-notes分层，不混成原生业务异常|

新私有0400观看包 `S13-DL-P13-first-bill-view-only-20261027-r1.zip`，**2606105B / SHA942091ca67d11f7a365153b6b6fe7ad633911fdba003471bc8a83a78ff8ca0f9**，52成员/48张原PNG。2637张全部原图和完整raw/执行源/argv/退出逐SHA另索引；观看包不代完整验收。旧P12/A04/RWD三ZIP、8263旧raw和全部旧P12报告原bytes保持。新包不上传Public，无秘密/配置/session/profile/请求体/DB/PDF/font/program。

root实现并统一报告/写者，runtime_rwd运行保护、testing_rwd采证、acceptance_rwd未实现产品或对应测试工具者独审SOURCE/真实本人browser/新physical/原件/包；同OS不冒OS隔离。未实现者本地总签 **ca9ab170684e238c092282eb5259c4d36a407fb80fd25478da33d8b75c3826f5** 已成立，T01—11及T12本地证据PASS；远端全文/refs/新唯一P13回执及状态读回尚待实际，当前不冒SYNCED。

复现（普通有写权限且有本店已确认未出账费岗位，不提交）：

1. 进入结算，选择有相应费用的患者，先读原患者及费用区。
2. 到第一个“选择费用出账”summary，Enter/Space展开，确认只是展开办理。
3. 阅读费项label中的原患者编号、日期、金额；checkbox只试勾选再恢复。
4. 用Tab/Shift+Tab依次浏览折扣、原因、确认和取消；确认按钮处不按Enter/Space、不点击。
5. 用320/390宽和浏览器原生200%观察自然单列与完整按钮；根字号200%是另一个测试条件。
6. 长标签正常纵滚读首末；若WebKit输入圈初态贴边，在字段外页面边滚轮微滚，保持原焦点，核完整圈。它不是P12 A04一次Tab修复。
7. 原取消返回查看；不产生账单、收退款、日结、治疗、库存、PDF或打印事件。

未验证屏幕阅读器/Safari/iOS/实机/用户亲手；未启真实资金/外部通道/正式政策/生产、负载恢复或组合扫码。未合产品/部署，main仅必要两文档路由。P13交付后停止，不改第二办理面板，不启动P14。
