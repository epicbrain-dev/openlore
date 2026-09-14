#!/usr/bin/env python3
"""
stream_live_camera.py
Transmits smooth 60 FPS camera orbit telemetry over UDP to OpenLore (127.0.0.1:11111).
Open http://localhost:8000 to watch the 3D Viewport and HUD Telemetry Bar update in real time.
"""

import json
import math
import socket
import sys
import time

def stream_camera(duration_seconds=60, host="127.0.0.1", port=11111, fps=60):
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    print("=" * 66)
    print("🎥 OpenLore Real-Time Live Link Streamer")
    print(f"📡 Broadcasting to {host}:{port} at {fps} FPS")
    print("🌐 Open http://localhost:8000 in your browser to watch live!")
    print("=" * 66)
    print("Streaming... Press Ctrl+C to stop.\n")

    interval = 1.0 / fps
    start_time = time.time()
    frame_idx = 0

    try:
        while True:
            elapsed = time.time() - start_time
            if duration_seconds and elapsed >= duration_seconds:
                break

            angle = elapsed * 0.8
            radius = 350.0
            x = math.cos(angle) * radius
            z = math.sin(angle) * radius
            y = 120.0 + math.sin(elapsed * 1.5) * 30.0

            yaw_deg = math.degrees(math.atan2(-x, -z))
            pitch_deg = -12.0

            p = math.radians(pitch_deg) * 0.5
            y_r = math.radians(yaw_deg) * 0.5
            r = 0.0

            qx = math.sin(p) * math.cos(y_r) * math.cos(r) - math.cos(p) * math.sin(y_r) * math.sin(r)
            qy = math.cos(p) * math.sin(y_r) * math.cos(r) + math.sin(p) * math.cos(y_r) * math.sin(r)
            qz = math.cos(p) * math.cos(y_r) * math.sin(r) - math.sin(p) * math.sin(y_r) * math.cos(r)
            qw = math.cos(p) * math.cos(y_r) * math.cos(r) + math.sin(p) * math.sin(y_r) * math.sin(r)

            fov = 38.0 + math.sin(elapsed * 0.5) * 6.0
            focal_length = 50.0 + math.cos(elapsed * 0.5) * 15.0

            payload = {
                "version": 1,
                "type": "LIVELINK_FRAME",
                "subject": "Steadicam_RigA",
                "role": "Camera",
                "translation": [round(x, 2), round(y, 2), round(z, 2)],
                "rotation": [round(qx, 4), round(qy, 4), round(qz, 4), round(qw, 4)],
                "camera": {
                    "focal_length": round(focal_length, 1),
                    "field_of_view": round(fov, 1),
                    "aperture": 2.8,
                },
                "timestamp": time.time(),
            }

            sock.sendto(json.dumps(payload).encode("utf-8"), (host, port))
            frame_idx += 1

            if frame_idx % 30 == 0:
                print(
                    f"\r  [Frame {frame_idx:05d} | {elapsed:4.1f}s] "
                    f"X={x:6.1f} Y={y:5.1f} Z={z:6.1f} | FOV={fov:4.1f}° | FL={focal_length:4.1f}mm",
                    end="",
                    flush=True,
                )

            time.sleep(interval)

    except KeyboardInterrupt:
        print("\n\nStream interrupted by user.")
    finally:
        sock.close()
        print(f"\n\n✅ Finished. Transmitted {frame_idx} telemetry frames.")

if __name__ == "__main__":
    dur = float(sys.argv[1]) if len(sys.argv) > 1 else 60.0
    stream_camera(duration_seconds=dur)
