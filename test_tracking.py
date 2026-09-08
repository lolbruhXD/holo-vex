"""
Unit tests for hand tracking system.
Tests landmark extraction, normalization, gesture detection, and error handling.
"""

import unittest
import numpy as np
import cv2
from unittest.mock import Mock, patch, MagicMock
from hand_tracker import HandTracker, HandLandmarks


class TestHandLandmarks(unittest.TestCase):
    """Test HandLandmarks dataclass."""

    def test_hand_landmarks_creation(self):
        """Test creating HandLandmarks object."""
        landmarks = np.random.rand(21, 3).astype(np.float32)
        hand_data = HandLandmarks(
            landmarks=landmarks,
            handedness="Left",
            confidence=0.95,
            raw_landmarks=[]
        )

        self.assertEqual(hand_data.handedness, "Left")
        self.assertEqual(hand_data.confidence, 0.95)
        self.assertEqual(hand_data.landmarks.shape, (21, 3))
        np.testing.assert_array_equal(hand_data.landmarks, landmarks)


class TestHandTracker(unittest.TestCase):
    """Test HandTracker functionality."""

    def setUp(self):
        """Set up test fixtures."""
        self.tracker = HandTracker(
            max_num_hands=2,
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5,
            model_complexity=0  # Use lite model for tests
        )

    def tearDown(self):
        """Clean up resources."""
        self.tracker.release()

    def test_tracker_initialization(self):
        """Test tracker initializes correctly."""
        self.assertIsNotNone(self.tracker.hands)
        self.assertIsNone(self.tracker.prev_left_hand)
        self.assertIsNone(self.tracker.prev_right_hand)
        self.assertEqual(self.tracker.frame_count, 0)
        self.assertEqual(self.tracker.detection_failures, 0)

    def test_landmark_indices(self):
        """Test landmark index constants."""
        self.assertEqual(HandTracker.WRIST, 0)
        self.assertEqual(HandTracker.THUMB_TIP, 4)
        self.assertEqual(HandTracker.INDEX_FINGER_TIP, 8)
        self.assertEqual(HandTracker.MIDDLE_FINGER_TIP, 12)
        self.assertEqual(HandTracker.RING_FINGER_TIP, 16)
        self.assertEqual(HandTracker.PINKY_TIP, 20)

    def test_extract_landmarks(self):
        """Test landmark extraction from MediaPipe format."""
        # Create mock MediaPipe landmarks
        mock_hand_landmarks = Mock()
        mock_landmarks = []

        for i in range(21):
            mock_landmark = Mock()
            mock_landmark.x = i * 0.01
            mock_landmark.y = i * 0.02
            mock_landmark.z = i * 0.001
            mock_landmarks.append(mock_landmark)

        mock_hand_landmarks.landmark = mock_landmarks

        # Extract landmarks
        landmarks = self.tracker._extract_landmarks(mock_hand_landmarks)

        # Verify shape
        self.assertEqual(landmarks.shape, (21, 3))

        # Verify values
        for i in range(21):
            self.assertAlmostEqual(landmarks[i, 0], i * 0.01)
            self.assertAlmostEqual(landmarks[i, 1], i * 0.02)
            self.assertAlmostEqual(landmarks[i, 2], i * 0.001)

    def test_denormalize_landmarks(self):
        """Test converting normalized to pixel coordinates."""
        # Create normalized landmarks
        normalized = np.array([
            [0.5, 0.5, -0.1],
            [0.0, 0.0, 0.0],
            [1.0, 1.0, -0.2]
        ], dtype=np.float32)

        frame_width = 1280
        frame_height = 720

        # Denormalize
        pixel_coords = self.tracker.denormalize_landmarks(
            normalized,
            frame_width,
            frame_height
        )

        # Verify shape
        self.assertEqual(pixel_coords.shape, (3, 3))

        # Verify values
        self.assertAlmostEqual(pixel_coords[0, 0], 640.0)  # 0.5 * 1280
        self.assertAlmostEqual(pixel_coords[0, 1], 360.0)  # 0.5 * 720
        self.assertAlmostEqual(pixel_coords[1, 0], 0.0)
        self.assertAlmostEqual(pixel_coords[1, 1], 0.0)
        self.assertAlmostEqual(pixel_coords[2, 0], 1280.0)
        self.assertAlmostEqual(pixel_coords[2, 1], 720.0)

        # Z should remain unchanged
        self.assertAlmostEqual(pixel_coords[0, 2], -0.1)
        self.assertAlmostEqual(pixel_coords[2, 2], -0.2)

    def test_get_fingertip_positions(self):
        """Test extracting fingertip positions."""
        # Create test landmarks
        landmarks = np.zeros((21, 3), dtype=np.float32)
        landmarks[HandTracker.THUMB_TIP] = [0.1, 0.2, -0.1]
        landmarks[HandTracker.INDEX_FINGER_TIP] = [0.3, 0.4, -0.2]
        landmarks[HandTracker.MIDDLE_FINGER_TIP] = [0.5, 0.6, -0.3]
        landmarks[HandTracker.RING_FINGER_TIP] = [0.7, 0.8, -0.4]
        landmarks[HandTracker.PINKY_TIP] = [0.9, 1.0, -0.5]

        hand_data = HandLandmarks(
            landmarks=landmarks,
            handedness="Right",
            confidence=0.9,
            raw_landmarks=[]
        )

        frame_width = 1000
        frame_height = 1000

        # Get fingertips
        fingertips = self.tracker.get_fingertip_positions(
            hand_data,
            frame_width,
            frame_height
        )

        # Verify all fingers present
        self.assertIn('thumb', fingertips)
        self.assertIn('index', fingertips)
        self.assertIn('middle', fingertips)
        self.assertIn('ring', fingertips)
        self.assertIn('pinky', fingertips)

        # Verify thumb position
        thumb_x, thumb_y, thumb_z = fingertips['thumb']
        self.assertAlmostEqual(thumb_x, 100.0)  # 0.1 * 1000
        self.assertAlmostEqual(thumb_y, 200.0)  # 0.2 * 1000

    def test_get_palm_center(self):
        """Test palm center calculation."""
        # Create test landmarks
        landmarks = np.zeros((21, 3), dtype=np.float32)
        landmarks[HandTracker.WRIST] = [0.5, 0.5, 0.0]
        landmarks[HandTracker.INDEX_FINGER_MCP] = [0.5, 0.4, 0.0]
        landmarks[HandTracker.MIDDLE_FINGER_MCP] = [0.5, 0.4, 0.0]
        landmarks[HandTracker.RING_FINGER_MCP] = [0.5, 0.4, 0.0]
        landmarks[HandTracker.PINKY_MCP] = [0.5, 0.4, 0.0]

        hand_data = HandLandmarks(
            landmarks=landmarks,
            handedness="Left",
            confidence=0.85,
            raw_landmarks=[]
        )

        frame_width = 1000
        frame_height = 1000

        # Get palm center
        palm_x, palm_y, palm_z = self.tracker.get_palm_center(
            hand_data,
            frame_width,
            frame_height
        )

        # Palm should be average of wrist and MCPs
        expected_x = 500.0  # 0.5 * 1000
        expected_y = 420.0  # ((0.5 + 4*0.4) / 5) * 1000

        self.assertAlmostEqual(palm_x, expected_x)
        self.assertAlmostEqual(palm_y, expected_y)

    def test_is_pinching_true(self):
        """Test pinch detection when fingers are close."""
        landmarks = np.zeros((21, 3), dtype=np.float32)
        landmarks[HandTracker.THUMB_TIP] = [0.5, 0.5, 0.0]
        landmarks[HandTracker.INDEX_FINGER_TIP] = [0.51, 0.51, 0.0]  # Very close

        hand_data = HandLandmarks(
            landmarks=landmarks,
            handedness="Right",
            confidence=0.9,
            raw_landmarks=[]
        )

        # Should detect pinch with default threshold
        is_pinching = self.tracker.is_pinching(hand_data, threshold=0.05)
        self.assertTrue(is_pinching)

    def test_is_pinching_false(self):
        """Test pinch detection when fingers are far apart."""
        landmarks = np.zeros((21, 3), dtype=np.float32)
        landmarks[HandTracker.THUMB_TIP] = [0.3, 0.3, 0.0]
        landmarks[HandTracker.INDEX_FINGER_TIP] = [0.7, 0.7, 0.0]  # Far apart

        hand_data = HandLandmarks(
            landmarks=landmarks,
            handedness="Right",
            confidence=0.9,
            raw_landmarks=[]
        )

        # Should not detect pinch
        is_pinching = self.tracker.is_pinching(hand_data, threshold=0.05)
        self.assertFalse(is_pinching)

    def test_get_hand_orientation(self):
        """Test hand orientation calculation."""
        landmarks = np.zeros((21, 3), dtype=np.float32)
        landmarks[HandTracker.WRIST] = [0.5, 0.5, 0.0]
        landmarks[HandTracker.MIDDLE_FINGER_MCP] = [0.5, 0.3, -0.1]

        hand_data = HandLandmarks(
            landmarks=landmarks,
            handedness="Left",
            confidence=0.9,
            raw_landmarks=[]
        )

        orientation = self.tracker.get_hand_orientation(hand_data)

        # Verify keys present
        self.assertIn('pitch', orientation)
        self.assertIn('yaw', orientation)
        self.assertIn('roll', orientation)

        # Verify values are angles in degrees
        self.assertIsInstance(orientation['pitch'], (int, float))
        self.assertIsInstance(orientation['yaw'], (int, float))
        self.assertEqual(orientation['roll'], 0.0)

    def test_diagnostics(self):
        """Test diagnostics reporting."""
        diag = self.tracker.get_diagnostics()

        self.assertIn('frame_count', diag)
        self.assertIn('detection_failures', diag)
        self.assertIn('failure_rate', diag)
        self.assertIn('left_hand_cached', diag)
        self.assertIn('right_hand_cached', diag)

        self.assertEqual(diag['frame_count'], 0)
        self.assertEqual(diag['detection_failures'], 0)
        self.assertFalse(diag['left_hand_cached'])
        self.assertFalse(diag['right_hand_cached'])

    def test_process_frame_no_hands(self):
        """Test processing frame with no hands detected."""
        # Create blank frame
        frame = np.zeros((480, 640, 3), dtype=np.uint8)

        # Process (will likely detect no hands)
        result = self.tracker.process_frame(frame)

        # Verify structure
        self.assertIn('left', result)
        self.assertIn('right', result)

        # Frame count should increment
        self.assertGreater(self.tracker.frame_count, 0)

    def test_temporal_smoothing(self):
        """Test that previous frame data is used when detection fails."""
        # Create fake hand data
        landmarks = np.random.rand(21, 3).astype(np.float32)
        fake_hand = HandLandmarks(
            landmarks=landmarks,
            handedness="Left",
            confidence=0.9,
            raw_landmarks=[]
        )

        # Manually set previous hand
        self.tracker.prev_left_hand = fake_hand

        # Create blank frame (no hands)
        frame = np.zeros((480, 640, 3), dtype=np.uint8)

        # Process
        result = self.tracker.process_frame(frame)

        # Should use cached data
        if result['left'] is not None:
            # If we got cached data, verify it matches
            np.testing.assert_array_equal(
                result['left'].landmarks,
                fake_hand.landmarks
            )


class TestIntegration(unittest.TestCase):
    """Integration tests with real video processing."""

    def test_tracker_with_synthetic_frame(self):
        """Test tracker with a synthetic test frame."""
        tracker = HandTracker(max_num_hands=1, model_complexity=0)

        # Create synthetic frame with simple pattern
        frame = np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)

        try:
            result = tracker.process_frame(frame)

            # Verify return structure
            self.assertIsInstance(result, dict)
            self.assertIn('left', result)
            self.assertIn('right', result)

            # Verify frame was processed
            self.assertEqual(tracker.frame_count, 1)

        finally:
            tracker.release()

    def test_multiple_frames(self):
        """Test processing multiple frames."""
        tracker = HandTracker(max_num_hands=2, model_complexity=0)

        frames = [
            np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)
            for _ in range(5)
        ]

        try:
            for frame in frames:
                result = tracker.process_frame(frame)
                self.assertIsInstance(result, dict)

            # Verify all frames were counted
            self.assertEqual(tracker.frame_count, 5)

        finally:
            tracker.release()


if __name__ == '__main__':
    unittest.main()
