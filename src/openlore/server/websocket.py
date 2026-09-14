"""Standard-library RFC 6455 WebSocket protocol implementation and live event broker."""

from __future__ import annotations

import base64
import hashlib
import json
import socket
import struct
import threading
from typing import Any, Dict, List, Optional, Set, Tuple

WS_GUID = "258EAFA5-E914-47DA-95CA-C5AB0DC85B11"

# Opcodes
OPCODE_CONTINUATION = 0x0
OPCODE_TEXT = 0x1
OPCODE_BINARY = 0x2
OPCODE_CLOSE = 0x8
OPCODE_PING = 0x9
OPCODE_PONG = 0xA


def compute_accept_key(sec_ws_key: str) -> str:
    """Compute the Sec-WebSocket-Accept token according to RFC 6455 Section 4.2.2."""
    combined = sec_ws_key.strip() + WS_GUID
    sha1_hash = hashlib.sha1(combined.encode("utf-8")).digest()
    return base64.b64encode(sha1_hash).decode("utf-8")


def encode_frame(payload: bytes, opcode: int = OPCODE_TEXT) -> bytes:
    """Encode an unmasked server-to-client WebSocket frame."""
    length = len(payload)
    header = bytearray()
    # FIN bit set (0x80) + opcode
    header.append(0x80 | (opcode & 0x0F))

    # Mask bit is 0 for server-to-client frames
    if length <= 125:
        header.append(length)
    elif length <= 65535:
        header.append(126)
        header.extend(struct.pack("!H", length))
    else:
        header.append(127)
        header.extend(struct.pack("!Q", length))

    return bytes(header) + payload


def decode_client_frame(data: bytes) -> Tuple[int, bytes, int]:
    """Decode a masked client-to-server WebSocket frame.
    
    Returns: (opcode, unmasked_payload, total_bytes_consumed)
    """
    if len(data) < 2:
        return -1, b"", 0

    first_byte = data[0]
    second_byte = data[1]

    opcode = first_byte & 0x0F
    is_masked = (second_byte & 0x80) != 0
    payload_len = second_byte & 0x7F

    offset = 2
    if payload_len == 126:
        if len(data) < 4:
            return -1, b"", 0
        payload_len = struct.unpack("!H", data[2:4])[0]
        offset = 4
    elif payload_len == 127:
        if len(data) < 10:
            return -1, b"", 0
        payload_len = struct.unpack("!Q", data[2:10])[0]
        offset = 10

    masking_key = b""
    if is_masked:
        if len(data) < offset + 4:
            return -1, b"", 0
        masking_key = data[offset : offset + 4]
        offset += 4

    total_len = offset + payload_len
    if len(data) < total_len:
        return -1, b"", 0

    raw_payload = data[offset:total_len]
    if is_masked:
        # Unmask via XOR with 4-byte key
        unmasked = bytearray(payload_len)
        for i in range(payload_len):
            unmasked[i] = raw_payload[i] ^ masking_key[i % 4]
        payload = bytes(unmasked)
    else:
        payload = raw_payload

    return opcode, payload, total_len


class WebSocketClient:
    """Represents a connected browser or DCC WebSocket client."""

    def __init__(self, sock: socket.socket, addr: Tuple[str, int]) -> None:
        self.sock = sock
        self.addr = addr
        self.is_open = True
        self._lock = threading.Lock()

    def send_text(self, text: str) -> bool:
        """Send a UTF-8 text frame to this client."""
        if not self.is_open:
            return False
        frame = encode_frame(text.encode("utf-8"), opcode=OPCODE_TEXT)
        with self._lock:
            try:
                self.sock.sendall(frame)
                return True
            except (OSError, BrokenPipeError):
                self.is_open = False
                return False

    def send_json(self, data: Any) -> bool:
        """Serialize data to JSON and transmit."""
        return self.send_text(json.dumps(data))

    def close(self) -> None:
        """Send close frame and terminate socket."""
        if not self.is_open:
            return
        self.is_open = False
        try:
            close_frame = encode_frame(struct.pack("!H", 1000), opcode=OPCODE_CLOSE)
            self.sock.sendall(close_frame)
        except Exception:
            pass
        try:
            self.sock.close()
        except Exception:
            pass


class WebSocketManager:
    """Thread-safe connection broker broadcasting real-time scene mutations."""

    def __init__(self) -> None:
        self._clients: Set[WebSocketClient] = set()
        self._lock = threading.Lock()

    @property
    def client_count(self) -> int:
        with self._lock:
            return len(self._clients)

    def register(self, client: WebSocketClient) -> None:
        with self._lock:
            self._clients.add(client)

    def unregister(self, client: WebSocketClient) -> None:
        with self._lock:
            self._clients.discard(client)
        client.close()

    def broadcast_text(self, text: str) -> int:
        """Broadcast text message to all active clients. Cleans dead sockets."""
        with self._lock:
            active = list(self._clients)

        dead: List[WebSocketClient] = []
        sent_count = 0
        for c in active:
            if c.send_text(text):
                sent_count += 1
            else:
                dead.append(c)

        if dead:
            with self._lock:
                for d in dead:
                    self._clients.discard(d)
        return sent_count

    def broadcast_json(self, data: Any) -> int:
        """Broadcast JSON payload to all active clients."""
        return self.broadcast_text(json.dumps(data))


# Global singleton instance
ws_manager = WebSocketManager()
