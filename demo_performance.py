"""
Advanced hand tracking demo with comprehensive performance monitoring.
Features FPS display, frame timing, optimization controls, and quality presets.
"""

import cv2
import numpy as np
from hand_tracker import HandTracker
from performance_monitor import PerformanceMonitor, QualityPreset
from typing import Optional


class PerformanceDemo:
    """Hand tracking demo with advanced performance monitoring and optimization."""

    def __init__(self, camera_id: int = 0, quality_preset: QualityPreset = QualityPreset.MEDIUM):
        """
        Initialize performance demo.

        Args:
            camera_id: Camera device index
            quality_preset: Initial quality preset
        """
        # Initialize performance monitor first
        self.perf_monitor = PerformanceMonitor(
            window_size=60,
            quality_preset=quality_preset
        )

        # Get quality settings
        settings = self.perf_monitor.quality_settings

        # Initialize hand tracker with quality settings
        self.tracker = HandTracker(
            max_num_hands=settings.max_hands,
            min_detection_confidence=settings.min_detection_confidence,
            min_tracking_confidence=settings.min_tracking_confidence,
            model_complexity=settings.model_complexity
        )

        # Initialize camera
        self.cap = cv2.VideoCapture(camera_id)
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, settings.resolution[0])
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, settings.resolution[1])
        self.cap.set(cv2.CAP_PROP_FPS, settings.target_fps)

        # Get actual dimensions
        self.frame_width = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        self.frame_height = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

        # Display options
        self.show_landmarks = True
        self.show_performance = True
        self.show_graph = True
        self.show_recommendations = False
        self.show_breakdown = True

        # Frame skipping for optimization
        self.frame_skip = 1  # Process every Nth frame

        # Performance graph
        self.graph_history = []
        self.max_graph_points = 100

        print(f"Demo initialized: {self.frame_width}x{self.frame_height}")
        print(f"Quality: {quality_preset.value}")
        print(f"Target FPS: {settings.target_fps}")

    def draw_performance_hud(self, frame: np.ndarray):
        """
        Draw comprehensive performance HUD.

        Args:
            frame: Frame to draw on (modified in-place)
        """
        metrics = self.perf_monitor.get_metrics()

        # Top bar with title and FPS
        overlay = frame.copy()
        cv2.rectangle(overlay, (0, 0), (self.frame_width, 100), (5, 7, 12), -1)
        cv2.addWeighted(overlay, 0.9, frame, 0.1, 0, frame)

        # Title
        cv2.putText(
            frame,
            "HOLOGRAPHIC VFX - PERFORMANCE OPTIMIZED",
            (20, 35),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            (56, 191, 232),
            2
        )

        # FPS - color coded
        fps_color = self._get_fps_color(metrics.avg_fps)
        fps_text = f"FPS: {metrics.avg_fps:.1f}"
        cv2.putText(
            frame,
            fps_text,
            (self.frame_width - 180, 35),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.8,
            fps_color,
            2
        )

        # Frame time
        time_text = f"{metrics.frame_time_ms:.1f}ms"
        cv2.putText(
            frame,
            time_text,
            (self.frame_width - 180, 65),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.5,
            (180, 180, 180),
            1
        )

        # Controls
        controls = [
            "[L] Landmarks",
            "[P] Perf Panel",
            "[G] Graph",
            "[R] Recommendations",
            "[1-4] Quality",
            "[Q] Quit"
        ]

        y_offset = 75
        x_offset = 20
        for control in controls:
            cv2.putText(
                frame,
                control,
                (x_offset, y_offset),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.45,
                (160, 160, 160),
                1
            )
            x_offset += 160

    def draw_performance_panel(self, frame: np.ndarray):
        """
        Draw detailed performance metrics panel.

        Args:
            frame: Frame to draw on
        """
        metrics = self.perf_monitor.get_metrics()
        breakdown = self.perf_monitor.get_performance_breakdown()

        # Panel dimensions
        panel_x = 20
        panel_y = 120
        panel_width = 320
        panel_height = 280

        # Background
        overlay = frame.copy()
        cv2.rectangle(
            overlay,
            (panel_x, panel_y),
            (panel_x + panel_width, panel_y + panel_height),
            (10, 13, 19),
            -1
        )
        cv2.addWeighted(overlay, 0.92, frame, 0.08, 0, frame)

        # Border
        cv2.rectangle(
            frame,
            (panel_x, panel_y),
            (panel_x + panel_width, panel_y + panel_height),
            (56, 191, 232),
            2
        )

        # Title
        cv2.putText(
            frame,
            "PERFORMANCE METRICS",
            (panel_x + 15, panel_y + 30),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.6,
            (56, 191, 232),
            2
        )

        # Metrics
        y = panel_y + 60
        spacing = 25

        # FPS stats
        self._draw_metric_line(
            frame, panel_x + 15, y,
            "FPS (avg):", f"{metrics.avg_fps:.1f}",
            (220, 220, 220)
        )
        y += spacing

        self._draw_metric_line(
            frame, panel_x + 15, y,
            "FPS (min/max):", f"{metrics.min_fps:.1f} / {metrics.max_fps:.1f}",
            (180, 180, 180)
        )
        y += spacing

        # Timing breakdown
        y += 10
        cv2.putText(
            frame,
            "Frame Time Breakdown:",
            (panel_x + 15, y),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.5,
            (100, 255, 200),
            1
        )
        y += spacing

        self._draw_metric_line(
            frame, panel_x + 25, y,
            "Tracking:", f"{metrics.tracking_time_ms:.2f}ms ({breakdown['tracking']:.1f}%)",
            (220, 220, 220)
        )
        y += spacing

        self._draw_metric_line(
            frame, panel_x + 25, y,
            "Render:", f"{metrics.render_time_ms:.2f}ms ({breakdown['render']:.1f}%)",
            (220, 220, 220)
        )
        y += spacing

        self._draw_metric_line(
            frame, panel_x + 25, y,
            "Total:", f"{metrics.frame_time_ms:.2f}ms",
            (220, 220, 220)
        )
        y += spacing

        # Frame stats
        y += 10
        self._draw_metric_line(
            frame, panel_x + 15, y,
            "Frames:", f"{metrics.total_frames}",
            (220, 220, 220)
        )
        y += spacing

        drop_rate = metrics.dropped_frames / max(metrics.total_frames, 1) * 100
        drop_color = (100, 255, 100) if drop_rate < 5 else (100, 100, 255)
        self._draw_metric_line(
            frame, panel_x + 15, y,
            "Dropped:", f"{metrics.dropped_frames} ({drop_rate:.1f}%)",
            drop_color
        )
        y += spacing

        # Memory
        self._draw_metric_line(
            frame, panel_x + 15, y,
            "Memory:", f"{metrics.memory_usage_mb:.1f} MB",
            (220, 220, 220)
        )

    def draw_performance_graph(self, frame: np.ndarray):
        """
        Draw real-time FPS graph.

        Args:
            frame: Frame to draw on
        """
        metrics = self.perf_monitor.get_metrics()

        # Add current FPS to history
        self.graph_history.append(metrics.fps)
        if len(self.graph_history) > self.max_graph_points:
            self.graph_history.pop(0)

        # Graph dimensions
        graph_x = self.frame_width - 370
        graph_y = 120
        graph_width = 350
        graph_height = 150

        # Background
        overlay = frame.copy()
        cv2.rectangle(
            overlay,
            (graph_x, graph_y),
            (graph_x + graph_width, graph_y + graph_height),
            (10, 13, 19),
            -1
        )
        cv2.addWeighted(overlay, 0.92, frame, 0.08, 0, frame)

        # Border
        cv2.rectangle(
            frame,
            (graph_x, graph_y),
            (graph_x + graph_width, graph_y + graph_height),
            (56, 191, 232),
            2
        )

        # Title
        cv2.putText(
            frame,
            "FPS GRAPH",
            (graph_x + 15, graph_y + 25),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.6,
            (56, 191, 232),
            2
        )

        if len(self.graph_history) < 2:
            return

        # Calculate graph area
        plot_x = graph_x + 15
        plot_y = graph_y + 40
        plot_width = graph_width - 30
        plot_height = graph_height - 50

        # Determine scale
        max_fps = max(self.graph_history) if self.graph_history else 60
        max_fps = max(max_fps, 30)  # Minimum scale of 30 FPS
        scale_y = plot_height / max_fps

        # Draw reference lines
        target_fps = self.perf_monitor.quality_settings.target_fps
        target_y = int(plot_y + plot_height - (target_fps * scale_y))
        cv2.line(
            frame,
            (plot_x, target_y),
            (plot_x + plot_width, target_y),
            (100, 255, 100),
            1,
            cv2.LINE_AA
        )
        cv2.putText(
            frame,
            f"{target_fps}",
            (plot_x + plot_width + 5, target_y + 5),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.35,
            (100, 255, 100),
            1
        )

        # Draw graph
        points = []
        for i, fps in enumerate(self.graph_history):
            x = plot_x + int((i / self.max_graph_points) * plot_width)
            y = plot_y + plot_height - int(min(fps, max_fps) * scale_y)
            points.append((x, y))

        # Draw lines
        for i in range(len(points) - 1):
            color = self._get_fps_color(self.graph_history[i])
            cv2.line(frame, points[i], points[i + 1], color, 2, cv2.LINE_AA)

        # Draw current FPS value
        if points:
            last_x, last_y = points[-1]
            cv2.circle(frame, (last_x, last_y), 4, (255, 255, 255), -1)

    def draw_recommendations_panel(self, frame: np.ndarray):
        """
        Draw optimization recommendations panel.

        Args:
            frame: Frame to draw on
        """
        recommendations = self.perf_monitor.get_optimization_recommendations()

        # Panel dimensions
        panel_x = 20
        panel_y = self.frame_height - 200
        panel_width = self.frame_width - 40
        panel_height = 180

        # Background
        overlay = frame.copy()
        cv2.rectangle(
            overlay,
            (panel_x, panel_y),
            (panel_x + panel_width, panel_y + panel_height),
            (10, 13, 19),
            -1
        )
        cv2.addWeighted(overlay, 0.92, frame, 0.08, 0, frame)

        # Border
        cv2.rectangle(
            frame,
            (panel_x, panel_y),
            (panel_x + panel_width, panel_y + panel_height),
            (233, 165, 104),
            2
        )

        # Title
        cv2.putText(
            frame,
            "OPTIMIZATION RECOMMENDATIONS",
            (panel_x + 15, panel_y + 30),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.6,
            (233, 165, 104),
            2
        )

        # Recommendations
        y = panel_y + 60
        for i, rec in enumerate(recommendations[:4]):  # Show max 4
            # Wrap text if too long
            if len(rec) > 80:
                words = rec.split()
                lines = []
                current_line = []
                for word in words:
                    current_line.append(word)
                    if len(' '.join(current_line)) > 80:
                        current_line.pop()
                        lines.append(' '.join(current_line))
                        current_line = [word]
                if current_line:
                    lines.append(' '.join(current_line))
            else:
                lines = [rec]

            for line in lines:
                cv2.putText(
                    frame,
                    f"• {line}",
                    (panel_x + 20, y),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.45,
                    (220, 220, 220),
                    1
                )
                y += 25

    def draw_timing_bars(self, frame: np.ndarray):
        """
        Draw timing breakdown as horizontal bars.

        Args:
            frame: Frame to draw on
        """
        breakdown = self.perf_monitor.get_performance_breakdown()
        metrics = self.perf_monitor.get_metrics()

        # Bar dimensions
        bar_x = 360
        bar_y = 120
        bar_width = 300
        bar_height = 25
        spacing = 35

        # Draw bars for tracking, render, other
        components = [
            ('Tracking', breakdown['tracking'], (110, 231, 183)),
            ('Render', breakdown['render'], (56, 191, 232)),
            ('Other', breakdown['other'], (180, 180, 180))
        ]

        for i, (label, percentage, color) in enumerate(components):
            y = bar_y + i * spacing

            # Label
            cv2.putText(
                frame,
                f"{label}:",
                (bar_x, y + 18),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.5,
                (220, 220, 220),
                1
            )

            # Bar background
            cv2.rectangle(
                frame,
                (bar_x + 100, y),
                (bar_x + 100 + bar_width, y + bar_height),
                (30, 35, 45),
                -1
            )

            # Bar fill
            fill_width = int((percentage / 100) * bar_width)
            cv2.rectangle(
                frame,
                (bar_x + 100, y),
                (bar_x + 100 + fill_width, y + bar_height),
                color,
                -1
            )

            # Percentage text
            cv2.putText(
                frame,
                f"{percentage:.1f}%",
                (bar_x + 100 + bar_width + 10, y + 18),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.45,
                color,
                1
            )

    def _draw_metric_line(self, frame, x, y, label, value, color):
        """Helper to draw a metric line."""
        cv2.putText(
            frame, label, (x, y),
            cv2.FONT_HERSHEY_SIMPLEX, 0.45, (180, 180, 180), 1
        )
        cv2.putText(
            frame, value, (x + 150, y),
            cv2.FONT_HERSHEY_SIMPLEX, 0.45, color, 1
        )

    def _get_fps_color(self, fps: float) -> tuple:
        """Get color based on FPS value."""
        target = self.perf_monitor.quality_settings.target_fps
        if fps >= target * 0.9:
            return (100, 255, 100)  # Green
        elif fps >= target * 0.6:
            return (100, 200, 255)  # Yellow
        else:
            return (100, 100, 255)  # Red

    def change_quality_preset(self, preset: QualityPreset):
        """
        Change quality preset and reinitialize tracker.

        Args:
            preset: New quality preset
        """
        print(f"\nChanging quality to: {preset.value}")

        # Update performance monitor
        self.perf_monitor.quality_preset = preset
        self.perf_monitor.quality_settings = self.perf_monitor.quality_settings.from_preset(preset)
        settings = self.perf_monitor.quality_settings

        # Reinitialize tracker
        self.tracker.release()
        self.tracker = HandTracker(
            max_num_hands=settings.max_hands,
            min_detection_confidence=settings.min_detection_confidence,
            min_tracking_confidence=settings.min_tracking_confidence,
            model_complexity=settings.model_complexity
        )

        # Update camera settings
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, settings.resolution[0])
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, settings.resolution[1])
        self.cap.set(cv2.CAP_PROP_FPS, settings.target_fps)

        self.frame_width = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        self.frame_height = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

        print(f"Resolution: {self.frame_width}x{self.frame_height}")
        print(f"Target FPS: {settings.target_fps}")

    def run(self):
        """Run the performance demo loop."""
        print("\n╔══════════════════════════════════════════════════════════╗")
        print("║      HOLOGRAPHIC VFX - PERFORMANCE DEMO                  ║")
        print("╠══════════════════════════════════════════════════════════╣")
        print("║ Controls:                                                ║")
        print("║   [L] - Toggle landmarks                                 ║")
        print("║   [P] - Toggle performance panel                         ║")
        print("║   [G] - Toggle FPS graph                                 ║")
        print("║   [R] - Toggle recommendations                           ║")
        print("║   [B] - Toggle timing breakdown                          ║")
        print("║   [1] - LOW quality (max performance)                    ║")
        print("║   [2] - MEDIUM quality (balanced)                        ║")
        print("║   [3] - HIGH quality (max accuracy)                      ║")
        print("║   [4] - ADAPTIVE quality (auto-adjust)                   ║")
        print("║   [S] - Print performance summary                        ║")
        print("║   [Q] - Quit                                             ║")
        print("╚══════════════════════════════════════════════════════════╝\n")

        while True:
            self.perf_monitor.start_frame()

            ret, frame = self.cap.read()
            if not ret:
                print("Failed to grab frame")
                break

            # Start tracking timing
            self.perf_monitor.start_tracking()

            # Process hand tracking (with optional frame skipping)
            if self.perf_monitor.should_process_frame(self.frame_skip):
                hands_data = self.tracker.process_frame(frame)
            else:
                hands_data = {'left': None, 'right': None}

            self.perf_monitor.end_tracking()

            # Flip frame for display
            frame = cv2.flip(frame, 1)

            # Start render timing
            self.perf_monitor.start_render()

            # Draw visualizations
            self.draw_performance_hud(frame)

            # Draw hand landmarks if enabled
            if self.show_landmarks:
                for handedness in ['left', 'right']:
                    hand_data = hands_data[handedness]
                    if hand_data:
                        self.tracker.draw_landmarks(frame, hand_data, connections=True)

            # Draw performance panels
            if self.show_performance:
                self.draw_performance_panel(frame)

            if self.show_graph:
                self.draw_performance_graph(frame)

            if self.show_recommendations:
                self.draw_recommendations_panel(frame)

            if self.show_breakdown:
                self.draw_timing_bars(frame)

            self.perf_monitor.end_render()

            # Display frame
            cv2.imshow('Performance Demo', frame)

            self.perf_monitor.end_frame()

            # Clean cache periodically
            if self.perf_monitor.total_frames % 100 == 0:
                self.perf_monitor.cache_clean()

            # Handle keyboard input
            key = cv2.waitKey(1) & 0xFF

            if key == ord('q'):
                break
            elif key == ord('l'):
                self.show_landmarks = not self.show_landmarks
            elif key == ord('p'):
                self.show_performance = not self.show_performance
            elif key == ord('g'):
                self.show_graph = not self.show_graph
            elif key == ord('r'):
                self.show_recommendations = not self.show_recommendations
            elif key == ord('b'):
                self.show_breakdown = not self.show_breakdown
            elif key == ord('1'):
                self.change_quality_preset(QualityPreset.LOW)
            elif key == ord('2'):
                self.change_quality_preset(QualityPreset.MEDIUM)
            elif key == ord('3'):
                self.change_quality_preset(QualityPreset.HIGH)
            elif key == ord('4'):
                self.change_quality_preset(QualityPreset.ADAPTIVE)
            elif key == ord('s'):
                print(self.perf_monitor.get_summary())

        self.cleanup()

    def cleanup(self):
        """Release resources and print final summary."""
        print("\n" + self.perf_monitor.get_summary())
        print("\nCleaning up...")
        self.tracker.release()
        self.cap.release()
        cv2.destroyAllWindows()
        print("Done.")


def main():
    """Entry point."""
    import argparse

    parser = argparse.ArgumentParser(description="Hand Tracking Performance Demo")
    parser.add_argument(
        '--quality',
        type=str,
        choices=['low', 'medium', 'high', 'adaptive'],
        default='medium',
        help='Quality preset (default: medium)'
    )
    parser.add_argument(
        '--camera',
        type=int,
        default=0,
        help='Camera device ID (default: 0)'
    )

    args = parser.parse_args()

    # Map string to enum
    quality_map = {
        'low': QualityPreset.LOW,
        'medium': QualityPreset.MEDIUM,
        'high': QualityPreset.HIGH,
        'adaptive': QualityPreset.ADAPTIVE
    }

    try:
        demo = PerformanceDemo(
            camera_id=args.camera,
            quality_preset=quality_map[args.quality]
        )
        demo.run()
    except KeyboardInterrupt:
        print("\n\nInterrupted by user")
    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
