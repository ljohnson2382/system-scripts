#!/bin/bash
"""
Setup script for system-scripts toolkit.
Installs dependencies and sets up the environment.
"""

import os
import sys
import subprocess
import platform


def check_python_version():
    """Check if Python version is supported."""
    if sys.version_info < (3, 6):
        print("Error: Python 3.6 or higher is required.")
        sys.exit(1)
    print(f"✓ Python {sys.version_info.major}.{sys.version_info.minor} detected")


def install_dependencies():
    """Install required Python packages."""
    try:
        print("Installing Python dependencies...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
        print("✓ Dependencies installed successfully")
    except subprocess.CalledProcessError as e:
        print(f"Error installing dependencies: {e}")
        sys.exit(1)


def check_system_requirements():
    """Check system-specific requirements."""
    system = platform.system().lower()
    
    if system == "linux":
        # Check for package managers
        managers = []
        if os.path.exists("/usr/bin/apt") or os.path.exists("/bin/apt"):
            managers.append("apt (Debian/Ubuntu)")
        if os.path.exists("/usr/bin/pacman"):
            managers.append("pacman (Arch)")
        if os.path.exists("/usr/bin/dnf"):
            managers.append("dnf (Fedora)")
        elif os.path.exists("/usr/bin/yum"):
            managers.append("yum (RHEL/CentOS)")
        
        if managers:
            print(f"✓ Package manager(s) found: {', '.join(managers)}")
        else:
            print("⚠ No supported package manager found")
    
    elif system == "darwin":
        print("✓ macOS detected")
        
        # Check for Homebrew
        if os.path.exists("/opt/homebrew/bin/brew") or os.path.exists("/usr/local/bin/brew"):
            print("✓ Homebrew detected")
        else:
            print("⚠ Homebrew not found - install for package management")
        
        # Check for mas
        try:
            subprocess.check_call(["which", "mas"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            print("✓ mas (Mac App Store CLI) detected")
        except subprocess.CalledProcessError:
            print("⚠ mas not found - install with 'brew install mas' for App Store updates")
    
    else:
        print(f"✓ {system} detected")


def make_executable():
    """Make scripts executable on Unix-like systems."""
    if platform.system() != "Windows":
        try:
            os.chmod("auto_update.py", 0o755)
            for root, dirs, files in os.walk("scripts"):
                for file in files:
                    if file.endswith(".py"):
                        file_path = os.path.join(root, file)
                        os.chmod(file_path, 0o755)
            print("✓ Scripts made executable")
        except Exception as e:
            print(f"⚠ Could not make scripts executable: {e}")


def create_directories():
    """Create necessary directories."""
    directories = ["logs"]
    for directory in directories:
        os.makedirs(directory, exist_ok=True)
    print("✓ Required directories created")


def run_test():
    """Run a basic test of the system."""
    try:
        print("Running system test...")
        result = subprocess.run([
            sys.executable, "auto_update.py", "--check-prereq"
        ], capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✓ System test passed")
            return True
        else:
            print(f"⚠ System test failed: {result.stderr}")
            return False
    except Exception as e:
        print(f"⚠ Could not run system test: {e}")
        return False


def main():
    """Main setup function."""
    print("System Scripts Toolkit Setup")
    print("=" * 40)
    
    # Basic checks
    check_python_version()
    check_system_requirements()
    
    # Setup
    install_dependencies()
    make_executable()
    create_directories()
    
    # Test
    if run_test():
        print("\n" + "=" * 40)
        print("✓ Setup completed successfully!")
        print("\nNext steps:")
        print("1. Review configuration files in configs/")
        print("2. Test with: python auto_update.py --dry-run")
        print("3. Run updates with: python auto_update.py")
        print("4. Check the README.md for detailed usage instructions")
    else:
        print("\n" + "=" * 40)
        print("⚠ Setup completed with warnings")
        print("Please check the output above and resolve any issues")
        print("You can still use the toolkit, but some features may not work")


if __name__ == "__main__":
    main()