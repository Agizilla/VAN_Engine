"""
LARA — CommandRouter Connectome Patches
Version: 0.1.1 | Build: 002 | Date: 2026-02-23

This file contains:
  1. New command handler methods to add to CommandRouter
  2. Patches to existing handlers (speak, create_persona, update_voice)
     that wire in connectome triggers and param passing

HOW TO APPLY:
  Either merge these methods into command_router.py directly,
  OR subclass CommandRouter and override the relevant methods.
  The SubclassRouter approach below is the cleanest option.

New commands added:
  connectome [describe|synthesise|trigger|set-weight|set-modulator]
  rate [positive|negative]
  set emotion [family] [value]
"""

# ─── Import from original router ─────────────────────────────
# In production, replace this with a proper import from lara_core.command_router
# from lara_core.command_router import CommandRouter as _BaseRouter

import re
from datetime import datetime
from pathlib import Path
from typing import Optional


class ConnectomeCommandMixin:
    """
    Mixin class — add these methods into CommandRouter to add
    all connectome-related command handling.
    Assumes self.personas, self.voice, self.connectome_mgr are available.
    """

    def _handle_connectome_cmd(self, raw: str) -> str:
        """
        Handle: connectome [subcommand] [args...]

        Subcommands:
          describe [persona_id]            → full human-readable neural state
          synthesise [persona_id]          → run graph, print key params
          trigger [persona_id] [event]     → manually fire a plasticity trigger
          set-weight [persona_id] [node_id] [value]
          set-modulator [persona_id] [family] [value]
          add-node [persona_id] [type] [weight]
          list                             → list all personas with connectomes
        """
        if not hasattr(self, 'connectome_mgr') or self.connectome_mgr is None:
            return "Connectome not enabled. Set connectome.enabled: true in config.yaml"

        parts = raw.strip().split()
        # parts[0] = "connectome", parts[1] = subcommand
        if len(parts) < 2:
            return self._connectome_help()

        sub = parts[1].lower()
        active_persona = self.cache.get("active_persona")

        if sub == "describe":
            pid = parts[2] if len(parts) > 2 else active_persona
            if not pid:
                return "No active persona. Specify: connectome describe [persona_id]"
            return self.connectome_mgr.describe(pid)

        elif sub in ("synthesise", "synthesize"):
            pid = parts[2] if len(parts) > 2 else active_persona
            if not pid:
                return "No active persona."
            result = self.connectome_mgr.synthesise(pid)
            if result is None:
                return f"No connectome for '{pid}'"
            # Format key params
            lines = [f"Synthesised connectome — {pid}"]
            for node_type, params in result.items():
                if node_type == "_meta":
                    continue
                if isinstance(params, dict):
                    param_str = ", ".join(f"{k}={v:.3f}" if isinstance(v, float)
                                          else f"{k}={v}"
                                          for k, v in params.items())
                    lines.append(f"  {node_type:<22} {param_str}")
            meta = result.get("_meta", {})
            lines.append(f"\n  Nodes: {meta.get('node_count')} | "
                         f"Edges: {meta.get('edge_count')} | "
                         f"At: {meta.get('synthesised_at','?')[:19]}")
            return "\n".join(lines)

        elif sub == "trigger":
            pid   = parts[2] if len(parts) > 2 else active_persona
            event = parts[3] if len(parts) > 3 else "chat_interaction"
            if not pid:
                return "No active persona."
            adaptations = self.connectome_mgr.trigger(pid, event, logger=self.logger)
            if not adaptations:
                return f"Trigger '{event}' fired for {pid} — no weight changes (conditions not met)"
            lines = [f"Trigger '{event}' → {len(adaptations)} adaptation(s) for {pid}:"]
            for a in adaptations:
                lines.append(
                    f"  {a['mobject_id']:<30} "
                    f"{a['old_weight']:.4f} → {a['new_weight']:.4f} "
                    f"(Δ{a['delta']:+.4f}) via rule {a['rule_id']}"
                )
            return "\n".join(lines)

        elif sub == "set-weight":
            if len(parts) < 5:
                return "Usage: connectome set-weight [persona_id] [node_id] [value]"
            pid, node_id, val = parts[2], parts[3], float(parts[4])
            ok = self.connectome_mgr.set_node_weight(pid, node_id, val)
            return (f"Node '{node_id}' weight set to {val:.3f} for {pid}"
                    if ok else f"Failed — check persona and node IDs")

        elif sub == "set-modulator":
            if len(parts) < 5:
                return "Usage: connectome set-modulator [persona_id] [family] [value]"
            pid, family, val = parts[2], parts[3], float(parts[4])
            ok = self.connectome_mgr.set_global_weight(pid, family, val)
            return (f"Global modulator '{family}' set to {val:.3f} for {pid}"
                    if ok else f"Failed — family must be one of: voice/emotion/rhythm/speech/prosody_family")

        elif sub == "list":
            personas = self.connectome_mgr.list_personas()
            if not personas:
                return "No connectomes on disk yet."
            return "Personas with connectomes:\n" + "\n".join(f"  - {p}" for p in personas)

        elif sub == "help":
            return self._connectome_help()

        else:
            return f"Unknown connectome subcommand '{sub}'. {self._connectome_help()}"

    def _connectome_help(self) -> str:
        return """Connectome Commands:
  connectome describe [persona_id]               Neural state summary
  connectome synthesise [persona_id]             Run graph → effective params
  connectome trigger [persona_id] [event]        Fire plasticity trigger
  connectome set-weight [pid] [node_id] [0-1]    Override node weight
  connectome set-modulator [pid] [family] [0-1]  Set global neuromodulator
  connectome list                                 List all personas with connectomes

Events: audio_training | user_rating_positive | user_rating_negative |
        new_lyrics | chat_interaction | media_ingestion | daily_decay

Families: voice_family | emotion_family | rhythm_family |
          speech_family | prosody_family"""

    def _handle_rate(self, raw: str) -> str:
        """
        Handle: rate [positive|negative|thumbsup|thumbsdown|good|bad]
        Fires user_rating plasticity trigger on the active persona's connectome.
        """
        low = raw.lower()
        positive = any(w in low for w in ("positive", "thumbsup", "good", "up", "yes", "great", "like"))
        negative = any(w in low for w in ("negative", "thumbsdown", "bad", "down", "no", "hate", "dislike"))

        if not positive and not negative:
            return "Please say 'rate positive' or 'rate negative' to give feedback."

        pid = self.cache.get("active_persona")
        if not pid:
            return "No active persona to rate."

        if not hasattr(self, 'connectome_mgr') or self.connectome_mgr is None:
            return "Connectome not enabled."

        adaptations = self.personas.apply_rating(pid, positive=positive)
        sentiment = "👍 Positive" if positive else "👎 Negative"
        if not adaptations:
            return f"{sentiment} rating noted for {pid}. (No weight changes triggered this time.)"

        changed = [f"{a['mobject_id'].split('_')[-1]}: {a['old_weight']:.3f}→{a['new_weight']:.3f}"
                   for a in adaptations]
        return (f"{sentiment} rating applied to {pid}.\n"
                f"  Connectome adapted: {', '.join(changed)}")

    def _handle_set_emotion(self, raw: str) -> str:
        """
        Handle: set emotion [valence|arousal|dominance] [value]
        Directly modulates a global emotion family weight.
        """
        pid = self.cache.get("active_persona")
        if not pid:
            return "No active persona."

        m = re.search(r"set\s+emotion\s+(\w+)\s+([\d.+-]+)", raw, re.IGNORECASE)
        if not m:
            return "Usage: set emotion [valence|arousal|dominance] [0.0–1.0]"

        dimension = m.group(1).lower()
        try:
            value = float(m.group(2))
        except ValueError:
            return "Value must be a number between 0.0 and 1.0"

        # Map dimension to node ID suffix
        dim_map = {"valence": "ev", "arousal": "ea", "dominance": "ed"}
        suffix = dim_map.get(dimension)
        if not suffix:
            return f"Unknown emotion dimension '{dimension}'. Use: valence, arousal, or dominance"

        node_id = f"{pid}_{suffix}"
        if not hasattr(self, 'connectome_mgr') or self.connectome_mgr is None:
            return "Connectome not enabled."

        ok = self.connectome_mgr.set_node_weight(pid, node_id, value)
        if ok:
            self.connectome_mgr.save(self.connectome_mgr.load(pid))
            return (f"Emotion {dimension} set to {value:.3f} for {pid}.\n"
                    f"  Node '{node_id}' updated. Next TTS will reflect new emotional state.")
        return f"Failed to set {dimension} — node '{node_id}' not found in connectome."

    # ── Patched versions of original handlers ────────────────

    def _handle_sing_connectome(self, raw: str) -> str:
        """
        Enhanced _handle_sing that:
        1. Reads connectome emotion state to colour the lyrics prompt
        2. Passes persona_id to voice.speak() for connectome param application
        3. Fires new_lyrics plasticity trigger after generation
        """
        pid = self.cache.get("active_persona")

        # Get emotional colour from connectome
        emotion_hint = ""
        if pid and hasattr(self, 'connectome_mgr') and self.connectome_mgr:
            try:
                emotion = self.connectome_mgr.get_emotion_state(pid)
                v, a = emotion.get("valence", 0), emotion.get("arousal", 0.5)
                tone = ("joyful" if v > 0.3 else "melancholic" if v < -0.2 else "neutral")
                energy = ("high-energy" if a > 0.65 else "calm" if a < 0.35 else "moderate")
                emotion_hint = f" The tone should be {tone} and {energy}."
            except Exception:
                pass

        topic_m = re.search(r"about\s+(.+?)(?:\s+and\s+produce|$)", raw, re.IGNORECASE)
        topic = topic_m.group(1).strip() if topic_m else "life and progress"

        lyrics_prompt = (
            f"Write original song lyrics about: {topic}.{emotion_hint}\n"
            "Format: 2 verses and a chorus. Keep it under 16 lines. "
            "No section labels. Just the lyrics."
        )
        lyrics = self.llm.generate(lyrics_prompt, max_tokens=300)

        lyrics_dir = self.data_dir / "lyrics_samples"
        lyrics_dir.mkdir(exist_ok=True)
        next_num = len(list(lyrics_dir.glob("*.txt"))) + 1
        lyrics_file = lyrics_dir / f"{next_num}.txt"
        lyrics_file.write_text(lyrics)

        # Speak with connectome voice params
        voice_model = self.cache.get("active_voice_model")
        self.voice.speak(lyrics, voice_model_id=voice_model, persona_id=pid)

        # Fire new_lyrics plasticity
        if pid and hasattr(self, 'connectome_mgr') and self.connectome_mgr:
            self.personas.notify_lyrics(pid, topic=topic)

        if self.logger:
            self.logger.info(f"Song performed | topic={topic} | saved={lyrics_file} | persona={pid}")

        return (f"Song performed and saved to {lyrics_file}\n"
                f"  Emotional colouring: {emotion_hint.strip() or 'default'}\n\n"
                f"Lyrics:\n{lyrics}")

    def _handle_create_persona_connectome(self, raw: str) -> str:
        """
        Enhanced _handle_create_persona that accepts persona base params
        from the command for connectome initialisation.

        Extended syntax:
          Create a persona named Vivian [pitch 200] [valence 0.7] [formal 0.8]
          using frame 7 from vid2.mp4 as face and recording as voice
        """
        id_m = re.search(r"persona\s+(\w+)", raw, re.IGNORECASE)
        name_m = re.search(r"named\s+([A-Za-z][A-Za-z\s]+?)(?:\s+using|\s+with|\s+pitch|\s+valence|$)",
                            raw, re.IGNORECASE)
        frame_m = re.search(r"frame\s+(\d+)\s+from\s+([^\s]+)", raw, re.IGNORECASE)

        persona_id = (id_m.group(1).lower() if id_m
                      else "persona_" + datetime.now().strftime("%H%M%S"))
        persona_name = (name_m.group(1).strip() if name_m else persona_id.capitalize())

        # Parse optional connectome seed params
        base_params = {}
        pitch_m   = re.search(r"pitch\s+([\d.]+)", raw, re.IGNORECASE)
        valence_m = re.search(r"valence\s+([\d.+-]+)", raw, re.IGNORECASE)
        formal_m  = re.search(r"formal\w*\s+([\d.]+)", raw, re.IGNORECASE)
        tempo_m   = re.search(r"tempo\s+([\d.]+)", raw, re.IGNORECASE)
        if pitch_m:   base_params["pitch_hz"]          = float(pitch_m.group(1))
        if valence_m: base_params["valence"]            = float(valence_m.group(1))
        if formal_m:  base_params["formality"]          = float(formal_m.group(1))
        if tempo_m:   base_params["tempo"]              = float(tempo_m.group(1))

        face_model_id = None
        if frame_m:
            frame_num = int(frame_m.group(1))
            video_name = frame_m.group(2)
            video_candidates = list(self.data_dir.rglob(f"*{video_name}*"))
            if video_candidates:
                frame_path = self.face.extract_frame(video_candidates[0], frame_num)
                if frame_path:
                    face_model_id = f"face_{persona_id}"
                    self.face.register_model(face_model_id, frame_path,
                                             description=f"Frame {frame_num} from {video_name}")

        voice_model_id = self.cache.get("active_voice_model")
        persona = self.personas.create(
            persona_id, persona_name,
            voice_model=voice_model_id,
            face_model=face_model_id,
            description=f"Created: {raw[:80]}",
            base_connectome_params=base_params,
        )
        self.cache.set("active_persona", persona_id)
        self.cache.checkpoint()

        from lara_core.status import write_status, write_readme
        write_status(self.data_dir, self.cache, self.config)
        write_readme(self.data_dir, self.config)

        # Notify media ingestion
        if face_model_id:
            self.personas.notify_media(persona_id, "face_frame")

        # Show connectome summary
        connectome_info = ""
        if hasattr(self, 'connectome_mgr') and self.connectome_mgr:
            connectome_info = f"\n\n{self.connectome_mgr.describe(persona_id)}"

        return (
            f"Persona '{persona_name}' created (id={persona_id})\n"
            f"  Face model  : {face_model_id or 'none'}\n"
            f"  Voice model : {voice_model_id or 'none'}\n"
            f"  Connectome  : {'initialised' if hasattr(self,'connectome_mgr') and self.connectome_mgr else 'disabled'}\n"
            f"  Seed params : {base_params or 'defaults'}"
            f"{connectome_info}"
        )
