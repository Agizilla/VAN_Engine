"""
Test suite for ISO_010 Drift Gating
"""

import sys
import io

if sys.platform == 'win32':
    if hasattr(sys.stdout, 'buffer') and sys.stdout.buffer and not isinstance(sys.stdout, io.TextIOWrapper):
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    if hasattr(sys.stderr, 'buffer') and sys.stderr.buffer and not isinstance(sys.stderr, io.TextIOWrapper):
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

sys.path.append('/VAN_Engine/core')
sys.path.append('/VAN_Engine/modules')
from IsographicQuaternion import IsographicQuaternion
from drift_gating import IsographicDriftGating


def test_known_node():
    gate = IsographicDriftGating(density_threshold=0.85)
    known = IsographicQuaternion(0.8, 0.3, 0.2, 0.1)
    result = gate.validate_interception(known)
    assert result.violated == False
    assert result.action == "EXECUTE_DETERMINISTIC_PATH"
    print("✓ test_known_node passed")


def test_random_node():
    gate = IsographicDriftGating(density_threshold=0.85)
    random_q = IsographicQuaternion(0.9, 0.8, 0.7, 0.6)
    result = gate.validate_interception(random_q)
    assert result.violated == True
    assert result.action == "HALT_AND_CLARIFY"
    assert result.diagnostic is not None
    print("✓ test_random_node passed")


def test_edge_case():
    gate = IsographicDriftGating(density_threshold=0.85)
    # Very close to known but slightly off
    edge = IsographicQuaternion(0.82, 0.31, 0.21, 0.11)
    result = gate.validate_interception(edge)
    # Should still be within threshold
    print(f"Edge case result: violated={result.violated}")


def test_missing_dimensions():
    gate = IsographicDriftGating(density_threshold=0.85)
    # Quaternion missing W coupling
    missing_w = IsographicQuaternion(0.01, 0.8, 0.8, 0.8)
    result = gate.validate_interception(missing_w)
    if result.diagnostic:
        missing = result.diagnostic.get("missing_dimensions", [])
        print(f"Missing dimensions detected: {missing}")


if __name__ == "__main__":
    test_known_node()
    test_random_node()
    test_edge_case()
    test_missing_dimensions()
    print("\nAll drift gating tests complete.")
