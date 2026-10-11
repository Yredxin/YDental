# P00 实测环境基线

核实日期：2026-10-10 UTC。需求来源为 YDental #1、#2 当前正文；启动时两个 Issue 均无评论。本文件记录已验证事实，不把原有 AGENTS.md 中的描述当作实测结论。

| 项目 | 实测值 |
| --- | --- |
| 工作区/核心 Git 根 | `/home/redxin/code/odoo/odoo-sd/code` |
| 核心远端 | `https://github.com/Yredxin/odoo.git` |
| 核心分支/提交 | `20.0` / `f0c5a9b42f544e7f18dc6c8e1c93b957837e0bcb` |
| 源码声明/运行输出 | `odoo/release.py`: `(20, 0, 0, FINAL, 0, '')`；`odoo-bin --version`: `Odoo Server 20.0` |
| 自研 Git 根/远端 | `code/sd-addons` / `https://github.com/Yredxin/YDental.git` |
| 自研原有基线 | `main` / `e1f6fce18a16cfc72bfa78517ae163ada7b9dd36`（已有提交，树为空） |
| 操作系统 | Ubuntu 26.04.1 LTS |
| Python | 核心 `.venv/bin/python`，3.12.15 |
| PostgreSQL | 服务端 18.6，Docker `odoo20-db`，本机连接 `127.0.0.1:5432` |
| PostgreSQL 镜像 | `postgres:18`，digest `sha256:74935e72241653ca55e0414067e6d8763aceb8a810eb51b452253ec3dcfc4336` |
| Git / gh | 2.53.0 / 2.102.0；gh 登录 Yredxin，仓库 ADMIN 权限 |
| 系统库 | libpq5 18.6-0ubuntu0.26.04.1；libxml2-16 2.15.2+dfsg-0.1ubuntu0.3；libxslt1.1 1.1.45-0.1 |
| Python 依赖 | 66 个包，`uv pip check` 退出 0；精确快照见 `python-packages.txt` |
| requirements.txt SHA256 | `ccda41a05218bb913c4e5053e1a58ae08155c1abd7cc5c719c924251836204a2` |
| 可选 Markdown 依赖 | markdown2 2.5.5（核心 `.local/requirements-extra.txt` 已固定） |

核心提交已通过 GitHub API 确认可取得，见 [已锁定核心](https://github.com/Yredxin/odoo/commit/f0c5a9b42f544e7f18dc6c8e1c93b957837e0bcb)。这是单个根提交的源码快照，**没有 upstream 提交祖先**。不能据本地分支名宣称它是官方当前 20.0 分支的完整镜像。与核实时官方 20.0 HEAD `e98dfa0acf9213c463ed29c7db0928227c4886b4` 比较：requirements.txt blob 相同，`odoo/` 与 `addons/` 子树 SHA 不同。本轮锁定可复现的本地快照并以其 API 实测，不替换核心。后续升级必须单独确认差异和回归。

## 启动与保护边界

现有服务启动方式：在核心根运行 `.venv/bin/python odoo-bin -c odoo.conf`，现有进程另设置忽略目录内的 `--logfile`。监听 `127.0.0.1:8069`，配置的 addons_path 为 `addons`。原有 data_dir 位于核心 `.local/share/odoo`；没有把自研模块静默安装到开发库，也没有修改配置或重启服务。

开始时 `odoo20-db` 数据库清单仅 `postgres` 和 `odoo20_dev`（除模板库）。只对维护库 `postgres` 做目录查询和明确命名的新测试库创建；既有业务库未连接进行业务操作。测试库见验收记录。存在 `odoo12-db` 容器，整个旧环境未操作。

核心开始时未提交状态为 `?? AGENTS.md`、`?? sd-addons/`，后者内部已有独立 `.git`，状态干净。根 AGENTS.md 是用户既有未跟踪文件，保持原样；核心 tracked 文件保持不变。所有 P00 内容在自研分支 `codex/p00-baseline`。不添加 submodule，不更改父仓库忽略规则。

核心 release 限制 Python 3.12-3.14、PostgreSQL >=16，本轮实际版本满足。没有安装系统软件，未找到 Chromium、Google Chrome、wkhtmltopdf；本轮 HttpCase 不需要浏览器，PDF 和真实浏览器点击验证未执行。HTTP 页面、登录/权限和菜单接口由自动化及实际预览服务验证。

## 可复现的源码获取

在其他机器的目标核心目录可取得上述公开提交后再建立既有约定的 `.venv`；在当前机器无需再次 clone。将 YDental 本分支放在该核心的 `sd-addons/`，按 README 的隔离入口运行。不要以追踪最新分支替代固定 SHA，也不要把本环境快照当成官方升级承诺。

当前配置中的数据库账号、密码、主密码、运行日志和预览凭据均不进入本文。依赖清单只记录包名与版本，第三方安装来源和许可证见 `reuse.md`。
