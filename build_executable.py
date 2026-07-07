"""
Platform-agnostic build script for creating OCTAVA executables.
This script replicates the functionality of the GitHub Actions workflow for local builds.

Usage:
    python build_executable.py
"""

import sys
import platform
import subprocess
from pathlib import Path

def run_command(cmd, description, cwd=None):
    """Run a command and handle errors."""
    print(f"\n{'='*60}")
    print(f"{description}")
    print(f"{'='*60}")
    print(f"Command: {cmd}")
    
    try:
        result = subprocess.run(
            cmd,
            shell=True,
            check=True,
            cwd=cwd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True
        )
        print(result.stdout)
        return True
    except subprocess.CalledProcessError as e:
        print(f"Error: {e}")
        print(f"Output: {e.stdout}")
        return False


def install_dependencies():
    """Install Python dependencies from requirements.txt."""
    requirements_file = Path(__file__).parent / "requirements.txt"
    return run_command(
        f'"{sys.executable}" -m pip install -r "{requirements_file}"',
        "Installing Python dependencies"
    )


def install_pyinstaller():
    """Install PyInstaller."""
    return run_command(
        f'"{sys.executable}" -m pip install pyinstaller',
        "Installing PyInstaller"
    )


def build_executable():
    """Build the executable using PyInstaller."""
    script_path = Path(__file__).parent / "code" / "gui.py"
    assets_path = Path(__file__).parent / "assets"

    # PyInstaller command with the same flags as the workflow
    pyinstaller_cmd = (
        f'"{sys.executable}" -m PyInstaller '
        f'--noconsole '
        f'--onefile '
        f'--add-data "{assets_path}:assets" '
        f'--hidden-import=PIL._tkinter_finder '
        f'"{script_path}"'
    )
    
    return run_command(
        pyinstaller_cmd,
        "Building executable with PyInstaller",
        cwd=Path(__file__).parent
    )

def main():
    """Main build process."""
    print("OCTAVA Executable Build Script")
    
    # Get platform information
    system = platform.system()
    arch = platform.machine()
    python_version = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"

    print(f"\n{'='*60}")
    print(f"Platform: {system}")
    print(f"Architecture: {arch}")
    print(f"Python version: {python_version}")
    
    # Confirm before proceeding
    print(f"\n{'='*60}")
    print("This script will:")
    print("  1. Install Python dependencies from requirements.txt")
    print("  2. Install PyInstaller")
    print("  3. Build the OCTAVA executable")
    
    response = input("\nProceed with build? (y/n): ")
    if response.lower() != 'y':
        print("Build cancelled.")
        sys.exit(0)
    
    # Step 1: Install dependencies
    if not install_dependencies():
        print("\nFailed to install dependencies. Build aborted.")
        sys.exit(1)
    
    # Step 2: Install PyInstaller
    if not install_pyinstaller():
        print("\nFailed to install PyInstaller. Build aborted.")
        sys.exit(1)
    
    # Step 3: Build executable
    if not build_executable():
        print("\nFailed to build executable. Build aborted.")
        sys.exit(1)
    
    print(f"\n{'='*60}")
    print("Build completed successfully!")
    print(f"Executable can be found in: {Path(__file__).parent / 'dist'}")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nBuild cancelled by user.")
        sys.exit(1)
    except Exception as e:
        print(f"\n\nUnexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
