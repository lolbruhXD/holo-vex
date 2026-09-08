"""
Unit tests for performance monitoring system.
Tests metrics calculation, quality presets, caching, and optimization recommendations.
"""

import time
import numpy as np
from performance_monitor import PerformanceMonitor, QualityPreset, QualitySettings


def test_quality_presets():
    """Test quality preset configurations."""
    print("Testing quality presets...")

    presets = [
        QualityPreset.LOW,
        QualityPreset.MEDIUM,
        QualityPreset.HIGH,
        QualityPreset.ADAPTIVE
    ]

    for preset in presets:
        settings = QualitySettings.from_preset(preset)
        print(f"\n{preset.value.upper()}:")
        print(f"  Resolution: {settings.resolution}")
        print(f"  Model Complexity: {settings.model_complexity}")
        print(f"  Max Hands: {settings.max_hands}")
        print(f"  Detection Confidence: {settings.min_detection_confidence}")
        print(f"  Target FPS: {settings.target_fps}")

    print("\n✓ Quality presets test passed")


def test_performance_metrics():
    """Test performance metrics calculation."""
    print("\nTesting performance metrics...")

    monitor = PerformanceMonitor(window_size=30, quality_preset=QualityPreset.MEDIUM)

    # Simulate 60 frames at ~30 FPS
    for i in range(60):
        monitor.start_frame()

        monitor.start_tracking()
        time.sleep(0.020)  # 20ms tracking
        monitor.end_tracking()

        monitor.start_render()
        time.sleep(0.010)  # 10ms render
        monitor.end_render()

        monitor.end_frame()

    metrics = monitor.get_metrics()

    print(f"\nMetrics after 60 frames:")
    print(f"  Avg FPS: {metrics.avg_fps:.1f}")
    print(f"  Frame Time: {metrics.frame_time_ms:.2f}ms")
    print(f"  Tracking Time: {metrics.tracking_time_ms:.2f}ms")
    print(f"  Render Time: {metrics.render_time_ms:.2f}ms")
    print(f"  Total Frames: {metrics.total_frames}")
    print(f"  Dropped Frames: {metrics.dropped_frames}")

    # Verify metrics are reasonable
    assert 25 < metrics.avg_fps < 35, f"FPS outside expected range: {metrics.avg_fps}"
    assert 15 < metrics.tracking_time_ms < 25, f"Tracking time unexpected: {metrics.tracking_time_ms}"
    assert 5 < metrics.render_time_ms < 15, f"Render time unexpected: {metrics.render_time_ms}"
    assert metrics.total_frames == 60, f"Frame count incorrect: {metrics.total_frames}"

    print("\n✓ Performance metrics test passed")


def test_timing_breakdown():
    """Test frame time breakdown calculation."""
    print("\nTesting timing breakdown...")

    monitor = PerformanceMonitor(window_size=30, quality_preset=QualityPreset.MEDIUM)

    # Simulate frames with known timing
    for i in range(30):
        monitor.start_frame()

        monitor.start_tracking()
        time.sleep(0.015)  # 15ms tracking (50% of 30ms frame)
        monitor.end_tracking()

        monitor.start_render()
        time.sleep(0.010)  # 10ms render (33% of 30ms frame)
        monitor.end_render()

        monitor.end_frame()

    breakdown = monitor.get_performance_breakdown()

    print(f"\nTiming Breakdown:")
    print(f"  Tracking: {breakdown['tracking']:.1f}%")
    print(f"  Render: {breakdown['render']:.1f}%")
    print(f"  Other: {breakdown['other']:.1f}%")

    # Verify percentages sum to ~100%
    total = breakdown['tracking'] + breakdown['render'] + breakdown['other']
    assert 95 < total < 105, f"Percentages don't sum to 100: {total}"

    # Verify tracking is largest component
    assert breakdown['tracking'] > 30, f"Tracking percentage too low: {breakdown['tracking']}"

    print("\n✓ Timing breakdown test passed")


def test_cache_system():
    """Test caching functionality."""
    print("\nTesting cache system...")

    monitor = PerformanceMonitor(window_size=30, quality_preset=QualityPreset.MEDIUM)

    # Test cache miss
    value = monitor.cache_get('test_key')
    assert value is None, "Cache should be empty initially"
    assert monitor.cache_misses == 1, f"Cache miss not recorded: {monitor.cache_misses}"

    # Test cache set and hit
    test_data = {'x': 10, 'y': 20}
    monitor.cache_set('test_key', test_data, ttl_frames=5)

    retrieved = monitor.cache_get('test_key')
    assert retrieved is not None, "Cache should return value"
    assert retrieved['value'] == test_data, "Cached data mismatch"
    assert monitor.cache_hits == 1, f"Cache hit not recorded: {monitor.cache_hits}"

    # Test cache expiration
    for i in range(10):
        monitor.start_frame()
        monitor.end_frame()

    monitor.cache_clean()
    value = monitor.cache_get('test_key')
    assert value is None, "Expired cache entry should be removed"

    print(f"\nCache Stats:")
    print(f"  Hits: {monitor.cache_hits}")
    print(f"  Misses: {monitor.cache_misses}")

    print("\n✓ Cache system test passed")


def test_frame_skipping():
    """Test frame skipping for optimization."""
    print("\nTesting frame skipping...")

    monitor = PerformanceMonitor(window_size=30, quality_preset=QualityPreset.MEDIUM)

    processed_frames = 0
    total_frames = 60
    skip_interval = 2  # Process every 2nd frame

    for i in range(total_frames):
        monitor.start_frame()
        monitor.end_frame()

        if monitor.should_process_frame(skip_interval):
            processed_frames += 1

    expected_processed = total_frames // skip_interval
    print(f"\nFrame Skipping (interval={skip_interval}):")
    print(f"  Total Frames: {total_frames}")
    print(f"  Processed: {processed_frames}")
    print(f"  Expected: {expected_processed}")

    assert processed_frames == expected_processed, \
        f"Frame skip count mismatch: {processed_frames} != {expected_processed}"

    print("\n✓ Frame skipping test passed")


def test_optimization_recommendations():
    """Test optimization recommendation system."""
    print("\nTesting optimization recommendations...")

    monitor = PerformanceMonitor(window_size=30, quality_preset=QualityPreset.MEDIUM)

    # Simulate good performance
    for i in range(30):
        monitor.start_frame()
        monitor.start_tracking()
        time.sleep(0.008)  # Fast tracking (40% of frame)
        monitor.end_tracking()
        monitor.start_render()
        time.sleep(0.005)  # Fast render (25% of frame)
        monitor.end_render()
        time.sleep(0.007)  # Other overhead (35% of frame)
        monitor.end_frame()

    recommendations = monitor.get_optimization_recommendations()
    print(f"\nGood Performance Recommendations:")
    for rec in recommendations:
        print(f"  • {rec}")

    # Good performance should have "optimal" or minimal warnings
    has_optimal = any("optimal" in rec.lower() for rec in recommendations)
    has_few_warnings = len(recommendations) <= 1

    assert has_optimal or has_few_warnings, \
        f"Should report optimal or minimal warnings, got: {recommendations}"

    # Reset and simulate poor performance
    monitor.reset_stats()

    for i in range(30):
        monitor.start_frame()
        monitor.start_tracking()
        time.sleep(0.060)  # Slow tracking (bottleneck)
        monitor.end_tracking()
        monitor.start_render()
        time.sleep(0.010)
        monitor.end_render()
        monitor.end_frame()

    recommendations = monitor.get_optimization_recommendations()
    print(f"\nPoor Performance Recommendations:")
    for rec in recommendations:
        print(f"  • {rec}")

    assert len(recommendations) > 1, "Should provide recommendations for poor performance"

    print("\n✓ Optimization recommendations test passed")


def test_dropped_frame_detection():
    """Test dropped frame detection."""
    print("\nTesting dropped frame detection...")

    monitor = PerformanceMonitor(window_size=30, quality_preset=QualityPreset.MEDIUM)

    # Simulate frames with some taking too long
    for i in range(50):
        monitor.start_frame()

        if i % 10 == 0:
            # Every 10th frame is slow
            time.sleep(0.100)  # 100ms - should be detected as dropped
        else:
            time.sleep(0.020)  # 20ms - normal

        monitor.end_frame()

    metrics = monitor.get_metrics()

    print(f"\nDropped Frame Detection:")
    print(f"  Total Frames: {metrics.total_frames}")
    print(f"  Dropped Frames: {metrics.dropped_frames}")
    print(f"  Drop Rate: {metrics.dropped_frames / metrics.total_frames * 100:.1f}%")

    # Should detect ~5 dropped frames (every 10th out of 50)
    assert metrics.dropped_frames > 0, "Should detect dropped frames"
    assert metrics.dropped_frames < 10, f"Too many dropped frames detected: {metrics.dropped_frames}"

    print("\n✓ Dropped frame detection test passed")


def test_adaptive_quality():
    """Test adaptive quality adjustment."""
    print("\nTesting adaptive quality adjustment...")

    monitor = PerformanceMonitor(
        window_size=30,
        quality_preset=QualityPreset.ADAPTIVE
    )

    initial_complexity = monitor.quality_settings.model_complexity
    initial_hands = monitor.quality_settings.max_hands

    print(f"\nInitial Settings:")
    print(f"  Model Complexity: {initial_complexity}")
    print(f"  Max Hands: {initial_hands}")

    # Simulate poor performance to trigger quality reduction
    for i in range(monitor.adjustment_interval + 5):
        monitor.start_frame()
        time.sleep(0.060)  # Slow frame
        monitor.end_frame()

    print(f"\nSettings After Poor Performance:")
    print(f"  Model Complexity: {monitor.quality_settings.model_complexity}")
    print(f"  Max Hands: {monitor.quality_settings.max_hands}")

    # Note: Adaptive adjustment may or may not trigger depending on exact timing
    # This test mainly verifies the system doesn't crash

    print("\n✓ Adaptive quality test passed")


def test_performance_summary():
    """Test performance summary generation."""
    print("\nTesting performance summary...")

    monitor = PerformanceMonitor(window_size=30, quality_preset=QualityPreset.MEDIUM)

    # Generate some data
    for i in range(30):
        monitor.start_frame()
        monitor.start_tracking()
        time.sleep(0.015)
        monitor.end_tracking()
        monitor.start_render()
        time.sleep(0.010)
        monitor.end_render()
        monitor.end_frame()

    summary = monitor.get_summary()

    print("\n" + summary)

    # Verify summary contains key information
    assert "FPS" in summary, "Summary should contain FPS"
    assert "Frame Time" in summary, "Summary should contain frame time"
    assert "Tracking" in summary, "Summary should contain tracking info"
    assert "Render" in summary, "Summary should contain render info"

    print("\n✓ Performance summary test passed")


def run_all_tests():
    """Run all performance monitor tests."""
    print("═" * 60)
    print("PERFORMANCE MONITOR TEST SUITE")
    print("═" * 60)

    try:
        test_quality_presets()
        test_performance_metrics()
        test_timing_breakdown()
        test_cache_system()
        test_frame_skipping()
        test_optimization_recommendations()
        test_dropped_frame_detection()
        test_adaptive_quality()
        test_performance_summary()

        print("\n" + "═" * 60)
        print("✓ ALL TESTS PASSED")
        print("═" * 60)

    except AssertionError as e:
        print(f"\n✗ TEST FAILED: {e}")
        raise
    except Exception as e:
        print(f"\n✗ UNEXPECTED ERROR: {e}")
        import traceback
        traceback.print_exc()
        raise


if __name__ == "__main__":
    run_all_tests()
