from __future__ import annotations

import socket
import sys
from pathlib import Path

import uvicorn


def discover_lan_ip() -> str:
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        # UDP connect does not send application data; it asks the OS which interface it would use.
        sock.connect(("192.0.2.1", 80))
        return sock.getsockname()[0]
    except OSError:
        return "<computer-lan-ip>"
    finally:
        sock.close()


if __name__ == "__main__":
    print("\nGPUFlow Local Lab | prototype 0.1.0")
    print("Desktop: http://127.0.0.1:8765")
    print(f"Phones on the same Wi-Fi: http://{discover_lan_ip()}:8765")
    print("Do not expose this test server to the public internet.")
    print("Press CTRL+C to stop.\n")
    uvicorn.run("app.main:app", host="0.0.0.0", port=8765, log_level="info")
