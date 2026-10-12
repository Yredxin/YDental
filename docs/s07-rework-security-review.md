# S07 定向安全自审

依据 odoo-guidelines 与 odoo-security，范围为返工两处服务边界、两新增只读字段和相应测试；原 [安全自审](s07-security-review.md)继续适用。

- 来源校验：仍为私有server hook、会话/当前店/实时业务写授权，增加真实lot.product类别匹配；不信任客户端kind/UI筛选。medicine只用于处方/椅旁，material用于治疗耗材；prosthesis不开放未授权临床用途。
- 历史补账：原pending是可信already-performed既存事实，普通创建/写/删除不可达；类别、摘要、原价/时间及本店来源再次核查。warehouse-write授权库存责任人可据真实纠正补账，原临床责任人不改；操作者由S01审计追踪。
- 可用性例外局限 `_recover` 的原pending分支；新issue/source/release仍拒过期停用，不以编辑效期/启用产品闯关。已有余额和自由文本不是纠正证据；只选原pending之后同lot/store/location的done receipt/正向盘点。关联与两个时间持久留痕。
- 原生sudo仍通过既有不可伪造MUTATION对象、固定model字符串、事务savepoint/fence。返工未新增SQL、public/RPC方法、路由、文件上传、eval/pickle、动态代码或可由HTTP构造的可信来源。
- HTTP类别测试用例仅在HttpCase生命周期内mock私有 `_issue` 为服务端冻结来源桥接，实际网络请求经过原controller/CSRF/会话/授权；没有向安装模块加入合成HTTP/RPC端点。独立pharmacy-only、medical-only类别负向在模型与真实双连接中覆盖。
- 两字段readonly并不单独构成安全边界；实际依靠原record.create/write token与禁止普通删除、S01源权限/公司域。新增HTTP读者恢复/原生RPC伪写负向，继续原跨店/撤权/附件/导出测试。
- 失败链保留同秒旧收货误选及修正ID顺序约束；新native done后异常仍完整回滚原pending，恢复竞争只一move。SQL额外核对历史补记纠正关联。

合成来源不代表真实S08真实性审核；真实来源适配器仍默认fail-closed。未来接入需真实不可变来源及原始执行时间、执行人/数量验证。截图/JSON只含合成标识、日志哈希及脱敏事实，不发布配置、密码、cookie或原始日志。

SIGSEGV属运行证据风险，不能靠代码安全自审判为修复。根因未确认时继续阻断正式部署，所需观察/后续定位见返工报告；不修改核心或系统依赖来掩盖问题。
