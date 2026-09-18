#!/usr/bin/env python3
"""
installer.py - Universal Cross-Platform Installer & Lifecycle Manager for OpenLore
Supported Platforms: macOS (Darwin x86_64 / arm64), Linux (x86_64 / aarch64), Windows (x64 / arm64)
Requirements: Python 3.9+ (Standard Library only - zero external dependencies)
"""

import argparse
import os
import platform
import shutil
import subprocess
import sys
import venv
from pathlib import Path
from typing import Dict, List, Optional, Tuple

MIN_PYTHON_VERSION = (3, 9)
DEFAULT_DIR_NAME = ".openlore"

# Terminal ANSI styling helpers
USE_COLOR = sys.stdout.isatty() and (platform.system() != "Windows" or os.environ.get("ANSICON") or "WT_SESSION" in os.environ)


def colorize(text: str, code: str) -> str:
    if not USE_COLOR:
        return text
    return f"\033[{code}m{text}\033[0m"


def bold(text: str) -> str:
    return colorize(text, "1")


def green(text: str) -> str:
    return colorize(text, "32")


def yellow(text: str) -> str:
    return colorize(text, "33")


def cyan(text: str) -> str:
    return colorize(text, "36")


def red(text: str) -> str:
    return colorize(text, "31")


def print_banner() -> None:
    banner = f"""
{cyan("╔═════════════════════════════════════════════════════════════════════════╗")}
{cyan("║")}   {bold("OpenLore")} — Version Control & Lore Engine for 3D Worlds & VFX      {cyan("║")}
{cyan("║")}   {bold("Cross-Platform Production Installer")}                              {cyan("║")}
{cyan("╚═════════════════════════════════════════════════════════════════════════╝")}
"""
    print(banner)


class SystemDiagnostics:
    """Probes host OS, architecture, Python environment, and DCC applications."""

    @staticmethod
    def get_os() -> str:
        s = platform.system().lower()
        if "darwin" in s:
            return "macOS"
        elif "linux" in s:
            return "Linux"
        elif "windows" in s:
            return "Windows"
        return platform.system()

    @staticmethod
    def get_arch() -> str:
        return platform.machine()

    @staticmethod
    def check_python_version() -> Tuple[bool, str]:
        current = sys.version_info[:2]
        version_str = f"{current[0]}.{current[1]}.{sys.version_info.micro}"
        if current < MIN_PYTHON_VERSION:
            return False, version_str
        return True, version_str

    @staticmethod
    def detect_dcc_tools() -> Dict[str, Optional[str]]:
        """Detects presence of major 3D DCC tools in standard paths or PATH."""
        dccs: Dict[str, Optional[str]] = {
            "blender": shutil.which("blender"),
            "maya": shutil.which("maya"),
            "houdini": shutil.which("houdini"),
            "unreal": shutil.which("UnrealEditor"),
            "unity": shutil.which("Unity"),
        }

        # Check standard macOS Application folders if not in PATH
        if platform.system() == "Darwin":
            if not dccs["blender"] and Path("/Applications/Blender.app").exists():
                dccs["blender"] = "/Applications/Blender.app"
            if not dccs["maya"]:
                for p in Path("/Applications/Autodesk").glob("maya*"):
                    if p.is_dir():
                        dccs["maya"] = str(p)
                        break
            if not dccs["houdini"]:
                for p in Path("/Applications/Houdini").glob("Houdini*"):
                    if p.is_dir():
                        dccs["houdini"] = str(p)
                        break
            if not dccs["unreal"] and Path("/Users/Shared/Epic Games").exists():
                for p in Path("/Users/Shared/Epic Games").glob("UE_*"):
                    if p.is_dir():
                        dccs["unreal"] = str(p)
                        break

        # Check standard Windows Program Files
        elif platform.system() == "Windows":
            pf = Path(os.environ.get("ProgramFiles", r"C:\Program Files"))
            if not dccs["blender"]:
                for p in (pf / "Blender Foundation").glob("Blender*"):
                    if p.is_dir():
                        dccs["blender"] = str(p)
                        break
            if not dccs["maya"]:
                for p in (pf / "Autodesk").glob("Maya*"):
                    if p.is_dir():
                        dccs["maya"] = str(p)
                        break
            if not dccs["houdini"]:
                for p in (pf / "Side Effects Software").glob("Houdini*"):
                    if p.is_dir():
                        dccs["houdini"] = str(p)
                        break
            if not dccs["unreal"]:
                for p in (pf / "Epic Games").glob("UE_*"):
                    if p.is_dir():
                        dccs["unreal"] = str(p)
                        break

        return dccs


class OpenLoreInstaller:
    """Manages installation, configuration, executable shims, and uninstallation."""

    def __init__(
        self,
        prefix: Optional[Path] = None,
        non_interactive: bool = False,
        modify_path: bool = True,
        with_dcc: Optional[str] = None,
        launch_web: bool = False,
        quiet: bool = False,
    ):
        if prefix:
            self.prefix = prefix.resolve()
        else:
            self.prefix = Path.home() / DEFAULT_DIR_NAME

        self.non_interactive = non_interactive
        self.modify_path = modify_path
        self.with_dcc = with_dcc
        self.launch_web = launch_web
        self.quiet = quiet

        self.bin_dir = self.prefix / "bin"
        self.env_dir = self.prefix / "env"
        self.web_dir = self.prefix / "web"
        self.data_dir = self.prefix / "data"
        self.dcc_dir = self.prefix / "dcc"

        # Determine source repo root if installer is running from within repo
        self.repo_root = Path(__file__).resolve().parent
        self.is_in_repo = (self.repo_root / "pyproject.toml").exists() or (self.repo_root / "setup.py").exists()

    def get_env_python(self) -> Path:
        if platform.system() == "Windows":
            return self.env_dir / "Scripts" / "python.exe"
        return self.env_dir / "bin" / "python"

    def get_env_pip(self) -> Path:
        if platform.system() == "Windows":
            return self.env_dir / "Scripts" / "pip.exe"
        return self.env_dir / "bin" / "pip"

    def log(self, msg: str) -> None:
        if not self.quiet:
            print(msg)

    def run_preflight_checks(self) -> bool:
        """Validates system prerequisites."""
        self.log(bold("\n[1/6] Performing System Preflight Diagnostics..."))
        os_name = SystemDiagnostics.get_os()
        arch = SystemDiagnostics.get_arch()
        ok_py, py_ver = SystemDiagnostics.check_python_version()

        self.log(f"  • Operating System: {cyan(os_name)} ({arch})")
        self.log(f"  • Host Python:     {cyan(py_ver)} ({sys.executable})")

        if not ok_py:
            print(red(f"\n❌ Error: OpenLore requires Python {MIN_PYTHON_VERSION[0]}.{MIN_PYTHON_VERSION[1]}+. Found Python {py_ver}."))
            print("Please install or upgrade Python before running the installer.")
            return False

        dccs = SystemDiagnostics.detect_dcc_tools()
        detected_names = [k.capitalize() for k, v in dccs.items() if v]
        if detected_names:
            self.log(f"  • Detected DCCs:   {green(', '.join(detected_names))}")
        else:
            self.log(f"  • Detected DCCs:   {yellow('None in standard paths (can link later)')}")

        self.log(f"  • Target Prefix:   {cyan(str(self.prefix))}")
        return True

    def create_layout(self) -> None:
        """Creates target directory hierarchy."""
        self.log(bold("\n[2/6] Scaffolding Isolated Installation Directory..."))
        for d in [self.bin_dir, self.web_dir, self.data_dir / "cas", self.data_dir / "stages", self.dcc_dir]:
            d.mkdir(parents=True, exist_ok=True)
        self.log(f"  ✅ Directory structure initialized at: {cyan(str(self.prefix))}")

    def provision_virtual_environment(self) -> bool:
        """Provisions an isolated virtual environment and installs OpenLore."""
        self.log(bold("\n[3/6] Provisioning Isolated Python Virtual Environment..."))
        try:
            # Create venv if not already existing
            if not self.get_env_python().exists():
                self.log(f"  • Creating venv at: {self.env_dir}")
                venv.create(self.env_dir, with_pip=True, clear=False)
            else:
                self.log(f"  • Found existing venv at: {self.env_dir}")

            env_python = self.get_env_python()
            if not env_python.exists():
                print(red(f"❌ Failed to locate virtual environment python at: {env_python}"))
                return False

            # Upgrade pip first — old pip (< 22) may not support hatchling editable installs
            self.log("  • Upgrading pip in virtual environment...")
            pip_upgrade = subprocess.run(
                [str(env_python), "-m", "pip", "install", "--upgrade", "pip"],
                stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
            )
            if pip_upgrade.returncode != 0:
                self.log(yellow(f"  ⚠️ pip upgrade warning (non-fatal): {pip_upgrade.stderr.strip()}"))

            # Install OpenLore
            self.log("  • Installing OpenLore and dependencies into runtime...")
            if self.is_in_repo:
                # Install from current repository
                cmd = [str(env_python), "-m", "pip", "install", "-e", str(self.repo_root)]
            else:
                # Standalone mode: install from bundled wheel, local dist/, or official release wheel
                script_dir = Path(__file__).resolve().parent
                bundled_wheels = list(script_dir.glob("*.whl")) + (list(self.repo_root.glob("dist/*.whl")) if self.repo_root.exists() else [])
                if bundled_wheels:
                    cmd = [str(env_python), "-m", "pip", "install", str(bundled_wheels[0])]
                else:
                    release_wheel = "https://github.com/epicbrain-dev/openlore/releases/download/v2.0.1/openlore-2.0.1-py3-none-any.whl"
                    cmd = [str(env_python), "-m", "pip", "install", release_wheel]

            res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            if res.returncode != 0:
                self.log(yellow("  ⚠️ pip install failed. Attempting .pth fallback..."))
                self.log(yellow(f"     pip stderr: {res.stderr.strip()}"))
                # If offline or unavailable, link src directory via .pth file
                site_packages = list(self.env_dir.glob("lib/python*/site-packages"))
                if not site_packages and platform.system() == "Windows":
                    site_packages = [self.env_dir / "Lib" / "site-packages"]
                if site_packages and (self.repo_root / "src").exists():
                    pth_file = site_packages[0] / "openlore.pth"
                    pth_file.write_text(str(self.repo_root / "src") + "\n", encoding="utf-8")
                    self.log(f"  ✅ Linked source directory via {pth_file.name}")
                else:
                    print(red("❌ pip install failed and no fallback source directory found."))
                    print(red(f"   pip output:\n{res.stderr.strip()}"))
                    return False

            # Verify the package is actually importable before declaring success
            check = subprocess.run(
                [str(env_python), "-c", "import openlore"],
                stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
            )
            if check.returncode != 0:
                print(red("❌ OpenLore package installed but cannot be imported:"))
                print(red(f"   {check.stderr.strip()}"))
                return False

            self.log("  ✅ Python virtual environment and OpenLore package ready.")
            return True
        except Exception as e:
            print(red(f"❌ Virtual environment provisioning failed: {e}"))
            return False

    def deploy_web_assets(self) -> None:
        """Copies or links compiled Web Cockpit assets to ~/.openlore/web/dist."""
        self.log(bold("\n[4/6] Deploying OpenLore Web Studio Frontend Assets..."))
        source_dist = self.repo_root / "web" / "dist"
        target_dist = self.web_dir / "dist"

        if source_dist.exists() and (source_dist / "index.html").exists():
            if target_dist.exists():
                shutil.rmtree(target_dist)
            shutil.copytree(source_dist, target_dist)
            self.log(f"  ✅ Deployed Web Studio assets to: {cyan(str(target_dist))}")
        else:
            target_dist.mkdir(parents=True, exist_ok=True)
            index_html = target_dist / "index.html"
            if not index_html.exists():
                index_html.write_text(
                    "<!DOCTYPE html><html><head><title>OpenLore Web Studio</title></head>"
                    "<body><h1>OpenLore Web Studio</h1><p>Ready for connection.</p></body></html>",
                    encoding="utf-8",
                )
            self.log(f"  ℹ️ Web Studio placeholder ready at: {cyan(str(target_dist))}")

    def generate_launcher_shims(self) -> None:
        """Generates cross-platform command-line launcher shims."""
        self.log(bold("\n[5/6] Generating Turnkey Command-Line Launchers..."))

        # 1. Unix bash shim
        unix_shim = self.bin_dir / "openlore"
        unix_content = f"""#!/usr/bin/env bash
OPENLORE_HOME="{self.prefix}"
export OPENLORE_HOME
exec "{self.get_env_python()}" -m openlore.cli.main "$@"
"""
        unix_shim.write_text(unix_content, encoding="utf-8")
        try:
            unix_shim.chmod(0o755)
        except OSError:
            pass
        self.log(f"  ✅ Generated Unix launcher: {cyan(str(unix_shim))}")

        # 2. Windows batch shim
        win_cmd = self.bin_dir / "openlore.cmd"
        win_cmd_content = f"""@echo off
set "OPENLORE_HOME={self.prefix}"
"{self.get_env_python()}" -m openlore.cli.main %*
"""
        win_cmd.write_text(win_cmd_content, encoding="utf-8")

        # 3. Windows PowerShell shim
        win_ps1 = self.bin_dir / "openlore.ps1"
        win_ps1_content = f"""$env:OPENLORE_HOME = "{self.prefix}"
& "{self.get_env_python()}" -m openlore.cli.main @args
"""
        win_ps1.write_text(win_ps1_content, encoding="utf-8")
        self.log(f"  ✅ Generated Windows launchers: {cyan(str(win_cmd.name))}, {cyan(str(win_ps1.name))}")

    def configure_path(self) -> None:
        """Adds ~/.openlore/bin to user's shell PATH if not already present."""
        if not self.modify_path:
            self.log("  ℹ️ Skipping PATH modification as requested (--no-modify-path).")
            return

        bin_str = str(self.bin_dir)
        system = platform.system()

        if system in ("Darwin", "Linux"):
            export_cmd = f'export PATH="{bin_str}:$PATH"'
            profiles = [
                Path.home() / ".zshrc",
                Path.home() / ".bashrc",
                Path.home() / ".profile",
            ]
            modified = False
            for prof in profiles:
                if prof.exists():
                    try:
                        content = prof.read_text(encoding="utf-8", errors="ignore")
                        if bin_str not in content:
                            with open(prof, "a", encoding="utf-8") as f:
                                f.write(f"\n# OpenLore Production CLI\n{export_cmd}\n")
                            self.log(f"  ✅ Added OpenLore to PATH in: {cyan(str(prof))}")
                            modified = True
                    except OSError:
                        pass
            if not modified:
                # If none exist, append to .profile or .zshrc
                target_prof = Path.home() / (".zshrc" if system == "Darwin" else ".bashrc")
                try:
                    with open(target_prof, "a", encoding="utf-8") as f:
                        f.write(f"\n# OpenLore Production CLI\n{export_cmd}\n")
                    self.log(f"  ✅ Created and configured PATH in: {cyan(str(target_prof))}")
                except OSError:
                    pass

        elif system == "Windows":
            # Append to user PATH via Windows PowerShell/Registry
            try:
                ps_script = f"""
$CurrentPath = [Environment]::GetEnvironmentVariable("PATH", "User")
if ($CurrentPath -notlike "*{bin_str}*") {{
    [Environment]::SetEnvironmentVariable("PATH", "$CurrentPath;{bin_str}", "User")
}}
"""
                subprocess.run(["powershell", "-NoProfile", "-Command", ps_script], check=False)
                self.log(f"  ✅ Added {bin_str} to Windows User PATH environment variable.")
            except Exception as e:
                self.log(yellow(f"  ⚠️ Could not update Windows PATH automatically: {e}"))

    def export_dcc_bridges(self) -> None:
        """Exports standalone DCC bridges into <prefix>/dcc."""
        if not self.with_dcc:
            return

        self.log(bold("\n[*] Exporting DCC Sidecars..."))
        try:
            from openlore.dcc.export import DCCExporter
            from openlore.bridge.unreal.plugin_scaffold import UnrealPluginScaffolder

            target = self.with_dcc.lower()
            if target in ("all", "blender", "maya", "houdini"):
                DCCExporter.export_all(self.dcc_dir)
                self.log(f"  ✅ Exported Blender, Maya, and Houdini bridges into: {cyan(str(self.dcc_dir))}")
            if target in ("all", "unreal"):
                UnrealPluginScaffolder.generate_plugin(self.dcc_dir / "unreal" / "OpenLoreLiveLink")
                self.log(f"  ✅ Exported Unreal Engine 5 C++ Plugin into: {cyan(str(self.dcc_dir / 'unreal'))}")
        except Exception as e:
            self.log(yellow(f"  ⚠️ Could not export DCC sidecars: {e}"))

    def verify_installation(self) -> bool:
        """Runs openlore --help to verify launcher function."""
        self.log(bold("\n[6/6] Verifying Installation & Self-Test..."))
        shim = self.bin_dir / ("openlore.cmd" if platform.system() == "Windows" else "openlore")

        if not shim.exists():
            print(red(f"❌ Launcher shim missing: {shim}"))
            return False

        try:
            res = subprocess.run([str(shim), "--help"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            if res.returncode == 0:
                self.log(green("  🎉 OpenLore CLI verified successfully!"))
                return True
            else:
                print(red(f"❌ CLI verification failed: {res.stderr.strip()}"))
                print(red("   The 'openlore' command cannot be run. Installation may be incomplete."))
                print(yellow("   Try re-running the installer or check the venv at: " + str(self.env_dir)))
                return False
        except Exception as e:
            print(red(f"❌ Self-test check failed: {e}"))
            return False

    def install(self) -> bool:
        """Full installation sequence."""
        print_banner()

        if not self.non_interactive:
            print(f"This wizard will install OpenLore into: {cyan(str(self.prefix))}\n")
            try:
                resp = input(bold("Proceed with installation? [Y/n]: ")).strip().lower()
                if resp in ("n", "no"):
                    print("Installation aborted by user.")
                    return False
            except (KeyboardInterrupt, EOFError):
                print("\nInstallation aborted.")
                return False

        if not self.run_preflight_checks():
            return False

        self.create_layout()

        if not self.provision_virtual_environment():
            return False

        self.deploy_web_assets()
        self.generate_launcher_shims()
        self.configure_path()
        self.export_dcc_bridges()

        if not self.verify_installation():
            print(red("\n❌ Installation verification failed. Please check the errors above."))
            return False

        self.log("\n" + "=" * 73)
        self.log(green(bold("🚀 OpenLore Installation Complete!")))
        self.log("=" * 73)
        self.log(f"\n• Binary directory:  {cyan(str(self.bin_dir))}")
        self.log(f"• Virtual runtime:   {cyan(str(self.env_dir))}")
        self.log(f"• Web Studio assets: {cyan(str(self.web_dir / 'dist'))}")
        self.log("\nQuick start commands:")
        self.log(f"  {bold('openlore doctor')}                 # Run complete system & DCC health diagnosis")
        self.log(f"  {bold('openlore web --port 8000')}       # Launch the 3D Web Cockpit & REST server")
        self.log(f"  {bold('openlore init')}                   # Initialize local CAS and prime lore graph")
        self.log("\nRestart your terminal or run:")
        if platform.system() == "Darwin":
            self.log(f"  {cyan('source ~/.zshrc')}")
        elif platform.system() == "Linux":
            self.log(f"  {cyan('source ~/.bashrc')}")
        else:
            self.log(f"  {cyan('refreshenv')}")
        self.log("=" * 73 + "\n")

        if self.launch_web:
            self.log(bold("[*] Launching OpenLore Web Studio Cockpit..."))
            shim = self.bin_dir / ("openlore.cmd" if platform.system() == "Windows" else "openlore")
            try:
                subprocess.run([str(shim), "web", "--port", "8000"])
            except KeyboardInterrupt:
                pass

        return True

    def uninstall(self) -> bool:
        """Cleanly uninstalls OpenLore."""
        print_banner()
        print(yellow(bold("⚠️ OpenLore Uninstallation Mode")))
        print(f"Target directory to remove: {cyan(str(self.prefix))}\n")

        if not self.non_interactive:
            try:
                resp = input(bold("Are you sure you want to completely remove OpenLore? [y/N]: ")).strip().lower()
                if resp not in ("y", "yes"):
                    print("Uninstallation aborted.")
                    return False
            except (KeyboardInterrupt, EOFError):
                print("\nUninstallation aborted.")
                return False

        if self.prefix.exists():
            try:
                shutil.rmtree(self.prefix)
                print(f"  ✅ Removed installation directory: {self.prefix}")
            except Exception as e:
                print(red(f"  ❌ Error removing {self.prefix}: {e}"))
                return False
        else:
            print(f"  ℹ️ Directory {self.prefix} does not exist.")

        # Clean up PATH entries in POSIX shell profiles
        if platform.system() in ("Darwin", "Linux"):
            bin_str = str(self.bin_dir)
            profiles = [Path.home() / ".zshrc", Path.home() / ".bashrc", Path.home() / ".profile"]
            for prof in profiles:
                if prof.exists():
                    try:
                        lines = prof.read_text(encoding="utf-8", errors="ignore").splitlines()
                        new_lines = [l for l in lines if bin_str not in l and "# OpenLore Production CLI" not in l]
                        prof.write_text("\n".join(new_lines) + "\n", encoding="utf-8")
                        print(f"  ✅ Cleaned shell profile: {prof.name}")
                    except OSError:
                        pass

        print(green(bold("\n🎉 OpenLore successfully uninstalled.\n")))
        return True


def main() -> int:
    parser = argparse.ArgumentParser(
        description="OpenLore Cross-Platform Installer & Lifecycle Manager",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--prefix",
        type=Path,
        default=None,
        help=f"Target installation directory (default: ~/{DEFAULT_DIR_NAME})",
    )
    parser.add_argument(
        "-y",
        "--yes",
        dest="non_interactive",
        action="store_true",
        help="Non-interactive / automatic confirmation mode",
    )
    parser.add_argument(
        "--no-modify-path",
        action="store_true",
        help="Do not modify user shell configuration or PATH environment variable",
    )
    parser.add_argument(
        "--with-dcc",
        choices=["all", "blender", "maya", "houdini", "unreal", "unity"],
        help="Export pre-configured DCC telemetry connectors during installation",
    )
    parser.add_argument(
        "--launch-web",
        action="store_true",
        help="Automatically start OpenLore Web Studio Cockpit after successful installation",
    )
    parser.add_argument(
        "--uninstall",
        action="store_true",
        help="Completely uninstall OpenLore and remove associated shims",
    )
    parser.add_argument(
        "-q",
        "--quiet",
        action="store_true",
        help="Quiet mode with minimal console output",
    )

    args = parser.parse_args()

    installer = OpenLoreInstaller(
        prefix=args.prefix,
        non_interactive=args.non_interactive,
        modify_path=not args.no_modify_path,
        with_dcc=args.with_dcc,
        launch_web=args.launch_web,
        quiet=args.quiet,
    )

    if args.uninstall:
        success = installer.uninstall()
    else:
        success = installer.install()

    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
