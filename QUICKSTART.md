# Performance Monitoring - Quick Start Guide

Get up and running with performance monitoring in 5 minutes.

## Installation

No additional dependencies required beyond the base hand tracking system:
- OpenCV (cv2)
- MediaPipe
- NumPy

Optional for memory tracking:
```bash
pip install psutil
```

## Basic Integration (3 lines of code)

Add performance monitoring to existing hand tracking code:

```python
from performance_monitor import PerformanceMonitor, QualityPreset

# 1. Initialize monitor
perf_monitor = PerformanceMonitor(quality_preset=QualityPreset.MEDIUM)

while True:
    # 2. Wrap your tracking
    perf_monitor.start_frame()
    perf_monitor.start_tracking()
    hands = tracker.process_frame(frame)
    perf_monitor.end_tracking()
    
    # 3. Get metrics
    metrics = perf_monitor.get_metrics()
    print(f"FPS: {metrics.avg_fps:.1f}")
    
    perf_monitor.end_frame()
```

## Quick Examples

### 1. Run the Simple Demo

```bash
python3 example_performance.py
```

Shows basic FPS overlay with minimal code.

### 2. Run the Full Performance Demo

```bash
python3 demo_performance.py --quality medium
```

Full-featured demo with:
- Real-time FPS graph
- Timing breakdown
- Optimization recommendations
- Interactive quality switching

### 3. Benchmark Quality Presets

```bash
python3 example_performance.py benchmark
```

Compare LOW, MEDIUM, HIGH presets on your hardware.

### 4. View Optimization Features

```bash
python3 example_performance.py optimize
```

See frame skipping, caching, and recommendation examples.

## Quality Presets Cheat Sheet

| Preset | Resolution | FPS Target | When to Use |
|--------|-----------|------------|-------------|
| LOW | 640x480 | 60 | Mobile, slow hardware, maximum speed |
| MEDIUM | 1280x720 | 30 | Default, balanced |
| HIGH | 1920x1080 | 30 | High accuracy needed, powerful hardware |
| ADAPTIVE | Starts at MEDIUM | 30 | Unknown hardware, auto-adjusts |

## Common Patterns

### Pattern 1: Display FPS on Screen

```python
metrics = perf_monitor.get_metrics()
cv2.putText(frame, f"FPS: {metrics.avg_fps:.1f}", (20, 30), 
            cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)
```

### Pattern 2: Optimize on Slow Devices

```python
# Use LOW preset + frame skipping
perf_monitor = PerformanceMonitor(quality_preset=QualityPreset.LOW)

if perf_monitor.should_process_frame(skip_interval=2):
    hands = tracker.process_frame(frame)
else:
    hands = cached_hands  # Reuse previous result
```

### Pattern 3: Adaptive Quality for Unknown Hardware

```python
# Automatically adjusts based on performance
perf_monitor = PerformanceMonitor(quality_preset=QualityPreset.ADAPTIVE)

# Check if quality changed
settings = perf_monitor.quality_settings
print(f"Current resolution: {settings.resolution}")
```

### Pattern 4: Get Performance Report

```python
# Print detailed summary
print(perf_monitor.get_summary())

# Get optimization tips
for rec in perf_monitor.get_optimization_recommendations():
    print(f"• {rec}")
```

### Pattern 5: Cache Expensive Operations

```python
# Cache computed features for 10 frames
features = perf_monitor.cache_get('hand_features')
if features is None:
    features = compute_hand_features(hand_data)
    perf_monitor.cache_set('hand_features', features, ttl_frames=10)
```

## Performance Targets

### Mobile / Raspberry Pi
```python
PerformanceMonitor(quality_preset=QualityPreset.LOW)
# Target: 15-30 FPS
```

### Laptop / Desktop
```python
PerformanceMonitor(quality_preset=QualityPreset.MEDIUM)
# Target: 25-35 FPS
```

### Workstation / Gaming PC
```python
PerformanceMonitor(quality_preset=QualityPreset.HIGH)
# Target: 20-30 FPS (limited by MediaPipe model)
```

## Troubleshooting Quick Fixes

### Problem: FPS too low

**Quick fix 1:** Reduce quality
```python
# Change from MEDIUM to LOW
perf_monitor.quality_preset = QualityPreset.LOW
```

**Quick fix 2:** Enable frame skipping
```python
if perf_monitor.should_process_frame(skip_interval=2):
    hands = tracker.process_frame(frame)
```

### Problem: High dropped frame rate

**Check breakdown:**
```python
breakdown = perf_monitor.get_performance_breakdown()
print(breakdown)
# If tracking > 60%: reduce model_complexity or max_hands
# If render > 40%: simplify visualization
```

### Problem: Inconsistent performance

**Use adaptive quality:**
```python
PerformanceMonitor(quality_preset=QualityPreset.ADAPTIVE)
# Automatically adjusts to maintain target FPS
```

## Keyboard Shortcuts (demo_performance.py)

| Key | Action |
|-----|--------|
| L | Toggle landmarks |
| P | Toggle performance panel |
| G | Toggle FPS graph |
| R | Toggle recommendations |
| B | Toggle timing breakdown |
| 1 | LOW quality |
| 2 | MEDIUM quality |
| 3 | HIGH quality |
| 4 | ADAPTIVE quality |
| S | Print summary to console |
| Q | Quit |

## What to Monitor

### During Development
- **Avg FPS**: Should be close to target
- **Frame Time**: Should be under 33ms for 30 FPS
- **Dropped Frames**: Should be under 5%

### In Production
- **Min FPS**: Should stay above usable threshold
- **Tracking Time**: Watch for increases (model bottleneck)
- **Memory Usage**: Watch for leaks over time

## File Overview

| File | Purpose |
|------|---------|
| `performance_monitor.py` | Core monitoring system |
| `demo_performance.py` | Full-featured demo |
| `example_performance.py` | Simple examples |
| `test_performance.py` | Test suite |
| `README_PERFORMANCE.md` | Complete documentation |
| `QUICKSTART.md` | This file |

## Next Steps

1. **Try the demos**: Run examples to see features
2. **Integrate into your code**: Add 3-line integration
3. **Benchmark your hardware**: Run benchmark command
4. **Optimize**: Use recommendations to improve performance
5. **Read full docs**: See README_PERFORMANCE.md for advanced features

## Getting Help

If performance is poor:
1. Run `python3 demo_performance.py` and press 'R' for recommendations
2. Try different quality presets (keys 1-4)
3. Check timing breakdown (key 'B') to find bottleneck
4. Print summary (key 'S') for detailed metrics

## Best Practices

✓ **DO:**
- Start with MEDIUM preset
- Use ADAPTIVE for unknown hardware
- Monitor FPS during development
- Cache expensive computations
- Profile before optimizing

✗ **DON'T:**
- Skip performance monitoring entirely
- Use HIGH preset on slow hardware
- Perform I/O in main loop
- Ignore recommendations
- Optimize without measuring

## 30-Second Integration Example

```python
from hand_tracker import HandTracker
from performance_monitor import PerformanceMonitor, QualityPreset

perf = PerformanceMonitor(quality_preset=QualityPreset.MEDIUM)
tracker = HandTracker()
cap = cv2.VideoCapture(0)

while True:
    perf.start_frame()
    
    ret, frame = cap.read()
    perf.start_tracking()
    hands = tracker.process_frame(frame)
    perf.end_tracking()
    
    # Your visualization code here
    
    print(f"FPS: {perf.get_metrics().avg_fps:.1f}")
    perf.end_frame()
    
    cv2.imshow('Frame', frame)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break
```

That's it! You now have professional-grade performance monitoring.

---

For complete API reference and advanced features, see [README_PERFORMANCE.md](README_PERFORMANCE.md)
