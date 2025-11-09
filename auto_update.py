#!/usr/bin/env python3
"""
Main auto-update orchestrator script for cross-platform system updates.
Detects the operating system and executes the appropriate update script.

Author: Loyd Johnson
Date: November 2025
"""

import os
import sys
import argparse
import json
import importlib.util
from datetime import datetime
from typing import Dict, Optional
import logging

# Add utils directory to path
sys.path.append(os.path.join(os.path.dirname(__file__)))
from utils.system_utils import OSDetector, LogManager, ConfigManager


class AutoUpdateOrchestrator:
    """Main orchestrator for cross-platform automatic updates."""
    
    def __init__(self, config_file: Optional[str] = None, logger: Optional[logging.Logger] = None):
        """
        Initialize the update orchestrator.
        
        Args:
            config_file: Path to configuration file
            logger: Logger instance
        """
        self.logger = logger or LogManager.setup_logging()
        self.os_info = OSDetector.get_os_info()
        
        # Load configuration
        self.config = self._load_config(config_file)
        
        # Determine update module based on OS
        self.update_module_path = self._get_update_module_path()
        
        self.logger.info(f"Detected OS: {self.os_info['distro']} ({self.os_info['os_type']})")
        self.logger.info(f"Update module: {self.update_module_path}")
    
    def run_updates(self, **kwargs) -> Dict[str, any]:
        """
        Run the appropriate update script for the detected OS.
        
        Args:
            **kwargs: Additional arguments to pass to the update script
            
        Returns:
            Dictionary with update results
        """
        self.logger.info("Starting cross-platform update process")
        
        # Merge kwargs with config
        update_config = self.config.copy()
        update_config.update(kwargs)
        
        try:
            # Import and run the appropriate updater
            updater_class = self._import_updater_class()
            updater = updater_class(config=update_config, logger=self.logger)
            
            # Run the update cycle
            results = updater.run_update_cycle()
            
            # Add orchestrator metadata
            results['orchestrator'] = {
                'version': '1.0.0',
                'detected_os': self.os_info,
                'update_module': self.update_module_path,
                'config_used': update_config
            }
            
            # Log results summary
            self._log_results_summary(results)
            
            return results
            
        except Exception as e:
            self.logger.error(f"Update orchestration failed: {e}")
            
            error_result = {
                'timestamp': datetime.now().isoformat(),
                'overall_status': 'failed',
                'error': str(e),
                'orchestrator': {
                    'version': '1.0.0',
                    'detected_os': self.os_info,
                    'update_module': self.update_module_path
                }
            }
            
            return error_result
    
    def _load_config(self, config_file: Optional[str]) -> Dict[str, any]:
        """
        Load configuration from file or use defaults.
        
        Args:
            config_file: Path to configuration file
            
        Returns:
            Configuration dictionary
        """
        default_config = {
            'pre_update_health_check': True,
            'post_update_health_check': True,
            'backup_important_configs': True,
            'log_level': 'INFO',
            'timeout_minutes': 60
        }
        
        if config_file and os.path.exists(config_file):
            try:
                with open(config_file, 'r') as f:
                    file_config = json.load(f)
                
                # Merge with defaults
                default_config.update(file_config)
                self.logger.info(f"Loaded configuration from {config_file}")
                
            except Exception as e:
                self.logger.warning(f"Failed to load config file {config_file}: {e}")
                self.logger.info("Using default configuration")
        
        else:
            # Try to find default config file
            default_path = ConfigManager.get_config_path()
            if os.path.exists(default_path):
                try:
                    with open(default_path, 'r') as f:
                        file_config = json.load(f)
                    
                    default_config.update(file_config)
                    self.logger.info(f"Loaded default configuration from {default_path}")
                    
                except Exception as e:
                    self.logger.warning(f"Failed to load default config: {e}")
            else:
                self.logger.info("No configuration file found, using defaults")
        
        return default_config
    
    def _get_update_module_path(self) -> str:
        """
        Determine the appropriate update module path based on OS.
        
        Returns:
            Module path string
        """
        distro = self.os_info['distro'].lower()
        
        # Map distributions to update modules
        module_map = {
            'debian': 'scripts.debian.auto_update',
            'ubuntu': 'scripts.debian.auto_update',
            'arch': 'scripts.arch.auto_update',
            'manjaro': 'scripts.arch.auto_update',
            'endeavouros': 'scripts.arch.auto_update',
            'garuda': 'scripts.arch.auto_update',
            'fedora': 'scripts.fedora.auto_update',
            'rhel': 'scripts.fedora.auto_update',
            'centos': 'scripts.fedora.auto_update',
            'rocky': 'scripts.fedora.auto_update',
            'alma': 'scripts.fedora.auto_update',
            'scientific': 'scripts.fedora.auto_update',
            'macos': 'scripts.macos.auto_update',
            'darwin': 'scripts.macos.auto_update'
        }
        
        module_path = module_map.get(distro)
        
        if not module_path:
            supported_distros = list(module_map.keys())
            raise Exception(
                f"Unsupported distribution: {distro}. "
                f"Supported distributions: {', '.join(supported_distros)}"
            )
        
        return module_path
    
    def _import_updater_class(self):
        """
        Dynamically import the appropriate updater class.
        
        Returns:
            Updater class
        """
        try:
            # Map module paths to class names
            class_map = {
                'scripts.debian.auto_update': 'DebianUpdater',
                'scripts.arch.auto_update': 'ArchUpdater',
                'scripts.fedora.auto_update': 'FedoraUpdater',
                'scripts.macos.auto_update': 'MacOSUpdater'
            }
            
            class_name = class_map.get(self.update_module_path)
            if not class_name:
                raise Exception(f"No class mapping for module: {self.update_module_path}")
            
            # Convert module path to file path
            module_file = self.update_module_path.replace('.', '/') + '.py'
            module_file = os.path.join(os.path.dirname(__file__), module_file)
            
            if not os.path.exists(module_file):
                raise Exception(f"Update module not found: {module_file}")
            
            # Import the module
            spec = importlib.util.spec_from_file_location(
                self.update_module_path, module_file
            )
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            
            # Get the updater class
            updater_class = getattr(module, class_name)
            
            return updater_class
            
        except Exception as e:
            raise Exception(f"Failed to import updater class: {e}")
    
    def _log_results_summary(self, results: Dict[str, any]):
        """
        Log a summary of the update results.
        
        Args:
            results: Results dictionary
        """
        status = results.get('overall_status', 'unknown')
        
        self.logger.info(f"Update process completed with status: {status.upper()}")
        
        # Log health check results
        if 'pre_update_health' in results:
            pre_health = results['pre_update_health']['overall_status']
            self.logger.info(f"Pre-update health check: {pre_health}")
        
        if 'post_update_health' in results:
            post_health = results['post_update_health']['overall_status']
            self.logger.info(f"Post-update health check: {post_health}")
        
        # Log update counts
        if 'available_updates' in results:
            updates = results['available_updates']
            if isinstance(updates, dict):
                total = updates.get('total_updates', 0)
                security = updates.get('security_updates', 0)
                self.logger.info(f"Updates processed - Total: {total}, Security: {security}")
        
        # Log reboot/restart requirement
        reboot_required = (results.get('reboot_required') or 
                          results.get('restart_required', False))
        if reboot_required:
            self.logger.warning("System reboot/restart is required")
    
    def get_supported_distributions(self) -> Dict[str, str]:
        """
        Get list of supported distributions and their update modules.
        
        Returns:
            Dictionary mapping distributions to modules
        """
        return {
            'Debian/Ubuntu': 'debian',
            'Arch/Manjaro': 'arch', 
            'Fedora/RHEL/CentOS': 'fedora',
            'macOS': 'macos'
        }
    
    def check_prerequisites(self) -> Dict[str, any]:
        """
        Check if prerequisites are met for the detected OS.
        
        Returns:
            Dictionary with prerequisite check results
        """
        distro = self.os_info['distro'].lower()
        results = {
            'os_supported': OSDetector.is_supported_distro(distro),
            'checks': {}
        }
        
        try:
            # Import the updater to run checks
            updater_class = self._import_updater_class()
            
            # Basic instantiation test
            try:
                updater = updater_class(logger=self.logger)
                results['checks']['module_import'] = 'success'
                
                # OS-specific prerequisite checks
                if hasattr(updater, 'check_prerequisites'):
                    prereq_results = updater.check_prerequisites()
                    results['checks'].update(prereq_results)
                    
            except Exception as e:
                results['checks']['module_import'] = f'failed: {e}'
            
        except Exception as e:
            results['checks']['module_availability'] = f'failed: {e}'
        
        return results


def main():
    """Main function for command-line execution."""
    parser = argparse.ArgumentParser(
        description='Cross-platform automatic update orchestrator',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python auto_update.py                    # Run with default settings
  python auto_update.py --config custom.json  # Use custom configuration
  python auto_update.py --dry-run          # Show what would be done
  python auto_update.py --check-prereq    # Check prerequisites only
  python auto_update.py --list-supported  # List supported distributions
        """
    )
    
    parser.add_argument(
        '--config', '-c',
        help='Path to configuration file'
    )
    
    parser.add_argument(
        '--dry-run', '-n',
        action='store_true',
        help='Show what would be done without making changes'
    )
    
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Enable verbose logging'
    )
    
    parser.add_argument(
        '--check-prereq',
        action='store_true',
        help='Check prerequisites and exit'
    )
    
    parser.add_argument(
        '--list-supported',
        action='store_true',
        help='List supported distributions and exit'
    )
    
    # OS-specific options
    parser.add_argument(
        '--security-only',
        action='store_true',
        help='Install security updates only (where supported)'
    )
    
    parser.add_argument(
        '--no-reboot',
        action='store_true',
        help='Disable automatic reboot/restart'
    )
    
    parser.add_argument(
        '--force',
        action='store_true',
        help='Force updates even if health checks fail'
    )
    
    args = parser.parse_args()
    
    # Setup logging
    log_level = 'DEBUG' if args.verbose else 'INFO'
    logger = LogManager.setup_logging(log_level)
    
    try:
        # Create orchestrator
        orchestrator = AutoUpdateOrchestrator(
            config_file=args.config,
            logger=logger
        )
        
        # Handle special commands
        if args.list_supported:
            print("Supported distributions:")
            supported = orchestrator.get_supported_distributions()
            for family, module in supported.items():
                print(f"  {family} -> {module} module")
            sys.exit(0)
        
        if args.check_prereq:
            print("Checking prerequisites...")
            prereq_results = orchestrator.check_prerequisites()
            
            print(f"OS Supported: {'Yes' if prereq_results['os_supported'] else 'No'}")
            
            for check, result in prereq_results['checks'].items():
                status = "✓" if result == 'success' else "✗"
                print(f"{status} {check}: {result}")
            
            # Exit with error if any checks failed
            all_success = all(r == 'success' for r in prereq_results['checks'].values())
            sys.exit(0 if prereq_results['os_supported'] and all_success else 1)
        
        # Prepare update configuration from command line args
        update_kwargs = {}
        
        if args.dry_run:
            logger.info("DRY RUN MODE - No changes will be made")
            # Set dry-run flags for all update types
            dry_run_config = {
                'update_system': False,
                'update_aur': False,
                'update_app_store': False,
                'update_homebrew': False,
                'unattended_upgrade': False,
                'auto_reboot': False,
                'auto_restart': False,
                'clean_cache': False,
                'remove_old_kernels': False,
                'clean_orphans': False
            }
            update_kwargs.update(dry_run_config)
        
        if args.security_only:
            update_kwargs['install_security_only'] = True
            update_kwargs['security_only'] = True
        
        if args.no_reboot:
            update_kwargs['auto_reboot'] = False
            update_kwargs['auto_restart'] = False
        
        if args.force:
            update_kwargs['pre_update_health_check'] = False
        
        # Run updates
        results = orchestrator.run_updates(**update_kwargs)
        
        # Print summary
        print(f"\n{'='*50}")
        print(f"System Update Results")
        print(f"{'='*50}")
        print(f"OS: {results['orchestrator']['detected_os']['distro']} "
              f"({results['orchestrator']['detected_os']['os_type']})")
        print(f"Status: {results['overall_status'].upper()}")
        print(f"Timestamp: {results['timestamp']}")
        
        # Print update-specific information
        if 'available_updates' in results:
            updates = results['available_updates']
            if isinstance(updates, dict):
                print(f"Updates Available: {updates.get('total_updates', 'unknown')}")
                if 'security_updates' in updates:
                    print(f"Security Updates: {updates['security_updates']}")
        
        # Print health check status
        if 'pre_update_health' in results:
            pre_status = results['pre_update_health']['overall_status']
            print(f"Pre-update Health: {pre_status}")
        
        if 'post_update_health' in results:
            post_status = results['post_update_health']['overall_status']
            print(f"Post-update Health: {post_status}")
        
        # Print reboot warning
        reboot_required = (results.get('reboot_required') or 
                          results.get('restart_required', False))
        if reboot_required:
            print("\n⚠️  SYSTEM REBOOT/RESTART REQUIRED ⚠️")
        
        # Print error if present
        if 'error' in results:
            print(f"\nError: {results['error']}")
        
        print(f"{'='*50}")
        
        # Exit with appropriate code
        success_statuses = ['success', 'no_updates']
        sys.exit(0 if results['overall_status'] in success_statuses else 1)
        
    except KeyboardInterrupt:
        logger.info("Update process interrupted by user")
        sys.exit(130)
    
    except Exception as e:
        logger.error(f"Update orchestration failed: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()