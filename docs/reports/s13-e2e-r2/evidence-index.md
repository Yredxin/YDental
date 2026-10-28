# 证据索引

固定代码：R1最终报告 `d0b79a9edfeb725a5a7706ef3f60232be725288c`、R1产品 `dca4e1d2821b20df7b4b940d28d461270c310225`、R2最终候选 `ca07961da750dd5c58342cfe5759f45c1f806d5e`；W4 scratch测试候选 `0ea98b7b0083f9b7b43ac837c980ca4bf1a3cb5f` 与 `ca07961` tree相同。W1最初独立scratch使用与 `d0b79a9` 相同的产品树；W2／W3／W5历史目标运行旧 `d0b79a9`；W6独立scratch运行 `ca07961`。不得将不同候选反签为完整最终候选通过。各阶段原始命令、退出码、截图、结果及各自来源SHA在 [W0](phase-W0.md)、[W1](phase-W1.md)、[W2](phase-W2.md)、[W3](phase-W3.md)、[W4](phase-W4.md)、[W5](phase-W5.md) 逐项索引，W6见 [阶段记录](phase-W6.md)。

W1真实升级日志 `5912f85ab697615ebb86fc191fbbf6faa9a99c89e68a9bacddbc9b9cadf2b61b`，独立升级读回 `dbb245d34dd78737b036ec49d67efc20c78b4183441c6e1a5b6be8a3cbdf54d7`，竞争读回 `d91ebd644e142464e5c8e9fce93b847a3d74f98913d3af74bc5ae6996fcabba9`。

W2 D2实际耗材 `aeb6f959fd78776d475a82ce8552d570b426eef2e8220fef0579672812d6454f`，D1补记 `e5892532bf1e3133a7ebb93e9af1cf6c788b6bd7d9d9a956fca1746a5549d633`，短缺独立负例 `4ab9f384915dfaadfcaaf6d252cfab45d9291297379852864b44e61818f0237e`。

W3 无权403 `3076d62f1ce8bb26d4c00b736f8eb5602928c7c1f4b841b807694ebc9d3d823a`，同key `cec83c1f97f744737db2a9ffee6c94170e1ae45218a3da1b7b4391c1b3616dbd`，HTTP竞争 `bfe14834ccedf7d2f56034289e0dd35dfe81522b3513924f46ffeec57690d24a`。

W4 最终候选scratch直接403 `c3fc868ecbc09b3c2cade90644d6d8c7ec1b5bc6e38e7b10f64bdc077883a221`、撤权403 `a90bbd0c1ddcc272249ed8eaf9c2ab85e4a9452b793218ca60bdb20930da7fe0`；39项日志 `c98090781053cdd1745ee9be081ba7ce01e6b32dc7a48830f4f0607af56f293e`，包含只读事务SQL ERROR及原生重试，非日志零错误。

W5末保护 `ba63ed3f98fd41e8b1c1611b14062b4ac70ffb5d29a245ce00070cb3af1d6e4f`。原始私有日志、配置、数据库、PDF、凭据、Session与截图不得上传Public；哈希索引不替代原始证据，详细回执在本机忽略目录 `.local/s13-e2e-r2/`。

W6最终候选升级 `3260311f2b184531fa1538ed2727443c6a3e439c27372f80eaa384a5dad75982`、并发独核 `a3015b6693fef750e28468503e13d7feea76deebebc6a4692b848241ed089369`、停止 `1a8f6d84382775b938a2d1ebdcd8cae2358540f45f2584b85b70e7ede5e4c529`；账号停用A独核 `3c0263a54cb73cf3ae702391b726a82e274a171ed97a68e1ccee1a847325a6e7`，最终保护 `0f2a4dba08f1846080c5fceb64798c74b6d57a10b9ea5722ed7bb28e45e71e7a`；8条tracking B独核 `26ba4afe82524a464c744f1f119ab842ba2a2dd9e3b4e40ec67046631afbfa29`。工具提交时precommit消息未被事务内guard采到，原遗漏和源码时序推断见 [W6](phase-W6.md)。
