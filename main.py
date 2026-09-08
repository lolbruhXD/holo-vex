#!/usr/bin/env python3
"""
Main Holographic VFX Application
Real-time hand-tracked holographic interaction system.
"""
import cv2
import numpy as np
import sys

from camera_system import CameraSystem, CameraMode
from hand_tracker import HandTracker
from gesture_system import GestureRecognizer
from two_hand_interaction import TwoHandInteraction
from holographic_orb import HolographicOrb
from holographic_cube import HolographicCube
from holographic_planet import HolographicPlanet
from particle_system import ParticleSystem
from lighting_system import LightingSystem
from theme_manager import ThemeManager
from performance_monitor import PerformanceMonitor, QualityPreset


class HolographicApp:
    """Main application integrating all systems."""

    def __init__(self, use_synthetic=False, quality='medium'):
        # Initialize systems
        self.camera = CameraSystem()
        if use_synthetic:
            self.camera.initialize(mode=CameraMode.SYNTHETIC)
        else:
            self.camera.initialize(mode=CameraMode.WEBCAM)
        self.tracker = HandTracker()
        self.gesture = GestureRecognizer()
        self.two_hand = TwoHandInteraction()
        self.particles = ParticleSystem(max_particles=500)
        self.lighting = LightingSystem()
        self.theme_manager = ThemeManager()

        # Performance monitoring
        quality_preset = {
            'low': QualityPreset.LOW,
            'medium': QualityPreset.MEDIUM,
            'high': QualityPreset.HIGH,
        }.get(quality, QualityPreset.MEDIUM)
        self.perf = PerformanceMonitor(quality_preset=quality_preset)

        # Holographic objects
        self.objects = {
            'orb': HolographicOrb(position=(320, 240), scale=60.0),
            'cube': HolographicCube(position=(320, 240), scale=80.0),
            'planet': HolographicPlanet(position=(320, 240), scale=70.0),
        }
        self.object_order = ['orb', 'cube', 'planet']
        self.current_object_idx = 0
        self.current_object = self.objects[self.object_order[0]]

        # State
        self.running = True
        self.show_landmarks = True
        self.show_hud = True
        self.lighting_enabled = True
        self.effects_enabled = True

        # Interaction state
        self.prev_position = None
        self.grab_offset = np.array([0.0, 0.0])

        print("Holographic VFX System Initialized")
        print("Controls:")
        print("  1/2/3   - Switch objects (Orb/Cube/Planet)")
        print("  T       - Cycle theme")
        print("  L       - Toggle lighting")
        print("  E       - Toggle effects")
        print("  H       - Toggle HUD")
        print("  D       - Toggle landmarks")
        print("  C       - Switch camera mode")
        print("  Q/ESC   - Quit")

    def switch_object(self, index):
        """Switch to a different holographic object."""
        if 0 <= index < len(self.object_order):
            self.current_object_idx = index
            obj_name = self.object_order[index]
            self.current_object = self.objects[obj_name]

            # Update theme for new object
            theme = self.theme_manager.get_current_theme()
            self.current_object.set_theme_by_dict(theme)

            # Particle burst on switch
            if self.effects_enabled:
                self.particles.burst(
                    self.current_object.position,
                    count=30,
                    speed=3.0,
                    lifetime=0.8,
                    color=theme['particle']
                )

            print(f"Switched to: {obj_name.upper()}")

    def cycle_theme(self):
        """Cycle to next visual theme."""
        self.theme_manager.cycle_theme()
        theme = self.theme_manager.get_current_theme()

        # Update all objects
        for obj in self.objects.values():
            obj.set_theme_by_dict(theme)

        # Update lighting
        self.lighting.set_theme_color(theme['primary'])

        print(f"Theme: {self.theme_manager.get_theme_name()}")

    def process_interaction(self, hands_data):
        """Process hand tracking and update object interaction."""
        if not hands_data:
            # No hands detected
            if self.current_object.is_grabbed:
                # Release object
                self.current_object.release()
                if self.effects_enabled:
                    theme = self.theme_manager.get_current_theme()
                    self.particles.burst(
                        self.current_object.position,
                        count=15,
                        speed=2.0,
                        lifetime=0.6,
                        color=theme['particle']
                    )
            self.prev_position = None
            return

        # Single hand interaction
        if len(hands_data) == 1:
            hand = hands_data[0]
            gesture_data = self.gesture.process_frame(hand['landmarks'])

            # Get hand position (palm center)
            palm_x = int(hand['palm_center'][0] * 640)
            palm_y = int(hand['palm_center'][1] * 480)
            hand_pos = np.array([palm_x, palm_y], dtype=np.float32)

            # Update lighting based on hand proximity
            dist = np.linalg.norm(hand_pos - np.array(self.current_object.position))
            self.lighting.update_hand_proximity(dist)

            # Pinch to grab
            if gesture_data['pinch']['active']:
                if not self.current_object.is_grabbed:
                    # Start grab
                    self.current_object.grab()
                    self.grab_offset = np.array(self.current_object.position) - hand_pos

                    if self.effects_enabled:
                        theme = self.theme_manager.get_current_theme()
                        self.particles.emit(
                            hand_pos,
                            velocity=[0, 0],
                            count=10,
                            lifetime=0.5,
                            color=theme['particle'],
                            spread=2.0
                        )

                # Move object with hand
                new_pos = hand_pos + self.grab_offset

                # Create trail particles for fast movement
                if self.prev_position is not None and self.effects_enabled:
                    velocity = new_pos - self.prev_position
                    speed = np.linalg.norm(velocity)
                    if speed > 5:
                        theme = self.theme_manager.get_current_theme()
                        self.particles.trail(
                            self.current_object.position,
                            velocity,
                            count=3,
                            lifetime=0.3,
                            size=2,
                            color=theme['particle']
                        )

                self.current_object.set_position(tuple(new_pos))
                self.prev_position = new_pos.copy()
            else:
                if self.current_object.is_grabbed:
                    # Release
                    self.current_object.release()
                    if self.effects_enabled:
                        theme = self.theme_manager.get_current_theme()
                        self.particles.burst(
                            self.current_object.position,
                            count=15,
                            speed=2.5,
                            lifetime=0.6,
                            color=theme['particle']
                        )
                self.prev_position = None

            # Scale by hand openness
            openness = gesture_data['openness']['value']
            scale = 50 + openness * 80  # 50 to 130
            self.current_object.set_scale(scale)

            # Update lighting
            self.lighting.update_pinch_state(gesture_data['pinch']['active'])

        # Two hand interaction
        elif len(hands_data) >= 2:
            hand1 = hands_data[0]
            hand2 = hands_data[1]

            landmarks1 = hand1['landmarks']
            landmarks2 = hand2['landmarks']

            result = self.two_hand.process_two_hands(landmarks1, landmarks2)

            if result['mode'] == 'TWO_HAND':
                # Two-hand scaling
                scale = result['scale'] * 80  # Base scale
                self.current_object.set_scale(scale)

                # Two-hand rotation (for objects that support it)
                if hasattr(self.current_object, 'rotation_speed_y'):
                    self.current_object.rotation_speed_y = result['rotation'] * 0.05

    def render_hud(self, frame):
        """Render heads-up display."""
        if not self.show_hud:
            return

        theme = self.theme_manager.get_current_theme()
        hud_color = theme['hud']

        # Semi-transparent panel
        overlay = frame.copy()
        cv2.rectangle(overlay, (10, 10), (300, 150), (10, 10, 10), -1)
        cv2.addWeighted(overlay, 0.7, frame, 0.3, 0, frame)

        # Title
        cv2.putText(frame, "HOLOGRAPHIC SYSTEM", (20, 35),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, hud_color, 2, cv2.LINE_AA)

        # Object info
        obj_name = self.object_order[self.current_object_idx].upper()
        cv2.putText(frame, f"Object: {obj_name}", (20, 60),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, (200, 200, 200), 1, cv2.LINE_AA)

        # Theme
        theme_name = self.theme_manager.get_theme_name()
        cv2.putText(frame, f"Theme: {theme_name}", (20, 80),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, (200, 200, 200), 1, cv2.LINE_AA)

        # FPS
        metrics = self.perf.get_metrics()
        fps_color = (100, 255, 100) if metrics.avg_fps > 25 else (100, 200, 255)
        cv2.putText(frame, f"FPS: {metrics.avg_fps:.1f}", (20, 100),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, fps_color, 1, cv2.LINE_AA)

        # Camera mode
        cam_mode = "Synthetic" if self.camera.mode == CameraMode.SYNTHETIC else "Webcam"
        cv2.putText(frame, f"Camera: {cam_mode}", (20, 120),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, (200, 200, 200), 1, cv2.LINE_AA)

        # Status badges
        y_pos = 140
        if self.lighting_enabled:
            cv2.putText(frame, "[L]", (20, y_pos), cv2.FONT_HERSHEY_SIMPLEX,
                       0.4, hud_color, 1, cv2.LINE_AA)
        if self.effects_enabled:
            cv2.putText(frame, "[E]", (55, y_pos), cv2.FONT_HERSHEY_SIMPLEX,
                       0.4, hud_color, 1, cv2.LINE_AA)

    def run(self):
        """Main application loop."""
        if not self.camera.is_initialized:
            print("ERROR: Camera not initialized")
            return False

        try:
            while self.running:
                self.perf.start_frame()

                # Capture frame
                ret, frame = self.camera.read_frame()
                if not ret or frame is None:
                    print("ERROR: Failed to read frame")
                    break

                # Ensure correct size
                frame = cv2.resize(frame, (640, 480))

                # Track hands
                self.perf.start_tracking()
                hands_data = self.tracker.process_frame(frame)
                self.perf.end_tracking()

                # Process interaction
                self.process_interaction(hands_data)

                # Update systems
                self.perf.start_render()
                self.current_object.update()
                self.particles.update()
                self.lighting.update()

                # Render lighting
                if self.lighting_enabled:
                    self.lighting.apply_to_frame(
                        frame,
                        self.current_object.position,
                        int(self.current_object.scale * 1.5)
                    )

                # Render object
                self.current_object.render(frame)

                # Render particles
                if self.effects_enabled:
                    self.particles.render(frame)

                # Draw hand landmarks
                if self.show_landmarks and hands_data:
                    for hand in hands_data:
                        self.tracker.draw_landmarks(frame, hand['landmarks'])

                # Render HUD
                self.render_hud(frame)

                self.perf.end_render()
                self.perf.end_frame()

                # Display
                cv2.imshow('Holographic VFX', frame)

                # Handle keyboard input
                key = cv2.waitKey(1) & 0xFF
                if key == ord('q') or key == 27:  # Q or ESC
                    self.running = False
                elif key == ord('1'):
                    self.switch_object(0)
                elif key == ord('2'):
                    self.switch_object(1)
                elif key == ord('3'):
                    self.switch_object(2)
                elif key == ord('t'):
                    self.cycle_theme()
                elif key == ord('l'):
                    self.lighting_enabled = not self.lighting_enabled
                    print(f"Lighting: {'ON' if self.lighting_enabled else 'OFF'}")
                elif key == ord('e'):
                    self.effects_enabled = not self.effects_enabled
                    print(f"Effects: {'ON' if self.effects_enabled else 'OFF'}")
                elif key == ord('h'):
                    self.show_hud = not self.show_hud
                elif key == ord('d'):
                    self.show_landmarks = not self.show_landmarks
                elif key == ord('c'):
                    # Toggle between synthetic and real mode
                    new_mode = CameraMode.REAL if self.camera.mode == CameraMode.SYNTHETIC else CameraMode.SYNTHETIC
                    self.camera.switch_mode(new_mode)
                    print(f"Camera mode: {'Synthetic' if self.camera.mode == CameraMode.SYNTHETIC else 'Webcam'}")

        finally:
            # Cleanup
            self.camera.release()
            cv2.destroyAllWindows()

            # Print final statistics
            print("\n" + "="*50)
            print("SESSION SUMMARY")
            print("="*50)
            print(self.perf.get_summary())

        return True


def main():
    """Entry point."""
    import argparse

    parser = argparse.ArgumentParser(description='Holographic VFX System')
    parser.add_argument('--synthetic', action='store_true',
                       help='Use synthetic camera mode (no webcam required)')
    parser.add_argument('--quality', choices=['low', 'medium', 'high'],
                       default='medium', help='Performance quality preset')

    args = parser.parse_args()

    app = HolographicApp(use_synthetic=args.synthetic, quality=args.quality)
    success = app.run()

    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()
