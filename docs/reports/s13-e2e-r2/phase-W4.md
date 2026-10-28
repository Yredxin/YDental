# R2-W4 跨店、撤权和源权限

**PARTIAL**。历史合成目标以 `d0b79a9edfeb725a5a7706ef3f60232be725288c` 实测本阶段指定跨店与撤权；最终修复候选 `ca07961da750dd5c58342cfe5759f45c1f806d5e` 在独立 scratch 精确复验拒绝与 denial 审计。不同候选及数据库分别列出，不将旧目标结果反签为已加载新候选；完整保护与最终候选影响面待主控和 W6。W4 A/B/C 为新线程、同主机，不冒 OS 隔离。

## 历史目标真实身份与请求

新跨店 UID1560 正常身份：A medical/write、B medical/read，B 独核会员2547/2548及同员工1515，`471e26ae863b05ff23ae53518dd4eb76f935cc73672b5c6204762e41ca86fa2b` / `7ead045b3180ba9ee7bfd4e3071f3c5923676adc2c024a3a348721755eeb59ab`。本轮合成患者1651新增B关系1682、A关系1681保持；新 A 店空白背景2不表示真实临床事实，B `50d8d7e65765198f46431ea3f54c5edf393142f6fac3ef201fe1085e96204a76` / `7cec2eed1507e40474512557f6a5e4083f45851d0a825daae6f6fd8a5634ced4`。

- 主控亲自正常登录、切B、读历史页面 HTTP200，背景可见且只读，Context/browser关闭；B核合法读取审计及背景2/v1不变，日志 `40af0ade24e2c9dcac43b41f7b4bdbe6c12d2d31f3a7f5af9296bcf9e14e6c40`，读回 `0b5b79340bb007d79ad1040f9a10727fd22931d1c515088fba876c50474aecff`。首runner误指W2脚本而SHA断言退出1，B复现为操作错误，主控修正定向复验；原失败保留。
- 当前 B scope 直接向 A 背景2写入真实 POST403 `access_denied`，B 核背景v1/空/作者保持、receipt0，A日志 `dbb3c9623252c7518d3b1fcb16e2688140cd74ac6fbce2b09ecf27fd9c1c8ab1`，读回 `603a6ff7beead6b36b305c3ab8dc4aa38bebbc1160dc6be9a5863333a44d052c`。B新Context复现同403、无非法提交。调用顺序支持当前B写权限先拒绝，不冒已到达源店写检查。
- 同Session的A旧页切B后POST真实409 `version_conflict`，B核背景及授权保持、session B/rev3、receipt0，日志 `3dd686c28d20cf3ed8752ee49366f47cc8adfe46f37f5609647e12a55a83fd5d`、读回 `519f8dec7119b5893a6a3024f611a7de05514428cada30bd8e01b1dbfb598abb`。这是旧页版本拒绝，不能替代当前B直接403。
- A medical撤权后，同原A/session旧表单POST403；B核授权变更audit86436、对象及receipt未变 `6edafdbfad89139a2faf906f951bb1182aa48659d4f4d753e75c06b99417cc83`。A write正常恢复，audit86440、B read保持，`366adb12a8fb359887d095665efc187468651cd49d0b0b107b3137ad7e4ba801`。原请求日志 `136b77861f00e04004e74bcab005645840f6789440b2032308900196c0787c2a`。

上述患者controller拒绝未出现denied审计；B独立复现并实测空AbstractModel bool false，主控登记 [E2E-R2-BUG-001](bug-register.md)。拒绝本身有效，不能以缺审计推断非法提交。

## 原件、附件、报表与源权限

UID1560/B无settlement权限 GET bill-original1真实403，B核原件元数据和附件引用保持 `841371e70ab535dab840a37f720bfc59681bf88e91127b886da8a42e73523bd0`；未读取旧原件正文。UID1554/A document310 POST403、附件15956直链GET404（不是403），B核元数据保持且document.action denied audit86448 `da7c3bc37bab5a7f34e4fd00ac8617a1e7fad941bb3f701aefe174caec07a151`。只验证所请求入口，不外推任意附件。

UID1560/B无export时 export POST403、original_billing/169 source GET403；临时export/write且仍无settlement时这两入口各真实403，独核 `4d0b0bf511c5d16d83b6cb3f1e7c9f9b320f36d5fe0331b23e18399350996abe` / `f8a3e7559a9e5758c435ed5f7870fce9e0ce8affa7d49f4cb3769b5077337585`。403正文未采，具体唯一拒因未知，不冒全源权限或完整导出结论；临时export正常恢复none、audit86487，`dde5b59ae28e082ea9f15890e6b20c44309e14a61f66a5e499db2ae75de341c1`。

审计入口首次定位失败，B独立复现为测试工具操作错误；主控修正后1554/A页面DOM当前99行未见patient.clinical.modify（非全部审计），arrivals报告200、executions/source360 403，patient.clinical/read RPC HTTP200但JSON error/result absent，日志 `f1798b3f5b5f60b92eb516a6c0bf18c73213b0bdc62713d7685f20c1f6a5330f`，B `02789f129997b1ac23336f68dac73ab93c2ef756da1d1f9c2bd0841c58ba8812`。不将RPC error冒HTTP403，不冒独立report grant。

## 修复候选与独立验证

产品修复 `794beea`，测试修正 `ca07961`。独立 scratch r2 的39项post-test为1failed/0error、exit1：故障注入全局patch在controller前的ir.http派发抛错致HTTP500，保留日志 `3b820c8769c21ff09c77e2f8557e6af06b1944091cbcc71ba595e42b6ec41c76`，不冒产品失败。r3在 `ca07961` 39项0failed/0errors、Odoo0，B核日志 `c98090781053cdd1745ee9be081ba7ce01e6b32dc7a48830f4f0607af56f293e`。测试故障注入为替身；真实source.view审计只读cursor SQL ERROR及原生retry RW记录保留，不冒日志ERROR0。

最终候选新scratch真实普通网页登录：B→A背景直接写403、独立读回持久denied audit46及目标不变 `c3fc868ecbc09b3c2cade90644d6d8c7ec1b5bc6e38e7b10f64bdc077883a221`；同Session撤权后A旧页403，audit55撤权与audit56拒绝已提交、clinical1/operation不变 `a90bbd0c1ddcc272249ed8eaf9c2ab85e4a9452b793218ca60bdb20930da7fe0`，授权正常恢复audit60 `4797ff4e9649df012fd431952b3458c3b0335b8a2d07187d4b5034629fe7ef35`。另新scratch旧页A→B得409且denied audit9已提交 `88d20f87aae67eb736c170d818d61553bfad4dc1c94772203dc5ad93fdb7b4e5`，与直接403分列。scratch不代表历史目标已升级或使用新候选。

最终scratch三身份停用前 `bf07ca164c185b1175a14311a1e797f211cef77786b4fbe304d262f906a5270c`、后 `6c0defbfe4d7359079f74e9cb441a0da0b731e133e6baa9c21a84a1b87e854a6`：三账号inactive、3受限讨论成员正常移除、3 chat及员工/会员/授权保留、mail/通知/activity0；Session失效未测。首次runner SHA断言失败、B复现操作错误，主控定向后另有shell UID预期错误写前失败，独核无提交；修正后正常停用。B核Odoo PID3068353不存在、18584无监听、容器97f370ea4eac exited，数据保留。历史目标的R2账号和专用18554服务仍须计划末处置。

W4阶段末历史保护读回待 B 结果，不将局部检查冒全量保护。私有原始日志在 `.local/s13-e2e-r2/`，不公开凭据、Session、原件或敏感日志。

初始化 UID1553/B 临时 patient/write 已正常恢复 none，B 核会员2549、患者关系1681/1682保持，audit86491 write→none及旧关键对象/mail抽查 `1103f6db7cb78f2de8d2b2053139472e673eaf3288a8dab888690a46cfd2ed85`；显式授权行和审计不删除。

W3→W4 B独立历史保护快照 `96054c8220253448de794d638cf476634a21d03b6d7b21826adac007b664a257`：158表/94187行非敏感字段、539文件；旧行零删除，原529附件文件校验保持，新增10为W4新partner3386/员工1515附件；旧记录仅4个技术mutex revision变化（patient/intake/queue/supply），其来源待核。快照与1553授权撤回并行，最终授权状态以其后独立读回为准；不称全库零差，未列入表/敏感字段及旧前像继续UNKNOWN。

其后 B 新物理最终保护快照 `f58252e52458073088b936c4e2cdeca376cd9c57756f226861577b0574194706`：158表／94187行非敏感字段及539文件，旧行无删除、原529文件一致、新10身份相关附件无缺失；四技术revision patient 1611→1621、intake 1363→1371、queue 1481→1489、supply 1605→1613。源码 `_grant` 调四锁、8次授权审计及新增2次patient操作的计数吻合，为源码与计数推断，非逐事务SQL追踪。覆盖限制及先前并行时点均保留。
