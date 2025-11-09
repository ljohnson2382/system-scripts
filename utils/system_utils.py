#!/usr/bin/env python3
"""
System utilities module for cross-platform automation toolkit.
Provides OS detection, logging setup, and common helper functions.

Author: Loyd Johnson
Date: November 2025
"""

import os
import platform
import logging
import subprocess
import sys
import shutil
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, List, Tuple


class OSDetector:
    """Handles operating system and distribution detection."""
    
    @staticmethod
    def get_os_info() -> Dict[str, str]:
        """
        Detect the operating system and distribution.
        
        Returns:
            Dict containing os_type, distro, version, and architecture
        """
        system = platform.system().lower()
        
        os_info = {
            'os_type': system,
            'distro': 'unknown',
            'version': platform.release(),
            'architecture': platform.machine()
        }
        
        if system == 'linux':
            os_info['distro'] = OSDetector._detect_linux_distro()
        elif system == 'darwin':
            os_info['distro'] = 'macos'
            os_info['version'] = platform.mac_ver()[0]
        elif system == 'windows':
            os_info['distro'] = 'windows'
            os_info['version'] = platform.version()
        
        return os_info
    
    @staticmethod
    def _detect_linux_distro() -> str:
        """
        Detect Linux distribution.
        
        Returns:
            String identifying the Linux distribution
        """
        # Check /etc/os-release first (modern standard)
        if os.path.exists('/etc/os-release'):
            try:
                with open('/etc/os-release', 'r') as f:
                    for line in f:
                        if line.startswith('ID='):
                            distro = line.strip().split('=')[1].strip('"\'')
                            return distro.lower()
            except IOError:
                pass
        
        # Fallback to checking specific distribution files
        distro_files = {
            '/etc/debian_version': 'debian',
            '/etc/redhat-release': 'redhat',
            '/etc/arch-release': 'arch',
            '/etc/fedora-release': 'fedora',
            '/etc/centos-release': 'centos',
            '/etc/ubuntu-release': 'ubuntu'
        }
        
        for file_path, distro_name in distro_files.items():
            if os.path.exists(file_path):
                return distro_name
        
        # Final fallback using lsb_release command
        try:
            result = subprocess.run(['lsb_release', '-i'], 
                                  capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                return result.stdout.split(':')[1].strip().lower()
        except (subprocess.TimeoutExpired, FileNotFoundError, IndexError):
            pass
        
        return 'unknown'
    
    @staticmethod
    def is_supported_distro(distro: str) -> bool:
        """
        Check if the distribution is supported by the toolkit.
        
        Args:
            distro: Distribution name
            
        Returns:
            Boolean indicating if distro is supported
        """
        supported = ['debian', 'ubuntu', 'arch', 'manjaro', 'fedora', 'centos', 
                    'rhel', 'macos', 'darwin']
        return distro.lower() in supported


class LogManager:
    """Manages logging configuration and setup."""
    
    DEFAULT_LOG_DIR = '/var/log'
    DEFAULT_LOG_FILE = 'auto_update_tracker.log'
    FALLBACK_LOG_DIR = 'logs'
    
    @staticmethod
    def setup_logging(log_level: str = 'INFO', 
                     log_file: Optional[str] = None,
                     console_output: bool = True) -> logging.Logger:
        """
        Setup logging with both file and console handlers.
        
        Args:
            log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
            log_file: Custom log file path (optional)
            console_output: Whether to output to console
            
        Returns:
            Configured logger instance
        """
        logger = logging.getLogger('system_scripts')
        
        # Clear any existing handlers
        logger.handlers.clear()
        
        # Set log level
        numeric_level = getattr(logging, log_level.upper(), logging.INFO)
        logger.setLevel(numeric_level)
        
        # Create formatter
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        # Setup file handler
        if log_file is None:
            log_file = LogManager._get_log_file_path()
        
        try:
            # Ensure log directory exists
            log_dir = os.path.dirname(log_file)
            os.makedirs(log_dir, exist_ok=True)
            
            file_handler = logging.FileHandler(log_file)
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)
            
        except PermissionError:
            # Fallback to local logs directory
            fallback_path = os.path.join(LogManager.FALLBACK_LOG_DIR, 
                                       LogManager.DEFAULT_LOG_FILE)
            os.makedirs(LogManager.FALLBACK_LOG_DIR, exist_ok=True)
            
            file_handler = logging.FileHandler(fallback_path)
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)
            
            if console_output:
                print(f"Warning: Could not write to {log_file}, "
                      f"using fallback: {fallback_path}")
        
        # Setup console handler
        if console_output:
            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setFormatter(formatter)
            logger.addHandler(console_handler)
        
        return logger
    
    @staticmethod
    def _get_log_file_path() -> str:
        """
        Determine the appropriate log file path based on the OS.
        
        Returns:
            Path to log file
        """
        os_info = OSDetector.get_os_info()
        
        if os_info['os_type'] == 'windows':
            # Windows: use user's Documents folder
            home = os.path.expanduser('~')
            log_dir = os.path.join(home, 'Documents', 'system-scripts', 'logs')
        elif os_info['distro'] == 'macos':
            # macOS: use user's Library/Logs
            home = os.path.expanduser('~')
            log_dir = os.path.join(home, 'Library', 'Logs', 'system-scripts')
        else:
            # Linux: try /var/log first, fallback to local
            log_dir = LogManager.DEFAULT_LOG_DIR
            if not os.access(log_dir, os.W_OK):
                log_dir = LogManager.FALLBACK_LOG_DIR
        
        return os.path.join(log_dir, LogManager.DEFAULT_LOG_FILE)


class CommandRunner:
    """Handles safe execution of system commands."""
    
    @staticmethod
    def run_command(command: List[str], 
                   timeout: int = 300,
                   check_return_code: bool = True,
                   capture_output: bool = True) -> Tuple[int, str, str]:
        """
        Execute a system command safely.
        
        Args:
            command: Command and arguments as list
            timeout: Command timeout in seconds
            check_return_code: Whether to raise exception on non-zero exit
            capture_output: Whether to capture stdout/stderr
            
        Returns:
            Tuple of (return_code, stdout, stderr)
        """
        logger = logging.getLogger('system_scripts')
        
        try:
            logger.debug(f"Executing command: {' '.join(command)}")
            
            result = subprocess.run(
                command,
                timeout=timeout,
                capture_output=capture_output,
                text=True,
                check=False  # We'll handle return codes manually
            )
            
            logger.debug(f"Command completed with return code: {result.returncode}")
            
            if check_return_code and result.returncode != 0:
                error_msg = f"Command failed: {' '.join(command)}\n" \
                           f"Return code: {result.returncode}\n" \
                           f"stderr: {result.stderr}"
                logger.error(error_msg)
                raise subprocess.CalledProcessError(
                    result.returncode, command, result.stdout, result.stderr
                )
            
            return result.returncode, result.stdout, result.stderr
            
        except subprocess.TimeoutExpired as e:
            logger.error(f"Command timed out after {timeout}s: {' '.join(command)}")
            raise e
        except FileNotFoundError as e:
            logger.error(f"Command not found: {command[0]}")
            raise e
    
    @staticmethod
    def is_command_available(command: str) -> bool:
        """
        Check if a command is available in the system PATH.
        
        Args:
            command: Command to check
            
        Returns:
            Boolean indicating if command is available
        """
        return shutil.which(command) is not None
    
    @staticmethod
    def requires_sudo() -> bool:
        """
        Check if the current user has sudo privileges.
        
        Returns:
            Boolean indicating if sudo is available and working
        """
        if os.geteuid() == 0:  # Already running as root
            return False
        
        try:
            # Test sudo with a harmless command
            result = subprocess.run(
                ['sudo', '-n', 'true'],
                capture_output=True,
                timeout=5
            )
            return result.returncode == 0
        except (FileNotFoundError, subprocess.TimeoutExpired):
            return False


class ConfigManager:
    """Manages configuration files and settings."""
    
    DEFAULT_CONFIG_FILE = 'update_config.json'
    
    @staticmethod
    def get_config_path(config_name: str = DEFAULT_CONFIG_FILE) -> str:
        """
        Get the path to a configuration file.
        
        Args:
            config_name: Name of the config file
            
        Returns:
            Path to the configuration file
        """
        # Look for config in standard locations
        search_paths = [
            os.path.join(os.getcwd(), 'configs', config_name),
            os.path.join(os.path.dirname(__file__), '..', 'configs', config_name),
            os.path.join('/etc', 'system-scripts', config_name),
            os.path.join(os.path.expanduser('~'), '.config', 'system-scripts', config_name)
        ]
        
        for path in search_paths:
            if os.path.exists(path):
                return path
        
        # Return the first path as default (will be created if needed)
        return search_paths[0]


def get_script_directory() -> str:
    """
    Get the directory where the script is located.
    
    Returns:
        Absolute path to script directory
    """
    return os.path.dirname(os.path.abspath(__file__))


def ensure_directory_exists(directory: str) -> None:
    """
    Ensure a directory exists, create it if it doesn't.
    
    Args:
        directory: Path to directory
    """
    os.makedirs(directory, exist_ok=True)


def format_bytes(bytes_value: int) -> str:
    """
    Format bytes into human-readable format.
    
    Args:
        bytes_value: Number of bytes
        
    Returns:
        Formatted string (e.g., "1.5 GB")
    """
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if bytes_value < 1024.0:
            return f"{bytes_value:.1f} {unit}"
        bytes_value /= 1024.0
    return f"{bytes_value:.1f} PB"


def get_timestamp() -> str:
    """
    Get current timestamp as formatted string.
    
    Returns:
        Current timestamp in ISO format
    """
    return datetime.now().isoformat()


# Example usage and testing
if __name__ == '__main__':
    # Test OS detection
    os_info = OSDetector.get_os_info()
    print(f"OS Info: {os_info}")
    
    # Test logging setup
    logger = LogManager.setup_logging('DEBUG')
    logger.info("System utilities module loaded successfully")
    
    # Test command runner
    try:
        if OSDetector.get_os_info()['os_type'] == 'windows':
            code, stdout, stderr = CommandRunner.run_command(['echo', 'Hello World'])
        else:
            code, stdout, stderr = CommandRunner.run_command(['echo', 'Hello World'])
        logger.info(f"Test command output: {stdout.strip()}")
    except Exception as e:
        logger.error(f"Test command failed: {e}")