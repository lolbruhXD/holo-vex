"""
Lighting System - Dynamic lighting for holographic objects.
"""
import numpy as np
import cv2


class LightingSystem:
    """Dynamic lighting system with intensity, direction, and color control."""

    def __init__(self):
        self.intensity = 1.0
        self.direction = np.array([0.0, -1.0, 1.0])  # Default from top-right
        self.direction = self.direction / np.linalg.norm(self.direction)
        self.color = (255, 255, 255)
        self.ambient = 0.3

        # Dynamic effects
        self.hand_proximity_boost = 0.0
        self.pinch_boost = 0.0
        self.movement_boost = 0.0

        # Animation
        self.time = 0.0

    def set_intensity(self, intensity):
        """Set global light intensity (0.0 to 2.0)."""
        self.intensity = max(0.0, min(2.0, intensity))

    def set_direction(self, direction):
        """Set light direction vector."""
        self.direction = np.array(direction, dtype=np.float32)
        norm = np.linalg.norm(self.direction)
        if norm > 0:
            self.direction /= norm

    def set_color(self, color):
        """Set light color (RGB tuple)."""
        self.color = color

    def set_theme_color(self, theme_color):
        """Set light color from theme."""
        self.color = theme_color

    def update_hand_proximity(self, distance, max_distance=200):
        """Update lighting based on hand proximity."""
        if distance < max_distance:
            self.hand_proximity_boost = 1.0 - (distance / max_distance)
        else:
            self.hand_proximity_boost = 0.0

    def update_pinch_state(self, is_pinching):
        """Update lighting based on pinch gesture."""
        target = 1.0 if is_pinching else 0.0
        self.pinch_boost += (target - self.pinch_boost) * 0.2

    def update_movement(self, velocity_magnitude, max_velocity=10.0):
        """Update lighting based on object movement speed."""
        self.movement_boost = min(1.0, velocity_magnitude / max_velocity)

    def update(self, dt=0.016):
        """Update lighting animations."""
        self.time += dt

        # Subtle orbital rotation of light direction
        angle = self.time * 0.5
        self.direction = np.array([
            np.cos(angle),
            -0.5,
            np.sin(angle)
        ])
        self.direction = self.direction / np.linalg.norm(self.direction)

    def get_effective_intensity(self):
        """Get current effective light intensity with all boosts."""
        base = self.intensity
        boost = (self.hand_proximity_boost * 0.3 +
                self.pinch_boost * 0.5 +
                self.movement_boost * 0.2)
        return base * (1.0 + boost)

    def apply_to_frame(self, frame, center, radius):
        """Apply lighting overlay to frame region."""
        intensity = self.get_effective_intensity()

        # Create radial gradient based on light direction
        h, w = frame.shape[:2]
        cx, cy = center

        # Light source position (offset from center)
        light_offset = 200
        lx = cx + int(self.direction[0] * light_offset)
        ly = cy + int(self.direction[1] * light_offset)

        # Create gradient mask
        y, x = np.ogrid[:h, :w]
        dist_from_light = np.sqrt((x - lx)**2 + (y - ly)**2)
        dist_from_center = np.sqrt((x - cx)**2 + (y - cy)**2)

        # Combine distance from light and center
        mask = np.exp(-dist_from_center / (radius * 2))
        light_mask = np.exp(-dist_from_light / (radius * 3))
        combined = mask * light_mask

        # Apply color tint
        overlay = np.zeros_like(frame, dtype=np.uint8)
        overlay[:, :] = self.color
        overlay = (overlay * combined[:, :, np.newaxis]).astype(np.uint8)

        # Blend with frame
        alpha = intensity * 0.15
        cv2.addWeighted(overlay, alpha, frame, 1.0, 0, frame)

    def create_glow(self, frame, position, radius, intensity_mult=1.0):
        """Create a glow effect at a position."""
        x, y = position
        intensity = self.get_effective_intensity() * intensity_mult

        # Multi-layer glow
        for r_mult, opacity in [(3.0, 0.08), (2.0, 0.15), (1.0, 0.3)]:
            r = int(radius * r_mult)
            overlay = frame.copy()
            cv2.circle(overlay, (x, y), r, self.color, -1, cv2.LINE_AA)
            cv2.addWeighted(overlay, opacity * intensity, frame, 1 - opacity * intensity, 0, frame)

    def create_directional_highlight(self, frame, center, radius, normal):
        """Create directional highlight based on surface normal."""
        # Calculate dot product between light direction and normal
        dot = np.dot(self.direction, normal)
        if dot <= 0:
            return  # Light coming from behind

        intensity = self.get_effective_intensity() * dot

        # Create highlight
        x, y = center
        r = int(radius * 0.6)
        overlay = frame.copy()
        cv2.circle(overlay, (x, y), r, self.color, -1, cv2.LINE_AA)
        cv2.addWeighted(overlay, intensity * 0.2, frame, 1 - intensity * 0.2, 0, frame)
