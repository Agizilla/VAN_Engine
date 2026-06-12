import sys
import io
import json
import math
from typing import Tuple, Optional

if sys.platform == 'win32' and not isinstance(sys.stdout, io.TextIOWrapper):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')


class IsographicQuaternion:
    def __init__(self, w: float, x: float, y: float, z: float):
        self.w = w
        self.x = x
        self.y = y
        self.z = z

    def get_sound_projection(self) -> float:
        return math.sqrt(self.w**2 + self.x**2)

    def get_shape_projection(self) -> float:
        return math.sqrt(self.w**2 + self.y**2)

    def get_number_projection(self) -> float:
        return math.sqrt(self.x**2 + self.z**2)

    def get_time_projection(self) -> float:
        return math.sqrt(self.y**2 + self.z**2)

    @property
    def magnitude(self) -> float:
        return math.sqrt(self.w**2 + self.x**2 + self.y**2 + self.z**2)

    def normalize(self) -> 'IsographicQuaternion':
        mag = self.magnitude
        if mag < 1e-10:
            return IsographicQuaternion(1.0, 0.0, 0.0, 0.0)
        return IsographicQuaternion(self.w / mag, self.x / mag, self.y / mag, self.z / mag)

    def __mul__(self, other: 'IsographicQuaternion') -> 'IsographicQuaternion':
        w = self.w * other.w - self.x * other.x - self.y * other.y - self.z * other.z
        x = self.w * other.x + self.x * other.w + self.y * other.z - self.z * other.y
        y = self.w * other.y - self.x * other.z + self.y * other.w + self.z * other.x
        z = self.w * other.z + self.x * other.y - self.y * other.x + self.z * other.w
        return IsographicQuaternion(w, x, y, z)

    def approx_equals(self, other: 'IsographicQuaternion', epsilon: float = 1e-6) -> bool:
        return (abs(self.w - other.w) < epsilon and
                abs(self.x - other.x) < epsilon and
                abs(self.y - other.y) < epsilon and
                abs(self.z - other.z) < epsilon)

    def to_tuple(self) -> Tuple[float, float, float, float]:
        return (self.w, self.x, self.y, self.z)

    @classmethod
    def from_tuple(cls, t: Tuple[float, float, float, float]) -> 'IsographicQuaternion':
        return cls(t[0], t[1], t[2], t[3])


class QuaternionClient:
    def __init__(self, bridge):
        self.bridge = bridge

    def lookup(self, token: str) -> Optional[IsographicQuaternion]:
        result = self.bridge.quaternion_lookup(token)
        if result:
            return IsographicQuaternion.from_tuple(result)
        return None

    def store(self, token: str, quat: IsographicQuaternion, applies_to: str):
        self.bridge.quaternion_store(token, quat.w, quat.x, quat.y, quat.z, applies_to)

    def validate_round_trip(self, token: str) -> bool:
        quat = self.lookup(token)
        if quat is None:
            return False
        original_mag = quat.magnitude
        sound = quat.get_sound_projection()
        shape = quat.get_shape_projection()
        number = quat.get_number_projection()
        time_val = quat.get_time_projection()
        reconstructed = IsographicQuaternion(
            math.sqrt(abs(sound * shape)),
            math.sqrt(abs(sound * number)),
            math.sqrt(abs(shape * time_val)),
            math.sqrt(abs(number * time_val))
        )
        return abs(original_mag - reconstructed.magnitude) < 1e-6


if __name__ == '__main__':
    q = IsographicQuaternion(0.707, 0.707, 0.0, 0.0)
    print(json.dumps({
        "magnitude": q.magnitude,
        "sound": q.get_sound_projection(),
        "shape": q.get_shape_projection(),
        "normalized": q.normalize().to_tuple()
    }))
