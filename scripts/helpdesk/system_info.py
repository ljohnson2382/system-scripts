#!/usr/bin/env python3
"""
System information gathering toolkit.
Comprehensive system info collection for help desk support.

Author: Loyd Johnson
Date: November 2025
"""

import os
import sys
import platform
import subprocess
import json
from datetime import datetime
from typing import Dict, List, Optional
import logging

# Add parent directories to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))
from utils.system_utils import OSDetector, CommandRunner, LogManager

try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False


class SystemInfoGatherer:
    """Comprehensive system information gathering for troubleshooting."""
    
    def __init__(self, logger: Optional[logging.Logger] = None):
        """Initialize system info gatherer."""
        self.logger = logger or LogManager.setup_logging()
        self.os_info = OSDetector.get_os_info()
    
    def gather_all_info(self) -> Dict[str, any]:
        """Gather comprehensive system information."""
        self.logger.info("Gathering comprehensive system information")
        
        info = {
            'timestamp': datetime.now().isoformat(),
            'basic_info': self.get_basic_system_info(),
            'hardware_info': self.get_hardware_info(),
            'software_info': self.get_software_info(),
            'network_info': self.get_network_summary(),
            'storage_info': self.get_storage_info(),
            'process_info': self.get_process_info(),
            'service_info': self.get_service_info(),
            'log_info': self.get_recent_logs(),
            'performance_info': self.get_performance_info()
        }
        
        return info
    
    def get_basic_system_info(self) -> Dict[str, any]:
        """Get basic system information."""
        info = {
            'hostname': platform.node(),
            'os_type': self.os_info['os_type'],
            'distro': self.os_info['distro'],
            'os_version': self.os_info['version'],
            'architecture': self.os_info['architecture'],
            'python_version': platform.python_version(),
            'platform_details': platform.platform()
        }
        
        # Add boot time and uptime if psutil is available
        if PSUTIL_AVAILABLE:
            try:
                boot_time = datetime.fromtimestamp(psutil.boot_time())
                uptime = datetime.now() - boot_time
                
                info.update({
                    'boot_time': boot_time.isoformat(),
                    'uptime_seconds': int(uptime.total_seconds()),
                    'uptime_human': str(uptime).split('.')[0]
                })
            except Exception as e:
                info['uptime_error'] = str(e)
        
        # Get user information
        try:
            if self.os_info['os_type'] == 'windows':
                info['current_user'] = os.getenv('USERNAME')
                info['user_domain'] = os.getenv('USERDOMAIN')
            else:
                info['current_user'] = os.getenv('USER')
                info['home_directory'] = os.getenv('HOME')
        except Exception as e:
            info['user_info_error'] = str(e)
        
        return info
    
    def get_hardware_info(self) -> Dict[str, any]:
        """Get hardware information."""
        info = {}
        
        if PSUTIL_AVAILABLE:
            try:
                # CPU Information
                info['cpu'] = {
                    'physical_cores': psutil.cpu_count(logical=False),
                    'logical_cores': psutil.cpu_count(logical=True),
                    'current_frequency_mhz': psutil.cpu_freq().current if psutil.cpu_freq() else 'unknown',
                    'usage_percent': psutil.cpu_percent(interval=1)
                }
                
                # Memory Information
                memory = psutil.virtual_memory()
                info['memory'] = {
                    'total_gb': round(memory.total / (1024**3), 2),
                    'available_gb': round(memory.available / (1024**3), 2),
                    'used_percent': memory.percent,
                    'swap_total_gb': round(psutil.swap_memory().total / (1024**3), 2) if psutil.swap_memory().total else 0
                }
                
                # Disk Information
                disks = []
                for partition in psutil.disk_partitions():
                    try:
                        usage = psutil.disk_usage(partition.mountpoint)
                        disks.append({
                            'device': partition.device,
                            'mountpoint': partition.mountpoint,
                            'fstype': partition.fstype,
                            'total_gb': round(usage.total / (1024**3), 2),
                            'used_percent': round((usage.used / usage.total) * 100, 1),
                            'free_gb': round(usage.free / (1024**3), 2)
                        })
                    except PermissionError:
                        disks.append({
                            'device': partition.device,
                            'mountpoint': partition.mountpoint,
                            'error': 'Permission denied'
                        })
                
                info['storage'] = {
                    'disks': disks,
                    'disk_count': len(disks)
                }
                
            except Exception as e:
                info['psutil_error'] = str(e)
        
        # Get additional hardware info using system commands
        try:
            if self.os_info['os_type'] == 'windows':
                info.update(self._get_windows_hardware_info())
            elif self.os_info['os_type'] == 'darwin':
                info.update(self._get_macos_hardware_info())
            else:
                info.update(self._get_linux_hardware_info())
        except Exception as e:
            info['system_hardware_error'] = str(e)
        
        return info
    
    def _get_windows_hardware_info(self) -> Dict[str, any]:
        """Get Windows-specific hardware information."""
        info = {}
        
        try:
            # Get system info using wmic
            commands = {
                'cpu_name': ['wmic', 'cpu', 'get', 'name'],
                'motherboard': ['wmic', 'baseboard', 'get', 'manufacturer,product'],
                'memory_modules': ['wmic', 'memorychip', 'get', 'capacity,speed'],
                'graphics_card': ['wmic', 'path', 'win32_VideoController', 'get', 'name']
            }
            
            for key, cmd in commands.items():
                try:
                    code, stdout, stderr = CommandRunner.run_command(cmd, timeout=10)
                    info[key] = stdout.strip()
                except Exception as e:
                    info[f'{key}_error'] = str(e)
        
        except Exception as e:
            info['wmic_error'] = str(e)
        
        return info
    
    def _get_macos_hardware_info(self) -> Dict[str, any]:
        """Get macOS-specific hardware information."""
        info = {}
        
        try:
            # Get system profiler info
            code, stdout, stderr = CommandRunner.run_command([
                'system_profiler', 'SPHardwareDataType', '-json'
            ], timeout=15)
            
            hardware_data = json.loads(stdout)
            if hardware_data and 'SPHardwareDataType' in hardware_data:
                hw_info = hardware_data['SPHardwareDataType'][0]
                info['hardware_overview'] = hw_info
        
        except Exception as e:
            info['system_profiler_error'] = str(e)
        
        return info
    
    def _get_linux_hardware_info(self) -> Dict[str, any]:
        """Get Linux-specific hardware information."""
        info = {}
        
        # CPU info from /proc/cpuinfo
        try:
            with open('/proc/cpuinfo', 'r') as f:
                cpuinfo = f.read()
            info['proc_cpuinfo'] = cpuinfo[:1000]  # Limit size
        except Exception as e:
            info['cpuinfo_error'] = str(e)
        
        # Memory info from /proc/meminfo
        try:
            with open('/proc/meminfo', 'r') as f:
                meminfo = f.read()
            info['proc_meminfo'] = meminfo[:1000]  # Limit size
        except Exception as e:
            info['meminfo_error'] = str(e)
        
        # Hardware info using lshw if available
        if CommandRunner.is_command_available('lshw'):
            try:
                code, stdout, stderr = CommandRunner.run_command([
                    'sudo', 'lshw', '-short'
                ], timeout=10)
                info['lshw_summary'] = stdout
            except Exception as e:
                info['lshw_error'] = str(e)
        
        return info
    
    def get_software_info(self) -> Dict[str, any]:
        """Get installed software information."""
        info = {}
        
        try:
            if self.os_info['os_type'] == 'windows':
                info.update(self._get_windows_software_info())
            elif self.os_info['os_type'] == 'darwin':
                info.update(self._get_macos_software_info())
            else:
                info.update(self._get_linux_software_info())
        except Exception as e:
            info['software_enum_error'] = str(e)
        
        return info
    
    def _get_windows_software_info(self) -> Dict[str, any]:
        """Get Windows software information."""
        info = {}
        
        # Get installed programs
        try:
            code, stdout, stderr = CommandRunner.run_command([
                'powershell', '-Command',
                'Get-ItemProperty HKLM:\\Software\\Wow6432Node\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\* | Select-Object DisplayName, DisplayVersion | Where-Object {$_.DisplayName} | Sort-Object DisplayName'
            ], timeout=30)
            
            info['installed_programs'] = stdout
        except Exception as e:
            info['programs_error'] = str(e)
        
        # Get Windows features
        try:
            code, stdout, stderr = CommandRunner.run_command([
                'dism', '/online', '/get-features', '/format:table'
            ], timeout=30)
            
            info['windows_features'] = stdout
        except Exception as e:
            info['features_error'] = str(e)
        
        return info
    
    def _get_macos_software_info(self) -> Dict[str, any]:
        """Get macOS software information."""
        info = {}
        
        # Get installed applications
        try:
            code, stdout, stderr = CommandRunner.run_command([
                'system_profiler', 'SPApplicationsDataType', '-json'
            ], timeout=30)
            
            apps_data = json.loads(stdout)
            if apps_data and 'SPApplicationsDataType' in apps_data:
                # Limit to first 50 apps to avoid huge output
                info['installed_applications'] = apps_data['SPApplicationsDataType'][:50]
        except Exception as e:
            info['applications_error'] = str(e)
        
        # Get Homebrew packages if available
        if CommandRunner.is_command_available('brew'):
            try:
                code, stdout, stderr = CommandRunner.run_command([
                    'brew', 'list'
                ], timeout=15)
                
                packages = stdout.strip().split('\n') if stdout.strip() else []
                info['homebrew_packages'] = {
                    'count': len(packages),
                    'packages': packages[:30]  # Limit output
                }
            except Exception as e:
                info['homebrew_error'] = str(e)
        
        return info
    
    def _get_linux_software_info(self) -> Dict[str, any]:
        """Get Linux software information."""
        info = {}
        
        # Get package information based on distribution
        distro = self.os_info['distro'].lower()
        
        try:
            if distro in ['debian', 'ubuntu']:
                code, stdout, stderr = CommandRunner.run_command([
                    'dpkg', '--get-selections'
                ], timeout=15)
                
                packages = [line.split()[0] for line in stdout.strip().split('\n') 
                          if 'install' in line]
                info['installed_packages'] = {
                    'count': len(packages),
                    'packages': packages[:50]  # Limit output
                }
            
            elif distro in ['arch', 'manjaro']:
                code, stdout, stderr = CommandRunner.run_command([
                    'pacman', '-Q'
                ], timeout=15)
                
                packages = [line.split()[0] for line in stdout.strip().split('\n')]
                info['installed_packages'] = {
                    'count': len(packages),
                    'packages': packages[:50]
                }
            
            elif distro in ['fedora', 'rhel', 'centos']:
                package_manager = 'dnf' if CommandRunner.is_command_available('dnf') else 'yum'
                code, stdout, stderr = CommandRunner.run_command([
                    package_manager, 'list', 'installed'
                ], timeout=15)
                
                # Parse package list
                lines = stdout.strip().split('\n')[1:]  # Skip header
                packages = [line.split()[0] for line in lines if line.strip()]
                info['installed_packages'] = {
                    'count': len(packages),
                    'packages': packages[:50]
                }
        
        except Exception as e:
            info['package_enum_error'] = str(e)
        
        return info
    
    def get_network_summary(self) -> Dict[str, any]:
        """Get basic network configuration summary."""
        info = {}
        
        if PSUTIL_AVAILABLE:
            try:
                # Get network interfaces
                interfaces = psutil.net_if_addrs()
                net_info = {}
                
                for interface, addresses in interfaces.items():
                    addr_info = []
                    for addr in addresses:
                        addr_info.append({
                            'family': str(addr.family),
                            'address': addr.address,
                            'netmask': addr.netmask
                        })
                    net_info[interface] = addr_info
                
                info['interfaces'] = net_info
                
                # Get network statistics
                net_stats = psutil.net_io_counters()
                info['statistics'] = {
                    'bytes_sent': net_stats.bytes_sent,
                    'bytes_recv': net_stats.bytes_recv,
                    'packets_sent': net_stats.packets_sent,
                    'packets_recv': net_stats.packets_recv
                }
                
            except Exception as e:
                info['psutil_net_error'] = str(e)
        
        return info
    
    def get_storage_info(self) -> Dict[str, any]:
        """Get detailed storage information."""
        if not PSUTIL_AVAILABLE:
            return {'error': 'psutil not available'}
        
        storage_info = {
            'disks': [],
            'total_capacity_gb': 0,
            'total_used_gb': 0
        }
        
        try:
            for partition in psutil.disk_partitions():
                try:
                    usage = psutil.disk_usage(partition.mountpoint)
                    
                    disk_info = {
                        'device': partition.device,
                        'mountpoint': partition.mountpoint,
                        'fstype': partition.fstype,
                        'total_gb': round(usage.total / (1024**3), 2),
                        'used_gb': round(usage.used / (1024**3), 2),
                        'free_gb': round(usage.free / (1024**3), 2),
                        'used_percent': round((usage.used / usage.total) * 100, 1)
                    }
                    
                    storage_info['disks'].append(disk_info)
                    storage_info['total_capacity_gb'] += disk_info['total_gb']
                    storage_info['total_used_gb'] += disk_info['used_gb']
                    
                except PermissionError:
                    storage_info['disks'].append({
                        'device': partition.device,
                        'mountpoint': partition.mountpoint,
                        'error': 'Permission denied'
                    })
        
        except Exception as e:
            storage_info['error'] = str(e)
        
        return storage_info
    
    def get_process_info(self) -> Dict[str, any]:
        """Get running process information."""
        if not PSUTIL_AVAILABLE:
            return {'error': 'psutil not available'}
        
        process_info = {
            'total_processes': 0,
            'top_cpu_processes': [],
            'top_memory_processes': []
        }
        
        try:
            processes = []
            for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent']):
                try:
                    processes.append(proc.info)
                except psutil.NoSuchProcess:
                    continue
            
            process_info['total_processes'] = len(processes)
            
            # Top CPU consumers
            cpu_sorted = sorted(processes, key=lambda x: x['cpu_percent'] or 0, reverse=True)
            process_info['top_cpu_processes'] = cpu_sorted[:10]
            
            # Top memory consumers  
            mem_sorted = sorted(processes, key=lambda x: x['memory_percent'] or 0, reverse=True)
            process_info['top_memory_processes'] = mem_sorted[:10]
            
        except Exception as e:
            process_info['error'] = str(e)
        
        return process_info
    
    def get_service_info(self) -> Dict[str, any]:
        """Get system service information."""
        info = {'services': []}
        
        try:
            if self.os_info['os_type'] == 'windows':
                code, stdout, stderr = CommandRunner.run_command([
                    'powershell', '-Command',
                    'Get-Service | Select-Object Name,Status | ConvertTo-Json'
                ], timeout=15)
                
                services = json.loads(stdout)
                if not isinstance(services, list):
                    services = [services]
                
                info['services'] = services[:30]  # Limit output
            
            elif CommandRunner.is_command_available('systemctl'):
                code, stdout, stderr = CommandRunner.run_command([
                    'systemctl', 'list-units', '--type=service', '--no-pager'
                ], timeout=15)
                
                info['systemctl_services'] = stdout
            
        except Exception as e:
            info['service_enum_error'] = str(e)
        
        return info
    
    def get_recent_logs(self) -> Dict[str, any]:
        """Get recent system log entries."""
        logs = {}
        
        try:
            if self.os_info['os_type'] == 'windows':
                # Get Windows event logs
                code, stdout, stderr = CommandRunner.run_command([
                    'powershell', '-Command',
                    'Get-EventLog -LogName System -Newest 10 | Select-Object TimeGenerated,EntryType,Source,Message | ConvertTo-Json'
                ], timeout=15)
                
                logs['windows_system_events'] = json.loads(stdout)
            
            elif CommandRunner.is_command_available('journalctl'):
                # Get systemd journal logs
                code, stdout, stderr = CommandRunner.run_command([
                    'journalctl', '-n', '20', '--no-pager'
                ], timeout=10)
                
                logs['journalctl_recent'] = stdout
            
            else:
                # Try traditional log files
                log_files = ['/var/log/messages', '/var/log/syslog']
                for log_file in log_files:
                    if os.path.exists(log_file):
                        try:
                            with open(log_file, 'r') as f:
                                lines = f.readlines()
                                logs[f'recent_{os.path.basename(log_file)}'] = ''.join(lines[-20:])
                                break
                        except PermissionError:
                            logs['log_access_error'] = 'Permission denied to read log files'
        
        except Exception as e:
            logs['log_error'] = str(e)
        
        return logs
    
    def get_performance_info(self) -> Dict[str, any]:
        """Get current performance metrics."""
        if not PSUTIL_AVAILABLE:
            return {'error': 'psutil not available'}
        
        perf_info = {}
        
        try:
            # CPU usage over 5 seconds
            cpu_percent = psutil.cpu_percent(interval=5)
            perf_info['cpu_usage_percent'] = cpu_percent
            
            # Memory usage
            memory = psutil.virtual_memory()
            perf_info['memory_usage_percent'] = memory.percent
            
            # Load average (Unix-like systems only)
            if hasattr(os, 'getloadavg'):
                load_avg = os.getloadavg()
                perf_info['load_average'] = {
                    '1_min': load_avg[0],
                    '5_min': load_avg[1],
                    '15_min': load_avg[2]
                }
            
            # Disk I/O
            disk_io = psutil.disk_io_counters()
            if disk_io:
                perf_info['disk_io'] = {
                    'read_bytes': disk_io.read_bytes,
                    'write_bytes': disk_io.write_bytes,
                    'read_time_ms': disk_io.read_time,
                    'write_time_ms': disk_io.write_time
                }
            
        except Exception as e:
            perf_info['performance_error'] = str(e)
        
        return perf_info


def main():
    """Main function for standalone execution."""
    import argparse
    
    parser = argparse.ArgumentParser(description='System information gatherer')
    parser.add_argument('--output', help='Output file path (JSON format)')
    parser.add_argument('--verbose', action='store_true',
                       help='Enable verbose logging')
    
    args = parser.parse_args()
    
    # Setup logging
    log_level = 'DEBUG' if args.verbose else 'INFO'
    logger = LogManager.setup_logging(log_level)
    
    # Gather information
    gatherer = SystemInfoGatherer(logger)
    system_info = gatherer.gather_all_info()
    
    # Output results
    if args.output:
        with open(args.output, 'w') as f:
            json.dump(system_info, f, indent=2, default=str)
        print(f"System information saved to {args.output}")
    else:
        # Print summary to console
        print(f"\n=== System Information Summary ===")
        print(f"Hostname: {system_info['basic_info']['hostname']}")
        print(f"OS: {system_info['basic_info']['distro']} {system_info['basic_info']['os_version']}")
        print(f"Architecture: {system_info['basic_info']['architecture']}")
        
        if 'uptime_human' in system_info['basic_info']:
            print(f"Uptime: {system_info['basic_info']['uptime_human']}")
        
        # Hardware summary
        hw_info = system_info.get('hardware_info', {})
        if 'cpu' in hw_info:
            cpu = hw_info['cpu']
            print(f"CPU: {cpu['logical_cores']} cores, {cpu['usage_percent']:.1f}% usage")
        
        if 'memory' in hw_info:
            mem = hw_info['memory']
            print(f"Memory: {mem['total_gb']:.1f}GB total, {mem['used_percent']:.1f}% used")
        
        # Storage summary
        storage = system_info.get('storage_info', {})
        if 'total_capacity_gb' in storage:
            print(f"Storage: {storage['total_capacity_gb']:.1f}GB total capacity")
        
        print(f"Timestamp: {system_info['timestamp']}")


if __name__ == '__main__':
    main()