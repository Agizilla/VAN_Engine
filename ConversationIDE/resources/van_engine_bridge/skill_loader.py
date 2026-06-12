#!/usr/bin/env python3
import sys, io, json, yaml
from pathlib import Path
from typing import Dict, Any, List, Optional, TypeVar, Generic
from dataclasses import dataclass, field

if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

T = TypeVar('T')

@dataclass
class ExtendManifest:
    skill: str = ""
    extends: List[str] = field(default_factory=list)
    merge_strategy: str = "append"
    enabled: bool = True
    description: str = ""

class SkillLoader:
    def __init__(self, base_directory: Path):
        self.skills_dir = base_directory / "skills"
        self.customizations_dir = base_directory / "USER" / "SKILLCUSTOMIZATIONS"
        self._manifests: Dict[str, ExtendManifest] = {}
        self._load_manifests()

    def _load_manifests(self):
        if not self.customizations_dir.exists():
            return
        for skill_dir in self.customizations_dir.iterdir():
            if not skill_dir.is_dir():
                continue
            manifest_path = skill_dir / "EXTEND.yaml"
            if manifest_path.exists():
                try:
                    content = manifest_path.read_text(encoding='utf-8')
                    manifest = self._parse_extend_manifest(content)
                    if manifest and manifest.enabled:
                        self._manifests[skill_dir.name] = manifest
                except Exception as e:
                    print(f"[SkillLoader] Warning: Failed to load {manifest_path}: {e}")

    def _parse_extend_manifest(self, yaml_content: str) -> Optional[ExtendManifest]:
        try:
            data = yaml.safe_load(yaml_content)
            if not data:
                return None
            return ExtendManifest(skill=data.get('skill', ''),
                extends=data.get('extends', []),
                merge_strategy=data.get('merge_strategy', 'append'),
                enabled=data.get('enabled', True),
                description=data.get('description', ''))
        except:
            return None

    def load_config(self, skill_name: str, config_filename: str) -> Dict[str, Any]:
        base_config_path = self.skills_dir / skill_name / config_filename
        base_config = {}
        if base_config_path.exists():
            try:
                content = base_config_path.read_text(encoding='utf-8')
                base_config = json.loads(content)
            except:
                pass
        manifest = self._manifests.get(skill_name)
        if not manifest or not manifest.enabled:
            return base_config
        if config_filename not in manifest.extends:
            return base_config
        custom_config_path = self.customizations_dir / skill_name / config_filename
        if not custom_config_path.exists():
            return base_config
        try:
            custom_content = custom_config_path.read_text(encoding='utf-8')
            custom_config = json.loads(custom_content)
        except:
            return base_config
        if manifest.merge_strategy == "override":
            return custom_config
        elif manifest.merge_strategy == "deep_merge":
            return self._deep_merge(base_config, custom_config)
        else:
            return self._append_merge(base_config, custom_config)

    def _deep_merge(self, base: Dict, custom: Dict) -> Dict:
        result = base.copy()
        for key, value in custom.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self._deep_merge(result[key], value)
            else:
                result[key] = value
        return result

    def _append_merge(self, base: Dict, custom: Dict) -> Dict:
        result = base.copy()
        for key, value in custom.items():
            if key in result and isinstance(result[key], list) and isinstance(value, list):
                result[key] = result[key] + value
            else:
                result[key] = value
        return result

    def has_customizations(self, skill_name: str) -> bool:
        return skill_name in self._manifests

    def list_customized_skills(self) -> List[str]:
        return list(self._manifests.keys())

    def get_customization_path(self, skill_name: str) -> Path:
        return self.customizations_dir / skill_name

def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("skill_name", help="Skill name")
    parser.add_argument("config_file", help="Config file name")
    parser.add_argument("--base-dir", default=str(Path.home() / ".claude"), help="Base directory (default: ~/.claude)")
    args = parser.parse_args()
    loader = SkillLoader(Path(args.base_dir))
    config = loader.load_config(args.skill_name, args.config_file)
    print(json.dumps(config, indent=2))

if __name__ == "__main__":
    main()
