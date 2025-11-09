#!/usr/bin/env python3
"""
Setup and environment management script for system-scripts toolkit.
Author: Loyd Johnson
Date: November 2025
"""

import os
import sys
import subprocess
import platform
from pathlib import Path

def check_python_version():
    """Check if Python version is compatible."""
    if sys.version_info < (3, 6):
        print("❌ Error: Python 3.6 or higher is required.")
        print(f"   Current version: {platform.python_version()}")
        return False
    else:
        print(f"✅ Python version: {platform.python_version()}")
        return True

def create_virtual_environment():
    """Create a virtual environment if it doesn't exist."""
    venv_path = Path("venv")
    
    if venv_path.exists():
        print("✅ Virtual environment already exists.")
        return True
    
    try:
        print("🔄 Creating virtual environment...")
        if platform.system() == "Windows":
            subprocess.run([sys.executable, "-m", "venv", "venv"], check=True)
        else:
            subprocess.run([sys.executable, "-m", "venv", "venv"], check=True)
        print("✅ Virtual environment created successfully.")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Error creating virtual environment: {e}")
        return False

def get_activation_instructions():
    """Get platform-specific activation instructions."""
    if platform.system() == "Windows":
        return {
            "cmd": "venv\\Scripts\\activate.bat",
            "powershell": "venv\\Scripts\\Activate.ps1",
            "instruction": "Run: venv\\Scripts\\activate.bat (Command Prompt) or venv\\Scripts\\Activate.ps1 (PowerShell)"
        }
    else:
        return {
            "bash": "source venv/bin/activate",
            "instruction": "Run: source venv/bin/activate"
        }

def install_dependencies(dev=False):
    """Install dependencies in the virtual environment."""
    venv_path = Path("venv")
    
    if platform.system() == "Windows":
        pip_path = venv_path / "Scripts" / "pip.exe"
        python_path = venv_path / "Scripts" / "python.exe"
    else:
        pip_path = venv_path / "bin" / "pip"
        python_path = venv_path / "bin" / "python"
    
    if not pip_path.exists():
        print("❌ Virtual environment not found. Please create it first.")
        return False
    
    try:
        print("🔄 Upgrading pip...")
        subprocess.run([str(python_path), "-m", "pip", "install", "--upgrade", "pip"], check=True)
        
        requirements_file = "requirements-dev.txt" if dev else "requirements.txt"
        print(f"🔄 Installing dependencies from {requirements_file}...")
        subprocess.run([str(pip_path), "install", "-r", requirements_file], check=True)
        
        print("✅ Dependencies installed successfully.")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Error installing dependencies: {e}")
        return False

def check_dependencies():
    """Check if required dependencies are available."""
    venv_path = Path("venv")
    
    if platform.system() == "Windows":
        python_path = venv_path / "Scripts" / "python.exe"
    else:
        python_path = venv_path / "bin" / "python"
    
    if not python_path.exists():
        print("❌ Virtual environment not found.")
        return False
    
    try:
        # Check psutil
        result = subprocess.run([str(python_path), "-c", "import psutil; print(psutil.__version__)"], 
                              capture_output=True, text=True, check=True)
        print(f"✅ psutil version: {result.stdout.strip()}")
        
        # Check requests
        result = subprocess.run([str(python_path), "-c", "import requests; print(requests.__version__)"], 
                              capture_output=True, text=True, check=True)
        print(f"✅ requests version: {result.stdout.strip()}")
        
        return True
    except subprocess.CalledProcessError:
        print("❌ Required dependencies not found.")
        return False

def setup_git_hooks():
    """Setup git hooks for development."""
    git_hooks_dir = Path(".git/hooks")
    
    if not git_hooks_dir.exists():
        print("ℹ️  Not a git repository. Skipping git hooks setup.")
        return
    
    # Create a simple pre-commit hook for Python linting
    pre_commit_hook = git_hooks_dir / "pre-commit"
    
    hook_content = """#!/bin/bash
# Pre-commit hook for system-scripts
# Run basic Python syntax checks

echo "Running pre-commit checks..."

# Check Python syntax
find . -name "*.py" -not -path "./venv/*" -exec python -m py_compile {} \\;

if [ $? -ne 0 ]; then
    echo "❌ Python syntax errors found. Commit aborted."
    exit 1
fi

echo "✅ Pre-commit checks passed."
"""
    
    try:
        with open(pre_commit_hook, 'w', newline='\n') as f:
            f.write(hook_content)
        
        # Make executable on Unix-like systems
        if platform.system() != "Windows":
            os.chmod(pre_commit_hook, 0o755)
        
        print("✅ Git pre-commit hook installed.")
    except Exception as e:
        print(f"⚠️  Could not install git hook: {e}")

def main():
    """Main setup function."""
    print("=" * 50)
    print("  System Scripts Toolkit - Environment Setup")
    print("  Author: Loyd Johnson")
    print("  Date: November 2025")
    print("=" * 50)
    print()
    
    # Check Python version
    if not check_python_version():
        return 1
    
    # Create virtual environment
    if not create_virtual_environment():
        return 1
    
    # Install dependencies
    dev_mode = "--dev" in sys.argv or "-d" in sys.argv
    if not install_dependencies(dev=dev_mode):
        return 1
    
    # Check dependencies
    if not check_dependencies():
        return 1
    
    # Setup git hooks for development
    if dev_mode:
        setup_git_hooks()
    
    print()
    print("🎉 Environment setup complete!")
    print()
    print("Next steps:")
    activation = get_activation_instructions()
    print(f"1. Activate the virtual environment:")
    print(f"   {activation['instruction']}")
    print()
    print("2. Test the installation:")
    print("   python auto_update.py --check-prereq")
    print()
    print("3. Run help desk tools:")
    print("   python scripts/helpdesk/system_info.py")
    print("   python scripts/helpdesk/network_diagnostics.py")
    print("   python scripts/helpdesk/performance_analyzer.py")
    print()
    
    if platform.system() == "Windows":
        print("4. Windows-specific tools:")
        print("   scripts\\windows\\windows_maintenance.bat")
        print("   powershell -ExecutionPolicy Bypass -File scripts\\windows\\windows_powershell_utils.ps1")
        print()
    
    return 0

if __name__ == "__main__":
    sys.exit(main())