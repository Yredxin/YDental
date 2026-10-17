[CODEX] S10-P0-21 定向验证工程增量 R2（第2/最多2轮；不重交已提交主链）

唯一授权6229311739、预检6229577294及首轮/R1冻结保持原字节。本批新B主链已记录commit_intent/commit_returned并完成独立RO/RR读回，但旧提交后比较器误用了“文书动作副作用”集合，拒绝res_partner15的customer_rank/write_date；旧decision FAIL和外层游标清理连接关闭错误永久保留，未发布b-chain成功marker，也未继续文书/原件/其它业务。

现有完整私有before/after/逐行全差异和脱敏索引实际证明：所有account/stock/fee/source/price/payment/partial等stored经济行完全相同；仅partner15 customer_rank 1→3及write_date、default/stable各1 signal。患者owner1、姓名/公司/来源身份和write_uid5全部不变。这是有明确来源的native存储分类计数，不冒称纯展示变化，也不倒推P020永久UNKNOWN。

固定core addons/account/models/account_move.py:6370–6386对customer invoice/receivable entry调用_increase_rank；addons/account/models/partner.py:883–917在rank0时立即置1，已有rank则将增量聚合到cr.postcommit.data，提交后另原生cursor执行。保存的本次真实posted invoice1和两个customer payment entry（350/390、partner15、actor5）精确对应立即1、提交后再+2。新实际比较器用本次保存行纯文件核验PASS，并反例拒绝rank+3、patient owner变化、金额变化；完整差异保存在断言前。没有改变旧门禁追认旧PASS。

修复只在新测试代码：把文书/PDF零经济副作用门禁与COMMIT独立读回门禁分开；每次COMMIT前读取固定native callback的确切partner/field/delta/actor并保存，只允许这些确切customer/supplier rank及write_uid/date技术变化。其它所有存储行仍精确全等，仅逐条native信号append≤1；不忽略res_partner整表/全部字段，不删stored金额。新商业操作仍普通合法账号，业务权限/产品不改。

外层registry cursor在子场景自有cursor长操作期间无用途地保持事务，清理时出现连接关闭。资金cursor的COMMIT和独立读回此前已完成；没有SIGSEGV，也没有实证系统根因。本轮取消闲置外层事务：先一个真实cursor核本库OID/cluster并关闭，再只把真实registry/已核db身份交给场景，由场景自己打开唯一业务cursor；不伪造ORM记录/posted状态，不调查/改变PG或OS。连接关闭的系统原因仍UNKNOWN，不声称稳定性已修复；若新的资金/业务连接丢失或未知变化立即STOP。

只读恢复脚本s10_p0_21_recover_chain.py先按上述精确源解释保存的新判定核旧已提交快照，再仅新开1条本批B RO/RR核当前所有stored行与该独立快照相同，成功后才从原提交前私有pending（实际execution/document/patient/fee/invoice/payment IDs）发布b-chain marker。经济动作、CREATE、install、configure、f1主链均不重复，不使用回滚输出猜ID，不连接任何旧库。不确定或字段不合即STOP。

产品仍be1d12a2d21771ca411ca8bdd510437980b68ef3，本轮测试实际HEAD 39880be1ae4dda46c16815ce3ca7b0ee9803c33e（R2代码425ba30及随后Decimal表示校准线性提交，非新一轮）；只改runtime/native并新增readonly恢复脚本。SHA与真实commit在round2-freeze.json，SHA256 ea4d08fddf45c40ae45a6a9123026ece4842c22a31be3e8afe468fbbb67323df. 旧freeze/脚本由各固定Git提交保存。

本条REST逐字读回后执行：python scripts/s10_p0_21_recover_chain.py（仅只读/文件门禁）→尚未执行的document_original与其余13组场景/普通Web/S10-only upgrade/最终尾审。独立RO总上限32不变，native核验进程上限因只读恢复增至3；其余连接/动作/超时/文件/数据保护预算不变。修复额度2/2用完，之后实际失败按范围/未知经济停止边界处理，不再更改冻结合同或另换库绕过。
