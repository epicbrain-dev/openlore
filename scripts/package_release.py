#!/usr/bin/env python3
"""
package_release.py
Automated release packaging utility for OpenLore.
Builds Python wheel/sdist and bundles DCC sidecars (Blender, Maya, Houdini, Unreal) into zip archives with SHA-256 checksums.
"""

import hashlib
import os
import shutil
import subprocess
import sys
import zipfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "src"))

from openlore import __version__
from openlore.bridge.unreal.plugin_scaffold import UnrealPluginScaffolder
from openlore.dcc.export import DCCExporter


def sha256_file(filepath: Path) -> str:
    hasher = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(65536):
            hasher.update(chunk)
    return hasher.hexdigest()


def build_release_packages(output_dir: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    version = __version__
    print("=" * 70)
    print(f"📦 OpenLore Release Packaging Suite - v{version}")
    print("=" * 70)

    # 1. Export DCC plugins
    print("\n[1/5] Exporting Native DCC Sidecars...")
    dcc_dir = REPO_ROOT / "dcc_exports"
    DCCExporter.export_all(dcc_dir)
    print("  ✅ Blender, Maya, and Houdini Solaris scripts exported.")

    # 2. Export Unreal Live Link Plugin
    print("\n[2/5] Scaffolding Unreal Engine 5 Live Link Plugin...")
    unreal_dir = REPO_ROOT / "unreal_plugin"
    UnrealPluginScaffolder.generate_plugin(unreal_dir, plugin_name="OpenLoreLiveLink")
    print(f"  ✅ Unreal Engine C++ plugin scaffolded at: {unreal_dir.relative_to(REPO_ROOT)}")

    # 3. Build Python Wheel and sdist
    print("\n[3/5] Building Python Distribution Packages (wheel & sdist)...")
    cmd = [sys.executable, "-m", "build", "--outdir", str(output_dir)]
    # Use --no-isolation if hatchling is already installed locally
    try:
        import hatchling
        cmd.append("--no-isolation")
    except ImportError:
        pass

    subprocess.check_call(cmd, cwd=str(REPO_ROOT))
    print("  ✅ Built Python wheel and source distribution.")

    # 4. Package DCC Zip Bundles
    print("\n[4/5] Packaging DCC Standalone Zip Archives...")

    # Blender Zip
    blender_zip = output_dir / f"openlore-blender-addon-v{version}.zip"
    with zipfile.ZipFile(blender_zip, "w", zipfile.ZIP_DEFLATED) as z:
        z.write(
            dcc_dir / "blender" / "openlore_blender_addon.py",
            arcname="openlore_blender_addon.py"
        )
    print(f"  ✅ Created {blender_zip.name} ({blender_zip.stat().st_size:,} bytes)")

    # Maya Zip
    maya_zip = output_dir / f"openlore-maya-bridge-v{version}.zip"
    with zipfile.ZipFile(maya_zip, "w", zipfile.ZIP_DEFLATED) as z:
        z.write(
            dcc_dir / "maya" / "openlore_maya_bridge.py",
            arcname="openlore_maya_bridge.py"
        )
    print(f"  ✅ Created {maya_zip.name} ({maya_zip.stat().st_size:,} bytes)")

    # Houdini Zip
    houdini_zip = output_dir / f"openlore-houdini-solaris-v{version}.zip"
    with zipfile.ZipFile(houdini_zip, "w", zipfile.ZIP_DEFLATED) as z:
        z.write(
            dcc_dir / "houdini" / "openlore_houdini_bridge.py",
            arcname="openlore_houdini_bridge.py"
        )
        z.write(
            dcc_dir / "houdini" / "openlore_solaris_shelf.shelf",
            arcname="openlore_solaris_shelf.shelf"
        )
    print(f"  ✅ Created {houdini_zip.name} ({houdini_zip.stat().st_size:,} bytes)")

    # Unreal Plugin Zip
    unreal_zip = output_dir / f"openlore-unreal-livelink-v{version}.zip"
    with zipfile.ZipFile(unreal_zip, "w", zipfile.ZIP_DEFLATED) as z:
        for root, _, files in os.walk(unreal_dir):
            for file in sorted(files):
                full_path = Path(root) / file
                rel_path = full_path.relative_to(unreal_dir)
                z.write(full_path, arcname=str(Path("OpenLoreLiveLink") / rel_path))
    print(f"  ✅ Created {unreal_zip.name} ({unreal_zip.stat().st_size:,} bytes)")

    # Unity Package Zip
    unity_zip = output_dir / f"openlore-unity-livelink-v{version}.zip"
    with zipfile.ZipFile(unity_zip, "w", zipfile.ZIP_DEFLATED) as z:
        z.write(
            dcc_dir / "unity" / "OpenLoreLiveLinkClient.cs",
            arcname="com.openlore.livelink/Runtime/OpenLoreLiveLinkClient.cs"
        )
        z.write(
            dcc_dir / "unity" / "package.json",
            arcname="com.openlore.livelink/package.json"
        )
    print(f"  ✅ Created {unity_zip.name} ({unity_zip.stat().st_size:,} bytes)")

    # 5. Generate Checksums
    print("\n[5/5] Generating SHA-256 Checksums...")
    checksums_file = output_dir / "SHA256SUMS.txt"
    with open(checksums_file, "w", encoding="utf-8") as f:
        for item in sorted(output_dir.iterdir()):
            if item.is_file() and item.name != "SHA256SUMS.txt":
                h = sha256_file(item)
                f.write(f"{h}  {item.name}\n")
                print(f"  • {item.name}: {h[:16]}...")

    print("=" * 70)
    print(f"🎉 Successfully packaged OpenLore v{version} release into {output_dir.relative_to(REPO_ROOT)}/")
    print("=" * 70)


if __name__ == "__main__":
    out = REPO_ROOT / "dist"
    build_release_packages(out)
