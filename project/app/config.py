# app/config.py

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from models.enums import RuntimeMode


PROJECT_ROOT = Path(__file__).resolve().parent.parent
MOTIONS_DIR = PROJECT_ROOT / "motions"
MODEL_DIR = PROJECT_ROOT / "assets" / "models"


@dataclass(slots=True)
class AppConfig:
    """
    应用配置对象。

    设计目标：
    1. 统一管理运行参数
    2. 避免路径和阈值散落在代码各处
    3. 便于后续切换本地模式 / 服务模式
    4. 提高企业第一版的可维护性
    """

    # 运行模式
    runtime_mode: RuntimeMode = RuntimeMode.LOCAL_DEBUG

    # 输入源配置
    camera_index: int = 0
    camera_width: int | None = 1280
    camera_height: int | None = 720

    # MediaPipe 配置
    pose_model_path: str = str(MODEL_DIR / "pose_landmarker_heavy.task")
    pose_num_poses: int = 1
    min_pose_detection_confidence: float = 0.5
    min_pose_presence_confidence: float = 0.5
    min_tracking_confidence: float = 0.5

    # 动作配置
    motions_dir: str = str(MOTIONS_DIR)
    default_motion_id: str = "push_up"

    # 滤波配置
    noise_filter_window_size: int = 5

    # 语音配置
    speech_enabled: bool = True
    speech_rate: int = 180
    speech_volume: float = 1.0
    speech_use_background_thread: bool = False

    # 可视化配置
    window_name: str = "Motion Analysis System"
    show_skeleton: bool = True
    show_angles: bool = True
    show_alignment: bool = True
    show_alerts: bool = True

    # 存储配置
    # None 表示交给 LocalPathProvider 使用默认用户目录
    output_dir: str | None = None

    def validate(self) -> None:
        """
        对配置做基础校验。

        说明：
        - 第一版只做必要校验，不做过度复杂检查
        - 在程序启动初期尽早发现明显配置错误
        """
        model_path = Path(self.pose_model_path)
        motions_path = Path(self.motions_dir)

        if not model_path.exists():
            raise FileNotFoundError(f"未找到 MediaPipe 模型文件: {model_path}")

        if not motions_path.exists():
            raise FileNotFoundError(f"未找到 motions 配置目录: {motions_path}")

        if self.output_dir is not None:
            Path(self.output_dir).mkdir(parents=True, exist_ok=True)

        if self.noise_filter_window_size <= 0:
            raise ValueError("noise_filter_window_size 必须大于 0")

        if not (0.0 <= self.speech_volume <= 1.0):
            raise ValueError("speech_volume 必须在 0.0 到 1.0 之间")