# DL-P12 证据索引

阶段 **PARTIAL / A04 OPEN**。本索引只列脱敏指针、大小和SHA，不上传private原件/数据库/凭据或效果ZIP。所有原图/actual执行源/命令与退出保留本机；不能用快照或PNG数量代验收。后续远端同步及总签旁签在同目录独立保存，不循环嵌自身未来hash。

完整原始文件清单：`.local/dl-p12/viewing/raw-evidence-inventory-r1.json`，**6059项 / 1408697B / SHA256 1d35b307b36e680661f0110326414fb5ade13bfe2e78841742ae0452d80d91e3**；清单本身不包含文件内容、不进入viewing ZIP。索引截止 `2026-10-26T17:04:03.385792+00:00`，之后的独立总签/同步收据另作旁签。

## 固定源码

|文件|SHA256|
|---|---|
|`ydental_settlement/views/ydental_settlement_templates.xml`|`dd4355d9f733325800d7cbd606b058894b53fd0301fb60b7b43e255c2c3994b1`|
|`ydental_settlement/__manifest__.py`|`41b3575f0d36e8c71a070f3a58319078d874d8270484472b36747047c539b5dc`|
|`ydental_settlement/static/src/scss/settlement_readonly_actions.scss`|`dbe8f7a2284f8f18978ec7fa2869ac9f15939789ac56a17e482843da8e795beb`|
|`ydental_settlement/static/src/scss/settlement_lookup.scss`|`4b0a880cf42eb9d2297452dff42c1b47ad45a069180488249413aec3d55cd49d`|
|`ydental_access/static/src/scss/_actions.scss`|`75127c581456d5c88aa62baaf34e1e1efd6f2c1374b8b3ed4ba53dbc24d1645f`|
|`ydental_inventory/views/ydental_inventory_templates.xml`|`01d4c1a1df7136bd2e573d8559c5d818754cbc571cc3581fe76d11fcd7bf7223`|
|`ydental_inventory/static/lib/lucide/SOURCE.json`|`c3902c5151c465af0dfa6accbe6c1fcbae52acb6d511114c57f7ccef1aece3d1`|
|`ydental_inventory/static/lib/lucide/LICENSE`|`1e7290b35280a048667bbf0ebabac1c7fd52a75300e8b2946ac165715997f2bc`|

## 逐实际客户端

SOURCE来自每process原始归档，code2不反签whole；状态/有效子层以raw result与独立审查为准。

|实际label|候选|Node/native|状态|PNG|result SHA256 / process SHA256|
|---|---|---|---|---:|---|
|`after-chromium-events-v1`|`2df168f`|0/0|P12_AFTER_CHROMIUM_EVENTS_PASS|1|`473d49c3f265a268528036813db719fbe92cc2ae89faf5c76d303c39c2950d3e` / `d8a81f49a029254f3bbdf988c0dcad311ef0b05886ecae745e3fb6a2e6bd5a6a`|
|`after-chromium-layout-v1`|`2df168f`|0/0|P12_AFTER_CHROMIUM_LAYOUT_PASS|33|`043cb59b188c7aa2404bbfa89f4fecbdbbbd8cc4ac991f0e9e81a885a685d5e6` / `aa8046690721753c7ec24b2c84613bf81cbbf66eb7112bc62bfcc4520575a6a7`|
|`after-webkit-events-v1`|`2df168f`|0/0|P12_AFTER_WEBKIT_EVENTS_PASS|1|`499fa6ac725397f688c9bc30dd104604c614ab7914455f8791fe76044ccfbb79` / `e9ef7ec68c3da6f5f175858aea53a2c0000ae3df7da16cd50ddb02294644bdfe`|
|`after-webkit-layout-v1`|`2df168f`|0/0|P12_AFTER_WEBKIT_LAYOUT_PASS|33|`7728fcf4cf3c128d3d43307cf35cba3f3f4c7d4a2828381edfcc939f71d5cabb` / `5e26aab9bfca9ab501d12afd25ce7a4ad942223402ac86bef50d5458f1068cce`|
|`before-chromium-documents-v1`|`0558abe`|0/0|P12_BEFORE_CHROMIUM_BYPASS_PASS|1|`ce49c8ad1f3ff9094e8d913aeb221547b8655cf7dcbbc50bda34ab5d62aed781` / `6d5e341eca5f89bab56e27df001b8959e22ac0c2fb3fd9cff1639da6b235dfb8`|
|`before-chromium-error-v1`|`0558abe`|0/0|P12_BEFORE_CHROMIUM_BYPASS_PASS|1|`083a10949738fc6595eb0e2b4538b2bb65b696253b9bc7cf6a08df714f92cfa5` / `03fc027bccb7ac80b5bfd1af503f27cfa39b3991968e058741c460e584e49c40`|
|`before-chromium-inventory-v1`|`0558abe`|0/0|P12_BEFORE_CHROMIUM_BYPASS_PASS|1|`d46061a2a8c3b082913298bf3c9c1a7c5e7d1935dfbf5fbc427b63a517335065` / `2c11a679a1c1f258fac9db2fd8dba50c4e429e3e971656596e43355ab20e673a`|
|`before-chromium-layout-v1`|`0558abe`|0/0|P12_BEFORE_CHROMIUM_LAYOUT_PASS|33|`1702de09ac8beaa63d6aea6c06a9e4c44e592fb484b861dbc5700e159651f323` / `5a7cd50aff367bb14c0cb52cfd3eeac1a1a8d96f37f5df4334694a13929b7d69`|
|`before-chromium-reports-directory-v1`|`0558abe`|0/0|P12_BEFORE_CHROMIUM_BYPASS_PASS|3|`7656185c2f580cf4667b0cbf8db24a8c0eb649633c2bb53801a4bdf596830876` / `90ec4a48b8bfa1220dc441ade77f35bb5409fa1f80f1583e2cb0f54cdfc31067`|
|`before-chromium-zoom-v1`|`0558abe`|0/0|P12_BEFORE_CHROMIUM_ZOOM_PASS|12|`8f02a85377d2692d2d85101e929d66337cb08a48df0729fa28dbfbc64748a6a6` / `0a5dceccdf3dded309eae5f5520a3b60dfa344a068ff05990544ad812d1618a9`|
|`before-webkit-documents-v1`|`0558abe`|0/0|P12_BEFORE_WEBKIT_BYPASS_PASS|1|`ae29cf2d1cc8ab2bf381a37f533c203a934b8091561f79cd31719a1bc39a243c` / `1f8b2b86d7e7a449ccc5f22d010a4fe488707313ebb629a8509fa356a944bbb8`|
|`before-webkit-error-v1`|`0558abe`|0/0|P12_BEFORE_WEBKIT_BYPASS_PASS|1|`a52a6d1bbce075b8db60f6979624ac7b6060d39c1f00d3ff2fd1a6b6cad85c3b` / `b914ed1f911dd8e8b0d6c6210f42c2d6ef9853fe9ef1dfad0164d73bdaa942be`|
|`before-webkit-inventory-v1`|`0558abe`|0/0|P12_BEFORE_WEBKIT_BYPASS_PASS|1|`3bc629f1b13110aec4fe133e7e6f85a6fa481c693c7aff775e6d7ead4543049c` / `31941c6b935a4930d46efa5bf45147b2cd8ab32abd32fa513bc297c0d36d68c7`|
|`before-webkit-layout-v1`|`0558abe`|0/0|P12_BEFORE_WEBKIT_LAYOUT_PASS|33|`ab21ec51375c9ae62e5e66ab2c03a9d9b8efc4d4f7cd90067f16ee5b54793643` / `818efe29d408e9c146763e59bda22895a2429e3b0bd7cb7e29394a1f9bb06fe3`|
|`before-webkit-reports-directory-v1`|`0558abe`|0/0|P12_BEFORE_WEBKIT_BYPASS_PASS|3|`07f1c7841856a381dd1bd759d3bce52fe72955c111f54368cfef63d6184948c8` / `f4746e6a12ce3e6d42ab9babf352f3a61e2f5723166febde43c00f8510f7720d`|
|`before-webkit-zoom-v1`|`0558abe`|0/0|P12_BEFORE_WEBKIT_ZOOM_PASS|12|`280dd4681a921b930236199f7cef116fe94bb667e0ba5e6497c21e3fc1073889` / `2836b22513fd6f72fcb93ffbbbef8548fd097e8c0939e177c38b2c5708b0a37d`|
|`diagnostic-chromium-oversized-v1`|`0670010`|2/0|FAILED_NO_AUTOMATIC_REPLAY|3|`792228b962c512029a0457b9fdb298828e5b9ecd6f8c88156824a30fe90e4393` / `3b3b88e543190c131f2b8630108eb6e30e995ee7690867fd1bb5cf1c3bbf5c88`|
|`diagnostic-chromium-oversized-v2`|`0670010`|0/0|P12_OVERSIZED_COMPONENT_KEYBOARD_DIAGNOSTIC_PASS|8|`d0ebf577af4647d19c38ec153e18b494c35e93c42b6d61e58f278275a0ab70b0` / `298743a692c4bfb6271acda1b43e98de23308a1c97c7cb5ca19fe2f9eb1a0a87`|
|`diagnostic-webkit-fresh-seed-v1`|`40d8cf0`|0/0|P12_FRESH_DOCUMENT_NOJS_SEED_DIAGNOSTIC_PASS|9|`608b36e33d6303f48f936afc1549d7d3c6c8e14c9d3da8a19952d34520ba72fa` / `afb8fcbd8b2d9cebc91a4b72248d0c2a6b01e39da070cdf69956829da5a4c48b`|
|`diagnostic-webkit-oversized-v2`|`0670010`|2/0|FAILED_NO_AUTOMATIC_REPLAY|0|`ef5a936e366a6e880c2f49e7c6e5b079c162bf9ead7175a8947e3494b87f6d97` / `09fcf52c1a6ecc12b4e558743600d24e528c9514f0f62c6c932f21f4500c7977`|
|`diagnostic-webkit-oversized-v3`|`0670010`|0/0|P12_OVERSIZED_COMPONENT_KEYBOARD_DIAGNOSTIC_PASS|6|`7a6b8cc389e6941ca3f713308792e077147838aff70616f5ddeb8901a8dd986c` / `5c254dddc1e9fd92794666ccdf3d6d5cca7cce2f945cda4523ac7294a07c8bf4`|
|`final-chromium-events-v1`|`6cc8d63`|0/0|P12_AFTER_CHROMIUM_EVENTS_PASS|1|`1729e6eae1205a09e323f869871b2361ce095f567827564ebdf4ffcd9dad66ce` / `356b7821678b325821432a11e80c505945072d703a258ed5dd05abda4d5bac1b`|
|`final-chromium-keyboard-v1`|`6cc8d63`|2/0|FAILED_NO_AUTOMATIC_REPLAY|2|`3c405c55a43cb3ef449cab4a33cb6fcdc0f7a321c8f664315622290ecc277a53` / `6549c2ad8af21c00976109f149236563d85d07a3ed9543c95ad3201437a77ebe`|
|`final-chromium-layout-v1`|`6cc8d63`|0/0|P12_AFTER_CHROMIUM_LAYOUT_PASS|33|`51313071f443a4d489b8b71b5860af6764326c1970821f6b49327e2598cc970f` / `f65b35b9ded9c107dbd46ea94cf7e831ad087137e4d77bfcca320c40b814b2ca`|
|`final-chromium-nojs-v1`|`6cc8d63`|2/0|FAILED_NO_AUTOMATIC_REPLAY|6|`fce092b97a640d34a133c7cc09a57fbefe5b9046257b527e49c9432178649125` / `1dc924480acccf220803bfd291b767ffa6a7e5fecb14aebb333911f0b9603537`|
|`final-chromium-nojs-v3`|`6cc8d63`|2/0|FAILED_NO_AUTOMATIC_REPLAY|1|`1fdd97a30c70c367e792443463290f64abf3ae47307227a7b5f433bd89dd00e0` / `053cdfb730166796e0c8b98998f7c96ffda6bf82bb0e0cd4ffa5d42c0a268697`|
|`final-chromium-nojs-v4`|`6cc8d63`|0/0|P12_AFTER_CHROMIUM_NOJS_PASS|14|`bdd9da4df7745110e607c89ba3d9132427588e4c84e4ce5ed3b5434a5b1e8ef3` / `6080eba91e6b33e81c156cde304413cc2009763a28fb9878b156e8a3f45c9ccf`|
|`final-chromium-permissions-none-v1`|`6cc8d63`|0/0|P12_AFTER_CHROMIUM_PERMISSIONS_PASS|2|`a25166c828a4728b5ec2e90d6ab3444533a4ee785cc4573dee4b9c6df669b965` / `122c268f8368a888b2fd391de9d23883ab55a3538b3f9f5c8840329d89fee9bd`|
|`final-chromium-permissions-v1`|`6cc8d63`|0/0|P12_AFTER_CHROMIUM_PERMISSIONS_PASS|5|`68df1afe9b89b7b1247911e5d7cfd1c48220ab0550b3d713296f4d9657fea876` / `eda548fa5c60773bf91f3f703fc1bddf5b7278595587c90b57951c0b73116478`|
|`final-chromium-zoom-v1`|`6cc8d63`|0/0|P12_AFTER_CHROMIUM_ZOOM_PASS|12|`1c97ba02288ea6ba1825b42c6d82d8eb00952d2f38b7a003fc4d87afb1305ecf` / `1e2ebe4c9069811889e3586747655e622d114bf60274fac7a00a2a011fa008d5`|
|`final-webkit-events-v1`|`6cc8d63`|0/0|P12_AFTER_WEBKIT_EVENTS_PASS|1|`e9a4cb958ecd27b77e2f2ad031e21b4f687b4a55f969d735fcece6766362c52a` / `b8d108432016aebd650c872b1e8a0f14293f53004cec41c8aae0fd7e841efae6`|
|`final-webkit-layout-v1`|`6cc8d63`|0/0|P12_AFTER_WEBKIT_LAYOUT_PASS|33|`9132b6f370827056982edb58d483deed527592279286d9d3fd1f1acbc915b5f5` / `28d69720b3242aa783a8a8d22e8b7267e25348db9abe7c71dcd8810df36c513d`|
|`final-webkit-nojs-v4`|`6cc8d63`|2/0|FAILED_NO_AUTOMATIC_REPLAY|8|`425b591a47c611670441f4772379ddfd5fdf472e882cb4932c1c094a3dbc46ae` / `2db6ea6c6db58242bd49d2251fe83d11e92d1385db71d39df1f773d4614e38e3`|
|`final-webkit-permissions-none-v1`|`6cc8d63`|0/0|P12_AFTER_WEBKIT_PERMISSIONS_PASS|2|`6f5986716f731523b7671b6c319f2154ad9a56cd999654ffab977b521fa9e833` / `e873fd0db20cc95b6223d0f6f3da7fd5745ead8c94568fea455ae07bd1ab2bf8`|
|`final-webkit-permissions-v1`|`6cc8d63`|0/0|P12_AFTER_WEBKIT_PERMISSIONS_PASS|5|`f8fd0c5e256761ad2a5f42cb7d5e17ae155c581c6db123d5d69f21998eee517d` / `f29cab0a286406d4352ae7d7a11e8110989ebb2dabc8d911737821716d0f0d9b`|
|`final-webkit-zoom-v1`|`6cc8d63`|0/0|P12_AFTER_WEBKIT_ZOOM_PASS|12|`4a2b19837c15f0c09500b93929ceee505920a73620540fa77ffc14c89a14f72f` / `27ee72fc9403dc51d6f932c2e920daa810805b9ce73a3d1f852215abae2920cf`|
|`final3-chromium-components-v7`|`40d8cf0`|2/0|FAILED_NO_AUTOMATIC_REPLAY|114|`2d58561ef528efa54c1bb5a35c37004683e64a1af13833c7eec9f95383dd1c33` / `26ba4946e7488b547e7a7b70eb0eaa0ccbd96bbbf8ae5aca289aabbecc1187b2`|
|`final3-chromium-documents-v1`|`40d8cf0`|0/0|P12_AFTER_CHROMIUM_BYPASS_PASS|1|`0c0a39bf6a29ee279f33a7bbd66b0c9c6823c0584eb1fa5237c8048aed59e9c2` / `18f14eded27e6e44b921e7e2f9755c61b925ebcea3e2f289fc9e3783be8ebbee`|
|`final3-chromium-error-v1`|`40d8cf0`|0/0|P12_AFTER_CHROMIUM_BYPASS_PASS|1|`898c8726fb22b0200729162b4a9356a93605f01f235da38788c199042af4faf1` / `66f771ed34e23c1f3d67482848c65a836db6a572fbc6816adfce69082651964a`|
|`final3-chromium-inventory-v1`|`40d8cf0`|0/0|P12_AFTER_CHROMIUM_BYPASS_PASS|1|`801b34c27e00dd16f2f63eeaafbb2804a91d43fb46ab78bb77d592dda40a2b86` / `53bf96a092bd0d2992a01becee945fe7ca6638d8a3492faa746ca4fe651f8914`|
|`final3-chromium-keyboard-v7`|`40d8cf0`|0/0|P12_AFTER_CHROMIUM_KEYBOARD_PASS|4|`f50e8b2814d8ac713051b15b89d4239538dfbf329c653d52346d1ad40e51ab2f` / `05d39af7065f72520f77640201167539475018244c7ab3aab1a134ba85af0942`|
|`final3-chromium-layout-v1`|`40d8cf0`|0/0|P12_AFTER_CHROMIUM_LAYOUT_PASS|35|`378753f19df1abd5ffef1ab96a8860d4e76a439d479a64bf31e259b9cb60ba8b` / `8ba1750e3c1ad0cfe4361730d19b14fd5d61902252bddc0154a94d0d52a586e0`|
|`final3-chromium-nojs-v5`|`40d8cf0`|0/0|P12_AFTER_CHROMIUM_NOJS_PASS|14|`ce5e274658ef2dcf7930f044003db545ca7c634720a40e7a84c72fc542edbaa4` / `9d3b5a98ce5de1a5b55d309a7d7cec91c0e35af85696728cff9ff7173f520a21`|
|`final3-chromium-reports-directory-v1`|`40d8cf0`|0/0|P12_AFTER_CHROMIUM_BYPASS_PASS|3|`d8c1774c263f768edbdab19bc1f79f236b5c6fd69ba02d0ce55b284606b04e48` / `9af90e39a8b5d042146d503417223c2f5a46a167856b89069a41f422d7213dfb`|
|`final3-webkit-documents-v1`|`40d8cf0`|0/0|P12_AFTER_WEBKIT_BYPASS_PASS|1|`2531d6c7666a72d8934d3b44b9bc5f276f9f48d1176876fd6a34352d752b4090` / `faf1b82a26d4c7122592acef8007a91db67767e241375d7f221b053927856440`|
|`final3-webkit-error-v1`|`40d8cf0`|0/0|P12_AFTER_WEBKIT_BYPASS_PASS|1|`9b7645a58fedf25aa477b4f196b751c3df2245681884a005ba16cf61c07d9141` / `0a84457fd63a41def331b3bc13680393c3cfee239b94409e430021b31a78a504`|
|`final3-webkit-inventory-v1`|`40d8cf0`|0/0|P12_AFTER_WEBKIT_BYPASS_PASS|1|`453cfb15ab26ac8d2895bf207cef1b4d42f02ddf0ef60da3ffcd824934ea00a4` / `8d82a51bed56e085cbce14f0de09e0c849959e740e796796f3065ca71d464967`|
|`final3-webkit-keyboard-v7`|`40d8cf0`|0/0|P12_AFTER_WEBKIT_KEYBOARD_PASS|4|`f0ebf9b67942bd4a8c52d900e83a825e45f7b39935900d6eb927f5c920377a6f` / `536433f54b065a1b12c6d99743b6168ec7cf854fdbdee5e06d830449c49d6396`|
|`final3-webkit-layout-v1`|`40d8cf0`|0/0|P12_AFTER_WEBKIT_LAYOUT_PASS|35|`dc11197d2c402f4c6d4f2b72b19e26a68179767f7b65b586140938261fba0c44` / `3d6c5dfd234ca4b7e8776dd5f043d542035e22a85e433afcb326c6523c6b6a6e`|
|`final3-webkit-nojs-v5`|`40d8cf0`|2/0|FAILED_NO_AUTOMATIC_REPLAY|8|`5359d3826799a79186fef962fcf0a4703ff7c8fab904c02abe33afa2aebd454f` / `f773a71de74a56a0b244911e79c7dba8f7a7da6471553398a0b51cc3726ce0c0`|
|`final3-webkit-nojs-v7`|`40d8cf0`|0/0|P12_AFTER_WEBKIT_NOJS_PASS|14|`b68d09c501107f98ea41b65a7a1d7eae3f64e8bb26bb16cba60fe21ea6c68d0d` / `dd398fb26f037fa24522482d597047e5cc5f9fff0de92d0a5c5b6632c69d8d36`|
|`final3-webkit-reports-directory-v1`|`40d8cf0`|0/0|P12_AFTER_WEBKIT_BYPASS_PASS|3|`125e14a6164f12beebed41d5cea7b11a9d1613890730474fb705fb11ac2c6b2c` / `f5970869be80cd846c0e3450702661a1fbc076f0aaabedcf4990a639c7bf2a79`|
|`focus4-chromium-components-v9`|`0670010`|2/0|FAILED_NO_AUTOMATIC_REPLAY|47|`8b522fff7cf95c21ba1eb534a1207cd2234557f96fe4c186dfa9dead896f3d8c` / `e4abc00feeeab4bdc171b91147022672aca1d87430e2944af216c5f8f1131838`|
|`focus4-chromium-keyboard-v8`|`0670010`|0/0|P12_AFTER_CHROMIUM_KEYBOARD_PASS|4|`d269b4c6fcdef4416eb137224cc86e7c1ab762c55426b006d7eb85e25f08c6c8` / `9c7e28250e258874b3b30ba57302c33e6940aec65248c4b9108a2464b76d6afe`|
|`focus4-chromium-nojs-v8`|`0670010`|0/0|P12_AFTER_CHROMIUM_NOJS_PASS|14|`eda689d21f932465c169ce30e3282f7e5eb085a1908cc5936a32995b3eafefd7` / `bc33c9062d2f1846b9b3e2912e401f26a2bc620ef32337cdee468199520e4f0f`|
|`focus4-chromium-zoom-v8`|`0670010`|0/0|P12_AFTER_CHROMIUM_ZOOM_PASS|16|`136680274eb2f5a495860bba38579ce7d0fa7be73f87bdc4ccb339b88f5a9af2` / `3ac38ab9207c616688d1acf269f434c4131e03fdd52db54f27d2e5f692ebf95e`|
|`focus4-webkit-keyboard-v8`|`0670010`|0/0|P12_AFTER_WEBKIT_KEYBOARD_PASS|4|`031874c05e6dad511c7c7154fb68911da06352c951a116bf79e5730522d70d03` / `41890a0cdd57c40a7b81480dd2b5f7054267b37daa7b252c73855ae84018a525`|
|`focus4-webkit-nojs-v8`|`0670010`|0/0|P12_AFTER_WEBKIT_NOJS_PASS|14|`6137a899d5dcc2e568f1880fd79094a86cb0191d1a571fcf528176698650fe6b` / `eb033fb822cff9ffc69b1146acd2de5a68a4da7a679542682e15383b082bddf4`|
|`focus4-webkit-zoom-v8`|`0670010`|0/0|P12_AFTER_WEBKIT_ZOOM_PASS|16|`6a3f3979bc14085bb3b789546e830a122afa10d2711dff426e8d58ba0e191650` / `a655d9182fbcbff4b1348839b3f1ad878f2a621745478e5dd30c9c2178184dcb`|
|`inline5-chromium-retained36-recovery-v2`|`0f1deb8`|2/0|FAILED_NO_AUTOMATIC_REPLAY|2|`313b691dbe348b67e809db230162479cb1cb9b259b9ee8ab5dfda802d5d2a77b` / `664f1d8abfdb68409f8ba9ccec807c55bb8b01c0911a90fbeea04dcfea4172e1`|
|`inline5-chromium-retained36-v1`|`0f1deb8`|2/0|FAILED_NO_AUTOMATIC_REPLAY|1|`0436f87eef3726f5ac1ede05e872e5cfedc826f16b421cf8eddafd828519c53e` / `4e5df972874ab74f78402e42eb6fc2d80dbd79ac806640d159c60159dcab0a1d`|
|`inline5-webkit-retained36-recovery-v2`|`0f1deb8`|2/0|FAILED_NO_AUTOMATIC_REPLAY|2|`200ffa3eb72c8646a5405eab30307f6bad6f538f210b35a4624dc66b9b2cab5d` / `fc2b0a5c699f677f2c1aba3229f1c493f19a0ee8516f2d73236a03d410361894`|
|`native5-chromium-keyboard-v10`|`0f1deb8`|0/0|P12_AFTER_CHROMIUM_KEYBOARD_PASS|4|`e294ca5690ef3dec0890960a33ed6932f08908ba685717496e8779ebd1f5a369` / `803940a3b6cc2479691d438814bcb7fb3cdef6bb059d1de0950d9e7ffd8385f6`|
|`native5-chromium-nojs-v10`|`0f1deb8`|0/0|P12_AFTER_CHROMIUM_NOJS_PASS|14|`bf6e1086b2ae5c40638b227eb2a8c63d7ba2f9f929d44dfe42c1da68fd890439` / `afd6fc6523cfc84fc3507ea76bb29e7da8a2e299e63422f63e63b73da859e16b`|
|`native5-chromium-zoom-v10`|`0f1deb8`|0/0|P12_AFTER_CHROMIUM_ZOOM_PASS|16|`21396556cdaa7dcc915b2281220764b8d5e7dcc03ee2ad205f421ff8bfbfbb78` / `d59d08c8ea98620c366b67efbfe8bf3b55283d96a0ce29c359457f0d50432503`|
|`native5-webkit-keyboard-v10`|`0f1deb8`|0/0|P12_AFTER_WEBKIT_KEYBOARD_PASS|4|`a9b218188c8d024a7ef236ae732c7f573774afbae7c6f83b7c27c3ff8957903c` / `8fbd797291d320a44bac39c53eee70d8cad57e968fad21bc16d056036e915629`|
|`native5-webkit-nojs-v10`|`0f1deb8`|0/0|P12_AFTER_WEBKIT_NOJS_PASS|14|`95476b726d4fa90278117a6891d2ec1728996cdcbf6a9f2e3cfe2062cd6bb995` / `96572d9caa0c8c9cdda2578e56ac4cbca78c6756f93ea728c02e84150a25f72e`|
|`native5-webkit-zoom-v10`|`0f1deb8`|0/0|P12_AFTER_WEBKIT_ZOOM_PASS|16|`b40aeea5d274fb3d1f07c18b8d8acadb30d8ba628434129f191ecac8dfe3e45d` / `6419684cad546f896d65ff59e1a9b4295ed65d93d937e976029eb98aef3010ca`|
|`partial5-chromium-components-v10`|`0f1deb8`|2/0|COMPLETE_WITH_OPEN_A04|70|`d32361798356e7d6699692ff96f373d4944456c7a70bba84daaabd08f44b7c05` / `f32beb355b75737c72a99eba2c490d7be0a65c368549a59f6e6b9453e2b7a1c0`|
|`partial5-webkit-components-v10`|`0f1deb8`|2/0|COMPLETE_WITH_OPEN_A04|172|`c23c9ba9819b613d64102ee05e39b0b4052dc44a87664af2b8dcfaa2edc6eb07` / `15a07977d0becaf749787a8d50c5e0705e2f0b1443d5a55cbc63a55eed62731b`|

## 关键原件和独立旁签

|私有相对路径|bytes|SHA256|
|---|---:|---|
|`.local/dl-p12/acceptance/after1-all4-browser-integrity.json`|58151|`c4660e21a03a0c7eb1fe7ae64bca478ecf6d53443e9ea284afcd9827a00ce812`|
|`.local/dl-p12/acceptance/after1-window-protection-independent.json`|2201|`d84656ccfc476c9f27b30cb2f768c9f7cc9702fc9107192b82b686eff312e3f2`|
|`.local/dl-p12/acceptance/after2-window-protection-independent.json`|2210|`3c1f57746b3ce4bfcb4b5635ba9ed01d4b82ef182562cfd164c32f520376056d`|
|`.local/dl-p12/acceptance/after3-window-protection-independent.json`|2682|`ca35596e965acf2f01b2608f9867da64cf274a508dda03da138b77efd9265ecc`|
|`.local/dl-p12/acceptance/after4-window-protection-independent.json`|2069|`a453ad3a3b4b6c76682a2df17921618d1aafce7e4893e3552c63feb282dd08ad`|
|`.local/dl-p12/acceptance/all48-before-after3-browser-integrity.json`|458746|`fd7bc9b2ce2557bafde1f0158a8a64ad4cff0b8e94417e7bb181257080beb65b`|
|`.local/dl-p12/acceptance/before-all12-browser-integrity.json`|80565|`c50cf906ec54ad718185b518421d55e5cde49b0f72aa6cd62ad8094040ac6b1c`|
|`.local/dl-p12/acceptance/before-clean-runtime-review.json`|1707|`b47517c2993e22b4debbf85418aa1f20c206ddafcc588f68f93309d8203bb561`|
|`.local/dl-p12/acceptance/before-complete-protection-independent.json`|2073|`a4d21d2b881cfcc3a0d568a3f3d3b4e710725ac0620d4d704ffe34b77bcdc195`|
|`.local/dl-p12/acceptance/before-layout-and-finite-bypasses-browser-integrity.json`|61806|`e5dcbda788e96ebd1e5898021a9acd4dbcd9c3cdf524ec3144d881ff1a97d627`|
|`.local/dl-p12/acceptance/before-layout-browser-integrity.json`|44939|`d986a54e65b1529899642053c799640a8bf1e4be7e886ec84769afcd75cf6802`|
|`.local/dl-p12/acceptance/before-native-connection.json`|25861|`4ce0ccce8e21312265d666cfe600e65e456955c5080c2a7cdfdb02946568dcac`|
|`.local/dl-p12/acceptance/before-runtime-review.json`|1707|`f390ce4deb5919b1efc93763fe8955b68806741de4dbffb38decf97f8627f078`|
|`.local/dl-p12/acceptance/before-source-pure-raw.json`|1372|`fb86f90a0586217a3538592d15dca81500a4a04a469392a779728f42ddf067bc`|
|`.local/dl-p12/acceptance/before-window-protection-independent.json`|2672|`a1a9457657aa65b3b639d6bc3bf5c41fcd0e471397462e035696d931da7925cb`|
|`.local/dl-p12/acceptance/final-complete-native-connection.json`|25873|`a3547311e64cb80428a494233640ae81242f53ea3bf09244c475e326e574e14e`|
|`.local/dl-p12/acceptance/final-complete-protection-independent.json`|33276|`4a38c2999f96af9b45548f29570f0d01d15d4ac7037e2a080cf2618ec7e39f63`|
|`.local/dl-p12/acceptance/final-component-additional-layers-independent.json`|22969|`70e369be21d833f8f89022b708c728e7c7a1ce05614ffdbe45e2128dbf4726b1`|
|`.local/dl-p12/acceptance/final-component-sublayers-independent.json`|51171|`c928dcafb650ab466f1cb82bf602c25e4c3a768f795304f3b868449a7913694d`|
|`.local/dl-p12/acceptance/final-quiescence-independent.json`|23000|`c148f336f2b0edeaa5e9ea3404f992c375c3d15de20e93a02afec57556290c3e`|
|`.local/dl-p12/acceptance/finding-P12-A01-closed-qualified.json`|7090|`51f61cff70494f3fee217a019470af3b7447089bcdbb08399d146b1339935579`|
|`.local/dl-p12/acceptance/finding-P12-A01-open.json`|7182|`4ffb72a901c35abe90219c79679286f55fb30df116c86bb6fca58b8b69ab8577`|
|`.local/dl-p12/acceptance/finding-P12-A02-closed-qualified.json`|1665|`45cfa6a12a1627246178344e070e87124fa1ac88b38e557f1353afd14d36ca88`|
|`.local/dl-p12/acceptance/finding-P12-A02-open.json`|2457|`27207ed844599b55c996ad12ad45fc8b3a57f36aed250c3a042bee6c86fae32f`|
|`.local/dl-p12/acceptance/finding-P12-A03-closed-qualified.json`|9687|`ea03048ead5422a6f80a9e7a3bb673c55c27513e7f62724d8ccefc277c6741a5`|
|`.local/dl-p12/acceptance/finding-P12-A03-open.json`|97218|`e70998ac50414de754976a07fa4dfe6eb270b4f7b9ac29df30859adcdb28dc8a`|
|`.local/dl-p12/acceptance/finding-P12-A03-timing-clarification.json`|1011|`d8bb9a3ef0891aecf30cd2ea0b7c7dfbd23c63b535a23e24da13f0db50a883ec`|
|`.local/dl-p12/acceptance/finding-P12-A04-confirmed-unresolved.json`|8264|`8ed0e3040679b5dbaab1b4b6fa7c0d1dec92fad3b244283cfb8f08079ce1c89d`|
|`.local/dl-p12/acceptance/finding-P12-A04-open.json`|3575|`64c8c9a69c0026453b304dc6ee04bbd39938c976a477c69e1f74f2b20e4e77a1`|
|`.local/dl-p12/acceptance/github-before-index.json`|7781|`03353e9eaf69cb1bf1744cd090d93bfad7d5dd15e4bcf0034939a8b144ef9f8c`|
|`.local/dl-p12/acceptance/os-pre-window.json`|386|`56592157e273f8732dcc62d3a7f4076bbee52b5094838819b038be5781107b06`|
|`.local/dl-p12/acceptance/prewindow-interim-independent.json`|4933|`5739f4185e8d01525b3706f84b233531e6f0b08d544aa354a0f7ce2b1d3c34ce`|
|`.local/dl-p12/acceptance/product1-load-independent.json`|66001|`87ba183979a296d1b25858072f4c66cf74278d006aa911e1b85d7ca23c99d216`|
|`.local/dl-p12/acceptance/product1-loaded-pager-independent.json`|1095|`a404dfd53c037fe75732f460b7a5d63e5ba48c0dd13e06fc9d2b3985507d6838`|
|`.local/dl-p12/acceptance/product1-real-layout-independent.json`|20528|`89a2b74436b723e82e1b8013826648e6d398eb6a3871f7795db9e03ec5e9a88e`|
|`.local/dl-p12/acceptance/product1-runtime-review.json`|1708|`64e0cdfa88344a1c1a5af17d8da3fb486e246e2ad5dab40e60975f00dda8aafa`|
|`.local/dl-p12/acceptance/product1-source-independent.json`|3166|`9034de887adbc14be8e19cf6971ac99fcf6f4eca35db5c75cf4ffc9ead07e84f`|
|`.local/dl-p12/acceptance/product1-source-pure-raw.json`|2525|`5cb0304c9edd033d2bc13ea71984b7860e646be23bd213084f7560418e8b6f91`|
|`.local/dl-p12/acceptance/product2-exact-reuse-independent.json`|2064|`12d967a5c78df43d9f9f5df54bb1baea5cfa542145a2f989f20cf1c2e46570fa`|
|`.local/dl-p12/acceptance/product2-real-layout-independent.json`|20528|`838c6e2baeff3915028aff2da5738cc973be956741642e1f6adafdb106db31a5`|
|`.local/dl-p12/acceptance/product2-runtime-review.json`|1709|`33b9528cdd42aa82506513e3d0d9b76f72952c635f949ee33a6a4db487c8e4ce`|
|`.local/dl-p12/acceptance/product2-source-independent.json`|3166|`8131d512969fcfad2f7e8acc2ad8b48162acbdca3d005d4511f1c68430fb3a54`|
|`.local/dl-p12/acceptance/product3-real-layout-independent.json`|20528|`fd0a2c5b146548ac3e1598440b76f7f65c21429f21f51236d7728ef3885b3aaa`|
|`.local/dl-p12/acceptance/product3-runtime-review.json`|1709|`61863dd222f23a3f5ab1f7bd90f1e6ec214adb38a1a3ed9109146c945e25dd54`|
|`.local/dl-p12/acceptance/product3-source-independent.json`|3166|`b8c826d8d7138fb87f321a0484585bdc882d1a7eacda5eba6e4d47a5e9057d31`|
|`.local/dl-p12/acceptance/product3-spacing-owners-independent.json`|123877|`79fbae8369d9789c4a7ecf7c220bbd832ba00818aeb31dbdfed288206df9a2a7`|
|`.local/dl-p12/acceptance/product4-house-guidelines-review.json`|5880|`caa144925b550cfa618ebf6934e385c4a1650e2160007bd8193e5f5bd8c7e055`|
|`.local/dl-p12/acceptance/product4-runtime-review.json`|1709|`6dbc381c43c5507b3e24f042e44c73ab742d8cd3cd305f789f525ddee82b42e1`|
|`.local/dl-p12/acceptance/product4-source-independent.json`|3166|`87b888252f4854c63861810869575fff82016a626e4cbc1e0d1fc59d6f88d94c`|
|`.local/dl-p12/acceptance/product5-compiled-isolation-independent.json`|15548|`289273f552ba898ebe74d06321e51a6a9dad7b123f246276b1352cf4c46d6b49`|
|`.local/dl-p12/acceptance/product5-normal-asset-independent.json`|1881|`33d667d5bc29b6daf7c53c94da5a6cdf761ff8a8d68e84e22cc91c41b3b9b2de`|
|`.local/dl-p12/acceptance/product5-runtime-review.json`|1709|`423036faf4c394706b5c5d67188d72ee5bb111ec2e3147b93f12b23c7a0c4e6a`|
|`.local/dl-p12/acceptance/product5-source-independent.json`|3166|`19e91bf9384d334f720c51f6b7efd8aa8e00adbc0968439141cb3d933d9b45fa`|
|`.local/dl-p12/acceptance/remote-before-0.json`|23059|`e503713805d0c58a9efe6988fdde7dd34bfe868d99740b0163cecd77bb8097fc`|
|`.local/dl-p12/acceptance/remote-before-1.json`|8519|`24ba23f06a852e7412316aba1baa3c46a7dfc9c83748cb339de8533916863a40`|
|`.local/dl-p12/acceptance/remote-before-2.json`|9197|`468dfff725ad052e518ad7c81ccc33c99ef5afcd276a712a017a4a1f471850f1`|
|`.local/dl-p12/acceptance/remote-before-3.json`|223239|`e45ffa4945d20bda77ec22c1540d454966d06d1f774b2b2b1da5ae83b325ae3c`|
|`.local/dl-p12/acceptance/remote-before-independent.json`|1388|`8400b223bb370e82358d9e0dd04ef5b10e74654038fbea33b728a0ad3f6e0cd1`|
|`.local/dl-p12/acceptance/source-ready-v1.json`|811|`45e17ca03c83658d8d3c32b631e118eec833beb6a1502ebbbdcfeabbd784e4fb`|
|`.local/dl-p12/runtime/final-runtime-facts.json`|312302|`379a451517203852a6703a1e632376131fcd545536a1148aa2ebc94eb5ccf7f7`|
|`.local/dl-p12/testing/final-facts-v1.json`|1233594|`76e5a116be9ba6462b3b0e7749e1a06e989fb0bfe9c867f096d9ee03de579527`|
|`.local/dl-p12/testing/public-tool-integration.json`|1119|`8a5c2138e8eeae24e09a86596f0889b04e0e8ddbbb6ae1fa327c6bb5005ee84d`|
|`.local/dl-p12/runtime/loaded-pager-contract.json`|468554|`decdc45a164d5e11659109670522107a37eb695d86e506a1f9def4359ffdce70`|
|`.local/dl-p12/verification/upgrade-before-baseline.json`|37709295|`e5fb4f17e3dc529343806ec19fa08db93cab3e2bce6eb55539ff90325f051b10`|
|`.local/dl-p12/verification/upgrade-product1-load-pre.json`|38371619|`d8690ea5780fb9b814300910c0813c3628b95c3707f8218627858a40c71f5d43`|
|`.local/dl-p12/checks/product1-load-upgrade/result.json`|4180|`1d85b0c9c215481b01a699eacab41bf0777a82c4bcd592884812aa9743157d69`|
|`.local/dl-p12/verification/upgrade-product1-load-post.json`|38371620|`548c20884fb8f7cd55c4441e4461a372792c0f64723169c5163cbca6f845398d`|
|`.local/dl-p12/verification/upgrade-final-root-baseline.json`|44731524|`ba64b9c6a5624e68e6c97db013d73c39c02a790da878c299c085ec9668f650b6`|
|`.local/dl-p12/verification/final-fullstage-protection-diff.json`|161384|`0f337c971f928b42b7688b67db9da500df2daeaf2ff8fb4173d590d3e203a7f3`|
|`.local/dl-p12/verification/final-root-reference-file-inventory.json`|21842|`8ed121408e367661074b0676b409ad4aed464469d45c5661dafb74d2bb7467e7`|
|`.local/dl-p12/viewing/S13-DL-P12-view-only-20261026-r1.zip`|9949005|`9ecdf42f3567a32bd2316f7c89e9b7f06ab4a442fb5fab5e6b08489122a7660a`|


## 重现命令与层级

- `../.venv/bin/python scripts/s13_dl_p12/source_contracts.py`：SOURCE/PURE，canonical exact/单资产/三addon/原生terms与许可冻结。发布后检查实际0，见testing/published-source-contracts.json；compile/Node syntax仅语法，不冒HTTP。
- runtime_config rebind、admission_probe、protected_snapshot collect、未实现者fresh review、bind_admission：每窗口固定candidate/scope/target/probe/checkpoint SHA；旧scope/STOP不改。
- `run_checks.py --phase upgrade --modules ydental_settlement --candidate 2df168f... --freeze ... --pre ... --label product1-load`：唯一加载实际0/ERROR0，原argv与log SHA在operation/result，之后CSS无-u。
- `browser_checks.py --run-id ... --engine chromium|webkit --stage before|after --mode ... --label ...`：每次原argv/退出/source逐process保。私有变体也逐实际源码归档；并非最终CLI重演全部。noJS trust NOT_OBSERVED、诊断/COMPONENT/partial明确分层。
- `acceptance_physical.py --candidate 0f1deb8... --checkpoint ... --checkpoint-sha256 ... --label final-complete`：未实现者另新physical/原path真实bytes，RO/RR/rollbackclosed；从初始18818审计起全阶段分类，不伪造历史时点独立连接。

原保护九区/投影、83ref→80path+三共享明细、所有原图/执行源/退出在上述完整private清单中；ZIP只90原PNG+README/有限measurements/manifest/SHA，不含程序/DB/原请求/字体/PDF。旧失败及UNKNOWN保，不把helper恢复、fixture或SYNCED冒技术全通过。最终本地总项/包核/远端ref与唯一回执旁签在后续元数据段列实际结果。


## 清单截止后的已发生独立旁签

|私有文件|bytes|SHA256|
|---|---:|---|
|`acceptance/final-component-sublayers-independent.json`|51171|`c928dcafb650ab466f1cb82bf602c25e4c3a768f795304f3b868449a7913694d`|
|`acceptance/final-component-additional-layers-independent.json`|22969|`70e369be21d833f8f89022b708c728e7c7a1ce05614ffdbe45e2128dbf4726b1`|
|`acceptance/final-viewing-package-independent.json`|46497|`2e83a4b4a9104d19e2c8dc98f7d69866c24c1205665506c10389b8a205c0e6bd`|
|`acceptance/final-complete-protection-independent.json`|33276|`4a38c2999f96af9b45548f29570f0d01d15d4ac7037e2a080cf2618ec7e39f63`|
|`acceptance/final-quiescence-independent.json`|23000|`c148f336f2b0edeaa5e9ea3404f992c375c3d15de20e93a02afec57556290c3e`|
|`acceptance/finding-P12-A04-confirmed-unresolved.json`|8264|`8ed0e3040679b5dbaab1b4b6fa7c0d1dec92fad3b244283cfb8f08079ce1c89d`|
|`acceptance/product4-house-guidelines-review.json`|5880|`caa144925b550cfa618ebf6934e385c4a1650e2160007bd8193e5f5bd8c7e055`|

另全原图/执行源平铺清单 `.local/dl-p12/testing/raw-manifest-v1.json` / 591053B / SHA256 `b88bd033624e8704b31713c211260fe0195e49342a559cebdb6df1b801f150d7`，1913项=700source+1003PNG+70×3原收据，private不进入ZIP或Public。


## 最终本地审计旁签

|私有文件|bytes|SHA256|
|---|---:|---|
|`acceptance/final-all70-fullsource-integrity-independent.json`|304057|`f4f569d646ab0fb66f52a8473d5d83fa21b96fbc243154152b8a80b5bdb365e7`|
|`acceptance/final-technical-partial.json`|9856|`3d3d982f938ff5d0fec4db8f9e5a4fa6ca7a2e9a159ba8d7e4c18243ec4bbf88`|
|`acceptance/final-public-delivery-review-independent.json`|15315|`a5399dfd5ddd15426c04c476d38a473ee1e9b8b4a5503f4ff90c676fd66a530c`|
