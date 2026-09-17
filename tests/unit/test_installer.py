"""Unit tests for OpenLore cross-platform installer suite and system diagnostics."""

import os
import platform
import shutil
import subprocess
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

import installer
from installer import (
    OpenLoreInstaller,
    SystemDiagnostics,
    bold,
    cyan,
    green,
    red,
    yellow,
)
from openlore.cli.main import create_parser, main


def test_ansi_styling():
    """Verify ANSI styling helper functions."""
    assert "test" in bold("test")
    assert "test" in green("test")
    assert "test" in yellow("test")
    assert "test" in cyan("test")
    assert "test" in red("test")


def test_system_diagnostics_os_arch():
    """Verify operating system and architecture diagnostics."""
    os_name = SystemDiagnostics.get_os()
    assert os_name in ("macOS", "Linux", "Windows") or len(os_name) > 0
    arch = SystemDiagnostics.get_arch()
    assert len(arch) > 0


def test_system_diagnostics_python_version():
    """Verify python version requirements checking."""
    ok, ver = SystemDiagnostics.check_python_version()
    # Test suite runs on Python 3.9+
    assert ok is True
    assert "." in ver


def test_system_diagnostics_dcc_detection():
    """Verify DCC tools inspection returns structured mapping."""
    dccs = SystemDiagnostics.detect_dcc_tools()
    assert isinstance(dccs, dict)
    for key in ("blender", "maya", "houdini", "unreal", "unity"):
        assert key in dccs


def test_installer_layout_creation(tmp_path: Path):
    """Verify installer creates expected isolated directory layout."""
    inst = OpenLoreInstaller(
        prefix=tmp_path / "openlore_test",
        non_interactive=True,
        modify_path=False,
    )
    inst.create_layout()

    assert (inst.prefix / "bin").is_dir()
    assert (inst.prefix / "web").is_dir()
    assert (inst.prefix / "data" / "cas").is_dir()
    assert (inst.prefix / "data" / "stages").is_dir()
    assert (inst.prefix / "dcc").is_dir()


def test_installer_generate_launcher_shims(tmp_path: Path):
    """Verify generation of Unix and Windows launcher shims."""
    prefix = tmp_path / "openlore_test"
    inst = OpenLoreInstaller(prefix=prefix, non_interactive=True, modify_path=False)
    inst.create_layout()
    inst.generate_launcher_shims()

    # Unix bash shim
    unix_shim = inst.bin_dir / "openlore"
    assert unix_shim.is_file()
    unix_content = unix_shim.read_text(encoding="utf-8")
    assert "#!/usr/bin/env bash" in unix_content
    assert "OPENLORE_HOME=" in unix_content
    assert "-m openlore.cli.main" in unix_content

    # Windows batch and powershell shims
    win_cmd = inst.bin_dir / "openlore.cmd"
    assert win_cmd.is_file()
    assert "@echo off" in win_cmd.read_text(encoding="utf-8")

    win_ps1 = inst.bin_dir / "openlore.ps1"
    assert win_ps1.is_file()
    assert "$env:OPENLORE_HOME" in win_ps1.read_text(encoding="utf-8")


def test_installer_deploy_web_assets(tmp_path: Path):
    """Verify web asset deployment and fallback generation."""
    prefix = tmp_path / "openlore_test"
    inst = OpenLoreInstaller(prefix=prefix, non_interactive=True, modify_path=False)
    inst.create_layout()
    inst.deploy_web_assets()

    index_html = inst.web_dir / "dist" / "index.html"
    assert index_html.is_file()
    content = index_html.read_text(encoding="utf-8")
    assert "OpenLore" in content


def test_installer_uninstaller_cleanup(tmp_path: Path):
    """Verify uninstallation cleans up files and shell profiles."""
    prefix = tmp_path / "openlore_test"
    inst = OpenLoreInstaller(prefix=prefix, non_interactive=True, modify_path=False)
    inst.create_layout()
    inst.generate_launcher_shims()

    assert prefix.exists()

    # Create mock shell profile
    mock_profile = tmp_path / ".zshrc"
    mock_profile.write_text(
        f"# Other config\nexport PATH=\"{inst.bin_dir}:$PATH\"\nexport FOO=1\n",
        encoding="utf-8",
    )

    with patch("pathlib.Path.home", return_value=tmp_path):
        success = inst.uninstall()
        assert success is True
        assert not prefix.exists()

        # Check profile was cleaned
        cleaned = mock_profile.read_text(encoding="utf-8")
        assert str(inst.bin_dir) not in cleaned
        assert "export FOO=1" in cleaned


def test_installer_cli_parsing():
    """Verify CLI argument parsing in installer.py."""
    with patch("sys.argv", ["installer.py", "--yes", "--no-modify-path", "--prefix", "/tmp/openlore"]):
        with patch.object(OpenLoreInstaller, "install", return_value=True) as mock_install:
            ret = installer.main()
            assert ret == 0
            assert mock_install.called


def test_cli_doctor_command(capsys):
    """Verify 'openlore doctor' CLI command execution."""
    parser = create_parser()
    args = parser.parse_args(["doctor"])
    assert args.command == "doctor"

    ret = main(["doctor"])
    assert ret == 0
    captured = capsys.readouterr()
    assert "OpenLore System Health & Environment Doctor" in captured.out
    assert "Operating System:" in captured.out
    assert "Python Runtime:" in captured.out


def test_cli_doctor_json_command(capsys):
    """Verify 'openlore doctor --json' outputs valid machine-readable JSON."""
    ret = main(["doctor", "--json"])
    assert ret == 0
    captured = capsys.readouterr()
    import json
    data = json.loads(captured.out)
    assert "version" in data
    assert "platform" in data
    assert "cas" in data
    assert "web_cockpit" in data
    assert "dependencies" in data
