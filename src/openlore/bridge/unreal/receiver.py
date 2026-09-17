"""UDP socket receiver ingesting Live Link telemetry from Unreal Engine 5."""

from __future__ import annotations

import os
import socket
import threading
import time
from typing import Any, Callable, Dict, List, Optional

from openlore.bridge.unreal.protocol import (
    MAGIC_BINARY_HEADER,
    LiveLinkFrameData,
    LiveLinkPacket,
    LiveLinkStaticData,
)
from openlore.exceptions import LiveLinkBridgeError


class LiveLinkStreamReceiver:
    """Listens for inbound Live Link UDP packets originating from Unreal Engine 5 or camera rigs."""

    def __init__(
        self,
        bind_host: Optional[str] = None,
        port: int = 11112,
        buffer_size: int = 65535,
    ) -> None:
        self.bind_host = bind_host or os.getenv("OPENLORE_LIVELINK_HOST", "127.0.0.1")
        self.port = port
        self.buffer_size = buffer_size

        self._socket: Optional[socket.socket] = None
        self._running: bool = False
        self._thread: Optional[threading.Thread] = None
        self._lock = threading.Lock()

        self._frame_callbacks: List[Callable[[LiveLinkFrameData], None]] = []
        self._static_callbacks: List[Callable[[LiveLinkStaticData], None]] = []

        # Telemetry metrics
        self._packets_received: int = 0
        self._bytes_received: int = 0
        self._last_received_time: float = 0.0
        self._last_frame: Optional[LiveLinkFrameData] = None

    @property
    def is_running(self) -> bool:
        """Return True if background listener is active."""
        return self._running

    @property
    def metrics(self) -> Dict[str, Any]:
        """Return inbound telemetry metrics."""
        with self._lock:
            return {
                "bind_host": self.bind_host,
                "port": self.port,
                "is_running": self._running,
                "packets_received": self._packets_received,
                "bytes_received": self._bytes_received,
                "last_received_time": self._last_received_time,
                "last_frame_subject": self._last_frame.subject_name if self._last_frame else None,
            }

    def on_frame(self, callback: Callable[[LiveLinkFrameData], None]) -> None:
        """Register a callback for decoded frame data."""
        with self._lock:
            self._frame_callbacks.append(callback)

    def on_static(self, callback: Callable[[LiveLinkStaticData], None]) -> None:
        """Register a callback for decoded static schema data."""
        with self._lock:
            self._static_callbacks.append(callback)

    def start(self) -> None:
        """Bind socket and begin asynchronous listening loop."""
        if self._running:
            return

        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            sock.bind((self.bind_host, self.port))
            sock.settimeout(0.5)
        except Exception as exc:
            sock.close()
            raise LiveLinkBridgeError(f"Failed to bind Live Link receiver to {self.bind_host}:{self.port}: {exc}") from exc

        self._socket = sock
        self._running = True

        def _listen() -> None:
            while self._running:
                try:
                    data, _addr = sock.recvfrom(self.buffer_size)
                except socket.timeout:
                    continue
                except OSError:
                    break

                with self._lock:
                    self._packets_received += 1
                    self._bytes_received += len(data)
                    self._last_received_time = time.time()

                self._dispatch_packet(data)

        self._thread = threading.Thread(target=_listen, name="OpenLoreLiveLinkReceiver", daemon=True)
        self._thread.start()

    def _dispatch_packet(self, payload: bytes) -> None:
        """Parse raw payload and invoke callbacks."""
        try:
            if payload.startswith(MAGIC_BINARY_HEADER):
                frame = LiveLinkPacket.decode_binary(payload)
                with self._lock:
                    self._last_frame = frame
                    callbacks = list(self._frame_callbacks)
                for cb in callbacks:
                    try:
                        cb(frame)
                    except Exception:
                        pass
            else:
                decoded = LiveLinkPacket.decode_json(payload)
                if isinstance(decoded, LiveLinkFrameData):
                    with self._lock:
                        self._last_frame = decoded
                        callbacks = list(self._frame_callbacks)
                    for cb in callbacks:
                        try:
                            cb(decoded)
                        except Exception:
                            pass
                elif isinstance(decoded, LiveLinkStaticData):
                    with self._lock:
                        callbacks_s = list(self._static_callbacks)
                    for cb in callbacks_s:
                        try:
                            cb(decoded)
                        except Exception:
                            pass
        except Exception:
            pass

    def stop(self) -> None:
        """Stop background receiver thread and close socket."""
        self._running = False
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=1.0)
            self._thread = None

        if self._socket:
            try:
                self._socket.close()
            except Exception:
                pass
            self._socket = None
