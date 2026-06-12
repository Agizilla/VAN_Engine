import subprocess
import json
import logging
import time
import os
from pathlib import Path
from typing import Optional, Dict
import threading

logger = logging.getLogger(__name__)

MAX_RETRIES = 3
RETRY_DELAYS = [5, 15, 30]
HEARTBEAT_FILE = ".daz_heartbeat"
HEARTBEAT_TIMEOUT = 90


class DAZOrchestrator:
    def __init__(self, config: dict):
        self.daz_path = config.get("daz_studio_path", "")
        self.workspace_dir = Path(config.get("workspace_dir", "./workspace"))
        self.output_dir = Path(config.get("output_dir", "./workspace/output"))
        self.timeout = config.get("timeout_seconds", 300)
        self.max_retries = config.get("max_retries", MAX_RETRIES)
        self.process = None
        self._heartbeat_path = self.workspace_dir / HEARTBEAT_FILE
        self._lock_files = [
            self.workspace_dir / "daz_studio.lock",
            Path(os.environ.get("TEMP", ".")) / "daz_studio.lock",
        ]

    def _cleanup_stale_locks(self):
        for lf in self._lock_files:
            if lf.exists():
                try:
                    age = time.time() - lf.stat().st_mtime
                    if age > 300:
                        lf.unlink()
                        logger.warning(f"Removed stale lock file: {lf}")
                except OSError:
                    pass

    def _write_heartbeat(self):
        try:
            self._heartbeat_path.parent.mkdir(parents=True, exist_ok=True)
            data = {"timestamp": time.time(), "pid": os.getpid()}
            self._heartbeat_path.write_text(json.dumps(data))
        except OSError:
            pass

    def _heartbeat_loop(self, stop_event: threading.Event):
        while not stop_event.is_set():
            self._write_heartbeat()
            stop_event.wait(15)

    def _monitor_heartbeat(self, stop_event: threading.Event) -> threading.Thread:
        t = threading.Thread(target=self._heartbeat_loop, args=(stop_event,), daemon=True)
        t.start()
        return t

    def validate_daz_installation(self) -> bool:
        path = Path(self.daz_path)
        if path.exists() and path.is_file():
            logger.info(f"DAZ Studio found at: {self.daz_path}")
            return True

        alternatives = [
            "C:\\Program Files\\DAZ 3D\\DAZStudio4\\dazstudio.exe",
            "C:\\Program Files (x86)\\DAZ 3D\\DAZStudio4\\dazstudio.exe",
            "C:\\Program Files\\DAZ 3D\\DAZStudio4.20\\dazstudio.exe",
            "C:\\Program Files\\DAZ 3D\\DAZStudio4.22\\dazstudio.exe",
        ]

        for alt in alternatives:
            if Path(alt).exists():
                self.daz_path = alt
                logger.info(f"DAZ Studio found at alternative path: {alt}")
                return True

        logger.error("DAZ Studio not found")
        return False

    def find_daz_script_path(self) -> Optional[Path]:
        possible_paths = [
            Path.cwd() / "daz_bridge.dsa",
            Path(__file__).parent.parent / "daz_bridge.dsa",
            self.workspace_dir / "daz_bridge.dsa",
        ]

        for path in possible_paths:
            if path.exists():
                return path.absolute()

        logger.error("daz_bridge.dsa not found")
        return None

    def prepare_workspace(self) -> bool:
        try:
            self.workspace_dir.mkdir(parents=True, exist_ok=True)
            self.output_dir.mkdir(parents=True, exist_ok=True)
            self._cleanup_stale_locks()
            logger.info(f"Workspace ready: {self.workspace_dir}")
            return True
        except Exception as e:
            logger.error(f"Cannot create workspace: {e}")
            return False

    def launch_daz_studio(self, script_path: Path) -> subprocess.Popen:
        cmd = [
            self.daz_path,
            "-noPrompt",
            "-script", str(script_path),
        ]

        logger.info(f"Launching DAZ Studio: {' '.join(cmd)}")

        env = os.environ.copy()
        env["DAZ_WORKSPACE"] = str(self.workspace_dir.absolute())
        env["DAZ_OUTPUT_DIR"] = str(self.output_dir.absolute())

        try:
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                env=env,
                text=True,
                creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0,
            )
            return process
        except Exception as e:
            logger.error(f"Failed to launch DAZ Studio: {e}")
            raise

    def monitor_process(self, process: subprocess.Popen) -> Dict:
        start_time = time.time()
        stdout_lines = []
        stderr_lines = []

        def read_stream(stream, lines_list):
            for line in iter(stream.readline, ""):
                if line:
                    lines_list.append(line.strip())
                    logger.info(f"[DAZ] {line.strip()}")
            stream.close()

        stdout_thread = threading.Thread(target=read_stream, args=(process.stdout, stdout_lines))
        stderr_thread = threading.Thread(target=read_stream, args=(process.stderr, stderr_lines))
        stdout_thread.start()
        stderr_thread.start()

        heartbeat_stop = threading.Event()
        heartbeat_thread = self._monitor_heartbeat(heartbeat_stop)

        last_heartbeat = time.time()
        heartbeat_warned = False

        try:
            while True:
                try:
                    exit_code = process.wait(timeout=10)
                    elapsed = time.time() - start_time
                    heartbeat_stop.set()
                    heartbeat_thread.join(timeout=5)
                    stdout_thread.join(timeout=5)
                    stderr_thread.join(timeout=5)

                    result = {
                        "success": exit_code == 0,
                        "exit_code": exit_code,
                        "elapsed_seconds": elapsed,
                        "stdout": "\n".join(stdout_lines),
                        "stderr": "\n".join(stderr_lines),
                    }

                    logger.info(
                        f"DAZ Studio completed: exit_code={exit_code}, elapsed={elapsed:.1f}s"
                    )
                    return result

                except subprocess.TimeoutExpired:
                    elapsed = time.time() - start_time
                    if elapsed >= self.timeout:
                        process.kill()
                        heartbeat_stop.set()
                        logger.error(f"DAZ Studio timed out after {self.timeout} seconds")
                        return {
                            "success": False,
                            "exit_code": -1,
                            "elapsed_seconds": self.timeout,
                            "stdout": "\n".join(stdout_lines),
                            "stderr": "Process timeout",
                        }

                    if self._heartbeat_path.exists():
                        try:
                            hb = json.loads(self._heartbeat_path.read_text())
                            last_heartbeat = hb.get("timestamp", last_heartbeat)
                            heartbeat_warned = False
                        except (json.JSONDecodeError, OSError):
                            pass

                    stalled = time.time() - last_heartbeat
                    if stalled > HEARTBEAT_TIMEOUT and not heartbeat_warned:
                        logger.warning(
                            f"No heartbeat from DAZ for {stalled:.0f}s "
                            f"(timeout in {self.timeout - elapsed:.0f}s)"
                        )
                        heartbeat_warned = True

        except Exception as e:
            heartbeat_stop.set()
            logger.error(f"Process monitoring error: {e}")
            return {"success": False, "exit_code": -1, "error": str(e)}

    def run_automation(self) -> Dict:
        if not self.validate_daz_installation():
            return {"success": False, "error": "DAZ Studio not found"}

        if not self.prepare_workspace():
            return {"success": False, "error": "Workspace preparation failed"}

        script_path = self.find_daz_script_path()
        if script_path is None:
            return {"success": False, "error": "daz_bridge.dsa not found"}

        last_error = None
        for attempt in range(1, self.max_retries + 1):
            logger.info(f"DAZ launch attempt {attempt}/{self.max_retries}")

            try:
                process = self.launch_daz_studio(script_path)
                self.process = process
                result = self.monitor_process(process)
                self.process = None

                if result.get("success"):
                    return result

                last_error = result

                if attempt < self.max_retries:
                    delay = RETRY_DELAYS[min(attempt - 1, len(RETRY_DELAYS) - 1)]
                    logger.warning(
                        f"DAZ attempt {attempt} failed (exit={result.get('exit_code')}), "
                        f"retrying in {delay}s..."
                    )
                    time.sleep(delay)

            except Exception as e:
                last_error = {"success": False, "error": str(e), "exit_code": -1}
                if attempt < self.max_retries:
                    delay = RETRY_DELAYS[min(attempt - 1, len(RETRY_DELAYS) - 1)]
                    logger.warning(f"DAZ attempt {attempt} threw: {e}, retrying in {delay}s...")
                    time.sleep(delay)

        logger.error("All DAZ launch attempts failed")
        if isinstance(last_error, dict):
            return last_error
        return {"success": False, "error": str(last_error), "exit_code": -1}
