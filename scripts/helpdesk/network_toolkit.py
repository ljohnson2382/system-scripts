#!/usr/bin/env python3
"""
Comprehensive network toolkit combining diagnostics and repair functionality.
This script demonstrates the clean integration of modular network tools.

Author: Loyd Johnson
Date: November 2025
"""

import os
import sys
import time
import argparse
from typing import Dict, List, Optional

try:
    from tqdm import tqdm
    HAS_TQDM = True
except ImportError:
    HAS_TQDM = False
    print("💡 Install 'tqdm' for enhanced progress bars: pip install tqdm")

# Add parent directories to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))
from utils.system_utils import LogManager
from network_diagnostics import NetworkDiagnostics
from network_repair import NetworkRepair


class ProgressTracker:
    """Simple progress tracker with fallback for when tqdm is not available."""
    
    def __init__(self, total: int, desc: str = "Progress", disable: bool = False):
        self.total = total
        self.desc = desc
        self.current = 0
        self.disable = disable
        
        if HAS_TQDM and not disable:
            self.pbar = tqdm(total=total, desc=desc, ncols=80, 
                           bar_format='{l_bar}{bar}| {n_fmt}/{total_fmt} [{elapsed}<{remaining}]')
        else:
            self.pbar = None
            if not disable:
                print(f"🔄 {desc}... (0/{total})")
    
    def update(self, n: int = 1, desc: str = None):
        """Update progress by n steps."""
        self.current += n
        
        if self.pbar:
            if desc:
                self.pbar.set_description(desc)
            self.pbar.update(n)
        elif not self.disable:
            status_desc = desc or self.desc
            print(f"🔄 {status_desc}... ({self.current}/{self.total})")
    
    def set_description(self, desc: str):
        """Update the description."""
        self.desc = desc
        if self.pbar:
            self.pbar.set_description(desc)
    
    def close(self):
        """Close the progress bar."""
        if self.pbar:
            self.pbar.close()
        elif not self.disable:
            print(f"✅ {self.desc} completed ({self.current}/{self.total})")
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()


class NetworkToolkit:
    """Comprehensive network diagnostics and repair toolkit."""
    
    def __init__(self, verbose: bool = False):
        """Initialize the network toolkit."""
        log_level = 'DEBUG' if verbose else 'INFO'
        self.logger = LogManager.setup_logging(log_level)
        
        self.diagnostics = NetworkDiagnostics(self.logger)
        self.repair = NetworkRepair(self.logger)
    
    def run_comprehensive_analysis(
        self, 
        target_hosts: List[str] = None,
        auto_fix: bool = False,
        dry_run: bool = True,
        max_fix_attempts: int = 1,
        show_progress: bool = True,
        auto_approve_destructive: bool = False
    ) -> Dict[str, any]:
        """
        Run complete network analysis with optional automated repair.
        
        Args:
            target_hosts: List of hosts to test connectivity to
            auto_fix: Whether to attempt automated fixes
            dry_run: If True, only show what fixes would be attempted
            max_fix_attempts: Maximum number of fix cycles to attempt
            show_progress: Whether to show progress bars
            
        Returns:
            Comprehensive results dictionary
        """
        # Calculate total steps for progress tracking
        total_steps = 1  # Initial diagnostics
        if auto_fix:
            total_steps += max_fix_attempts
            if not dry_run:
                total_steps += 1  # Final diagnostics
        
        results = {
            'session_start': time.time(),
            'initial_diagnostics': None,
            'fix_attempts': [],
            'final_diagnostics': None,
            'summary': {}
        }
        
        with ProgressTracker(total_steps, "Network Analysis", disable=not show_progress) as pbar:
            # Phase 1: Initial Diagnostics
            pbar.set_description("🔍 Running network diagnostics")
            self.logger.info("=== Phase 1: Initial Network Diagnostics ===")
            
            results['initial_diagnostics'] = self._run_diagnostics_with_feedback(
                target_hosts, "Initial Diagnostics", show_progress and total_steps > 1
            )
            
            initial_status = results['initial_diagnostics']['overall_status']
            self.logger.info(f"Initial network status: {initial_status}")
            pbar.update(1, f"✅ Diagnostics complete: {initial_status.replace('_', ' ').title()}")
            
            # Phase 2: Automated Repair (if needed and requested)
            if auto_fix and initial_status != 'healthy':
                self.logger.info("=== Phase 2: Automated Network Repair ===")
                
                current_results = results['initial_diagnostics']
                
                for attempt in range(1, max_fix_attempts + 1):
                    pbar.set_description(f"🔧 Repair attempt {attempt}/{max_fix_attempts}")
                    self.logger.info(f"Fix attempt {attempt}/{max_fix_attempts}")
                    
                    fix_results = self._run_repairs_with_feedback(
                        current_results, dry_run, f"Repair Attempt {attempt}", show_progress, auto_approve_destructive
                    )
                    
                    results['fix_attempts'].append({
                        'attempt': attempt,
                        'results': fix_results
                    })
                    
                    successful_fixes = len(fix_results.get('fixes_successful', []))
                    total_fixes = len(fix_results.get('fixes_attempted', []))
                    
                    if dry_run:
                        pbar.update(1, f"✅ Dry run: {total_fixes} fixes previewed")
                        break
                    elif not fix_results.get('fixes_successful'):
                        pbar.update(1, f"❌ No successful fixes in attempt {attempt}")
                        break
                    else:
                        pbar.update(1, f"🔧 Applied {successful_fixes}/{total_fixes} fixes")
                        
                        # Wait for network changes to take effect
                        self._wait_with_feedback(10, "Allowing network changes to stabilize", show_progress)
                        
                        # Re-run diagnostics to check if issues were resolved
                        current_results = self.diagnostics.run_full_diagnostics(target_hosts)
                        
                        if current_results['overall_status'] == 'healthy':
                            self.logger.info("Network issues resolved!")
                            pbar.set_description("🎉 Network issues resolved")
                            break
            
            # Phase 3: Final Diagnostics (if fixes were actually applied)
            if auto_fix and not dry_run and results['fix_attempts'] and any(attempt['results'].get('fixes_successful') for attempt in results['fix_attempts']):
                pbar.set_description("🔍 Running post-repair diagnostics")
                self.logger.info("=== Phase 3: Post-Repair Diagnostics ===")
                
                results['final_diagnostics'] = self._run_diagnostics_with_feedback(
                    target_hosts, "Post-Repair Diagnostics", show_progress and HAS_TQDM
                )
                
                final_status = results['final_diagnostics']['overall_status']
                pbar.update(1, f"✅ Final status: {final_status.replace('_', ' ').title()}")
            
            # Generate summary
            pbar.set_description("📊 Generating analysis summary")
            results['summary'] = self._generate_summary(results)
            results['session_duration'] = time.time() - results['session_start']
        
        return results
    
    def _run_diagnostics_with_feedback(self, target_hosts: List[str], phase_name: str, show_detailed: bool = False) -> Dict[str, any]:
        """Run diagnostics with progress feedback."""
        if show_detailed and HAS_TQDM:
            # Detailed progress for individual diagnostic steps
            diagnostic_steps = [
                "Network interfaces", "DNS resolution", "Connectivity tests", 
                "Routing info", "Port scans", "Bandwidth test"
            ]
            
            with ProgressTracker(len(diagnostic_steps), phase_name) as diag_pbar:
                print(f"\n🔍 {phase_name}:")
                
                # Initialize results dictionary
                results = {
                    'timestamp': time.strftime('%Y-%m-%dT%H:%M:%S'),
                    'network_interfaces': {},
                    'dns_resolution': {},
                    'connectivity_tests': {},
                    'routing_info': {},
                    'port_scans': {},
                    'bandwidth_test': {},
                    'overall_status': 'unknown'
                }
                
                # Step 1: Network interfaces
                diag_pbar.set_description("Getting network interfaces")
                try:
                    results['network_interfaces'] = self.diagnostics.get_network_interfaces()
                except Exception as e:
                    results['network_interfaces'] = {'error': str(e)}
                diag_pbar.update(1)
                
                # Step 2: DNS resolution
                diag_pbar.set_description("Testing DNS resolution")
                try:
                    results['dns_resolution'] = self.diagnostics.test_dns_resolution()
                except Exception as e:
                    results['dns_resolution'] = {'error': str(e)}
                diag_pbar.update(1)
                
                # Step 3: Connectivity tests
                diag_pbar.set_description("Testing connectivity")
                try:
                    results['connectivity_tests'] = self.diagnostics.test_connectivity(target_hosts or ['8.8.8.8', 'google.com', '1.1.1.1'])
                except Exception as e:
                    results['connectivity_tests'] = {'error': str(e)}
                diag_pbar.update(1)
                
                # Step 4: Routing info
                diag_pbar.set_description("Getting routing information")
                try:
                    results['routing_info'] = self.diagnostics.get_routing_info()
                except Exception as e:
                    results['routing_info'] = {'error': str(e)}
                diag_pbar.update(1)
                
                # Step 5: Port scans
                diag_pbar.set_description("Scanning common ports")
                try:
                    results['port_scans'] = self.diagnostics.scan_common_ports()
                except Exception as e:
                    results['port_scans'] = {'error': str(e)}
                diag_pbar.update(1)
                
                # Step 6: Bandwidth test
                diag_pbar.set_description("Testing bandwidth")
                try:
                    results['bandwidth_test'] = self.diagnostics.test_bandwidth()
                except Exception as e:
                    results['bandwidth_test'] = {'error': str(e)}
                diag_pbar.update(1)
                
                # Assess overall health
                results['overall_status'] = self.diagnostics._assess_network_health(results)
                
                return results
        else:
            # Simple progress or no progress
            if show_detailed:
                print(f"\n🔍 {phase_name}: Running comprehensive diagnostics...")
            return self.diagnostics.run_full_diagnostics(target_hosts)
    
    def _run_repairs_with_feedback(self, diagnostic_results: Dict[str, any], dry_run: bool, phase_name: str, show_progress: bool = True, auto_approve_destructive: bool = False) -> Dict[str, any]:
        """Run repairs with progress feedback."""
        if not show_progress:
            return self.repair.run_automated_fixes(diagnostic_results, dry_run, show_progress=False)
        
        print(f"\n🔧 {phase_name}:")
        
        # Count actual fixes that will be attempted
        fix_categories = []
        if diagnostic_results.get('dns_resolution', {}).get('failed_resolutions', 0) > 0:
            fix_categories.append(('DNS fixes', 3))
        if diagnostic_results.get('connectivity_tests', {}).get('failed_pings', 0) > 0:
            fix_categories.append(('Connectivity fixes', 3))
        if 'error' in diagnostic_results.get('network_interfaces', {}):
            fix_categories.append(('Interface fixes', 1))
        if diagnostic_results.get('overall_status') in ['minor_issues', 'major_issues']:
            # Only add Windows fixes if we're on Windows
            if self.repair.os_info['os_type'] == 'windows':
                fix_categories.append(('Windows fixes', 3))
        
        if not fix_categories:
            print("   ✅ No fixes needed")
            return {'fixes_attempted': [], 'fixes_successful': [], 'fixes_failed': [], 'dry_run': dry_run}
        
        total_fixes = sum(count for _, count in fix_categories)
        mode_text = "DRY RUN" if dry_run else "EXECUTING"
        
        # Create a progress tracker that we'll update manually
        with ProgressTracker(total_fixes, f"{mode_text} Fixes") as fix_pbar:
            
            # Create a custom repair instance with progress callback
            class ProgressAwareRepair(NetworkRepair):
                def __init__(self, repair_instance, progress_callback):
                    self.__dict__.update(repair_instance.__dict__)
                    self.progress_callback = progress_callback
                
                def _attempt_fix(self, fix_config, dry_run_inner):
                    # Update progress before attempting fix
                    action = "Preview" if dry_run_inner else "Apply"
                    self.progress_callback(f"{action}: {fix_config['description']}")
                    
                    # Call original method
                    result = super()._attempt_fix(fix_config, dry_run_inner)
                    
                    # Update progress after completion
                    status = "✅" if result['success'] else "❌"
                    self.progress_callback(f"{status} {fix_config['description']}")
                    
                    return result
            
            def progress_callback(description):
                fix_pbar.set_description(description)
                fix_pbar.update(1)
            
            # Create progress-aware repair instance
            progress_repair = ProgressAwareRepair(self.repair, progress_callback)
            
            # Run the fixes
            return progress_repair.run_automated_fixes(diagnostic_results, dry_run, show_progress=False, auto_approve_destructive=auto_approve_destructive)
    
    def _wait_with_feedback(self, seconds: int, description: str, show_progress: bool = True):
        """Wait with visual feedback."""
        if not show_progress:
            time.sleep(seconds)
            return
        
        if HAS_TQDM:
            with tqdm(total=seconds, desc=description, ncols=60, 
                     bar_format='{l_bar}{bar}| {elapsed}s') as wait_bar:
                for _ in range(seconds):
                    time.sleep(1)
                    wait_bar.update(1)
        else:
            print(f"⏳ {description} ({seconds}s)...")
            for i in range(seconds):
                time.sleep(1)
                dots = '.' * ((i % 3) + 1)
                print(f"\r⏳ {description} ({seconds - i - 1}s remaining){dots}   ", end='', flush=True)
            print(f"\r✅ {description} completed" + " " * 20)
    
    def _generate_summary(self, results: Dict[str, any]) -> Dict[str, any]:
        """Generate a comprehensive summary of the network analysis session."""
        initial = results['initial_diagnostics']
        final = results.get('final_diagnostics')
        fix_attempts = results.get('fix_attempts', [])
        
        summary = {
            'initial_status': initial['overall_status'],
            'final_status': final['overall_status'] if final else initial['overall_status'],
            'improvement': False,
            'total_fixes_attempted': 0,
            'total_fixes_successful': 0,
            'issues_resolved': [],
            'issues_remaining': [],
            'recommendations': []
        }
        
        # Calculate fix statistics
        for attempt in fix_attempts:
            attempt_results = attempt['results']
            summary['total_fixes_attempted'] += len(attempt_results.get('fixes_attempted', []))
            summary['total_fixes_successful'] += len(attempt_results.get('fixes_successful', []))
        
        # Determine if there was improvement
        if final:
            status_order = {'healthy': 3, 'minor_issues': 2, 'major_issues': 1, 'unknown': 0}
            initial_score = status_order.get(summary['initial_status'], 0)
            final_score = status_order.get(summary['final_status'], 0)
            summary['improvement'] = final_score > initial_score
        
        # Analyze specific issues
        initial_dns = initial.get('dns_resolution', {})
        initial_conn = initial.get('connectivity_tests', {})
        
        if final:
            final_dns = final.get('dns_resolution', {})
            final_conn = final.get('connectivity_tests', {})
            
            # Check DNS improvement
            if (initial_dns.get('failed_resolutions', 0) > 0 and 
                final_dns.get('failed_resolutions', 0) == 0):
                summary['issues_resolved'].append('DNS resolution issues')
            elif final_dns.get('failed_resolutions', 0) > 0:
                summary['issues_remaining'].append('DNS resolution issues')
            
            # Check connectivity improvement
            if (initial_conn.get('failed_pings', 0) > 0 and 
                final_conn.get('failed_pings', 0) == 0):
                summary['issues_resolved'].append('Network connectivity issues')
            elif final_conn.get('failed_pings', 0) > 0:
                summary['issues_remaining'].append('Network connectivity issues')
        else:
            # No final diagnostics, list current issues
            if initial_dns.get('failed_resolutions', 0) > 0:
                summary['issues_remaining'].append('DNS resolution issues')
            if initial_conn.get('failed_pings', 0) > 0:
                summary['issues_remaining'].append('Network connectivity issues')
        
        # Add recommendations based on results
        if summary['final_status'] != 'healthy':
            if fix_attempts and not fix_attempts[-1]['results'].get('fixes_successful'):
                summary['recommendations'].append("Consider manual network configuration review")
            if summary['issues_remaining']:
                summary['recommendations'].append("Check hardware connections and router configuration")
            summary['recommendations'].append("Contact network administrator or ISP if issues persist")
        
        return summary
    
    def print_comprehensive_report(self, results: Dict[str, any]) -> None:
        """Print a detailed, professional report of the network analysis."""
        print("\n" + "="*70)
        print("           COMPREHENSIVE NETWORK ANALYSIS REPORT")
        print("="*70)
        
        # Session Information
        print(f"\nSession Duration: {results.get('session_duration', 0):.1f} seconds")
        print(f"Analysis Date: {results['initial_diagnostics']['timestamp']}")
        
        # Executive Summary
        print(f"\n--- EXECUTIVE SUMMARY ---")
        summary = results['summary']
        print(f"Initial Status:  {summary['initial_status'].upper().replace('_', ' ')}")
        print(f"Final Status:    {summary['final_status'].upper().replace('_', ' ')}")
        
        if summary['improvement']:
            print("Result:          ✅ NETWORK IMPROVED")
        elif summary['final_status'] == 'healthy':
            print("Result:          ✅ NETWORK HEALTHY")
        elif summary['total_fixes_attempted'] > 0:
            print("Result:          ⚠️  PARTIAL IMPROVEMENT")
        else:
            print("Result:          ❌ ISSUES DETECTED")
        
        # Detailed Diagnostics
        print(f"\n--- INITIAL DIAGNOSTICS ---")
        initial = results['initial_diagnostics']
        self._print_diagnostic_summary(initial)
        
        # Fix Attempts
        if results.get('fix_attempts'):
            print(f"\n--- AUTOMATED REPAIR ATTEMPTS ---")
            for i, attempt in enumerate(results['fix_attempts'], 1):
                attempt_results = attempt['results']
                print(f"\nAttempt {i}:")
                print(f"  Fixes Attempted: {len(attempt_results.get('fixes_attempted', []))}")
                print(f"  Fixes Successful: {len(attempt_results.get('fixes_successful', []))}")
                print(f"  Fixes Failed: {len(attempt_results.get('fixes_failed', []))}")
                
                if attempt_results.get('fixes_attempted'):
                    for fix in attempt_results['fixes_attempted']:
                        status = "✅" if fix['success'] else "❌"
                        print(f"    {status} {fix['description']}")
        
        # Final Diagnostics
        if results.get('final_diagnostics'):
            print(f"\n--- POST-REPAIR DIAGNOSTICS ---")
            self._print_diagnostic_summary(results['final_diagnostics'])
        
        # Summary and Recommendations
        print(f"\n--- SUMMARY ---")
        if summary['issues_resolved']:
            print("✅ Issues Resolved:")
            for issue in summary['issues_resolved']:
                print(f"   • {issue}")
        
        if summary['issues_remaining']:
            print("⚠️  Issues Remaining:")
            for issue in summary['issues_remaining']:
                print(f"   • {issue}")
        
        if summary['recommendations']:
            print("\n💡 Recommendations:")
            for rec in summary['recommendations']:
                print(f"   • {rec}")
        
        print("\n" + "="*70)
    
    def _print_diagnostic_summary(self, diagnostics: Dict[str, any]) -> None:
        """Print a summary of diagnostic results."""
        # DNS Results
        dns = diagnostics.get('dns_resolution', {})
        if dns:
            total_dns = dns.get('successful_resolutions', 0) + dns.get('failed_resolutions', 0)
            print(f"DNS Resolution:     {dns.get('successful_resolutions', 0)}/{total_dns} successful")
        
        # Connectivity Results
        conn = diagnostics.get('connectivity_tests', {})
        if conn:
            total_conn = conn.get('successful_pings', 0) + conn.get('failed_pings', 0)
            print(f"Connectivity:       {conn.get('successful_pings', 0)}/{total_conn} successful")
        
        # Performance Assessment
        bandwidth = diagnostics.get('bandwidth_test', {})
        if bandwidth:
            assessment = bandwidth.get('assessment', 'unknown').title()
            avg_ping = bandwidth.get('average_ping_ms', 'N/A')
            print(f"Performance:        {assessment} (avg: {avg_ping}ms)")
        
        # Port Scan Results
        ports = diagnostics.get('port_scans', {})
        if ports:
            print(f"Open Ports:         {len(ports.get('open_ports', []))}")


def main():
    """Main function demonstrating the integrated network toolkit."""
    parser = argparse.ArgumentParser(
        description='Comprehensive Network Diagnostics and Repair Toolkit',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Basic diagnostics only
  python network_toolkit.py
  
  # Diagnostics with dry-run repair preview
  python network_toolkit.py --auto-fix --dry-run
  
  # Full diagnostics and automated repair
  python network_toolkit.py --auto-fix --execute-fixes
  
  # Verbose output with custom hosts
  python network_toolkit.py --verbose --hosts 8.8.8.8 1.1.1.1 google.com
        """
    )
    
    parser.add_argument('--hosts', nargs='+', default=['8.8.8.8', 'google.com', '1.1.1.1'],
                       help='Hosts to test connectivity to')
    parser.add_argument('--verbose', action='store_true',
                       help='Enable verbose logging')
    parser.add_argument('--auto-fix', action='store_true',
                       help='Attempt automated fixes for detected issues')
    parser.add_argument('--dry-run', action='store_true', default=True,
                       help='Show what fixes would be attempted (default: True)')
    parser.add_argument('--execute-fixes', action='store_true',
                       help='Actually execute fixes (overrides --dry-run)')
    parser.add_argument('--max-attempts', type=int, default=1,
                       help='Maximum number of fix attempts (default: 1)')
    parser.add_argument('--quick', action='store_true',
                       help='Skip comprehensive reporting, show summary only')
    parser.add_argument('--no-progress', action='store_true',
                       help='Disable progress bars and detailed feedback')
    parser.add_argument('--simple-progress', action='store_true',
                       help='Use simple text progress instead of bars')
    parser.add_argument('--auto-approve-destructive', action='store_true',
                       help='Auto-approve destructive operations (DANGEROUS - use with caution)')
    
    args = parser.parse_args()
    
    # Determine execution mode
    dry_run = args.dry_run and not args.execute_fixes
    show_progress = not args.no_progress
    
    # Override tqdm if simple progress requested
    if args.simple_progress:
        global HAS_TQDM
        HAS_TQDM = False
    
    if args.execute_fixes:
        print("⚠️  LIVE MODE: Network changes will be made!")
        confirm = input("Continue? (y/N): ").strip().lower()
        if confirm != 'y':
            print("Operation cancelled.")
            return
    
    # Initialize toolkit
    toolkit = NetworkToolkit(verbose=args.verbose)
    
    # Show startup message with progress info
    if show_progress and not args.quick:
        print("\n🚀 Starting Network Toolkit Analysis...")
        if not HAS_TQDM:
            print("💡 For enhanced progress bars, install tqdm: pip install tqdm")
    
    # Run comprehensive analysis
    results = toolkit.run_comprehensive_analysis(
        target_hosts=args.hosts,
        auto_fix=args.auto_fix,
        dry_run=dry_run,
        max_fix_attempts=args.max_attempts,
        show_progress=show_progress,
        auto_approve_destructive=args.auto_approve_destructive
    )
    
    # Display results
    if args.quick:
        # Quick summary
        summary = results['summary']
        print(f"\n=== NETWORK STATUS: {summary['final_status'].upper().replace('_', ' ')} ===")
        if summary['improvement']:
            print("✅ Network condition improved")
        elif summary['total_fixes_attempted'] > 0:
            print(f"🔧 {summary['total_fixes_successful']}/{summary['total_fixes_attempted']} fixes successful")
        if summary['recommendations']:
            print("💡 Recommendations available (use --verbose for details)")
    else:
        # Comprehensive report
        toolkit.print_comprehensive_report(results)


if __name__ == '__main__':
    main()