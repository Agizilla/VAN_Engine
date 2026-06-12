"""
Isographic Quaternion with coupled dimensions (Sound-Shape, Sound-Number, Shape-Time, Number-Time)
ISO_009: Quadruple Mapping
Windows UTF-8 safe
"""

import sys
import io
import math

if sys.platform == 'win32':
    if hasattr(sys.stdout, 'buffer') and sys.stdout.buffer and not isinstance(sys.stdout, io.TextIOWrapper):
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    if hasattr(sys.stderr, 'buffer') and sys.stderr.buffer and not isinstance(sys.stderr, io.TextIOWrapper):
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')


class IsographicQuaternion:
    """4D quaternion with coupled dimensions for isographic indexing"""

    def __init__(self, w: float, x: float, y: float, z: float):
        self.w = w  # Sound-Shape coupling
        self.x = x  # Sound-Number coupling
        self.y = y  # Shape-Time coupling
        self.z = z  # Number-Time coupling

    def get_sound_projection(self) -> float:
        return math.sqrt(self.w * self.w + self.x * self.x)

    def get_shape_projection(self) -> float:
        return math.sqrt(self.w * self.w + self.y * self.y)

    def get_number_projection(self) -> float:
        return math.sqrt(self.x * self.x + self.z * self.z)

    def get_time_projection(self) -> float:
        return math.sqrt(self.y * self.y + self.z * self.z)

    @property
    def magnitude(self) -> float:
        return math.sqrt(self.w * self.w + self.x * self.x + self.y * self.y + self.z * self.z)

    def normalize(self) -> 'IsographicQuaternion':
        mag = self.magnitude
        if mag < 1e-10:
            return self
        return IsographicQuaternion(self.w / mag, self.x / mag, self.y / mag, self.z / mag)

    def __mul__(self, other: 'IsographicQuaternion') -> 'IsographicQuaternion':
        return IsographicQuaternion(
            self.w * other.w - self.x * other.x - self.y * other.y - self.z * other.z,
            self.w * other.x + self.x * other.w + self.y * other.z - self.z * other.y,
            self.w * other.y - self.x * other.z + self.y * other.w + self.z * other.x,
            self.w * other.z + self.x * other.y - self.y * other.x + self.z * other.w
        )

    def approx_equal(self, other: 'IsographicQuaternion', tolerance: float = 1e-6) -> bool:
        return (abs(self.w - other.w) < tolerance and
                abs(self.x - other.x) < tolerance and
                abs(self.y - other.y) < tolerance and
                abs(self.z - other.z) < tolerance)

    def __repr__(self) -> str:
        return f"IsographicQuaternion(w={self.w:.3f}, x={self.x:.3f}, y={self.y:.3f}, z={self.z:.3f})"
