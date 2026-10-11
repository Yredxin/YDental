# S02 最终归档资源边界

唯一修正来源为 [GPT-REVIEW 6110056678](https://github.com/Yredxin/YDental/issues/26#issuecomment-6110056678) 及本会话用户明确授权。前四项修正已通过复核，沿用原分支，不重设计。本文仅补充原契约中 item 对 resource.active 的生命周期语义。

resource 归档只禁止新使用；已有 placement 不删除、不解绑、不复制 station、不改历史引用，仍可显示并移动/缩放/旋转。资源库默认不列出归档资源；通过固定ID读取历史SVG仍按原权限检查。

|动作|resource 要求|其余规则|
|---|---|---|
|新建 item（包括 active=False 的新记录）|必须 active|原归属/有效 floor/版本/权限检查保持|
|显式指定或改绑 item.resource|目标必须 active|不能借历史关联创建新使用|
|item 恢复（action_unarchive 或 write(active=True)）|必须 active|有效 floor/归属等保持|
|既有 item/station 普通几何编辑|已有 resource 可 inactive|几何仍有限有界、尺寸为正；station 同步原 item，无新副本|
|归档旧 item|resource 可 inactive|ID、station/resource引用保留|
|resource 恢复后再恢复 item|允许|原ID及引用不变|

实现保留 `_check_item` 的几何/归属/有效floor约束，只移出其无条件resource.active判断。现有 `_check_space_change` 在 create 后、write 前且授权/版本/锁之后，针对 create、显式resource赋值、active=True验证资源有效；不能用 context 伪造跳过。校验对固定resource记录读取active使用窄范围sudo，与原约束的参照完整性检查相同，不放宽调用者CRUD权限，不新增public API。

新增一个模型方法和一个真实HTTP方法，验证同一条完整生命周期以及inactive目标改绑反向；其余全部S02测试保留。最终新建隔离库重新 install/upgrade，原guard和完整21项浏览器回归，证据仅新增到 `docs/evidence/s02-final-fix-20261011/`。旧 `docs/evidence/s02/`、`s02-rework-20261011/` 与失败链均不覆盖。使用18104，不停止或重配原18102/18103预览及其他服务。

不写Project，执行状态保持返工；不改原生Status/workflow，不关闭#26、不生产发布、不启用S03。真实下游排期/患者任务/队列/租约联调继续 NOT_RUN；不能把本次几何和合成钩子回归当作下游联调。
