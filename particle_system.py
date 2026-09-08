"""
Particle System - Reusable particle effects for holographic objects.
"""
import numpy as np
import cv2


class Particle:
    """Individual particle with position, velocity, lifetime."""

    def __init__(self, position, velocity, lifetime, size, color):
        self.position = np.array(position, dtype=np.float32)
        self.velocity = np.array(velocity, dtype=np.float32)
        self.lifetime = lifetime
        self.max_lifetime = lifetime
        self.size = size
        self.color = color
        self.opacity = 1.0

    def update(self, dt):
        """Update particle position and lifetime."""
        self.position += self.velocity * dt * 60  # Scale by 60fps
        self.lifetime -= dt
        self.opacity = max(0.0, self.lifetime / self.max_lifetime)
        return self.lifetime > 0

    def render(self, frame):
        """Render particle to frame."""
        if self.opacity <= 0:
            return

        x, y = int(self.position[0]), int(self.position[1])

        # Check bounds
        h, w = frame.shape[:2]
        if x < 0 or x >= w or y < 0 or y >= h:
            return

        # Multi-layer glow
        for radius_mult, opacity_mult in [(2.0, 0.2), (1.5, 0.4), (1.0, 0.8)]:
            radius = max(1, int(self.size * radius_mult))
            opacity = self.opacity * opacity_mult

            overlay = frame.copy()
            cv2.circle(overlay, (x, y), radius, self.color, -1, cv2.LINE_AA)
            cv2.addWeighted(overlay, opacity, frame, 1 - opacity, 0, frame)


class ParticleSystem:
    """Manages multiple particles with emission, forces, and rendering."""

    def __init__(self, max_particles=1000):
        self.max_particles = max_particles
        self.particles = []
        self.gravity = np.array([0.0, 0.0])
        self.attraction_points = []

    def emit(self, position, velocity, count=1, lifetime=1.0, size=3, color=(255, 255, 255),
             spread=0.0):
        """Emit particles from a position."""
        for _ in range(count):
            if len(self.particles) >= self.max_particles:
                break

            # Add random spread to velocity
            vel = np.array(velocity, dtype=np.float32)
            if spread > 0:
                vel += np.random.randn(2) * spread

            particle = Particle(position, vel, lifetime, size, color)
            self.particles.append(particle)

    def burst(self, position, count=20, speed=2.0, lifetime=1.0, size=3, color=(255, 255, 255)):
        """Emit particles in all directions (explosion effect)."""
        for i in range(count):
            if len(self.particles) >= self.max_particles:
                break

            angle = (i / count) * 2 * np.pi
            velocity = np.array([np.cos(angle), np.sin(angle)]) * speed
            particle = Particle(position, velocity, lifetime, size, color)
            self.particles.append(particle)

    def trail(self, position, direction, count=5, lifetime=0.5, size=2, color=(255, 255, 255)):
        """Emit particles in a trail behind moving object."""
        # Emit particles opposite to direction of movement
        trail_velocity = -np.array(direction) * 0.5
        spread = 0.5

        for _ in range(count):
            if len(self.particles) >= self.max_particles:
                break

            vel = trail_velocity + np.random.randn(2) * spread
            particle = Particle(position, vel, lifetime, size, color)
            self.particles.append(particle)

    def add_attraction_point(self, position, strength=1.0, radius=100.0):
        """Add an attraction point for particles."""
        self.attraction_points.append({
            'position': np.array(position, dtype=np.float32),
            'strength': strength,
            'radius': radius
        })

    def clear_attraction_points(self):
        """Remove all attraction points."""
        self.attraction_points = []

    def set_gravity(self, gravity):
        """Set global gravity vector."""
        self.gravity = np.array(gravity, dtype=np.float32)

    def update(self, dt=0.016):
        """Update all particles."""
        # Apply forces and update
        for particle in self.particles:
            # Apply gravity
            particle.velocity += self.gravity * dt

            # Apply attraction forces
            for attractor in self.attraction_points:
                diff = attractor['position'] - particle.position
                dist = np.linalg.norm(diff)

                if dist > 0 and dist < attractor['radius']:
                    # Inverse square law, clamped
                    force_magnitude = attractor['strength'] / max(dist * dist, 1.0)
                    force_magnitude = min(force_magnitude, 5.0)  # Clamp max force
                    force = (diff / dist) * force_magnitude
                    particle.velocity += force * dt * 60

        # Update and remove dead particles
        self.particles = [p for p in self.particles if p.update(dt)]

    def render(self, frame):
        """Render all particles."""
        for particle in self.particles:
            particle.render(frame)

    def clear(self):
        """Remove all particles."""
        self.particles = []

    def get_count(self):
        """Get current particle count."""
        return len(self.particles)
