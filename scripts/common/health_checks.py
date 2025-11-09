#!/usr/bin/env python3
"""
Health check module for system monitoring and validation.
Provides SSH connectivity tests, disk space monitoring, uptime checks,
and service status verification.

Author: Loyd Johnson
Date: November 2025
"""

import os
import socket
import subprocess
import shutil
import psutil
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import logging

# Import from our utils module
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))
from utils.system_utils import OSDetector, CommandRunner, LogManager


class HealthChecker:
    """Main class for performing various system health checks."""
    
    def __init__(self, logger: Optional[logging.Logger] = None):
        """
        Initialize health checker.
        
        Args:
            logger: Optional logger instance
        """
        self.logger = logger or LogManager.setup_logging()
        self.os_info = OSDetector.get_os_info()
    
    def run_all_checks(self, config: Optional[Dict] = None) -> Dict[str, Dict]:
        """
        Run all available health checks.
        
        Args:
            config: Optional configuration dictionary
            
        Returns:
            Dictionary with results from all checks
        """
        self.logger.info("Starting comprehensive health check")
        
        # Default configuration
        default_config = {
            'disk_warning_threshold': 80,
            'disk_critical_threshold': 90,
            'memory_warning_threshold': 80,
            'ssh_timeout': 5,
            'check_services': [],
            'check_ports': [],
            'remote_hosts': []
        }
        
        if config:
            default_config.update(config)
        config = default_config
        
        results = {
            'timestamp': datetime.now().isoformat(),
            'system_info': self.get_system_info(),
            'disk_space': self.check_disk_space(
                warning_threshold=config['disk_warning_threshold'],
                critical_threshold=config['disk_critical_threshold']
            ),
            'memory_usage': self.check_memory_usage(
                warning_threshold=config['memory_warning_threshold']
            ),
            'uptime': self.check_uptime(),
            'load_average': self.check_load_average(),
            'services': self.check_services(config['check_services']),
            'ports': self.check_ports(config['check_ports']),
            'network': self.check_network_connectivity(config['remote_hosts'])
        }
        
        # Calculate overall health status
        results['overall_status'] = self._calculate_overall_status(results)
        
        self.logger.info(f"Health check completed. Overall status: {results['overall_status']}")
        return results
    
    def get_system_info(self) -> Dict[str, str]:
        """
        Get basic system information.
        
        Returns:
            Dictionary with system details
        """
        try:
            boot_time = datetime.fromtimestamp(psutil.boot_time())
            uptime = datetime.now() - boot_time
            
            info = {
                'os_type': self.os_info['os_type'],
                'distro': self.os_info['distro'],
                'version': self.os_info['version'],
                'architecture': self.os_info['architecture'],
                'hostname': socket.gethostname(),
                'boot_time': boot_time.isoformat(),
                'uptime_seconds': int(uptime.total_seconds()),
                'uptime_human': str(uptime).split('.')[0]  # Remove microseconds
            }
            
            # Add CPU information
            info['cpu_count'] = psutil.cpu_count(logical=True)
            info['cpu_count_physical'] = psutil.cpu_count(logical=False)
            
            return info
            
        except Exception as e:
            self.logger.error(f"Failed to get system info: {e}")
            return {'error': str(e)}
    
    def check_disk_space(self, warning_threshold: int = 80, 
                        critical_threshold: int = 90) -> Dict[str, Dict]:
        """
        Check disk space usage for all mounted filesystems.
        
        Args:
            warning_threshold: Warning threshold percentage
            critical_threshold: Critical threshold percentage
            
        Returns:
            Dictionary with disk usage information
        """
        results = {}
        
        try:
            # Get all disk partitions
            partitions = psutil.disk_partitions()
            
            for partition in partitions:
                try:
                    # Skip special filesystems on Linux
                    if self.os_info['os_type'] == 'linux':
                        skip_types = ['tmpfs', 'devtmpfs', 'sysfs', 'proc', 'squashfs']
                        if partition.fstype in skip_types:
                            continue
                    
                    usage = psutil.disk_usage(partition.mountpoint)
                    used_percent = (usage.used / usage.total) * 100
                    
                    # Determine status
                    if used_percent >= critical_threshold:
                        status = 'critical'
                    elif used_percent >= warning_threshold:
                        status = 'warning'
                    else:
                        status = 'ok'
                    
                    results[partition.mountpoint] = {
                        'device': partition.device,
                        'fstype': partition.fstype,
                        'total_bytes': usage.total,
                        'used_bytes': usage.used,
                        'free_bytes': usage.free,
                        'used_percent': round(used_percent, 2),
                        'status': status,
                        'total_human': self._format_bytes(usage.total),
                        'used_human': self._format_bytes(usage.used),
                        'free_human': self._format_bytes(usage.free)
                    }
                    
                except PermissionError:
                    results[partition.mountpoint] = {
                        'error': 'Permission denied',
                        'status': 'unknown'
                    }
                except Exception as e:
                    results[partition.mountpoint] = {
                        'error': str(e),
                        'status': 'error'
                    }
            
        except Exception as e:
            self.logger.error(f"Failed to check disk space: {e}")
            results['error'] = str(e)
        
        return results
    
    def check_memory_usage(self, warning_threshold: int = 80) -> Dict[str, any]:
        """
        Check system memory usage.
        
        Args:
            warning_threshold: Warning threshold percentage
            
        Returns:
            Dictionary with memory usage information
        """
        try:
            memory = psutil.virtual_memory()
            swap = psutil.swap_memory()
            
            # Determine status
            if memory.percent >= warning_threshold:
                status = 'warning'
            else:
                status = 'ok'
            
            return {
                'total_bytes': memory.total,
                'available_bytes': memory.available,
                'used_bytes': memory.used,
                'free_bytes': memory.free,
                'used_percent': round(memory.percent, 2),
                'status': status,
                'total_human': self._format_bytes(memory.total),
                'available_human': self._format_bytes(memory.available),
                'used_human': self._format_bytes(memory.used),
                'swap': {
                    'total_bytes': swap.total,
                    'used_bytes': swap.used,
                    'free_bytes': swap.free,
                    'used_percent': round(swap.percent, 2),
                    'total_human': self._format_bytes(swap.total),
                    'used_human': self._format_bytes(swap.used)
                }
            }
            
        except Exception as e:
            self.logger.error(f"Failed to check memory usage: {e}")
            return {'error': str(e), 'status': 'error'}
    
    def check_uptime(self) -> Dict[str, any]:
        """
        Check system uptime.
        
        Returns:
            Dictionary with uptime information
        """
        try:
            boot_time = datetime.fromtimestamp(psutil.boot_time())
            uptime = datetime.now() - boot_time
            uptime_seconds = int(uptime.total_seconds())
            
            # Calculate days, hours, minutes
            days = uptime_seconds // 86400
            hours = (uptime_seconds % 86400) // 3600
            minutes = (uptime_seconds % 3600) // 60
            
            return {
                'boot_time': boot_time.isoformat(),
                'uptime_seconds': uptime_seconds,
                'uptime_human': f"{days}d {hours}h {minutes}m",
                'status': 'ok'
            }
            
        except Exception as e:
            self.logger.error(f"Failed to check uptime: {e}")
            return {'error': str(e), 'status': 'error'}
    
    def check_load_average(self) -> Dict[str, any]:
        """
        Check system load average (Linux/macOS only).
        
        Returns:
            Dictionary with load average information
        """
        try:
            if self.os_info['os_type'] == 'windows':
                # Windows doesn't have load average, use CPU percent instead
                cpu_percent = psutil.cpu_percent(interval=1)
                return {
                    'cpu_percent': cpu_percent,
                    'status': 'warning' if cpu_percent > 80 else 'ok',
                    'note': 'Windows - showing CPU percentage'
                }
            
            # Linux/macOS load average
            load1, load5, load15 = os.getloadavg()
            cpu_count = psutil.cpu_count()
            
            # Normalize load by CPU count
            load_normalized = load1 / cpu_count
            
            # Determine status
            if load_normalized > 1.5:
                status = 'critical'
            elif load_normalized > 1.0:
                status = 'warning'
            else:
                status = 'ok'
            
            return {
                'load_1min': load1,
                'load_5min': load5,
                'load_15min': load15,
                'load_normalized': round(load_normalized, 2),
                'cpu_count': cpu_count,
                'status': status
            }
            
        except Exception as e:
            self.logger.error(f"Failed to check load average: {e}")
            return {'error': str(e), 'status': 'error'}
    
    def check_services(self, service_list: List[str]) -> Dict[str, Dict]:
        """
        Check status of system services.
        
        Args:
            service_list: List of service names to check
            
        Returns:
            Dictionary with service status information
        """
        results = {}
        
        if not service_list:
            return {'note': 'No services specified for checking'}
        
        for service in service_list:
            try:
                if self.os_info['distro'] in ['debian', 'ubuntu', 'fedora', 'centos', 'rhel']:
                    # Use systemctl for systemd-based systems
                    code, stdout, stderr = CommandRunner.run_command(
                        ['systemctl', 'is-active', service],
                        check_return_code=False
                    )
                    
                    status = 'running' if stdout.strip() == 'active' else 'stopped'
                    
                elif self.os_info['distro'] == 'arch':
                    # Arch also uses systemctl
                    code, stdout, stderr = CommandRunner.run_command(
                        ['systemctl', 'is-active', service],
                        check_return_code=False
                    )
                    
                    status = 'running' if stdout.strip() == 'active' else 'stopped'
                    
                elif self.os_info['distro'] == 'macos':
                    # Use launchctl for macOS
                    code, stdout, stderr = CommandRunner.run_command(
                        ['launchctl', 'print', f"system/{service}"],
                        check_return_code=False
                    )
                    
                    status = 'running' if code == 0 else 'stopped'
                    
                else:
                    status = 'unknown'
                
                results[service] = {
                    'status': status,
                    'health_status': 'ok' if status == 'running' else 'warning'
                }
                
            except Exception as e:
                results[service] = {
                    'error': str(e),
                    'health_status': 'error'
                }
        
        return results
    
    def check_ports(self, port_list: List[int]) -> Dict[str, Dict]:
        """
        Check if specified ports are listening.
        
        Args:
            port_list: List of port numbers to check
            
        Returns:
            Dictionary with port status information
        """
        results = {}
        
        if not port_list:
            return {'note': 'No ports specified for checking'}
        
        # Get all listening connections
        try:
            connections = psutil.net_connections(kind='inet')
            listening_ports = {conn.laddr.port for conn in connections 
                             if conn.status == psutil.CONN_LISTEN}
        except Exception as e:
            self.logger.error(f"Failed to get network connections: {e}")
            listening_ports = set()
        
        for port in port_list:
            try:
                is_listening = port in listening_ports
                
                results[str(port)] = {
                    'is_listening': is_listening,
                    'status': 'ok' if is_listening else 'warning'
                }
                
            except Exception as e:
                results[str(port)] = {
                    'error': str(e),
                    'status': 'error'
                }
        
        return results
    
    def check_network_connectivity(self, hosts: List[str], timeout: int = 5) -> Dict[str, Dict]:
        """
        Check network connectivity to remote hosts.
        
        Args:
            hosts: List of hostnames or IP addresses to check
            timeout: Connection timeout in seconds
            
        Returns:
            Dictionary with connectivity results
        """
        results = {}
        
        if not hosts:
            return {'note': 'No hosts specified for checking'}
        
        for host in hosts:
            try:
                # Parse host and port
                if ':' in host:
                    hostname, port_str = host.split(':', 1)
                    port = int(port_str)
                else:
                    hostname = host
                    port = 22  # Default to SSH port
                
                # Test connection
                start_time = time.time()
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(timeout)
                
                try:
                    result = sock.connect_ex((hostname, port))
                    response_time = (time.time() - start_time) * 1000  # Convert to ms
                    
                    if result == 0:
                        status = 'ok'
                        reachable = True
                    else:
                        status = 'warning'
                        reachable = False
                        
                finally:
                    sock.close()
                
                results[host] = {
                    'reachable': reachable,
                    'response_time_ms': round(response_time, 2),
                    'status': status
                }
                
            except socket.gaierror:
                results[host] = {
                    'error': 'DNS resolution failed',
                    'status': 'error'
                }
            except Exception as e:
                results[host] = {
                    'error': str(e),
                    'status': 'error'
                }
        
        return results
    
    def _calculate_overall_status(self, results: Dict) -> str:
        """
        Calculate overall health status based on individual check results.
        
        Args:
            results: Results dictionary from all checks
            
        Returns:
            Overall status string
        """
        status_priorities = {'critical': 3, 'error': 2, 'warning': 1, 'ok': 0}
        max_priority = 0
        
        def check_status(item):
            nonlocal max_priority
            if isinstance(item, dict):
                if 'status' in item:
                    priority = status_priorities.get(item['status'], 0)
                    max_priority = max(max_priority, priority)
                else:
                    # Recursively check nested dictionaries
                    for value in item.values():
                        if isinstance(value, (dict, list)):
                            check_status(value)
            elif isinstance(item, list):
                for element in item:
                    check_status(element)
        
        # Check all results except timestamp and system_info
        for key, value in results.items():
            if key not in ['timestamp', 'system_info', 'overall_status']:
                check_status(value)
        
        # Return status based on highest priority found
        for status, priority in status_priorities.items():
            if priority == max_priority:
                return status
        
        return 'ok'
    
    def _format_bytes(self, bytes_value: int) -> str:
        """
        Format bytes into human-readable format.
        
        Args:
            bytes_value: Number of bytes
            
        Returns:
            Formatted string
        """
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if bytes_value < 1024.0:
                return f"{bytes_value:.1f} {unit}"
            bytes_value /= 1024.0
        return f"{bytes_value:.1f} PB"


def main():
    """Example usage of the health checker."""
    # Setup logging
    logger = LogManager.setup_logging('INFO')
    
    # Create health checker
    checker = HealthChecker(logger)
    
    # Example configuration
    config = {
        'disk_warning_threshold': 80,
        'disk_critical_threshold': 90,
        'memory_warning_threshold': 80,
        'check_services': ['ssh', 'nginx', 'mysql'],
        'check_ports': [22, 80, 443],
        'remote_hosts': ['google.com:80', '8.8.8.8:53']
    }
    
    # Run all checks
    results = checker.run_all_checks(config)
    
    # Print summary
    print(f"\n=== System Health Check Results ===")
    print(f"Overall Status: {results['overall_status'].upper()}")
    print(f"Timestamp: {results['timestamp']}")
    print(f"Hostname: {results['system_info']['hostname']}")
    print(f"OS: {results['system_info']['distro']} {results['system_info']['version']}")
    print(f"Uptime: {results['system_info']['uptime_human']}")
    
    # Log results
    logger.info(f"Health check completed with overall status: {results['overall_status']}")


if __name__ == '__main__':
    main()