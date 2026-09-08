"""
Unit tests for the holographic orb implementation.

Tests core functionality:
- Base class initialization and properties
- Orb rendering components
- Particle system
- Energy rings
- Interaction handling
- Theme switching
"""

import pytest
import numpy as np
import cv2
from holographic_base import HolographicObject, Theme
from holographic_orb import HolographicOrb, Particle, EnergyRing


class TestHolographicBase:
    """Tests for HolographicObject base class."""

    def test_initialization(self):
        """Test base object initialization."""
        obj = HolographicObject(
            position=(0.5, 0.5, 0.0),
            scale=1.5,
            rotation=(10.0, 20.0, 30.0),
            theme=Theme.EMERALD
        )

        assert np.allclose(obj.position, [0.5, 0.5, 0.0])
        assert obj.scale == 1.5
        assert np.allclose(obj.rotation, [10.0, 20.0, 30.0])
        assert obj.theme == Theme.EMERALD
        assert not obj.is_grabbed
        assert not obj.is_hovered

    def test_theme_colors(self):
        """Test theme color retrieval."""
        obj = HolographicObject(theme=Theme.CYAN)
        colors = obj.get_colors()

        assert 'primary' in colors
        assert 'secondary' in colors
        assert 'accent' in colors
        assert 'glow' in colors

        # Check RGB format
        for color_name, color_value in colors.items():
            assert len(color_value) == 3
            assert all(0 <= c <= 255 for c in color_value)

    def test_set_position(self):
        """Test position setting."""
        obj = HolographicObject()
        obj.set_position(0.3, 0.7, -0.5)

        assert np.allclose(obj.position, [0.3, 0.7, -0.5])

    def test_set_scale(self):
        """Test scale setting with minimum constraint."""
        obj = HolographicObject()

        obj.set_scale(2.0)
        assert obj.scale == 2.0

        obj.set_scale(0.05)  # Below minimum
        assert obj.scale == 0.1  # Should clamp to minimum

    def test_rotation(self):
        """Test rotation methods."""
        obj = HolographicObject()

        obj.set_rotation(45.0, 90.0, 180.0)
        assert np.allclose(obj.rotation, [45.0, 90.0, 180.0])

        obj.rotate(10.0, 20.0, 30.0)
        assert np.allclose(obj.rotation, [55.0, 110.0, 210.0])

        # Test wrapping
        obj.rotate(200.0, 300.0, 200.0)
        assert all(0 <= angle < 360 for angle in obj.rotation)

    def test_translation(self):
        """Test position translation."""
        obj = HolographicObject(position=(0.5, 0.5, 0.0))
        obj.translate(0.1, -0.2, 0.3)

        assert np.allclose(obj.position, [0.6, 0.3, 0.3])

    def test_distance_calculation(self):
        """Test distance to point calculation."""
        obj = HolographicObject(position=(0.5, 0.5, 0.0))
        point = np.array([0.8, 0.5, 0.0])

        distance = obj.distance_to_point(point)
        assert np.isclose(distance, 0.3)

    def test_grab_release(self):
        """Test grab and release mechanics."""
        obj = HolographicObject(position=(0.5, 0.5, 0.0))
        grab_point = np.array([0.4, 0.4, 0.0])

        # Grab
        obj.grab(grab_point)
        assert obj.is_grabbed
        assert not np.allclose(obj.grab_offset, [0.0, 0.0, 0.0])

        # Move
        new_grab_point = np.array([0.6, 0.6, 0.0])
        obj.move_to_grab_point(new_grab_point)
        assert not np.allclose(obj.position, [0.5, 0.5, 0.0])

        # Release
        obj.release()
        assert not obj.is_grabbed
        assert np.allclose(obj.grab_offset, [0.0, 0.0, 0.0])

    def test_hover_detection(self):
        """Test hover detection."""
        obj = HolographicObject(position=(0.5, 0.5, 0.0))

        # Point within threshold
        close_point = np.array([0.5, 0.5, 0.0])
        assert obj.check_hover(close_point, threshold=100.0)
        assert obj.is_hovered

        # Point outside threshold
        far_point = np.array([0.9, 0.9, 0.0])
        assert not obj.check_hover(far_point, threshold=10.0)
        assert not obj.is_hovered

    def test_update(self):
        """Test update method effects."""
        obj = HolographicObject()
        obj.rotation_speed = np.array([10.0, 20.0, 30.0])

        initial_rotation = obj.rotation.copy()
        obj.update(dt=1.0)

        # Rotation should have changed
        assert not np.allclose(obj.rotation, initial_rotation)

        # Time should have advanced
        assert obj.time > 0.0

    def test_screen_position(self):
        """Test 3D to 2D screen projection."""
        obj = HolographicObject(position=(0.5, 0.5, 0.0))
        screen_pos = obj.get_screen_position(1280, 720)

        assert screen_pos == (640, 360)


class TestParticle:
    """Tests for Particle class."""

    def test_initialization(self):
        """Test particle initialization."""
        position = np.array([100.0, 200.0, 0.0])
        velocity = np.array([10.0, -5.0, 0.0])
        particle = Particle(
            position=position,
            velocity=velocity,
            lifetime=2.0,
            size=3.0,
            color=(255, 100, 50)
        )

        assert np.allclose(particle.position, position)
        assert np.allclose(particle.velocity, velocity)
        assert particle.lifetime == 2.0
        assert particle.size == 3.0
        assert particle.color == (255, 100, 50)

    def test_particle_lifetime(self):
        """Test particle lifetime and alive status."""
        particle = Particle(
            position=np.array([0.0, 0.0, 0.0]),
            velocity=np.array([0.0, 0.0, 0.0]),
            lifetime=1.0,
            size=2.0,
            color=(255, 255, 255)
        )

        assert particle.is_alive()

        # Update beyond lifetime
        particle.update(dt=2.0, center=np.array([0.0, 0.0]))
        assert not particle.is_alive()

    def test_particle_alpha_fade(self):
        """Test particle alpha calculation."""
        particle = Particle(
            position=np.array([0.0, 0.0, 0.0]),
            velocity=np.array([0.0, 0.0, 0.0]),
            lifetime=2.0,
            size=2.0,
            color=(255, 255, 255)
        )

        # Full alpha at start
        assert particle.get_alpha() == 1.0

        # Reduced alpha after time
        particle.update(dt=1.0, center=np.array([0.0, 0.0]))
        alpha = particle.get_alpha()
        assert 0.0 < alpha < 1.0


class TestEnergyRing:
    """Tests for EnergyRing class."""

    def test_initialization(self):
        """Test energy ring initialization."""
        ring = EnergyRing(
            radius=1.5,
            thickness=3.0,
            rotation_speed=2.0,
            color=(100, 200, 255)
        )

        assert ring.radius == 1.5
        assert ring.thickness == 3.0
        assert ring.rotation_speed == 2.0
        assert ring.color == (100, 200, 255)

    def test_ring_rotation(self):
        """Test ring rotation update."""
        ring = EnergyRing(
            radius=1.0,
            thickness=2.0,
            rotation_speed=1.0,
            color=(255, 255, 255)
        )

        initial_angle = ring.angle
        ring.update(dt=1.0)

        assert ring.angle != initial_angle
        assert 0 <= ring.angle < 2 * np.pi

    def test_pulse_scale(self):
        """Test pulsing scale calculation."""
        ring = EnergyRing(
            radius=1.0,
            thickness=2.0,
            rotation_speed=1.0,
            color=(255, 255, 255)
        )

        scale = ring.get_pulse_scale()
        assert 0.85 <= scale <= 1.15  # Within pulse range


class TestHolographicOrb:
    """Tests for HolographicOrb class."""

    def test_initialization(self):
        """Test orb initialization."""
        orb = HolographicOrb(
            position=(0.5, 0.5, 0.0),
            scale=1.5,
            base_radius=80.0,
            theme=Theme.VIOLET
        )

        assert np.allclose(orb.position, [0.5, 0.5, 0.0])
        assert orb.scale == 1.5
        assert orb.base_radius == 80.0
        assert orb.theme == Theme.VIOLET
        assert len(orb.energy_rings) == 3
        assert len(orb.particles) == 0

    def test_effective_radius(self):
        """Test effective radius calculation."""
        orb = HolographicOrb(base_radius=100.0, scale=1.5)

        radius = orb.get_effective_radius()
        # Should be base * scale * pulse (pulse is ~1.0)
        assert 140.0 < radius < 160.0

    def test_theme_switching(self):
        """Test theme change updates energy rings."""
        orb = HolographicOrb(theme=Theme.CYAN)

        initial_ring_colors = [ring.color for ring in orb.energy_rings]

        orb.set_theme(Theme.CRIMSON)
        new_ring_colors = [ring.color for ring in orb.energy_rings]

        # Colors should have changed
        assert initial_ring_colors != new_ring_colors
        assert orb.theme == Theme.CRIMSON

    def test_particle_spawning(self):
        """Test particle spawning."""
        orb = HolographicOrb()
        initial_count = len(orb.particles)

        orb.spawn_particle(center=(320, 240))

        assert len(orb.particles) == initial_count + 1

    def test_particle_limit(self):
        """Test particle count limiting."""
        orb = HolographicOrb()

        # Spawn many particles
        for _ in range(200):
            orb.spawn_particle(center=(320, 240))

        orb.update(dt=0.1)

        # Should be capped at 150
        assert len(orb.particles) <= 150

    def test_update_spawns_particles(self):
        """Test that update spawns particles over time."""
        orb = HolographicOrb()
        initial_count = len(orb.particles)

        # Run multiple updates
        for _ in range(10):
            orb.update(dt=0.1)

        # Should have spawned particles
        assert len(orb.particles) > initial_count

    def test_interaction_effects(self):
        """Test interaction affects visual properties."""
        orb = HolographicOrb()
        default_glow = orb.glow_intensity
        default_emission = orb.particle_emission_rate

        # Grabbed state
        orb.is_grabbed = True
        orb.update(dt=0.1)
        assert orb.glow_intensity > default_glow
        assert orb.particle_emission_rate > default_emission

        # Hovered state
        orb.is_grabbed = False
        orb.is_hovered = True
        orb.update(dt=0.1)
        assert orb.glow_intensity > 1.0
        assert orb.particle_emission_rate > 1.0

    def test_render_creates_output(self):
        """Test that render modifies the frame."""
        orb = HolographicOrb(position=(0.5, 0.5, 0.0))

        # Create blank frame
        frame = np.zeros((480, 640, 3), dtype=np.uint8)
        frame_before = frame.copy()

        orb.render(frame)

        # Frame should have been modified
        assert not np.array_equal(frame, frame_before)

    def test_render_all_themes(self):
        """Test rendering with all themes."""
        orb = HolographicOrb()
        frame = np.zeros((480, 640, 3), dtype=np.uint8)

        for theme in Theme:
            orb.set_theme(theme)
            orb.render(frame)
            # Should complete without error

    def test_orb_string_representation(self):
        """Test __repr__ method."""
        orb = HolographicOrb(theme=Theme.AMBER)
        repr_str = repr(orb)

        assert "HolographicOrb" in repr_str
        assert "amber" in repr_str
        assert "particles" in repr_str


class TestIntegration:
    """Integration tests for complete workflows."""

    def test_grab_and_move_workflow(self):
        """Test complete grab and move workflow."""
        orb = HolographicOrb(position=(0.5, 0.5, 0.0))

        # Start grab
        grab_point = np.array([0.5, 0.5, 0.0])
        orb.grab(grab_point)
        assert orb.is_grabbed

        # Move
        for i in range(10):
            new_point = grab_point + np.array([0.01 * i, 0.01 * i, 0.0])
            orb.move_to_grab_point(new_point)
            orb.update(dt=0.016)

        # Position should have changed
        assert not np.allclose(orb.position, [0.5, 0.5, 0.0])

        # Release
        orb.release()
        assert not orb.is_grabbed

    def test_render_with_particles_and_rings(self):
        """Test rendering with active particles and rings."""
        orb = HolographicOrb()

        # Spawn some particles
        for _ in range(20):
            orb.spawn_particle(center=(320, 240))

        # Update rings
        for _ in range(5):
            orb.update(dt=0.1)

        # Render
        frame = np.zeros((480, 640, 3), dtype=np.uint8)
        orb.render(frame)

        # Check that something was drawn
        assert np.any(frame > 0)

    def test_performance_many_updates(self):
        """Test performance with many updates."""
        orb = HolographicOrb()
        frame = np.zeros((480, 640, 3), dtype=np.uint8)

        # Run many update/render cycles
        for _ in range(100):
            orb.update(dt=0.016)
            orb.render(frame)

        # Should complete without errors
        assert len(orb.particles) > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
