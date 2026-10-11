# S01 最终浏览器证据

固定 commit `abf7b243b12a3717ee63cab4247ae5d5a7d5c43f`，Firefox155.0，默认安全控制，无覆盖开关；15项检查PASS，实际结果见 [browser-final.json](browser-final.json)。图片为真实页面截图，无重绘，只含合成数据。人工视觉复核及SHA见 [visual-review.json](visual-review.json)。失败/中间尝试及其原图另行保留。

- [A门店中文页面](browser-attempts/20261011T104046397328/browser-store-a-zh.png)
- [旧标签409拒写](browser-attempts/20261011T104046397328/browser-stale-page.png)
- [店长中文人员页](browser-attempts/20261011T104046397328/browser-staff-zh.png)
- [模板16项中文前后预览](browser-attempts/20261011T104046397328/browser-template-preview-zh.png)
- [撤A后B仍可读取](browser-attempts/20261011T104046397328/browser-b-after-a-removal.png)
- [原生后端全局门店提示](browser-attempts/20261011T104046397328/browser-global-status-zh.png)

从addon Git根执行，在已记录的新库完成安装、升级、probe并serve后：

```bash
PYTHONPATH="$PWD/.local/s00-b-deps/verify-lib" \
PLAYWRIGHT_BROWSERS_PATH="$PWD/.local/s00-b-deps/browsers" \
LD_LIBRARY_PATH="$PWD/.local/s00-b-deps/browser-libs/usr/lib/x86_64-linux-gnu" \
../.venv/bin/python scripts/s01_browser.py --db ydental_s01_test_20261011103447_2298e42e
```

复用已固定S00本机浏览器二进制/依赖；不重跑S00验证，不安装系统依赖。库/端点/配置SHA/PID/端口/0600凭据和安全环境先核对；浏览器只允许127.0.0.1:18089。脚本只适用于合成预览，流程会应用模板/移除A任职，不能把已变更预览无条件当作初始夹具重跑。需重新准备前提或另建新隔离库。
