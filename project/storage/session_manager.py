# storage/session_manager.py

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

from models.alert import Alert
from models.motion_definition import MotionDefinition


@dataclass(slots=True)
class SessionManager:
    """
    会话管理器。

    设计定位：
    - 管理一次本地分析会话的基本信息
    - 生成会话目录和输出文件路径
    - 统计帧数和告警信息
    - 在会话结束时生成 summary 数据

    说明：
    - 一次会话默认对应一个动作
    - output_root 由外部决定，SessionManager 不负责路径策略
    """

    output_root: str | Path
    motion_definition: MotionDefinition

    session_id: str = field(init=False)
    session_dir: Path = field(init=False)
    start_time: datetime = field(init=False)
    end_time: datetime | None = field(default=None, init=False)

    total_frames: int = field(default=0, init=False)
    detected_frames: int = field(default=0, init=False)

    _alert_counter: Counter = field(default_factory=Counter, init=False)

    def __post_init__(self) -> None:
        self.output_root = Path(self.output_root)
        self.start_time = datetime.now()
        self.session_id = self.start_time.strftime("%Y%m%d_%H%M%S")

        self.session_dir = (
            self.output_root
            / self.motion_definition.motion_id
            / self.session_id
        )
        self.session_dir.mkdir(parents=True, exist_ok=True)

    def register_frame(self, pose_detected: bool, alerts: list[Alert]) -> None:
        """
        注册一帧结果，用于统计。
        """
        self.total_frames += 1

        if pose_detected:
            self.detected_frames += 1

        for alert in alerts:
            self._alert_counter[(alert.code, alert.level.value)] += 1

    def close(self) -> None:
        """
        结束会话。
        """
        self.end_time = datetime.now()

    def get_csv_path(self) -> Path:
        """
        返回当前会话 CSV 输出路径。
        """
        return self.session_dir / "frame_metrics.csv"

    def get_summary_json_path(self) -> Path:
        """
        返回当前会话 JSON 摘要输出路径。
        """
        return self.session_dir / "session_summary.json"

    def build_summary(self) -> dict:
        """
        构建当前会话摘要数据。
        """
        alert_summary = []

        for (code, level), count in sorted(self._alert_counter.items()):
            alert_summary.append(
                {
                    "code": code,
                    "level": level,
                    "count": count,
                }
            )

        return {
            "session_id": self.session_id,
            "motion_id": self.motion_definition.motion_id,
            "motion_name": self.motion_definition.motion_name,
            "motion_version": self.motion_definition.version,
            "start_time": self.start_time.isoformat(),
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "total_frames": self.total_frames,
            "detected_frames": self.detected_frames,
            "detection_ratio": (
                self.detected_frames / self.total_frames if self.total_frames > 0 else 0.0
            ),
            "enabled_metrics": self.motion_definition.enabled_metrics,
            "alert_summary": alert_summary,
            "csv_path": str(self.get_csv_path()),
            "summary_json_path": str(self.get_summary_json_path()),
        }