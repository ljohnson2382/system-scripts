#!/usr/bin/env python3
"""
Network diagnostics and troubleshooting toolkit.
Common network troubleshooting tasks for help desk support.

Author: Loyd Johnson
Date: November 2025
"""

import os
import sys
import socket
import subprocess
import platform
import json
from datetime import datetime
from typing import Dict, List, Optional, Tuple
import logging

# Add parent directories to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))
from utils.system_utils import OSDetector, CommandRunner, LogManager


class NetworkDiagnostics:
    """Network troubleshooting and diagnostic tools."""
    
    def __init__(self, logger: Optional[logging.Logger] = None):
        """Initialize network diagnostics."""
        self.logger = logger or LogManager.setup_logging()
        self.os_info = OSDetector.get_os_info()
    
    def run_full_diagnostics(self, target_hosts: List[str] = None) -> Dict[str, any]:
        """
        Run comprehensive network diagnostics.
        
        Args:
            target_hosts: List of hosts to test connectivity to
            
        Returns:
            Dictionary with diagnostic results
        """
        if target_hosts is None:
            target_hosts = ['8.8.8.8', 'google.com', '1.1.1.1']
        
        self.logger.info("Starting network diagnostics")
        
        results = {
            'timestamp': datetime.now().isoformat(),
            'network_interfaces': self.get_network_interfaces(),
            'dns_resolution': self.test_dns_resolution(),
            'connectivity_tests': self.test_connectivity(target_hosts),
            'routing_info': self.get_routing_info(),
            'port_scans': self.scan_common_ports(),
            'bandwidth_test': self.test_bandwidth(),
            'overall_status': 'unknown'
        }
        
        # Determine overall network health
        results['overall_status'] = self._assess_network_health(results)
        
        return results
    
    def get_network_interfaces(self) -> Dict[str, any]:
        """Get network interface information."""
        try:
            if self.os_info['os_type'] == 'windows':
                return self._get_windows_interfaces()
            else:
                return self._get_unix_interfaces()
        except Exception as e:
            self.logger.error(f"Failed to get network interfaces: {e}")
            return {'error': str(e)}
    
    def _get_windows_interfaces(self) -> Dict[str, any]:
        """Get Windows network interface info."""
        try:
            code, stdout, stderr = CommandRunner.run_command([
                'powershell', '-Command', 
                'Get-NetAdapter | Select-Object Name,Status,LinkSpeed,MediaType | ConvertTo-Json'
            ])
            
            interfaces = json.loads(stdout)
            if not isinstance(interfaces, list):
                interfaces = [interfaces]
            
            return {
                'interfaces': interfaces,
                'count': len(interfaces)
            }
            
        except Exception as e:
            # Fallback to ipconfig
            code, stdout, stderr = CommandRunner.run_command(['ipconfig', '/all'])
            return {
                'raw_output': stdout,
                'note': 'Parsed from ipconfig /all'
            }
    
    def _get_unix_interfaces(self) -> Dict[str, any]:
        """Get Unix/Linux network interface info."""
        interfaces = {}
        
        try:
            # Try ip command first
            if CommandRunner.is_command_available('ip'):
                code, stdout, stderr = CommandRunner.run_command(['ip', 'addr', 'show'])
                interfaces['ip_addr'] = stdout
            
            # Try ifconfig as fallback
            elif CommandRunner.is_command_available('ifconfig'):
                code, stdout, stderr = CommandRunner.run_command(['ifconfig', '-a'])
                interfaces['ifconfig'] = stdout
            
            # Get interface statistics
            if CommandRunner.is_command_available('ip'):
                code, stdout, stderr = CommandRunner.run_command(['ip', '-s', 'link'])
                interfaces['statistics'] = stdout
            
            return interfaces
            
        except Exception as e:
            return {'error': str(e)}
    
    def test_dns_resolution(self) -> Dict[str, any]:
        """Test DNS resolution capabilities."""
        test_domains = [
            'google.com',
            'microsoft.com', 
            'cloudflare.com',
            'github.com'
        ]
        
        results = {
            'successful_resolutions': 0,
            'failed_resolutions': 0,
            'details': {}
        }
        
        for domain in test_domains:
            try:
                start_time = datetime.now()
                ip_address = socket.gethostbyname(domain)
                end_time = datetime.now()
                
                response_time = (end_time - start_time).total_seconds() * 1000
                
                results['details'][domain] = {
                    'status': 'success',
                    'ip_address': ip_address,
                    'response_time_ms': round(response_time, 2)
                }
                results['successful_resolutions'] += 1
                
            except socket.gaierror as e:
                results['details'][domain] = {
                    'status': 'failed',
                    'error': str(e)
                }
                results['failed_resolutions'] += 1
        
        return results
    
    def test_connectivity(self, hosts: List[str]) -> Dict[str, any]:
        """Test connectivity to specified hosts."""
        results = {
            'successful_pings': 0,
            'failed_pings': 0,
            'details': {}
        }
        
        for host in hosts:
            try:
                ping_result = self._ping_host(host)
                results['details'][host] = ping_result
                
                if ping_result['status'] == 'success':
                    results['successful_pings'] += 1
                else:
                    results['failed_pings'] += 1
                    
            except Exception as e:
                results['details'][host] = {
                    'status': 'error',
                    'error': str(e)
                }
                results['failed_pings'] += 1
        
        return results
    
    def _ping_host(self, host: str, count: int = 4) -> Dict[str, any]:
        """Ping a specific host."""
        try:
            if self.os_info['os_type'] == 'windows':
                cmd = ['ping', '-n', str(count), host]
            else:
                cmd = ['ping', '-c', str(count), host]
            
            code, stdout, stderr = CommandRunner.run_command(
                cmd, timeout=30, check_return_code=False
            )
            
            if code == 0:
                # Parse ping statistics
                lines = stdout.split('\n')
                stats = self._parse_ping_output(lines)
                
                return {
                    'status': 'success',
                    'statistics': stats,
                    'raw_output': stdout
                }
            else:
                return {
                    'status': 'failed',
                    'error': stderr,
                    'raw_output': stdout
                }
                
        except Exception as e:
            return {
                'status': 'error',
                'error': str(e)
            }
    
    def _parse_ping_output(self, lines: List[str]) -> Dict[str, any]:
        """Parse ping command output for statistics."""
        stats = {
            'packets_sent': 0,
            'packets_received': 0,
            'packet_loss_percent': 0,
            'avg_response_time': 0
        }
        
        try:
            for line in lines:
                line = line.lower()
                
                if 'packets transmitted' in line or 'packets sent' in line:
                    # Unix format: "4 packets transmitted, 4 received, 0% packet loss"
                    # Windows format: "Packets: Sent = 4, Received = 4, Lost = 0 (0% loss)"
                    words = line.split()
                    
                    if 'transmitted' in line:
                        stats['packets_sent'] = int(words[0])
                        received_idx = words.index('received,') if 'received,' in words else words.index('received')
                        stats['packets_received'] = int(words[received_idx - 1])
                    elif 'sent' in line and '=' in line:
                        # Windows format parsing
                        for i, word in enumerate(words):
                            if word == 'sent' and i + 2 < len(words):
                                stats['packets_sent'] = int(words[i + 2].rstrip(','))
                            elif word == 'received' and i + 2 < len(words):
                                stats['packets_received'] = int(words[i + 2].rstrip(','))
                
                elif 'avg' in line or 'average' in line:
                    # Extract average response time
                    words = line.split()
                    for word in words:
                        if 'ms' in word:
                            try:
                                stats['avg_response_time'] = float(word.replace('ms', ''))
                                break
                            except ValueError:
                                continue
            
            # Calculate packet loss
            if stats['packets_sent'] > 0:
                stats['packet_loss_percent'] = (
                    (stats['packets_sent'] - stats['packets_received']) / 
                    stats['packets_sent'] * 100
                )
        
        except Exception as e:
            self.logger.warning(f"Could not parse ping output: {e}")
        
        return stats
    
    def get_routing_info(self) -> Dict[str, any]:
        """Get routing table and gateway information."""
        try:
            if self.os_info['os_type'] == 'windows':
                return self._get_windows_routing()
            else:
                return self._get_unix_routing()
        except Exception as e:
            return {'error': str(e)}
    
    def _get_windows_routing(self) -> Dict[str, any]:
        """Get Windows routing information."""
        try:
            # Get routing table
            code, stdout, stderr = CommandRunner.run_command(['route', 'print'])
            
            # Get default gateway
            code2, gateway_output, stderr2 = CommandRunner.run_command([
                'powershell', '-Command',
                'Get-NetRoute -DestinationPrefix "0.0.0.0/0" | Select-Object NextHop'
            ])
            
            return {
                'routing_table': stdout,
                'default_gateway_info': gateway_output
            }
            
        except Exception as e:
            return {'error': str(e)}
    
    def _get_unix_routing(self) -> Dict[str, any]:
        """Get Unix/Linux routing information."""
        routing_info = {}
        
        try:
            # Try modern ip route
            if CommandRunner.is_command_available('ip'):
                code, stdout, stderr = CommandRunner.run_command(['ip', 'route'])
                routing_info['ip_route'] = stdout
            
            # Try classic route command
            if CommandRunner.is_command_available('route'):
                code, stdout, stderr = CommandRunner.run_command(['route', '-n'])
                routing_info['route_table'] = stdout
            
            # Try netstat
            if CommandRunner.is_command_available('netstat'):
                code, stdout, stderr = CommandRunner.run_command(['netstat', '-rn'])
                routing_info['netstat_routes'] = stdout
            
            return routing_info
            
        except Exception as e:
            return {'error': str(e)}
    
    def scan_common_ports(self, host: str = 'localhost') -> Dict[str, any]:
        """Scan common ports to check what services are running."""
        common_ports = [22, 23, 25, 53, 80, 110, 143, 443, 993, 995, 3389, 5432, 3306]
        
        results = {
            'host': host,
            'open_ports': [],
            'closed_ports': [],
            'details': {}
        }
        
        for port in common_ports:
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(2)
                result = sock.connect_ex((host, port))
                sock.close()
                
                if result == 0:
                    results['open_ports'].append(port)
                    results['details'][port] = 'open'
                else:
                    results['closed_ports'].append(port)
                    results['details'][port] = 'closed'
                    
            except Exception as e:
                results['details'][port] = f'error: {str(e)}'
        
        return results
    
    def test_bandwidth(self) -> Dict[str, any]:
        """Basic bandwidth test using ping response times."""
        test_hosts = ['8.8.8.8', '1.1.1.1']
        
        results = {
            'ping_tests': {},
            'assessment': 'unknown'
        }
        
        total_avg_time = 0
        successful_tests = 0
        
        for host in test_hosts:
            ping_result = self._ping_host(host, count=10)
            results['ping_tests'][host] = ping_result
            
            if ping_result['status'] == 'success':
                avg_time = ping_result['statistics']['avg_response_time']
                total_avg_time += avg_time
                successful_tests += 1
        
        if successful_tests > 0:
            overall_avg = total_avg_time / successful_tests
            
            if overall_avg < 50:
                results['assessment'] = 'excellent'
            elif overall_avg < 100:
                results['assessment'] = 'good' 
            elif overall_avg < 200:
                results['assessment'] = 'fair'
            else:
                results['assessment'] = 'poor'
            
            results['average_ping_ms'] = round(overall_avg, 2)
        
        return results
    
    def _assess_network_health(self, results: Dict[str, any]) -> str:
        """Assess overall network health based on test results."""
        issues = []
        
        # Check DNS resolution
        dns_results = results.get('dns_resolution', {})
        if dns_results.get('failed_resolutions', 0) > dns_results.get('successful_resolutions', 0):
            issues.append('dns_issues')
        
        # Check connectivity
        conn_results = results.get('connectivity_tests', {})
        if conn_results.get('failed_pings', 0) > conn_results.get('successful_pings', 0):
            issues.append('connectivity_issues')
        
        # Check bandwidth
        bandwidth = results.get('bandwidth_test', {})
        if bandwidth.get('assessment') == 'poor':
            issues.append('bandwidth_issues')
        
        if not issues:
            return 'healthy'
        elif len(issues) == 1:
            return 'minor_issues'
        else:
            return 'major_issues'


def main():
    """Main function for standalone execution."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Network diagnostics toolkit')
    parser.add_argument('--hosts', nargs='+', default=['8.8.8.8', 'google.com'],
                       help='Hosts to test connectivity to')
    parser.add_argument('--verbose', action='store_true',
                       help='Enable verbose logging')
    
    args = parser.parse_args()
    
    # Setup logging
    log_level = 'DEBUG' if args.verbose else 'INFO'
    logger = LogManager.setup_logging(log_level)
    
    # Run diagnostics
    diagnostics = NetworkDiagnostics(logger)
    results = diagnostics.run_full_diagnostics(args.hosts)
    
    # Print summary
    print(f"\n=== Network Diagnostics Results ===")
    print(f"Overall Status: {results['overall_status'].upper()}")
    print(f"Timestamp: {results['timestamp']}")
    
    # DNS Results
    dns = results.get('dns_resolution', {})
    if dns:
        print(f"DNS Resolution: {dns['successful_resolutions']}/{dns['successful_resolutions'] + dns['failed_resolutions']} successful")
    
    # Connectivity Results  
    conn = results.get('connectivity_tests', {})
    if conn:
        print(f"Ping Tests: {conn['successful_pings']}/{conn['successful_pings'] + conn['failed_pings']} successful")
    
    # Bandwidth Assessment
    bandwidth = results.get('bandwidth_test', {})
    if bandwidth:
        print(f"Network Performance: {bandwidth.get('assessment', 'unknown')}")
        if 'average_ping_ms' in bandwidth:
            print(f"Average Ping: {bandwidth['average_ping_ms']}ms")
    
    # Port Scan Results
    ports = results.get('port_scans', {})
    if ports:
        print(f"Open Ports: {len(ports.get('open_ports', []))}")


if __name__ == '__main__':
    main()