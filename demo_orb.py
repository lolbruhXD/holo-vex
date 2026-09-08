"""
Interactive demo of the holographic orb with hand tracking.

Features:
- Real-time hand tracking
- Grab and move the orb with pinch gesture
- Orb reacts to hand proximity
- Theme switching with keyboard
- Multiple visual layers and effects

Controls:
- PINCH (thumb + index) to grab and move orb
- T - Cycle through themes
- + - Increase orb size
- - - Decrease orb size
- R - Reset orb position
- D - Toggle diagnostics
- Q - Quit
"""

import cv2
import numpy as np
import time
from hand_tracker import HandTracker
from holographic_orb import HolographicOrb
from holographic_base import Theme


class OrbDemo:
    """Interactive holographic orb demonstration."""

    def __init__(self):
        """Initialize demo."""
        # Hand tracking
        self.tracker = HandTracker(
            max_num_hands=2,
            min_detection_confidence=0.7,
            min_tracking_confidence=0.5
        )

        # Holographic orb
        self.orb = HolographicOrb(
            position=(0.5, 0.5, 0.0),
            scale=1.0,
            base_radius=60.0,
            theme=Theme.CYAN
        )

        # Camera
        self.cap = cv2.VideoCapture(0)
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)

        # State
        self.show_diagnostics = True
        self.frame_times = []
        self.max_frame_times = 30

        # Theme cycling
        self.themes = list(Theme)
        self.current_theme_idx = 0

        # Interaction
        self.grab_hand = None  # 'left' or 'right'
        self.hover_distance_threshold = 150.0

        print("Holographic Orb Demo")
        print("=" * 50)
        print("Controls:")
        print("  PINCH - Grab and move orb")
        print("  T - Cycle themes")
        print("  + - Increase size")
        print("  - - Decrease size")
        print("  R - Reset position")
        print("  D - Toggle diagnostics")
        print("  Q - Quit")
        print("=" * 50)

    def get_hand_3d_position(
        self,
        hand_data,
        frame_width: int,
        frame_height: int
    ) -> np.ndarray:
        """
        Get 3D position of hand (using index fingertip).

        Args:
            hand_data: HandLandmarks object
            frame_width: Frame width
            frame_height: Frame height

        Returns:
            Normalized (x, y, z) position
        """
        fingertips = self.tracker.get_fingertip_positions(
            hand_data,
            frame_width,
            frame_height
        )

        index_tip = fingertips['index']

        # Normalize to [0, 1]
        x_norm = index_tip[0] / frame_width
        y_norm = index_tip[1] / frame_height
        z_norm = index_tip[2]  # Already relative

        return np.array([x_norm, y_norm, z_norm], dtype=np.float32)

    def check_pinch_grab(
        self,
        hands_data: dict,
        frame_width: int,
        frame_height: int
    ):
        """
        Check for pinch gesture and handle grab/release.

        Args:
            hands_data: Dictionary with 'left' and 'right' HandLandmarks
            frame_width: Frame width
            frame_height: Frame height
        """
        # Check each hand
        for hand_key in ['left', 'right']:
            hand_data = hands_data[hand_key]
            if hand_data is None:
                # Release if this was the grabbing hand
                if self.grab_hand == hand_key:
                    self.orb.release()
                    self.grab_hand = None
                continue

            is_pinching = self.tracker.is_pinching(hand_data, threshold=0.04)
            hand_pos_3d = self.get_hand_3d_position(
                hand_data,
                frame_width,
                frame_height
            )

            if is_pinching:
                if self.grab_hand is None:
                    # Check if hand is near orb
                    distance = self.orb.distance_to_point(hand_pos_3d)
                    if distance < 0.15:  # Normalized distance threshold
                        # Start grab
                        self.orb.grab(hand_pos_3d)
                        self.grab_hand = hand_key
                elif self.grab_hand == hand_key:
                    # Continue moving grabbed orb
                    self.orb.move_to_grab_point(hand_pos_3d)
            else:
                # Release if this hand was grabbing
                if self.grab_hand == hand_key:
                    self.orb.release()
                    self.grab_hand = None

    def check_hover(
        self,
        hands_data: dict,
        frame_width: int,
        frame_height: int
    ):
        """
        Check if any hand is hovering near the orb.

        Args:
            hands_data: Dictionary with 'left' and 'right' HandLandmarks
            frame_width: Frame width
            frame_height: Frame height
        """
        any_hover = False

        for hand_key in ['left', 'right']:
            hand_data = hands_data[hand_key]
            if hand_data is None:
                continue

            hand_pos_3d = self.get_hand_3d_position(
                hand_data,
                frame_width,
                frame_height
            )

            # Convert to pixel distance for hover check
            orb_screen_pos = self.orb.get_screen_position(frame_width, frame_height)
            hand_screen_pos = (
                int(hand_pos_3d[0] * frame_width),
                int(hand_pos_3d[1] * frame_height)
            )

            pixel_distance = np.linalg.norm(
                np.array(orb_screen_pos) - np.array(hand_screen_pos)
            )

            if pixel_distance < self.hover_distance_threshold:
                any_hover = True
                break

        self.orb.is_hovered = any_hover

    def cycle_theme(self):
        """Cycle to next theme."""
        self.current_theme_idx = (self.current_theme_idx + 1) % len(self.themes)
        new_theme = self.themes[self.current_theme_idx]
        self.orb.set_theme(new_theme)
        print(f"Theme: {new_theme.value}")

    def draw_diagnostics(self, frame: np.ndarray, hands_data: dict):
        """Draw diagnostic overlay."""
        h, w = frame.shape[:2]

        # Semi-transparent background
        overlay = frame.copy()
        cv2.rectangle(
            overlay,
            (10, 10),
            (400, 250),
            (10, 13, 28),
            -1
        )
        cv2.addWeighted(overlay, 0.7, frame, 0.3, 0, frame)

        # Text
        y_offset = 35
        line_height = 25
        font = cv2.FONT_HERSHEY_SIMPLEX
        font_scale = 0.5
        color = (110, 231, 183)
        thickness = 1

        # FPS
        if len(self.frame_times) > 1:
            avg_fps = 1.0 / (sum(self.frame_times) / len(self.frame_times))
            cv2.putText(
                frame,
                f"FPS: {avg_fps:.1f}",
                (20, y_offset),
                font,
                font_scale,
                color,
                thickness
            )

        y_offset += line_height

        # Orb info
        cv2.putText(
            frame,
            f"Orb Position: ({self.orb.position[0]:.2f}, {self.orb.position[1]:.2f})",
            (20, y_offset),
            font,
            font_scale,
            color,
            thickness
        )
        y_offset += line_height

        cv2.putText(
            frame,
            f"Orb Scale: {self.orb.scale:.2f}",
            (20, y_offset),
            font,
            font_scale,
            color,
            thickness
        )
        y_offset += line_height

        cv2.putText(
            frame,
            f"Orb Radius: {self.orb.get_effective_radius():.1f}px",
            (20, y_offset),
            font,
            font_scale,
            color,
            thickness
        )
        y_offset += line_height

        cv2.putText(
            frame,
            f"Theme: {self.orb.theme.value}",
            (20, y_offset),
            font,
            font_scale,
            color,
            thickness
        )
        y_offset += line_height

        cv2.putText(
            frame,
            f"Particles: {len(self.orb.particles)}",
            (20, y_offset),
            font,
            font_scale,
            color,
            thickness
        )
        y_offset += line_height

        # Interaction state
        state = "GRABBED" if self.orb.is_grabbed else ("HOVER" if self.orb.is_hovered else "IDLE")
        state_color = (244, 114, 182) if self.orb.is_grabbed else (
            (233, 165, 104) if self.orb.is_hovered else (110, 231, 183)
        )
        cv2.putText(
            frame,
            f"State: {state}",
            (20, y_offset),
            font,
            font_scale,
            state_color,
            thickness + 1
        )
        y_offset += line_height

        # Hand tracking
        tracker_diag = self.tracker.get_diagnostics()
        left_detected = "YES" if hands_data['left'] else "NO"
        right_detected = "YES" if hands_data['right'] else "NO"

        cv2.putText(
            frame,
            f"Left Hand: {left_detected}  Right Hand: {right_detected}",
            (20, y_offset),
            font,
            font_scale,
            color,
            thickness
        )

    def run(self):
        """Run the demo loop."""
        prev_time = time.time()

        try:
            while True:
                ret, frame = self.cap.read()
                if not ret:
                    print("Failed to grab frame")
                    break

                # Calculate delta time
                current_time = time.time()
                dt = current_time - prev_time
                prev_time = current_time

                # Track frame times for FPS
                self.frame_times.append(dt)
                if len(self.frame_times) > self.max_frame_times:
                    self.frame_times.pop(0)

                h, w = frame.shape[:2]

                # Process hands
                hands_data = self.tracker.process_frame(frame)

                # Handle grab/release
                self.check_pinch_grab(hands_data, w, h)

                # Handle hover
                if not self.orb.is_grabbed:
                    self.check_hover(hands_data, w, h)

                # Update orb
                self.orb.update(dt)

                # Create dark background for holographic effect
                dark_frame = (frame * 0.2).astype(np.uint8)

                # Render orb
                self.orb.render(dark_frame)

                # Draw hand landmarks (optional)
                for hand_key in ['left', 'right']:
                    hand_data = hands_data[hand_key]
                    if hand_data:
                        # Draw fingertips
                        fingertips = self.tracker.get_fingertip_positions(hand_data, w, h)
                        for finger_name, (fx, fy, fz) in fingertips.items():
                            cv2.circle(
                                dark_frame,
                                (int(fx), int(fy)),
                                8,
                                (56, 189, 248),
                                2
                            )

                        # Check if pinching
                        if self.tracker.is_pinching(hand_data, threshold=0.04):
                            index_pos = fingertips['index']
                            cv2.circle(
                                dark_frame,
                                (int(index_pos[0]), int(index_pos[1])),
                                15,
                                (244, 114, 182),
                                3
                            )

                # Draw diagnostics
                if self.show_diagnostics:
                    self.draw_diagnostics(dark_frame, hands_data)

                # Display
                cv2.imshow('Holographic Orb Demo', dark_frame)

                # Handle keyboard input
                key = cv2.waitKey(1) & 0xFF

                if key == ord('q'):
                    print("Exiting...")
                    break
                elif key == ord('t'):
                    self.cycle_theme()
                elif key == ord('+') or key == ord('='):
                    self.orb.set_scale(self.orb.scale + 0.1)
                    print(f"Scale: {self.orb.scale:.2f}")
                elif key == ord('-') or key == ord('_'):
                    self.orb.set_scale(self.orb.scale - 0.1)
                    print(f"Scale: {self.orb.scale:.2f}")
                elif key == ord('r'):
                    self.orb.set_position(0.5, 0.5, 0.0)
                    self.orb.set_scale(1.0)
                    print("Orb reset")
                elif key == ord('d'):
                    self.show_diagnostics = not self.show_diagnostics

        finally:
            self.cleanup()

    def cleanup(self):
        """Clean up resources."""
        self.tracker.release()
        self.cap.release()
        cv2.destroyAllWindows()
        print("Cleanup complete")


if __name__ == "__main__":
    demo = OrbDemo()
    demo.run()
