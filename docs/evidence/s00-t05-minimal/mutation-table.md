# Every Project mutation and immediate full readback

|#|UTC|Mutation|Target/value|Exit|Readback|Expected-only change|
|---|---|---|---|---|---|---|
|1|2026-10-11T08:59:59.859769+00:00|archiveProjectV2Item|#1|0|[check-001.json](check-001.json)|True|
|2|2026-10-11T09:00:03.382302+00:00|archiveProjectV2Item|#2|0|[check-002.json](check-002.json)|True|
|3|2026-10-11T09:00:06.333229+00:00|archiveProjectV2Item|#3|0|[check-003.json](check-003.json)|True|
|4|2026-10-11T09:00:12.198120+00:00|archiveProjectV2Item|#4|0|[check-004.json](check-004.json)|True|
|5|2026-10-11T09:00:15.400779+00:00|archiveProjectV2Item|#5|0|[check-005.json](check-005.json)|True|
|6|2026-10-11T09:00:18.806401+00:00|archiveProjectV2Item|#6|0|[check-006.json](check-006.json)|True|
|7|2026-10-11T09:00:21.911853+00:00|archiveProjectV2Item|#7|0|[check-007.json](check-007.json)|True|
|8|2026-10-11T09:00:29.028982+00:00|archiveProjectV2Item|#8|0|[check-008.json](check-008.json)|True|
|9|2026-10-11T09:00:32.404547+00:00|archiveProjectV2Item|#9|0|[check-009.json](check-009.json)|True|
|10|2026-10-11T09:00:35.517052+00:00|archiveProjectV2Item|#10|0|[check-010.json](check-010.json)|True|
|11|2026-10-11T09:00:38.939513+00:00|archiveProjectV2Item|#11|0|[check-011.json](check-011.json)|True|
|12|2026-10-11T09:00:42.034138+00:00|archiveProjectV2Item|#12|0|[check-012.json](check-012.json)|True|
|13|2026-10-11T09:00:54.358228+00:00|archiveProjectV2Item|#13|0|[check-013.json](check-013.json)|True|
|14|2026-10-11T09:00:59.790896+00:00|archiveProjectV2Item|#14|0|[check-014.json](check-014.json)|True|
|15|2026-10-11T09:01:05.365798+00:00|archiveProjectV2Item|#15|0|[check-015.json](check-015.json)|True|
|16|2026-10-11T09:01:13.347980+00:00|archiveProjectV2Item|#16|0|[check-016.json](check-016.json)|True|
|17|2026-10-11T09:01:17.155671+00:00|archiveProjectV2Item|#17|0|[check-017.json](check-017.json)|True|
|18|2026-10-11T09:01:20.920186+00:00|archiveProjectV2Item|#18|0|[check-018.json](check-018.json)|True|
|19|2026-10-11T09:01:23.626202+00:00|archiveProjectV2Item|#19|0|[check-019.json](check-019.json)|True|
|20|2026-10-11T09:01:26.719871+00:00|archiveProjectV2Item|#20|0|[check-020.json](check-020.json)|True|
|21|2026-10-11T09:01:30.630529+00:00|archiveProjectV2Item|#21|0|[check-021.json](check-021.json)|True|
|22|2026-10-11T09:01:34.235261+00:00|archiveProjectV2Item|#22|0|[check-022.json](check-022.json)|True|
|23|2026-10-11T09:01:37.809841+00:00|createProjectV2Field|阶段|0|[check-023.json](check-023.json)|True|
|24|2026-10-11T09:01:41.573874+00:00|createProjectV2Field|执行状态|0|[check-024.json](check-024.json)|True|
|25|2026-10-11T09:01:44.817784+00:00|updateProjectV2ItemFieldValue|#23 阶段=PLAN|0|[check-025.json](check-025.json)|True|
|26|2026-10-11T09:01:49.036298+00:00|updateProjectV2ItemFieldValue|#23 执行状态=进行中|0|[check-026.json](check-026.json)|True|
|27|2026-10-11T09:01:52.354352+00:00|updateProjectV2ItemFieldValue|#24 阶段=S00|0|[check-027.json](check-027.json)|True|
|28|2026-10-11T09:01:56.448506+00:00|updateProjectV2ItemFieldValue|#24 执行状态=待复核|0|[check-028.json](check-028.json)|True|
|29|2026-10-11T09:02:06.283335+00:00|updateProjectV2ItemFieldValue|#25 阶段=S01|0|[check-029.json](check-029.json)|True|
|30|2026-10-11T09:02:10.167104+00:00|updateProjectV2ItemFieldValue|#25 执行状态=待启用|0|[check-030.json](check-030.json)|True|
|31|2026-10-11T09:02:16.031306+00:00|updateProjectV2ItemFieldValue|#26 阶段=S02|0|[check-031.json](check-031.json)|True|
|32|2026-10-11T09:02:20.651514+00:00|updateProjectV2ItemFieldValue|#26 执行状态=待启用|0|[check-032.json](check-032.json)|True|
|33|2026-10-11T09:02:24.166367+00:00|updateProjectV2ItemFieldValue|#27 阶段=S03|0|[check-033.json](check-033.json)|True|
|34|2026-10-11T09:02:27.204665+00:00|updateProjectV2ItemFieldValue|#27 执行状态=待启用|0|[check-034.json](check-034.json)|True|
|35|2026-10-11T09:02:31.214557+00:00|updateProjectV2ItemFieldValue|#28 阶段=S04|0|[check-035.json](check-035.json)|True|
|36|2026-10-11T09:02:39.707833+00:00|updateProjectV2ItemFieldValue|#28 执行状态=待启用|0|[check-036.json](check-036.json)|True|
|37|2026-10-11T09:02:45.288212+00:00|updateProjectV2ItemFieldValue|#29 阶段=S05|0|[check-037.json](check-037.json)|True|
|38|2026-10-11T09:02:49.068508+00:00|updateProjectV2ItemFieldValue|#29 执行状态=待启用|0|[check-038.json](check-038.json)|True|
|39|2026-10-11T09:02:52.488673+00:00|updateProjectV2ItemFieldValue|#30 阶段=S06|0|[check-039.json](check-039.json)|True|
|40|2026-10-11T09:02:56.124932+00:00|updateProjectV2ItemFieldValue|#30 执行状态=待启用|0|[check-040.json](check-040.json)|True|
|41|2026-10-11T09:02:59.180422+00:00|updateProjectV2ItemFieldValue|#31 阶段=S07|0|[check-041.json](check-041.json)|True|
|42|2026-10-11T09:03:02.822000+00:00|updateProjectV2ItemFieldValue|#31 执行状态=待启用|0|[check-042.json](check-042.json)|True|
|43|2026-10-11T09:03:06.463223+00:00|updateProjectV2ItemFieldValue|#32 阶段=S08|0|[check-043.json](check-043.json)|True|
|44|2026-10-11T09:03:09.908463+00:00|updateProjectV2ItemFieldValue|#32 执行状态=待启用|0|[check-044.json](check-044.json)|True|
|45|2026-10-11T09:03:13.491314+00:00|updateProjectV2ItemFieldValue|#33 阶段=S09|0|[check-045.json](check-045.json)|True|
|46|2026-10-11T09:03:16.945863+00:00|updateProjectV2ItemFieldValue|#33 执行状态=待启用|0|[check-046.json](check-046.json)|True|
|47|2026-10-11T09:03:20.552626+00:00|updateProjectV2ItemFieldValue|#34 阶段=S10|0|[check-047.json](check-047.json)|True|
|48|2026-10-11T09:03:27.670952+00:00|updateProjectV2ItemFieldValue|#34 执行状态=待启用|0|[check-048.json](check-048.json)|True|
|49|2026-10-11T09:03:32.003331+00:00|updateProjectV2ItemFieldValue|#35 阶段=S11|0|[check-049.json](check-049.json)|True|
|50|2026-10-11T09:03:35.560500+00:00|updateProjectV2ItemFieldValue|#35 执行状态=待启用|0|[check-050.json](check-050.json)|True|
|51|2026-10-11T09:03:39.929934+00:00|updateProjectV2ItemFieldValue|#36 阶段=S12|0|[check-051.json](check-051.json)|True|
|52|2026-10-11T09:03:47.444392+00:00|updateProjectV2ItemFieldValue|#36 执行状态=待启用|0|[check-052.json](check-052.json)|True|
|53|2026-10-11T09:03:51.281506+00:00|updateProjectV2ItemFieldValue|#37 阶段=S13|0|[check-053.json](check-053.json)|True|
|54|2026-10-11T09:03:54.597407+00:00|updateProjectV2ItemFieldValue|#37 执行状态=待启用|0|[check-054.json](check-054.json)|True|
|55|2026-10-11T09:03:58.111389+00:00|createProjectV2View|当前计划|0|[check-055.json](check-055.json)|True|
|56|2026-10-11T09:04:01.342332+00:00|updateProjectV2View|当前计划 / repo:Yredxin/YDental is:issue 阶段:PLAN,S00,S01,S02,S03,S04,S05,S06,S07,S08,S09,S10,S11,S12,S13|0|[check-056.json](check-056.json)|True|
