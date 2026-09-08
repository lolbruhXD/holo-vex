"""
Two-Hand Interaction System
Implements two-hand scaling, rotation, and smooth fallback to single-hand control
Integrates with existing gesture recognition system
"""

import numpy as np
from typing import Optional, Tuple, Dict
from dataclasses import dataclass
from enum import Enum
import time


class InteractionMode(Enum):
    """Interaction mode based on detected hands"""
    NONE = "none"
    SINGLE_HAND = "single_hand"
    TWO_HAND = "two_hand"
    TRANSITIONING = "transitioning"


@dataclass
class HandState:
    """State for a single hand"""
    landmarks: np.ndarray  # Shape: (21, 3)
    handedness: str  # "Left" or "Right"
    pinch_point: Optional[np.ndarray]  # 3D coordinates
    is_pinching: bool
    timestamp: float


@dataclass
class TwoHandState:
    """State for two-hand interaction"""
    left_hand: Optional[HandState]
    right_hand: Optional[HandState]
    distance: float  # Distance between hands
    midpoint: np.ndarray  # Center point between hands
    angle: float  # Rotation angle in radians
    timestamp: float


class TwoHandTransform:
    """Calculates scale and rotation from two-hand gestures"""

    def __init__(self):
        self.initial_distance: Optional[float] = None
        self.initial_angle: Optional[float] = None
        self.current_scale = 1.0
        self.current_rotation = 0.0

    def calculate_distance(self, point1: np.ndarray, point2: np.ndarray) -> float:
        """
        Calculate Euclidean distance between two 3D points

        Args:
            point1: First 3D point
            point2: Second 3D point

        Returns:
            Distance between points
        """
        return float(np.linalg.norm(point2 - point1))

    def calculate_midpoint(self, point1: np.ndarray, point2: np.ndarray) -> np.ndarray:
        """
        Calculate midpoint between two points

        Args:
            point1: First 3D point
            point2: Second 3D point

        Returns:
            Midpoint coordinates
        """
        return (point1 + point2) / 2.0

    def calculate_angle(self, point1: np.ndarray, point2: np.ndarray) -> float:
        """
        Calculate angle of line connecting two points (in XY plane)

        Args:
            point1: First 3D point
            point2: Second 3D point

        Returns:
            Angle in radians
        """
        delta = point2 - point1
        return float(np.arctan2(delta[1], delta[0]))

    def initialize(self, left_point: np.ndarray, right_point: np.ndarray):
        """
        Initialize transform with initial two-hand pose

        Args:
            left_point: Left hand position
            right_point: Right hand position
        """
        self.initial_distance = self.calculate_distance(left_point, right_point)
        self.initial_angle = self.calculate_angle(left_point, right_point)
        self.current_scale = 1.0
        self.current_rotation = 0.0

    def update(self, left_point: np.ndarray, right_point: np.ndarray) -> Tuple[float, float, np.ndarray]:
        """
        Update scale and rotation based on current hand positions

        Args:
            left_point: Current left hand position
            right_point: Current right hand position

        Returns:
            Tuple of (scale, rotation_radians, midpoint)
        """
        current_distance = self.calculate_distance(left_point, right_point)
        current_angle = self.calculate_angle(left_point, right_point)
        midpoint = self.calculate_midpoint(left_point, right_point)

        if self.initial_distance is not None and self.initial_distance > 0:
            self.current_scale = current_distance / self.initial_distance
        else:
            self.current_scale = 1.0

        if self.initial_angle is not None:
            self.current_rotation = current_angle - self.initial_angle
        else:
            self.current_rotation = 0.0

        return self.current_scale, self.current_rotation, midpoint

    def reset(self):
        """Reset transform to initial state"""
        self.initial_distance = None
        self.initial_angle = None
        self.current_scale = 1.0
        self.current_rotation = 0.0


class TransitionSmoother:
    """Smooths transitions between interaction modes"""

    def __init__(self, blend_duration: float = 0.3):
        """
        Args:
            blend_duration: Time in seconds to blend between modes
        """
        self.blend_duration = blend_duration
        self.transition_start_time: Optional[float] = None
        self.is_transitioning = False

        # Values to blend from
        self.blend_from_scale = 1.0
        self.blend_from_rotation = 0.0

    def start_transition(self, current_scale: float, current_rotation: float):
        """
        Begin a transition from current values

        Args:
            current_scale: Scale to blend from
            current_rotation: Rotation to blend from
        """
        self.transition_start_time = time.time()
        self.is_transitioning = True
        self.blend_from_scale = current_scale
        self.blend_from_rotation = current_rotation

    def get_blend_factor(self) -> float:
        """
        Calculate current blend factor (0 = start, 1 = end)

        Returns:
            Blend factor between 0 and 1
        """
        if not self.is_transitioning or self.transition_start_time is None:
            return 1.0

        elapsed = time.time() - self.transition_start_time
        factor = min(elapsed / self.blend_duration, 1.0)

        if factor >= 1.0:
            self.is_transitioning = False

        # Smooth easing function (ease-out cubic)
        return 1.0 - pow(1.0 - factor, 3.0)

    def blend_values(self, target_scale: float, target_rotation: float) -> Tuple[float, float]:
        """
        Blend from stored values to target values

        Args:
            target_scale: Target scale value
            target_rotation: Target rotation value

        Returns:
            Tuple of (blended_scale, blended_rotation)
        """
        if not self.is_transitioning:
            return target_scale, target_rotation

        blend = self.get_blend_factor()

        scale = self.blend_from_scale + (target_scale - self.blend_from_scale) * blend
        rotation = self.blend_from_rotation + (target_rotation - self.blend_from_rotation) * blend

        return scale, rotation

    def reset(self):
        """Reset transition state"""
        self.transition_start_time = None
        self.is_transitioning = False


class TwoHandInteractionSystem:
    """Main two-hand interaction system"""

    def __init__(self,
                 mode_switch_threshold: float = 0.5,
                 min_hand_distance: float = 0.05,
                 max_hand_distance: float = 1.5):
        """
        Args:
            mode_switch_threshold: Time in seconds before switching modes
            min_hand_distance: Minimum valid distance between hands
            max_hand_distance: Maximum valid distance between hands
        """
        self.mode = InteractionMode.NONE
        self.previous_mode = InteractionMode.NONE

        self.transform = TwoHandTransform()
        self.smoother = TransitionSmoother(blend_duration=0.3)

        self.mode_switch_threshold = mode_switch_threshold
        self.min_hand_distance = min_hand_distance
        self.max_hand_distance = max_hand_distance

        # Mode timing
        self.mode_change_time: Optional[float] = None
        self.pending_mode: Optional[InteractionMode] = None

        # Current state
        self.current_two_hand_state: Optional[TwoHandState] = None
        self.active_single_hand: Optional[str] = None  # "Left" or "Right"

        # Output values
        self.scale = 1.0
        self.rotation = 0.0
        self.control_point = np.array([0.5, 0.5, 0.0])

    def update(self,
               left_hand: Optional[HandState],
               right_hand: Optional[HandState]) -> Dict:
        """
        Update interaction system with current hand states

        Args:
            left_hand: Left hand state (None if not detected)
            right_hand: Right hand state (None if not detected)

        Returns:
            Dictionary containing interaction data
        """
        # Determine target mode
        target_mode = self._determine_target_mode(left_hand, right_hand)

        # Handle mode switching with delay
        if target_mode != self.mode:
            self._handle_mode_switch(target_mode)

        # Process based on current mode
        if self.mode == InteractionMode.TWO_HAND:
            self._process_two_hand(left_hand, right_hand)
        elif self.mode == InteractionMode.SINGLE_HAND:
            self._process_single_hand(left_hand, right_hand)
        elif self.mode == InteractionMode.NONE:
            self._process_no_hands()

        return self._compile_interaction_data()

    def _determine_target_mode(self,
                               left_hand: Optional[HandState],
                               right_hand: Optional[HandState]) -> InteractionMode:
        """Determine which interaction mode should be active"""

        # Both hands pinching = two-hand mode
        if (left_hand and left_hand.is_pinching and
            right_hand and right_hand.is_pinching and
            left_hand.pinch_point is not None and
            right_hand.pinch_point is not None):

            # Validate hand distance
            distance = np.linalg.norm(right_hand.pinch_point - left_hand.pinch_point)
            if self.min_hand_distance <= distance <= self.max_hand_distance:
                return InteractionMode.TWO_HAND

        # One hand pinching = single-hand mode
        if ((left_hand and left_hand.is_pinching) or
            (right_hand and right_hand.is_pinching)):
            return InteractionMode.SINGLE_HAND

        # No hands = no interaction
        return InteractionMode.NONE

    def _handle_mode_switch(self, target_mode: InteractionMode):
        """Handle mode switching with threshold delay"""
        current_time = time.time()

        # Check if we're already waiting for this mode
        if self.pending_mode == target_mode:
            # Check if threshold time has passed
            if (self.mode_change_time and
                current_time - self.mode_change_time >= self.mode_switch_threshold):
                self._switch_to_mode(target_mode)
        else:
            # New pending mode
            self.pending_mode = target_mode
            self.mode_change_time = current_time

            # If threshold is zero, switch immediately
            if self.mode_switch_threshold == 0.0:
                self._switch_to_mode(target_mode)

    def _switch_to_mode(self, new_mode: InteractionMode):
        """Execute mode switch"""
        self.previous_mode = self.mode
        self.mode = new_mode
        self.pending_mode = None

        # Handle mode-specific transitions
        if new_mode == InteractionMode.TWO_HAND:
            # Starting two-hand interaction
            self.transform.reset()
        elif new_mode == InteractionMode.SINGLE_HAND and self.previous_mode == InteractionMode.TWO_HAND:
            # Falling back from two-hand to single-hand
            self.smoother.start_transition(self.scale, self.rotation)
        elif new_mode == InteractionMode.NONE:
            # Releasing all interaction
            self.smoother.start_transition(self.scale, self.rotation)

    def _process_two_hand(self, left_hand: HandState, right_hand: HandState):
        """Process two-hand interaction"""
        if not left_hand or not right_hand:
            return

        if left_hand.pinch_point is None or right_hand.pinch_point is None:
            return

        # Initialize on first frame
        if self.transform.initial_distance is None:
            self.transform.initialize(left_hand.pinch_point, right_hand.pinch_point)

        # Update transform
        scale, rotation, midpoint = self.transform.update(
            left_hand.pinch_point,
            right_hand.pinch_point
        )

        # Apply smoothing if transitioning
        if self.smoother.is_transitioning:
            scale, rotation = self.smoother.blend_values(scale, rotation)

        self.scale = scale
        self.rotation = rotation
        self.control_point = midpoint

        # Store two-hand state
        distance = np.linalg.norm(right_hand.pinch_point - left_hand.pinch_point)
        angle = self.transform.calculate_angle(left_hand.pinch_point, right_hand.pinch_point)

        self.current_two_hand_state = TwoHandState(
            left_hand=left_hand,
            right_hand=right_hand,
            distance=distance,
            midpoint=midpoint,
            angle=angle,
            timestamp=time.time()
        )

    def _process_single_hand(self,
                            left_hand: Optional[HandState],
                            right_hand: Optional[HandState]):
        """Process single-hand interaction"""
        active_hand = None

        if left_hand and left_hand.is_pinching:
            active_hand = left_hand
            self.active_single_hand = "Left"
        elif right_hand and right_hand.is_pinching:
            active_hand = right_hand
            self.active_single_hand = "Right"

        if active_hand and active_hand.pinch_point is not None:
            self.control_point = active_hand.pinch_point

            # Smoothly transition scale and rotation back to neutral
            if self.smoother.is_transitioning:
                self.scale, self.rotation = self.smoother.blend_values(1.0, 0.0)
            else:
                self.scale = 1.0
                self.rotation = 0.0

        self.current_two_hand_state = None

    def _process_no_hands(self):
        """Process no active hands"""
        # Smoothly transition back to neutral
        if self.smoother.is_transitioning:
            self.scale, self.rotation = self.smoother.blend_values(1.0, 0.0)
        else:
            self.scale = 1.0
            self.rotation = 0.0

        self.active_single_hand = None
        self.current_two_hand_state = None

    def _compile_interaction_data(self) -> Dict:
        """Compile all interaction data for output"""
        data = {
            "mode": self.mode.value,
            "previous_mode": self.previous_mode.value,
            "pending_mode": self.pending_mode.value if self.pending_mode else None,
            "is_transitioning": self.smoother.is_transitioning,
            "scale": self.scale,
            "rotation": self.rotation,
            "rotation_degrees": np.degrees(self.rotation),
            "control_point": self.control_point.tolist(),
            "active_single_hand": self.active_single_hand,
        }

        if self.current_two_hand_state:
            data["two_hand_state"] = {
                "distance": self.current_two_hand_state.distance,
                "midpoint": self.current_two_hand_state.midpoint.tolist(),
                "angle": self.current_two_hand_state.angle,
                "angle_degrees": np.degrees(self.current_two_hand_state.angle),
            }

        return data

    def reset(self):
        """Reset interaction system"""
        self.mode = InteractionMode.NONE
        self.previous_mode = InteractionMode.NONE
        self.pending_mode = None
        self.transform.reset()
        self.smoother.reset()
        self.scale = 1.0
        self.rotation = 0.0
        self.control_point = np.array([0.5, 0.5, 0.0])
        self.active_single_hand = None
        self.current_two_hand_state = None


# Utility functions

def format_interaction_info(interaction_data: Dict) -> list:
    """Format interaction data for display"""
    lines = [
        f"Mode: {interaction_data['mode']}",
        f"Scale: {interaction_data['scale']:.2f}x",
        f"Rotation: {interaction_data['rotation_degrees']:.1f}°",
        f"Control: [{interaction_data['control_point'][0]:.2f}, "
        f"{interaction_data['control_point'][1]:.2f}, "
        f"{interaction_data['control_point'][2]:.2f}]",
    ]

    if interaction_data.get('active_single_hand'):
        lines.append(f"Active Hand: {interaction_data['active_single_hand']}")

    if interaction_data.get('is_transitioning'):
        lines.append("Status: Transitioning")

    if 'two_hand_state' in interaction_data:
        two_hand = interaction_data['two_hand_state']
        lines.append(f"Hand Distance: {two_hand['distance']:.3f}")

    return lines


# Alias for backward compatibility
TwoHandInteraction = TwoHandInteractionSystem
