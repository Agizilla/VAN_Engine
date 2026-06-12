"""
ISO_010: Drift Gating - Deterministic Halt on Low Confidence
Windows UTF-8 safe
"""

import sys
import io
import math
from typing import Optional, Dict, Any, List, Tuple
from dataclasses import dataclass, field

if sys.platform == 'win32':
    if hasattr(sys.stdout, 'buffer') and sys.stdout.buffer and not isinstance(sys.stdout, io.TextIOWrapper):
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    if hasattr(sys.stderr, 'buffer') and sys.stderr.buffer and not isinstance(sys.stderr, io.TextIOWrapper):
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# Import quaternion
sys.path.append('/VAN_Engine/core')
from IsographicQuaternion import IsographicQuaternion


@dataclass
class GatingResult:
    """Result of drift gate validation"""
    violated: bool
    action: str  # "HALT_AND_CLARIFY" or "EXECUTE_DETERMINISTIC_PATH"
    diagnostic: Optional[Dict[str, Any]] = None


@dataclass
class DiagnosticBlock:
    """Structured diagnostic for clarification"""
    exception_type: str
    target_coordinates: Tuple[float, float, float, float]
    nearest_valid_nodes: List[str]
    missing_dimensions: List[str]
    suggested_questions: List[str] = field(default_factory=list)


class IsographicDriftGating:
    """ISO_010: Halt execution when query drifts outside indexed space"""

    def __init__(self, density_threshold: float = 0.85):
        self.density_threshold = density_threshold
        # In production, this would connect to the actual substrate
        self._mock_substrate = self._create_mock_substrate()

    def _create_mock_substrate(self):
        """Mock substrate for testing - replace with actual index"""
        return {
            "bluetooth": IsographicQuaternion(0.8, 0.3, 0.2, 0.1),
            "audio": IsographicQuaternion(0.7, 0.4, 0.3, 0.2),
            "quaternion": IsographicQuaternion(0.9, 0.2, 0.1, 0.05),
            "iso_009": IsographicQuaternion(0.95, 0.1, 0.05, 0.02)
        }

    def calculate_graph_density(self, target: IsographicQuaternion) -> float:
        """Calculate proximity to nearest localized ISO node cluster"""
        # Simplified: maximum similarity to any known node
        max_similarity = 0.0
        for node_name, node_quat in self._mock_substrate.items():
            # Cosine similarity on quaternion magnitude
            dot = (target.w * node_quat.w + target.x * node_quat.x +
                   target.y * node_quat.y + target.z * node_quat.z)
            mag_product = target.magnitude * node_quat.magnitude
            if mag_product > 0:
                similarity = dot / mag_product
                max_similarity = max(max_similarity, similarity)
        return max_similarity

    def get_nearest_nodes(self, target: IsographicQuaternion, limit: int = 2) -> List[str]:
        """Get nearest valid nodes for diagnostic"""
        similarities = []
        for name, quat in self._mock_substrate.items():
            dot = (target.w * quat.w + target.x * quat.x +
                   target.y * quat.y + target.z * quat.z)
            mag_product = target.magnitude * quat.magnitude
            sim = dot / mag_product if mag_product > 0 else 0
            similarities.append((name, sim))
        similarities.sort(key=lambda x: x[1], reverse=True)
        return [name for name, _ in similarities[:limit]]

    def detect_missing_couplings(self, target: IsographicQuaternion) -> List[str]:
        """Detect which dimensions are underrepresented"""
        missing = []
        mag = target.magnitude
        if mag < 1e-6:
            return ["all_dimensions"]

        w_ratio = abs(target.w / mag)
        x_ratio = abs(target.x / mag)
        y_ratio = abs(target.y / mag)
        z_ratio = abs(target.z / mag)

        if w_ratio < 0.1:
            missing.append("sound_shape_coupling")
        if x_ratio < 0.1:
            missing.append("sound_number_coupling")
        if y_ratio < 0.1:
            missing.append("shape_time_coupling")
        if z_ratio < 0.1:
            missing.append("number_time_coupling")

        return missing if missing else ["none"]

    def validate_interception(self, target: IsographicQuaternion) -> GatingResult:
        """Main entry point for drift gating"""
        local_density = self.calculate_graph_density(target)

        if local_density < self.density_threshold:
            nearest = self.get_nearest_nodes(target)
            missing = self.detect_missing_couplings(target)

            diagnostic = DiagnosticBlock(
                exception_type="ISO_010_BOUNDARY_VIOLATION",
                target_coordinates=(target.w, target.x, target.y, target.z),
                nearest_valid_nodes=nearest,
                missing_dimensions=missing,
                suggested_questions=[
                    f"Does this involve {missing[0] if missing else 'unknown'}?",
                    "Can you provide a temporal anchor (pre-1994 vs post-1994)?",
                    "Is this related to any known ISO node?"
                ]
            )

            return GatingResult(
                violated=True,
                action="HALT_AND_CLARIFY",
                diagnostic={
                    "exception": diagnostic.exception_type,
                    "nearest_nodes": diagnostic.nearest_valid_nodes,
                    "missing_dimensions": diagnostic.missing_dimensions,
                    "action": diagnostic.exception_type,
                    "prompt": f"The token requested intersects known concepts but lacks a precise {'/'.join(diagnostic.missing_dimensions)} anchor. Please clarify."
                }
            )

        return GatingResult(
            violated=False,
            action="EXECUTE_DETERMINISTIC_PATH"
        )


# Test function
def test_drift_gating():
    gate = IsographicDriftGating(density_threshold=0.85)

    # Test with known node
    known = IsographicQuaternion(0.8, 0.3, 0.2, 0.1)
    result = gate.validate_interception(known)
    print(f"Known node test: violated={result.violated}, action={result.action}")

    # Test with random quaternion far from any node
    random_q = IsographicQuaternion(0.1, 0.9, 0.8, 0.7)
    result = gate.validate_interception(random_q)
    print(f"Random node test: violated={result.violated}, action={result.action}")
    if result.diagnostic:
        print(f"  Diagnostic: {result.diagnostic.get('prompt', '')[:100]}...")


if __name__ == "__main__":
    test_drift_gating()
