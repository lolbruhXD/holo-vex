"""
Demo application for hand tracking system.
Shows real-time hand detection with landmarks, diagnostics, and gesture recognition.
"""

import cv2
import numpy as np
from hand_tracker import HandTracker
from typing import Optional


class TrackingDemo:
    """Interactive demo of hand tracking capabilities."""

    def __init__(self, camera_id: int = 0):
        """
        Initialize tracking demo.

        Args:
            camera_id: Camera device index (0 for default)
        """
        self.tracker = HandTracker(
            max_num_hands=2,
            min_detection_confidence=0.7,
            min_tracking_confidence=0.5,
            model_complexity=1
        )

        self.cap = cv2.VideoCapture(camera_id)

        # Set camera properties for better performance
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
        self.cap.set(cv2.CAP_PROP_FPS, 60)

        # Get actual dimensions
        self.frame_width = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        self.frame_height = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

        # Display options
        self.show_landmarks = True
        self.show_fingertips = True
        self.show_palm = True
        self.show_diagnostics = True

        # FPS calculation
        self.fps_history = []
        self.max_fps_samples = 30

        print(f"Camera initialized: {self.frame_width}x{self.frame_height}")

    def draw_hud(self, frame: np.ndarray, fps: float):
        """
        Draw heads-up display with controls and diagnostics.

        Args:
            frame: Frame to draw on (modified in-place)
            fps: Current frames per second
        """
        # Semi-transparent overlay
        overlay = frame.copy()

        # Top bar background
        cv2.rectangle(overlay, (0, 0), (self.frame_width, 80), (10, 15, 25), -1)

        # Blend overlay
        cv2.addWeighted(overlay, 0.85, frame, 0.15, 0, frame)

        # Title
        cv2.putText(
            frame,
            "HOLOGRAPHIC VFX - HAND TRACKING",
            (20, 35),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.8,
            (100, 255, 200),
            2
        )

        # FPS counter
        fps_text = f"FPS: {fps:.1f}"
        cv2.putText(
            frame,
            fps_text,
            (self.frame_width - 150, 35),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            (255, 255, 255),
            2
        )

        # Controls
        controls = [
            "[L] Toggle Landmarks",
            "[F] Toggle Fingertips",
            "[P] Toggle Palm",
            "[D] Toggle Diagnostics",
            "[Q] Quit"
        ]

        y_offset = 60
        for i, control in enumerate(controls):
            cv2.putText(
                frame,
                control,
                (20 + i * 220, y_offset),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.5,
                (180, 180, 180),
                1
            )

    def draw_fingertips(self, frame: np.ndarray, hand_data, handedness: str):
        """
        Draw fingertip markers.

        Args:
            frame: Frame to draw on
            hand_data: HandLandmarks object
            handedness: "left" or "right"
        """
        fingertips = self.tracker.get_fingertip_positions(
            hand_data,
            self.frame_width,
            self.frame_height
        )

        # Color based on handedness
        color = (255, 100, 100) if handedness == "left" else (100, 100, 255)

        finger_names = ['thumb', 'index', 'middle', 'ring', 'pinky']

        for name in finger_names:
            x, y, z = fingertips[name]
            x, y = int(x), int(y)

            # Draw fingertip marker
            cv2.circle(frame, (x, y), 12, color, 2)
            cv2.circle(frame, (x, y), 4, (255, 255, 255), -1)

            # Draw label
            label_y = y - 20
            cv2.putText(
                frame,
                name[:3].upper(),
                (x - 15, label_y),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.4,
                color,
                1
            )

    def draw_palm(self, frame: np.ndarray, hand_data, handedness: str):
        """
        Draw palm center marker.

        Args:
            frame: Frame to draw on
            hand_data: HandLandmarks object
            handedness: "left" or "right"
        """
        palm_x, palm_y, palm_z = self.tracker.get_palm_center(
            hand_data,
            self.frame_width,
            self.frame_height
        )

        x, y = int(palm_x), int(palm_y)

        # Color based on handedness
        color = (255, 150, 100) if handedness == "left" else (100, 150, 255)

        # Draw palm marker
        cv2.circle(frame, (x, y), 20, color, 2)
        cv2.circle(frame, (x, y), 8, color, -1)

        # Draw label
        cv2.putText(
            frame,
            f"{handedness.upper()} PALM",
            (x - 40, y + 40),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.5,
            color,
            2
        )

    def draw_gestures(self, frame: np.ndarray, hand_data, handedness: str):
        """
        Draw detected gestures.

        Args:
            frame: Frame to draw on
            hand_data: HandLandmarks object
            handedness: "left" or "right"
        """
        # Check for pinch
        is_pinching = self.tracker.is_pinching(hand_data, threshold=0.05)

        if is_pinching:
            # Get index fingertip position
            fingertips = self.tracker.get_fingertip_positions(
                hand_data,
                self.frame_width,
                self.frame_height
            )
            x, y, _ = fingertips['index']
            x, y = int(x), int(y)

            # Draw pinch indicator
            cv2.circle(frame, (x, y), 30, (0, 255, 0), 3)
            cv2.putText(
                frame,
                "PINCH",
                (x - 30, y - 40),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.6,
                (0, 255, 0),
                2
            )

    def draw_diagnostics_panel(self, frame: np.ndarray, hands_data: dict):
        """
        Draw diagnostics information panel.

        Args:
            frame: Frame to draw on
            hands_data: Dictionary with left/right hand data
        """
        diag = self.tracker.get_diagnostics()

        # Panel background
        panel_x = self.frame_width - 300
        panel_y = 100
        panel_width = 280
        panel_height = 200

        overlay = frame.copy()
        cv2.rectangle(
            overlay,
            (panel_x, panel_y),
            (panel_x + panel_width, panel_y + panel_height),
            (10, 15, 25),
            -1
        )
        cv2.addWeighted(overlay, 0.85, frame, 0.15, 0, frame)

        # Border
        cv2.rectangle(
            frame,
            (panel_x, panel_y),
            (panel_x + panel_width, panel_y + panel_height),
            (100, 255, 200),
            2
        )

        # Title
        cv2.putText(
            frame,
            "DIAGNOSTICS",
            (panel_x + 10, panel_y + 25),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.6,
            (100, 255, 200),
            2
        )

        # Diagnostic info
        info_lines = [
            f"Frames: {diag['frame_count']}",
            f"Failures: {diag['detection_failures']}",
            f"Failure Rate: {diag['failure_rate']*100:.1f}%",
            "",
            f"Left Hand: {'DETECTED' if hands_data['left'] else 'MISSING'}",
            f"Right Hand: {'DETECTED' if hands_data['right'] else 'MISSING'}",
        ]

        # Add confidence if hands detected
        if hands_data['left']:
            conf = hands_data['left'].confidence * 100
            info_lines.append(f"Left Conf: {conf:.1f}%")

        if hands_data['right']:
            conf = hands_data['right'].confidence * 100
            info_lines.append(f"Right Conf: {conf:.1f}%")

        y_offset = panel_y + 55
        for line in info_lines:
            cv2.putText(
                frame,
                line,
                (panel_x + 15, y_offset),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.5,
                (220, 220, 220),
                1
            )
            y_offset += 25

    def run(self):
        """Run the tracking demo loop."""
        print("\n=== Hand Tracking Demo ===")
        print("Controls:")
        print("  [L] - Toggle landmark display")
        print("  [F] - Toggle fingertip markers")
        print("  [P] - Toggle palm center")
        print("  [D] - Toggle diagnostics")
        print("  [Q] - Quit\n")

        clock = cv2.getTickCount()

        while True:
            ret, frame = self.cap.read()
            if not ret:
                print("Failed to grab frame")
                break

            # Calculate FPS
            new_clock = cv2.getTickCount()
            fps = cv2.getTickFrequency() / (new_clock - clock)
            clock = new_clock

            self.fps_history.append(fps)
            if len(self.fps_history) > self.max_fps_samples:
                self.fps_history.pop(0)
            avg_fps = np.mean(self.fps_history)

            # Process hand tracking
            hands_data = self.tracker.process_frame(frame)

            # Flip frame back for display
            frame = cv2.flip(frame, 1)

            # Draw HUD
            self.draw_hud(frame, avg_fps)

            # Draw tracking visualizations
            for handedness in ['left', 'right']:
                hand_data = hands_data[handedness]

                if hand_data is None:
                    continue

                # Draw landmarks
                if self.show_landmarks:
                    self.tracker.draw_landmarks(frame, hand_data, connections=True)

                # Draw fingertips
                if self.show_fingertips:
                    self.draw_fingertips(frame, hand_data, handedness)

                # Draw palm
                if self.show_palm:
                    self.draw_palm(frame, hand_data, handedness)

                # Draw gestures
                self.draw_gestures(frame, hand_data, handedness)

            # Draw diagnostics panel
            if self.show_diagnostics:
                self.draw_diagnostics_panel(frame, hands_data)

            # Display
            cv2.imshow('Hand Tracking Demo', frame)

            # Handle keyboard input
            key = cv2.waitKey(1) & 0xFF

            if key == ord('q'):
                break
            elif key == ord('l'):
                self.show_landmarks = not self.show_landmarks
            elif key == ord('f'):
                self.show_fingertips = not self.show_fingertips
            elif key == ord('p'):
                self.show_palm = not self.show_palm
            elif key == ord('d'):
                self.show_diagnostics = not self.show_diagnostics

        self.cleanup()

    def cleanup(self):
        """Release resources."""
        print("\nCleaning up...")
        self.tracker.release()
        self.cap.release()
        cv2.destroyAllWindows()
        print("Done.")


def main():
    """Entry point."""
    try:
        demo = TrackingDemo(camera_id=0)
        demo.run()
    except KeyboardInterrupt:
        print("\n\nInterrupted by user")
    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
