from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional

from .audit import AuditLog, AuditSeverity
from .enums import VanBlockType
from .envelope import VanEnvelope
from .lexer import VanLexer
from .parser import AstEnvelope, VanParser
from .security import RighteousnessFilter


class VanContext:
    def __init__(self):
        self.State: Dict[str, Any] = {}
        self.Envelope: Optional[AstEnvelope] = None

    def Get(self, key: str, default=None):
        return self.State.get(key, default)

    def Set(self, key: str, value: Any) -> None:
        self.State[key] = value

    def Contains(self, key: str) -> bool:
        return key in self.State

    def Clear(self) -> None:
        self.State.clear()

    @property
    def Count(self) -> int:
        return len(self.State)


class VanFunctionRegistry:
    def __init__(self):
        self._map: Dict[str, Dict[str, Callable[[VanContext, AstEnvelope], Any]]] = {}
        self._register_core_functions()

    def Register(
        self,
        carrier: str,
        modulation: str,
        executor: Callable[[VanContext, AstEnvelope], Any],
    ) -> None:
        if carrier not in self._map:
            self._map[carrier] = {}
        self._map[carrier][modulation] = executor

    def TryGetExecutor(
        self, envelope: AstEnvelope
    ) -> Optional[Callable[[VanContext, AstEnvelope], Any]]:
        mod_map = self._map.get(envelope.Carrier)
        if mod_map is None:
            return None
        return mod_map.get(envelope.Modulation)

    async def TryExecute(self, envelope: VanEnvelope, state: Dict[str, Any]) -> tuple[bool, Any]:
        ast_env = AstEnvelope(
            Carrier=envelope.Carrier,
            Modulation=envelope.Modulation,
            QFactor=envelope.QFactor,
            Dither=envelope.Dither,
            Data=list(envelope.Data),
            DataTypes=list(envelope.DataTypes),
        )
        executor = self.TryGetExecutor(ast_env)
        if executor is None:
            return False, None
        ctx = VanContext()
        ctx.State = state
        ctx.Envelope = ast_env
        try:
            coro = executor(ctx, ast_env)
            result = await coro
            return True, result
        except Exception:
            return False, None

    def _register_core_functions(self) -> None:
        async def _soft_knee(ctx: VanContext, env: AstEnvelope) -> Dict[str, Any]:
            return {"result": "Expanded"}

        async def _modbus_write(ctx: VanContext, env: AstEnvelope) -> Dict[str, bool]:
            return {"written": True}

        async def _gecko_shift(ctx: VanContext, env: AstEnvelope) -> Dict[str, bool]:
            return {"shifted": True}

        async def _master_audio(ctx: VanContext, env: AstEnvelope) -> Dict[str, Any]:
            return {"skill": "AudioSkill", "status": "registered", "methods": 107}

        async def _master_image(ctx: VanContext, env: AstEnvelope) -> Dict[str, Any]:
            return {"skill": "ImageSkill", "status": "registered", "methods": 52}

        async def _master_video(ctx: VanContext, env: AstEnvelope) -> Dict[str, Any]:
            return {"skill": "VideoSkill", "status": "registered", "methods": 60}

        self.Register("VanEngine", "Soft-Knee-Expander", _soft_knee)
        self.Register("SCADA", "ModbusWrite", _modbus_write)
        self.Register("Audio", "GeckoShift", _gecko_shift)
        self.Register("Audio", "MasterAudio", _master_audio)
        self.Register("Image", "MasterImage", _master_image)
        self.Register("Video", "MasterVideo", _master_video)


class CortexRuntime:
    def __init__(
        self,
        filter_obj: Optional[RighteousnessFilter] = None,
        audit: Optional[AuditLog] = None,
    ):
        self._registry = VanFunctionRegistry()
        self._context = VanContext()
        audit_path = os.path.join(os.getcwd(), "audit.log")
        self._audit = audit or AuditLog(audit_path)
        self._filter = filter_obj or RighteousnessFilter(self._audit)
        self._folk_mother_mode = True

    @property
    def Context(self) -> VanContext:
        return self._context

    @property
    def Registry(self) -> VanFunctionRegistry:
        return self._registry

    @property
    def Filter(self) -> RighteousnessFilter:
        return self._filter

    @property
    def Audit(self) -> AuditLog:
        return self._audit

    @property
    def FolkMotherMode(self) -> bool:
        return self._folk_mother_mode

    @FolkMotherMode.setter
    def FolkMotherMode(self, value: bool) -> None:
        self._folk_mother_mode = value

    async def ExecuteFileAsync(self, path: str) -> None:
        text = await self._read_file_async(path)
        envelopes = self._parse_text(text)
        for env in envelopes:
            await self.ExecuteEnvelopeAsync(env)

    async def ExecuteStringAsync(self, van_text: str) -> Any:
        envelopes = self._parse_text(van_text)
        last_result: Any = None
        for env in envelopes:
            last_result = await self.ExecuteEnvelopeAsync(env)
        return last_result if last_result is not None else {"result": "empty"}

    async def ExecuteEnvelopeAsync(self, envelope: AstEnvelope) -> Any:
        self._context.Envelope = envelope

        if self._folk_mother_mode and not self._filter.IsRighteous(envelope):
            self._audit.Record(
                "FolkMother",
                f"Envelope rejected by FolkMother consent: {envelope.Header}",
                AuditSeverity.Critical,
            )
            return {"rejected": True, "reason": "RighteousnessFilter blocked envelope"}

        if envelope.BlockType == VanBlockType.State and len(envelope.Data) >= 2:
            key = str(envelope.Data[0] or "")
            value = str(envelope.Data[1] or "")
            try:
                self._context.Set(key, float(value))
            except ValueError:
                low = value.lower()
                if low in ("true", "false"):
                    self._context.Set(key, low == "true")
                else:
                    self._context.Set(key, value)

        executor = self._registry.TryGetExecutor(envelope)
        if executor is not None:
            self._audit.RecordEnvelope(envelope.Carrier, envelope.Modulation, "executed")
            return await executor(self._context, envelope)

        self._audit.RecordEnvelope(envelope.Carrier, envelope.Modulation, "fallback")
        return await self._fallback_executor(envelope)

    def _parse_text(self, text: str) -> List[AstEnvelope]:
        parser = VanParser(text)
        return parser.Parse()

    async def _fallback_executor(self, envelope: AstEnvelope) -> Dict[str, Any]:
        return {
            "carrier": envelope.Carrier,
            "modulation": envelope.Modulation,
            "data": envelope.Data,
            "state_count": self._context.Count,
            "q_factor": envelope.QFactor,
            "block_type": envelope.BlockType.value,
        }

    async def _read_file_async(self, path: str) -> str:
        import asyncio
        loop = asyncio.get_running_loop()

        def _read():
            with open(path, "r", encoding="utf-8") as f:
                return f.read()

        return await loop.run_in_executor(None, _read)

    def Dispose(self) -> None:
        self._audit.Dispose()
        self._context.Clear()
