#!/usr/bin/env python3
"""
Arch Linux automatic update script using pacman and optional AUR helper.
Handles system updates, AUR packages, and maintenance tasks.

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


class ArchUpdater:
    """Handles automatic updates for Arch Linux systems."""
    
    def __init__(self, config: Optional[Dict] = None, logger: Optional[logging.Logger] = None):
        """
        Initialize the Arch updater.
        
        Args:
            config: Configuration dictionary
            logger: Logger instance
        """
        self.logger = logger or LogManager.setup_logging()
        self.os_info = OSDetector.get_os_info()
        
        # Validate that this is an Arch-based system
        if self.os_info['distro'] not in ['arch', 'manjaro', 'endeavouros', 'garuda']:
            raise Exception(f"This script is for Arch-based systems only. "
                          f"Detected: {self.os_info['distro']}")
        
        # Default configuration
        self.config = {
            'update_system': True,
            'update_aur': False,
            'aur_helper': 'yay',  # yay, paru, or trizen
            'auto_resolve_conflicts': False,
            'clean_cache': True,
            'clean_orphans': True,
            'check_mirrors': True,
            'update_mirrorlist': False,
            'backup_pacman_db': True,
            'ignore_packages': [],
            'pre_update_health_check': True,
            'post_update_health_check': True,
            'max_parallel_downloads': 5,
            'timeout_minutes': 60
        }
        
        if config:
            self.config.update(config)
        
        self.health_checker = HealthChecker(self.logger)
        self.aur_helper = self._detect_aur_helper()
    
    def run_update_cycle(self) -> Dict[str, any]:
        """
        Run a complete update cycle.
        
        Returns:
            Dictionary with update results
        """
        self.logger.info("Starting Arch Linux update cycle")
        
        results = {
            'timestamp': datetime.now().isoformat(),
            'os_info': self.os_info,
            'pre_update_health': None,
            'database_sync': None,
            'available_updates': None,
            'system_update': None,
            'aur_update': None,
            'cleanup': None,
            'post_update_health': None,
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
            
            # Backup pacman database
            if self.config['backup_pacman_db']:
                self.logger.info("Backing up pacman database")
                self._backup_pacman_database()
            
            # Update mirror list if configured
            if self.config['update_mirrorlist']:
                self.logger.info("Updating mirror list")
                self._update_mirrorlist()
            
            # Sync package databases
            self.logger.info("Synchronizing package databases")
            results['database_sync'] = self._sync_databases()
            
            # Check for available updates
            self.logger.info("Checking for available updates")
            results['available_updates'] = self._check_available_updates()
            
            if not results['available_updates']['has_updates'] and not self.config['update_aur']:
                self.logger.info("No updates available")
                results['overall_status'] = 'no_updates'
            else:
                # Update system packages
                if self.config['update_system'] and results['available_updates']['has_updates']:
                    self.logger.info("Updating system packages")
                    results['system_update'] = self._update_system_packages()
                
                # Update AUR packages
                if self.config['update_aur'] and self.aur_helper:
                    self.logger.info("Updating AUR packages")
                    results['aur_update'] = self._update_aur_packages()
            
            # Cleanup
            if self.config['clean_cache'] or self.config['clean_orphans']:
                self.logger.info("Running cleanup tasks")
                results['cleanup'] = self._cleanup_system()
            
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
    
    def _detect_aur_helper(self) -> Optional[str]:
        """
        Detect available AUR helper.
        
        Returns:
            Name of available AUR helper or None
        """
        helpers = ['yay', 'paru', 'trizen', 'pikaur']
        
        for helper in helpers:
            if CommandRunner.is_command_available(helper):
                self.logger.info(f"Found AUR helper: {helper}")
                return helper
        
        if self.config['update_aur']:
            self.logger.warning("AUR updates requested but no AUR helper found")
        
        return None
    
    def _backup_pacman_database(self):
        """Backup the pacman database."""
        try:
            backup_dir = f"/tmp/pacman_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            os.makedirs(backup_dir, exist_ok=True)
            
            # Backup pacman database
            CommandRunner.run_command([
                'sudo', 'cp', '-r', '/var/lib/pacman/local', backup_dir
            ])
            
            self.logger.info(f"Pacman database backed up to {backup_dir}")
            
        except Exception as e:
            self.logger.warning(f"Could not backup pacman database: {e}")
    
    def _update_mirrorlist(self) -> Dict[str, any]:
        """
        Update the mirrorlist using reflector (if available).
        
        Returns:
            Dictionary with mirror update results
        """
        try:
            if not CommandRunner.is_command_available('reflector'):
                return {'status': 'skipped', 'reason': 'reflector not available'}
            
            # Use reflector to update mirrors
            code, stdout, stderr = CommandRunner.run_command([
                'sudo', 'reflector',
                '--country', 'United States,Canada,Germany,France,United Kingdom',
                '--protocol', 'https',
                '--latest', '10',
                '--sort', 'rate',
                '--save', '/etc/pacman.d/mirrorlist'
            ], timeout=300)
            
            return {
                'status': 'success',
                'return_code': code,
                'output': stdout
            }
            
        except Exception as e:
            self.logger.warning(f"Failed to update mirrorlist: {e}")
            return {'status': 'failed', 'error': str(e)}
    
    def _sync_databases(self) -> Dict[str, any]:
        """
        Synchronize package databases.
        
        Returns:
            Dictionary with sync results
        """
        try:
            # Run pacman -Sy to sync databases
            code, stdout, stderr = CommandRunner.run_command(
                ['sudo', 'pacman', '-Sy'],
                timeout=300
            )
            
            return {
                'status': 'success',
                'return_code': code,
                'stdout': stdout,
                'stderr': stderr
            }
            
        except subprocess.CalledProcessError as e:
            self.logger.error(f"Failed to sync databases: {e}")
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
            # Check for official repository updates
            code, stdout, stderr = CommandRunner.run_command(
                ['pacman', '-Qu'],
                check_return_code=False
            )
            
            official_updates = []
            if code == 0 and stdout.strip():
                lines = stdout.strip().split('\n')
                for line in lines:
                    if line.strip():
                        parts = line.split()
                        if len(parts) >= 2:
                            package_name = parts[0]
                            official_updates.append(package_name)
            
            # Check for AUR updates if AUR helper is available
            aur_updates = []
            if self.aur_helper and self.config['update_aur']:
                aur_updates = self._check_aur_updates()
            
            return {
                'has_updates': len(official_updates) > 0 or len(aur_updates) > 0,
                'official_updates': len(official_updates),
                'aur_updates': len(aur_updates),
                'official_packages': official_updates[:20],  # Limit to first 20
                'aur_packages': aur_updates[:20]
            }
            
        except Exception as e:
            self.logger.error(f"Failed to check available updates: {e}")
            return {
                'has_updates': False,
                'error': str(e)
            }
    
    def _check_aur_updates(self) -> List[str]:
        """
        Check for AUR package updates.
        
        Returns:
            List of AUR packages with updates
        """
        try:
            if not self.aur_helper:
                return []
            
            # Different AUR helpers have different commands
            if self.aur_helper in ['yay', 'paru']:
                code, stdout, stderr = CommandRunner.run_command(
                    [self.aur_helper, '-Qua'],
                    check_return_code=False,
                    timeout=120
                )
            else:  # trizen, pikaur
                code, stdout, stderr = CommandRunner.run_command(
                    [self.aur_helper, '-Qua'],
                    check_return_code=False,
                    timeout=120
                )
            
            aur_packages = []
            if code == 0 and stdout.strip():
                lines = stdout.strip().split('\n')
                for line in lines:
                    if line.strip():
                        parts = line.split()
                        if len(parts) >= 1:
                            package_name = parts[0]
                            aur_packages.append(package_name)
            
            return aur_packages
            
        except Exception as e:
            self.logger.warning(f"Could not check AUR updates: {e}")
            return []
    
    def _update_system_packages(self) -> Dict[str, any]:
        """
        Update official repository packages.
        
        Returns:
            Dictionary with update results
        """
        try:
            # Build pacman command
            cmd = ['sudo', 'pacman', '-Su', '--noconfirm']
            
            # Add ignored packages
            if self.config['ignore_packages']:
                for pkg in self.config['ignore_packages']:
                    cmd.extend(['--ignore', pkg])
            
            # Handle conflict resolution
            if not self.config['auto_resolve_conflicts']:
                # Remove --noconfirm to allow manual conflict resolution
                cmd.remove('--noconfirm')
            
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
            self.logger.error(f"System package update failed: {e}")
            return {
                'status': 'failed',
                'error': str(e),
                'return_code': e.returncode,
                'stdout': e.stdout if hasattr(e, 'stdout') else '',
                'stderr': e.stderr if hasattr(e, 'stderr') else ''
            }
    
    def _update_aur_packages(self) -> Dict[str, any]:
        """
        Update AUR packages using the detected AUR helper.
        
        Returns:
            Dictionary with AUR update results
        """
        try:
            if not self.aur_helper:
                return {'status': 'skipped', 'reason': 'No AUR helper available'}
            
            # Build AUR helper command
            if self.aur_helper == 'yay':
                cmd = ['yay', '-Sua', '--noconfirm']
            elif self.aur_helper == 'paru':
                cmd = ['paru', '-Sua', '--noconfirm']
            elif self.aur_helper == 'trizen':
                cmd = ['trizen', '-Sua', '--noconfirm']
            elif self.aur_helper == 'pikaur':
                cmd = ['pikaur', '-Sua', '--noconfirm']
            else:
                return {'status': 'skipped', 'reason': f'Unsupported AUR helper: {self.aur_helper}'}
            
            # Handle conflict resolution
            if not self.config['auto_resolve_conflicts']:
                cmd.remove('--noconfirm')
            
            # Run the AUR update
            timeout = self.config['timeout_minutes'] * 60
            code, stdout, stderr = CommandRunner.run_command(
                cmd, timeout=timeout, check_return_code=False
            )
            
            return {
                'status': 'success' if code == 0 else 'partial',
                'return_code': code,
                'stdout': stdout,
                'stderr': stderr,
                'helper_used': self.aur_helper
            }
            
        except subprocess.CalledProcessError as e:
            self.logger.error(f"AUR package update failed: {e}")
            return {
                'status': 'failed',
                'error': str(e),
                'return_code': e.returncode,
                'helper_used': self.aur_helper
            }
    
    def _cleanup_system(self) -> Dict[str, any]:
        """
        Clean up the system by removing orphaned packages and cleaning cache.
        
        Returns:
            Dictionary with cleanup results
        """
        results = {}
        
        try:
            # Remove orphaned packages
            if self.config['clean_orphans']:
                self.logger.info("Removing orphaned packages")
                
                # First, find orphaned packages
                code, stdout, stderr = CommandRunner.run_command(
                    ['pacman', '-Qdtq'],
                    check_return_code=False
                )
                
                if code == 0 and stdout.strip():
                    # Remove orphaned packages
                    orphaned_packages = stdout.strip().split('\n')
                    code, stdout, stderr = CommandRunner.run_command(
                        ['sudo', 'pacman', '-Rns', '--noconfirm'] + orphaned_packages,
                        timeout=300
                    )
                    
                    results['orphan_removal'] = {
                        'status': 'success',
                        'packages_removed': len(orphaned_packages),
                        'packages': orphaned_packages
                    }
                else:
                    results['orphan_removal'] = {
                        'status': 'success',
                        'packages_removed': 0,
                        'note': 'No orphaned packages found'
                    }
            
            # Clean package cache
            if self.config['clean_cache']:
                self.logger.info("Cleaning package cache")
                
                # Remove all cached packages except the most recent versions
                code, stdout, stderr = CommandRunner.run_command(
                    ['sudo', 'pacman', '-Sc', '--noconfirm'],
                    timeout=300
                )
                
                results['cache_cleanup'] = {
                    'status': 'success',
                    'return_code': code,
                    'output': stdout
                }
            
            return results
            
        except subprocess.CalledProcessError as e:
            self.logger.error(f"Cleanup failed: {e}")
            results['error'] = str(e)
            return results
    
    def get_system_info(self) -> Dict[str, str]:
        """
        Get Arch-specific system information.
        
        Returns:
            Dictionary with system information
        """
        info = {
            'distro': self.os_info['distro'],
            'kernel': self.os_info['version'],
            'aur_helper': self.aur_helper or 'none'
        }
        
        # Get package counts
        try:
            # Count official packages
            code, stdout, stderr = CommandRunner.run_command(
                ['pacman', '-Q'],
                check_return_code=False
            )
            if code == 0:
                info['total_packages'] = len(stdout.strip().split('\n'))
            
            # Count explicitly installed packages
            code, stdout, stderr = CommandRunner.run_command(
                ['pacman', '-Qe'],
                check_return_code=False
            )
            if code == 0:
                info['explicit_packages'] = len(stdout.strip().split('\n'))
            
            # Count AUR packages if helper available
            if self.aur_helper:
                code, stdout, stderr = CommandRunner.run_command(
                    ['pacman', '-Qm'],
                    check_return_code=False
                )
                if code == 0:
                    info['aur_packages'] = len(stdout.strip().split('\n')) if stdout.strip() else 0
        
        except Exception as e:
            self.logger.warning(f"Could not get package counts: {e}")
        
        return info


def main():
    """Main function for standalone execution."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Arch Linux automatic updater')
    parser.add_argument('--config', help='Path to configuration file')
    parser.add_argument('--dry-run', action='store_true', 
                       help='Show what would be done without making changes')
    parser.add_argument('--verbose', action='store_true',
                       help='Enable verbose logging')
    parser.add_argument('--aur', action='store_true',
                       help='Include AUR package updates')
    
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
    if args.aur:
        config['update_aur'] = True
    
    # Override for dry run
    if args.dry_run:
        logger.info("DRY RUN MODE - No changes will be made")
        config['update_system'] = False
        config['update_aur'] = False
        config['clean_cache'] = False
        config['clean_orphans'] = False
    
    try:
        # Create updater and run update cycle
        updater = ArchUpdater(config, logger)
        results = updater.run_update_cycle()
        
        # Print summary
        print(f"\n=== Arch Linux Update Results ===")
        print(f"Status: {results['overall_status'].upper()}")
        print(f"Timestamp: {results['timestamp']}")
        
        if 'available_updates' in results and results['available_updates']:
            updates = results['available_updates']
            print(f"Official Updates: {updates.get('official_updates', 0)}")
            if updates.get('aur_updates', 0) > 0:
                print(f"AUR Updates: {updates.get('aur_updates', 0)}")
        
        # Get system info
        system_info = updater.get_system_info()
        if 'total_packages' in system_info:
            print(f"Total Packages: {system_info['total_packages']}")
        
        # Exit with appropriate code
        sys.exit(0 if results['overall_status'] in ['success', 'no_updates'] else 1)
        
    except Exception as e:
        logger.error(f"Update process failed: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()