"""Generate animated SVG from pose_system.json keyframes.

Usage:
    python gen_svg_animation.py pose_system.json [output.svg]

Takes a JSON pose config and generates an SVG with SMIL animations.
Uses opacity-switching between keyframe poses (proven technique).
"""
import json, sys
from pathlib import Path

NS = "http://www.w3.org/2000/svg"

PART_ATTRS = {
    "head":   ["head_cx","head_cy","head_r"],
    "torso":  ["torso_x1","torso_y1","torso_x2","torso_y2"],
    "left_arm":  ["left_arm_x1","left_arm_y1","left_arm_x2","left_arm_y2"],
    "right_arm": ["right_arm_x1","right_arm_y1","right_arm_x2","right_arm_y2"],
    "left_leg":  ["left_leg_x1","left_leg_y1","left_leg_x2","left_leg_y2"],
    "right_leg": ["right_leg_x1","right_leg_y1","right_leg_x2","right_leg_y2"],
}

BREAST_ATTRS = {
    "left_breast":  ["breast_left_cx","breast_left_cy","breast_left_r"],
    "right_breast": ["breast_right_cx","breast_right_cy","breast_right_r"],
    "left_nipple":  ["breast_left_cx","breast_left_cy","nipple_left_r"],
    "right_nipple": ["breast_right_cx","breast_right_cy","nipple_right_r"],
}


def esc(s):
    return str(s).replace("&","&amp;").replace("<","&lt;").replace(">","&gt;").replace('"',"&quot;")


def render_pose_group(pose, col, female, label, dur, kt_on, kt_off):
    """Return SVG group element(s) for one character in one pose, with opacity animate."""
    lines = ['<g>']
    # Opacity: visible between kt_on and kt_off
    lines.append(f'<animate attributeName="opacity" values="0;0;1;1;0;0" '
                 f'keyTimes="0;{kt_on:.3f};{kt_on+0.01:.3f};{kt_off-0.01:.3f};{kt_off:.3f};1" '
                 f'dur="{dur}s" repeatCount="indefinite"/>')

    def v(k): return pose.get(k, 0)

    # Head
    lines.append(f'<circle cx="{v("head_cx")}" cy="{v("head_cy")}" r="{v("head_r")}" '
                 f'fill="none" stroke="{col}" stroke-width="3"/>')

    # Torso
    lines.append(f'<line x1="{v("torso_x1")}" y1="{v("torso_y1")}" '
                 f'x2="{v("torso_x2")}" y2="{v("torso_y2")}" stroke="{col}" stroke-width="3"/>')

    # Arms
    for arm in ["left_arm","right_arm"]:
        a = f"{arm}_x1"; b = f"{arm}_y1"; c = f"{arm}_x2"; d = f"{arm}_y2"
        lines.append(f'<line x1="{v(a)}" y1="{v(b)}" x2="{v(c)}" y2="{v(d)}" '
                     f'stroke="{col}" stroke-width="2.5"/>')

    # Legs
    for leg in ["left_leg","right_leg"]:
        a = f"{leg}_x1"; b = f"{leg}_y1"; c = f"{leg}_x2"; d = f"{leg}_y2"
        lines.append(f'<line x1="{v(a)}" y1="{v(b)}" x2="{v(c)}" y2="{v(d)}" '
                     f'stroke="{col}" stroke-width="2.5"/>')

    # Breasts + nipples (female only)
    if female:
        for side in ["left","right"]:
            cx = v(f"breast_{side}_cx"); cy = v(f"breast_{side}_cy"); r = v(f"breast_{side}_r")
            nr = v(f"nipple_{side}_r")
            lines.append(f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="none" stroke="{col}" stroke-width="2"/>')
            if nr > 0:
                lines.append(f'<circle cx="{cx}" cy="{cy}" r="{nr}" fill="{col}"/>')

    # Label
    lines.append(f'<text x="0" y="25" text-anchor="middle" font-size="11" fill="#777" '
                 f'font-family="sans-serif">{esc(label)}</text>')

    lines.append('</g>')
    return lines


def generate(config: dict) -> str:
    scene = config["scene"]
    chars_cfg = config["characters"]
    poses = config["poses"]
    anim = config["animation"]
    kfs = anim["keyframes"]
    dur = anim["duration"]
    loop = anim["loop"]

    w, h = scene["width"], scene["height"]
    bg = scene["bg"]

    lines = []
    lines.append('<?xml version="1.0" encoding="utf-8"?>')
    lines.append(f'<svg xmlns="{NS}" viewBox="0 0 {w} {h}" width="100%" height="100%">')
    lines.append(f'<rect width="{w}" height="{h}" fill="{bg}" rx="8"/>')
    lines.append(f'<line x1="0" y1="{h-85}" x2="{w}" y2="{h-85}" stroke="#333" stroke-width="2"/>')

    # Draw each character separately
    for cname in sorted(chars_cfg.keys()):
        cfg = chars_cfg[cname]
        col = cfg["color"]
        female = cfg.get("female", False)
        label = cfg.get("label", cname)

        lines.append(f'<!-- {cname} -->')
        lines.append(f'<g>')

        # Position translation: extract (x,y) from each keyframe
        x_vals = []; y_vals = []; kt_list = []
        for i, kf in enumerate(kfs):
            t = kf["t"]
            st = kf["characters"].get(cname)
            if st:
                x_vals.append(f"{st['x']:.1f}")
                y_vals.append(f"{st['y']:.1f}")
            else:
                # Hold last known position
                prev = kfs[i-1]["characters"].get(cname, {"x":0,"y":0})
                x_vals.append(f"{prev['x']:.1f}")
                y_vals.append(f"{prev['y']:.1f}")
            kt_list.append(f"{t/dur:.3f}")

        lines.append(f'<animateTransform attributeName="transform" type="translate" '
                     f'values="{";".join(x_vals)}" keyTimes="{";".join(kt_list)}" '
                     f'dur="{dur}s" repeatCount="indefinite"/>')
        lines.append(f'<animateTransform attributeName="transform" type="translate" '
                     f'values="{";".join(y_vals)}" keyTimes="{";".join(kt_list)}" '
                     f'dur="{dur}s" repeatCount="indefinite" additive="sum"/>')

        # Generate a pose group for each keyframe segment
        for i in range(len(kfs)):
            st = kfs[i]["characters"].get(cname)
            if not st:
                continue
            pose_name = st.get("pose", "standing")
            custom = st.get("custom")
            pose = poses.get(pose_name, poses["standing"])
            if custom:
                pose = dict(pose)
                pose.update(custom)

            kt_start = kfs[i]["t"] / dur
            if i + 1 < len(kfs):
                kt_end = kfs[i + 1]["t"] / dur
            else:
                kt_end = 1.0

            # Determine if this pose group is needed (check if next keyframe has same position+pose)
            next_st = kfs[i+1]["characters"].get(cname) if i+1 < len(kfs) else None
            same_pose = next_st and next_st.get("pose") == pose_name and next_st.get("x") == st["x"] and next_st.get("y") == st["y"]

            # For the transition region, we render this pose from slightly before kt_end to kt_end
            # Using opacity switching between kf pairs
            lines.extend(render_pose_group(pose, col, female, label, dur, kt_start, kt_end))

        lines.append('</g>')

    # Progress bar
    lines.append(f'<g transform="translate({w//2-200},{h-40})">')
    lines.append(f'<rect x="0" y="0" width="400" height="4" rx="2" fill="#333"/>')
    if loop:
        lines.append(f'<rect x="0" y="0" width="0" height="4" rx="2" fill="#666">'
                     f'<animate attributeName="width" values="0;400;0" dur="{dur}s" repeatCount="indefinite"/>'
                     f'</rect>')
    lines.append('</g>')
    lines.append(f'<text x="{w//2}" y="{h-15}" text-anchor="middle" font-size="9" fill="#555" '
                 f'font-family="sans-serif">{dur}s {"loop" if loop else "once"}</text>')
    lines.append('</svg>')
    return "\n".join(lines)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python gen_svg_animation.py pose_system.json [output.svg]")
        sys.exit(1)
    src = Path(sys.argv[1])
    if not src.exists():
        print(f"ERROR: {src} not found")
        sys.exit(1)
    config = json.loads(src.read_text(encoding="utf-8"))
    svg = generate(config)
    dst = Path(sys.argv[2]) if len(sys.argv) > 2 else src.with_suffix(".svg")
    dst.write_text(svg, encoding="utf-8")
    print(f"OK: {dst}  ({len(svg)} bytes)")
