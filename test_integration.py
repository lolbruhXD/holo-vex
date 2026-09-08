#!/usr/bin/env python3
"""
Integration Tests - Full system testing
"""
import unittest
import numpy as np
import cv2

from camera_system import CameraCapture
from hand_tracker import HandTracker
from gesture_system import GestureRecognizer
from two_hand_interaction import TwoHandInteraction
from holographic_orb import HolographicOrb
from holographic_cube import HolographicCube
from holographic_planet import HolographicPlanet
from particle_system import ParticleSystem
from lighting_system import LightingSystem
from theme_manager import ThemeManager


class TestCameraSystem(unittest.TestCase):
    """Test camera system."""

    def test_synthetic_camera(self):
        """Test synthetic camera initialization and frame capture."""
        cam = CameraCapture(use_synthetic=True)
        self.assertTrue(cam.open())

        ret, frame = cam.read()
        self.assertTrue(ret)
        self.assertIsNotNone(frame)
        self.assertEqual(frame.shape[:2], (480, 640))

        cam.release()

    def test_camera_toggle(self):
        """Test camera mode toggling."""
        cam = CameraCapture(use_synthetic=True)
        cam.open()

        self.assertTrue(cam.use_synthetic)
        cam.toggle_mode()

        # Note: May fail to open real camera in test environment
        cam.release()


class TestHolographicObjects(unittest.TestCase):
    """Test holographic objects."""

    def setUp(self):
        self.frame = np.zeros((480, 640, 3), dtype=np.uint8)

    def test_orb_creation(self):
        """Test orb object creation and basic properties."""
        orb = HolographicOrb(position=(320, 240), scale=60.0)
        self.assertEqual(orb.position, (320, 240))
        self.assertEqual(orb.scale, 60.0)
        self.assertTrue(orb.visible)
        self.assertFalse(orb.is_grabbed)

    def test_orb_render(self):
        """Test orb rendering."""
        orb = HolographicOrb()
        orb.render(self.frame)
        # Frame should be modified (not all black)
        self.assertTrue(np.any(self.frame > 0))

    def test_cube_creation(self):
        """Test cube object creation."""
        cube = HolographicCube(position=(320, 240), scale=80.0)
        self.assertEqual(cube.position, (320, 240))
        self.assertEqual(cube.scale, 80.0)
        self.assertEqual(len(cube.base_vertices), 8)
        self.assertEqual(len(cube.edges), 12)

    def test_cube_render(self):
        """Test cube rendering."""
        cube = HolographicCube()
        cube.render(self.frame)
        self.assertTrue(np.any(self.frame > 0))

    def test_planet_creation(self):
        """Test planet object creation."""
        planet = HolographicPlanet(position=(320, 240), scale=70.0)
        self.assertEqual(planet.position, (320, 240))
        self.assertEqual(planet.scale, 70.0)
        self.assertEqual(len(planet.rings), 3)

    def test_planet_render(self):
        """Test planet rendering."""
        planet = HolographicPlanet()
        planet.render(self.frame)
        self.assertTrue(np.any(self.frame > 0))

    def test_object_interaction(self):
        """Test object grab/release."""
        orb = HolographicOrb()

        self.assertFalse(orb.is_grabbed)
        orb.grab()
        self.assertTrue(orb.is_grabbed)
        orb.release()
        self.assertFalse(orb.is_grabbed)

    def test_object_movement(self):
        """Test object position update."""
        orb = HolographicOrb(position=(100, 100))
        orb.set_position((200, 200))
        self.assertEqual(orb.position, (200, 200))

    def test_object_scaling(self):
        """Test object scale update."""
        orb = HolographicOrb(scale=50.0)
        orb.set_scale(100.0)
        self.assertEqual(orb.scale, 100.0)


class TestParticleSystem(unittest.TestCase):
    """Test particle system."""

    def setUp(self):
        self.particles = ParticleSystem(max_particles=100)
        self.frame = np.zeros((480, 640, 3), dtype=np.uint8)

    def test_particle_emission(self):
        """Test particle emission."""
        self.particles.emit((320, 240), (1, 0), count=10)
        self.assertEqual(self.particles.get_count(), 10)

    def test_particle_burst(self):
        """Test particle burst."""
        self.particles.burst((320, 240), count=20)
        self.assertEqual(self.particles.get_count(), 20)

    def test_particle_update(self):
        """Test particle lifetime update."""
        self.particles.emit((320, 240), (0, 0), count=5, lifetime=0.1)

        # Update several times
        for _ in range(10):
            self.particles.update(dt=0.05)

        # Particles should have expired
        self.assertEqual(self.particles.get_count(), 0)

    def test_particle_max_limit(self):
        """Test particle count limit."""
        self.particles.emit((320, 240), (0, 0), count=200)
        self.assertLessEqual(self.particles.get_count(), 100)

    def test_particle_render(self):
        """Test particle rendering."""
        self.particles.emit((320, 240), (0, 0), count=10)
        self.particles.render(self.frame)
        # Some pixels should be modified
        self.assertTrue(np.any(self.frame > 0))


class TestLightingSystem(unittest.TestCase):
    """Test lighting system."""

    def setUp(self):
        self.lighting = LightingSystem()

    def test_intensity_control(self):
        """Test light intensity setting."""
        self.lighting.set_intensity(1.5)
        self.assertEqual(self.lighting.intensity, 1.5)

        # Test clamping
        self.lighting.set_intensity(5.0)
        self.assertEqual(self.lighting.intensity, 2.0)

    def test_direction_setting(self):
        """Test light direction."""
        self.lighting.set_direction([1, 0, 0])
        expected = np.array([1, 0, 0], dtype=np.float32)
        np.testing.assert_array_almost_equal(self.lighting.direction, expected)

    def test_hand_proximity(self):
        """Test hand proximity boost."""
        self.lighting.update_hand_proximity(50, max_distance=100)
        self.assertGreater(self.lighting.hand_proximity_boost, 0)

        self.lighting.update_hand_proximity(200, max_distance=100)
        self.assertEqual(self.lighting.hand_proximity_boost, 0)

    def test_pinch_state(self):
        """Test pinch state lighting."""
        self.lighting.update_pinch_state(True)
        self.assertGreater(self.lighting.pinch_boost, 0)


class TestThemeManager(unittest.TestCase):
    """Test theme management."""

    def setUp(self):
        self.theme_manager = ThemeManager()

    def test_default_theme(self):
        """Test default theme."""
        self.assertEqual(self.theme_manager.current_theme_name, 'cyan')

    def test_theme_cycling(self):
        """Test theme cycling."""
        initial = self.theme_manager.current_theme_name
        self.theme_manager.cycle_theme()
        self.assertNotEqual(self.theme_manager.current_theme_name, initial)

    def test_set_theme(self):
        """Test setting theme by name."""
        result = self.theme_manager.set_theme('purple')
        self.assertTrue(result)
        self.assertEqual(self.theme_manager.current_theme_name, 'purple')

        result = self.theme_manager.set_theme('invalid')
        self.assertFalse(result)

    def test_get_theme_color(self):
        """Test getting theme colors."""
        color = self.theme_manager.get_theme_color('primary')
        self.assertIsInstance(color, tuple)
        self.assertEqual(len(color), 3)


class TestTwoHandInteraction(unittest.TestCase):
    """Test two-hand interaction."""

    def setUp(self):
        self.two_hand = TwoHandInteraction()

        # Create synthetic hand landmarks
        self.hand1 = np.random.rand(21, 3).astype(np.float32)
        self.hand2 = np.random.rand(21, 3).astype(np.float32)

    def test_two_hand_detection(self):
        """Test two-hand mode detection."""
        result = self.two_hand.process_two_hands(self.hand1, self.hand2)
        self.assertIn('mode', result)
        self.assertIn('scale', result)
        self.assertIn('rotation', result)

    def test_single_hand_fallback(self):
        """Test fallback to single hand."""
        # Process with None as second hand
        result = self.two_hand.process_two_hands(self.hand1, None)
        self.assertIsNotNone(result)


def run_tests():
    """Run all tests."""
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    # Add all test classes
    suite.addTests(loader.loadTestsFromTestCase(TestCameraSystem))
    suite.addTests(loader.loadTestsFromTestCase(TestHolographicObjects))
    suite.addTests(loader.loadTestsFromTestCase(TestParticleSystem))
    suite.addTests(loader.loadTestsFromTestCase(TestLightingSystem))
    suite.addTests(loader.loadTestsFromTestCase(TestThemeManager))
    suite.addTests(loader.loadTestsFromTestCase(TestTwoHandInteraction))

    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    return result.wasSuccessful()


if __name__ == '__main__':
    import sys
    success = run_tests()
    sys.exit(0 if success else 1)
