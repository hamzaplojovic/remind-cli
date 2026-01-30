"""Build script for creating standalone binaries."""

import platform
import subprocess
import sys
from pathlib import Path


def build_binary(output_dir: Path | None = None) -> None:
    """Build a standalone binary using PyInstaller."""
    if output_dir is None:
        output_dir = Path("dist")

    output_dir.mkdir(exist_ok=True)

    system = platform.system()
    arch = platform.machine()

    print(f"Building for {system} ({arch})")

    # PyInstaller command
    cmd = [
        sys.executable,
        "-m",
        "PyInstaller",
        "--onefile",
        "--console",
        "--name",
        "remind",
        "--distpath",
        str(output_dir),
        "--workpath",
        "build",
        "--specpath",
        "build",
        "remind/__main__.py",
    ]

    try:
        subprocess.run(cmd, check=True, cwd=Path(__file__).parent.parent)
        binary_name = "remind.exe" if system == "Windows" else "remind"
        binary_path = output_dir / binary_name
        print(f"✓ Binary built: {binary_path}")
        print(f"  Size: {binary_path.stat().st_size / (1024 * 1024):.2f} MB")
    except subprocess.CalledProcessError as e:
        print(f"✗ Build failed: {e}")
        sys.exit(1)


def build_deb_package() -> None:
    """Build a Debian package."""
    print("Building Debian package...")
    # Placeholder for deb building
    print("Not yet implemented")


def build_rpm_package() -> None:
    """Build an RPM package."""
    print("Building RPM package...")
    # Placeholder for rpm building
    print("Not yet implemented")


if __name__ == "__main__":
    build_binary()
