#!/usr/bin/env python3
"""
macOS automatic update script using softwareupdate and Homebrew.
Handles system updates, App Store apps, and Homebrew packages.

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


class MacOSUpdater:
    """Handles automatic updates for macOS systems."""
    
    def __init__(self, config: Optional[Dict] = None, logger: Optional[logging.Logger] = None):
        """
        Initialize the macOS updater.
        
        Args:
            config: Configuration dictionary
            logger: Logger instance
        """
        self.logger = logger or LogManager.setup_logging()
        self.os_info = OSDetector.get_os_info()
        
        # Validate that this is a macOS system
        if self.os_info['os_type'] != 'darwin':
            raise Exception(f"This script is for macOS systems only. "
                          f"Detected: {self.os_info['os_type']}")
        
        # Default configuration
        self.config = {
            'update_system': True,
            'update_app_store': True,
            'update_homebrew': True,
            'install_recommended_updates': True,
            'auto_restart': False,
            'restart_delay_minutes': 5,
            'homebrew_upgrade_all': True,
            'homebrew_cleanup': True,
            'backup_homebrew_bundle': True,
            'check_xcode_tools': True,
            'pre_update_health_check': True,
            'post_update_health_check': True,
            'timeout_minutes': 60,
            'excluded_homebrew_packages': []
        }
        
        if config:
            self.config.update(config)
        
        self.health_checker = HealthChecker(self.logger)
        self.homebrew_available = self._check_homebrew_available()
    
    def run_update_cycle(self) -> Dict[str, any]:
        """
        Run a complete update cycle.
        
        Returns:
            Dictionary with update results
        """
        self.logger.info("Starting macOS update cycle")
        
        results = {
            'timestamp': datetime.now().isoformat(),
            'os_info': self.os_info,
            'pre_update_health': None,
            'xcode_tools_check': None,
            'available_updates': None,
            'system_update': None,
            'app_store_update': None,
            'homebrew_update': None,
            'post_update_health': None,
            'restart_required': False,
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
            
            # Check Xcode Command Line Tools
            if self.config['check_xcode_tools']:
                self.logger.info("Checking Xcode Command Line Tools")
                results['xcode_tools_check'] = self._check_xcode_tools()
            
            # Check for available updates
            self.logger.info("Checking for available updates")
            results['available_updates'] = self._check_available_updates()
            
            has_any_updates = False
            
            # System updates
            if (self.config['update_system'] and 
                results['available_updates'].get('system_updates', 0) > 0):
                self.logger.info("Installing system updates")
                results['system_update'] = self._update_system()
                has_any_updates = True
            
            # App Store updates
            if (self.config['update_app_store'] and 
                results['available_updates'].get('app_store_updates', 0) > 0):
                self.logger.info("Installing App Store updates")
                results['app_store_update'] = self._update_app_store()
                has_any_updates = True
            
            # Homebrew updates
            if (self.config['update_homebrew'] and self.homebrew_available):
                self.logger.info("Updating Homebrew packages")
                results['homebrew_update'] = self._update_homebrew()
                has_any_updates = True
            
            if not has_any_updates:
                self.logger.info("No updates were performed")
                results['overall_status'] = 'no_updates'
            
            # Check if restart is required
            results['restart_required'] = self._check_restart_required()
            
            # Handle automatic restart if configured
            if results['restart_required'] and self.config['auto_restart']:
                self._schedule_restart()
            
            # Post-update health check
            if self.config['post_update_health_check']:
                self.logger.info("Running post-update health check")
                results['post_update_health'] = self.health_checker.run_all_checks()
            
        except Exception as e:
            self.logger.error(f"Update cycle failed: {e}")
            results['overall_status'] = 'failed'
            results['error'] = str(e)
        
        self.logger.info(f"Update cycle completed with status: {results['overall_status']}")
        return results
    
    def _check_homebrew_available(self) -> bool:
        """
        Check if Homebrew is available.
        
        Returns:
            Boolean indicating if Homebrew is available
        """
        return CommandRunner.is_command_available('brew')
    
    def _check_xcode_tools(self) -> Dict[str, any]:
        """
        Check and update Xcode Command Line Tools if needed.
        
        Returns:
            Dictionary with Xcode tools status
        """
        try:
            # Check if Xcode tools are installed
            code, stdout, stderr = CommandRunner.run_command(
                ['xcode-select', '-p'],
                check_return_code=False
            )
            
            if code != 0:
                self.logger.info("Xcode Command Line Tools not found, attempting to install")
                
                # Trigger installation
                code, stdout, stderr = CommandRunner.run_command(
                    ['xcode-select', '--install'],
                    check_return_code=False,
                    timeout=10
                )
                
                return {
                    'status': 'installation_triggered',
                    'note': 'Xcode Command Line Tools installation initiated. Manual approval may be required.'
                }
            
            return {
                'status': 'installed',
                'path': stdout.strip()
            }
            
        except Exception as e:
            self.logger.warning(f"Could not check Xcode tools: {e}")
            return {'status': 'unknown', 'error': str(e)}
    
    def _check_available_updates(self) -> Dict[str, any]:
        """
        Check for available updates across all sources.
        
        Returns:
            Dictionary with available updates information
        """
        results = {
            'system_updates': 0,
            'app_store_updates': 0,
            'homebrew_updates': 0,
            'system_packages': [],
            'app_store_packages': [],
            'homebrew_packages': []
        }
        
        try:
            # Check system updates
            system_updates = self._check_system_updates()
            results.update(system_updates)
            
            # Check App Store updates
            if self.config['update_app_store']:
                app_store_updates = self._check_app_store_updates()
                results['app_store_updates'] = app_store_updates.get('count', 0)
                results['app_store_packages'] = app_store_updates.get('packages', [])
            
            # Check Homebrew updates
            if self.config['update_homebrew'] and self.homebrew_available:
                homebrew_updates = self._check_homebrew_updates()
                results['homebrew_updates'] = homebrew_updates.get('count', 0)
                results['homebrew_packages'] = homebrew_updates.get('packages', [])
            
            return results
            
        except Exception as e:
            self.logger.error(f"Failed to check available updates: {e}")
            results['error'] = str(e)
            return results
    
    def _check_system_updates(self) -> Dict[str, any]:
        """
        Check for macOS system updates.
        
        Returns:
            Dictionary with system update information
        """
        try:
            # List available updates
            code, stdout, stderr = CommandRunner.run_command(
                ['softwareupdate', '--list'],
                timeout=300,
                check_return_code=False
            )
            
            updates = []
            lines = stdout.split('\n')
            
            for line in lines:
                line = line.strip()
                if line.startswith('*'):
                    # Extract update name
                    if ':' in line:
                        update_name = line.split(':', 1)[0].replace('*', '').strip()
                        updates.append(update_name)
                elif line.startswith('Title:'):
                    # Alternative format
                    update_name = line.replace('Title:', '').strip()
                    updates.append(update_name)
            
            return {
                'system_updates': len(updates),
                'system_packages': updates
            }
            
        except Exception as e:
            self.logger.warning(f"Could not check system updates: {e}")
            return {
                'system_updates': 0,
                'system_packages': [],
                'error': str(e)
            }
    
    def _check_app_store_updates(self) -> Dict[str, any]:
        """
        Check for App Store updates using mas (if available).
        
        Returns:
            Dictionary with App Store update information
        """
        try:
            if not CommandRunner.is_command_available('mas'):
                return {
                    'count': 0,
                    'packages': [],
                    'note': 'mas (Mac App Store CLI) not available'
                }
            
            # List outdated apps
            code, stdout, stderr = CommandRunner.run_command(
                ['mas', 'outdated'],
                timeout=120,
                check_return_code=False
            )
            
            updates = []
            if code == 0 and stdout.strip():
                lines = stdout.strip().split('\n')
                for line in lines:
                    if line.strip():
                        parts = line.split()
                        if len(parts) >= 2:
                            app_name = ' '.join(parts[1:])
                            updates.append(app_name)
            
            return {
                'count': len(updates),
                'packages': updates
            }
            
        except Exception as e:
            self.logger.warning(f"Could not check App Store updates: {e}")
            return {'count': 0, 'packages': [], 'error': str(e)}
    
    def _check_homebrew_updates(self) -> Dict[str, any]:
        """
        Check for Homebrew package updates.
        
        Returns:
            Dictionary with Homebrew update information
        """
        try:
            if not self.homebrew_available:
                return {'count': 0, 'packages': []}
            
            # Update Homebrew repository
            code, stdout, stderr = CommandRunner.run_command(
                ['brew', 'update'],
                timeout=300
            )
            
            # List outdated packages
            code, stdout, stderr = CommandRunner.run_command(
                ['brew', 'outdated'],
                timeout=120,
                check_return_code=False
            )
            
            updates = []
            if code == 0 and stdout.strip():
                lines = stdout.strip().split('\n')
                for line in lines:
                    if line.strip():
                        package_name = line.split()[0]
                        updates.append(package_name)
            
            return {
                'count': len(updates),
                'packages': updates
            }
            
        except Exception as e:
            self.logger.warning(f"Could not check Homebrew updates: {e}")
            return {'count': 0, 'packages': [], 'error': str(e)}
    
    def _update_system(self) -> Dict[str, any]:
        """
        Install system updates using softwareupdate.
        
        Returns:
            Dictionary with update results
        """
        try:
            # Build command
            if self.config['install_recommended_updates']:
                cmd = ['sudo', 'softwareupdate', '--install', '--recommended']
            else:
                cmd = ['sudo', 'softwareupdate', '--install', '--all']
            
            # Add restart flag if configured
            if not self.config['auto_restart']:
                cmd.append('--no-scan')
            
            # Run the update
            timeout = self.config['timeout_minutes'] * 60
            code, stdout, stderr = CommandRunner.run_command(
                cmd, timeout=timeout
            )
            
            return {
                'status': 'success',
                'return_code': code,
                'stdout': stdout,
                'stderr': stderr
            }
            
        except subprocess.CalledProcessError as e:
            self.logger.error(f"System update failed: {e}")
            return {
                'status': 'failed',
                'error': str(e),
                'return_code': e.returncode,
                'stdout': e.stdout if hasattr(e, 'stdout') else '',
                'stderr': e.stderr if hasattr(e, 'stderr') else ''
            }
    
    def _update_app_store(self) -> Dict[str, any]:
        """
        Update App Store applications using mas.
        
        Returns:
            Dictionary with App Store update results
        """
        try:
            if not CommandRunner.is_command_available('mas'):
                return {'status': 'skipped', 'reason': 'mas not available'}
            
            # Update all App Store apps
            code, stdout, stderr = CommandRunner.run_command(
                ['mas', 'upgrade'],
                timeout=1800  # 30 minutes for large apps
            )
            
            return {
                'status': 'success',
                'return_code': code,
                'stdout': stdout,
                'stderr': stderr
            }
            
        except subprocess.CalledProcessError as e:
            self.logger.error(f"App Store update failed: {e}")
            return {
                'status': 'failed',
                'error': str(e),
                'return_code': e.returncode,
                'stdout': e.stdout if hasattr(e, 'stdout') else '',
                'stderr': e.stderr if hasattr(e, 'stderr') else ''
            }
    
    def _update_homebrew(self) -> Dict[str, any]:
        """
        Update Homebrew packages.
        
        Returns:
            Dictionary with Homebrew update results
        """
        results = {}
        
        try:
            if not self.homebrew_available:
                return {'status': 'skipped', 'reason': 'Homebrew not available'}
            
            # Backup current package list if configured
            if self.config['backup_homebrew_bundle']:
                self._backup_homebrew_bundle()
            
            # Update Homebrew itself
            self.logger.info("Updating Homebrew")
            code, stdout, stderr = CommandRunner.run_command(
                ['brew', 'update'],
                timeout=300
            )
            results['brew_update'] = {
                'status': 'success',
                'return_code': code
            }
            
            # Upgrade packages
            if self.config['homebrew_upgrade_all']:
                self.logger.info("Upgrading all Homebrew packages")
                
                # Build upgrade command
                cmd = ['brew', 'upgrade']
                
                # Add excluded packages
                if self.config['excluded_homebrew_packages']:
                    outdated_packages = self._get_outdated_homebrew_packages()
                    packages_to_upgrade = [
                        pkg for pkg in outdated_packages 
                        if pkg not in self.config['excluded_homebrew_packages']
                    ]
                    
                    if packages_to_upgrade:
                        cmd.extend(packages_to_upgrade)
                    else:
                        results['package_upgrade'] = {
                            'status': 'skipped',
                            'reason': 'All packages excluded'
                        }
                        cmd = None
                
                if cmd:
                    code, stdout, stderr = CommandRunner.run_command(
                        cmd, timeout=1800  # 30 minutes
                    )
                    results['package_upgrade'] = {
                        'status': 'success',
                        'return_code': code,
                        'output': stdout
                    }
            
            # Cleanup if configured
            if self.config['homebrew_cleanup']:
                self.logger.info("Cleaning up Homebrew")
                code, stdout, stderr = CommandRunner.run_command(
                    ['brew', 'cleanup'],
                    timeout=300
                )
                results['cleanup'] = {
                    'status': 'success',
                    'return_code': code,
                    'output': stdout
                }
            
            return results
            
        except subprocess.CalledProcessError as e:
            self.logger.error(f"Homebrew update failed: {e}")
            results['error'] = str(e)
            return results
    
    def _get_outdated_homebrew_packages(self) -> List[str]:
        """
        Get list of outdated Homebrew packages.
        
        Returns:
            List of package names
        """
        try:
            code, stdout, stderr = CommandRunner.run_command(
                ['brew', 'outdated'],
                check_return_code=False
            )
            
            if code == 0 and stdout.strip():
                lines = stdout.strip().split('\n')
                return [line.split()[0] for line in lines if line.strip()]
            
            return []
            
        except Exception:
            return []
    
    def _backup_homebrew_bundle(self):
        """Create a backup of the current Homebrew installation."""
        try:
            backup_dir = f"/tmp/homebrew_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            os.makedirs(backup_dir, exist_ok=True)
            
            # Create Brewfile
            brewfile_path = os.path.join(backup_dir, 'Brewfile')
            code, stdout, stderr = CommandRunner.run_command(
                ['brew', 'bundle', 'dump', '--file', brewfile_path]
            )
            
            self.logger.info(f"Homebrew bundle backed up to {brewfile_path}")
            
        except Exception as e:
            self.logger.warning(f"Could not backup Homebrew bundle: {e}")
    
    def _check_restart_required(self) -> bool:
        """
        Check if a restart is required after updates.
        
        Returns:
            Boolean indicating if restart is required
        """
        try:
            # Check for pending system updates that require restart
            code, stdout, stderr = CommandRunner.run_command(
                ['softwareupdate', '--list'],
                check_return_code=False,
                timeout=60
            )
            
            # Look for restart indicators in the output
            if code == 0:
                restart_keywords = [
                    'restart required',
                    'will require a restart',
                    '[restart]'
                ]
                
                for keyword in restart_keywords:
                    if keyword.lower() in stdout.lower():
                        return True
            
            return False
            
        except Exception as e:
            self.logger.warning(f"Could not determine restart requirement: {e}")
            return False
    
    def _schedule_restart(self):
        """Schedule a system restart."""
        try:
            delay_minutes = self.config['restart_delay_minutes']
            self.logger.warning(f"Scheduling system restart in {delay_minutes} minutes")
            
            # Schedule restart using shutdown command
            CommandRunner.run_command([
                'sudo', 'shutdown', '-r', f'+{delay_minutes}'
            ])
            
        except Exception as e:
            self.logger.error(f"Failed to schedule restart: {e}")
    
    def get_system_info(self) -> Dict[str, any]:
        """
        Get macOS-specific system information.
        
        Returns:
            Dictionary with system information
        """
        info = {
            'os_version': self.os_info['version'],
            'architecture': self.os_info['architecture'],
            'homebrew_available': self.homebrew_available
        }
        
        try:
            # Get macOS version details
            code, stdout, stderr = CommandRunner.run_command(
                ['sw_vers'],
                check_return_code=False
            )
            
            if code == 0:
                lines = stdout.strip().split('\n')
                for line in lines:
                    if ':' in line:
                        key, value = line.split(':', 1)
                        key = key.strip().lower().replace(' ', '_')
                        info[f'macos_{key}'] = value.strip()
            
            # Get Homebrew info if available
            if self.homebrew_available:
                code, stdout, stderr = CommandRunner.run_command(
                    ['brew', '--version'],
                    check_return_code=False
                )
                if code == 0:
                    info['homebrew_version'] = stdout.split('\n')[0]
                
                # Get package counts
                code, stdout, stderr = CommandRunner.run_command(
                    ['brew', 'list'],
                    check_return_code=False
                )
                if code == 0:
                    info['homebrew_packages'] = len(stdout.strip().split('\n')) if stdout.strip() else 0
            
        except Exception as e:
            self.logger.warning(f"Could not get complete system info: {e}")
        
        return info


def main():
    """Main function for standalone execution."""
    import argparse
    
    parser = argparse.ArgumentParser(description='macOS automatic updater')
    parser.add_argument('--config', help='Path to configuration file')
    parser.add_argument('--dry-run', action='store_true', 
                       help='Show what would be done without making changes')
    parser.add_argument('--verbose', action='store_true',
                       help='Enable verbose logging')
    parser.add_argument('--no-homebrew', action='store_true',
                       help='Skip Homebrew updates')
    parser.add_argument('--no-app-store', action='store_true',
                       help='Skip App Store updates')
    
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
    if args.no_homebrew:
        config['update_homebrew'] = False
    if args.no_app_store:
        config['update_app_store'] = False
    
    # Override for dry run
    if args.dry_run:
        logger.info("DRY RUN MODE - No changes will be made")
        config['update_system'] = False
        config['update_app_store'] = False
        config['update_homebrew'] = False
        config['auto_restart'] = False
    
    try:
        # Create updater and run update cycle
        updater = MacOSUpdater(config, logger)
        results = updater.run_update_cycle()
        
        # Print summary
        print(f"\n=== macOS Update Results ===")
        print(f"Status: {results['overall_status'].upper()}")
        print(f"Timestamp: {results['timestamp']}")
        
        if 'available_updates' in results:
            updates = results['available_updates']
            print(f"System Updates: {updates.get('system_updates', 0)}")
            print(f"App Store Updates: {updates.get('app_store_updates', 0)}")
            print(f"Homebrew Updates: {updates.get('homebrew_updates', 0)}")
        
        if results.get('restart_required'):
            print("⚠️  RESTART REQUIRED")
        
        # Get system info
        system_info = updater.get_system_info()
        if 'homebrew_packages' in system_info:
            print(f"Homebrew Packages: {system_info['homebrew_packages']}")
        
        # Exit with appropriate code
        sys.exit(0 if results['overall_status'] in ['success', 'no_updates'] else 1)
        
    except Exception as e:
        logger.error(f"Update process failed: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()