# YDental

当前需求 **YD-N1 R1**。唯一执行依据为 [总计划 #23](https://github.com/Yredxin/YDental/issues/23)、以下阶段当前正文及有效评论。用户逐批启用；本页仅为链接入口，不复制需求或另立计划。

|阶段|当前 Issue|
|---|---|
|S00|[#24](https://github.com/Yredxin/YDental/issues/24)|
|S01|[#25](https://github.com/Yredxin/YDental/issues/25)|
|S02|[#26](https://github.com/Yredxin/YDental/issues/26)|
|S03|[#27](https://github.com/Yredxin/YDental/issues/27)|
|S04|[#28](https://github.com/Yredxin/YDental/issues/28)|
|S05|[#29](https://github.com/Yredxin/YDental/issues/29)|
|S06|[#30](https://github.com/Yredxin/YDental/issues/30)|
|S07|[#31](https://github.com/Yredxin/YDental/issues/31)|
|S08|[#32](https://github.com/Yredxin/YDental/issues/32)|
|S09|[#33](https://github.com/Yredxin/YDental/issues/33)|
|S10|[#34](https://github.com/Yredxin/YDental/issues/34)|
|S11|[#35](https://github.com/Yredxin/YDental/issues/35)|
|S12|[#36](https://github.com/Yredxin/YDental/issues/36)|
|S13|[#37](https://github.com/Yredxin/YDental/issues/37)|

本次接续用户已授权的 **#24 / S00-B：最小运行验证**。S00-A固定交付57f4838已技术复核；本批运行结果和剩余阻塞见下方S00-B报告。交付后等待技术复核和用户效果确认；S01及后续阶段未启用，整个S00未完成。

- [当前工作约束](AGENTS.md)
- [当前工程约定与数据字典/动作模板](docs/contracts.md)
- [S00-A实际核查、Project阻塞及复核报告](docs/s00-a-report.md)
- [S00-B最小运行报告与查看步骤](docs/s00-b-report.md)
- [S00-B本批脱敏证据](docs/evidence/s00-b/summary.json)
- [S00-A固定核查证据](docs/evidence/s00-a/summary.json)

本仓库为核心 checkout 内独立 sd-addons Git 仓库。ydental_base现为英文源字符串与本模块zh_CN，提供唯一牙科入口和固定合成PDF样张；仅以S00-B实测证据评估已启用范围。当前运行工具为scripts/s00_b.py；scripts/p00.py及旧配置样例保留为历史材料，不作为当前测试指令。

docs/baseline.md、docs/acceptance.md、旧依赖清单与旧 PR 是历史技术材料；旧业务规则和 PASS 不纳入当前验收。docs/reuse.md 保留撤销说明。历史实体、代码和许可证保留，不重开旧任务，不自动合并 PR。
