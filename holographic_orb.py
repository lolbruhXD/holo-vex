"""
Holographic ORB object with impressive visual effects.

Features:
- Glowing core with radial gradients
- Bloom effect
- Translucent shell with Fresnel-like edge highlighting
- Particle system with orbital motion
- Energy rings that pulse and rotate
- Theme-aware colors
- Interactive response to hand proximity and grabbing
"""

import cv2
import numpy as np
from typing import Tuple, Optional, List
from holographic_base import HolographicObject, Theme


class Particle:
    """Single particle for orb particle effects."""

    def __init__(
        self,
        position: np.ndarray,
        velocity: np.ndarray,
        lifetime: float,
        size: float,
        color: Tuple[int, int, int]
    ):
        self.position = position.copy()
        self.velocity = velocity.copy()
        self.lifetime = lifetime
        self.max_lifetime = lifetime
        self.size = size
        self.color = color
        self.orbit_angle = np.random.uniform(0, 2 * np.pi)
        self.orbit_radius = np.random.uniform(20, 80)
        self.orbit_speed = np.random.uniform(1.0, 3.0)

    def update(self, dt: float, center: np.ndarray):
        """Update particle position."""
        self.lifetime -= dt

        # Orbital motion around center
        self.orbit_angle += self.orbit_speed * dt
        orbit_x = center[0] + self.orbit_radius * np.cos(self.orbit_angle)
        orbit_y = center[1] + self.orbit_radius * np.sin(self.orbit_angle)

        # Blend between velocity motion and orbital motion
        orbit_influence = 0.7
        self.position[0] = (1 - orbit_influence) * (self.position[0] + self.velocity[0] * dt) + orbit_influence * orbit_x
        self.position[1] = (1 - orbit_influence) * (self.position[1] + self.velocity[1] * dt) + orbit_influence * orbit_y

        # Fade velocity
        self.velocity *= 0.98

    def is_alive(self) -> bool:
        """Check if particle is still alive."""
        return self.lifetime > 0

    def get_alpha(self) -> float:
        """Get particle alpha based on lifetime."""
        return max(0.0, min(1.0, self.lifetime / self.max_lifetime))


class EnergyRing:
    """Rotating energy ring around the orb."""

    def __init__(
        self,
        radius: float,
        thickness: float,
        rotation_speed: float,
        color: Tuple[int, int, int]
    ):
        self.radius = radius
        self.thickness = thickness
        self.rotation_speed = rotation_speed
        self.angle = np.random.uniform(0, 2 * np.pi)
        self.color = color
        self.pulse_phase = np.random.uniform(0, 2 * np.pi)

    def update(self, dt: float):
        """Update ring rotation."""
        self.angle += self.rotation_speed * dt
        self.angle %= (2 * np.pi)
        self.pulse_phase += dt * 3.0
        self.pulse_phase %= (2 * np.pi)

    def get_pulse_scale(self) -> float:
        """Get pulsing scale factor."""
        return 1.0 + 0.15 * np.sin(self.pulse_phase)


class HolographicOrb(HolographicObject):
    """
    Impressive holographic orb with multiple visual layers:
    - Inner glowing core
    - Radial gradient shell
    - Bloom effect
    - Orbiting particles
    - Rotating energy rings
    - Edge highlighting (Fresnel effect)
    """

    def __init__(
        self,
        position: Tuple[float, float, float] = (0.5, 0.5, 0.0),
        scale: float = 1.0,
        base_radius: float = 60.0,
        theme: Theme = Theme.CYAN
    ):
        """
        Initialize holographic orb.

        Args:
            position: Normalized (x, y, z) position [0, 1]
            scale: Scale multiplier
            base_radius: Base radius in pixels
            theme: Color theme
        """
        super().__init__(position, scale, (0, 0, 0), theme)

        self.base_radius = base_radius
        self.particles: List[Particle] = []
        self.energy_rings: List[EnergyRing] = []

        # Visual layers
        self.core_radius_factor = 0.4
        self.shell_thickness = 0.3
        self.bloom_radius_factor = 1.8

        # Particle system
        self.particle_spawn_timer = 0.0
        self.particle_spawn_interval = 0.05  # seconds

        # Auto-rotation
        self.rotation_speed = np.array([0.0, 0.0, 20.0])  # Gentle roll

        # Initialize energy rings
        self._init_energy_rings()

    def _init_energy_rings(self):
        """Initialize energy rings around the orb."""
        colors = self.get_colors()

        self.energy_rings = [
            EnergyRing(
                radius=1.2,
                thickness=3.0,
                rotation_speed=1.5,
                color=colors['secondary']
            ),
            EnergyRing(
                radius=1.4,
                thickness=2.0,
                rotation_speed=-1.0,
                color=colors['accent']
            ),
            EnergyRing(
                radius=1.6,
                thickness=2.5,
                rotation_speed=0.8,
                color=colors['primary']
            )
        ]

    def get_effective_radius(self) -> float:
        """Get current radius including scale and pulse."""
        pulse = 1.0 + 0.08 * np.sin(self.pulse_phase)
        return self.base_radius * self.scale * pulse

    def set_theme(self, theme: Theme):
        """Change theme and update energy rings."""
        super().set_theme(theme)
        self._init_energy_rings()

    def spawn_particle(self, center: Tuple[int, int]):
        """Spawn a new particle."""
        colors = self.get_colors()

        # Random position near orb surface
        angle = np.random.uniform(0, 2 * np.pi)
        radius = self.get_effective_radius() * np.random.uniform(0.8, 1.1)
        px = center[0] + radius * np.cos(angle)
        py = center[1] + radius * np.sin(angle)

        position = np.array([px, py, 0.0], dtype=np.float32)

        # Velocity away from center (but will be overridden by orbital motion)
        velocity = np.array([
            np.cos(angle) * 10.0,
            np.sin(angle) * 10.0,
            0.0
        ], dtype=np.float32)

        # Random color from theme
        color_choice = np.random.choice(['primary', 'secondary', 'accent'])
        color = colors[color_choice]

        particle = Particle(
            position=position,
            velocity=velocity,
            lifetime=np.random.uniform(1.0, 2.5),
            size=np.random.uniform(2.0, 5.0),
            color=color
        )

        self.particles.append(particle)

    def update(self, dt: float):
        """Update orb state and effects."""
        super().update(dt)

        # Get screen position for particle spawning
        center = (int(self.position[0] * 640), int(self.position[1] * 480))

        # Spawn particles
        self.particle_spawn_timer += dt
        spawn_rate = self.particle_spawn_interval / self.particle_emission_rate

        while self.particle_spawn_timer >= spawn_rate:
            self.spawn_particle(center)
            self.particle_spawn_timer -= spawn_rate

        # Update particles
        self.particles = [p for p in self.particles if p.is_alive()]
        for particle in self.particles:
            particle.update(dt, np.array([center[0], center[1]], dtype=np.float32))

        # Update energy rings
        for ring in self.energy_rings:
            ring.update(dt)

        # Limit particle count
        max_particles = 150
        if len(self.particles) > max_particles:
            self.particles = self.particles[-max_particles:]

    def _draw_bloom(
        self,
        frame: np.ndarray,
        center: Tuple[int, int],
        radius: float,
        color: Tuple[int, int, int],
        intensity: float
    ):
        """Draw bloom/glow effect."""
        h, w = frame.shape[:2]
        bloom_overlay = np.zeros((h, w, 3), dtype=np.float32)

        bloom_radius = int(radius * self.bloom_radius_factor)

        # Multiple passes for soft bloom
        for i in range(3):
            current_radius = bloom_radius - i * 15
            if current_radius <= 0:
                break

            alpha = intensity * 0.15 * (1.0 - i * 0.3)
            cv2.circle(
                bloom_overlay,
                center,
                current_radius,
                color,
                -1,
                lineType=cv2.LINE_AA
            )

        # Blur for soft glow
        bloom_overlay = cv2.GaussianBlur(bloom_overlay, (51, 51), 0)

        # Add to frame with blending
        frame_float = frame.astype(np.float32)
        frame_float = cv2.add(frame_float, bloom_overlay * 0.8)
        np.clip(frame_float, 0, 255, out=frame_float)
        frame[:] = frame_float.astype(np.uint8)

    def _draw_core(
        self,
        frame: np.ndarray,
        center: Tuple[int, int],
        radius: float,
        color: Tuple[int, int, int]
    ):
        """Draw glowing core with radial gradient."""
        h, w = frame.shape[:2]
        overlay = np.zeros((h, w, 3), dtype=np.float32)

        core_radius = int(radius * self.core_radius_factor)

        # Bright center
        cv2.circle(
            overlay,
            center,
            core_radius,
            color,
            -1,
            lineType=cv2.LINE_AA
        )

        # Radial gradient layers
        gradient_steps = 8
        for i in range(gradient_steps):
            t = i / gradient_steps
            current_radius = int(core_radius + (radius - core_radius) * t)
            alpha = 1.0 - t ** 0.7

            color_scaled = tuple(int(c * alpha) for c in color)

            cv2.circle(
                overlay,
                center,
                current_radius,
                color_scaled,
                2,
                lineType=cv2.LINE_AA
            )

        # Blend onto frame
        frame_float = frame.astype(np.float32)
        frame_float = cv2.addWeighted(frame_float, 1.0, overlay, 0.9, 0)
        np.clip(frame_float, 0, 255, out=frame_float)
        frame[:] = frame_float.astype(np.uint8)

    def _draw_shell(
        self,
        frame: np.ndarray,
        center: Tuple[int, int],
        radius: float,
        color: Tuple[int, int, int]
    ):
        """Draw translucent shell with edge highlighting."""
        # Main shell circle
        shell_color = tuple(int(c * 0.4) for c in color)
        cv2.circle(
            frame,
            center,
            int(radius),
            shell_color,
            2,
            lineType=cv2.LINE_AA
        )

        # Edge highlight (Fresnel-like effect)
        highlight_color = tuple(int(c * 0.8) for c in color)
        cv2.circle(
            frame,
            center,
            int(radius) + 1,
            highlight_color,
            1,
            lineType=cv2.LINE_AA
        )

        # Inner edge glow
        inner_radius = int(radius * 0.92)
        cv2.circle(
            frame,
            center,
            inner_radius,
            shell_color,
            1,
            lineType=cv2.LINE_AA
        )

    def _draw_energy_rings(
        self,
        frame: np.ndarray,
        center: Tuple[int, int],
        base_radius: float
    ):
        """Draw rotating energy rings."""
        for ring in self.energy_rings:
            radius = int(base_radius * ring.radius * ring.get_pulse_scale())
            thickness = int(ring.thickness)

            # Draw ring as ellipse for 3D effect
            axes = (radius, int(radius * 0.3))
            angle = int(np.degrees(ring.angle))

            # Outer glow
            glow_color = tuple(int(c * 0.3) for c in ring.color)
            cv2.ellipse(
                frame,
                center,
                axes,
                angle,
                0,
                360,
                glow_color,
                thickness + 2,
                lineType=cv2.LINE_AA
            )

            # Main ring
            cv2.ellipse(
                frame,
                center,
                axes,
                angle,
                0,
                360,
                ring.color,
                thickness,
                lineType=cv2.LINE_AA
            )

    def _draw_particles(self, frame: np.ndarray):
        """Draw particle system."""
        for particle in self.particles:
            alpha = particle.get_alpha()
            if alpha <= 0:
                continue

            px, py = int(particle.position[0]), int(particle.position[1])

            # Check bounds
            h, w = frame.shape[:2]
            if px < 0 or px >= w or py < 0 or py >= h:
                continue

            # Color with alpha
            color_with_alpha = tuple(int(c * alpha) for c in particle.color)
            size = int(particle.size * alpha)

            # Draw particle with glow
            cv2.circle(
                frame,
                (px, py),
                size + 1,
                tuple(int(c * 0.5) for c in color_with_alpha),
                -1,
                lineType=cv2.LINE_AA
            )
            cv2.circle(
                frame,
                (px, py),
                size,
                color_with_alpha,
                -1,
                lineType=cv2.LINE_AA
            )

    def render(self, frame: np.ndarray, camera_matrix: Optional[np.ndarray] = None):
        """
        Render the holographic orb.

        Rendering order (back to front):
        1. Bloom/glow
        2. Energy rings
        3. Particles
        4. Shell
        5. Core
        """
        h, w = frame.shape[:2]
        center = self.get_screen_position(w, h)
        radius = self.get_effective_radius()
        colors = self.get_colors()

        # 1. Bloom effect (furthest back)
        self._draw_bloom(
            frame,
            center,
            radius,
            colors['glow'],
            self.glow_intensity
        )

        # 2. Energy rings
        self._draw_energy_rings(frame, center, radius)

        # 3. Particles
        self._draw_particles(frame)

        # 4. Translucent shell
        self._draw_shell(frame, center, radius, colors['primary'])

        # 5. Glowing core (front)
        self._draw_core(frame, center, radius, colors['primary'])

        # Interaction highlight
        if self.is_grabbed:
            # Bright pulse when grabbed
            pulse_color = tuple(int(c * 1.5) for c in colors['accent'])
            cv2.circle(
                frame,
                center,
                int(radius * 1.05),
                pulse_color,
                3,
                lineType=cv2.LINE_AA
            )
        elif self.is_hovered:
            # Subtle highlight when hovered
            hover_color = tuple(int(c * 0.8) for c in colors['accent'])
            cv2.circle(
                frame,
                center,
                int(radius * 1.03),
                hover_color,
                2,
                lineType=cv2.LINE_AA
            )

    def __repr__(self) -> str:
        return (
            f"HolographicOrb("
            f"pos={self.position}, "
            f"radius={self.get_effective_radius():.1f}, "
            f"particles={len(self.particles)}, "
            f"theme={self.theme.value})"
        )
