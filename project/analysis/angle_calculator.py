# analysis/angle_calculator.py

from __future__ import annotations

from models.landmarks import PoseLandmarks
from models.metrics import AngleMetrics
from utils.math_utils import calculate_angle, point_from_landmark_xy


class AngleCalculator:
    """
    平台级基础角度计算器。

    设计定位：
    - 这是“平台能力层”，不是“动作规则层”
    - 只负责提供系统当前支持的基础角度计算能力
    - 不关心俯卧撑、深蹲、平板支撑等具体动作
    - 动作要不要使用这些角度，由 motion 配置决定

    当前平台支持的基础角度：
    - left_elbow
    - right_elbow
    - left_shoulder
    - right_shoulder
    - left_hip
    - right_hip
    - left_knee
    - right_knee
    - left_ankle
    - right_ankle
    """

    def calculate_all(self, pose_landmarks: PoseLandmarks) -> AngleMetrics:
        """
        计算当前姿态下平台支持的全部基础角度。

        返回：
        - AngleMetrics，其中 values 字典的 key 为固定 metric_id
        """
        values: dict[str, float] = {}

        # 上肢角度
        self._try_add_angle(
            values=values,
            metric_id="left_elbow",
            pose_landmarks=pose_landmarks,
            point_names=("left_shoulder", "left_elbow", "left_wrist"),
        )
        self._try_add_angle(
            values=values,
            metric_id="right_elbow",
            pose_landmarks=pose_landmarks,
            point_names=("right_shoulder", "right_elbow", "right_wrist"),
        )

        self._try_add_angle(
            values=values,
            metric_id="left_shoulder",
            pose_landmarks=pose_landmarks,
            point_names=("left_elbow", "left_shoulder", "left_hip"),
        )
        self._try_add_angle(
            values=values,
            metric_id="right_shoulder",
            pose_landmarks=pose_landmarks,
            point_names=("right_elbow", "right_shoulder", "right_hip"),
        )

        # 下肢角度
        self._try_add_angle(
            values=values,
            metric_id="left_hip",
            pose_landmarks=pose_landmarks,
            point_names=("left_shoulder", "left_hip", "left_knee"),
        )
        self._try_add_angle(
            values=values,
            metric_id="right_hip",
            pose_landmarks=pose_landmarks,
            point_names=("right_shoulder", "right_hip", "right_knee"),
        )

        self._try_add_angle(
            values=values,
            metric_id="left_knee",
            pose_landmarks=pose_landmarks,
            point_names=("left_hip", "left_knee", "left_ankle"),
        )
        self._try_add_angle(
            values=values,
            metric_id="right_knee",
            pose_landmarks=pose_landmarks,
            point_names=("right_hip", "right_knee", "right_ankle"),
        )

        self._try_add_angle(
            values=values,
            metric_id="left_ankle",
            pose_landmarks=pose_landmarks,
            point_names=("left_knee", "left_ankle", "left_foot_index"),
        )
        self._try_add_angle(
            values=values,
            metric_id="right_ankle",
            pose_landmarks=pose_landmarks,
            point_names=("right_knee", "right_ankle", "right_foot_index"),
        )

        return AngleMetrics(values=values)

    def _try_add_angle(
        self,
        values: dict[str, float],
        metric_id: str,
        pose_landmarks: PoseLandmarks,
        point_names: tuple[str, str, str],
    ) -> None:
        """
        尝试根据三个关键点计算角度，成功则写入 values。

        参数：
        - values:
            角度结果字典
        - metric_id:
            固定指标 ID，例如 left_knee
        - pose_landmarks:
            当前帧关键点集合
        - point_names:
            三个关键点名称，顺序为 (p1, vertex, p3)

        说明：
        - 任意关键点缺失时，直接跳过，不抛异常
        - 这是企业第一版里重要的鲁棒性设计
        """
        point_1 = point_from_landmark_xy(pose_landmarks.get(point_names[0]))
        vertex = point_from_landmark_xy(pose_landmarks.get(point_names[1]))
        point_3 = point_from_landmark_xy(pose_landmarks.get(point_names[2]))

        if point_1 is None or vertex is None or point_3 is None:
            return

        values[metric_id] = calculate_angle(point_1, vertex, point_3)