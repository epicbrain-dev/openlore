"""Unit tests for standard-library RFC 6455 WebSocket implementation."""

from __future__ import annotations

import struct
import unittest

from openlore.server.websocket import (
    OPCODE_CLOSE,
    OPCODE_PING,
    OPCODE_TEXT,
    WebSocketClient,
    WebSocketManager,
    compute_accept_key,
    decode_client_frame,
    encode_frame,
)


class MockSocket:
    """In-memory mock socket recording sent payloads."""

    def __init__(self) -> None:
        self.sent_bytes = bytearray()
        self.is_closed = False

    def sendall(self, data: bytes) -> None:
        if self.is_closed:
            raise BrokenPipeError("Socket is closed")
        self.sent_bytes.extend(data)

    def close(self) -> None:
        self.is_closed = True


class TestWebSocketProtocol(unittest.TestCase):
    def test_rfc6455_accept_key_test_vector(self) -> None:
        # RFC 6455 Section 4.2.2 standard test vector
        client_key = "dGhlIHNhbXBsZSBub25jZQ=="
        expected_accept = "s3pPLMBiTxaQ9kYGzzhZRbK+xOo="
        self.assertEqual(compute_accept_key(client_key), expected_accept)

    def test_encode_frame_small_payload(self) -> None:
        payload = b"Hello, OpenLore!"
        frame = encode_frame(payload, opcode=OPCODE_TEXT)

        # First byte: 0x81 (FIN=1, Opcode=1)
        self.assertEqual(frame[0], 0x81)
        # Second byte: payload length (unmasked, so bit 7 is 0)
        self.assertEqual(frame[1], len(payload))
        # Content
        self.assertEqual(frame[2:], payload)

    def test_encode_frame_medium_payload(self) -> None:
        # Payload between 126 and 65535 bytes
        payload = b"X" * 1000
        frame = encode_frame(payload, opcode=OPCODE_TEXT)

        self.assertEqual(frame[0], 0x81)
        self.assertEqual(frame[1], 126)
        length_field = struct.unpack("!H", frame[2:4])[0]
        self.assertEqual(length_field, 1000)
        self.assertEqual(frame[4:], payload)

    def test_decode_masked_client_frame(self) -> None:
        # Build masked client frame: "Hello"
        # Masking key: 4 bytes (0x37, 0xfa, 0x21, 0x3d)
        mask = b"\x37\xfa\x21\x3d"
        text = b"Hello"
        masked = bytearray(len(text))
        for i in range(len(text)):
            masked[i] = text[i] ^ mask[i % 4]

        # Header: 0x81 (FIN + Text), 0x85 (Masked + 5 bytes length)
        raw = bytes([0x81, 0x80 | len(text)]) + mask + bytes(masked)

        opcode, unmasked, consumed = decode_client_frame(raw)
        self.assertEqual(opcode, OPCODE_TEXT)
        self.assertEqual(unmasked, text)
        self.assertEqual(consumed, len(raw))

    def test_websocket_manager_broadcast(self) -> None:
        mgr = WebSocketManager()
        sock1 = MockSocket()
        sock2 = MockSocket()
        c1 = WebSocketClient(sock1, ("127.0.0.1", 5001))
        c2 = WebSocketClient(sock2, ("127.0.0.1", 5002))

        mgr.register(c1)
        mgr.register(c2)
        self.assertEqual(mgr.client_count, 2)

        sent = mgr.broadcast_json({"type": "CAM_SYNC", "pos": [1, 2, 3]})
        self.assertEqual(sent, 2)
        self.assertGreater(len(sock1.sent_bytes), 0)
        self.assertGreater(len(sock2.sent_bytes), 0)

        # Disconnect c1
        mgr.unregister(c1)
        self.assertEqual(mgr.client_count, 1)


if __name__ == "__main__":
    unittest.main()
