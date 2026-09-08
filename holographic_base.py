"""
Base class for holographic objects with common properties and behaviors.
"""

import numpy as np
from typing import Tuple, Optional, Dict
from enum import Enum


class Theme(Enum):
    """Color themes for holographic objects."""
    CYAN = "cyan"
    EMERALD = "emerald"
    AMBER = "amber"
    VIOLET = "violet"
    CRIMSON = "crimson"


class HolographicObject:
    """
    Base class for all holographic objects.

    Provides common functionality for position, scale, rotation,
    interaction handling, and theme-aware rendering.
    """

    # Theme color palettes (RGB, 0-255)
    THEME_COLORS = {
        Theme.CYAN: {
            'primary': (56, 189, 248),      # Bright cyan
            'secondary': (14, 165, 233),    # Deep cyan
            'accent': (186, 230, 253),      # Light cyan
            'glow': (56, 189, 248)          # Cyan glow
        },
        Theme.EMERALD: {
            'primary': (110, 231, 183),     # Bright emerald
            'secondary': (52, 211, 153),    # Deep emerald
            'accent': (209, 250, 229),      # Light emerald
            'glow': (110, 231, 183)         # Emerald glow
        },
        Theme.AMBER: {
            'primary': (233, 165, 104),     # Bright amber
            'secondary': (251, 146, 60),    # Deep amber
            'accent': (254, 215, 170),      # Light amber
            'glow': (233, 165, 104)         # Amber glow
        },
        Theme.VIOLET: {
            'primary': (167, 139, 250),     # Bright violet
            'secondary': (139, 92, 246),    # Deep violet
            'accent': (221, 214, 254),      # Light violet
            'glow': (167, 139, 250)         # Violet glow
        },
        Theme.CRIMSON: {
            'primary': (244, 114, 182),     # Bright crimson
            'secondary': (236, 72, 153),    # Deep crimson
            'accent': (252, 231, 243),      # Light crimson
            'glow': (244, 114, 182)         # Crimson glow
        }
    }

    def __init__(
        self,
        position: Tuple[float, float, float] = (0.0, 0.0, 0.0),
        scale: float = 1.0,
        rotation: Tuple[float, float, float] = (0.0, 0.0, 0.0),
        theme: Theme = Theme.CYAN
    ):
        """
        Initialize holographic object.

        Args:
            position: (x, y, z) position in 3D space
            scale: Uniform scale factor
            rotation: (pitch, yaw, roll) rotation in degrees
            theme: Color theme
        """
        self.position = np.array(position, dtype=np.float32)
        self.scale = scale
        self.rotation = np.array(rotation, dtype=np.float32)
        self.theme = theme

        # Interaction state
        self.is_grabbed = False
        self.is_hovered = False
        self.grab_offset = np.zeros(3, dtype=np.float32)

        # Animation state
        self.time = 0.0
        self.pulse_phase = 0.0
        self.rotation_speed = np.array([0.0, 0.0, 0.0], dtype=np.float32)

        # Visual properties
        self.opacity = 1.0
        self.glow_intensity = 1.0
        self.particle_emission_rate = 1.0

    def get_colors(self) -> Dict[str, Tuple[int, int, int]]:
        """Get current theme colors."""
        return self.THEME_COLORS[self.theme]

    def set_theme(self, theme: Theme):
        """Change the color theme."""
        self.theme = theme

    def set_position(self, x: float, y: float, z: float):
        """Set object position."""
        self.position = np.array([x, y, z], dtype=np.float32)

    def set_scale(self, scale: float):
        """Set object scale."""
        self.scale = max(0.1, scale)

    def set_rotation(self, pitch: float, yaw: float, roll: float):
        """Set object rotation in degrees."""
        self.rotation = np.array([pitch, yaw, roll], dtype=np.float32)

    def rotate(self, dpitch: float, dyaw: float, droll: float):
        """Rotate object by delta angles."""
        self.rotation += np.array([dpitch, dyaw, droll], dtype=np.float32)
        self.rotation %= 360.0

    def translate(self, dx: float, dy: float, dz: float):
        """Move object by delta."""
        self.position += np.array([dx, dy, dz], dtype=np.float32)

    def distance_to_point(self, point: np.ndarray) -> float:
        """Calculate distance from object center to a point."""
        return np.linalg.norm(self.position - point)

    def grab(self, grab_point: np.ndarray):
        """
        Grab the object at a specific point.

        Args:
            grab_point: 3D point where object is grabbed
        """
        self.is_grabbed = True
        self.grab_offset = self.position - grab_point

    def release(self):
        """Release the object from grab."""
        self.is_grabbed = False
        self.grab_offset = np.zeros(3, dtype=np.float32)

    def move_to_grab_point(self, grab_point: np.ndarray):
        """
        Move object while grabbed.

        Args:
            grab_point: Current grab point position
        """
        if self.is_grabbed:
            self.position = grab_point + self.grab_offset

    def check_hover(self, point: np.ndarray, threshold: float = 100.0) -> bool:
        """
        Check if a point is hovering near the object.

        Args:
            point: 3D point to check
            threshold: Distance threshold for hover detection

        Returns:
            True if point is within hover threshold
        """
        distance = self.distance_to_point(point)
        self.is_hovered = distance < threshold
        return self.is_hovered

    def update(self, dt: float):
        """
        Update object state.

        Args:
            dt: Delta time in seconds
        """
        self.time += dt

        # Update pulse animation
        self.pulse_phase = (self.pulse_phase + dt * 2.0) % (2 * np.pi)

        # Auto-rotation
        self.rotation += self.rotation_speed * dt
        self.rotation %= 360.0

        # Interaction effects
        if self.is_grabbed:
            self.glow_intensity = 1.5
            self.particle_emission_rate = 2.0
        elif self.is_hovered:
            self.glow_intensity = 1.2
            self.particle_emission_rate = 1.5
        else:
            # Smooth return to default
            self.glow_intensity = self.glow_intensity * 0.95 + 1.0 * 0.05
            self.particle_emission_rate = self.particle_emission_rate * 0.95 + 1.0 * 0.05

    def render(self, frame: np.ndarray, camera_matrix: Optional[np.ndarray] = None):
        """
        Render the object to a frame.

        Args:
            frame: BGR image to render onto
            camera_matrix: Optional camera projection matrix
        """
        raise NotImplementedError("Subclasses must implement render()")

    def get_screen_position(
        self,
        frame_width: int,
        frame_height: int
    ) -> Tuple[int, int]:
        """
        Convert 3D position to 2D screen coordinates.

        Simple orthographic projection for now.

        Args:
            frame_width: Screen width in pixels
            frame_height: Screen height in pixels

        Returns:
            (x, y) screen coordinates
        """
        # Normalize position to [0, 1]
        x_norm = self.position[0]
        y_norm = self.position[1]

        # Convert to pixel coordinates
        x_px = int(x_norm * frame_width)
        y_px = int(y_norm * frame_height)

        return (x_px, y_px)

    def __repr__(self) -> str:
        return (
            f"{self.__class__.__name__}("
            f"pos={self.position}, "
            f"scale={self.scale:.2f}, "
            f"theme={self.theme.value})"
        )
