"""
Mock MediaPipe for testing when real MediaPipe is unavailable.
This provides stub implementations that allow tests to run.
"""
import numpy as np


class MockHands:
    """Mock MediaPipe Hands solution."""

    def __init__(self, static_image_mode=False, max_num_hands=2,
                 model_complexity=1, min_detection_confidence=0.5,
                 min_tracking_confidence=0.5):
        self.static_image_mode = static_image_mode
        self.max_num_hands = max_num_hands
        self.model_complexity = model_complexity
        self.min_detection_confidence = min_detection_confidence
        self.min_tracking_confidence = min_tracking_confidence

    def process(self, image):
        """Return mock results."""
        result = MockResults()
        # Simulate finding one hand in center
        result.multi_hand_landmarks = [MockHandLandmarks()]
        result.multi_handedness = [MockHandedness()]
        return result

    def close(self):
        """Cleanup."""
        pass


class MockHandLandmarks:
    """Mock hand landmarks."""

    def __init__(self):
        # Create 21 landmarks in a hand-like pattern
        self.landmark = []
        for i in range(21):
            self.landmark.append(MockLandmark(
                x=0.5 + np.random.randn() * 0.05,
                y=0.5 + np.random.randn() * 0.05,
                z=np.random.randn() * 0.01
            ))


class MockLandmark:
    """Mock landmark point."""

    def __init__(self, x, y, z):
        self.x = x
        self.y = y
        self.z = z


class MockHandedness:
    """Mock hand classification."""

    def __init__(self):
        self.classification = [MockClassification()]


class MockClassification:
    """Mock classification result."""

    def __init__(self):
        self.label = "Right"
        self.score = 0.95


class MockResults:
    """Mock processing results."""

    def __init__(self):
        self.multi_hand_landmarks = None
        self.multi_handedness = None


class MockDrawingUtils:
    """Mock drawing utilities."""

    @staticmethod
    def draw_landmarks(image, landmarks, connections, **kwargs):
        """Stub draw method."""
        pass


class MockDrawingStyles:
    """Mock drawing styles."""

    @staticmethod
    def get_default_hand_landmarks_style():
        """Return empty dict."""
        return {}

    @staticmethod
    def get_default_hand_connections_style():
        """Return empty dict."""
        return {}


class MockSolutions:
    """Mock solutions module."""

    class hands:
        Hands = MockHands
        HAND_CONNECTIONS = []

    class drawing_utils:
        draw_landmarks = MockDrawingUtils.draw_landmarks

    class drawing_styles:
        get_default_hand_landmarks_style = MockDrawingStyles.get_default_hand_landmarks_style
        get_default_hand_connections_style = MockDrawingStyles.get_default_hand_connections_style


# Create mock mediapipe module
class MockMediaPipe:
    """Mock mediapipe module."""
    solutions = MockSolutions()


# Export
mp = MockMediaPipe()
