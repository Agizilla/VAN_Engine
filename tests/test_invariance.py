"""
Invariance Guard: Round-trip validation preserving quaternion magnitude
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

sys.path.append('/VAN_Engine/core')
from IsographicQuaternion import IsographicQuaternion


class InvariantContractException(Exception):
    """Raised when invariance is violated"""
    pass


class MockSubstrate:
    """Mock for testing - simulates token lookup and resolution"""

    def __init__(self):
        self._tokens = {
            "bluetooth": IsographicQuaternion(0.8, 0.3, 0.2, 0.1),
            "audio": IsographicQuaternion(0.7, 0.4, 0.3, 0.2),
            "quaternion": IsographicQuaternion(0.9, 0.2, 0.1, 0.05),
            "iso_009": IsographicQuaternion(0.95, 0.1, 0.05, 0.02),
            "sound_shape": IsographicQuaternion(0.99, 0.01, 0.01, 0.01),
        }

    def lookup(self, token_key: str) -> IsographicQuaternion:
        if token_key not in self._tokens:
            raise KeyError(f"Token not found: {token_key}")
        return self._tokens[token_key]

    def resolve_from_quaternion(self, quat: IsographicQuaternion) -> str:
        """Find closest token by quaternion similarity"""
        best_token = None
        best_similarity = -1

        for token, stored_quat in self._tokens.items():
            dot = (quat.w * stored_quat.w + quat.x * stored_quat.x +
                   quat.y * stored_quat.y + quat.z * stored_quat.z)
            mag_product = quat.magnitude * stored_quat.magnitude
            similarity = dot / mag_product if mag_product > 0 else 0
            if similarity > best_similarity:
                best_similarity = similarity
                best_token = token

        return best_token if best_token else "unknown"

    def resolve_from_coordinates(self, sound: float, shape: float,
                                  number: float, time: float) -> str:
        """Legacy method - reconstruct quaternion from projections"""
        # This is lossy! The invariance guard tests magnitude preservation
        # to detect this loss.
        quat = IsographicQuaternion(
            w=math.sqrt(max(0, min(sound, shape) ** 2)),
            x=math.sqrt(max(0, sound ** 2 - min(sound, shape) ** 2)),
            y=math.sqrt(max(0, shape ** 2 - min(sound, shape) ** 2)),
            z=math.sqrt(max(0, number ** 2 + time ** 2))
        )
        return self.resolve_from_quaternion(quat)


class InvarianceGuard:
    """ISO_TEST_HARNESS: Validates round-trip magnitude preservation"""

    def __init__(self, substrate: MockSubstrate, tolerance: float = 1e-6):
        self.substrate = substrate
        self.tolerance = tolerance

    def assert_round_trip_integrity(self, initial_token_key: str) -> bool:
        """Round-trip: Token -> Sound -> Shape -> Number -> Time -> Token"""
        # Lookup token -> quaternion
        initial_quat = self.substrate.lookup(initial_token_key)

        # Extract projections (lossy operation)
        sound = initial_quat.get_sound_projection()
        shape = initial_quat.get_shape_projection()
        number = initial_quat.get_number_projection()
        time_val = initial_quat.get_time_projection()

        # Resolve back from coordinates (more loss)
        resolved_key = self.substrate.resolve_from_coordinates(sound, shape, number, time_val)

        # Critical: compare quaternion magnitudes, not tokens
        resolved_quat = self.substrate.lookup(resolved_key)

        original_mag = initial_quat.magnitude
        resolved_mag = resolved_quat.magnitude
        mag_diff = abs(original_mag - resolved_mag)

        if mag_diff > self.tolerance:
            raise InvariantContractException(
                f"Semantic drift detected! Token '{initial_token_key}' "
                f"magnitude decay from {original_mag:.6f} to {resolved_mag:.6f} "
                f"(diff={mag_diff:.6f})"
            )

        print(f"✓ Round-trip passed for '{initial_token_key}': "
              f"magnitude preserved ({original_mag:.6f} -> {resolved_mag:.6f})")
        return True

    def assert_direct_round_trip(self, initial_token_key: str) -> bool:
        """Direct quaternion round-trip (no projection loss)"""
        initial_quat = self.substrate.lookup(initial_token_key)
        resolved_token = self.substrate.resolve_from_quaternion(initial_quat)
        resolved_quat = self.substrate.lookup(resolved_token)

        if not initial_quat.approx_equal(resolved_quat, self.tolerance):
            raise InvariantContractException(
                f"Direct quaternion mismatch for '{initial_token_key}':\n"
                f"  Original: {initial_quat}\n"
                f"  Resolved: {resolved_quat}"
            )

        mag_match = abs(initial_quat.magnitude - resolved_quat.magnitude) < self.tolerance
        if not mag_match:
            raise InvariantContractException(
                f"Magnitude mismatch for '{initial_token_key}': "
                f"{initial_quat.magnitude:.6f} vs {resolved_quat.magnitude:.6f}"
            )

        print(f"✓ Direct round-trip passed for '{initial_token_key}'")
        return True


def test_invariance_guard():
    substrate = MockSubstrate()
    guard = InvarianceGuard(substrate)

    # Test tokens that should pass
    test_tokens = ["bluetooth", "audio", "quaternion", "iso_009", "sound_shape"]

    for token in test_tokens:
        try:
            guard.assert_round_trip_integrity(token)
        except InvariantContractException as e:
            print(f"✗ Failed for {token}: {e}")

    print("\n--- Direct round-trip tests (should all pass) ---")
    for token in test_tokens:
        try:
            guard.assert_direct_round_trip(token)
        except InvariantContractException as e:
            print(f"✗ Direct failed for {token}: {e}")


if __name__ == "__main__":
    test_invariance_guard()
