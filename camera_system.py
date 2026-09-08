"""
Camera System for Holographic VFX Application

Provides camera enumeration, initialization, multi-source support, and synthetic mode.
Compatible with Apple Silicon M5 Pro, Python 3.9+.
"""

import cv2
import numpy as np
import platform
import time
from enum import Enum
from typing import Optional, Tuple, Dict, List, Union
from dataclasses import dataclass


class CameraMode(Enum):
    """Camera operation modes"""
    REAL = "real"
    SYNTHETIC = "synthetic"


class CameraBackend(Enum):
    """Camera backend preferences by platform"""
    AUTO = cv2.CAP_ANY
    AVFOUNDATION = cv2.CAP_AVFOUNDATION  # macOS native
    V4L2 = cv2.CAP_V4L2  # Linux
    DSHOW = cv2.CAP_DSHOW  # Windows
    GSTREAMER = cv2.CAP_GSTREAMER


@dataclass
class CameraInfo:
    """Camera device information"""
    index: int
    name: str
    backend: str
    width: int
    height: int
    fps: float
    is_available: bool


@dataclass
class CameraConfig:
    """Camera configuration"""
    width: int = 1280
    height: int = 720
    fps: int = 30
    buffer_size: int = 1
    backend: CameraBackend = CameraBackend.AUTO


class SyntheticCamera:
    """Generates synthetic camera feeds for testing without hardware"""

    def __init__(self, width: int = 1280, height: int = 720, fps: int = 30):
        self.width = width
        self.height = height
        self.fps = fps
        self.frame_count = 0
        self.start_time = time.time()

        # Generate gradient background
        self.background = self._generate_gradient()

        # Particle system for ambient motion
        self.particles = self._init_particles(50)

    def _generate_gradient(self) -> np.ndarray:
        """Create atmospheric gradient background"""
        frame = np.zeros((self.height, self.width, 3), dtype=np.uint8)

        # Deep space gradient: near-black to deep blue
        for y in range(self.height):
            ratio = y / self.height
            # Tinted toward cyan-blue
            r = int(5 + ratio * 10)
            g = int(7 + ratio * 15)
            b = int(12 + ratio * 28)
            frame[y, :] = [b, g, r]

        return frame

    def _init_particles(self, count: int) -> np.ndarray:
        """Initialize floating particles"""
        particles = np.random.rand(count, 4)
        particles[:, 0] *= self.width   # x position
        particles[:, 1] *= self.height  # y position
        particles[:, 2] = np.random.rand(count) * 2 - 1  # x velocity
        particles[:, 3] = np.random.rand(count) * 2 - 1  # y velocity
        return particles

    def _update_particles(self):
        """Update particle positions with wrapping"""
        self.particles[:, 0] += self.particles[:, 2]
        self.particles[:, 1] += self.particles[:, 3]

        # Wrap around edges
        self.particles[:, 0] %= self.width
        self.particles[:, 1] %= self.height

    def read(self) -> Tuple[bool, np.ndarray]:
        """Generate synthetic frame"""
        frame = self.background.copy()

        # Update and draw particles
        self._update_particles()
        for particle in self.particles:
            x, y = int(particle[0]), int(particle[1])
            cv2.circle(frame, (x, y), 2, (255, 255, 255), -1)

        # Add animated elements
        elapsed = time.time() - self.start_time

        # Pulsing circle (simulates presence)
        pulse_radius = int(50 + 20 * np.sin(elapsed * 2))
        center_x, center_y = self.width // 2, self.height // 2
        cv2.circle(frame, (center_x, center_y), pulse_radius, (56, 189, 248), 2)

        # Synthetic hand region hint (placeholder)
        hand_x = int(self.width * 0.5 + 200 * np.sin(elapsed))
        hand_y = int(self.height * 0.6)
        cv2.circle(frame, (hand_x, hand_y), 60, (110, 231, 183, 100), -1)

        # Add timestamp overlay
        cv2.putText(
            frame,
            f"SYNTHETIC MODE | Frame {self.frame_count}",
            (20, 30),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.6,
            (56, 189, 248),
            1,
            cv2.LINE_AA
        )

        self.frame_count += 1

        # Simulate frame rate
        time.sleep(1.0 / self.fps)

        return True, frame

    def isOpened(self) -> bool:
        """Always available"""
        return True

    def release(self):
        """No resources to release"""
        pass

    def get(self, prop_id: int) -> float:
        """Get camera property"""
        if prop_id == cv2.CAP_PROP_FRAME_WIDTH:
            return float(self.width)
        elif prop_id == cv2.CAP_PROP_FRAME_HEIGHT:
            return float(self.height)
        elif prop_id == cv2.CAP_PROP_FPS:
            return float(self.fps)
        return 0.0


class CameraSystem:
    """
    Multi-source camera system with enumeration, initialization, and fallback support.
    Handles real cameras with platform-specific backends and synthetic mode.
    """

    def __init__(self):
        self.camera: Optional[cv2.VideoCapture | SyntheticCamera] = None
        self.mode: CameraMode = CameraMode.REAL
        self.config: Optional[CameraConfig] = None
        self.is_initialized: bool = False
        self.current_source: Optional[Union[int, str]] = None

        # Platform detection
        self.platform = platform.system()
        self.preferred_backend = self._get_preferred_backend()

        # Error tracking
        self.consecutive_failures = 0
        self.max_consecutive_failures = 10
        self.last_successful_read = None
        self.total_frames_read = 0
        self.total_frames_failed = 0

    def _get_preferred_backend(self) -> CameraBackend:
        """Select best backend for platform"""
        if self.platform == "Darwin":  # macOS
            return CameraBackend.AVFOUNDATION
        elif self.platform == "Linux":
            return CameraBackend.V4L2
        elif self.platform == "Windows":
            return CameraBackend.DSHOW
        return CameraBackend.AUTO

    def enumerate_cameras(self, max_index: int = 10) -> List[CameraInfo]:
        """
        Enumerate available camera devices.

        Args:
            max_index: Maximum device index to probe

        Returns:
            List of detected cameras with metadata
        """
        cameras = []

        for idx in range(max_index):
            try:
                # Try preferred backend first
                cap = cv2.VideoCapture(idx, self.preferred_backend.value)

                if cap.isOpened():
                    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
                    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
                    fps = cap.get(cv2.CAP_PROP_FPS)

                    # Get backend name
                    backend_name = cap.getBackendName()

                    # Generate descriptive name
                    name = f"Camera {idx}"
                    if self.platform == "Darwin":
                        name = f"FaceTime HD Camera {idx}" if idx == 0 else f"Camera {idx}"

                    cameras.append(CameraInfo(
                        index=idx,
                        name=name,
                        backend=backend_name,
                        width=width if width > 0 else 0,
                        height=height if height > 0 else 0,
                        fps=fps if fps > 0 else 0.0,
                        is_available=True
                    ))

                    cap.release()
                else:
                    # Camera exists but cannot be opened
                    cameras.append(CameraInfo(
                        index=idx,
                        name=f"Camera {idx}",
                        backend="none",
                        width=0,
                        height=0,
                        fps=0.0,
                        is_available=False
                    ))
            except Exception as e:
                # Camera enumeration failed for this index
                print(f"Warning: Failed to enumerate camera {idx}: {e}")
                continue

        # Filter to only available cameras
        return [cam for cam in cameras if cam.is_available]

    def initialize(
        self,
        source: Optional[Union[int, str]] = None,
        config: Optional[CameraConfig] = None,
        mode: CameraMode = CameraMode.REAL
    ) -> bool:
        """
        Initialize camera system.

        Args:
            source: Camera index (int) or device path (str). None uses default (0)
            config: Camera configuration. None uses defaults
            mode: CameraMode.REAL for hardware, CameraMode.SYNTHETIC for testing

        Returns:
            True if initialization successful
        """
        self.mode = mode
        self.config = config or CameraConfig()
        self.current_source = source if source is not None else 0

        try:
            if mode == CameraMode.SYNTHETIC:
                return self._initialize_synthetic()
            else:
                return self._initialize_real()
        except Exception as e:
            print(f"Camera initialization failed: {e}")
            return False

    def _initialize_synthetic(self) -> bool:
        """Initialize synthetic camera"""
        self.camera = SyntheticCamera(
            width=self.config.width,
            height=self.config.height,
            fps=self.config.fps
        )
        self.is_initialized = True
        print(f"✓ Synthetic camera initialized: {self.config.width}x{self.config.height} @ {self.config.fps} FPS")
        return True

    def _initialize_real(self) -> bool:
        """Initialize real hardware camera"""
        # Determine backend
        backend = self.config.backend.value
        if backend == cv2.CAP_ANY:
            backend = self.preferred_backend.value

        # Open camera
        if isinstance(self.current_source, int):
            self.camera = cv2.VideoCapture(self.current_source, backend)
        else:
            self.camera = cv2.VideoCapture(self.current_source)

        if not self.camera.isOpened():
            raise RuntimeError(f"Failed to open camera source: {self.current_source}")

        # Configure camera properties
        self.camera.set(cv2.CAP_PROP_FRAME_WIDTH, self.config.width)
        self.camera.set(cv2.CAP_PROP_FRAME_HEIGHT, self.config.height)
        self.camera.set(cv2.CAP_PROP_FPS, self.config.fps)
        self.camera.set(cv2.CAP_PROP_BUFFERSIZE, self.config.buffer_size)

        # Verify actual settings
        actual_width = int(self.camera.get(cv2.CAP_PROP_FRAME_WIDTH))
        actual_height = int(self.camera.get(cv2.CAP_PROP_FRAME_HEIGHT))
        actual_fps = self.camera.get(cv2.CAP_PROP_FPS)

        self.is_initialized = True
        print(f"✓ Camera initialized: {actual_width}x{actual_height} @ {actual_fps:.1f} FPS")
        print(f"  Source: {self.current_source} | Backend: {self.camera.getBackendName()}")

        return True

    def read_frame(self) -> Tuple[bool, Optional[np.ndarray]]:
        """
        Read frame from camera.

        Returns:
            (success, frame) tuple
        """
        if not self.is_initialized or self.camera is None:
            return False, None

        try:
            ret, frame = self.camera.read()
            if not ret or frame is None:
                return False, None

            # Flip horizontally for mirror effect (common for front-facing cameras)
            if self.mode == CameraMode.REAL:
                frame = cv2.flip(frame, 1)

            return True, frame

        except Exception as e:
            print(f"Frame read error: {e}")
            return False, None

    def get_frame_size(self) -> Tuple[int, int]:
        """Get current frame dimensions (width, height)"""
        if not self.is_initialized or self.camera is None:
            return (0, 0)

        width = int(self.camera.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(self.camera.get(cv2.CAP_PROP_FRAME_HEIGHT))
        return (width, height)

    def get_fps(self) -> float:
        """Get camera FPS"""
        if not self.is_initialized or self.camera is None:
            return 0.0
        return self.camera.get(cv2.CAP_PROP_FPS)

    def switch_source(self, source: Union[int, str]) -> bool:
        """
        Switch to different camera source.

        Args:
            source: New camera index or device path

        Returns:
            True if switch successful
        """
        if self.is_initialized:
            self.release()

        return self.initialize(source=source, config=self.config, mode=self.mode)

    def switch_mode(self, mode: CameraMode) -> bool:
        """
        Switch between real and synthetic camera modes.

        Args:
            mode: Target camera mode

        Returns:
            True if switch successful
        """
        if self.mode == mode:
            return True

        if self.is_initialized:
            self.release()

        return self.initialize(source=self.current_source, config=self.config, mode=mode)

    def release(self):
        """Release camera resources"""
        if self.camera is not None:
            self.camera.release()
            self.camera = None

        self.is_initialized = False
        print("✓ Camera released")

    def __enter__(self):
        """Context manager entry"""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.release()

    def get_info(self) -> Dict:
        """Get current camera system information"""
        if not self.is_initialized:
            return {"status": "not_initialized"}

        width, height = self.get_frame_size()

        return {
            "status": "initialized",
            "mode": self.mode.value,
            "source": self.current_source,
            "resolution": f"{width}x{height}",
            "fps": self.get_fps(),
            "platform": self.platform,
            "backend": self.camera.getBackendName() if hasattr(self.camera, 'getBackendName') else "synthetic"
        }


# Demo and testing
if __name__ == "__main__":
    print("=== Camera System Test ===\n")

    # Create camera system
    cam_system = CameraSystem()

    # Enumerate available cameras
    print("Enumerating cameras...")
    cameras = cam_system.enumerate_cameras()

    if cameras:
        print(f"\nFound {len(cameras)} camera(s):")
        for cam in cameras:
            print(f"  [{cam.index}] {cam.name}")
            print(f"      Backend: {cam.backend}")
            print(f"      Resolution: {cam.width}x{cam.height}")
            print(f"      FPS: {cam.fps:.1f}")
    else:
        print("No cameras detected - will use synthetic mode")

    # Initialize camera (fallback to synthetic if no hardware)
    print("\nInitializing camera...")
    config = CameraConfig(width=1280, height=720, fps=30)

    if cameras:
        success = cam_system.initialize(source=0, config=config, mode=CameraMode.REAL)
    else:
        success = cam_system.initialize(config=config, mode=CameraMode.SYNTHETIC)

    if not success:
        print("Failed to initialize camera")
        exit(1)

    # Display camera info
    info = cam_system.get_info()
    print("\nCamera Info:")
    for key, value in info.items():
        print(f"  {key}: {value}")

    # Capture and display frames
    print("\nCapturing frames... (press 'q' to quit, 's' to switch to synthetic)")

    try:
        while True:
            ret, frame = cam_system.read_frame()

            if not ret or frame is None:
                print("Failed to read frame")
                break

            # Add HUD overlay
            cv2.putText(
                frame,
                f"Mode: {cam_system.mode.value.upper()} | {info['resolution']} | {info['fps']:.1f} FPS",
                (20, frame.shape[0] - 20),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.6,
                (56, 189, 248),
                2,
                cv2.LINE_AA
            )

            cv2.imshow("Camera System Test", frame)

            key = cv2.waitKey(1) & 0xFF
            if key == ord('q'):
                break
            elif key == ord('s'):
                # Toggle between real and synthetic
                new_mode = CameraMode.SYNTHETIC if cam_system.mode == CameraMode.REAL else CameraMode.REAL
                print(f"\nSwitching to {new_mode.value} mode...")
                cam_system.switch_mode(new_mode)
                info = cam_system.get_info()

    finally:
        cam_system.release()
        cv2.destroyAllWindows()
        print("\nTest complete")


# Alias for backward compatibility
CameraCapture = CameraSystem
