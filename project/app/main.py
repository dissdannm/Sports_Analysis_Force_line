from __future__ import annotations

import cv2

from acquisition.local_camera_source import LocalCameraSource
from analysis.alignment_analyzer import AlignmentAnalyzer
from analysis.angle_calculator import AngleCalculator
from analysis.motion_analyzer import MotionAnalyzer
from analysis.noise_filter import NoiseFilter
from analysis.rule_engine import RuleEngine
from analysis.temporal_analyzer import TemporalAnalyzer
from app.config import AppConfig
from core.motion_registry import MotionRegistry
from core.pipeline import Pipeline
from output.local_tts_engine import LocalTTSEngine
from output.metric_overlay import MetricOverlay
from output.skeleton_drawer import SkeletonDrawer
from output.speech_manager import SpeechManager
from perception.mediapipe_pose import MediaPipePoseEstimator
from storage.csv_writer import CSVWriter
from storage.json_writer import JSONWriter
from storage.local_path_provider import LocalPathProvider
from storage.session_manager import SessionManager


def resolve_motion_id(
    motion_registry: MotionRegistry,
    default_motion_id: str,
    preferred_motion_id: str | None = None,
    interactive: bool = True,
) -> str:
    """
    统一解析当前应使用的 motion_id。

    优先级：
    1. preferred_motion_id
    2. 本地交互输入
    3. default_motion_id
    """
    available_motion_ids = motion_registry.list_motion_ids()

    if not available_motion_ids:
        raise RuntimeError("当前未加载到任何动作配置")

    if preferred_motion_id is not None:
        preferred_motion_id = preferred_motion_id.strip()
        if preferred_motion_id not in available_motion_ids:
            raise ValueError(
                f"传入的 preferred_motion_id 不合法: {preferred_motion_id}，"
                f"可选动作: {available_motion_ids}"
            )
        return preferred_motion_id

    if not interactive:
        if default_motion_id not in available_motion_ids:
            raise ValueError(
                f"default_motion_id 不合法: {default_motion_id}，"
                f"可选动作: {available_motion_ids}"
            )
        return default_motion_id

    print("\n可选动作列表：")
    for index, motion_id in enumerate(available_motion_ids, start=1):
        motion = motion_registry.get_motion(motion_id)
        print(f"{index}. {motion.motion_id} ({motion.motion_name})")

    print(f"\n请输入动作编号或 motion_id，直接回车将使用默认动作：{default_motion_id}")
    user_input = input("动作选择：").strip()

    if user_input == "":
        if default_motion_id not in available_motion_ids:
            raise ValueError(
                f"default_motion_id 不合法: {default_motion_id}，"
                f"可选动作: {available_motion_ids}"
            )
        return default_motion_id

    if user_input.isdigit():
        selected_index = int(user_input)
        if 1 <= selected_index <= len(available_motion_ids):
            return available_motion_ids[selected_index - 1]

        raise ValueError(
            f"输入的动作编号超出范围: {selected_index}，"
            f"可选范围为 1 ~ {len(available_motion_ids)}"
        )

    if user_input in available_motion_ids:
        return user_input

    raise ValueError(
        f"输入的 motion_id 不存在: {user_input}，"
        f"可选动作: {available_motion_ids}"
    )


def main(
    preferred_motion_id: str | None = None,
    interactive_select: bool = True,
) -> None:
    """
    本地调试模式程序入口。
    """
    config = AppConfig()
    config.validate()

    frame_source = LocalCameraSource(
        camera_index=config.camera_index,
        width=config.camera_width,
        height=config.camera_height,
    )

    pose_estimator = MediaPipePoseEstimator(
        model_path=config.pose_model_path,
        num_poses=config.pose_num_poses,
        min_pose_detection_confidence=config.min_pose_detection_confidence,
        min_pose_presence_confidence=config.min_pose_presence_confidence,
        min_tracking_confidence=config.min_tracking_confidence,
    )

    motion_registry = MotionRegistry(config.motions_dir)
    motion_registry.load_all()

    motion_id = resolve_motion_id(
        motion_registry=motion_registry,
        default_motion_id=config.default_motion_id,
        preferred_motion_id=preferred_motion_id,
        interactive=interactive_select,
    )

    selected_motion = motion_registry.get_motion(motion_id)
    print(
        f"\n当前动作：{selected_motion.motion_id} ({selected_motion.motion_name}) | "
        f"版本：{selected_motion.version}"
    )

    angle_calculator = AngleCalculator()
    alignment_analyzer = AlignmentAnalyzer()
    temporal_analyzer = TemporalAnalyzer()

    motion_analyzer = MotionAnalyzer(
        angle_calculator=angle_calculator,
        alignment_analyzer=alignment_analyzer,
        temporal_analyzer=temporal_analyzer,
    )

    noise_filter = NoiseFilter(window_size=config.noise_filter_window_size)
    rule_engine = RuleEngine()

    speech_engine = None
    if config.speech_enabled:
        speech_engine = LocalTTSEngine(
            rate=config.speech_rate,
            volume=config.speech_volume,
            use_background_thread=config.speech_use_background_thread,
        )

    speech_manager = SpeechManager(speech_engine=speech_engine)

    skeleton_drawer = SkeletonDrawer()
    metric_overlay = MetricOverlay()

    pipeline = Pipeline(
        pose_estimator=pose_estimator,
        motion_registry=motion_registry,
        motion_analyzer=motion_analyzer,
        noise_filter=noise_filter,
        rule_engine=rule_engine,
        speech_manager=speech_manager,
        skeleton_drawer=skeleton_drawer,
        metric_overlay=metric_overlay,
        motion_id=motion_id,
        show_skeleton=config.show_skeleton,
        show_angles=config.show_angles,
        show_alignment=config.show_alignment,
        show_alerts=config.show_alerts,
    )

    path_provider = LocalPathProvider(base_dir=config.output_dir)
    output_root = path_provider.get_output_root()

    session_manager = SessionManager(
        output_root=output_root,
        motion_definition=pipeline.motion_definition,
    )

    csv_writer = CSVWriter(
        file_path=session_manager.get_csv_path(),
        motion_id=pipeline.motion_definition.motion_id,
        enabled_metrics=pipeline.motion_definition.enabled_metrics,
    )
    csv_writer.open()

    json_writer = JSONWriter(session_manager.get_summary_json_path())

    frame_source.open()
    frame_index = 0

    try:
        while True:
            success, frame = frame_source.read()
            if not success:
                print("读取摄像头画面失败，程序结束。")
                break

            timestamp_ms = frame_index * 33
            result = pipeline.process_frame(frame, timestamp_ms)

            session_manager.register_frame(
                pose_detected=result.pose_detected,
                alerts=result.alerts,
            )

            csv_writer.write_row(
                frame_index=frame_index,
                timestamp_ms=timestamp_ms,
                pose_detected=result.pose_detected,
                motion_metrics=result.motion_metrics,
            )

            cv2.imshow(config.window_name, result.frame)

            frame_index += 1

            key = cv2.waitKey(1) & 0xFF
            if key == 27:  # ESC
                print("检测到 ESC，程序退出。")
                break

    finally:
        session_manager.close()
        summary_data = session_manager.build_summary()
        json_writer.write(summary_data)

        csv_writer.close()
        frame_source.close()
        pose_estimator.close()
        cv2.destroyAllWindows()


if __name__ == "__main__":
    main()