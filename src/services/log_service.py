import os
import glob
from typing import Optional
from src.config import Config

class LogService:
    def __init__(self, config: Config):
        self.config = config

    def get_logs(self, lines: int = 50, filename: str = "ora_all.log") -> str:
        """
        Retrieves the last N lines from the specified log file.
        Uses config.log_dir to locate the file.
        """
        # Ensure log_dir exists (or at least try to use it)
        log_path = os.path.join(self.config.log_dir, filename)
        
        if not os.path.exists(log_path):
            return f"Log file not found at: {log_path}"

        try:
            # Simple tail implementation
            with open(log_path, "r", encoding="utf-8", errors="replace") as f:
                # Reading all lines might be heavy for huge logs, but for <100MB it's usually instant.
                # Improvements: seek from end. For now, simple readlines is safer for variable encoding.
                content = f.read().splitlines()
                tail = content[-lines:]
                return "\n".join(tail)
        except Exception as e:
            return f"Error reading logs: {e}"

    def list_log_files(self) -> list[str]:
        """List available log files in the directory."""
        if not os.path.exists(self.config.log_dir):
            return []
        files = glob.glob(os.path.join(self.config.log_dir, "*.log"))
        return [os.path.basename(f) for f in files]
