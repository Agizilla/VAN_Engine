"""
LARA — Boot Sequence Patch for Connectome
Version: 0.1.1 | Build: 002 | Date: 2026-02-23

Add these lines to lara.py boot() function to wire in the ConnectomeManager.
The patch replaces the PersonaManager and VoiceManager with their v2 variants.

HOW TO APPLY:
  In lara.py, replace:
    from lara_core.persona import PersonaManager
    from lara_core.voice import VoiceManager
  With:
    from lara_core.connectome import ConnectomeManager
    from lara_core.persona_v2 import PersonaManager
    from lara_core.voice_v2 import VoiceManager

  Then add ConnectomeManager init between cache and persona:
    connectome = ConnectomeManager(data_dir, config, logger)
    personas = PersonaManager(data_dir, config, connectome, logger)
    voice    = VoiceManager(data_dir, config, connectome, logger)

  Also update the CommandRouter call to pass connectome_mgr:
    router = CommandRouter(
        ...existing args...,
        connectome_mgr=connectome,
    )

  And update the CommandRouter __init__ signature to:
    def __init__(self, ..., connectome_mgr=None, ...):
        self.connectome_mgr = connectome_mgr

This file documents the exact changes needed — the actual edits
are in the UPGRADE CHECKLIST in CONNECTOME_GUIDE.md.
"""

# This is a documentation/patch-guide file, not executable.
# See CONNECTOME_GUIDE.md for step-by-step upgrade instructions.

BOOT_PATCH_IMPORTS = """
# ── Connectome (add after existing imports in lara.py) ───────
from lara_core.connectome import ConnectomeManager
from lara_core.persona_v2 import PersonaManager    # replaces persona.py
from lara_core.voice_v2 import VoiceManager        # replaces voice.py
"""

BOOT_PATCH_INIT = """
# ── Add in boot() after cache init, before personas ──────────
connectome = ConnectomeManager(data_dir, config, logger)

# ── Replace original PersonaManager / VoiceManager calls ─────
personas = PersonaManager(data_dir, config, connectome, logger)
voice    = VoiceManager(data_dir, config, connectome, logger)
"""

BOOT_PATCH_RETURN = """
# ── Add to the return dict in boot() ─────────────────────────
return {
    ...
    "connectome": connectome,    # <-- add this line
    ...
}
"""

ROUTER_PATCH = """
# ── Update CommandRouter init in run_cli() and run_tui() ─────
router = CommandRouter(
    data_dir=c["data_dir"],
    config=c["config"],
    cache=c["cache"],
    persona_mgr=c["personas"],
    voice_mgr=c["voice"],
    face_mgr=c["face"],
    skills_mgr=c["skills"],
    online_ctrl=c["online"],
    llm=c["llm"],
    context_buf=c["ctx"],
    connectome_mgr=c.get("connectome"),    # <-- add this
    logger=c["logger"],
)
"""
