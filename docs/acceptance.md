> 历史技术材料：本文旧计划、业务规则及验收结论不作为 YD-N1 R1 执行依据。本次只增加此提示，原记录保留。当前入口见 [README](../README.md)，当前核查见 [S00-A报告](s00-a-report.md)。

# P00 实施与验收证据

2026-10-10 UTC；分支 `codex/p00-baseline`；对应任务 [#2](https://github.com/Yredxin/YDental/issues/2)。本文件记录技术验证，项目负责人业务验收尚未执行。PR 和精确提交 SHA 在 #2 交付评论中记录，以免把提交 SHA 自引用写进提交。

## 实际范围

- 新增唯一自研应用 `ydental_base`：牙科菜单、URL action、登录且具有应用访问权限的只读基线页、默认停用虚拟 demo 用户和 5 项 HttpCase 测试。
- 新增隔离脚本、无秘密配置样例、README、AGENTS.md、忽略规则、LGPL 许可证及简明基线/数据与权限/复用文档。
- 本轮没有员工模型/视图、患者或诊疗业务，没有第三方源码迁移，没有修改核心文件/配置，也未在现有开发库安装模块。

## 实际命令与结果

以下命令均从 `/home/redxin/code/odoo/odoo-sd/code` 执行，使用已存在的 `.venv/bin/python`。脚本生成的配置包含精确数据库及 db-filter、隔离 data_dir、`addons,sd-addons`，命令没有明文凭据。

```bash
UV_CACHE_DIR=/tmp/odoo20-uv-cache uv pip check --python .venv/bin/python
.venv/bin/python sd-addons/scripts/p00.py install --db ydental_p00_test_20261010_baseline02
.venv/bin/python sd-addons/scripts/p00.py upgrade --db ydental_p00_test_20261010_baseline02
.venv/bin/python sd-addons/scripts/p00.py test --db ydental_p00_test_20261010_baseline02
.venv/bin/python sd-addons/scripts/p00.py test --db ydental_p00_test_20261010_baseline02 --port 8089
.venv/bin/python sd-addons/scripts/p00.py evaluate --db ydental_p00_test_20261010_native
```

| 验证 | 退出码 | 脱敏证据 |
| --- | --- | --- |
| Python 依赖 | 0 | Checked 66 packages；All installed packages are compatible |
| 应用安装 | 0 | Module ydental_base loaded；Modules loaded；Registry loaded in 14.730s |
| 虚拟预览用户初始化 | 0 | shell 提交成功；随机凭据仅在忽略目录内，未发布 |
| 应用升级 | 0 | ydental_base 安全/模板/菜单 XML 重载；Modules loaded |
| 最小自动化测试 | 0 | `0 failed, 0 error(s) of 5 tests`；5 post-tests；最终运行无 ERROR/WARNING |
| 原生复用安装评估 | 0 | hr=20.0.1.1、stock=20.0.1.1、account=20.0.1.5，均 installed；Registry loaded in 44.335s |
| Python 语法检查 | 0 | `python -m compileall -q sd-addons/ydental_base sd-addons/scripts` |
| 既有核心 tracked 文件比较 | 0 | `git diff --exit-code`；初始未跟踪 AGENTS.md/sd-addons 仍保持相同边界 |

五项测试覆盖：匿名跳转登录、有权限用户页面和菜单可达、无应用权限内部用户拒绝且隐藏菜单、portal 用户拒绝、升级后单一入口且 demo 账号停用/无系统管理权限。测试日志中的 stats 计数另包含 setup/teardown，实际测试方法数以结果汇总的 5 为准。

最终因 8079 已运行预览，使用 8089 重跑测试入口，退出 0，并由脚本再次核验 `0 failed, 0 error(s) of 5 tests`，避免把零测试的成功退出误认为通过。

私有原始日志在 `sd-addons/.local/<库名>/`。首次 install 在数据库创建前因 psycopg2 connection context 开启事务而失败，退出 1；已改为 closing/autocommit，并换用新名字 `baseline02` 成功创建、安装。原失败目录保留，没有删除/覆盖数据库。首次测试通过但有预期 AccessError WARNING，已仅在负向测试中 mute 后重新运行，最终 5 项通过且无警告。

首次预览因端口检测把测试退出后的 TCP TIME_WAIT 当成占用而拒绝，退出 2；已加 SO_REUSEADDR 后成功启动。真实占用的端口仍会拒绝，不结束任何已有服务。

## 数据库保护的实际验证

以下拒绝操作均退出 2，没有执行 Odoo 安装/升级：

```text
install --db odoo20_dev
  Database must match ydental_p00_test_[a-z0-9_]{1,40}
install --db ydental_p00_test_20261010_baseline02
  Local run already exists; choose a new unique database name
upgrade --db ydental_p00_test_unowned
  Database has not been created by this runner; refusing to operate
```

创建前清单仅 `postgres`、`odoo20_dev`（不含模板）；本轮新增两个明确测试库，没有 drop、reinit、reset。后续操作校验 OID/连接端点，限制 dbfilter；所有业务 SQL/HTTP 验证都只连接两个测试库。`postgres` 仅用于系统目录只读检查和 CREATE DATABASE。既有服务 PID 42433、端口 8069 保持运行；odoo-12 环境未操作。

## 访问验证

```bash
.venv/bin/python sd-addons/scripts/p00.py serve --db ydental_p00_test_20261010_baseline02
```

地址 `http://127.0.0.1:8079/odoo`；凭据在本机 `sd-addons/.local/ydental_p00_test_20261010_baseline02/access.json`，仅供该测试库使用，不复制到 Issue。登录后在应用切换菜单选择「牙科」，或访问 `http://127.0.0.1:8079/ydental`。

已在独立预览进程通过 requests 实际提交带 CSRF 的登录表单：web client 200，load_menus 包含「牙科」，action/load 返回 ir.actions.act_url `/ydental`，沿 action 访问页面返回 200 且含基线文字；匿名访问 303。该验证读取本地随机凭据但不打印或存入交付文档。真实浏览器点击和截图**未执行**（未装浏览器）；不把 HTTP 验证描述为人工界面验收。

## #2 执行清单与验收状态

| 执行项 | 状态 | 依据 |
| --- | --- | --- |
| 路径、Git、数据库、启动方式核实 | 通过 | baseline.md；既有修改未夹带 |
| Odoo/Python/PostgreSQL 版本、来源提交/依赖 | 通过 | 精确锁定核心根快照，明确 upstream 祖先缺失和树差异 |
| 核心/自研/第三方边界 | 通过 | 本仓库即 sd-addons；第三方未引入 |
| 最小实现与 README/AGENTS/忽略/配置/说明 | 通过 | 唯一应用 ydental_base，未批量生成空模块 |
| 开源评估 | 通过 | 原生三项实装；OCA/牙科标候选、未执行安装与原因，未冒充兼容 |
| 核心关系与唯一患者/预约主记录 | 通过（设计基线） | contracts.md；业务模型尚未实现 |
| 六岗位矩阵、员工/账号/角色分离 | 通过（设计基线） | contracts.md；本轮只有入口组 |
| 隔离/时区/编号/归档/附件/审计/幂等 | 通过（设计基线） | contracts.md；各阶段实现并验证 |
| 安装/升级/权限测试与虚拟数据 | 通过 | 两个新库，5 项测试，随机预览凭据本地保存 |
| 首版范围/暂缓项/容量与 P01 估算 | 通过（估算） | 见下方；无总工期承诺 |

| #2 验收标准 | 技术状态 | 说明 |
| --- | --- | --- |
| 1. README 可复现隔离启动/安装，精确版本且无秘密 | 通过 | 已按所述入口实跑；另一开发者独立复现/负责人确认尚未执行 |
| 2. 至少一次安装、升级、最小测试并提供结果 | 通过 | 均退出 0，5 项测试无失败/错误；早期失败已披露 |
| 3. 不改旧环境/其他仓库/非目标业务库，无核心/备份/秘密 | 通过 | 写入限定自研/忽略运行文件及新测试库；核心 diff 为空；提交前秘密扫描 |
| 4. 关系说明、角色矩阵、选型和未决事项齐全 | 通过 | contracts.md/reuse.md；每个未决项注明影响与处理阶段 |

## 容量、范围与下一阶段估算

只实现内部单诊所首版的基线入口，暂缓员工及后续业务、门户/短信/支付/医保、CAD/三维平面、复杂牙位交互、真实患者迁移和生产部署。后续平面可用底图与基础二维工位，牙位可先用表单/列表。

本轮样本库约 24 MB（基线含虚拟 demo）、54 MB（原生评估，无业务 demo），安装初始化约 15s/44s。它们只是空环境成本，不是患者/附件增长率或并发承载证明；未执行压测、备份恢复、生产容量或地区合规验收。正式数据量、并发人数和附件体量需负责人提供，P10 以预期负载做压测和恢复演练。

环境观测为 4 个逻辑 CPU、7.25 GiB 内存、工作区当时约 39.97 GiB 可用；资源与现有服务共享，不能把该观测当作生产配置建议。

P01 仅作粗估：一名熟悉 Odoo 20 的开发者，复用 hr.employee/hr.job 完成员工、账号关联、六角色基础授权及隔离/负向测试，约 2-4 人日；另需负责人验收时间。假设不含排班、薪资、考勤、历史数据迁移和多店独立核算，角色/账号规则变更会影响估算。团队容量及日期未定，不虚构总工期或自动开工。

## 阻塞、交付与回滚

GitHub 仓库 ADMIN、分支推送和 PR 已通过远端回读核验。首次交付时 Project #4 因缺少 read:project/project scope 无法读取或更新；用户随后完成浏览器授权，现已恢复访问并实际验证写入权限，该阻塞已解除。

授权后读取现有 Project 条目，确认 YDental #1-#12 各存在一条，无重复、无缺项；Project 总计 13 项，另有既有 PR #13，均予以保留。没有重复添加、删除条目或重建 Project。现有 Status 只有 Todo、In progress、Done，无待验收选项；因此只将已实际实施的 #2 从 Todo 更新为 In progress，并立即回读确认；#1、#3-#12 及 PR #13 的状态均保持原样。

本轮交付为 P00 技术实现提交待验收，GitHub/Project 权限阻塞已解除，负责人验收尚未执行。待验收说明保留在 PR 与 #2 交付评论中；不将 P00 标为 Done，不改 Issue 勾选或关闭状态，不自动合并 PR，不进入 #3。本次补充仅更新交付文档及 GitHub 状态，没有修改应用代码或操作数据库；沿用已记录的安装、升级和测试结果，未重新运行测试。

回滚：停止本次 8079 预览进程（前台启动时 Ctrl-C）；保留两个测试库和日志，切回原 `main`。没有对现有业务库进行 schema/data 迁移，无需对开发库执行卸载或恢复。已提交变更如需撤销，在分支上新增 revert 提交，不重写历史。任何删库/清理另行明确批准。
