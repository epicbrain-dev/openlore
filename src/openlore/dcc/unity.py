"""Unity 6 Live Link and OpenUSD C# Package Scaffolder for OpenLore."""

from __future__ import annotations

import json
from pathlib import Path


class UnityBridgeScaffolder:
    """Generates the official Unity 6 (UPM Package) Live Link Bridge for OpenLore."""

    @staticmethod
    def get_client_cs_source() -> str:
        return '''// OpenLore Unity 6 Live Link Client
// Copyright (c) 2026 OpenLore Project. All Rights Reserved.

using System;
using System.Collections.Concurrent;
using System.Net;
using System.Net.Sockets;
using System.Text;
using System.Threading;
using UnityEngine;

namespace OpenLore.LiveLink
{
    [Serializable]
    public class TransformData
    {
        public float[] translation;
        public float[] rotation;
        public float[] scale;
    }

    [Serializable]
    public class CameraOpticsData
    {
        public float field_of_view = 39.6f;
        public float focal_length = 50.0f;
        public float aperture = 2.8f;
        public float focus_distance = 1000.0f;
    }

    [Serializable]
    public class LiveLinkFramePacket
    {
        public int version = 1;
        public string type = "FrameData";
        public string subject_name = "Camera_StageA";
        public string role = "Camera";
        public double timestamp;
        public TransformData transform;
        public CameraOpticsData camera_frame_data;
    }

    [ExecuteInEditMode]
    public class OpenLoreLiveLinkClient : MonoBehaviour
    {
        [Header("Network Configuration")]
        [Tooltip("UDP Port to listen for OpenLore Live Link datagrams")]
        public int listenPort = 11111;

        [Tooltip("Expected Subject Name to filter and drive this GameObject")]
        public string targetSubjectName = "Camera_StageA";

        [Header("Optics & Target")]
        [Tooltip("Optional Camera component to apply real-time focal length and FOV to")]
        public Camera targetCamera;

        [Header("Live Telemetry Readout")]
        [SerializeField] private bool isReceiving = false;
        [SerializeField] private int receivedPackets = 0;
        [SerializeField] private string lastSubjectReceived = "";

        private UdpClient _udpClient;
        private Thread _receiveThread;
        private volatile bool _isRunning = false;
        private readonly ConcurrentQueue<LiveLinkFramePacket> _packetQueue = new ConcurrentQueue<LiveLinkFramePacket>();

        public bool IsReceiving => isReceiving;
        public int PacketCount => receivedPackets;

        private void OnEnable()
        {
            if (targetCamera == null)
            {
                targetCamera = GetComponent<Camera>();
            }
            StartReceiver();
        }

        private void OnDisable()
        {
            StopReceiver();
        }

        public void StartReceiver()
        {
            if (_isRunning) return;

            try
            {
                _udpClient = new UdpClient(listenPort);
                _isRunning = true;
                _receiveThread = new Thread(ReceiveLoop)
                {
                    IsBackground = true,
                    Name = "OpenLore_UDP_Receiver"
                };
                _receiveThread.Start();
                Debug.Log($"[OpenLore] Unity Live Link Client listening on UDP port {listenPort}");
            }
            catch (Exception ex)
            {
                Debug.LogError($"[OpenLore] Failed to bind UDP port {listenPort}: {ex.Message}");
            }
        }

        public void StopReceiver()
        {
            _isRunning = false;
            if (_udpClient != null)
            {
                try { _udpClient.Close(); } catch { }
                _udpClient = null;
            }

            if (_receiveThread != null && _receiveThread.IsAlive)
            {
                _receiveThread.Join(200);
                _receiveThread = null;
            }
            isReceiving = false;
            Debug.Log("[OpenLore] Unity Live Link Client stopped.");
        }

        private void ReceiveLoop()
        {
            IPEndPoint remoteEndPoint = new IPEndPoint(IPAddress.Any, 0);

            while (_isRunning)
            {
                try
                {
                    byte[] data = _udpClient.Receive(ref remoteEndPoint);
                    if (data != null && data.Length > 0)
                    {
                        string jsonStr = Encoding.UTF8.GetString(data);
                        LiveLinkFramePacket packet = JsonUtility.FromJson<LiveLinkFramePacket>(jsonStr);
                        if (packet != null)
                        {
                            _packetQueue.Enqueue(packet);
                        }
                    }
                }
                catch (SocketException)
                {
                    // Socket closed on stop
                    break;
                }
                catch (Exception ex)
                {
                    if (_isRunning)
                    {
                        Debug.LogWarning($"[OpenLore] UDP Receive Warning: {ex.Message}");
                    }
                }
            }
        }

        private void Update()
        {
            // Drain queue and apply latest frame
            LiveLinkFramePacket latest = null;
            while (_packetQueue.TryDequeue(out LiveLinkFramePacket pkt))
            {
                if (string.IsNullOrEmpty(targetSubjectName) || pkt.subject_name == targetSubjectName)
                {
                    latest = pkt;
                    receivedPackets++;
                }
            }

            if (latest != null)
            {
                ApplyPacketToTransform(latest);
                isReceiving = true;
                lastSubjectReceived = latest.subject_name;
            }
        }

        private void ApplyPacketToTransform(LiveLinkFramePacket pkt)
        {
            if (pkt.transform != null && pkt.transform.translation != null && pkt.transform.translation.Length >= 3)
            {
                // Coordinate conversion: OpenLore/Maya/Houdini Left-Handed cm to Unity Left-Handed meters
                float x = pkt.transform.translation[0] * 0.01f;
                float y = pkt.transform.translation[1] * 0.01f;
                float z = pkt.transform.translation[2] * 0.01f;

                transform.position = new Vector3(x, y, z);
            }

            if (pkt.transform != null && pkt.transform.rotation != null && pkt.transform.rotation.Length >= 4)
            {
                float qx = pkt.transform.rotation[0];
                float qy = pkt.transform.rotation[1];
                float qz = pkt.transform.rotation[2];
                float qw = pkt.transform.rotation[3];

                if (Mathf.Abs(qx) > 0.0001f || Mathf.Abs(qy) > 0.0001f || Mathf.Abs(qz) > 0.0001f || Mathf.Abs(qw) > 0.0001f)
                {
                    transform.rotation = new Quaternion(qx, qy, qz, qw);
                }
            }

            // Apply camera optics if camera attached
            if (targetCamera != null && pkt.camera_frame_data != null)
            {
                if (pkt.camera_frame_data.field_of_view > 1.0f)
                {
                    targetCamera.fieldOfView = pkt.camera_frame_data.field_of_view;
                }
                if (targetCamera.usePhysicalProperties && pkt.camera_frame_data.focal_length > 1.0f)
                {
                    targetCamera.focalLength = pkt.camera_frame_data.focal_length;
                }
            }
        }
    }
}
'''

    @staticmethod
    def get_package_json() -> str:
        manifest = {
            "name": "com.openlore.livelink",
            "version": "1.0.0",
            "displayName": "OpenLore Live Link Bridge",
            "description": "Real-time 60 FPS camera tracking and transform streaming client for OpenLore virtual production.",
            "unity": "2023.2",
            "author": {
                "name": "OpenLore Project",
                "email": "engineering@openlore.io",
                "url": "https://openlore.io"
            },
            "keywords": [
                "openlore",
                "livelink",
                "virtual-production",
                "openusd",
                "camera-tracking"
            ]
        }
        return json.dumps(manifest, indent=2)

    @classmethod
    def export(cls, output_dir: Path) -> Path:
        """Export Unity package files to target directory."""
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        client_file = output_dir / "OpenLoreLiveLinkClient.cs"
        client_file.write_text(cls.get_client_cs_source(), encoding="utf-8")

        pkg_json = output_dir / "package.json"
        pkg_json.write_text(cls.get_package_json(), encoding="utf-8")

        return client_file
