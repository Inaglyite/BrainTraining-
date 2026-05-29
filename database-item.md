# 手势识别小游戏数据库字段设计

下面这份表适合记录“**一个用户在一个小游戏中的一次交互**”。
它可以同时支持后续的 IRT / DKT 分析、难度自适应，以及在线回放测试。

## 1. 建议的核心字段

| 字段名 | 类型建议 | 是否必填 | 说明 | 示例 |
|---|---|---:|---|---|
| `user_id` | BIGINT / VARCHAR | 是 | 用户唯一标识，建议匿名化存储 | `1001` |
| `game_type` | VARCHAR(32) | 是 | 游戏类型：`算式回溯` / `数箱子` / `石头剪刀布` | `数箱子` |
| `difficulty_level` | INT / DECIMAL | 是 | 当前题目或关卡的难度等级；可用离散值或小数值 | `3` / `2.5` |
| `attempt_index` | INT | 是 | 该用户在该游戏或该会话中的第几次交互 | `12` |
| `correct` | TINYINT(1) / BOOLEAN | 是 | 本次是否完成正确，`1` 为对，`0` 为错 | `1` |
| `response_time` | FLOAT / INT | 是 | 用户完成本次任务耗时，单位建议为秒 | `4.72` |
| `consecutive_errors` | INT | 是 | 该用户当前连续错误次数 | `2` |
| `total_attempted` | INT | 是 | 该用户累计交互次数 | `58` |
| `skill_opportunities` | INT | 是 | 当前游戏类型或当前技能下的累计练习次数 | `17` |
| `time_since_last_same_game` | FLOAT / INT | 否 | 距离上一次玩同一游戏过去的时间，单位建议为秒 | `138.5` |
| `help_used` | BOOLEAN | 否 | 本次是否使用帮助 / 提示 | `false` |
| `skip_used` | BOOLEAN | 否 | 本次是否跳过 / 放弃本题 | `false` |

## 2. 字段含义说明

### 2.1 必填字段

- `user_id`：用于区分不同玩家。
- `game_type`：用于区分不同小游戏。
- `difficulty_level`：用于难度自适应控制，是 IRT / 难度策略的关键输入。
- `attempt_index`：用于恢复行为顺序，支持序列模型（如 DKT）。
- `correct`：监督学习标签，训练 IRT / DKT 的核心结果。
- `response_time`：反映反应速度，常常和能力、熟练度、疲劳程度有关。
- `consecutive_errors`：反映用户当前是否卡住，适合做动态调难度。
- `total_attempted`：反映用户总体练习量。
- `skill_opportunities`：反映用户在当前游戏/技能上的局部练习量。

### 2.2 可选字段

- `time_since_last_same_game`：如果用户第一次玩该游戏，没有上一次记录时可为空。
- `help_used`：如果你的小游戏没有提示功能，可以先不存。
- `skip_used`：如果你的小游戏没有跳过功能，也可以不存。

## 3. 推荐数据样例

| user_id | game_type | difficulty_level | attempt_index | correct | response_time | consecutive_errors | total_attempted | skill_opportunities | time_since_last_same_game | help_used | skip_used |
|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|---|---|
| 1001 | 数箱子 | 3 | 0 | 1 | 4.8 | 0 | 1 | 1 |  | false | false |
| 1001 | 数箱子 | 4 | 1 | 0 | 7.2 | 1 | 2 | 2 | 35.6 | true | false |
| 1001 | 算式回溯 | 2.5 | 2 | 1 | 5.1 | 0 | 3 | 1 | 120.0 | false | false |

## 4. 为什么这些字段适合做 IRT / DKT

- **IRT** 主要依赖 `user_id`、`game_type`、`difficulty_level`、`correct` 来估计用户能力和题目难度。
- **DKT** 需要 `attempt_index`、`response_time`、`consecutive_errors`、`skill_opportunities` 这类时序信息来预测下一次表现。
- `help_used`、`skip_used` 可以帮助判断用户是否真实掌握，也能辅助识别“卡住但硬撑”或“直接跳过”的情况。

## 5. 索引建议

为了支持查询、训练和回放，建议至少建立以下索引：

1. `INDEX(user_id)`
2. `INDEX(game_type)`
3. `INDEX(user_id, attempt_index)`
4. `INDEX(user_id, game_type)`
5. `INDEX(game_type, difficulty_level)`

如果你后续会做在线自适应推荐，`(user_id, game_type, attempt_index)` 也很有价值。

## 6. 设计建议

- `difficulty_level` 建议先统一成一个数值字段，后面再决定是整数等级还是带小数的连续值。
- `time_since_last_same_game` 建议统一用秒，便于计算和模型输入。
- 如果未来想做更细的分析，可以再加这些扩展字段：
  - `session_id`
  - `start_time`
  - `end_time`
  - `hint_count`
  - `gesture_accuracy`
  - `reaction_speed_level`

## 7. 推荐的最小可落地版本

如果你想先做一个最小可用数据库，建议先只存这 8 个字段：

- `user_id`
- `game_type`
- `difficulty_level`
- `attempt_index`
- `correct`
- `response_time`
- `consecutive_errors`
- `total_attempted`

等这个版本稳定后，再逐步补充 `skill_opportunities`、`time_since_last_same_game`、`help_used`、`skip_used`。


