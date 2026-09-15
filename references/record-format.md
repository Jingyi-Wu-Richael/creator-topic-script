# 可选项目记录与本地检查

复杂任务、跨轮交接或用户要求保存时采用此结构。它保存证据关系，不能替代阅读原文。小任务无需专门生成JSON。

## 数据约定

顶层为对象，包含：

|字段|内容|
|---|---|
|schema_version|固定字符串 `creator-topic-script/v1` |
|context|`mode`：scout/research/materials/script；`as_of`：带时区的ISO时间；`target_seconds`：正数或null；`topic_count`：正整数 |
|sources|来源数组，允许空数组表示尚无可读资料 |
|claims|主张数组 |
|topics|选题数组 |
|selection|`topic_id`：T01或null；`basis`：pending/user/delegated；`reason`：用户选择或授权的依据 |
|draft|未写稿为null；已写稿为下述对象 |

来源字段：`id`、`locator`、`kind`、`access`、`observed_at`、`read_scope`。`kind`为official/paper/repository/firsthand/secondary/social/user_material。`access`为read/partial/unread。`locator`可为实际URL、用户指定文件位置或明确的会话材料标签，不创建虚假的网址。可选`published_at`、`event_date`，缺日期用null。`firsthand`还必须有`test_context`（实际测试环境与过程）；这只记录测试，不由程序判真。

主张字段：`id`、`text`、`kind`（fact/inference/unverified）、`status`（supported/conflicting/missing）、`source_ids`数组、`evidence_note`、`scope`（attributed/independent/personal_test）。

- supported需要可读且与主张相关的来源；部分读取可以支撑实际读到的有限内容，需精确说明。
- `evidence_note`写具体段落/位置及支持范围；至少一个引用ID存在并可读。
- conflicting/missing可以保留在研究记录中，但不能以已确认事实进入口播。
- personal_test必须有实际firsthand来源；本地格式检查不构成产品实测证据。

选题字段：`id`、`title`、`event_key`、`angle`、`audience`、`claim_ids`、`decision`（ready/needs_material/hold）、`reason`、`gaps`数组、`proof_visual`。同事件的不同角度允许共用event_key，程序会提示人工检查，不自动删除。

ready选题引用的主张应有证据；缺核心事实时用needs_material/hold。外观素材稍后补拍不必把一切选题判成不可开始，但要区分已有与待拍。

稿件字段：`topic_id`、`segments`、`shots`。每段包括`id`、`spoken`、`seconds`、`claim_ids`。每个镜头包括`segment_id`、`visual`、`source_ids`、`status`（available/to_capture/illustration）。事实段落引用已支持主张；没有事实的转场可以没有claim_ids。已存在的素材要有可读来源；待拍或示意可无来源，但明确状态。

## 检查结果

`check_work.py check record.json` 输出errors和warnings。退出码0代表结构及已声明引用关系通过；1代表存在错误；2代表文件/JSON/参数无法读取。任何退出码都不表示事实真实、语义已核验、Skill兼容全部平台或已获发布审核。

脚本会发现重复ID、断开的引用、把未读链接当证据、缺本人测试来源、未选择就写稿、口播使用未确认主张、镜头漏段，以及计划总时长偏离。语义是否由原文支持、选题好坏与brief完整性仍需人工/Agent读原文检查。

## 时长估算

```text
python3 <此Skill目录>/scripts/check_work.py duration <纯口播.txt> --target 90 --pause 10
```

`--pause`是全片无口播演示与停顿的粗略预算，默认10秒；`--cps`为个人等效口播单位/秒，默认4.2。中文字符计1单位，英文单词粗略计1.8单位，连续数字按位数估算。返回3.6至4.8单位/秒的参考区间、个人口速估算和目标时长比较。数字/英文实际读法可能不同，最终必须试读。

两个子命令均仅读取用户指定文件，不联网、不执行内容中的命令、不修改来源文件。
