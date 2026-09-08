# Holographic ORB Object

Polished holographic ORB implementation with impressive visual effects for the holographic VFX system.

## Features

### Visual Effects
- **Glowing Core**: Radial gradient core with bright center
- **Translucent Shell**: Semi-transparent outer shell with Fresnel-like edge highlighting
- **Bloom Effect**: Multi-pass soft glow with Gaussian blur
- **Particle System**: 
  - Orbital particle motion around orb center
  - Up to 150 particles with individual lifetime and alpha fading
  - Theme-aware particle colors
  - Emission rate scales with interaction state
- **Energy Rings**: 
  - 3 rotating energy rings at different radii
  - Independent rotation speeds and directions
  - Pulsing animation
  - 3D ellipse rendering for depth effect

### Base Architecture
- **HolographicObject Base Class**:
  - Position (x, y, z) in normalized coordinates [0, 1]
  - Scale, rotation (pitch, yaw, roll)
  - Grab/release mechanics with offset tracking
  - Hover detection
  - Theme system with 5 color palettes (Cyan, Emerald, Amber, Violet, Crimson)
  - Auto-rotation support
  - Pulse animation

### Interaction
- **Grab**: Pinch gesture (thumb + index) to grab and move
- **Movement**: Smooth position tracking while grabbed
- **Hover Response**: 
  - Increased glow intensity (1.2x)
  - Increased particle emission (1.5x)
  - Visual highlight ring
- **Grab Response**:
  - Enhanced glow intensity (1.5x)
  - Doubled particle emission (2.0x)
  - Bright pulse ring

### Theme System
All colors adapt to selected theme:
- **Cyan**: Bright cyan core (56, 189, 248) with deep cyan accents
- **Emerald**: Bright emerald core (110, 231, 183) with green accents
- **Amber**: Warm amber core (233, 165, 104) with orange accents
- **Violet**: Bright violet core (167, 139, 250) with purple accents
- **Crimson**: Bright crimson core (244, 114, 182) with pink accents

## Files

### Core Implementation
- **holographic_base.py**: Base class for all holographic objects
  - Common properties (position, scale, rotation)
  - Interaction handling (grab, hover, release)
  - Theme management
  - Screen projection utilities

- **holographic_orb.py**: ORB implementation
  - `Particle`: Individual particle with orbital motion
  - `EnergyRing`: Rotating ring with pulsing animation
  - `HolographicOrb`: Main orb class with all visual effects
  - Layered rendering: bloom → rings → particles → shell → core

### Demo & Testing
- **demo_orb.py**: Interactive demo with hand tracking
  - Real-time hand tracking integration
  - Pinch-to-grab mechanics
  - Keyboard controls for theme/scale/reset
  - Performance diagnostics overlay

- **test_holographic_orb.py**: Comprehensive unit tests
  - Base class tests (40+ test cases)
  - Particle system tests
  - Energy ring tests
  - Integration tests
  - Performance tests

## Usage

### Basic Usage

```python
from holographic_orb import HolographicOrb
from holographic_base import Theme
import cv2
import numpy as np

# Create orb
orb = HolographicOrb(
    position=(0.5, 0.5, 0.0),  # Center of screen
    scale=1.0,
    base_radius=60.0,
    theme=Theme.CYAN
)

# Main loop
while True:
    # Update orb (dt in seconds)
    orb.update(dt=0.016)
    
    # Render to frame
    frame = np.zeros((720, 1280, 3), dtype=np.uint8)
    orb.render(frame)
    
    cv2.imshow('Orb', frame)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break
```

### Interaction

```python
# Grab at a point
grab_point = np.array([0.5, 0.5, 0.0])
orb.grab(grab_point)

# Move while grabbed
new_point = np.array([0.6, 0.4, 0.0])
orb.move_to_grab_point(new_point)

# Release
orb.release()

# Check hover
hand_position = np.array([0.52, 0.48, 0.0])
is_hovering = orb.check_hover(hand_position, threshold=100.0)
```

### Theme Switching

```python
from holographic_base import Theme

# Change theme
orb.set_theme(Theme.EMERALD)
orb.set_theme(Theme.VIOLET)
orb.set_theme(Theme.CRIMSON)
```

### Properties

```python
# Modify properties
orb.set_position(0.3, 0.7, 0.0)
orb.set_scale(1.5)
orb.set_rotation(45.0, 90.0, 0.0)

# Auto-rotation
orb.rotation_speed = np.array([0.0, 0.0, 30.0])  # 30 deg/sec roll

# Visual properties
orb.opacity = 0.8
orb.glow_intensity = 1.5
orb.particle_emission_rate = 2.0
```

## Running the Demo

### Requirements
```bash
pip install -r requirements.txt
```

### Launch Interactive Demo
```bash
python demo_orb.py
```

### Controls
- **PINCH** (thumb + index) - Grab and move orb
- **T** - Cycle through themes
- **+/-** - Increase/decrease orb size
- **R** - Reset orb position and scale
- **D** - Toggle diagnostics overlay
- **Q** - Quit

## Testing

Run the test suite:
```bash
pytest test_holographic_orb.py -v
```

Test coverage:
- Base class initialization and properties
- Position, scale, rotation transforms
- Grab/release mechanics
- Hover detection
- Theme color management
- Particle spawning and lifecycle
- Energy ring rotation and pulsing
- Rendering with all visual layers
- Integration workflows

## Architecture

### Rendering Pipeline

The orb renders in layers from back to front:

1. **Bloom Layer**: Soft glow effect with multiple passes and Gaussian blur
2. **Energy Rings**: Three rotating elliptical rings with independent motion
3. **Particle System**: Orbiting particles with alpha fading
4. **Shell Layer**: Translucent shell with edge highlighting
5. **Core Layer**: Bright radial gradient core
6. **Interaction Highlights**: Grab/hover state indicators

### Performance

Optimized for real-time rendering:
- Target: 30-60 FPS on Apple Silicon M5 Pro
- Particle limit: 150 active particles
- Efficient numpy operations for particle updates
- Additive blending for glow effects
- Anti-aliased drawing (cv2.LINE_AA)

### Coordinate System

- **3D Position**: Normalized [0, 1] coordinates
  - (0.5, 0.5, 0.0) = screen center
  - Z-axis for depth (not fully implemented)
- **Screen Projection**: Simple orthographic projection
  - Converts normalized to pixel coordinates
  - Scales by frame dimensions

## Design Decisions

### Visual Style
- Dark background (frame * 0.2) for holographic effect
- Additive color blending for glows
- Translucent layers for depth
- Pulsing animations for "alive" feel
- Orbital particle motion (not linear) for coherence

### Interaction Model
- Pinch gesture for precise grabbing
- Grab offset preserves relative hand position
- Smooth visual feedback for hover/grab states
- Distance-based hover detection

### Performance Trade-offs
- Particle limit prevents performance degradation
- Bloom uses 3 passes (not 5+) for speed
- Energy rings use ellipses (not 3D meshes)
- No shadows or reflections (yet)

## Future Enhancements

Potential additions:
- [ ] Multiple orbs with collision detection
- [ ] Physics simulation (gravity, momentum)
- [ ] Sound effects on interaction
- [ ] Advanced shaders (if moving to OpenGL)
- [ ] Texture mapping on shell
- [ ] Reflection/refraction effects
- [ ] Trail effects when moving
- [ ] Customizable particle shapes

## License

Built for holographic VFX application. Uses OpenCV (Apache 2.0) and NumPy (BSD).
