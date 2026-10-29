# 患者、服务受理与工位队列

当前 ENVIRONMENT_NOT_READY；所有用户验收结果初始 NOT_RUN。操作前先准备授权门店、合成数据及各用例前置，结果未知停止并核查。

| 用例 | 作用 |
| --- | --- |
| [UAT-PAT-001](cases/UAT-PAT-001.md) | 合成患者档案与门店关系 |
| [UAT-INT-001](cases/UAT-INT-001.md) | 服务目录、门店映射及演示价版本 |
| [UAT-INT-002](cases/UAT-INT-002.md) | 预约或现场登记资格 |
| [UAT-INT-003](cases/UAT-INT-003.md) | 实际到店与任务报到 |
| [UAT-QUE-001](cases/UAT-QUE-001.md) | 工位进入、叫号与开始执行 |
| [UAT-QUE-002](cases/UAT-QUE-002.md) | 过号与连接异常观察 |

预约、到店、报到、叫号和实际执行是不同状态；场景应链接上述唯一用例，不重复提交同一动作。
