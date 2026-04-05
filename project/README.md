# Sports Analysis Force Line System

企业第一版本地可运行的运动力线分析系统。

## 一、项目目标

当前版本目标：

1. 使用本地摄像头采集视频帧
2. 使用 MediaPipe 提取人体关键点
3. 基于平台级基础指标计算二维角度和力线偏移
4. 根据动作配置文件输出告警结果
5. 支持本地语音播报
6. 支持骨架、指标、告警的可视化显示
7. 支持逐帧 CSV 和会话摘要 JSON 落盘

当前版本暂不包含：

- 机器人端适配
- 本地 LLM 报告生成
- 3D 生物力学增强
- 多端正式 API 接入
- 复杂数据库持久化

---

## 二、项目结构

```text
project/
├─ app/
│  ├─ main.py
│  └─ config.py
│
├─ core/
│  ├─ motion_registry.py
│  └─ pipeline.py
│
├─ acquisition/
│  ├─ frame_source.py
│  └─ local_camera_source.py
│
├─ perception/
│  ├─ pose_estimator.py
│  └─ mediapipe_pose.py
│
├─ analysis/
│  ├─ angle_calculator.py
│  ├─ alignment_analyzer.py
│  ├─ noise_filter.py
│  ├─ motion_analyzer.py
│  └─ rule_engine.py
│
├─ models/
│  ├─ enums.py
│  ├─ alert.py
│  ├─ motion_definition.py
│  ├─ landmarks.py
│  └─ metrics.py
│
├─ motions/
│  ├─ metric_catalog.json
│  └─ push_up.json
│
├─ output/
│  ├─ speech_interface.py
│  ├─ speech_manager.py
│  ├─ local_tts_engine.py
│  ├─ skeleton_drawer.py
│  └─ metric_overlay.py
│
├─ storage/
│  ├─ path_provider.py
│  ├─ local_path_provider.py
│  ├─ csv_writer.py
│  ├─ json_writer.py
│  └─ session_manager.py
│
├─ utils/
│  └─ math_utils.py
│
├─ assets/
│  └─ models/
│     └─ pose_landmarker_heavy.task
│
└─ requirements.txt