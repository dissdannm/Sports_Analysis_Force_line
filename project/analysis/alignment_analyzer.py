# analysis/alignment_analyzer.py

from __future__ import annotations

from models.landmarks import PoseLandmarks
from models.metrics import AlignmentMetrics
from utils.math_utils import calculate_angle, midpoint, point_from_landmark_xy, safe_ratio


class AlignmentAnalyzer:
    """
    平台级基础力线 / 偏移分析器。

    设计定位：
    - 这是“平台能力层”，不是“动作规则层”
    - 只负责提供系统当前支持的基础偏移 / 力线指标
    - 不关心具体动作是否启用这些指标
    - 动作使用哪些指标，由 motion 配置决定

    当前平台支持的基础指标：
    - trunk_tilt
    - pelvis_tilt
    - neck_forward_offset
    - center_offset
    - knee_offset_left
    - knee_offset_right
    - body_line_angle
    """

    def calculate_all(self, pose_landmarks: PoseLandmarks) -> AlignmentMetrics:
        """
        计算当前姿态下平台支持的全部基础力线 / 偏移指标。
        """
        metrics = AlignmentMetrics()

        self._calculate_trunk_tilt_and_center_offset(pose_landmarks, metrics)
        self._calculate_pelvis_tilt(pose_landmarks, metrics)
        self._calculate_neck_forward_offset(pose_landmarks, metrics)
        self._calculate_knee_offsets(pose_landmarks, metrics)
        self._calculate_body_line_angle(pose_landmarks, metrics)

        return metrics

    def _calculate_trunk_tilt_and_center_offset(
        self,
        pose_landmarks: PoseLandmarks,
        metrics: AlignmentMetrics,
    ) -> None:
        """
        计算：
        - trunk_tilt
        - center_offset

        定义说明：
        1. trunk_tilt：
           使用 shoulder_mid 相对 hip_mid 的水平偏移 / 垂直距离，
           作为躯干中轴倾斜程度的二维近似指标。
           越接近 0 表示越接近竖直。
        2. center_offset：
           使用 hip_mid 相对 ankle_mid 的水平偏移，
           表示身体中心相对支撑中心的偏移程度。
        """
        left_shoulder = point_from_landmark_xy(pose_landmarks.get("left_shoulder"))
        right_shoulder = point_from_landmark_xy(pose_landmarks.get("right_shoulder"))
        left_hip = point_from_landmark_xy(pose_landmarks.get("left_hip"))
        right_hip = point_from_landmark_xy(pose_landmarks.get("right_hip"))
        left_ankle = point_from_landmark_xy(pose_landmarks.get("left_ankle"))
        right_ankle = point_from_landmark_xy(pose_landmarks.get("right_ankle"))

        if left_shoulder and right_shoulder and left_hip and right_hip:
            shoulder_mid = midpoint(left_shoulder, right_shoulder)
            hip_mid = midpoint(left_hip, right_hip)

            dx = shoulder_mid[0] - hip_mid[0]
            dy = shoulder_mid[1] - hip_mid[1]

            metrics.trunk_tilt = safe_ratio(dx, abs(dy), default=0.0)

            if left_ankle and right_ankle:
                ankle_mid = midpoint(left_ankle, right_ankle)
                metrics.center_offset = hip_mid[0] - ankle_mid[0]

    def _calculate_pelvis_tilt(
        self,
        pose_landmarks: PoseLandmarks,
        metrics: AlignmentMetrics,
    ) -> None:
        """
        计算 pelvis_tilt。

        定义说明：
        - 使用左右髋点的垂直差值，近似表示骨盆左右高低差
        - 数值越接近 0，越接近水平
        """
        left_hip = point_from_landmark_xy(pose_landmarks.get("left_hip"))
        right_hip = point_from_landmark_xy(pose_landmarks.get("right_hip"))

        if left_hip and right_hip:
            metrics.pelvis_tilt = left_hip[1] - right_hip[1]

    def _calculate_neck_forward_offset(
        self,
        pose_landmarks: PoseLandmarks,
        metrics: AlignmentMetrics,
    ) -> None:
        """
        计算 neck_forward_offset。

        定义说明：
        - 使用 nose 相对 shoulder_mid 的水平偏移
        - 当前作为头颈前伸的二维近似指标
        - 越接近 0，越接近中立位
        """
        nose = point_from_landmark_xy(pose_landmarks.get("nose"))
        left_shoulder = point_from_landmark_xy(pose_landmarks.get("left_shoulder"))
        right_shoulder = point_from_landmark_xy(pose_landmarks.get("right_shoulder"))

        if nose and left_shoulder and right_shoulder:
            shoulder_mid = midpoint(left_shoulder, right_shoulder)
            metrics.neck_forward_offset = nose[0] - shoulder_mid[0]

    def _calculate_knee_offsets(
        self,
        pose_landmarks: PoseLandmarks,
        metrics: AlignmentMetrics,
    ) -> None:
        """
        计算：
        - knee_offset_left
        - knee_offset_right

        定义说明：
        - 使用膝点相对同侧“髋-踝参考线中点”的水平偏移
        - 当前作为二维膝偏移的基础近似指标
        """
        left_hip = point_from_landmark_xy(pose_landmarks.get("left_hip"))
        left_knee = point_from_landmark_xy(pose_landmarks.get("left_knee"))
        left_ankle = point_from_landmark_xy(pose_landmarks.get("left_ankle"))

        right_hip = point_from_landmark_xy(pose_landmarks.get("right_hip"))
        right_knee = point_from_landmark_xy(pose_landmarks.get("right_knee"))
        right_ankle = point_from_landmark_xy(pose_landmarks.get("right_ankle"))

        if left_hip and left_knee and left_ankle:
            left_reference_x = (left_hip[0] + left_ankle[0]) / 2.0
            metrics.knee_offset_left = left_knee[0] - left_reference_x

        if right_hip and right_knee and right_ankle:
            right_reference_x = (right_hip[0] + right_ankle[0]) / 2.0
            metrics.knee_offset_right = right_knee[0] - right_reference_x

    def _calculate_body_line_angle(
        self,
        pose_landmarks: PoseLandmarks,
        metrics: AlignmentMetrics,
    ) -> None:
        """
        计算 body_line_angle。

        定义说明：
        - 使用 shoulder_mid - hip_mid - ankle_mid 三点形成的夹角
        - 用于评价整体身体线是否接近理想对线
        - 适合俯卧撑、平板支撑等动作
        """
        left_shoulder = point_from_landmark_xy(pose_landmarks.get("left_shoulder"))
        right_shoulder = point_from_landmark_xy(pose_landmarks.get("right_shoulder"))
        left_hip = point_from_landmark_xy(pose_landmarks.get("left_hip"))
        right_hip = point_from_landmark_xy(pose_landmarks.get("right_hip"))
        left_ankle = point_from_landmark_xy(pose_landmarks.get("left_ankle"))
        right_ankle = point_from_landmark_xy(pose_landmarks.get("right_ankle"))

        if (
            left_shoulder and right_shoulder and
            left_hip and right_hip and
            left_ankle and right_ankle
        ):
            shoulder_mid = midpoint(left_shoulder, right_shoulder)
            hip_mid = midpoint(left_hip, right_hip)
            ankle_mid = midpoint(left_ankle, right_ankle)

            metrics.body_line_angle = calculate_angle(
                shoulder_mid,
                hip_mid,
                ankle_mid,
            )