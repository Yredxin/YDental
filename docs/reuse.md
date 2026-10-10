# P00 开源复用评估

核实日期 2026-10-10。以下只表示所列精确版本的验证结果；最小安装通过不等同于员工、库存、财务业务验收。P00 不实现 P01，不安装或迁移后续第三方插件。

## 原生能力（已验证安装，拟复用）

来源统一为 [已锁定核心快照](https://github.com/Yredxin/odoo/tree/f0c5a9b42f544e7f18dc6c8e1c93b957837e0bcb/addons)，提交 `f0c5a9b42f544e7f18dc6c8e1c93b957837e0bcb`；精确 manifest 的依赖和许可证摘录见 `native-manifests.json`。在新库 `ydental_p00_test_20261010_native` 执行 `scripts/p00.py evaluate`，实际参数 `-i hr,stock,account --stop-after-init --no-http`，退出 0，Modules loaded / Registry loaded。未运行原生整套业务测试。

| 能力 | 模块/manifest 版本 | 许可证 | 直接依赖 | 最小验证与决策 |
| --- | --- | --- | --- | --- |
| 员工 | hr 1.1（运行版本前缀 20.0） | LGPL-3 | auth_signup, base_setup, digest, phone_validation, resource_mail, web_hierarchy | 已安装；P01 复用 hr.employee/hr.job，与账号/角色分离，牙科岗位权限后续扩展。本轮不自建员工表。 |
| 库存 | stock 1.1 | LGPL-3 | product, barcodes_gs1_nomenclature, digest | 已安装；P06 复用仓库、批次、移动/退料。药品效期等附加模块尚未安装测试，不宣称 stock 单独满足全部需求。 |
| 财务 | account 1.5 | LGPL-3 | base_setup, onboarding, product, analytic, portal, digest | 已安装；P09 复用 account.move/account.payment 及原生对账，牙科费用来源薄层另做。地区税制、退款和部分付款未验证。 |

原生不适合直接承担统一医疗就诊和临床权限，未来按阶段扩展；不复制原生模型逻辑。当前 `ydental_base` 只依赖 web，未把上述三模块添加到应用依赖中。

## OCA 资源预约（候选，20.0 安装未执行）

- 来源：[OCA/calendar](https://github.com/OCA/calendar)。核实 20.0 HEAD `617a7ade45b230bfe0701abaaa1a1bc627a26701`，树中只有仓库模板/工具配置，**没有 resource_booking**。
- 可取得候选：[resource_booking，19.0 提交](https://github.com/OCA/calendar/tree/a0f55db96b9f5e1d7889b1b50dc0c3e5dd677baf/resource_booking)，manifest `19.0.1.0.1`，AGPL-3。
- 直接依赖：calendar、mail、portal、resource、web_calendar_slot_duration；额外 Python `cssselect`。web_calendar_slot_duration 来源为 [OCA/web 19.0](https://github.com/OCA/web/tree/19.0/web_calendar_slot_duration)，manifest `19.0.1.0.0`，LGPL-3，依赖 web；它也未锁定作为已采用组件。
- 最小安装：**未执行**。没有可直接采用的同主版本模块，本轮不混装 19.0、不擅自迁移全部 OCA 插件。
- 决策：P05 优先重新评估 OCA 并考虑二开适配，重点验证新统一 ir.access、时间冲突与资源并发；患者/就诊保持 YDental 契约。若采用 AGPL 组件，须明确组合与分发/网络服务义务，不能将其标为 LGPL 自研代码。

## 牙科候选（来源/manifest 已核实，兼容与完整许可尚未验证）

- 来源：[souhaibouadi/dental](https://github.com/souhaibouadi/dental/tree/5a35a0c189ba82f4a3e8e1ead681581a69f69a94)，提交 `5a35a0c189ba82f4a3e8e1ead681581a69f69a94`。
- addon `dental_clinic`，manifest `17.0.1.0.0`，声明 LGPL-3；GitHub 仓库 license API 返回 null，根树未见独立 LICENSE，因此完整授权/资源权属仍需核实。不能仅以 manifest 声明完成许可证审计。
- 直接依赖：base、mail、contacts、product、account、calendar。候选包含患者、预约、治疗、牙位和收费向导；这只来自源码/manifest 内容核实，不等同于功能实测。
- 最小安装：**未执行**。跨 17→20 主版本，安全文件仍引用旧 ir.model.access 格式，不能直接安装到已锁定核心；没有引入其代码或资源。
- 决策：保留为领域参考，当前不采用或全量迁移；P04/P07 前逐项复核模型耦合、临床修订/附件权限、数据关系和许可证。若不满足则自研缺失薄层并记录放弃理由。当前不承诺其兼容性或质量。

## 自研最小入口（已安装、升级和权限测试）

`ydental_base` 20.0.1.0.0，LGPL-3.0-or-later，依赖 web，不增加第三方 Python 依赖。原生框架提供菜单、会话、组和 QWeb；只自研缺失的牙科入口及后端组校验，没有新增患者/预约/员工模型。结果见验收记录。

全部 Python 环境版本见 `python-packages.txt`（仅环境记录，不把它替代核心带环境标记的 requirements.txt）；依赖由核心管理。P00 没有新安装 Python 包，未将第三方源码 vendoring 到 YDental。以后每次采用插件必须在这里补齐精确提交、传递依赖、许可和独立安装/升级/权限结果。
