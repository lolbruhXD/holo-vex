"""
Holographic Cube - Wireframe cube with glowing edges and translucent faces.
"""
import numpy as np
import cv2
from holographic_base import HolographicObject


class HolographicCube(HolographicObject):
    """Holographic cube with wireframe edges, glowing vertices, and animated rotation."""

    def __init__(self, position=(320, 240), scale=100.0):
        super().__init__(position, scale)
        self.visible = True
        self.age = 0.0
        self.rotation_x = 0.0
        self.rotation_y = 0.0
        self.rotation_z = 0.0
        self.rotation_speed_x = 0.01
        self.rotation_speed_y = 0.015
        self.rotation_speed_z = 0.008

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

        # Cube vertices in local space (-1 to 1)
        self.base_vertices = np.array([
            [-1, -1, -1], [1, -1, -1], [1, 1, -1], [-1, 1, -1],  # Back
            [-1, -1,  1], [1, -1,  1], [1, 1,  1], [-1, 1,  1],  # Front
        ], dtype=np.float32)

        # Cube edges (vertex index pairs)
        self.edges = [
            (0, 1), (1, 2), (2, 3), (3, 0),  # Back face
            (4, 5), (5, 6), (6, 7), (7, 4),  # Front face
            (0, 4), (1, 5), (2, 6), (3, 7),  # Connecting edges
        ]

        # Face definitions (vertex indices for each face)
        self.faces = [
            [0, 1, 2, 3],  # Back
            [4, 5, 6, 7],  # Front
            [0, 1, 5, 4],  # Bottom
            [2, 3, 7, 6],  # Top
            [0, 3, 7, 4],  # Left
            [1, 2, 6, 5],  # Right
        ]

        self.edge_glow_phase = np.random.rand(12) * 2 * np.pi
        self.particles = []
        self._init_particles()

    def _init_particles(self):
        """Initialize particles orbiting the cube."""
        num_particles = 60
        for _ in range(num_particles):
            self.particles.append({
                'offset': np.random.randn(3) * 1.5,
                'phase': np.random.rand() * 2 * np.pi,
                'speed': 0.02 + np.random.rand() * 0.03,
                'size': np.random.randint(1, 4),
            })

    def _rotation_matrix(self, rx, ry, rz):
        """Create 3D rotation matrix."""
        # Rotation around X
        Rx = np.array([
            [1, 0, 0],
            [0, np.cos(rx), -np.sin(rx)],
            [0, np.sin(rx), np.cos(rx)]
        ])

        # Rotation around Y
        Ry = np.array([
            [np.cos(ry), 0, np.sin(ry)],
            [0, 1, 0],
            [-np.sin(ry), 0, np.cos(ry)]
        ])

        # Rotation around Z
        Rz = np.array([
            [np.cos(rz), -np.sin(rz), 0],
            [np.sin(rz), np.cos(rz), 0],
            [0, 0, 1]
        ])

        return Rz @ Ry @ Rx

    def _project_3d_to_2d(self, vertices_3d, fov=500):
        """Project 3D vertices to 2D screen space with perspective."""
        projected = []
        for v in vertices_3d:
            z = v[2] + 3  # Move camera back
            if z <= 0:
                z = 0.1
            scale = fov / z
            x_2d = int(self.position[0] + v[0] * scale)
            y_2d = int(self.position[1] - v[1] * scale)
            projected.append((x_2d, y_2d, z))
        return projected

    def update(self, dt=0.016):
        """Update cube rotation and particle animation."""
        super().update(dt)

        # Increment age
        self.age += dt

        # Animate rotation
        self.rotation_x += self.rotation_speed_x
        self.rotation_y += self.rotation_speed_y
        self.rotation_z += self.rotation_speed_z

        # Update particle phases
        for p in self.particles:
            p['phase'] += p['speed']

        # Update edge glow
        self.edge_glow_phase += 0.05

    def render(self, frame):
        """Render the holographic cube with all effects."""
        if not self.visible:
            return

        # Transform vertices
        R = self._rotation_matrix(self.rotation_x, self.rotation_y, self.rotation_z)
        vertices_3d = (self.base_vertices @ R.T) * self.scale

        # Project to 2D
        vertices_2d = self._project_3d_to_2d(vertices_3d)

        # Render translucent faces
        self._render_faces(frame, vertices_2d)

        # Render edges with glow
        self._render_edges(frame, vertices_2d)

        # Render particles
        self._render_particles(frame, vertices_2d)

        # Render vertices
        self._render_vertices(frame, vertices_2d)

    def _render_faces(self, frame, vertices_2d):
        """Render translucent cube faces."""
        theme = self.themes[self.current_theme]

        for face_indices in self.faces:
            # Get face vertices
            face_pts = np.array([vertices_2d[i][:2] for i in face_indices], dtype=np.int32)

            # Calculate face center depth
            avg_z = np.mean([vertices_2d[i][2] for i in face_indices])

            # Depth-based opacity (closer faces more visible)
            base_opacity = 0.15 if avg_z > 3 else 0.25
            opacity = base_opacity * (1.2 if self.is_grabbed else 1.0)

            # Create face overlay
            overlay = frame.copy()
            cv2.fillPoly(overlay, [face_pts], theme['secondary'])
            cv2.addWeighted(overlay, opacity, frame, 1 - opacity, 0, frame)

    def _render_edges(self, frame, vertices_2d):
        """Render glowing wireframe edges."""
        theme = self.themes[self.current_theme]

        for edge_idx, (i, j) in enumerate(self.edges):
            p1 = vertices_2d[i][:2]
            p2 = vertices_2d[j][:2]

            # Animated glow intensity
            glow_intensity = 0.5 + 0.5 * np.sin(self.edge_glow_phase[edge_idx])
            if self.is_grabbed:
                glow_intensity *= 1.5

            # Draw glow layers
            for thickness in [8, 5, 3, 1]:
                opacity = glow_intensity * (0.1 + 0.2 / thickness)
                overlay = frame.copy()
                color = theme['primary'] if thickness <= 3 else theme['secondary']
                cv2.line(overlay, p1, p2, color, thickness, cv2.LINE_AA)
                cv2.addWeighted(overlay, opacity, frame, 1 - opacity, 0, frame)

    def _render_vertices(self, frame, vertices_2d):
        """Render glowing vertex points."""
        theme = self.themes[self.current_theme]

        for v_2d in vertices_2d:
            x, y = v_2d[:2]

            # Pulsing glow
            pulse = 0.7 + 0.3 * np.sin(self.age * 3)
            radius = int(4 * pulse)

            # Multi-layer glow
            for r, opacity in [(radius + 4, 0.15), (radius + 2, 0.3), (radius, 0.8)]:
                overlay = frame.copy()
                cv2.circle(overlay, (x, y), r, theme['primary'], -1, cv2.LINE_AA)
                cv2.addWeighted(overlay, opacity, frame, 1 - opacity, 0, frame)

    def _render_particles(self, frame, vertices_2d):
        """Render particles orbiting the cube."""
        theme = self.themes[self.current_theme]

        R = self._rotation_matrix(self.rotation_x, self.rotation_y, self.rotation_z)

        for p in self.particles:
            # Calculate particle position in 3D space
            offset = p['offset'] * np.cos(p['phase'])
            pos_3d = offset * self.scale
            pos_3d_rotated = pos_3d @ R.T

            # Project to 2D
            projected = self._project_3d_to_2d([pos_3d_rotated])
            if projected:
                x, y, z = projected[0]

                # Depth-based opacity
                opacity = 0.4 if z > 3 else 0.7
                if self.is_grabbed:
                    opacity *= 1.3

                # Draw particle
                overlay = frame.copy()
                cv2.circle(overlay, (x, y), p['size'], theme['primary'], -1, cv2.LINE_AA)
                cv2.addWeighted(overlay, opacity, frame, 1 - opacity, 0, frame)
