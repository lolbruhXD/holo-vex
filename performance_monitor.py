"""
Performance monitoring and optimization for real-time hand tracking.
Provides FPS tracking, frame timing analysis, optimization strategies, and quality presets.
"""

import time
import numpy as np
from collections import deque
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum


class QualityPreset(Enum):
    """Quality presets balancing performance and accuracy."""
    LOW = "low"           # Maximum performance, reduced accuracy
    MEDIUM = "medium"     # Balanced
    HIGH = "high"         # Maximum accuracy, may reduce FPS
    ADAPTIVE = "adaptive" # Auto-adjust based on performance


@dataclass
class PerformanceMetrics:
    """Container for performance metrics."""
    fps: float
    avg_fps: float
    min_fps: float
    max_fps: float
    frame_time_ms: float
    tracking_time_ms: float
    render_time_ms: float
    total_frames: int
    dropped_frames: int
    memory_usage_mb: float


@dataclass
class QualitySettings:
    """Quality configuration for hand tracking."""
    resolution: Tuple[int, int]
    model_complexity: int  # 0 = lite, 1 = full
    max_hands: int
    min_detection_confidence: float
    min_tracking_confidence: float
    target_fps: int

    @staticmethod
    def from_preset(preset: QualityPreset) -> 'QualitySettings':
        """Create settings from quality preset."""
        presets = {
            QualityPreset.LOW: QualitySettings(
                resolution=(640, 480),
                model_complexity=0,
                max_hands=1,
                min_detection_confidence=0.5,
                min_tracking_confidence=0.5,
                target_fps=60
            ),
            QualityPreset.MEDIUM: QualitySettings(
                resolution=(1280, 720),
                model_complexity=0,
                max_hands=2,
                min_detection_confidence=0.6,
                min_tracking_confidence=0.5,
                target_fps=30
            ),
            QualityPreset.HIGH: QualitySettings(
                resolution=(1920, 1080),
                model_complexity=1,
                max_hands=2,
                min_detection_confidence=0.7,
                min_tracking_confidence=0.5,
                target_fps=30
            ),
            QualityPreset.ADAPTIVE: QualitySettings(
                resolution=(1280, 720),
                model_complexity=0,
                max_hands=2,
                min_detection_confidence=0.6,
                min_tracking_confidence=0.5,
                target_fps=30
            )
        }
        return presets[preset]


class PerformanceMonitor:
    """
    Comprehensive performance monitoring and optimization.

    Features:
    - Real-time FPS tracking with smoothing
    - Frame time breakdown (tracking, rendering, total)
    - Dropped frame detection
    - Performance optimization recommendations
    - Adaptive quality adjustment
    - Memory usage tracking
    """

    def __init__(
        self,
        window_size: int = 60,
        quality_preset: QualityPreset = QualityPreset.MEDIUM
    ):
        """
        Initialize performance monitor.

        Args:
            window_size: Number of frames to average for metrics
            quality_preset: Initial quality preset
        """
        # Timing
        self.frame_times = deque(maxlen=window_size)
        self.tracking_times = deque(maxlen=window_size)
        self.render_times = deque(maxlen=window_size)

        # Frame tracking
        self.total_frames = 0
        self.dropped_frames = 0
        self.last_frame_time = time.perf_counter()

        # Current frame timing
        self.frame_start_time = 0
        self.tracking_start_time = 0
        self.tracking_duration = 0
        self.render_start_time = 0
        self.render_duration = 0

        # Quality settings
        self.quality_preset = quality_preset
        self.quality_settings = QualitySettings.from_preset(quality_preset)

        # Adaptive quality
        self.adaptive_enabled = (quality_preset == QualityPreset.ADAPTIVE)
        self.fps_target = self.quality_settings.target_fps
        self.fps_adjustment_cooldown = 0
        self.adjustment_interval = 60  # Frames between adjustments

        # Performance warnings
        self.low_fps_threshold = 15.0
        self.warning_count = 0

        # Optimization cache
        self.cached_data = {}
        self.cache_hits = 0
        self.cache_misses = 0

    def start_frame(self):
        """Mark the start of a new frame."""
        self.frame_start_time = time.perf_counter()
        self.total_frames += 1

    def start_tracking(self):
        """Mark the start of tracking phase."""
        self.tracking_start_time = time.perf_counter()

    def end_tracking(self):
        """Mark the end of tracking phase."""
        self.tracking_duration = time.perf_counter() - self.tracking_start_time
        self.tracking_times.append(self.tracking_duration)

    def start_render(self):
        """Mark the start of render phase."""
        self.render_start_time = time.perf_counter()

    def end_render(self):
        """Mark the end of render phase."""
        self.render_duration = time.perf_counter() - self.render_start_time
        self.render_times.append(self.render_duration)

    def end_frame(self):
        """Mark the end of a frame and update metrics."""
        current_time = time.perf_counter()
        frame_time = current_time - self.frame_start_time

        self.frame_times.append(frame_time)

        # Detect dropped frames (frame took too long)
        if frame_time > (1.0 / self.fps_target) * 2:
            self.dropped_frames += 1

        self.last_frame_time = current_time

        # Check for adaptive quality adjustment
        if self.adaptive_enabled:
            self.fps_adjustment_cooldown -= 1
            if self.fps_adjustment_cooldown <= 0:
                self._adjust_quality_adaptive()
                self.fps_adjustment_cooldown = self.adjustment_interval

    def get_metrics(self) -> PerformanceMetrics:
        """
        Get current performance metrics.

        Returns:
            PerformanceMetrics object with all current stats
        """
        if not self.frame_times:
            return PerformanceMetrics(
                fps=0, avg_fps=0, min_fps=0, max_fps=0,
                frame_time_ms=0, tracking_time_ms=0, render_time_ms=0,
                total_frames=0, dropped_frames=0, memory_usage_mb=0
            )

        # Calculate FPS from frame times
        frame_times_array = np.array(self.frame_times)
        fps_values = 1.0 / (frame_times_array + 1e-6)

        current_fps = fps_values[-1] if len(fps_values) > 0 else 0
        avg_fps = np.mean(fps_values)
        min_fps = np.min(fps_values)
        max_fps = np.max(fps_values)

        # Calculate average times in milliseconds
        avg_frame_time = np.mean(frame_times_array) * 1000
        avg_tracking_time = (
            np.mean(self.tracking_times) * 1000 if self.tracking_times else 0
        )
        avg_render_time = (
            np.mean(self.render_times) * 1000 if self.render_times else 0
        )

        # Estimate memory usage (rough approximation)
        memory_mb = self._estimate_memory_usage()

        return PerformanceMetrics(
            fps=current_fps,
            avg_fps=avg_fps,
            min_fps=min_fps,
            max_fps=max_fps,
            frame_time_ms=avg_frame_time,
            tracking_time_ms=avg_tracking_time,
            render_time_ms=avg_render_time,
            total_frames=self.total_frames,
            dropped_frames=self.dropped_frames,
            memory_usage_mb=memory_mb
        )

    def _estimate_memory_usage(self) -> float:
        """Estimate memory usage in MB."""
        try:
            import psutil
            import os
            process = psutil.Process(os.getpid())
            return process.memory_info().rss / (1024 * 1024)
        except ImportError:
            # Rough estimate based on data structures
            base_memory = 50  # Base overhead
            buffer_memory = len(self.frame_times) * 0.001
            return base_memory + buffer_memory

    def get_performance_breakdown(self) -> Dict[str, float]:
        """
        Get percentage breakdown of where time is spent.

        Returns:
            Dictionary with percentage of time in tracking, render, other
        """
        if not self.frame_times:
            return {'tracking': 0, 'render': 0, 'other': 0}

        avg_frame_time = np.mean(self.frame_times)
        avg_tracking_time = np.mean(self.tracking_times) if self.tracking_times else 0
        avg_render_time = np.mean(self.render_times) if self.render_times else 0

        if avg_frame_time == 0:
            return {'tracking': 0, 'render': 0, 'other': 0}

        tracking_pct = (avg_tracking_time / avg_frame_time) * 100
        render_pct = (avg_render_time / avg_frame_time) * 100
        other_pct = 100 - tracking_pct - render_pct

        return {
            'tracking': tracking_pct,
            'render': render_pct,
            'other': other_pct
        }

    def _adjust_quality_adaptive(self):
        """Automatically adjust quality based on performance."""
        metrics = self.get_metrics()

        # If FPS is consistently low, reduce quality
        if metrics.avg_fps < self.fps_target * 0.8:
            self._reduce_quality()
        # If FPS is consistently high, increase quality
        elif metrics.avg_fps > self.fps_target * 1.2:
            self._increase_quality()

    def _reduce_quality(self):
        """Reduce quality settings to improve performance."""
        settings = self.quality_settings

        # Try reducing in order of impact
        if settings.model_complexity > 0:
            settings.model_complexity = 0
            print("[PERF] Reduced model complexity to lite")
        elif settings.max_hands > 1:
            settings.max_hands = 1
            print("[PERF] Reduced max hands to 1")
        elif settings.resolution[0] > 640:
            settings.resolution = (640, 480)
            print("[PERF] Reduced resolution to 640x480")

    def _increase_quality(self):
        """Increase quality settings when performance allows."""
        settings = self.quality_settings

        # Try increasing in reverse order
        if settings.resolution[0] < 1280:
            settings.resolution = (1280, 720)
            print("[PERF] Increased resolution to 1280x720")
        elif settings.max_hands < 2:
            settings.max_hands = 2
            print("[PERF] Increased max hands to 2")
        elif settings.model_complexity < 1:
            settings.model_complexity = 1
            print("[PERF] Increased model complexity to full")

    def should_process_frame(self, skip_interval: int = 1) -> bool:
        """
        Determine if current frame should be processed (frame skipping).

        Args:
            skip_interval: Process every Nth frame (1 = all frames)

        Returns:
            True if frame should be processed
        """
        return (self.total_frames % skip_interval) == 0

    def cache_get(self, key: str) -> Optional[any]:
        """
        Get cached data.

        Args:
            key: Cache key

        Returns:
            Cached value or None
        """
        if key in self.cached_data:
            self.cache_hits += 1
            return self.cached_data[key]
        self.cache_misses += 1
        return None

    def cache_set(self, key: str, value: any, ttl_frames: int = 10):
        """
        Set cached data with TTL.

        Args:
            key: Cache key
            value: Value to cache
            ttl_frames: Time-to-live in frames
        """
        self.cached_data[key] = {
            'value': value,
            'expires': self.total_frames + ttl_frames
        }

    def cache_clean(self):
        """Remove expired cache entries."""
        expired_keys = [
            k for k, v in self.cached_data.items()
            if v['expires'] <= self.total_frames
        ]
        for key in expired_keys:
            del self.cached_data[key]

    def get_optimization_recommendations(self) -> List[str]:
        """
        Get performance optimization recommendations.

        Returns:
            List of recommendation strings
        """
        recommendations = []
        metrics = self.get_metrics()
        breakdown = self.get_performance_breakdown()

        # Low FPS warning
        if metrics.avg_fps < self.low_fps_threshold:
            recommendations.append(
                f"FPS critically low ({metrics.avg_fps:.1f}). "
                "Consider reducing quality preset."
            )

        # High dropped frame rate
        drop_rate = metrics.dropped_frames / max(metrics.total_frames, 1)
        if drop_rate > 0.1:
            recommendations.append(
                f"High dropped frame rate ({drop_rate*100:.1f}%). "
                "Reduce tracking complexity or resolution."
            )

        # Tracking bottleneck
        if breakdown['tracking'] > 60:
            recommendations.append(
                "Tracking is bottleneck (>60% of frame time). "
                "Reduce model_complexity or max_hands."
            )

        # Render bottleneck
        if breakdown['render'] > 40:
            recommendations.append(
                "Rendering is bottleneck (>40% of frame time). "
                "Simplify visualization or reduce draw calls."
            )

        # Cache efficiency
        total_cache_ops = self.cache_hits + self.cache_misses
        if total_cache_ops > 100:
            hit_rate = self.cache_hits / total_cache_ops
            if hit_rate < 0.5:
                recommendations.append(
                    f"Low cache hit rate ({hit_rate*100:.1f}%). "
                    "Adjust caching strategy."
                )

        if not recommendations:
            recommendations.append("Performance is optimal.")

        return recommendations

    def reset_stats(self):
        """Reset all statistics."""
        self.frame_times.clear()
        self.tracking_times.clear()
        self.render_times.clear()
        self.total_frames = 0
        self.dropped_frames = 0
        self.warning_count = 0
        self.cache_hits = 0
        self.cache_misses = 0
        self.cached_data.clear()

    def get_summary(self) -> str:
        """
        Get human-readable performance summary.

        Returns:
            Formatted summary string
        """
        metrics = self.get_metrics()
        breakdown = self.get_performance_breakdown()

        summary = f"""
╔══════════════════════════════════════════════════════════════╗
║              PERFORMANCE MONITOR SUMMARY                     ║
╠══════════════════════════════════════════════════════════════╣
║ FPS: {metrics.fps:6.1f} (avg: {metrics.avg_fps:6.1f}, range: {metrics.min_fps:5.1f}-{metrics.max_fps:5.1f}) ║
║ Frame Time: {metrics.frame_time_ms:6.2f} ms                                      ║
║   ├─ Tracking: {metrics.tracking_time_ms:6.2f} ms ({breakdown['tracking']:5.1f}%)                     ║
║   ├─ Render:   {metrics.render_time_ms:6.2f} ms ({breakdown['render']:5.1f}%)                     ║
║   └─ Other:    {metrics.frame_time_ms - metrics.tracking_time_ms - metrics.render_time_ms:6.2f} ms ({breakdown['other']:5.1f}%)                     ║
║ Frames: {metrics.total_frames:8d} (dropped: {metrics.dropped_frames:5d}, {metrics.dropped_frames/max(metrics.total_frames,1)*100:4.1f}%)      ║
║ Memory: {metrics.memory_usage_mb:6.1f} MB                                         ║
║ Quality: {self.quality_preset.value.upper():12s}                                  ║
╚══════════════════════════════════════════════════════════════╝
        """.strip()

        return summary
