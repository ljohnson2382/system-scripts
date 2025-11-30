#!/usr/bin/env python3
"""
Network repair and automated fix toolkit.
Automated remediation for common network issues detected by network_diagnostics.

Author: Loyd Johnson
Date: November 2025
"""

import os
import sys
import time
import logging
from datetime import datetime
from typing import Dict, List, Optional

try:
    from tqdm import tqdm
    HAS_TQDM = True
except ImportError:
    HAS_TQDM = False

# Add parent directories to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))
from utils.system_utils import OSDetector, CommandRunner, LogManager


class NetworkRepair:
    """Automated network repair and remediation tools."""
    
    def __init__(self, logger: Optional[logging.Logger] = None):
        """Initialize network repair toolkit."""
        self.logger = logger or LogManager.setup_logging()
        self.os_info = OSDetector.get_os_info()
    
    def run_automated_fixes(self, diagnostic_results: Dict[str, any], dry_run: bool = True, show_progress: bool = True, auto_approve_destructive: bool = False) -> Dict[str, any]:
        """
        Attempt automated fixes for detected network issues.
        
        Args:
            diagnostic_results: Results from NetworkDiagnostics.run_full_diagnostics()
            dry_run: If True, only show what would be done
            show_progress: Whether to show progress indicators
            auto_approve_destructive: If True, skip user confirmation for destructive operations
            
        Returns:
            Dictionary with fix results
        """
        fix_results = {
            'timestamp': datetime.now().isoformat(),
            'dry_run': dry_run,
            'auto_approve_destructive': auto_approve_destructive,
            'fixes_attempted': [],
            'fixes_successful': [],
            'fixes_failed': [],
            'fixes_skipped': [],
            'fixes_declined': [],
            'requires_admin': False,
            'recommendations': []
        }
        
        overall_status = diagnostic_results.get('overall_status', 'unknown')
        
        if overall_status == 'healthy':
            fix_results['recommendations'].append("Network appears healthy - no fixes needed")
            return fix_results
        
        if overall_status in ['minor_issues', 'major_issues']:
            self.logger.info(f"Attempting automated fixes (dry_run={dry_run})")
            
            # Count potential fixes for progress tracking
            total_fixes = 0
            dns_results = diagnostic_results.get('dns_resolution', {})
            conn_results = diagnostic_results.get('connectivity_tests', {})
            interface_results = diagnostic_results.get('network_interfaces', {})
            
            if dns_results.get('failed_resolutions', 0) > 0:
                total_fixes += 3  # DNS fixes
            if conn_results.get('failed_pings', 0) > 0:
                total_fixes += 3  # Connectivity fixes
            if 'error' in interface_results:
                total_fixes += 1  # Interface fixes
            if self.os_info['os_type'] == 'windows':
                total_fixes += 3  # Windows-specific fixes
            
            if total_fixes == 0:
                fix_results['recommendations'].append("No automated fixes available for detected issues")
                return fix_results
            
            mode_desc = "Previewing network fixes" if dry_run else "Applying network fixes"
            
            if show_progress and HAS_TQDM:
                progress_bar = tqdm(total=total_fixes, desc=mode_desc, ncols=80, 
                                  bar_format='{l_bar}{bar}| {n_fmt}/{total_fmt} [{elapsed}]')
            elif show_progress:
                print(f"🔧 {mode_desc} (0/{total_fixes})")
                progress_bar = None
            else:
                progress_bar = None
            
            try:
                # DNS Issues
                if dns_results.get('failed_resolutions', 0) > 0:
                    if show_progress and not HAS_TQDM:
                        print(f"  🔍 Checking DNS fixes...")
                    fix_results = self._fix_dns_issues(fix_results, dns_results, dry_run, progress_bar)
                
                # Connectivity Issues  
                if conn_results.get('failed_pings', 0) > 0:
                    if show_progress and not HAS_TQDM:
                        print(f"  🌐 Checking connectivity fixes...")
                    fix_results = self._fix_connectivity_issues(fix_results, conn_results, dry_run, progress_bar)
                
                # Network Interface Issues
                if 'error' in interface_results:
                    if show_progress and not HAS_TQDM:
                        print(f"  🔌 Checking interface fixes...")
                    fix_results = self._fix_interface_issues(fix_results, interface_results, dry_run, progress_bar)
                
                # Windows-specific network fixes
                if self.os_info['os_type'] == 'windows':
                    if show_progress and not HAS_TQDM:
                        print(f"  💻 Checking Windows-specific fixes...")
                    fix_results = self._fix_windows_network_issues(fix_results, diagnostic_results, dry_run, progress_bar)
                
            finally:
                if progress_bar and HAS_TQDM:
                    progress_bar.close()
                elif show_progress and not HAS_TQDM:
                    successful = len(fix_results['fixes_successful'])
                    total_attempted = len(fix_results['fixes_attempted'])
                    print(f"  ✅ Fixes completed: {successful}/{total_attempted} successful")
            
            # Add general recommendations
            self._add_recommendations(fix_results, diagnostic_results)
        
        return fix_results
    
    def _fix_dns_issues(self, fix_results: Dict[str, any], dns_results: Dict[str, any], dry_run: bool, progress_bar=None) -> Dict[str, any]:
        """Attempt to fix DNS resolution issues."""
        self.logger.info("Attempting DNS fixes...")
        
        fixes_to_try = [
            {
                'name': 'flush_dns_cache',
                'description': 'Flush DNS cache',
                'priority': 1,
                'requires_admin': True,
                'commands': {
                    'windows': ['ipconfig', '/flushdns'],
                    'linux': ['sudo', 'systemctl', 'restart', 'systemd-resolved'],
                    'macos': ['sudo', 'dscacheutil', '-flushcache']
                }
            },
            {
                'name': 'reset_dns_servers',
                'description': 'Reset DNS servers to Google DNS (8.8.8.8, 8.8.4.4)',
                'priority': 2,
                'requires_admin': True,
                'commands': {
                    'windows': [
                        ['powershell', '-Command', 'Get-NetAdapter | Where-Object {$_.Status -eq "Up"} | ForEach-Object {Set-DnsClientServerAddress -InterfaceAlias $_.Name -ServerAddresses @("8.8.8.8", "8.8.4.4")}']
                    ],
                    'linux': [
                        ['sudo', 'sh', '-c', 'echo "nameserver 8.8.8.8" > /etc/resolv.conf'],
                        ['sudo', 'sh', '-c', 'echo "nameserver 8.8.4.4" >> /etc/resolv.conf']
                    ],
                    'macos': ['networksetup', '-setdnsservers', 'Wi-Fi', '8.8.8.8', '8.8.4.4']
                }
            },
            {
                'name': 'restart_dns_service',
                'description': 'Restart DNS service',
                'priority': 3,
                'requires_admin': True,
                'commands': {
                    'windows': [
                        ['net', 'stop', 'dnscache'],
                        ['timeout', '2'],
                        ['net', 'start', 'dnscache']
                    ],
                    'linux': ['sudo', 'systemctl', 'restart', 'systemd-resolved'],
                    'macos': ['sudo', 'killall', '-HUP', 'mDNSResponder']
                }
            }
        ]
        
        # Sort by priority
        fixes_to_try.sort(key=lambda x: x['priority'])
        
        for fix in fixes_to_try:
            if progress_bar and HAS_TQDM:
                progress_bar.set_description(f"{'Previewing' if dry_run else 'Applying'} {fix['description'].lower()}")
            
            fix_result = self._attempt_fix(fix, dry_run)
            fix_results['fixes_attempted'].append(fix_result)
            
            if fix_result['success']:
                fix_results['fixes_successful'].append(fix_result['name'])
            else:
                fix_results['fixes_failed'].append(fix_result['name'])
            
            if fix['requires_admin']:
                fix_results['requires_admin'] = True
            
            if progress_bar and HAS_TQDM:
                progress_bar.update(1)
        
        return fix_results
    
    def _fix_connectivity_issues(self, fix_results: Dict[str, any], conn_results: Dict[str, any], dry_run: bool, progress_bar=None) -> Dict[str, any]:
        """Attempt to fix connectivity issues."""
        self.logger.info("Attempting connectivity fixes...")
        
        fixes_to_try = [
            {
                'name': 'release_renew_ip',
                'description': 'Release and renew IP address',
                'priority': 1,
                'requires_admin': True,
                'commands': {
                    'windows': [
                        ['ipconfig', '/release'],
                        ['timeout', '3'],
                        ['ipconfig', '/renew']
                    ],
                    'linux': [
                        ['sudo', 'dhclient', '-r'],
                        ['sudo', 'dhclient']
                    ],
                    'macos': [
                        ['sudo', 'ipconfig', 'set', 'en0', 'BOOTP'],
                        ['sudo', 'ipconfig', 'set', 'en0', 'DHCP']
                    ]
                }
            },
            {
                'name': 'reset_network_adapter',
                'description': 'Reset network adapter configuration',
                'priority': 2,
                'requires_admin': True,
                'commands': {
                    'windows': ['netsh', 'winsock', 'reset'],
                    'linux': ['sudo', 'systemctl', 'restart', 'NetworkManager'],
                    'macos': [
                        ['networksetup', '-setairportpower', 'en0', 'off'],
                        ['sleep', '5'],
                        ['networksetup', '-setairportpower', 'en0', 'on']
                    ]
                }
            },
            {
                'name': 'reset_tcp_ip_stack',
                'description': 'Reset TCP/IP stack',
                'priority': 3,
                'requires_admin': True,
                'commands': {
                    'windows': [
                        ['netsh', 'int', 'ip', 'reset'],
                        ['netsh', 'int', 'tcp', 'reset']
                    ],
                    'linux': ['sudo', 'systemctl', 'restart', 'networking'],
                    'macos': [
                        ['sudo', 'ifconfig', 'en0', 'down'],
                        ['sleep', '3'],
                        ['sudo', 'ifconfig', 'en0', 'up']
                    ]
                }
            }
        ]
        
        # Sort by priority
        fixes_to_try.sort(key=lambda x: x['priority'])
        
        for fix in fixes_to_try:
            if progress_bar and HAS_TQDM:
                progress_bar.set_description(f"{'Previewing' if dry_run else 'Applying'} {fix['description'].lower()}")
            
            fix_result = self._attempt_fix(fix, dry_run)
            fix_results['fixes_attempted'].append(fix_result)
            
            if fix_result['success']:
                fix_results['fixes_successful'].append(fix_result['name'])
            else:
                fix_results['fixes_failed'].append(fix_result['name'])
            
            if fix['requires_admin']:
                fix_results['requires_admin'] = True
            
            if progress_bar and HAS_TQDM:
                progress_bar.update(1)
        
        return fix_results
    
    def _fix_interface_issues(self, fix_results: Dict[str, any], interface_results: Dict[str, any], dry_run: bool, progress_bar=None) -> Dict[str, any]:
        """Attempt to fix network interface issues."""
        self.logger.info("Attempting interface fixes...")
        
        fixes_to_try = [
            {
                'name': 'disable_enable_adapter',
                'description': 'Disable and re-enable primary network adapter',
                'priority': 1,
                'requires_admin': True,
                'commands': {
                    'windows': [
                        ['powershell', '-Command', 'Get-NetAdapter | Where-Object {$_.Status -eq "Up"} | Select-Object -First 1 | Disable-NetAdapter -Confirm:$false'],
                        ['timeout', '5'],
                        ['powershell', '-Command', 'Get-NetAdapter | Where-Object {$_.Status -eq "Disabled"} | Select-Object -First 1 | Enable-NetAdapter -Confirm:$false']
                    ],
                    'linux': [
                        ['sudo', 'ip', 'link', 'set', 'dev', 'eth0', 'down'],
                        ['sleep', '5'],
                        ['sudo', 'ip', 'link', 'set', 'dev', 'eth0', 'up']
                    ],
                    'macos': [
                        ['sudo', 'ifconfig', 'en0', 'down'],
                        ['sleep', '5'],
                        ['sudo', 'ifconfig', 'en0', 'up']
                    ]
                }
            }
        ]
        
        for fix in fixes_to_try:
            if progress_bar and HAS_TQDM:
                progress_bar.set_description(f"{'Previewing' if dry_run else 'Applying'} {fix['description'].lower()}")
            
            fix_result = self._attempt_fix(fix, dry_run)
            fix_results['fixes_attempted'].append(fix_result)
            
            if fix_result['success']:
                fix_results['fixes_successful'].append(fix_result['name'])
            else:
                fix_results['fixes_failed'].append(fix_result['name'])
            
            if fix['requires_admin']:
                fix_results['requires_admin'] = True
            
            if progress_bar and HAS_TQDM:
                progress_bar.update(1)
        
        return fix_results
    
    def _fix_windows_network_issues(self, fix_results: Dict[str, any], results: Dict[str, any], dry_run: bool, progress_bar=None) -> Dict[str, any]:
        """Windows-specific network fixes."""
        self.logger.info("Attempting Windows-specific fixes...")
        
        fixes_to_try = [
            {
                'name': 'reset_winsock',
                'description': 'Reset Winsock catalog',
                'priority': 1,
                'requires_admin': True,
                'commands': {
                    'windows': ['netsh', 'winsock', 'reset']
                }
            },
            {
                'name': 'restart_network_services',
                'description': 'Restart essential network services',
                'priority': 2,
                'requires_admin': True,
                'commands': {
                    'windows': [
                        ['net', 'stop', 'dnscache'],
                        ['timeout', '2'],
                        ['net', 'start', 'dnscache'],
                        ['net', 'stop', 'dhcp'],
                        ['timeout', '2'],
                        ['net', 'start', 'dhcp']
                    ]
                }
            },
            {
                'name': 'reset_firewall',
                'description': 'Reset Windows Firewall to defaults (USE WITH CAUTION)',
                'priority': 3,
                'requires_admin': True,
                'commands': {
                    'windows': ['netsh', 'advfirewall', 'reset']
                }
            }
        ]
        
        # Sort by priority
        fixes_to_try.sort(key=lambda x: x['priority'])
        
        for fix in fixes_to_try:
            if progress_bar and HAS_TQDM:
                progress_bar.set_description(f"{'Previewing' if dry_run else 'Applying'} {fix['description'].lower()}")
            
            fix_result = self._attempt_fix(fix, dry_run)
            fix_results['fixes_attempted'].append(fix_result)
            
            if fix_result['success']:
                fix_results['fixes_successful'].append(fix_result['name'])
            else:
                fix_results['fixes_failed'].append(fix_result['name'])
            
            if fix['requires_admin']:
                fix_results['requires_admin'] = True
            
            if progress_bar and HAS_TQDM:
                progress_bar.update(1)
        
        return fix_results
    
    def _attempt_fix(self, fix_config: Dict[str, any], dry_run: bool) -> Dict[str, any]:
        """Attempt to execute a specific fix."""
        fix_result = {
            'name': fix_config['name'],
            'description': fix_config['description'],
            'priority': fix_config.get('priority', 999),
            'success': False,
            'output': '',
            'error': '',
            'dry_run': dry_run,
            'execution_time': 0,
            'skipped': False,
            'user_declined': False
        }
        
        start_time = time.time()
        
        try:
            os_type = self.os_info['os_type']
            commands = fix_config.get('commands', {}).get(os_type, [])
            
            if not commands:
                fix_result['error'] = f"No commands defined for {os_type}"
                return fix_result
            
            # Check if this is a destructive operation that needs user confirmation
            destructive_operations = {
                'reset_firewall': {
                    'description': 'Reset Windows Firewall to defaults',
                    'warning': 'This will remove ALL custom firewall rules and may affect VPN, remote access, and security policies.',
                    'impact': 'HIGH RISK - May break network access for applications and services'
                },
                'reset_tcp_ip_stack': {
                    'description': 'Reset TCP/IP stack',
                    'warning': 'This will reset all TCP/IP settings and may require a system restart.',
                    'impact': 'MEDIUM RISK - May cause temporary network disconnection'
                },
                'disable_enable_adapter': {
                    'description': 'Disable and re-enable network adapter',
                    'warning': 'This will temporarily disconnect all network access.',
                    'impact': 'MEDIUM RISK - Brief network interruption (5-10 seconds)'
                },
                'reset_network_adapter': {
                    'description': 'Reset network adapter configuration',
                    'warning': 'This will reset Winsock settings and may affect network connectivity.',
                    'impact': 'MEDIUM RISK - May require restart for full effect'
                }
            }
            
            if fix_config['name'] in destructive_operations and not dry_run:
                destructive_info = destructive_operations[fix_config['name']]
                
                print(f"\n⚠️  DESTRUCTIVE OPERATION DETECTED ⚠️")
                print(f"Operation: {destructive_info['description']}")
                print(f"Impact: {destructive_info['impact']}")
                print(f"Warning: {destructive_info['warning']}")
                print(f"\nThis operation cannot be easily undone!")
                
                while True:
                    choice = input(f"\nProceed with '{fix_config['description']}'? (y/N/s for skip): ").strip().lower()
                    
                    if choice == 'y' or choice == 'yes':
                        print(f"✓ User approved: {fix_config['description']}")
                        break
                    elif choice == 's' or choice == 'skip':
                        print(f"⏩ User skipped: {fix_config['description']}")
                        fix_result['skipped'] = True
                        fix_result['success'] = True  # Consider skip as success
                        fix_result['output'] = "Skipped by user request"
                        return fix_result
                    elif choice == 'n' or choice == 'no' or choice == '':
                        print(f"❌ User declined: {fix_config['description']}")
                        fix_result['user_declined'] = True
                        fix_result['error'] = "User declined to execute this fix"
                        return fix_result
                    else:
                        print("Please enter 'y' (yes), 'n' (no), or 's' (skip)")
            
            if dry_run:
                # Show destructive warning even in dry run
                if fix_config['name'] in destructive_operations:
                    destructive_info = destructive_operations[fix_config['name']]
                    fix_result['output'] = f"DRY RUN: Would execute {len(commands)} command(s) [⚠️ {destructive_info['impact']}]"
                else:
                    fix_result['output'] = f"DRY RUN: Would execute {len(commands)} command(s)"
                fix_result['success'] = True
                return fix_result
            
            # Execute commands
            all_outputs = []
            for cmd in commands:
                if isinstance(cmd, list):
                    code, stdout, stderr = CommandRunner.run_command(cmd, timeout=30, check_return_code=False)
                    all_outputs.append(f"Command: {' '.join(cmd)}\nOutput: {stdout}")
                    
                    if code != 0 and 'timeout' not in cmd[0].lower():  # Allow timeout commands to "fail"
                        fix_result['error'] = f"Command failed: {stderr}"
                        return fix_result
                else:
                    # String command (shell)
                    code, stdout, stderr = CommandRunner.run_command([cmd], shell=True, timeout=30, check_return_code=False)
                    all_outputs.append(f"Command: {cmd}\nOutput: {stdout}")
                    
                    if code != 0:
                        fix_result['error'] = f"Command failed: {stderr}"
                        return fix_result
            
            fix_result['output'] = '\n\n'.join(all_outputs)
            fix_result['success'] = True
            
        except Exception as e:
            fix_result['error'] = str(e)
        
        finally:
            fix_result['execution_time'] = round(time.time() - start_time, 2)
        
        return fix_result
    
    def _add_recommendations(self, fix_results: Dict[str, any], diagnostic_results: Dict[str, any]) -> None:
        """Add manual recommendations when automated fixes aren't sufficient."""
        recommendations = []
        
        # Check for persistent DNS issues
        dns_results = diagnostic_results.get('dns_resolution', {})
        if dns_results.get('failed_resolutions', 0) > 2:
            recommendations.append(
                "Consider checking router DNS settings or contacting ISP if DNS issues persist"
            )
        
        # Check for connectivity issues
        conn_results = diagnostic_results.get('connectivity_tests', {})
        if conn_results.get('failed_pings', 0) >= conn_results.get('successful_pings', 1):
            recommendations.append(
                "Check physical network cables and router connectivity if ping failures persist"
            )
        
        # Check for firewall issues
        if self.os_info['os_type'] == 'windows':
            recommendations.append(
                "Consider temporarily disabling Windows Firewall to test connectivity"
            )
        
        # Performance recommendations
        bandwidth = diagnostic_results.get('bandwidth_test', {})
        if bandwidth.get('assessment') == 'poor':
            recommendations.extend([
                "Consider running bandwidth tests at different times to rule out network congestion",
                "Check for background applications consuming bandwidth",
                "Contact ISP if consistent poor performance occurs"
            ])
        
        fix_results['recommendations'].extend(recommendations)


def main():
    """Main function for standalone execution."""
    import argparse
    from network_diagnostics import NetworkDiagnostics
    
    parser = argparse.ArgumentParser(description='Network repair toolkit - fixes common network issues')
    parser.add_argument('--hosts', nargs='+', default=['8.8.8.8', 'google.com'],
                       help='Hosts to test connectivity to for diagnostics')
    parser.add_argument('--verbose', action='store_true',
                       help='Enable verbose logging')
    parser.add_argument('--dry-run', action='store_true', default=True,
                       help='Show what fixes would be attempted (default: True)')
    parser.add_argument('--execute-fixes', action='store_true',
                       help='Actually execute fixes (overrides --dry-run)')
    parser.add_argument('--skip-diagnostics', action='store_true',
                       help='Skip initial diagnostics (use with caution)')
    parser.add_argument('--no-progress', action='store_true',
                       help='Disable progress bars')
    parser.add_argument('--auto-approve-destructive', action='store_true',
                       help='Auto-approve destructive operations (DANGEROUS - use with caution)')
    
    args = parser.parse_args()
    
    # Setup logging
    log_level = 'DEBUG' if args.verbose else 'INFO'
    logger = LogManager.setup_logging(log_level)
    
    # Determine if this is a dry run
    dry_run = args.dry_run and not args.execute_fixes
    show_progress = not args.no_progress
    
    if dry_run:
        logger.info("Running in DRY RUN mode - no changes will be made")
    else:
        logger.warning("EXECUTING FIXES - network changes will be made")
    
    if not HAS_TQDM and show_progress:
        print("💡 For enhanced progress bars, install tqdm: pip install tqdm")
    
    # Run diagnostics first (unless skipped)
    if not args.skip_diagnostics:
        print("=== Running Network Diagnostics ===")
        diagnostics = NetworkDiagnostics(logger)
        diagnostic_results = diagnostics.run_full_diagnostics(args.hosts)
        
        print(f"Network Status: {diagnostic_results['overall_status'].upper()}")
        
        if diagnostic_results['overall_status'] == 'healthy':
            print("✅ Network appears healthy - no fixes needed")
            return
    else:
        # Create dummy results for repair testing
        diagnostic_results = {
            'overall_status': 'major_issues',
            'dns_resolution': {'failed_resolutions': 2, 'successful_resolutions': 1},
            'connectivity_tests': {'failed_pings': 2, 'successful_pings': 1},
            'network_interfaces': {'error': 'test'},
            'bandwidth_test': {'assessment': 'poor'}
        }
        print("⚠️  Skipping diagnostics - assuming network issues exist")
    
    # Run repair attempts
    print(f"\n=== Network Repair Results {'(DRY RUN)' if dry_run else '(LIVE EXECUTION)'} ===")
    
    if args.auto_approve_destructive and not dry_run:
        print("⚠️  AUTO-APPROVE MODE: Destructive operations will proceed without confirmation!")
    
    repair = NetworkRepair(logger)
    fix_results = repair.run_automated_fixes(diagnostic_results, dry_run, show_progress, args.auto_approve_destructive)
    
    print(f"Fixes Attempted: {len(fix_results['fixes_attempted'])}")
    print(f"Fixes Successful: {len(fix_results['fixes_successful'])}")
    print(f"Fixes Failed: {len(fix_results['fixes_failed'])}")
    
    if fix_results.get('fixes_skipped'):
        print(f"Fixes Skipped: {len(fix_results['fixes_skipped'])}")
    
    if fix_results.get('fixes_declined'):
        print(f"Fixes Declined: {len(fix_results['fixes_declined'])}")
    
    if fix_results['requires_admin']:
        print("⚠️  Some fixes require administrator privileges")
    
    # Show detailed results
    for fix in fix_results['fixes_attempted']:
        if fix.get('skipped'):
            status = "⏩ SKIPPED"
        elif fix.get('user_declined'):
            status = "❌ DECLINED"
        elif fix['success']:
            status = "✅ SUCCESS"
        else:
            status = "❌ FAILED"
        
        priority = f"[P{fix['priority']}]" if 'priority' in fix else ""
        exec_time = f"({fix['execution_time']}s)" if 'execution_time' in fix else ""
        
        print(f"  {status} {priority} {fix['description']} {exec_time}")
        
        if fix.get('user_declined') and fix['error']:
            print(f"    Reason: {fix['error']}")
        elif not fix['success'] and fix['error'] and not fix.get('skipped'):
            print(f"    Error: {fix['error']}")
        elif args.verbose and fix['output'] and not fix.get('skipped'):
            print(f"    Output: {fix['output'][:100]}...")
    
    # Show recommendations
    if fix_results['recommendations']:
        print("\n=== Manual Recommendations ===")
        for i, rec in enumerate(fix_results['recommendations'], 1):
            print(f"  {i}. {rec}")
    
    if not dry_run and fix_results['fixes_successful']:
        print("\n💡 Consider re-running diagnostics to verify fixes were successful")


if __name__ == '__main__':
    main()