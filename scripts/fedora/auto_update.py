#!/usr/bin/env python3
"""
Fedora/RHEL automatic update script using dnf.
Handles system updates, security patches, and maintenance tasks.

Author: Loyd Johnson
Date: November 2025
"""

import os
import sys
import subprocess
import json
from datetime import datetime
from typing import Dict, List, Optional, Tuple
import logging

# Add parent directories to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))
from utils.system_utils import OSDetector, CommandRunner, LogManager
from scripts.common.health_checks import HealthChecker


class FedoraUpdater:
    """Handles automatic updates for Fedora/RHEL systems."""
    
    def __init__(self, config: Optional[Dict] = None, logger: Optional[logging.Logger] = None):
        """
        Initialize the Fedora updater.
        
        Args:
            config: Configuration dictionary
            logger: Logger instance
        """
        self.logger = logger or LogManager.setup_logging()
        self.os_info = OSDetector.get_os_info()
        
        # Validate that this is a Fedora/RHEL-based system
        supported_distros = ['fedora', 'rhel', 'centos', 'rocky', 'alma', 'scientific']
        if self.os_info['distro'] not in supported_distros:
            raise Exception(f"This script is for Fedora/RHEL-based systems only. "
                          f"Detected: {self.os_info['distro']}")
        
        # Determine package manager (dnf or yum)
        self.package_manager = self._detect_package_manager()
        
        # Default configuration
        self.config = {
            'update_system': True,
            'install_security_only': False,
            'auto_reboot': False,
            'auto_reboot_time': '02:00',
            'enable_auto_updates': False,
            'exclude_packages': [],
            'clean_cache': True,
            'remove_old_kernels': True,
            'max_kernels_to_keep': 3,
            'update_firmware': False,
            'check_repositories': True,
            'backup_important_configs': True,
            'pre_update_health_check': True,
            'post_update_health_check': True,
            'timeout_minutes': 60
        }
        
        if config:
            self.config.update(config)
        
        self.health_checker = HealthChecker(self.logger)
    
    def run_update_cycle(self) -> Dict[str, any]:
        """
        Run a complete update cycle.
        
        Returns:
            Dictionary with update results
        """
        self.logger.info(f"Starting {self.os_info['distro']} update cycle using {self.package_manager}")
        
        results = {
            'timestamp': datetime.now().isoformat(),
            'os_info': self.os_info,
            'package_manager': self.package_manager,
            'pre_update_health': None,
            'repository_refresh': None,
            'available_updates': None,
            'system_update': None,
            'firmware_update': None,
            'cleanup': None,
            'post_update_health': None,
            'reboot_required': False,
            'overall_status': 'success'
        }
        
        try:
            # Pre-update health check
            if self.config['pre_update_health_check']:
                self.logger.info("Running pre-update health check")
                results['pre_update_health'] = self.health_checker.run_all_checks()
                
                if results['pre_update_health']['overall_status'] == 'critical':
                    self.logger.error("Pre-update health check failed critically. Aborting update.")
                    results['overall_status'] = 'aborted'
                    return results
            
            # Backup important configurations
            if self.config['backup_important_configs']:
                self.logger.info("Backing up important configurations")
                self._backup_configs()
            
            # Check and refresh repositories
            if self.config['check_repositories']:
                self.logger.info("Refreshing package repositories")
                results['repository_refresh'] = self._refresh_repositories()
            
            # Check for available updates
            self.logger.info("Checking for available updates")
            results['available_updates'] = self._check_available_updates()
            
            if not results['available_updates']['has_updates']:
                self.logger.info("No updates available")
                results['overall_status'] = 'no_updates'
            else:
                # Update system packages
                if self.config['update_system']:
                    self.logger.info("Updating system packages")
                    results['system_update'] = self._update_system_packages()
                
                # Update firmware if configured
                if self.config['update_firmware']:
                    self.logger.info("Updating firmware")
                    results['firmware_update'] = self._update_firmware()
            
            # Cleanup tasks
            if (self.config['clean_cache'] or 
                self.config['remove_old_kernels']):
                self.logger.info("Running cleanup tasks")
                results['cleanup'] = self._cleanup_system()
            
            # Check if reboot is required
            results['reboot_required'] = self._check_reboot_required()
            
            # Configure automatic updates if requested
            if self.config['enable_auto_updates']:
                self.logger.info("Configuring automatic updates")
                self._configure_auto_updates()
            
            # Post-update health check
            if self.config['post_update_health_check']:
                self.logger.info("Running post-update health check")
                results['post_update_health'] = self.health_checker.run_all_checks()
            
            # Handle automatic reboot if configured
            if results['reboot_required'] and self.config['auto_reboot']:
                self._schedule_reboot()
            
        except Exception as e:
            self.logger.error(f"Update cycle failed: {e}")
            results['overall_status'] = 'failed'
            results['error'] = str(e)
        
        self.logger.info(f"Update cycle completed with status: {results['overall_status']}")
        return results
    
    def _detect_package_manager(self) -> str:
        """
        Detect available package manager (dnf or yum).
        
        Returns:
            Name of package manager to use
        """
        if CommandRunner.is_command_available('dnf'):
            return 'dnf'
        elif CommandRunner.is_command_available('yum'):
            return 'yum'
        else:
            raise Exception("Neither dnf nor yum package manager found")
    
    def _refresh_repositories(self) -> Dict[str, any]:
        """
        Refresh package repositories and check for issues.
        
        Returns:
            Dictionary with repository refresh results
        """
        try:
            # Clean metadata cache
            code, stdout, stderr = CommandRunner.run_command(
                ['sudo', self.package_manager, 'clean', 'metadata'],
                timeout=120
            )
            
            # Refresh repository metadata
            code, stdout, stderr = CommandRunner.run_command(
                ['sudo', self.package_manager, 'makecache'],
                timeout=300
            )
            
            # Check repository status
            repo_status = self._check_repository_status()
            
            return {
                'status': 'success',
                'return_code': code,
                'repository_status': repo_status,
                'stdout': stdout,
                'stderr': stderr
            }
            
        except subprocess.CalledProcessError as e:
            self.logger.error(f"Failed to refresh repositories: {e}")
            return {
                'status': 'failed',
                'error': str(e),
                'return_code': e.returncode
            }
    
    def _check_repository_status(self) -> Dict[str, any]:
        """
        Check the status of configured repositories.
        
        Returns:
            Dictionary with repository information
        """
        try:
            # List enabled repositories
            code, stdout, stderr = CommandRunner.run_command(
                [self.package_manager, 'repolist', 'enabled'],
                check_return_code=False
            )
            
            enabled_repos = []
            if code == 0:
                lines = stdout.strip().split('\n')[1:]  # Skip header
                for line in lines:
                    if line.strip() and not line.startswith('repo id'):
                        parts = line.split()
                        if len(parts) >= 1:
                            enabled_repos.append(parts[0])
            
            return {
                'enabled_repositories': len(enabled_repos),
                'repositories': enabled_repos[:10]  # Limit output
            }
            
        except Exception as e:
            self.logger.warning(f"Could not check repository status: {e}")
            return {'error': str(e)}
    
    def _check_available_updates(self) -> Dict[str, any]:
        """
        Check for available package updates.
        
        Returns:
            Dictionary with available updates information
        """
        try:
            # Check for all updates
            cmd = [self.package_manager, 'check-update']
            code, stdout, stderr = CommandRunner.run_command(
                cmd, check_return_code=False, timeout=300
            )
            
            # Parse output to get package list
            all_updates = []
            security_updates = []
            
            if code == 100:  # dnf/yum returns 100 when updates are available
                lines = stdout.strip().split('\n')
                for line in lines:
                    if line.strip() and not line.startswith('Last metadata') and '.' in line:
                        parts = line.split()
                        if len(parts) >= 2:
                            package_name = parts[0].split('.')[0]
                            all_updates.append(package_name)
            
            # Check for security updates specifically
            security_updates = self._get_security_updates()
            
            return {
                'has_updates': len(all_updates) > 0,
                'total_updates': len(all_updates),
                'security_updates': len(security_updates),
                'packages': all_updates[:20],  # Limit to first 20
                'security_packages': security_updates
            }
            
        except Exception as e:
            self.logger.error(f"Failed to check available updates: {e}")
            return {
                'has_updates': False,
                'error': str(e)
            }
    
    def _get_security_updates(self) -> List[str]:
        """
        Get list of available security updates.
        
        Returns:
            List of packages with security updates
        """
        try:
            # Use dnf/yum updateinfo to get security updates
            if self.package_manager == 'dnf':
                code, stdout, stderr = CommandRunner.run_command(
                    ['dnf', 'updateinfo', 'list', 'security'],
                    check_return_code=False,
                    timeout=120
                )
            else:  # yum
                code, stdout, stderr = CommandRunner.run_command(
                    ['yum', 'updateinfo', 'list', 'security'],
                    check_return_code=False,
                    timeout=120
                )
            
            security_packages = []
            if code == 0:
                lines = stdout.strip().split('\n')
                for line in lines:
                    if line.strip() and not line.startswith('Last metadata'):
                        parts = line.split()
                        if len(parts) >= 3:
                            # Extract package name from update info
                            package = parts[2].split('.')[0] if '.' in parts[2] else parts[2]
                            if package not in security_packages:
                                security_packages.append(package)
            
            return security_packages
            
        except Exception as e:
            self.logger.warning(f"Could not determine security updates: {e}")
            return []
    
    def _update_system_packages(self) -> Dict[str, any]:
        """
        Update system packages using dnf/yum.
        
        Returns:
            Dictionary with update results
        """
        try:
            # Build update command
            if self.config['install_security_only']:
                cmd = ['sudo', self.package_manager, 'update', '--security', '-y']
            else:
                cmd = ['sudo', self.package_manager, 'update', '-y']
            
            # Add excluded packages
            if self.config['exclude_packages']:
                for pkg in self.config['exclude_packages']:
                    cmd.extend(['--exclude', pkg])
            
            # Run the update
            timeout = self.config['timeout_minutes'] * 60
            code, stdout, stderr = CommandRunner.run_command(
                cmd, timeout=timeout
            )
            
            return {
                'status': 'success',
                'return_code': code,
                'stdout': stdout,
                'stderr': stderr,
                'security_only': self.config['install_security_only']
            }
            
        except subprocess.CalledProcessError as e:
            self.logger.error(f"System package update failed: {e}")
            return {
                'status': 'failed',
                'error': str(e),
                'return_code': e.returncode,
                'stdout': e.stdout if hasattr(e, 'stdout') else '',
                'stderr': e.stderr if hasattr(e, 'stderr') else ''
            }
    
    def _update_firmware(self) -> Dict[str, any]:
        """
        Update system firmware using fwupd.
        
        Returns:
            Dictionary with firmware update results
        """
        try:
            if not CommandRunner.is_command_available('fwupdmgr'):
                return {'status': 'skipped', 'reason': 'fwupdmgr not available'}
            
            # Refresh firmware metadata
            code, stdout, stderr = CommandRunner.run_command(
                ['sudo', 'fwupdmgr', 'refresh'],
                timeout=120,
                check_return_code=False
            )
            
            # Get firmware updates
            code, stdout, stderr = CommandRunner.run_command(
                ['fwupdmgr', 'get-updates'],
                timeout=60,
                check_return_code=False
            )
            
            if code == 0 and 'No updates' not in stdout:
                # Apply firmware updates
                code, stdout, stderr = CommandRunner.run_command(
                    ['sudo', 'fwupdmgr', 'update', '--assume-yes'],
                    timeout=600
                )
                
                return {
                    'status': 'success',
                    'updates_applied': True,
                    'return_code': code,
                    'output': stdout
                }
            else:
                return {
                    'status': 'success',
                    'updates_applied': False,
                    'note': 'No firmware updates available'
                }
            
        except Exception as e:
            self.logger.warning(f"Firmware update failed: {e}")
            return {'status': 'failed', 'error': str(e)}
    
    def _cleanup_system(self) -> Dict[str, any]:
        """
        Clean up the system by removing old packages and cleaning cache.
        
        Returns:
            Dictionary with cleanup results
        """
        results = {}
        
        try:
            # Clean package cache
            if self.config['clean_cache']:
                self.logger.info("Cleaning package cache")
                code, stdout, stderr = CommandRunner.run_command(
                    ['sudo', self.package_manager, 'clean', 'all'],
                    timeout=300
                )
                results['cache_cleanup'] = {
                    'status': 'success',
                    'return_code': code,
                    'output': stdout
                }
            
            # Remove old kernels
            if self.config['remove_old_kernels']:
                self.logger.info("Removing old kernels")
                results['kernel_cleanup'] = self._remove_old_kernels()
            
            # Auto-remove orphaned packages (dnf only)
            if self.package_manager == 'dnf':
                self.logger.info("Removing orphaned packages")
                code, stdout, stderr = CommandRunner.run_command(
                    ['sudo', 'dnf', 'autoremove', '-y'],
                    timeout=300,
                    check_return_code=False
                )
                results['autoremove'] = {
                    'status': 'success' if code == 0 else 'warning',
                    'return_code': code,
                    'output': stdout
                }
            
            return results
            
        except subprocess.CalledProcessError as e:
            self.logger.error(f"Cleanup failed: {e}")
            results['error'] = str(e)
            return results
    
    def _remove_old_kernels(self) -> Dict[str, any]:
        """
        Remove old kernel packages, keeping the specified number.
        
        Returns:
            Dictionary with kernel cleanup results
        """
        try:
            # Get installed kernels
            code, stdout, stderr = CommandRunner.run_command(
                [self.package_manager, 'list', 'installed', 'kernel'],
                check_return_code=False
            )
            
            if code != 0:
                return {'status': 'skipped', 'reason': 'Could not list installed kernels'}
            
            # Parse kernel list
            kernels = []
            lines = stdout.strip().split('\n')
            for line in lines:
                if 'kernel.' in line and not line.startswith('Installed'):
                    parts = line.split()
                    if len(parts) >= 1:
                        kernels.append(parts[0])
            
            # Keep the most recent kernels
            if len(kernels) > self.config['max_kernels_to_keep']:
                kernels_to_remove = kernels[:-self.config['max_kernels_to_keep']]
                
                # Remove old kernels
                cmd = ['sudo', self.package_manager, 'remove', '-y'] + kernels_to_remove
                code, stdout, stderr = CommandRunner.run_command(cmd, timeout=300)
                
                return {
                    'status': 'success',
                    'kernels_removed': len(kernels_to_remove),
                    'kernels_kept': self.config['max_kernels_to_keep'],
                    'removed_packages': kernels_to_remove
                }
            else:
                return {
                    'status': 'success',
                    'kernels_removed': 0,
                    'note': f"Only {len(kernels)} kernels installed, keeping all"
                }
            
        except Exception as e:
            self.logger.warning(f"Could not remove old kernels: {e}")
            return {'status': 'failed', 'error': str(e)}
    
    def _check_reboot_required(self) -> bool:
        """
        Check if a reboot is required after updates.
        
        Returns:
            Boolean indicating if reboot is required
        """
        # Check if needs-restarting command is available
        if CommandRunner.is_command_available('needs-restarting'):
            try:
                code, stdout, stderr = CommandRunner.run_command(
                    ['needs-restarting', '-r'],
                    check_return_code=False
                )
                return code == 1  # needs-restarting returns 1 if reboot needed
            except Exception:
                pass
        
        # Fallback: check for kernel updates
        try:
            current_kernel = os.uname().release
            code, stdout, stderr = CommandRunner.run_command(
                [self.package_manager, 'list', 'installed', 'kernel'],
                check_return_code=False
            )
            
            if code == 0:
                latest_kernel = None
                lines = stdout.strip().split('\n')
                for line in lines:
                    if 'kernel.' in line:
                        parts = line.split()
                        if len(parts) >= 2:
                            version = parts[1]
                            if version > (latest_kernel or ''):
                                latest_kernel = version
                
                return latest_kernel and latest_kernel not in current_kernel
            
        except Exception as e:
            self.logger.warning(f"Could not determine reboot requirement: {e}")
        
        return False
    
    def _configure_auto_updates(self):
        """Configure automatic updates using dnf-automatic."""
        try:
            if not CommandRunner.is_command_available('dnf-automatic'):
                self.logger.warning("dnf-automatic not available, cannot configure auto updates")
                return
            
            # Install dnf-automatic if not present
            CommandRunner.run_command(
                ['sudo', 'dnf', 'install', '-y', 'dnf-automatic'],
                timeout=300
            )
            
            # Enable and start dnf-automatic timer
            CommandRunner.run_command(
                ['sudo', 'systemctl', 'enable', '--now', 'dnf-automatic.timer']
            )
            
            self.logger.info("Automatic updates configured successfully")
            
        except Exception as e:
            self.logger.warning(f"Could not configure automatic updates: {e}")
    
    def _schedule_reboot(self):
        """Schedule a system reboot."""
        try:
            reboot_time = self.config['auto_reboot_time']
            self.logger.warning(f"Scheduling system reboot at {reboot_time}")
            
            # Schedule reboot using at command
            CommandRunner.run_command([
                'sudo', 'sh', '-c', 
                f'echo "systemctl reboot" | at {reboot_time}'
            ])
            
        except Exception as e:
            self.logger.error(f"Failed to schedule reboot: {e}")
    
    def _backup_configs(self):
        """Backup important configuration files before updates."""
        try:
            backup_dir = f"/tmp/config_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            os.makedirs(backup_dir, exist_ok=True)
            
            # Important files to backup
            important_files = [
                '/etc/dnf/dnf.conf',
                '/etc/yum.conf',
                '/etc/yum.repos.d/',
                '/etc/ssh/sshd_config',
                '/etc/fstab',
                '/etc/crontab'
            ]
            
            for file_path in important_files:
                if os.path.exists(file_path):
                    try:
                        CommandRunner.run_command([
                            'sudo', 'cp', '-r', file_path, backup_dir
                        ])
                    except Exception as e:
                        self.logger.warning(f"Could not backup {file_path}: {e}")
            
            self.logger.info(f"Configuration backup created in {backup_dir}")
            
        except Exception as e:
            self.logger.warning(f"Could not create configuration backup: {e}")


def main():
    """Main function for standalone execution."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Fedora/RHEL automatic updater')
    parser.add_argument('--config', help='Path to configuration file')
    parser.add_argument('--dry-run', action='store_true', 
                       help='Show what would be done without making changes')
    parser.add_argument('--security-only', action='store_true',
                       help='Install security updates only')
    parser.add_argument('--verbose', action='store_true',
                       help='Enable verbose logging')
    
    args = parser.parse_args()
    
    # Setup logging
    log_level = 'DEBUG' if args.verbose else 'INFO'
    logger = LogManager.setup_logging(log_level)
    
    # Load configuration
    config = {}
    if args.config and os.path.exists(args.config):
        try:
            with open(args.config, 'r') as f:
                config = json.load(f)
        except Exception as e:
            logger.error(f"Failed to load config file: {e}")
            sys.exit(1)
    
    # Command line overrides
    if args.security_only:
        config['install_security_only'] = True
    
    # Override for dry run
    if args.dry_run:
        logger.info("DRY RUN MODE - No changes will be made")
        config['update_system'] = False
        config['auto_reboot'] = False
        config['clean_cache'] = False
        config['remove_old_kernels'] = False
    
    try:
        # Create updater and run update cycle
        updater = FedoraUpdater(config, logger)
        results = updater.run_update_cycle()
        
        # Print summary
        print(f"\n=== {results['os_info']['distro'].title()} Update Results ===")
        print(f"Status: {results['overall_status'].upper()}")
        print(f"Package Manager: {results['package_manager']}")
        print(f"Timestamp: {results['timestamp']}")
        
        if 'available_updates' in results and results['available_updates']:
            updates = results['available_updates']
            print(f"Total Updates: {updates.get('total_updates', 0)}")
            print(f"Security Updates: {updates.get('security_updates', 0)}")
        
        if results.get('reboot_required'):
            print("⚠️  REBOOT REQUIRED")
        
        # Exit with appropriate code
        sys.exit(0 if results['overall_status'] in ['success', 'no_updates'] else 1)
        
    except Exception as e:
        logger.error(f"Update process failed: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()