#!/usr/bin/env python3
"""
Debian/Ubuntu automatic update script using unattended-upgrades.
Handles package updates, security patches, and system maintenance.

Author: Loyd Johnson
Date: November 2025
"""

import os
import sys
import subprocess
import json
from datetime import datetime
from typing import Dict, List, Optional
import logging

# Add parent directories to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))
from utils.system_utils import OSDetector, CommandRunner, LogManager
from scripts.common.health_checks import HealthChecker


class DebianUpdater:
    """Handles automatic updates for Debian/Ubuntu systems."""
    
    def __init__(self, config: Optional[Dict] = None, logger: Optional[logging.Logger] = None):
        """
        Initialize the Debian updater.
        
        Args:
            config: Configuration dictionary
            logger: Logger instance
        """
        self.logger = logger or LogManager.setup_logging()
        self.os_info = OSDetector.get_os_info()
        
        # Validate that this is a Debian-based system
        if self.os_info['distro'] not in ['debian', 'ubuntu']:
            raise Exception(f"This script is for Debian/Ubuntu systems only. "
                          f"Detected: {self.os_info['distro']}")
        
        # Default configuration
        self.config = {
            'enable_auto_updates': True,
            'auto_reboot': False,
            'auto_reboot_time': '02:00',
            'update_package_lists': True,
            'unattended_upgrade': True,
            'auto_remove': True,
            'auto_clean': True,
            'mail_on_error': False,
            'mail_to': 'root',
            'allowed_origins': [
                '${distro_id}:${distro_codename}-security',
                '${distro_id}ESMApps:${distro_codename}-apps-security',
                '${distro_id}ESM:${distro_codename}-infra-security'
            ],
            'package_blacklist': [],
            'pre_update_health_check': True,
            'post_update_health_check': True,
            'backup_important_configs': True
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
        self.logger.info("Starting Debian/Ubuntu update cycle")
        
        results = {
            'timestamp': datetime.now().isoformat(),
            'os_info': self.os_info,
            'pre_update_health': None,
            'package_list_update': None,
            'available_updates': None,
            'update_execution': None,
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
            
            # Update package lists
            if self.config['update_package_lists']:
                self.logger.info("Updating package lists")
                results['package_list_update'] = self._update_package_lists()
            
            # Get available updates
            self.logger.info("Checking for available updates")
            results['available_updates'] = self._check_available_updates()
            
            if not results['available_updates']['has_updates']:
                self.logger.info("No updates available")
                results['overall_status'] = 'no_updates'
                return results
            
            # Backup important configurations
            if self.config['backup_important_configs']:
                self.logger.info("Backing up important configurations")
                self._backup_configs()
            
            # Run unattended upgrades
            if self.config['unattended_upgrade']:
                self.logger.info("Running unattended upgrades")
                results['update_execution'] = self._run_unattended_upgrade()
            
            # Cleanup
            if self.config['auto_remove'] or self.config['auto_clean']:
                self.logger.info("Running cleanup tasks")
                results['cleanup'] = self._cleanup_system()
            
            # Check if reboot is required
            results['reboot_required'] = self._check_reboot_required()
            
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
    
    def _update_package_lists(self) -> Dict[str, any]:
        """
        Update the package lists using apt update.
        
        Returns:
            Dictionary with update results
        """
        try:
            # Run apt update
            code, stdout, stderr = CommandRunner.run_command(
                ['sudo', 'apt', 'update'],
                timeout=300
            )
            
            return {
                'status': 'success',
                'return_code': code,
                'stdout': stdout,
                'stderr': stderr
            }
            
        except subprocess.CalledProcessError as e:
            self.logger.error(f"Failed to update package lists: {e}")
            return {
                'status': 'failed',
                'error': str(e),
                'return_code': e.returncode
            }
    
    def _check_available_updates(self) -> Dict[str, any]:
        """
        Check for available package updates.
        
        Returns:
            Dictionary with available updates information
        """
        try:
            # Get list of upgradeable packages
            code, stdout, stderr = CommandRunner.run_command(
                ['apt', 'list', '--upgradable'],
                check_return_code=False
            )
            
            # Parse output to get package list
            lines = stdout.strip().split('\n')[1:]  # Skip header
            upgradeable_packages = []
            
            for line in lines:
                if line.strip() and '/' in line:
                    parts = line.split()
                    if len(parts) >= 2:
                        package_name = parts[0].split('/')[0]
                        upgradeable_packages.append(package_name)
            
            # Get security updates specifically
            security_updates = self._get_security_updates()
            
            return {
                'has_updates': len(upgradeable_packages) > 0,
                'total_updates': len(upgradeable_packages),
                'security_updates': len(security_updates),
                'packages': upgradeable_packages[:20],  # Limit to first 20
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
            # Use unattended-upgrade --dry-run to see what would be upgraded
            code, stdout, stderr = CommandRunner.run_command(
                ['sudo', 'unattended-upgrade', '--dry-run', '--debug'],
                timeout=120,
                check_return_code=False
            )
            
            security_packages = []
            lines = stdout.split('\n')
            
            for line in lines:
                if 'security' in line.lower() and 'upgrade' in line.lower():
                    # Extract package name from debug output
                    # This is a simplified parser - actual format may vary
                    words = line.split()
                    for word in words:
                        if '/' in word and not word.startswith('/'):
                            package = word.split('/')[0]
                            if package not in security_packages:
                                security_packages.append(package)
            
            return security_packages
            
        except Exception as e:
            self.logger.warning(f"Could not determine security updates: {e}")
            return []
    
    def _run_unattended_upgrade(self) -> Dict[str, any]:
        """
        Run unattended-upgrade to install updates.
        
        Returns:
            Dictionary with upgrade results
        """
        try:
            # Ensure unattended-upgrades is configured
            self._configure_unattended_upgrades()
            
            # Run unattended-upgrade
            code, stdout, stderr = CommandRunner.run_command(
                ['sudo', 'unattended-upgrade', '--verbose'],
                timeout=1800  # 30 minutes
            )
            
            return {
                'status': 'success',
                'return_code': code,
                'stdout': stdout,
                'stderr': stderr
            }
            
        except subprocess.CalledProcessError as e:
            self.logger.error(f"Unattended upgrade failed: {e}")
            return {
                'status': 'failed',
                'error': str(e),
                'return_code': e.returncode,
                'stdout': e.stdout if hasattr(e, 'stdout') else '',
                'stderr': e.stderr if hasattr(e, 'stderr') else ''
            }
    
    def _configure_unattended_upgrades(self):
        """Configure unattended-upgrades based on our settings."""
        config_content = f'''// Automatically upgrade packages from these origin patterns
Unattended-Upgrade::Allowed-Origins {{
{chr(10).join([f'    "{origin}";' for origin in self.config['allowed_origins']])}
}};

// List of packages to not update (regexp are supported)
Unattended-Upgrade::Package-Blacklist {{
{chr(10).join([f'    "{pkg}";' for pkg in self.config['package_blacklist']])}
}};

// Auto-remove unused dependencies
Unattended-Upgrade::Remove-Unused-Dependencies "{str(self.config['auto_remove']).lower()}";

// Automatically reboot if required
Unattended-Upgrade::Automatic-Reboot "{str(self.config['auto_reboot']).lower()}";

// Automatically reboot time
Unattended-Upgrade::Automatic-Reboot-Time "{self.config['auto_reboot_time']}";

// Send email on errors
Unattended-Upgrade::Mail "{self.config['mail_to'] if self.config['mail_on_error'] else ''}";
'''
        
        # Write configuration file
        config_path = '/etc/apt/apt.conf.d/50unattended-upgrades'
        temp_path = '/tmp/50unattended-upgrades'
        
        try:
            with open(temp_path, 'w') as f:
                f.write(config_content)
            
            # Copy to proper location with sudo
            CommandRunner.run_command(['sudo', 'cp', temp_path, config_path])
            CommandRunner.run_command(['sudo', 'chmod', '644', config_path])
            
            # Clean up temp file
            os.unlink(temp_path)
            
            self.logger.info("Unattended-upgrades configuration updated")
            
        except Exception as e:
            self.logger.warning(f"Could not update unattended-upgrades config: {e}")
    
    def _cleanup_system(self) -> Dict[str, any]:
        """
        Clean up the system by removing unused packages and cleaning cache.
        
        Returns:
            Dictionary with cleanup results
        """
        results = {}
        
        try:
            # Auto-remove unused packages
            if self.config['auto_remove']:
                self.logger.info("Removing unused packages")
                code, stdout, stderr = CommandRunner.run_command(
                    ['sudo', 'apt', 'autoremove', '-y'],
                    timeout=300
                )
                results['autoremove'] = {
                    'status': 'success',
                    'return_code': code,
                    'output': stdout
                }
            
            # Clean package cache
            if self.config['auto_clean']:
                self.logger.info("Cleaning package cache")
                code, stdout, stderr = CommandRunner.run_command(
                    ['sudo', 'apt', 'autoclean'],
                    timeout=300
                )
                results['autoclean'] = {
                    'status': 'success',
                    'return_code': code,
                    'output': stdout
                }
            
            return results
            
        except subprocess.CalledProcessError as e:
            self.logger.error(f"Cleanup failed: {e}")
            results['error'] = str(e)
            return results
    
    def _check_reboot_required(self) -> bool:
        """
        Check if a reboot is required after updates.
        
        Returns:
            Boolean indicating if reboot is required
        """
        reboot_required_file = '/var/run/reboot-required'
        return os.path.exists(reboot_required_file)
    
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
                '/etc/apt/sources.list',
                '/etc/apt/sources.list.d/',
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
    
    parser = argparse.ArgumentParser(description='Debian/Ubuntu automatic updater')
    parser.add_argument('--config', help='Path to configuration file')
    parser.add_argument('--dry-run', action='store_true', 
                       help='Show what would be done without making changes')
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
    
    # Override for dry run
    if args.dry_run:
        logger.info("DRY RUN MODE - No changes will be made")
        config['unattended_upgrade'] = False
        config['auto_reboot'] = False
    
    try:
        # Create updater and run update cycle
        updater = DebianUpdater(config, logger)
        results = updater.run_update_cycle()
        
        # Print summary
        print(f"\n=== Debian/Ubuntu Update Results ===")
        print(f"Status: {results['overall_status'].upper()}")
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