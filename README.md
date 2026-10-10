# YDental

Odoo 20 社区版牙科项目。当前仅交付 [P00 / Issue #2](https://github.com/Yredxin/YDental/issues/2)：可安装的 `ydental_base`，一个「牙科」应用入口和受权限保护的基线页面。员工及后续业务尚未实现。

本仓库就是现有工作区的 `sd-addons/`：

```text
odoo-sd/code/                # 独立 Odoo 核心仓库、.venv、私有 odoo.conf
  addons/                   # 原生 addons
  odoo/                     # 框架
  sd-addons/                # 本 YDental Git 仓库
    ydental_base/           # 当前唯一自研 addon
    scripts/p00.py          # 隔离验证入口
    config/odoo.conf.example
    docs/
```

第三方插件以后放在独立的 `odoo-sd/third-party/<source>/`，逐项锁定来源并加入相应配置；当前未引入第三方。不要再次 clone 核心到本仓库，也不要创建第二套 YDental 工作区。

## 环境前提

本轮实测版本、核心 SHA、依赖和限制见 [环境基线](docs/baseline.md)。另一开发者需准备可访问的该核心 checkout、其 `.venv` 和有 CREATEDB 权限的 PostgreSQL 开发账号；不需要操作既有开发库。在现有工作区从 `code/` 运行以下命令。

```bash
.venv/bin/python odoo-bin --version
UV_CACHE_DIR=/tmp/odoo20-uv-cache uv pip check --python .venv/bin/python
```

首次准备环境时按核心 `requirements.txt` 安装依赖：

```bash
UV_CACHE_DIR=/tmp/odoo20-uv-cache uv pip install --python .venv/bin/python -r requirements.txt
```

现有 `odoo.conf` 只被脚本读取数据库连接字段，不修改。没有该文件时复制本仓库配置样例到一个忽略文件，在终端填写本机数据库凭据，再给每次命令增加 `--config <私有配置绝对路径>`。不得提交私有文件。

## 安装、升级与测试

把示例库名替换成每次新建的唯一名字；`install` 遇到已有库立即拒绝。下列后续命令只能操作脚本刚创建、具有匹配 OID/端点记录的库。脚本没有删除数据库或重初始化命令。

```bash
.venv/bin/python sd-addons/scripts/p00.py install --db ydental_p00_test_example01
.venv/bin/python sd-addons/scripts/p00.py upgrade --db ydental_p00_test_example01
.venv/bin/python sd-addons/scripts/p00.py test --db ydental_p00_test_example01
```

脚本明确设置数据库、精确 db-filter、`addons,sd-addons`、每库独立 data_dir、禁用 cron 和数据库列表；安装包含 Odoo 虚拟 demo 数据及默认停用的 YDental 演示用户。它额外创建一个仅有应用入口权限的虚拟预览账号，随机密码只写 `.local/<库名>/access.json`（0600），并随机化该测试库管理员密码。测试账号在测试事务中生成，测试后回滚。

实际调用为 `.venv/bin/python odoo-bin -c <生成的私有配置>`，加：

| 操作 | 参数 |
| --- | --- |
| 安装 | `-i ydental_base --with-demo --stop-after-init --no-http` |
| 升级 | `-u ydental_base --stop-after-init --no-http` |
| 测试 | `-u ydental_base --test-enable --test-tags /ydental_base --stop-after-init` |
| 原生评估 | `-i hr,stock,account --stop-after-init --no-http` |

测试使用 HttpCase 验证真实 HTTP 和菜单响应，因此测试阶段开启独立本地 HTTP 8079。无需 Chromium。端口占用时增加 `--port 8089` 等，不停已有服务。日志保留在忽略的 `.local/<库名>/`，上传前必须脱敏并提取证据。

测试入口同时检查 Odoo 退出码及最小测试汇总；找不到汇总、测试不足 5 项或有失败/错误时返回失败。

原生模块仅做隔离安装评估（不实现 P01）：

```bash
.venv/bin/python sd-addons/scripts/p00.py evaluate --db ydental_p00_test_native_example01
```

## 本地访问与验收

```bash
.venv/bin/python sd-addons/scripts/p00.py serve --db ydental_p00_test_example01
```

访问 `http://127.0.0.1:8079/odoo`，使用本地 `access.json` 中的虚拟预览账号，应用切换菜单选择「牙科」；也可在登录后访问 `/ydental`。不附公开凭据。现有 `http://127.0.0.1:8069` 服务继续使用原配置，本轮不在开发库安装模块。

服务前台运行时 Ctrl-C 只停止本次测试进程。回滚时保留测试库与日志，切回本仓库既有 `main` 即可；本轮没有生产/开发库迁移，不执行卸载、删库或重置。测试库后续清理由负责人明确批准。

- [核心数据关系、公共约定和权限矩阵](docs/contracts.md)
- [开源复用评估和许可证](docs/reuse.md)
- [实测验收记录、未决事项及下一阶段估算](docs/acceptance.md)
- [长期工作约定](AGENTS.md)

代码采用 LGPL-3.0-or-later，见 `LICENSE` 和 `COPYING.GPL3`。总计划见 [Issue #1](https://github.com/Yredxin/YDental/issues/1)。本阶段通过 PR 提交待验收，不自动合并、关闭任务或进入 P01。
