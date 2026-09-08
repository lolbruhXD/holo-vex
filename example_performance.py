"""
Quick example demonstrating performance monitoring integration.
Minimal example showing how to add performance tracking to hand tracking code.
"""

import cv2
import numpy as np
from hand_tracker import HandTracker
from performance_monitor import PerformanceMonitor, QualityPreset


def simple_performance_demo():
    """Minimal example with performance monitoring."""

    # Initialize with MEDIUM quality (balanced)
    perf_monitor = PerformanceMonitor(
        window_size=60,
        quality_preset=QualityPreset.MEDIUM
    )

    settings = perf_monitor.quality_settings

    # Initialize hand tracker with quality settings
    tracker = HandTracker(
        max_num_hands=settings.max_hands,
        min_detection_confidence=settings.min_detection_confidence,
        min_tracking_confidence=settings.min_tracking_confidence,
        model_complexity=settings.model_complexity
    )

    # Initialize camera
    cap = cv2.VideoCapture(0)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, settings.resolution[0])
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, settings.resolution[1])

    frame_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    frame_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

    print("Performance Monitoring Demo")
    print("Press 'Q' to quit, 'S' for summary\n")

    try:
        while True:
            # === FRAME START ===
            perf_monitor.start_frame()

            ret, frame = cap.read()
            if not ret:
                break

            # === TRACKING PHASE ===
            perf_monitor.start_tracking()
            hands_data = tracker.process_frame(frame)
            perf_monitor.end_tracking()

            # Flip for display
            frame = cv2.flip(frame, 1)

            # === RENDER PHASE ===
            perf_monitor.start_render()

            # Draw hands
            for handedness in ['left', 'right']:
                hand_data = hands_data[handedness]
                if hand_data:
                    tracker.draw_landmarks(frame, hand_data, connections=True)

            # Draw simple FPS overlay
            metrics = perf_monitor.get_metrics()

            # Background bar
            cv2.rectangle(frame, (0, 0), (frame_width, 60), (10, 15, 25), -1)

            # FPS with color coding
            fps_color = (100, 255, 100) if metrics.avg_fps >= 25 else (100, 100, 255)
            cv2.putText(
                frame,
                f"FPS: {metrics.avg_fps:.1f}",
                (20, 35),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.8,
                fps_color,
                2
            )

            # Frame time
            cv2.putText(
                frame,
                f"Frame: {metrics.frame_time_ms:.1f}ms",
                (250, 35),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.6,
                (200, 200, 200),
                1
            )

            # Tracking time
            cv2.putText(
                frame,
                f"Track: {metrics.tracking_time_ms:.1f}ms",
                (500, 35),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.6,
                (200, 200, 200),
                1
            )

            perf_monitor.end_render()

            # === FRAME END ===
            perf_monitor.end_frame()

            # Display
            cv2.imshow('Simple Performance Demo', frame)

            # Handle input
            key = cv2.waitKey(1) & 0xFF
            if key == ord('q'):
                break
            elif key == ord('s'):
                print("\n" + perf_monitor.get_summary())
                recommendations = perf_monitor.get_optimization_recommendations()
                print("\nRecommendations:")
                for rec in recommendations:
                    print(f"  • {rec}")

    finally:
        # Cleanup and final summary
        print("\n" + perf_monitor.get_summary())
        tracker.release()
        cap.release()
        cv2.destroyAllWindows()


def benchmark_quality_presets():
    """Benchmark all quality presets to compare performance."""

    print("╔══════════════════════════════════════════════════════════╗")
    print("║           QUALITY PRESET BENCHMARK                       ║")
    print("╚══════════════════════════════════════════════════════════╝\n")

    presets = [
        QualityPreset.LOW,
        QualityPreset.MEDIUM,
        QualityPreset.HIGH
    ]

    results = []

    for preset in presets:
        print(f"Testing {preset.value.upper()}...")

        perf_monitor = PerformanceMonitor(window_size=30, quality_preset=preset)
        settings = perf_monitor.quality_settings

        tracker = HandTracker(
            max_num_hands=settings.max_hands,
            min_detection_confidence=settings.min_detection_confidence,
            min_tracking_confidence=settings.min_tracking_confidence,
            model_complexity=settings.model_complexity
        )

        cap = cv2.VideoCapture(0)
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, settings.resolution[0])
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, settings.resolution[1])

        # Run for 100 frames
        for i in range(100):
            perf_monitor.start_frame()

            ret, frame = cap.read()
            if not ret:
                break

            perf_monitor.start_tracking()
            hands_data = tracker.process_frame(frame)
            perf_monitor.end_tracking()

            perf_monitor.start_render()
            frame = cv2.flip(frame, 1)
            for handedness in ['left', 'right']:
                if hands_data[handedness]:
                    tracker.draw_landmarks(frame, hands_data[handedness])
            perf_monitor.end_render()

            perf_monitor.end_frame()

        metrics = perf_monitor.get_metrics()
        results.append({
            'preset': preset.value.upper(),
            'resolution': f"{settings.resolution[0]}x{settings.resolution[1]}",
            'avg_fps': metrics.avg_fps,
            'frame_time': metrics.frame_time_ms,
            'tracking_time': metrics.tracking_time_ms
        })

        tracker.release()
        cap.release()

    # Print comparison table
    print("\n╔══════════════════════════════════════════════════════════════════════╗")
    print("║                    BENCHMARK RESULTS                                 ║")
    print("╠══════════════════════════════════════════════════════════════════════╣")
    print("║ Preset    Resolution      Avg FPS    Frame Time    Tracking Time    ║")
    print("╠══════════════════════════════════════════════════════════════════════╣")

    for r in results:
        print(f"║ {r['preset']:8s}  {r['resolution']:12s}  {r['avg_fps']:6.1f}      {r['frame_time']:6.1f}ms      {r['tracking_time']:6.1f}ms     ║")

    print("╚══════════════════════════════════════════════════════════════════════╝\n")


def optimization_example():
    """Example showing how to use optimization features."""

    print("Optimization Features Example\n")

    perf_monitor = PerformanceMonitor(
        window_size=60,
        quality_preset=QualityPreset.ADAPTIVE  # Auto-adjusting
    )

    # Example 1: Frame skipping
    print("1. Frame Skipping:")
    print("   Process every 2nd frame to reduce tracking overhead by 50%\n")

    frame_count = 0
    for i in range(100):
        perf_monitor.start_frame()

        if perf_monitor.should_process_frame(skip_interval=2):
            print(f"   Frame {i}: PROCESSING")
            # Do expensive tracking
        else:
            print(f"   Frame {i}: SKIPPED (using cached data)")
            # Use previous results

        perf_monitor.end_frame()

        if i >= 5:  # Just show first few
            break

    # Example 2: Caching
    print("\n2. Caching Expensive Computations:")

    def expensive_computation():
        """Simulate expensive operation."""
        time.sleep(0.01)
        return np.random.rand(100, 100)

    import time

    # First call - cache miss
    start = time.perf_counter()
    result = perf_monitor.cache_get('expensive_op')
    if result is None:
        result = expensive_computation()
        perf_monitor.cache_set('expensive_op', result, ttl_frames=10)
    elapsed_miss = (time.perf_counter() - start) * 1000
    print(f"   Cache miss: {elapsed_miss:.2f}ms")

    # Second call - cache hit
    start = time.perf_counter()
    result = perf_monitor.cache_get('expensive_op')
    elapsed_hit = (time.perf_counter() - start) * 1000
    print(f"   Cache hit: {elapsed_hit:.2f}ms")
    print(f"   Speedup: {elapsed_miss / elapsed_hit:.1f}x\n")

    # Example 3: Optimization recommendations
    print("3. Optimization Recommendations:")
    recommendations = perf_monitor.get_optimization_recommendations()
    for rec in recommendations:
        print(f"   • {rec}")


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1:
        command = sys.argv[1]

        if command == "benchmark":
            benchmark_quality_presets()
        elif command == "optimize":
            optimization_example()
        else:
            print("Usage:")
            print("  python example_performance.py          # Run simple demo")
            print("  python example_performance.py benchmark # Benchmark presets")
            print("  python example_performance.py optimize  # Show optimization features")
    else:
        simple_performance_demo()
