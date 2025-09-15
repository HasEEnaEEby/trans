import os
from typing import Optional

try:
    import clamd  # type: ignore
except Exception:  # pragma: no cover
    clamd = None  # type: ignore


class AvScanner:
    def __init__(self) -> None:
        self.enabled = os.getenv("AV_SCAN_ENABLED", "false").lower() == "true"
        self.client: Optional["clamd.ClamdNetworkSocket"] = None
        if self.enabled and clamd is not None:
            host = os.getenv("CLAMAV_HOST", "localhost")
            port = int(os.getenv("CLAMAV_PORT", "3310"))
            try:
                self.client = clamd.ClamdNetworkSocket(host=host, port=port)
                self.client.ping()
            except Exception:
                self.client = None
                self.enabled = False

    def scan_bytes(self, data: bytes) -> None:
        if not self.enabled or self.client is None:
            return
        res = self.client.instream(data)  # type: ignore
        if isinstance(res, dict):
            status = next(iter(res.values()))
            if isinstance(status, tuple) and status[0] == 'FOUND':
                raise ValueError("Malware detected")


scanner = AvScanner()
