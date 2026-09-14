"""UDP and socket stream provider broadcasting OpenLore scene telemetry to Unreal Engine Live Link."""

from __future__ import annotations

import socket
import threading
import time
from typing import Any, Dict, List, Optional

from openlore.bridge.unreal.protocol import (
    LiveLinkFrameData,
    LiveLinkPacket,
    LiveLinkStaticData,
    LiveLinkSubjectType,
)
from openlore.exceptions import LiveLinkBridgeError


class LiveLinkStreamProvider:
    """High-speed UDP streamer transmitting Live Link packets to Unreal Engine 5."""

    def __init__(
        self,
        host: str = "127.0.0.1",
        port: int = 11111,
        multicast: bool = False,
    ) -> None:
        self.host = host
        self.port = port
        self.multicast = multicast
        self._socket: Optional[socket.socket] = None
        self._subjects_static: Dict[str, LiveLinkStaticData] = {}
        self._subjects_frame: Dict[str, LiveLinkFrameData] = {}

        self._running: bool = False
        self._thread: Optional[threading.Thread] = None
        self._lock = threading.Lock()

        # Telemetry metrics
        self._packets_sent: int = 0
        self._bytes_sent: int = 0
        self._last_broadcast_time: float = 0.0

    @property
    def is_running(self) -> bool:
        """Return True if background broadcast thread is active."""
        return self._running

    @property
    def active_subjects(self) -> List[str]:
        """Return list of currently registered subject names."""
        with self._lock:
            return list(self._subjects_static.keys())

    @property
    def metrics(self) -> Dict[str, Any]:
        """Return live telemetry metrics."""
        with self._lock:
            return {
                "host": self.host,
                "port": self.port,
                "is_running": self._running,
                "active_subjects_count": len(self._subjects_static),
                "packets_sent": self._packets_sent,
                "bytes_sent": self._bytes_sent,
                "last_broadcast_time": self._last_broadcast_time,
            }

    def _ensure_socket(self) -> socket.socket:
        """Create or return existing UDP socket."""
        with self._lock:
            if self._socket is None:
                sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                if self.multicast:
                    sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, 2)
                else:
                    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                    sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
                self._socket = sock
            return self._socket

    def register_subject(
        self,
        static_data: LiveLinkStaticData,
        initial_frame: Optional[LiveLinkFrameData] = None,
    ) -> None:
        """Register a new subject for streaming."""
        with self._lock:
            self._subjects_static[static_data.subject_name] = static_data
            if initial_frame is not None:
                self._subjects_frame[static_data.subject_name] = initial_frame
            elif static_data.subject_name not in self._subjects_frame:
                self._subjects_frame[static_data.subject_name] = LiveLinkFrameData(
                    subject_name=static_data.subject_name,
                    subject_type=static_data.subject_type,
                )

    def update_frame(self, frame: LiveLinkFrameData) -> None:
        """Update the latest frame snapshot for a subject."""
        with self._lock:
            self._subjects_frame[frame.subject_name] = frame
            if frame.subject_name not in self._subjects_static:
                # Auto-register static data if missing
                self._subjects_static[frame.subject_name] = LiveLinkStaticData(
                    subject_name=frame.subject_name,
                    subject_type=frame.subject_type,
                )

    def send_packet(self, payload: bytes) -> int:
        """Send raw bytes over the UDP socket to target endpoint."""
        sock = self._ensure_socket()
        try:
            bytes_written = sock.sendto(payload, (self.host, self.port))
            with self._lock:
                self._packets_sent += 1
                self._bytes_sent += bytes_written
                self._last_broadcast_time = time.time()
            return bytes_written
        except Exception as exc:
            raise LiveLinkBridgeError(f"Failed to send Live Link UDP packet: {exc}") from exc

    def broadcast_static(self, subject_name: str, wire_format: str = "json") -> int:
        """Send static schema packet for specified subject."""
        with self._lock:
            static_data = self._subjects_static.get(subject_name)
        if not static_data:
            raise LiveLinkBridgeError(f"Subject '{subject_name}' is not registered.")

        payload = LiveLinkPacket.encode_json(static_data)
        return self.send_packet(payload)

    def broadcast_frame(self, subject_name: str, wire_format: str = "json") -> int:
        """Send current frame snapshot for specified subject."""
        with self._lock:
            frame_data = self._subjects_frame.get(subject_name)
        if not frame_data:
            raise LiveLinkBridgeError(f"No frame data available for '{subject_name}'.")

        if wire_format.lower() == "binary":
            payload = LiveLinkPacket.encode_binary(frame_data)
        else:
            payload = LiveLinkPacket.encode_json(frame_data)
        return self.send_packet(payload)

    def start_stream(self, target_fps: float = 60.0, wire_format: str = "json") -> None:
        """Start asynchronous streaming loop broadcasting all registered subjects at target frame rate."""
        if self._running:
            return

        self._running = True
        interval = 1.0 / max(target_fps, 1.0)

        def _loop() -> None:
            # Broadcast initial static data for all subjects
            with self._lock:
                names = list(self._subjects_static.keys())
            for name in names:
                try:
                    self.broadcast_static(name, wire_format="json")
                except Exception:
                    pass

            frame_counter = 0
            while self._running:
                start_tick = time.perf_counter()
                with self._lock:
                    subjects = list(self._subjects_frame.keys())

                frame_counter += 1
                for sub_name in subjects:
                    try:
                        # Advance frame count and timestamp
                        with self._lock:
                            if sub_name in self._subjects_frame:
                                f = self._subjects_frame[sub_name]
                                f.frame_number = frame_counter
                                f.timestamp = time.time()
                        self.broadcast_frame(sub_name, wire_format=wire_format)
                    except Exception:
                        pass

                # Periodically re-send static data every 120 frames (keep-alive schema for late-joining UE5 instances)
                if frame_counter % 120 == 0:
                    for name in subjects:
                        try:
                            self.broadcast_static(name, wire_format="json")
                        except Exception:
                            pass

                elapsed = time.perf_counter() - start_tick
                sleep_time = interval - elapsed
                if sleep_time > 0:
                    time.sleep(sleep_time)

        self._thread = threading.Thread(target=_loop, name="OpenLoreLiveLinkStreamer", daemon=True)
        self._thread.start()

    def stop_stream(self) -> None:
        """Stop background streaming thread and close UDP socket."""
        self._running = False
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=1.0)
            self._thread = None
        self.close()

    def close(self) -> None:
        """Close underlying socket and release networking resources."""
        with self._lock:
            if self._socket:
                try:
                    self._socket.close()
                except Exception:
                    pass
                self._socket = None
