# storage/csv_writer.py

from __future__ import annotations

import csv
from pathlib import Path

from models.metrics import MotionMetrics


class CSVWriter:
    """
    每帧结果 CSV 写入器。

    设计定位：
    - 负责将单次会话中的逐帧分析结果写入 CSV
    - 一次会话通常对应一个动作，因此列结构固定
    - 不负责路径规划，不负责 session_id 生成

    使用方式：
    1. 初始化时传入 file_path 和 enabled_metrics
    2. 调用 open() 打开文件
    3. 每帧调用 write_row(...)
    4. 结束时调用 close()
    """

    def __init__(self, file_path: str | Path, motion_id: str, enabled_metrics: list[str]) -> None:
        self.file_path = Path(file_path)
        self.motion_id = motion_id
        self.enabled_metrics = enabled_metrics

        self._file = None
        self._writer = None
        self._opened = False

    def open(self) -> None:
        """
        打开 CSV 文件并写入表头。
        """
        self.file_path.parent.mkdir(parents=True, exist_ok=True)
        self._file = open(self.file_path, mode="w", newline="", encoding="utf-8-sig")
        self._writer = csv.writer(self._file)

        header = [
            "frame_index",
            "timestamp_ms",
            "motion_id",
            "pose_detected",
        ] + self.enabled_metrics

        self._writer.writerow(header)
        self._opened = True

    def write_row(
        self,
        frame_index: int,
        timestamp_ms: int,
        pose_detected: bool,
        motion_metrics: MotionMetrics | None,
    ) -> None:
        """
        写入单帧分析结果。

        说明：
        - 未检测到人体时，指标列写空值
        - motion_metrics.selected 中不存在的指标也写空值
        """
        if not self._opened or self._writer is None:
            raise RuntimeError("CSVWriter 尚未打开，请先调用 open()")

        selected_values = {}
        if motion_metrics is not None:
            selected_values = motion_metrics.selected

        row = [
            frame_index,
            timestamp_ms,
            self.motion_id,
            int(pose_detected),
        ]

        for metric_id in self.enabled_metrics:
            value = selected_values.get(metric_id)
            row.append("" if value is None else value)

        self._writer.writerow(row)

    def close(self) -> None:
        """
        关闭 CSV 文件。
        """
        if self._file is not None:
            self._file.close()
            self._file = None
            self._writer = None
            self._opened = False