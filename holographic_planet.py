"""
Holographic Planet - Spherical body with atmospheric glow and orbit rings.
"""
import numpy as np
import cv2
from holographic_base import HolographicObject


class HolographicPlanet(HolographicObject):
    """Holographic planet with atmospheric glow, orbit rings, and surface detail."""

    def __init__(self, position=(320, 240), scale=80.0):
        super().__init__(position, scale)
        self.visible = True
        self.age = 0.0
        self.rotation = 0.0
        self.rotation_speed = 0.02

        # Theme system
        self.current_theme = 'cyan'
        self.themes = {
            'cyan': {
                'primary': (56, 189, 248),
                'secondary': (14, 165, 233),
                'accent': (186, 230, 253),
            },
            'purple': {
                'primary': (167, 139, 250),
                'secondary': (139, 92, 246),
                'accent': (221, 214, 254),
            },
            'green': {
                'primary': (110, 231, 183),
                'secondary': (52, 211, 153),
                'accent': (209, 250, 229),
            },
            'amber': {
                'primary': (233, 165, 104),
                'secondary': (251, 146, 60),
                'accent': (254, 215, 170),
            },
        }

        # Ring parameters
        self.rings = [
            {'radius': 1.5, 'width': 0.15, 'tilt': 0.3, 'speed': 0.015, 'phase': 0.0},
            {'radius': 1.8, 'width': 0.1, 'tilt': 0.3, 'speed': -0.01, 'phase': np.pi},
            {'radius': 2.1, 'width': 0.12, 'tilt': 0.3, 'speed': 0.012, 'phase': np.pi / 2},
        ]

        # Surface detail points
        self.surface_points = []
        self._init_surface_points()

        # Orbit particles
        self.orbit_particles = []
        self._init_orbit_particles()

    def _init_surface_points(self):
        """Initialize surface detail points using spherical coordinates."""
        num_points = 80
        for _ in range(num_points):
            theta = np.random.rand() * 2 * np.pi
            phi = np.random.rand() * np.pi
            brightness = 0.3 + np.random.rand() * 0.7
            size = np.random.randint(1, 3)
            self.surface_points.append({
                'theta': theta,
                'phi': phi,
                'brightness': brightness,
                'size': size,
            })

    def _init_orbit_particles(self):
        """Initialize particles in orbit around the planet."""
        num_particles = 100
        for _ in range(num_particles):
            ring_idx = np.random.randint(0, len(self.rings))
            ring = self.rings[ring_idx]
            angle = np.random.rand() * 2 * np.pi
            radius_offset = np.random.randn() * 0.05
            self.orbit_particles.append({
                'ring_idx': ring_idx,
                'angle': angle,
                'radius_offset': radius_offset,
                'size': np.random.randint(1, 3),
                'phase': np.random.rand() * 2 * np.pi,
            })

    def _spherical_to_2d(self, theta, phi, radius, rotation_offset=0.0):
        """Convert spherical coordinates to 2D screen position with rotation."""
        # Apply rotation
        theta_rot = theta + rotation_offset

        # Spherical to Cartesian
        x = radius * np.sin(phi) * np.cos(theta_rot)
        y = radius * np.cos(phi)
        z = radius * np.sin(phi) * np.sin(theta_rot)

        # Simple perspective projection
        scale_factor = 1.0 / (1.0 + z / (radius * 3))

        # Project to screen
        screen_x = int(self.position[0] + x * self.scale * scale_factor)
        screen_y = int(self.position[1] - y * self.scale * scale_factor)

        return screen_x, screen_y, z, scale_factor

    def update(self, dt=0.016):
        """Update planet rotation and animations."""
        super().update(dt)

        # Increment age
        self.age += dt

        # Rotate planet
        self.rotation += self.rotation_speed

        # Update rings
        for ring in self.rings:
            ring['phase'] += ring['speed']

        # Update orbit particles
        for p in self.orbit_particles:
            p['angle'] += self.rings[p['ring_idx']]['speed'] * 0.5
            p['phase'] += 0.03

    def render(self, frame):
        """Render the holographic planet with all effects."""
        if not self.visible:
            return

        # Render in order: far rings, planet body, near rings, particles
        self._render_rings(frame, far_only=True)
        self._render_planet_body(frame)
        self._render_rings(frame, near_only=True)
        self._render_orbit_particles(frame)

    def _render_planet_body(self, frame):
        """Render the planet sphere with atmospheric glow."""
        theme = self.themes[self.current_theme]
        x, y = int(self.position[0]), int(self.position[1])

        # Multi-layer atmospheric glow
        for radius_mult, opacity in [(1.5, 0.08), (1.3, 0.15), (1.1, 0.25)]:
            radius = int(self.scale * radius_mult)
            overlay = frame.copy()
            cv2.circle(overlay, (x, y), radius, theme['secondary'], -1, cv2.LINE_AA)
            cv2.addWeighted(overlay, opacity, frame, 1 - opacity, 0, frame)

        # Main planet body
        main_radius = int(self.scale)
        overlay = frame.copy()

        # Radial gradient for sphere
        for r in range(main_radius, 0, -2):
            intensity = (r / main_radius) ** 1.5
            opacity = 0.3 * intensity
            color = tuple(int(c * intensity) for c in theme['primary'])
            cv2.circle(overlay, (x, y), r, color, 2, cv2.LINE_AA)

        cv2.addWeighted(overlay, 0.6, frame, 0.4, 0, frame)

        # Surface details
        self._render_surface_details(frame)

        # Core glow
        core_radius = int(self.scale * 0.4)
        overlay = frame.copy()
        cv2.circle(overlay, (x, y), core_radius, theme['primary'], -1, cv2.LINE_AA)
        glow_intensity = 0.6 if self.is_grabbed else 0.4
        cv2.addWeighted(overlay, glow_intensity, frame, 1 - glow_intensity, 0, frame)

    def _render_surface_details(self, frame):
        """Render surface detail points on the planet."""
        theme = self.themes[self.current_theme]

        for point in self.surface_points:
            screen_x, screen_y, z, scale = self._spherical_to_2d(
                point['theta'], point['phi'], 1.0, self.rotation
            )

            # Only render front-facing points
            if z < 0:
                opacity = point['brightness'] * (1.0 - z / 1.0) * 0.6
                size = max(1, int(point['size'] * scale))

                overlay = frame.copy()
                cv2.circle(overlay, (screen_x, screen_y), size, theme['primary'], -1, cv2.LINE_AA)
                cv2.addWeighted(overlay, opacity, frame, 1 - opacity, 0, frame)

    def _render_rings(self, frame, far_only=False, near_only=False):
        """Render orbit rings around the planet."""
        theme = self.themes[self.current_theme]

        for ring in self.rings:
            # Determine if ring is far or near based on tilt phase
            is_far = np.sin(ring['phase']) < 0

            if far_only and not is_far:
                continue
            if near_only and is_far:
                continue

            self._render_single_ring(frame, ring, theme)

    def _render_single_ring(self, frame, ring, theme):
        """Render a single orbit ring with segmentation."""
        radius = int(ring['radius'] * self.scale)
        width = int(ring['width'] * self.scale)
        tilt = ring['tilt']

        # Create tilted ellipse
        center = (int(self.position[0]), int(self.position[1]))
        axes = (radius, int(radius * (1 - tilt)))
        angle = int(np.degrees(ring['phase']))

        # Segmented ring pattern
        num_segments = 60
        for i in range(num_segments):
            if i % 3 == 0:  # Create gaps
                continue

            start_angle = int(i * 360 / num_segments)
            end_angle = int((i + 1) * 360 / num_segments)

            # Depth-based opacity
            segment_angle_rad = np.radians(start_angle + angle)
            depth_factor = 0.3 + 0.7 * (0.5 + 0.5 * np.cos(segment_angle_rad))
            opacity = 0.15 * depth_factor

            if self.is_grabbed:
                opacity *= 1.5

            overlay = frame.copy()
            cv2.ellipse(overlay, center, axes, angle, start_angle, end_angle,
                       theme['primary'], width, cv2.LINE_AA)
            cv2.addWeighted(overlay, opacity, frame, 1 - opacity, 0, frame)

    def _render_orbit_particles(self, frame):
        """Render particles orbiting in the ring system."""
        theme = self.themes[self.current_theme]

        for p in self.orbit_particles:
            ring = self.rings[p['ring_idx']]
            radius = (ring['radius'] + p['radius_offset']) * self.scale

            # Calculate particle position
            angle = p['angle'] + ring['phase']
            x = int(self.position[0] + radius * np.cos(angle))
            y = int(self.position[1] + radius * np.sin(angle) * (1 - ring['tilt']))

            # Pulsing opacity
            pulse = 0.5 + 0.5 * np.sin(p['phase'])
            opacity = 0.3 * pulse

            if self.is_grabbed:
                opacity *= 1.4

            # Draw particle
            overlay = frame.copy()
            cv2.circle(overlay, (x, y), p['size'], theme['primary'], -1, cv2.LINE_AA)
            cv2.addWeighted(overlay, opacity, frame, 1 - opacity, 0, frame)
