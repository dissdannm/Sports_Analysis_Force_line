# analysis/alignment_analyzer.py

from __future__ import annotations

from models.landmarks import PoseLandmarks
from models.metrics import AlignmentMetrics
from utils.math_utils import (
    angle_with_horizontal,
    calculate_angle,
    midpoint,
    point_from_landmark_xy,
    safe_ratio,
    line_midpoint_vertical_gap,
)


class AlignmentAnalyzer:
    """
    平台级基础力线 / 偏移分析器。
    """

    def calculate_all(self, pose_landmarks: PoseLandmarks) -> AlignmentMetrics:
        metrics = AlignmentMetrics()

        self._calculate_trunk_tilt_and_center_offset(pose_landmarks, metrics)
        self._calculate_pelvis_tilt(pose_landmarks, metrics)
        self._calculate_neck_forward_offset(pose_landmarks, metrics)
        self._calculate_knee_offsets(pose_landmarks, metrics)
        self._calculate_body_line_angle(pose_landmarks, metrics)
        self._calculate_trunk_ground_angle(pose_landmarks, metrics)
        self._calculate_neck_flexion_angle(pose_landmarks, metrics)
        self._calculate_lumbar_gap_distance(pose_landmarks, metrics)

        return metrics

    def _calculate_trunk_tilt_and_center_offset(
        self,
        pose_landmarks: PoseLandmarks,
        metrics: AlignmentMetrics,
    ) -> None:
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
        left_hip = point_from_landmark_xy(pose_landmarks.get("left_hip"))
        right_hip = point_from_landmark_xy(pose_landmarks.get("right_hip"))

        if left_hip and right_hip:
            metrics.pelvis_tilt = left_hip[1] - right_hip[1]

    def _calculate_neck_forward_offset(
        self,
        pose_landmarks: PoseLandmarks,
        metrics: AlignmentMetrics,
    ) -> None:
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

    def _calculate_trunk_ground_angle(
        self,
        pose_landmarks: PoseLandmarks,
        metrics: AlignmentMetrics,
    ) -> None:
        left_shoulder = point_from_landmark_xy(pose_landmarks.get("left_shoulder"))
        right_shoulder = point_from_landmark_xy(pose_landmarks.get("right_shoulder"))
        left_hip = point_from_landmark_xy(pose_landmarks.get("left_hip"))
        right_hip = point_from_landmark_xy(pose_landmarks.get("right_hip"))

        if left_shoulder and right_shoulder and left_hip and right_hip:
            shoulder_mid = midpoint(left_shoulder, right_shoulder)
            hip_mid = midpoint(left_hip, right_hip)
            metrics.trunk_ground_angle = angle_with_horizontal(hip_mid, shoulder_mid)

    def _calculate_neck_flexion_angle(
        self,
        pose_landmarks: PoseLandmarks,
        metrics: AlignmentMetrics,
    ) -> None:
        nose = point_from_landmark_xy(pose_landmarks.get("nose"))
        left_shoulder = point_from_landmark_xy(pose_landmarks.get("left_shoulder"))
        right_shoulder = point_from_landmark_xy(pose_landmarks.get("right_shoulder"))
        left_hip = point_from_landmark_xy(pose_landmarks.get("left_hip"))
        right_hip = point_from_landmark_xy(pose_landmarks.get("right_hip"))

        if nose and left_shoulder and right_shoulder and left_hip and right_hip:
            shoulder_mid = midpoint(left_shoulder, right_shoulder)
            hip_mid = midpoint(left_hip, right_hip)
            metrics.neck_flexion_angle = calculate_angle(
                nose,
                shoulder_mid,
                hip_mid,
            )

    def _calculate_lumbar_gap_distance(
        self,
        pose_landmarks: PoseLandmarks,
        metrics: AlignmentMetrics,
    ) -> None:
        left_shoulder = point_from_landmark_xy(pose_landmarks.get("left_shoulder"))
        right_shoulder = point_from_landmark_xy(pose_landmarks.get("right_shoulder"))
        left_hip = point_from_landmark_xy(pose_landmarks.get("left_hip"))
        right_hip = point_from_landmark_xy(pose_landmarks.get("right_hip"))

        if left_shoulder and right_shoulder and left_hip and right_hip:
            shoulder_mid = midpoint(left_shoulder, right_shoulder)
            hip_mid = midpoint(left_hip, right_hip)
            metrics.lumbar_gap_distance = line_midpoint_vertical_gap(
                shoulder_mid,
                hip_mid,
                hip_mid,
            )