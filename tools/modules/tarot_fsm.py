"""
ISO_011: Archetypal Finite State Machine - Tarot/Astrology as Deterministic State Machine
Windows UTF-8 safe
"""

import sys
import io
from dataclasses import dataclass
from typing import List, Dict, Any, Optional
from enum import Enum

if sys.platform == 'win32':
    if hasattr(sys.stdout, 'buffer') and sys.stdout.buffer and not isinstance(sys.stdout, io.TextIOWrapper):
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    if hasattr(sys.stderr, 'buffer') and sys.stderr.buffer and not isinstance(sys.stderr, io.TextIOWrapper):
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

from IsographicQuaternion import IsographicQuaternion


class TarotPosition(Enum):
    PAST = "past"
    PRESENT = "present"
    OBSTACLE = "obstacle"
    POTENTIAL = "potential"


class AstrologicalBody(Enum):
    SATURN = "saturn"
    JUPITER = "jupiter"
    MARS = "mars"
    VENUS = "venus"
    MERCURY = "mercury"
    MOON = "moon"
    SUN = "sun"


@dataclass
class AstrologicalTransit:
    """Transit modifier affecting quaternion dimensions"""
    body: AstrologicalBody
    sign: str
    target_dimension: str  # "W", "X", "Y", "Z", or "all"
    magnitude: float  # -1.0 to 1.0


@dataclass
class TarotCard:
    """Archetypal card with quaternion mapping"""
    name: str
    position: TarotPosition
    quaternion: IsographicQuaternion
    applies_to: List[str]


class TarotSpread:
    """Four-card spread representing an execution pipeline"""

    def __init__(self, past_node: TarotCard, present_node: TarotCard,
                 obstacle_node: TarotCard, potential_node: TarotCard):
        self.past_node = past_node
        self.present_node = present_node
        self.obstacle_node = obstacle_node
        self.potential_node = potential_node


@dataclass
class SystemicState:
    """Current state of the archetypal engine"""
    quaternion: IsographicQuaternion
    active_filters: List[str]
    constraints: Dict[str, float]


class ExecutionPipeline:
    """Executable pipeline derived from tarot layout"""

    def __init__(self):
        self.initial_state: Optional[IsographicQuaternion] = None
        self.active_filters: List[str] = []
        self.inversion_boundary: Optional[IsographicQuaternion] = None
        self.optimization_target: Optional[IsographicQuaternion] = None

    def set_initial_state(self, quat: IsographicQuaternion):
        self.initial_state = quat

    def apply_active_filter(self, applies_to: List[str]):
        self.active_filters = applies_to

    def inject_inversion_boundary(self, quat: IsographicQuaternion):
        self.inversion_boundary = quat

    def set_optimization_target(self, quat: IsographicQuaternion):
        self.optimization_target = quat

    def execute(self, input_quat: IsographicQuaternion) -> IsographicQuaternion:
        """Run the pipeline (simplified)"""
        result = input_quat

        if self.inversion_boundary:
            # Inversion: reflect across boundary
            result = IsographicQuaternion(
                w=2 * self.inversion_boundary.w - result.w,
                x=2 * self.inversion_boundary.x - result.x,
                y=2 * self.inversion_boundary.y - result.y,
                z=2 * self.inversion_boundary.z - result.z
            )

        if self.optimization_target:
            # Move toward target by 10%
            result = IsographicQuaternion(
                w=result.w + 0.1 * (self.optimization_target.w - result.w),
                x=result.x + 0.1 * (self.optimization_target.x - result.x),
                y=result.y + 0.1 * (self.optimization_target.y - result.y),
                z=result.z + 0.1 * (self.optimization_target.z - result.z)
            )

        return result


class ArchetypalStateMachine:
    """ISO_011: Creative variance engine using tarot/astrology as state machine"""

    def __init__(self):
        self.current_state = SystemicState(
            quaternion=IsographicQuaternion(1, 0, 0, 0),
            active_filters=[],
            constraints={}
        )
        self._card_library = self._init_card_library()

    def _init_card_library(self) -> Dict[str, TarotCard]:
        """Initialize common tarot cards with quaternion mappings"""
        return {
            "fool": TarotCard(
                name="The Fool",
                position=TarotPosition.PAST,
                quaternion=IsographicQuaternion(0.5, 0.5, 0.5, 0.5),
                applies_to=["beginnings", "potential", "risk"]
            ),
            "magician": TarotCard(
                name="The Magician",
                position=TarotPosition.PRESENT,
                quaternion=IsographicQuaternion(0.9, 0.2, 0.1, 0.05),
                applies_to=["manifestation", "willpower", "creation"]
            ),
            "tower": TarotCard(
                name="The Tower",
                position=TarotPosition.OBSTACLE,
                quaternion=IsographicQuaternion(0.1, 0.8, 0.7, 0.9),
                applies_to=["disruption", "breakthrough", "chaos"]
            ),
            "star": TarotCard(
                name="The Star",
                position=TarotPosition.POTENTIAL,
                quaternion=IsographicQuaternion(0.3, 0.3, 0.8, 0.8),
                applies_to=["hope", "guidance", "renewal"]
            )
        }

    def apply_transit_modifier(self, transit: AstrologicalTransit):
        """Apply astrological transit as dimension-specific filter"""
        quat = self.current_state.quaternion

        # Determine modifier based on transit body and target dimension
        modifier = 1.0 + transit.magnitude

        if transit.target_dimension == "W" or transit.target_dimension == "all":
            quat.w *= modifier
        if transit.target_dimension == "X" or transit.target_dimension == "all":
            quat.x *= modifier
        if transit.target_dimension == "Y" or transit.target_dimension == "all":
            quat.y *= modifier
        if transit.target_dimension == "Z" or transit.target_dimension == "all":
            quat.z *= modifier

        self.current_state.quaternion = quat.normalize()
        self.current_state.active_filters.append(f"{transit.body.value}_{transit.sign}")

    def process_layout(self, spread: TarotSpread) -> ExecutionPipeline:
        """Convert tarot layout to executable pipeline"""
        pipeline = ExecutionPipeline()

        # Position 1: Past → Historical Baseline
        pipeline.set_initial_state(spread.past_node.quaternion)

        # Position 2: Present → Active Context Constraints
        pipeline.apply_active_filter(spread.present_node.applies_to)

        # Position 3: Obstacle → Inversion/High-Impedance Filter
        pipeline.inject_inversion_boundary(spread.obstacle_node.quaternion)

        # Position 4: Potential → Target Evolutionary Path
        pipeline.set_optimization_target(spread.potential_node.quaternion)

        return pipeline

    def generate_variation(self, base_quat: IsographicQuaternion,
                           spread: TarotSpread) -> IsographicQuaternion:
        """Generate creative variation using tarot pipeline"""
        pipeline = self.process_layout(spread)
        return pipeline.execute(base_quat)


# Test function
def test_tarot_fsm():
    fsm = ArchetypalStateMachine()

    # Create a spread
    spread = TarotSpread(
        past_node=fsm._card_library["fool"],
        present_node=fsm._card_library["magician"],
        obstacle_node=fsm._card_library["tower"],
        potential_node=fsm._card_library["star"]
    )

    # Apply a transit
    transit = AstrologicalTransit(
        body=AstrologicalBody.SATURN,
        sign="Pisces",
        target_dimension="W",  # Sound-Shape coupling
        magnitude=0.3
    )
    fsm.apply_transit_modifier(transit)

    # Generate variation
    base = IsographicQuaternion(0.6, 0.4, 0.3, 0.2)
    result = fsm.generate_variation(base, spread)

    print(f"Base quaternion: {base}")
    print(f"After transit + tarot: {result}")
    print(f"Magnitude preserved: {abs(base.magnitude - result.magnitude) < 0.01}")


if __name__ == "__main__":
    test_tarot_fsm()
