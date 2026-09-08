"""
Gesture System for Holographic VFX Application
Implements pinch detection, openness calculation, smoothing, hysteresis, and state machine
"""

import numpy as np
from typing import Optional, Tuple, List
from dataclasses import dataclass
from enum import Enum
import time


class GestureState(Enum):
    """State machine states for gesture recognition"""
    IDLE = "idle"
    PINCH_START = "pinch_start"
    PINCH_HOLD = "pinch_hold"
    PINCH_RELEASE = "pinch_release"
    OPEN_HAND = "open_hand"


@dataclass
class HandLandmarks:
    """Container for MediaPipe hand landmark data"""
    landmarks: np.ndarray  # Shape: (21, 3) - x, y, z coordinates
    handedness: str  # "Left" or "Right"
    timestamp: float


class PinchDetector:
    """Detects pinch gestures between thumb and index finger"""

    # MediaPipe hand landmark indices
    THUMB_TIP = 4
    INDEX_TIP = 8
    THUMB_IP = 3
    INDEX_PIP = 6
    WRIST = 0

    def __init__(self, pinch_threshold: float = 0.04, release_threshold: float = 0.06):
        """
        Args:
            pinch_threshold: Distance threshold for pinch detection (normalized)
            release_threshold: Distance threshold for pinch release (hysteresis)
        """
        self.pinch_threshold = pinch_threshold
        self.release_threshold = release_threshold

    def calculate_pinch_distance(self, landmarks: np.ndarray) -> float:
        """
        Calculate normalized distance between thumb tip and index finger tip

        Args:
            landmarks: Hand landmarks array (21, 3)

        Returns:
            Normalized distance between thumb and index tips
        """
        thumb_tip = landmarks[self.THUMB_TIP]
        index_tip = landmarks[self.INDEX_TIP]

        # Calculate Euclidean distance
        distance = np.linalg.norm(thumb_tip - index_tip)

        # Normalize by hand size (wrist to middle finger base)
        wrist = landmarks[self.WRIST]
        middle_base = landmarks[9]  # Middle finger MCP
        hand_size = np.linalg.norm(middle_base - wrist)

        if hand_size > 0:
            normalized_distance = distance / hand_size
        else:
            normalized_distance = 1.0

        return normalized_distance

    def is_pinching(self, landmarks: np.ndarray, current_state: GestureState) -> bool:
        """
        Determine if hand is in pinch state with hysteresis

        Args:
            landmarks: Hand landmarks array (21, 3)
            current_state: Current gesture state for hysteresis

        Returns:
            True if pinching, False otherwise
        """
        distance = self.calculate_pinch_distance(landmarks)

        # Apply hysteresis based on current state
        if current_state in [GestureState.PINCH_HOLD, GestureState.PINCH_START]:
            # Use higher threshold to release
            return distance < self.release_threshold
        else:
            # Use lower threshold to engage
            return distance < self.pinch_threshold

    def get_pinch_point(self, landmarks: np.ndarray) -> np.ndarray:
        """
        Calculate the midpoint between thumb and index finger tips

        Args:
            landmarks: Hand landmarks array (21, 3)

        Returns:
            3D coordinates of pinch point
        """
        thumb_tip = landmarks[self.THUMB_TIP]
        index_tip = landmarks[self.INDEX_TIP]
        return (thumb_tip + index_tip) / 2.0


class OpennessCalculator:
    """Calculates hand openness based on finger extension"""

    # Finger tip and base indices
    FINGER_TIPS = [4, 8, 12, 16, 20]  # Thumb, Index, Middle, Ring, Pinky
    FINGER_BASES = [2, 5, 9, 13, 17]  # Corresponding MCP joints
    WRIST = 0

    def __init__(self):
        self.finger_weights = np.array([0.8, 1.0, 1.0, 0.9, 0.7])  # Weight each finger

    def calculate_openness(self, landmarks: np.ndarray) -> float:
        """
        Calculate hand openness from 0.0 (closed fist) to 1.0 (fully open)

        Args:
            landmarks: Hand landmarks array (21, 3)

        Returns:
            Openness value between 0.0 and 1.0
        """
        wrist = landmarks[self.WRIST]
        openness_values = []

        for tip_idx, base_idx, weight in zip(self.FINGER_TIPS, self.FINGER_BASES, self.finger_weights):
            tip = landmarks[tip_idx]
            base = landmarks[base_idx]

            # Distance from wrist to tip
            tip_distance = np.linalg.norm(tip - wrist)
            # Distance from wrist to base
            base_distance = np.linalg.norm(base - wrist)

            if base_distance > 0:
                # Extension ratio
                extension = (tip_distance - base_distance) / base_distance
                # Normalize to 0-1 range
                normalized = np.clip(extension / 0.5, 0.0, 1.0)
                openness_values.append(normalized * weight)
            else:
                openness_values.append(0.0)

        # Weighted average
        weighted_openness = np.sum(openness_values) / np.sum(self.finger_weights)

        return float(np.clip(weighted_openness, 0.0, 1.0))

    def calculate_finger_curl(self, landmarks: np.ndarray, finger_index: int) -> float:
        """
        Calculate curl amount for a specific finger (0 = extended, 1 = curled)

        Args:
            landmarks: Hand landmarks array (21, 3)
            finger_index: 0=thumb, 1=index, 2=middle, 3=ring, 4=pinky

        Returns:
            Curl value between 0.0 and 1.0
        """
        if finger_index < 0 or finger_index >= len(self.FINGER_TIPS):
            return 0.0

        tip_idx = self.FINGER_TIPS[finger_index]
        base_idx = self.FINGER_BASES[finger_index]

        tip = landmarks[tip_idx]
        base = landmarks[base_idx]
        wrist = landmarks[self.WRIST]

        tip_distance = np.linalg.norm(tip - wrist)
        base_distance = np.linalg.norm(base - wrist)

        if base_distance > 0:
            extension = (tip_distance - base_distance) / base_distance
            curl = 1.0 - np.clip(extension / 0.5, 0.0, 1.0)
            return float(curl)

        return 0.0


class GestureSmoothing:
    """Applies temporal smoothing to gesture values"""

    def __init__(self, window_size: int = 5, alpha: float = 0.3):
        """
        Args:
            window_size: Size of moving average window
            alpha: Exponential smoothing factor (0-1, lower = more smoothing)
        """
        self.window_size = window_size
        self.alpha = alpha
        self.history: List[float] = []
        self.ema_value: Optional[float] = None

    def smooth_value(self, value: float, method: str = "ema") -> float:
        """
        Apply smoothing to a single value

        Args:
            value: Raw input value
            method: "ema" (exponential moving average) or "sma" (simple moving average)

        Returns:
            Smoothed value
        """
        if method == "ema":
            return self._exponential_moving_average(value)
        elif method == "sma":
            return self._simple_moving_average(value)
        else:
            return value

    def _exponential_moving_average(self, value: float) -> float:
        """Apply exponential moving average"""
        if self.ema_value is None:
            self.ema_value = value
        else:
            self.ema_value = self.alpha * value + (1 - self.alpha) * self.ema_value
        return self.ema_value

    def _simple_moving_average(self, value: float) -> float:
        """Apply simple moving average"""
        self.history.append(value)
        if len(self.history) > self.window_size:
            self.history.pop(0)
        return float(np.mean(self.history))

    def reset(self):
        """Reset smoothing state"""
        self.history.clear()
        self.ema_value = None


class HysteresisFilter:
    """Applies hysteresis to prevent rapid state oscillation"""

    def __init__(self, low_threshold: float, high_threshold: float):
        """
        Args:
            low_threshold: Lower threshold for state transition
            high_threshold: Upper threshold for state transition
        """
        self.low_threshold = low_threshold
        self.high_threshold = high_threshold
        self.state = False

    def update(self, value: float) -> bool:
        """
        Update hysteresis state based on value

        Args:
            value: Input value to compare against thresholds

        Returns:
            Current state after hysteresis
        """
        if self.state:
            # Currently high, check if we should go low
            if value < self.low_threshold:
                self.state = False
        else:
            # Currently low, check if we should go high
            if value > self.high_threshold:
                self.state = True

        return self.state

    def reset(self, initial_state: bool = False):
        """Reset to initial state"""
        self.state = initial_state


class GestureStateMachine:
    """State machine for gesture recognition and tracking"""

    def __init__(self):
        self.state = GestureState.IDLE
        self.previous_state = GestureState.IDLE
        self.state_entry_time = time.time()
        self.state_duration = 0.0

        # Minimum durations for state transitions (seconds)
        self.min_pinch_duration = 0.05
        self.min_open_duration = 0.1

        # State transition counters for debouncing
        self.pinch_counter = 0
        self.release_counter = 0
        self.debounce_threshold = 3

    def update(self, is_pinching: bool, openness: float) -> GestureState:
        """
        Update state machine based on current gesture inputs

        Args:
            is_pinching: Whether hand is currently pinching
            openness: Hand openness value (0-1)

        Returns:
            Current gesture state
        """
        current_time = time.time()
        self.state_duration = current_time - self.state_entry_time

        new_state = self._determine_new_state(is_pinching, openness)

        if new_state != self.state:
            self._transition_to(new_state)

        return self.state

    def _determine_new_state(self, is_pinching: bool, openness: float) -> GestureState:
        """Determine next state based on current inputs"""

        if self.state == GestureState.IDLE:
            if is_pinching:
                self.pinch_counter += 1
                if self.pinch_counter >= self.debounce_threshold:
                    return GestureState.PINCH_START
            else:
                self.pinch_counter = 0
                if openness > 0.7:
                    return GestureState.OPEN_HAND

        elif self.state == GestureState.PINCH_START:
            if is_pinching and self.state_duration >= self.min_pinch_duration:
                return GestureState.PINCH_HOLD
            elif not is_pinching:
                return GestureState.IDLE

        elif self.state == GestureState.PINCH_HOLD:
            if not is_pinching:
                self.release_counter += 1
                if self.release_counter >= self.debounce_threshold:
                    return GestureState.PINCH_RELEASE
            else:
                self.release_counter = 0

        elif self.state == GestureState.PINCH_RELEASE:
            if self.state_duration >= 0.1:
                if openness > 0.7:
                    return GestureState.OPEN_HAND
                else:
                    return GestureState.IDLE

        elif self.state == GestureState.OPEN_HAND:
            if is_pinching:
                return GestureState.PINCH_START
            elif openness < 0.5:
                return GestureState.IDLE

        return self.state

    def _transition_to(self, new_state: GestureState):
        """Transition to a new state"""
        self.previous_state = self.state
        self.state = new_state
        self.state_entry_time = time.time()
        self.state_duration = 0.0
        self.pinch_counter = 0
        self.release_counter = 0

    def get_state_info(self) -> dict:
        """Get current state information"""
        return {
            "state": self.state.value,
            "previous_state": self.previous_state.value,
            "duration": self.state_duration,
            "entry_time": self.state_entry_time
        }

    def reset(self):
        """Reset state machine to initial state"""
        self.state = GestureState.IDLE
        self.previous_state = GestureState.IDLE
        self.state_entry_time = time.time()
        self.state_duration = 0.0
        self.pinch_counter = 0
        self.release_counter = 0


class GestureRecognizer:
    """Main gesture recognition system integrating all components"""

    def __init__(self):
        self.pinch_detector = PinchDetector(
            pinch_threshold=0.04,
            release_threshold=0.06
        )
        self.openness_calculator = OpennessCalculator()
        self.state_machine = GestureStateMachine()

        # Separate smoothing for different metrics
        self.openness_smoother = GestureSmoothing(window_size=5, alpha=0.3)
        self.pinch_distance_smoother = GestureSmoothing(window_size=3, alpha=0.4)

        # Hysteresis for openness state
        self.openness_hysteresis = HysteresisFilter(
            low_threshold=0.5,
            high_threshold=0.7
        )

        # Gesture data
        self.current_openness = 0.0
        self.current_pinch_distance = 0.0
        self.pinch_point = None
        self.is_pinching = False

    def process_hand(self, landmarks: np.ndarray) -> dict:
        """
        Process hand landmarks and update gesture state

        Args:
            landmarks: Hand landmarks array (21, 3)

        Returns:
            Dictionary containing gesture information
        """
        # Calculate raw values
        raw_openness = self.openness_calculator.calculate_openness(landmarks)
        raw_pinch_distance = self.pinch_detector.calculate_pinch_distance(landmarks)

        # Apply smoothing
        self.current_openness = self.openness_smoother.smooth_value(raw_openness, method="ema")
        self.current_pinch_distance = self.pinch_distance_smoother.smooth_value(
            raw_pinch_distance, method="ema"
        )

        # Detect pinching with hysteresis
        self.is_pinching = self.pinch_detector.is_pinching(
            landmarks,
            self.state_machine.state
        )

        # Update state machine
        gesture_state = self.state_machine.update(self.is_pinching, self.current_openness)

        # Calculate pinch point if pinching
        if self.is_pinching:
            self.pinch_point = self.pinch_detector.get_pinch_point(landmarks)
        else:
            self.pinch_point = None

        # Compile gesture data
        gesture_data = {
            "state": gesture_state.value,
            "openness": self.current_openness,
            "is_pinching": self.is_pinching,
            "pinch_distance": self.current_pinch_distance,
            "pinch_point": self.pinch_point.tolist() if self.pinch_point is not None else None,
            "state_info": self.state_machine.get_state_info(),
            "raw_openness": raw_openness,
            "raw_pinch_distance": raw_pinch_distance
        }

        return gesture_data

    def reset(self):
        """Reset all gesture tracking state"""
        self.state_machine.reset()
        self.openness_smoother.reset()
        self.pinch_distance_smoother.reset()
        self.openness_hysteresis.reset()
        self.current_openness = 0.0
        self.current_pinch_distance = 0.0
        self.pinch_point = None
        self.is_pinching = False


# Utility functions for visualization and debugging

def get_gesture_color(state: GestureState) -> Tuple[int, int, int]:
    """Get BGR color for visualizing gesture state"""
    color_map = {
        GestureState.IDLE: (128, 128, 128),  # Gray
        GestureState.PINCH_START: (0, 255, 255),  # Yellow
        GestureState.PINCH_HOLD: (0, 140, 255),  # Orange
        GestureState.PINCH_RELEASE: (255, 0, 255),  # Magenta
        GestureState.OPEN_HAND: (0, 255, 0)  # Green
    }
    return color_map.get(state, (255, 255, 255))


def format_gesture_info(gesture_data: dict) -> List[str]:
    """Format gesture data for display"""
    lines = [
        f"State: {gesture_data['state']}",
        f"Openness: {gesture_data['openness']:.2f}",
        f"Pinching: {'Yes' if gesture_data['is_pinching'] else 'No'}",
        f"Pinch Dist: {gesture_data['pinch_distance']:.3f}",
        f"Duration: {gesture_data['state_info']['duration']:.2f}s"
    ]
    return lines
