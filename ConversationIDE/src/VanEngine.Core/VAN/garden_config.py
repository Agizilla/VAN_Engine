from __future__ import annotations

from pathlib import Path


class GardenConfig:
    def __init__(self, state_root: str = "", schema_root: str = "",
                 registry_root: str = "", policy_root: str = ""):
        self.state_root = state_root
        self.schema_root = schema_root
        self.registry_root = registry_root
        self.policy_root = policy_root

    @property
    def is_complete(self) -> bool:
        return all([self.state_root, self.schema_root, self.registry_root, self.policy_root])

    @staticmethod
    def from_directory(dir_path: str) -> GardenConfig:
        d = Path(dir_path)
        return GardenConfig(
            state_root=str(d / "garden_one_state.json"),
            schema_root=str(d / "garden_two_schema.json"),
            registry_root=str(d / "garden_three_registry.json"),
            policy_root=str(d / "garden_four_network_policy.json"),
        )

    def all_paths(self) -> list[str]:
        return [self.state_root, self.schema_root, self.registry_root, self.policy_root]
