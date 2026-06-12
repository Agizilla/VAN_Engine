import signal
import threading
from typing import Any, Optional


class TimeoutError(Exception):
    pass


class SandboxExecutor:
    def __init__(self, timeout: float = 10.0):
        self.timeout = timeout

    def run(self, fn, *args, **kwargs) -> Any:
        result = []
        error = []

        def worker():
            try:
                res = fn(*args, **kwargs)
                result.append(res)
            except Exception as e:
                error.append(e)

        thread = threading.Thread(target=worker, daemon=True)
        thread.start()
        thread.join(timeout=self.timeout)

        if thread.is_alive():
            raise TimeoutError(f"Execution timed out after {self.timeout}s")

        if error:
            raise error[0]

        return result[0]
