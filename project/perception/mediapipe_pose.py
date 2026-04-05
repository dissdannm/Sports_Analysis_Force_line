# perception/mediapipe_pose.py

from __future__ import annotations

from pathlib import Path
from typing import Optional

import cv2
import mediapipe as mp
from mediapipe.tasks import python
from mediapipe.tasks.python import vision

from models.landmarks import Landmark, PoseLandmarks
from perception.pose_estimator import PoseEstimator


class MediaPipePoseEstimator(PoseEstimator):
    """
    基于 MediaPipe Tasks API 的人体姿态识别器。

    当前版本设计目标：
    1. 输入 OpenCV BGR 图像
    2. 输出项目内部统一的 PoseLandmarks
    3. 使用 VIDEO 模式，适合摄像头连续帧处理
    4. 当前只处理单人姿态，满足企业第一版主线
    """

    LANDMARK_INDEX_MAP = {
        "nose": 0,
        "left_eye_inner": 1,
        "left_eye": 2,
        "left_eye_outer": 3,
        "right_eye_inner": 4,
        "right_eye": 5,
        "right_eye_outer": 6,
        "left_ear": 7,
        "right_ear": 8,
        "mouth_left": 9,
        "mouth_right": 10,
        "left_shoulder": 11,
        "right_shoulder": 12,
        "left_elbow": 13,
        "right_elbow": 14,
        "left_wrist": 15,
        "right_wrist": 16,
        "left_pinky": 17,
        "right_pinky": 18,
        "left_index": 19,
        "right_index": 20,
        "left_thumb": 21,
        "right_thumb": 22,
        "left_hip": 23,
        "right_hip": 24,
        "left_knee": 25,
        "right_knee": 26,
        "left_ankle": 27,
        "right_ankle": 28,
        "left_heel": 29,
        "right_heel": 30,
        "left_foot_index": 31,
        "right_foot_index": 32,
    }

    def __init__(
        self,
        model_path: str,
        num_poses: int = 1,
        min_pose_detection_confidence: float = 0.5,
        min_pose_presence_confidence: float = 0.5,
        min_tracking_confidence: float = 0.5,
        output_segmentation_masks: bool = False,
    ) -> None:
        """
        参数说明：
        - model_path:
            MediaPipe Pose Landmarker 的 .task 模型文件路径
        - num_poses:
            最多检测多少个人体；企业第一版默认单人
        - min_pose_detection_confidence:
            人体检测最低置信度
        - min_pose_presence_confidence:
            姿态存在最低置信度
        - min_tracking_confidence:
            跟踪最低置信度
        - output_segmentation_masks:
            是否输出分割掩码；当前版本不需要
        """
        self.model_path = Path(model_path).resolve()
        if not self.model_path.exists():
            raise FileNotFoundError(f"未找到 pose landmarker 模型文件: {self.model_path}")

        base_options = python.BaseOptions(model_asset_path=str(self.model_path))
        options = vision.PoseLandmarkerOptions(
            base_options=base_options,
            running_mode=vision.RunningMode.VIDEO,
            num_poses=num_poses,
            min_pose_detection_confidence=min_pose_detection_confidence,
            min_pose_presence_confidence=min_pose_presence_confidence,
            min_tracking_confidence=min_tracking_confidence,
            output_segmentation_masks=output_segmentation_masks,
        )

        self._landmarker = vision.PoseLandmarker.create_from_options(options)

    def process(self, frame, timestamp_ms: int) -> Optional[PoseLandmarks]:
        """
        处理单帧图像并返回关键点集合。

        参数：
        - frame:
            OpenCV BGR 图像
        - timestamp_ms:
            当前帧对应的毫秒时间戳，必须单调递增

        返回：
        - PoseLandmarks:
            检测成功时返回
        - None:
            未检测到人体或输入无效时返回
        """
        if frame is None:
            return None

        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        mp_image = mp.Image(
            image_format=mp.ImageFormat.SRGB,
            data=rgb_frame,
        )

        result = self._landmarker.detect_for_video(mp_image, timestamp_ms)

        if not result.pose_landmarks:
            return None

        first_pose = result.pose_landmarks[0]
        converted_landmarks = {}

        for name, index in self.LANDMARK_INDEX_MAP.items():
            landmark = first_pose[index]
            converted_landmarks[name] = Landmark(
                x=landmark.x,
                y=landmark.y,
                z=landmark.z,
                visibility=0.0,
            )

        return PoseLandmarks(landmarks=converted_landmarks)

    def close(self) -> None:
        """
        释放 MediaPipe 识别器资源。
        """
        if self._landmarker is not None:
            self._landmarker.close()
            self._landmarker = None