"""Unit tests and cross-language validation for Native C++ DCC Live Link SDK."""

from __future__ import annotations

import os
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

from openlore.bridge.unreal.protocol import (
    CoordinateConverter,
    LiveLinkFrameData,
    LiveLinkPacket,
    LiveLinkSubjectType,
)

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
CPP_HEADER = REPO_ROOT / "include" / "openlore" / "openlore.hpp"


class TestNativeCppSDK(unittest.TestCase):
    """Test suite validating C++ SDK header integrity and cross-language binary interoperability."""

    def test_header_exists_and_contains_definitions(self) -> None:
        self.assertTrue(CPP_HEADER.exists(), "include/openlore/openlore.hpp must exist")
        content = CPP_HEADER.read_text(encoding="utf-8")
        self.assertIn("namespace OpenLore", content)
        self.assertIn("class VectorClock", content)
        self.assertIn("class CASHash", content)
        self.assertIn("struct LiveLinkFrame", content)
        self.assertIn("class UDPBroadcastClient", content)
        self.assertIn("MAGIC_HEADER", content)
        self.assertIn("PROTOCOL_VERSION = 1", content)

    def test_cpp_compilation_and_binary_parity(self) -> None:
        compiler = shutil.which("clang++") or shutil.which("g++")
        if not compiler:
            self.skipTest("C++ compiler (clang++ or g++) not available in current environment")

        with tempfile.TemporaryDirectory() as temp_dir:
            test_src = Path(temp_dir) / "test_runner.cpp"
            test_bin = Path(temp_dir) / "test_runner"

            # Author minimal C++ program exercising OpenLore header
            test_src.write_text(f"""
#include <iostream>
#include <cassert>
#include "{CPP_HEADER}"

int main() {{
    using namespace OpenLore;

    // 1. Vector Clock Test
    VectorClock vc1;
    vc1.Increment("studio_la");
    vc1.Increment("studio_la");
    VectorClock vc2;
    vc2.Increment("studio_la");
    assert(vc1.Dominates(vc2));
    assert(!vc2.Dominates(vc1));

    // 2. CASHash Validation
    std::string validHash = "af1349b9f5f9a1a6a0404dea36dcc9499bcb25c9adc112b7cc9a93cae41f3262";
    CASHash h(validHash);
    assert(h.ShardPath() == "objects/af/13/" + validHash);

    // 3. Binary Frame Serialization Test
    LiveLinkFrame frame;
    frame.subject_name = "CppCamera";
    frame.subject_type = SubjectType::Camera;
    frame.timestamp = 1700000000.5;
    frame.frame_number = 42;
    frame.translation = Vector3(10.0f, 20.0f, 30.0f);
    frame.rotation = Quaternion(0.0f, 0.0f, 0.7071f, 0.7071f);
    frame.scale = Vector3(1.0f, 1.0f, 1.0f);
    frame.camera.field_of_view = 45.0f;
    frame.camera.focal_length = 35.0f;
    frame.camera.aperture = 2.0f;
    frame.camera.focus_distance = 500.0f;

    std::vector<uint8_t> bytes = frame.SerializeBinary();
    std::cout.write(reinterpret_cast<const char*>(bytes.data()), bytes.size());
    return 0;
}}
""", encoding="utf-8")

            # Compile test program
            compile_cmd = [
                compiler,
                "-std=c++17",
                "-Wall",
                "-Wextra",
                "-Werror",
                str(test_src),
                "-o",
                str(test_bin),
            ]
            res = subprocess.run(compile_cmd, capture_output=True, text=True)
            self.assertEqual(res.returncode, 0, f"Compilation failed: {res.stderr}")

            # Execute test program and capture binary output
            run_res = subprocess.run([str(test_bin)], capture_output=True, check=True)
            raw_binary = run_res.stdout

            # Verify Python protocol deserializes C++ emitted packet exactly
            py_frame = LiveLinkPacket.decode_binary(raw_binary)
            self.assertEqual(py_frame.subject_name, "CppCamera")
            self.assertEqual(py_frame.subject_type, LiveLinkSubjectType.CAMERA)
            self.assertAlmostEqual(py_frame.timestamp, 1700000000.5, places=3)
            self.assertEqual(py_frame.frame_number, 42)
            self.assertAlmostEqual(py_frame.translation[0], 10.0, places=2)
            self.assertAlmostEqual(py_frame.translation[1], 20.0, places=2)
            self.assertAlmostEqual(py_frame.translation[2], 30.0, places=2)
            self.assertAlmostEqual(py_frame.rotation[2], 0.7071, places=3)
            self.assertAlmostEqual(py_frame.rotation[3], 0.7071, places=3)
            self.assertAlmostEqual(py_frame.field_of_view, 45.0, places=2)
            self.assertAlmostEqual(py_frame.focal_length, 35.0, places=2)
            self.assertAlmostEqual(py_frame.aperture, 2.0, places=2)
            self.assertAlmostEqual(py_frame.focus_distance, 500.0, places=2)


if __name__ == "__main__":
    unittest.main()
