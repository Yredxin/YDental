# S01 修正 Firefox 最终截图

固定测试提交 `af7f975165bb28c157980d1d5b31de564f813b41`；Firefox 155.0；21 项 PASS、默认安全控制。全部七张最终截图已实际打开检查，只含合成材料。

```bash
../.venv/bin/python scripts/s01.py probe --db ydental_s01_test_20261011114045_4ea25b6c --port 18090
../.venv/bin/python scripts/s01.py serve --db ydental_s01_test_20261011114045_4ea25b6c --port 18090
PYTHONPATH="$PWD/.local/s00-b-deps/verify-lib" PLAYWRIGHT_BROWSERS_PATH="$PWD/.local/s00-b-deps/browsers" LD_LIBRARY_PATH="$PWD/.local/s00-b-deps/browser-libs/usr/lib/x86_64-linux-gnu" ../.venv/bin/python scripts/s01_browser.py --db ydental_s01_test_20261011114045_4ea25b6c --port 18090 --evidence s01-rework
```

probe 只可首次合成 seed，不重复执行已播种库；重新验证需另建完整新库。浏览器仅读取本机0600凭据，不输出或保存 Cookie，不覆盖浏览器安全控制。

|截图|核对内容|
|---|---|
|[browser-trusted-care-scope.png](browser-attempts/20261011T114426562757/browser-trusted-care-scope.png)|明确目标 care 范围，无无关 C 记录|
|[browser-store-a-zh.png](browser-attempts/20261011T114426562757/browser-store-a-zh.png)|当前 A 与 source.query 留痕|
|[browser-stale-page.png](browser-attempts/20261011T114426562757/browser-stale-page.png)|旧页409，源未误写|
|[browser-staff-zh.png](browser-attempts/20261011T114426562757/browser-staff-zh.png)|同公司员工/岗位授权页面|
|[browser-template-preview-zh.png](browser-attempts/20261011T114426562757/browser-template-preview-zh.png)|16项模板预览与确认|
|[browser-b-after-a-removal.png](browser-attempts/20261011T114426562757/browser-b-after-a-removal.png)|移除A后B仍可读|
|[browser-global-status-zh.png](browser-attempts/20261011T114426562757/browser-global-status-zh.png)|原生后端全局门店提示|
