"""SVG Animated skill — generates SMIL-animated SVG from pose keyframes.

Routes:
  - animate: Generate animated SVG from pose_system.json config
  - list: Show available pose configs in tools/animation/
"""
import hashlib
import json
import os
from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parent.parent
ANIM_DIR = SKILL_DIR / "tools" / "animation"
POSE_SYSTEM = ANIM_DIR / "pose_system.json"
GENERATOR = ANIM_DIR / "gen_svg_animation.py"
SVG_CACHE_DIR = Path(__file__).resolve().parent / "_svg_cache"


class SvgAnimatedSkill:
    def execute(self, action: str = "animate", pose_config: str = None,
                output: str = None, fmt: str = "svg", **kwargs) -> dict:
        if action == "list":
            return self._list_configs()
        if action == "animate":
            return self._animate(pose_config, output, fmt)
        return {"error": f"Unknown action: {action}"}

    def _list_configs(self) -> dict:
        configs = []
        if ANIM_DIR.exists():
            for f in sorted(ANIM_DIR.glob("*.json")):
                try:
                    d = json.loads(f.read_text(encoding="utf-8"))
                    chars = list(d.get("characters", {}).keys())
                    kfs = len(d.get("animation", {}).get("keyframes", []))
                    dur = d.get("animation", {}).get("duration", 0)
                    configs.append({
                        "filename": f.name,
                        "path": str(f),
                        "characters": chars,
                        "keyframes": kfs,
                        "duration": dur,
                    })
                except Exception:
                    pass
        return {"result": {"configs": configs}}

    def _validate_config(self, config: dict) -> list[str]:
        warnings = []
        if "characters" not in config:
            warnings.append("Missing required key: 'characters'")
        anim = config.get("animation", {})
        if "duration" not in anim:
            warnings.append("Missing required key: 'animation.duration'")
        elif anim["duration"] < 0.5:
            warnings.append("Warning: animation.duration < 0.5s may be too short")
        if "keyframes" not in anim:
            warnings.append("Missing required key: 'keyframes'")
        elif len(anim["keyframes"]) < 2:
            warnings.append("Warning: fewer than 2 keyframes may produce no motion")
        return warnings

    def _get_cache_key(self, config: dict) -> str:
        raw = json.dumps(config, sort_keys=True)
        return hashlib.md5(raw.encode()).hexdigest()

    def _cache_get(self, key: str, fmt: str) -> str | None:
        cache_file = SVG_CACHE_DIR / f"{key}.{fmt}"
        if cache_file.exists():
            return cache_file.read_text(encoding="utf-8")
        return None

    def _cache_put(self, key: str, fmt: str, content: str):
        SVG_CACHE_DIR.mkdir(parents=True, exist_ok=True)
        cache_file = SVG_CACHE_DIR / f"{key}.{fmt}"
        cache_file.write_text(content, encoding="utf-8")

    def _animate(self, pose_config: str = None, output: str = None,
                 fmt: str = "svg") -> dict:
        src = Path(pose_config) if pose_config else POSE_SYSTEM
        if not src.exists():
            return {"error": f"Pose config not found: {src}"}

        try:
            config = json.loads(src.read_text(encoding="utf-8"))
        except Exception as e:
            return {"error": f"Failed to parse config: {e}"}

        result_meta = {"config_path": str(src)}
        warnings = self._validate_config(config)
        if warnings:
            result_meta["warnings"] = warnings
            for w in warnings:
                if w.startswith("Missing"):
                    return {"error": w, "result": result_meta}

        cache_key = self._get_cache_key(config)
        cached = self._cache_get(cache_key, fmt)
        if cached:
            if output:
                Path(output).write_text(cached, encoding="utf-8")
            return {
                "result": {
                    **result_meta,
                    "path": output or str(src.with_suffix(f".{fmt}")),
                    "size": len(cached),
                    "cached": True,
                    "format": fmt,
                    "characters": list(config.get("characters", {}).keys()),
                    "duration": config.get("animation", {}).get("duration", 0),
                    "keyframes": len(config.get("animation", {}).get("keyframes", [])),
                }
            }

        import sys as _sys
        _sys.path.insert(0, str(ANIM_DIR.parent.parent))
        from tools.animation.gen_svg_animation import generate

        svg = generate(config)

        if fmt == "svg":
            content = svg
        elif fmt == "html":
            content = f"""<!DOCTYPE html><html><body style="margin:0">{svg}</body></html>"""
        elif fmt == "png":
            try:
                import cairosvg
                png_bytes = cairosvg.svg2png(bytestring=svg.encode())
                png_dst = Path(output) if output else src.with_suffix(".png")
                png_dst.write_bytes(png_bytes)
                self._cache_put(cache_key, "svg", svg)
                return {
                    "result": {
                        **result_meta,
                        "path": str(png_dst),
                        "size": len(png_bytes),
                        "format": "png",
                        "characters": list(config.get("characters", {}).keys()),
                        "duration": config.get("animation", {}).get("duration", 0),
                        "keyframes": len(config.get("animation", {}).get("keyframes", [])),
                    }
                }
            except ImportError:
                return {"error": "cairosvg required for PNG output: pip install cairosvg"}
        else:
            content = svg

        dst = Path(output) if output else src.with_suffix(f".{fmt}")
        dst.write_text(content, encoding="utf-8")
        self._cache_put(cache_key, "svg", svg)

        return {
            "result": {
                **result_meta,
                "path": str(dst),
                "size": len(content),
                "format": fmt,
                "characters": list(config.get("characters", {}).keys()),
                "duration": config.get("animation", {}).get("duration", 0),
                "keyframes": len(config.get("animation", {}).get("keyframes", [])),
            }
        }
