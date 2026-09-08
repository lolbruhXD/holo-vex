"""
Hand tracking module using MediaPipe for real-time landmark detection.
Provides normalized 3D coordinates for 21 landmarks per hand with robust error handling.
"""

import cv2
import numpy as np
from typing import Optional, Dict, List, Tuple
from dataclasses import dataclass

# Try to import mediapipe, fall back to mock if unavailable
try:
    import mediapipe as mp
    MEDIAPIPE_AVAILABLE = True
except ImportError:
    print("WARNING: MediaPipe not available, using mock implementation")
    from mock_mediapipe import mp
    MEDIAPIPE_AVAILABLE = False


@dataclass
class HandLandmarks:
    """Container for hand landmark data."""
    landmarks: np.ndarray  # Shape: (21, 3) - x, y, z normalized coordinates
    handedness: str  # "Left" or "Right"
    confidence: float
    raw_landmarks: List  # Original MediaPipe landmarks for reference


class HandTracker:
    """
    Real-time hand tracking using MediaPipe Hands.

    Detects up to 2 hands (left and right) with 21 3D landmarks each.
    Landmarks are normalized to [0, 1] range relative to image dimensions.
    """

    # MediaPipe hand landmark indices
    WRIST = 0
    THUMB_CMC = 1
    THUMB_MCP = 2
    THUMB_IP = 3
    THUMB_TIP = 4
    INDEX_FINGER_MCP = 5
    INDEX_FINGER_PIP = 6
    INDEX_FINGER_DIP = 7
    INDEX_FINGER_TIP = 8
    MIDDLE_FINGER_MCP = 9
    MIDDLE_FINGER_PIP = 10
    MIDDLE_FINGER_DIP = 11
    MIDDLE_FINGER_TIP = 12
    RING_FINGER_MCP = 13
    RING_FINGER_PIP = 14
    RING_FINGER_DIP = 15
    RING_FINGER_TIP = 16
    PINKY_MCP = 17
    PINKY_PIP = 18
    PINKY_DIP = 19
    PINKY_TIP = 20

    def __init__(
        self,
        max_num_hands: int = 2,
        min_detection_confidence: float = 0.7,
        min_tracking_confidence: float = 0.5,
        model_complexity: int = 1
    ):
        """
        Initialize MediaPipe hand tracking.

        Args:
            max_num_hands: Maximum hands to detect (1-2)
            min_detection_confidence: Minimum confidence for initial detection
            min_tracking_confidence: Minimum confidence for tracking
            model_complexity: 0 (lite) or 1 (full) - affects accuracy/speed
        """
        self.mp_hands = mp.solutions.hands
        self.mp_drawing = mp.solutions.drawing_utils
        self.mp_drawing_styles = mp.solutions.drawing_styles

        self.hands = self.mp_hands.Hands(
            static_image_mode=False,
            max_num_hands=max_num_hands,
            min_detection_confidence=min_detection_confidence,
            min_tracking_confidence=min_tracking_confidence,
            model_complexity=model_complexity
        )

        self.prev_left_hand: Optional[HandLandmarks] = None
        self.prev_right_hand: Optional[HandLandmarks] = None
        self.frame_count = 0
        self.detection_failures = 0

    def process_frame(
        self,
        frame: np.ndarray
    ) -> Dict[str, Optional[HandLandmarks]]:
        """
        Process a single frame and extract hand landmarks.

        Args:
            frame: BGR image from camera (H, W, 3)

        Returns:
            Dictionary with 'left' and 'right' keys, each containing
            HandLandmarks or None if hand not detected
        """
        self.frame_count += 1

        # Convert BGR to RGB for MediaPipe
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        # Flip horizontally for mirror effect
        rgb_frame = cv2.flip(rgb_frame, 1)

        # Process with MediaPipe
        results = self.hands.process(rgb_frame)

        hands_data = {
            'left': None,
            'right': None
        }

        if not results.multi_hand_landmarks:
            self.detection_failures += 1
            # Use previous frame data if available (temporal smoothing)
            if self.prev_left_hand:
                hands_data['left'] = self.prev_left_hand
            if self.prev_right_hand:
                hands_data['right'] = self.prev_right_hand
            return hands_data

        # Reset failure counter on successful detection
        self.detection_failures = 0

        # Extract landmarks for each detected hand
        for hand_landmarks, handedness in zip(
            results.multi_hand_landmarks,
            results.multi_handedness
        ):
            # Determine handedness
            label = handedness.classification[0].label  # "Left" or "Right"
            confidence = handedness.classification[0].score

            # Extract normalized landmarks
            landmarks_array = self._extract_landmarks(hand_landmarks)

            hand_data = HandLandmarks(
                landmarks=landmarks_array,
                handedness=label,
                confidence=confidence,
                raw_landmarks=hand_landmarks.landmark
            )

            # Store by handedness
            key = label.lower()
            hands_data[key] = hand_data

            # Cache for temporal smoothing
            if key == 'left':
                self.prev_left_hand = hand_data
            else:
                self.prev_right_hand = hand_data

        return hands_data

    def _extract_landmarks(
        self,
        hand_landmarks
    ) -> np.ndarray:
        """
        Convert MediaPipe landmarks to numpy array.

        Args:
            hand_landmarks: MediaPipe HandLandmarks object

        Returns:
            Array of shape (21, 3) with normalized x, y, z coordinates
        """
        landmarks = np.zeros((21, 3), dtype=np.float32)

        for idx, landmark in enumerate(hand_landmarks.landmark):
            landmarks[idx] = [
                landmark.x,  # Normalized [0, 1]
                landmark.y,  # Normalized [0, 1]
                landmark.z   # Relative depth (negative = closer)
            ]

        return landmarks

    def denormalize_landmarks(
        self,
        landmarks: np.ndarray,
        frame_width: int,
        frame_height: int
    ) -> np.ndarray:
        """
        Convert normalized landmarks to pixel coordinates.

        Args:
            landmarks: Normalized landmarks (21, 3)
            frame_width: Image width in pixels
            frame_height: Image height in pixels

        Returns:
            Landmarks in pixel coordinates (21, 3)
        """
        denorm = landmarks.copy()
        denorm[:, 0] *= frame_width
        denorm[:, 1] *= frame_height
        # Z remains relative depth

        return denorm

    def get_fingertip_positions(
        self,
        hand_data: HandLandmarks,
        frame_width: int,
        frame_height: int
    ) -> Dict[str, Tuple[int, int, float]]:
        """
        Extract fingertip positions in pixel coordinates.

        Args:
            hand_data: HandLandmarks object
            frame_width: Image width
            frame_height: Image height

        Returns:
            Dictionary mapping finger names to (x, y, z) tuples
        """
        landmarks_px = self.denormalize_landmarks(
            hand_data.landmarks,
            frame_width,
            frame_height
        )

        return {
            'thumb': tuple(landmarks_px[self.THUMB_TIP]),
            'index': tuple(landmarks_px[self.INDEX_FINGER_TIP]),
            'middle': tuple(landmarks_px[self.MIDDLE_FINGER_TIP]),
            'ring': tuple(landmarks_px[self.RING_FINGER_TIP]),
            'pinky': tuple(landmarks_px[self.PINKY_TIP])
        }

    def get_palm_center(
        self,
        hand_data: HandLandmarks,
        frame_width: int,
        frame_height: int
    ) -> Tuple[int, int, float]:
        """
        Calculate palm center from wrist and MCP joints.

        Args:
            hand_data: HandLandmarks object
            frame_width: Image width
            frame_height: Image height

        Returns:
            (x, y, z) palm center in pixel coordinates
        """
        landmarks_px = self.denormalize_landmarks(
            hand_data.landmarks,
            frame_width,
            frame_height
        )

        # Average of wrist and four MCP joints
        palm_points = landmarks_px[[
            self.WRIST,
            self.INDEX_FINGER_MCP,
            self.MIDDLE_FINGER_MCP,
            self.RING_FINGER_MCP,
            self.PINKY_MCP
        ]]

        palm_center = np.mean(palm_points, axis=0)
        return tuple(palm_center)

    def is_pinching(
        self,
        hand_data: HandLandmarks,
        threshold: float = 0.05
    ) -> bool:
        """
        Detect pinch gesture (thumb and index fingertip close together).

        Args:
            hand_data: HandLandmarks object
            threshold: Maximum normalized distance for pinch detection

        Returns:
            True if pinching detected
        """
        thumb_tip = hand_data.landmarks[self.THUMB_TIP]
        index_tip = hand_data.landmarks[self.INDEX_FINGER_TIP]

        distance = np.linalg.norm(thumb_tip - index_tip)
        return distance < threshold

    def get_hand_orientation(
        self,
        hand_data: HandLandmarks
    ) -> Dict[str, float]:
        """
        Calculate hand orientation angles.

        Args:
            hand_data: HandLandmarks object

        Returns:
            Dictionary with 'pitch', 'yaw', 'roll' in degrees
        """
        wrist = hand_data.landmarks[self.WRIST]
        middle_mcp = hand_data.landmarks[self.MIDDLE_FINGER_MCP]

        # Vector from wrist to middle finger MCP
        direction = middle_mcp - wrist

        # Calculate angles
        pitch = np.arctan2(direction[1], np.sqrt(direction[0]**2 + direction[2]**2))
        yaw = np.arctan2(direction[0], direction[2])

        return {
            'pitch': np.degrees(pitch),
            'yaw': np.degrees(yaw),
            'roll': 0.0  # Simplified - full roll requires more landmarks
        }

    def draw_landmarks(
        self,
        frame: np.ndarray,
        hand_data: HandLandmarks,
        connections: bool = True
    ):
        """
        Draw hand landmarks and connections on frame.

        Args:
            frame: BGR image to draw on (modified in-place)
            hand_data: HandLandmarks object
            connections: Whether to draw connections between landmarks
        """
        h, w = frame.shape[:2]
        landmarks_px = self.denormalize_landmarks(hand_data.landmarks, w, h)

        # Draw connections
        if connections:
            for connection in self.mp_hands.HAND_CONNECTIONS:
                start_idx, end_idx = connection
                start = landmarks_px[start_idx][:2].astype(int)
                end = landmarks_px[end_idx][:2].astype(int)
                cv2.line(frame, tuple(start), tuple(end), (0, 255, 100), 2)

        # Draw landmarks
        for landmark in landmarks_px:
            x, y = landmark[:2].astype(int)
            cv2.circle(frame, (x, y), 5, (255, 0, 150), -1)
            cv2.circle(frame, (x, y), 7, (255, 255, 255), 1)

    def get_diagnostics(self) -> Dict:
        """Return tracking diagnostics."""
        return {
            'frame_count': self.frame_count,
            'detection_failures': self.detection_failures,
            'failure_rate': (
                self.detection_failures / max(self.frame_count, 1)
            ),
            'left_hand_cached': self.prev_left_hand is not None,
            'right_hand_cached': self.prev_right_hand is not None
        }

    def release(self):
        """Release MediaPipe resources."""
        if self.hands:
            self.hands.close()
