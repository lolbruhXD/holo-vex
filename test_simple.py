#!/usr/bin/env python3
"""
Simple Integration Test - Basic functionality validation
"""
import sys
import os

# Suppress warnings
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'

print("=" * 60)
print("HOLOGRAPHIC VFX SYSTEM - INTEGRATION TEST")
print("=" * 60)
print()

# Test 1: Import all modules
print("Test 1: Module Imports")
print("-" * 60)
try:
    from camera_system import CameraCapture
    print("✓ camera_system")
except ImportError as e:
    print(f"✗ camera_system: {e}")
    sys.exit(1)

try:
    from hand_tracker import HandTracker
    print("✓ hand_tracker (mock mode)")
except ImportError as e:
    print(f"✗ hand_tracker: {e}")
    sys.exit(1)

try:
    from gesture_system import GestureRecognizer
    print("✓ gesture_system")
except ImportError as e:
    print(f"✗ gesture_system: {e}")
    sys.exit(1)

try:
    from two_hand_interaction import TwoHandInteraction
    print("✓ two_hand_interaction")
except ImportError as e:
    print(f"✗ two_hand_interaction: {e}")
    sys.exit(1)

try:
    from holographic_orb import HolographicOrb
    print("✓ holographic_orb")
except ImportError as e:
    print(f"✗ holographic_orb: {e}")
    sys.exit(1)

try:
    from holographic_cube import HolographicCube
    print("✓ holographic_cube")
except ImportError as e:
    print(f"✗ holographic_cube: {e}")
    sys.exit(1)

try:
    from holographic_planet import HolographicPlanet
    print("✓ holographic_planet")
except ImportError as e:
    print(f"✗ holographic_planet: {e}")
    sys.exit(1)

try:
    from particle_system import ParticleSystem
    print("✓ particle_system")
except ImportError as e:
    print(f"✗ particle_system: {e}")
    sys.exit(1)

try:
    from lighting_system import LightingSystem
    print("✓ lighting_system")
except ImportError as e:
    print(f"✗ lighting_system: {e}")
    sys.exit(1)

try:
    from theme_manager import ThemeManager
    print("✓ theme_manager")
except ImportError as e:
    print(f"✗ theme_manager: {e}")
    sys.exit(1)

try:
    from performance_monitor import PerformanceMonitor
    print("✓ performance_monitor")
except ImportError as e:
    print(f"✗ performance_monitor: {e}")
    sys.exit(1)

print()

# Test 2: Camera System
print("Test 2: Camera System (Synthetic Mode)")
print("-" * 60)
try:
    import cv2
    import numpy as np
    from camera_system import CameraMode

    cam = CameraCapture()
    # Initialize in synthetic mode
    if cam.initialize(mode=CameraMode.SYNTHETIC):
        ret, frame = cam.read_frame()
        if ret and frame is not None:
            print(f"✓ Camera capture working: {frame.shape}")
            cam.release()
        else:
            print("✗ Camera failed to capture frame")
            sys.exit(1)
    else:
        print("✗ Camera failed to initialize")
        sys.exit(1)
except Exception as e:
    print(f"✗ Camera system error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print()

# Test 3: Particle System
print("Test 3: Particle System")
print("-" * 60)
try:
    particles = ParticleSystem(max_particles=100)
    particles.emit((320, 240), (1, 0), count=10)
    count = particles.get_count()
    print(f"✓ Particle emission: {count} particles")

    particles.update()
    print("✓ Particle update")

    frame = np.zeros((480, 640, 3), dtype=np.uint8)
    particles.render(frame)
    print("✓ Particle render")
except Exception as e:
    print(f"✗ Particle system error: {e}")
    sys.exit(1)

print()

# Test 4: Lighting System
print("Test 4: Lighting System")
print("-" * 60)
try:
    lighting = LightingSystem()
    lighting.set_intensity(1.5)
    print(f"✓ Lighting intensity: {lighting.intensity}")

    lighting.update_hand_proximity(50, 100)
    print(f"✓ Hand proximity boost: {lighting.hand_proximity_boost:.2f}")

    lighting.update()
    print("✓ Lighting update")
except Exception as e:
    print(f"✗ Lighting system error: {e}")
    sys.exit(1)

print()

# Test 5: Theme Manager
print("Test 5: Theme Manager")
print("-" * 60)
try:
    themes = ThemeManager()
    print(f"✓ Default theme: {themes.get_theme_name()}")

    themes.cycle_theme()
    print(f"✓ Cycled theme: {themes.get_theme_name()}")

    themes.set_theme('amber')
    print(f"✓ Set theme: {themes.get_theme_name()}")
except Exception as e:
    print(f"✗ Theme manager error: {e}")
    sys.exit(1)

print()

# Test 6: Holographic Objects
print("Test 6: Holographic Objects")
print("-" * 60)
try:
    frame = np.zeros((480, 640, 3), dtype=np.uint8)

    # Test Orb
    orb = HolographicOrb()
    orb.update(0.016)
    orb.render(frame)
    print("✓ Holographic Orb")

    # Test Cube
    cube = HolographicCube()
    cube.update(0.016)
    cube.render(frame)
    print("✓ Holographic Cube")

    # Test Planet
    planet = HolographicPlanet()
    planet.update(0.016)
    planet.render(frame)
    print("✓ Holographic Planet")
except Exception as e:
    print(f"✗ Holographic objects error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print()

# Test 7: Main Application Import
print("Test 7: Main Application")
print("-" * 60)
try:
    import main
    print("✓ Main application module loads")
except ImportError as e:
    print(f"✗ Main application import error: {e}")
    sys.exit(1)

print()
print("=" * 60)
print("ALL TESTS PASSED ✓")
print("=" * 60)
print()
print("System is ready to run!")
print("Start with: python3 main.py --synthetic")
print()

sys.exit(0)
