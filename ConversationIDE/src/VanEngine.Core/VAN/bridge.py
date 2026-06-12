"""
Bridge module for importing VAN_Engine brain without relative import issues
"""

import sys
import os
from pathlib import Path

# Add parent directory to path for absolute imports
sys.path.insert(0, str(Path(__file__).parent))

# Try absolute imports
try:
    from engine import VanEngine
    from brain import VANEngineBrain
    from audit import AuditLog
    from memory import MemoryStore
    from state import VanStateEngine
    from runtime import CortexRuntime
    from security import RighteousnessFilter
    
    __all__ = [
        'VanEngine',
        'VANEngineBrain', 
        'AuditLog',
        'MemoryStore',
        'VanStateEngine',
        'CortexRuntime',
        'RighteousnessFilter'
    ]
    
    print("[Bridge] Successfully imported VAN_Engine modules")
    
except ImportError as e:
    print(f"[Bridge] Import error: {e}")
    
    # Create mock classes as fallback
    class MockBrain:
        _instance = None
        
        @classmethod
        def Instance(cls):
            if cls._instance is None:
                cls._instance = cls()
            return cls._instance
        
        def ExecuteQuery(self, query):
            class Result:
                def __init__(self, msg):
                    self.Message = msg
                    self.Success = True
                    self.Action = "EXECUTE"
            return Result(f"Mock response: {query}")
        
        def GetStats(self):
            class Stats:
                def __init__(self):
                    self.TokenCount = 0
                    self.AuditEventCount = 0
                    self.Uptime = 0
                    self.ActiveISO = [f"ISO_{i:03d}" for i in range(1, 21)]
            return Stats()
        
        def SelfTest(self):
            class TestResult:
                def __init__(self):
                    self.IsValid = True
                    self.Diagnostics = "Mock mode - OK"
            return TestResult()
        
        def GetAuditTrail(self, count):
            return []
    
    VANEngineBrain = MockBrain
    
    class MockEngine:
        class Metrics:
            def __init__(self):
                self.envelopes = 0
        
        def __init__(self):
            self.Metrics = self.Metrics()
    
    VanEngine = MockEngine
    
    print("[Bridge] Using mock implementations")