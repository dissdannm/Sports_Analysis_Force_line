# README.md

## 项目名称

体测动作二维力线分析系统（企业第一版）

## 项目目标

本项目用于基于 MediaPipe 姿态关键点，对体测/运动动作进行二维结构化分析，输出角度、力线、时序指标、语音反馈与会话结果文件。

当前重点支持：

* 俯卧撑（push_up）
* 仰卧起坐（sit_up）
* 臀桥（bridge）

## 当前能力范围

### 已完成

* 本地摄像头采集
* MediaPipe 姿态关键点识别
* 平台级角度指标计算
* 平台级力线/偏移指标计算
* 动作 JSON 配置驱动
* 规则引擎告警输出
* 本地语音播报
* 时序分析器骨架
* sit_up / bridge 的部分 temporal 指标
* CSV / JSON 会话结果保存

### 当前正式支持的指标类型

* angle
* offset
* temporal

### 当前正式支持的新增 temporal / 扩展指标

* trunk_ground_angle
* knee_angle_variation
* rep_cycle_duration
* ascent_duration
* peak_hold_duration
* descent_duration
* hip_angular_velocity

## 运行方式

在项目根目录运行：

```bash
python -m app.main
```

## 目录角色说明

* `app/`：程序入口与配置
* `analysis/`：平台级指标、时序指标、规则分析
* `core/`：动作注册与单帧流水线
* `models/`：统一数据结构
* `motions/`：动作配置文件与指标目录表
* `output/`：语音、骨架绘制、画面叠加
* `storage/`：本地输出与会话保存
* `perception/`：视觉姿态估计
* `acquisition/`：视频采集

## 当前约束

* 当前为二维版本
* 不保存视频作为长期数据资产
* 正式采集建议优先保留结构化关键点 / 指标 / 动作事件数据
* `motion_phase` 和 `rep_counter` 当前属于状态输出变量，不作为规则型指标写入 `enabled_metrics`

## 下一阶段重点

* sit_up：`neck_flexion_angle`、`lumbar_gap_distance`、`quality_score`
* bridge：`trajectory_consistency`、`ahp_quality_score`
* 采集数据协议与数据集规范
* 移动端采集方案

---

# PROJECT_STRUCTURE.md

## 项目目录结构

```text
project/
├─ app/
│  ├─ __init__.py
│  ├─ config.py
│  └─ main.py
├─ acquisition/
│  ├─ __init__.py
│  └─ local_camera_source.py
├─ perception/
│  ├─ __init__.py
│  ├─ pose_estimator.py
│  └─ mediapipe_pose.py
├─ analysis/
│  ├─ __init__.py
│  ├─ angle_calculator.py
│  ├─ alignment_analyzer.py
│  ├─ temporal_analyzer.py
│  ├─ motion_analyzer.py
│  ├─ noise_filter.py
│  └─ rule_engine.py
├─ core/
│  ├─ __init__.py
│  ├─ motion_registry.py
│  └─ pipeline.py
├─ models/
│  ├─ __init__.py
│  ├─ alert.py
│  ├─ enums.py
│  ├─ landmarks.py
│  ├─ metrics.py
│  └─ motion_definition.py
├─ output/
│  ├─ __init__.py
│  ├─ speech_interface.py
│  ├─ local_tts_engine.py
│  ├─ speech_manager.py
│  ├─ skeleton_drawer.py
│  └─ metric_overlay.py
├─ storage/
│  ├─ __init__.py
│  ├─ csv_writer.py
│  ├─ json_writer.py
│  ├─ local_path_provider.py
│  └─ session_manager.py
├─ motions/
│  ├─ metric_catalog.json
│  ├─ push_up.json
│  ├─ sit_up.json
│  └─ bridge.json
└─ assets/
   └─ models/
      └─ pose_landmarker_heavy.task
```

## 关键模块职责

### 1. `angle_calculator.py`

平台级基础角度指标能力库。
负责：

* 左右肘角
* 左右肩角
* 左右髋角
* 左右膝角
* 左右踝角

### 2. `alignment_analyzer.py`

平台级基础力线 / 偏移能力库。
负责：

* trunk_tilt
* pelvis_tilt
* neck_forward_offset
* center_offset
* knee_offset_left
* knee_offset_right
* body_line_angle
* trunk_ground_angle

### 3. `temporal_analyzer.py`

平台级时序变量分析器。
当前负责：

* sit_up：knee_angle_variation、rep_cycle_duration、内部计次/阶段状态
* bridge：ascent_duration、peak_hold_duration、descent_duration、hip_angular_velocity

### 4. `motion_analyzer.py`

把 angle / alignment / temporal 三层指标合并成统一动作级指标结果。

### 5. `rule_engine.py`

根据动作 JSON 的规则区间和提示语，生成统一告警对象。

### 6. `motion_registry.py`

扫描 `motions/` 目录，读取 `metric_catalog.json` 与动作 JSON，并做动作配置校验。

## 当前设计原则

### 平台能力层

尽量少改，由程序员维护：

* angle_calculator.py
* alignment_analyzer.py
* temporal_analyzer.py
* motion_registry.py
* metric_catalog.json

### 动作配置层

高频维护入口：

* motions/push_up.json
* motions/sit_up.json
* motions/bridge.json

### 规则层

由动作 JSON 中的阈值、提示语与 timing 参数表达。

---

# MOTION_JSON_GUIDE.md

## 目标

本文件用于说明：

1. 运康/业务同学如何填写动作 JSON
2. 维护者在新增动作时如何判断要改 JSON 还是改 Python

## 一条总原则

### 先问两个问题

1. 这次是在改平台能力，还是改动作规则？
2. 这个新需求是旧指标重新组合，还是需要新增全新数学指标？

结论：

* 旧指标重新组合 → 改 JSON
* 新数学/时序指标 → 改 Python + catalog，再回到 JSON

## 动作 JSON 标准结构

每个动作文件建议固定包含以下部分：

* `motion_id`
* `motion_name`
* `version`
* `description`
* `landmarks_required`
* `enabled_metrics`
* `metric_rules`
* `voice_prompts`
* `timing`
* `tags`
* `extras`

## 各字段说明

### `enabled_metrics`

当前动作真正启用、并进入规则引擎判断的指标。
注意：

* 这里只放“规则型指标”
* `motion_phase`、`rep_counter` 这类状态输出变量当前不要放进来

### `metric_rules`

每个启用指标的阈值规则。
包括：

* `normal_range`
* `severity_rules`

### `voice_prompts`

每个启用指标对应的 mild / moderate / severe 语音提示语。

### `timing`

当前动作的时序参数：

* `stable_frames`
* `voice_cooldown_ms`
* `min_hold_ms`

### `extras`

暂未正式进入平台能力、但已明确属于后续规划的指标/说明。
例如：

* `neck_flexion_angle`
* `lumbar_gap_distance`
* `quality_score`
* `trajectory_consistency`
* `ahp_quality_score`

## 新增动作维护流程

### 情况 A：平台已支持所有所需指标

步骤：

1. 编写新的 `motions/xxx.json`
2. 放入 `motions/`
3. 重启程序
4. 选择该动作测试

### 情况 B：动作依赖新指标

步骤：

1. 在 `motions/metric_catalog.json` 注册新指标
2. 在对应分析器实现：

   * 角度类 → `angle_calculator.py`
   * 力线类 → `alignment_analyzer.py`
   * 时序类 → `temporal_analyzer.py`
3. 修改 `motion_analyzer.py` 统一输出
4. 再把指标接入动作 JSON

## 当前动作说明

### push_up

当前重点看：整体力线、头颈、骨盆、肘部（按当前项目版本）

### sit_up

当前正式支持：

* left_knee
* right_knee
* trunk_ground_angle
* knee_angle_variation
* rep_cycle_duration

### bridge

当前正式支持：

* left_hip
* right_hip
* pelvis_tilt
* ascent_duration
* peak_hold_duration
* descent_duration
* hip_angular_velocity

---

# NEXT_STEPS.md

## 当前版本定位

这是一个“可继续开发的稳定基线版本”，不是最终完整版。

## 已完成

* 统一项目主链路
* 动作配置驱动
* catalog 更新
* sit_up 的基础标准化重构
* bridge 的 temporal 骨架接入
* main.py 收口为正常版本

## 下一阶段任务清单

### A. sit_up 剩余 extra 转正

1. `neck_flexion_angle`
2. `lumbar_gap_distance`
3. `quality_score`

### B. bridge 剩余 extra 转正

1. `trajectory_consistency`
2. `ahp_quality_score`

### C. 指标分层优化

当前问题：

* `enabled_metrics` 主要服务规则引擎
* `motion_phase` / `rep_counter` 属于状态输出变量

下一步建议：

* 新增 `output_metrics` 概念
* 将规则型指标与输出型指标分层

### D. 数据采集体系

需尽快落地：

* `session_meta.json`
* `frame_landmarks.jsonl`
* `frame_metrics.csv`
* `rep_events.csv`
* `summary.json`

### E. 采集端 / 分析端分工

建议：

* 手机端：正式采集端
* Windows：开发调试 + 数据分析端

### F. 文档与 Git 规范

建议保持：

* 每完成一个小功能即 commit
* 重要版本打 tag
* 文档同步更新

## 下一轮最优先建议

1. 完成 sit_up 剩余三个变量
2. 设计 dataset schema v1
3. 规划比赛数据采集方案
