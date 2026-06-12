#!/usr/bin/env python3
import sys, io, json, asyncio, time, re
from pathlib import Path
from typing import Optional, Dict, Any, Tuple
from enum import Enum

if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

class InferenceTier(Enum):
    FAST = "fast"
    STANDARD = "standard"
    SMART = "smart"

class InferenceResult:
    def __init__(self, success: bool, output: str, tier: str,
                 latency_ms: float, error: str = None,
                 parsed: Any = None, from_cache: bool = False):
        self.success = success
        self.output = output
        self.tier = tier
        self.latency_ms = latency_ms
        self.error = error
        self.parsed = parsed
        self.from_cache = from_cache

    def to_dict(self) -> dict:
        return {
            "success": self.success,
            "output": self.output,
            "tier": self.tier,
            "latency_ms": self.latency_ms,
            "error": self.error,
            "parsed": self.parsed,
            "from_cache": self.from_cache
        }

class InferenceBridge:
    TIMEOUTS = {
        InferenceTier.FAST: 15000,
        InferenceTier.STANDARD: 30000,
        InferenceTier.SMART: 90000
    }

    def __init__(self, engine_root: Path):
        self.engine_root = Path(engine_root)
        self._cache = {}
        self._brain = None

    def _get_brain(self):
        if self._brain is None:
            try:
                sys.path.insert(0, str(self.engine_root))
                from VAN.brain import VANEngineBrain
                self._brain = VANEngineBrain.Instance()
            except ImportError:
                self._brain = None
        return self._brain

    async def run(self, system_prompt: str, user_prompt: str,
                  tier: InferenceTier = InferenceTier.STANDARD,
                  expect_json: bool = False) -> InferenceResult:
        start_time = time.time()
        cache_key = f"{system_prompt}:{user_prompt}:{tier.value}"

        if tier == InferenceTier.FAST and cache_key in self._cache:
            return InferenceResult(
                success=True, output=self._cache[cache_key],
                tier=tier.value, latency_ms=(time.time() - start_time) * 1000,
                from_cache=True
            )

        try:
            result = await asyncio.wait_for(
                self._execute_inference(system_prompt, user_prompt, tier, expect_json),
                timeout=self.TIMEOUTS[tier] / 1000
            )
            if tier == InferenceTier.FAST and result.success:
                self._cache[cache_key] = result.output
            return result
        except asyncio.TimeoutError:
            return InferenceResult(
                success=False, output="", tier=tier.value,
                latency_ms=(time.time() - start_time) * 1000,
                error=f"Timeout after {self.TIMEOUTS[tier]}ms"
            )
        except Exception as e:
            return InferenceResult(
                success=False, output="", tier=tier.value,
                latency_ms=(time.time() - start_time) * 1000, error=str(e)
            )

    async def _execute_inference(self, system_prompt: str, user_prompt: str,
                                  tier: InferenceTier, expect_json: bool) -> InferenceResult:
        if tier == InferenceTier.FAST:
            return await self._fast_inference(user_prompt, expect_json)
        elif tier == InferenceTier.SMART:
            return await self._smart_inference(user_prompt, expect_json)
        else:
            return await self._standard_inference(user_prompt, expect_json)

    async def _fast_inference(self, user_prompt: str, expect_json: bool) -> InferenceResult:
        query_lower = user_prompt.lower()
        if "status" in query_lower or "health" in query_lower:
            brain = self._get_brain()
            if brain:
                stats = brain.GetStats()
                output = f"VAN_Engine online. Tokens: {stats.TokenCount}. Uptime: {stats.Uptime:.1f}s"
            else:
                output = "VAN_Engine: Fallback mode (brain not loaded)"
            return InferenceResult(True, output, "fast", 0)
        if "help" in query_lower:
            help_text = """Available commands:\n- status / health: System status\n- help: This message\n- lookup <token>: Find token\n- algorithm: Run 7-phase Algorithm"""
            return InferenceResult(True, help_text, "fast", 0)
        lookup_match = re.search(r'lookup\s+(\w+)', query_lower)
        if lookup_match:
            token = lookup_match.group(1)
            brain = self._get_brain()
            if brain:
                quat = brain.LookupToken(token)
                if quat:
                    return InferenceResult(True, f"Token '{token}': {quat}", "fast", 0)
                return InferenceResult(True, f"Token '{token}' not found", "fast", 0)
        return InferenceResult(True, f"Fast inference: {user_prompt[:100]}...", "fast", 0)

    async def _standard_inference(self, user_prompt: str, expect_json: bool) -> InferenceResult:
        brain = self._get_brain()
        if not brain:
            return InferenceResult(False, "", "standard", 0, "Brain not available")
        result = brain.ExecuteQuery(user_prompt)
        return InferenceResult(True, result.Message, "standard", 0)

    async def _smart_inference(self, user_prompt: str, expect_json: bool) -> InferenceResult:
        brain = self._get_brain()
        if not brain:
            return InferenceResult(False, "", "smart", 0, "Brain not available")
        result = await brain.ExecuteAlgorithmQuery(user_prompt)
        output = f"Algorithm execution complete.\nEffort: {result.EffortTier}\n{result.Message}"
        return InferenceResult(True, output, "smart", 0, parsed={
            "action": result.Action, "phase": result.AlgorithmPhase,
            "effort": result.EffortTier, "isc_checked": result.ISCChecked,
            "isc_total": result.ISCTotal
        })

_bridge = None

def get_bridge(engine_root: Path = None) -> InferenceBridge:
    global _bridge
    if _bridge is None:
        if engine_root is None:
            engine_root = Path(__file__).parent.parent.parent
        _bridge = InferenceBridge(engine_root)
    return _bridge

async def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--tier", choices=["fast", "standard", "smart"], default="standard")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("prompt", nargs="*")
    args = parser.parse_args()
    if not args.prompt:
        print("Usage: inference_bridge.py --tier fast 'your prompt'")
        sys.exit(1)
    prompt = " ".join(args.prompt)
    bridge = get_bridge()
    tier = InferenceTier(args.tier)
    result = await bridge.run("", prompt, tier, args.json)
    if args.json:
        print(json.dumps(result.to_dict()))
    else:
        print(result.output)

if __name__ == "__main__":
    asyncio.run(main())
