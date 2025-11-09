#!/usr/bin/env python3
"""
System performance analysis and optimization toolkit.
Advanced performance monitoring and system optimization for help desk support.

Author: Loyd Johnson
Date: November 2025
"""

import os
import sys
import time
import json
import subprocess
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional
import logging

# Add parent directories to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))
from utils.system_utils import OSDetector, CommandRunner, LogManager

try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False


class PerformanceAnalyzer:
    """Advanced system performance analysis and optimization."""
    
    def __init__(self, logger: Optional[logging.Logger] = None):
        """Initialize performance analyzer."""
        self.logger = logger or LogManager.setup_logging()
        self.os_info = OSDetector.get_os_info()
        self.baseline_metrics = None
    
    def run_full_analysis(self, duration_minutes: int = 5) -> Dict[str, any]:
        """Run comprehensive performance analysis."""
        self.logger.info(f"Starting {duration_minutes}-minute performance analysis")
        
        analysis = {
            'timestamp': datetime.now().isoformat(),
            'analysis_duration_minutes': duration_minutes,
            'system_info': self._get_system_summary(),
            'baseline_performance': self.capture_performance_snapshot(),
            'performance_over_time': self._monitor_performance_over_time(duration_minutes),
            'bottleneck_analysis': self.analyze_bottlenecks(),
            'optimization_recommendations': self.generate_recommendations(),
            'resource_hogs': self.identify_resource_hogs(),
            'startup_analysis': self.analyze_startup_performance(),
            'disk_analysis': self.analyze_disk_performance(),
            'network_analysis': self.analyze_network_performance()
        }
        
        return analysis
    
    def _get_system_summary(self) -> Dict[str, any]:
        """Get basic system information."""
        return {
            'hostname': OSDetector.get_hostname(),
            'os_type': self.os_info['os_type'],
            'distro': self.os_info['distro'],
            'version': self.os_info['version'],
            'architecture': self.os_info['architecture']
        }
    
    def capture_performance_snapshot(self) -> Dict[str, any]:
        """Capture current performance metrics snapshot."""
        snapshot = {
            'timestamp': datetime.now().isoformat(),
            'cpu_usage': self._get_cpu_metrics(),
            'memory_usage': self._get_memory_metrics(),
            'disk_usage': self._get_disk_metrics(),
            'network_usage': self._get_network_metrics(),
            'process_count': self._get_process_count(),
            'load_average': self._get_load_average()
        }
        
        return snapshot
    
    def _get_cpu_metrics(self) -> Dict[str, any]:
        """Get CPU performance metrics."""
        if not PSUTIL_AVAILABLE:
            return {'error': 'psutil not available'}
        
        try:
            # CPU usage per core and overall
            cpu_percent = psutil.cpu_percent(interval=1, percpu=True)
            cpu_overall = psutil.cpu_percent(interval=1)
            
            # CPU frequency information
            cpu_freq = psutil.cpu_freq()
            
            # CPU times
            cpu_times = psutil.cpu_times()
            
            return {
                'overall_usage_percent': cpu_overall,
                'per_core_usage': cpu_percent,
                'core_count': {
                    'physical': psutil.cpu_count(logical=False),
                    'logical': psutil.cpu_count(logical=True)
                },
                'frequency_mhz': {
                    'current': cpu_freq.current if cpu_freq else None,
                    'min': cpu_freq.min if cpu_freq else None,
                    'max': cpu_freq.max if cpu_freq else None
                },
                'cpu_times': {
                    'user': cpu_times.user,
                    'system': cpu_times.system,
                    'idle': cpu_times.idle
                }
            }
        except Exception as e:
            return {'error': str(e)}
    
    def _get_memory_metrics(self) -> Dict[str, any]:
        """Get memory performance metrics."""
        if not PSUTIL_AVAILABLE:
            return {'error': 'psutil not available'}
        
        try:
            virtual_mem = psutil.virtual_memory()
            swap_mem = psutil.swap_memory()
            
            return {
                'virtual_memory': {
                    'total_gb': round(virtual_mem.total / (1024**3), 2),
                    'available_gb': round(virtual_mem.available / (1024**3), 2),
                    'used_gb': round(virtual_mem.used / (1024**3), 2),
                    'used_percent': virtual_mem.percent,
                    'cached_gb': round(virtual_mem.cached / (1024**3), 2) if hasattr(virtual_mem, 'cached') else None
                },
                'swap_memory': {
                    'total_gb': round(swap_mem.total / (1024**3), 2),
                    'used_gb': round(swap_mem.used / (1024**3), 2),
                    'free_gb': round(swap_mem.free / (1024**3), 2),
                    'used_percent': swap_mem.percent
                }
            }
        except Exception as e:
            return {'error': str(e)}
    
    def _get_disk_metrics(self) -> Dict[str, any]:
        """Get disk performance metrics."""
        if not PSUTIL_AVAILABLE:
            return {'error': 'psutil not available'}
        
        try:
            # Disk I/O statistics
            disk_io = psutil.disk_io_counters()
            
            # Disk usage by partition
            partitions = []
            for partition in psutil.disk_partitions():
                try:
                    usage = psutil.disk_usage(partition.mountpoint)
                    partitions.append({
                        'device': partition.device,
                        'mountpoint': partition.mountpoint,
                        'fstype': partition.fstype,
                        'total_gb': round(usage.total / (1024**3), 2),
                        'used_percent': round((usage.used / usage.total) * 100, 1),
                        'free_gb': round(usage.free / (1024**3), 2)
                    })
                except PermissionError:
                    partitions.append({
                        'device': partition.device,
                        'error': 'Permission denied'
                    })
            
            return {
                'io_counters': {
                    'read_count': disk_io.read_count if disk_io else 0,
                    'write_count': disk_io.write_count if disk_io else 0,
                    'read_bytes': disk_io.read_bytes if disk_io else 0,
                    'write_bytes': disk_io.write_bytes if disk_io else 0,
                    'read_time_ms': disk_io.read_time if disk_io else 0,
                    'write_time_ms': disk_io.write_time if disk_io else 0
                },
                'partitions': partitions
            }
        except Exception as e:
            return {'error': str(e)}
    
    def _get_network_metrics(self) -> Dict[str, any]:
        """Get network performance metrics."""
        if not PSUTIL_AVAILABLE:
            return {'error': 'psutil not available'}
        
        try:
            net_io = psutil.net_io_counters()
            
            return {
                'bytes_sent': net_io.bytes_sent,
                'bytes_recv': net_io.bytes_recv,
                'packets_sent': net_io.packets_sent,
                'packets_recv': net_io.packets_recv,
                'errors_in': net_io.errin,
                'errors_out': net_io.errout,
                'drops_in': net_io.dropin,
                'drops_out': net_io.dropout
            }
        except Exception as e:
            return {'error': str(e)}
    
    def _get_process_count(self) -> int:
        """Get current process count."""
        if not PSUTIL_AVAILABLE:
            return 0
        
        try:
            return len(psutil.pids())
        except Exception:
            return 0
    
    def _get_load_average(self) -> Optional[Dict[str, float]]:
        """Get system load average (Unix-like systems only)."""
        try:
            if hasattr(os, 'getloadavg'):
                load_avg = os.getloadavg()
                return {
                    '1_minute': load_avg[0],
                    '5_minute': load_avg[1],
                    '15_minute': load_avg[2]
                }
        except Exception:
            pass
        
        return None
    
    def _monitor_performance_over_time(self, duration_minutes: int) -> List[Dict[str, any]]:
        """Monitor performance metrics over specified duration."""
        self.logger.info(f"Monitoring performance for {duration_minutes} minutes")
        
        samples = []
        sample_interval = 30  # seconds
        total_samples = (duration_minutes * 60) // sample_interval
        
        for i in range(total_samples):
            sample = self.capture_performance_snapshot()
            sample['sample_number'] = i + 1
            samples.append(sample)
            
            if i < total_samples - 1:  # Don't sleep after last sample
                time.sleep(sample_interval)
        
        return samples
    
    def analyze_bottlenecks(self) -> Dict[str, any]:
        """Analyze system bottlenecks."""
        bottlenecks = {
            'cpu_bottleneck': self._check_cpu_bottleneck(),
            'memory_bottleneck': self._check_memory_bottleneck(),
            'disk_bottleneck': self._check_disk_bottleneck(),
            'network_bottleneck': self._check_network_bottleneck(),
            'overall_assessment': 'normal'
        }
        
        # Determine overall assessment
        issues = [k for k, v in bottlenecks.items() 
                 if isinstance(v, dict) and v.get('severity') in ['high', 'critical']]
        
        if any('critical' in str(bottlenecks[issue]) for issue in issues):
            bottlenecks['overall_assessment'] = 'critical'
        elif any('high' in str(bottlenecks[issue]) for issue in issues):
            bottlenecks['overall_assessment'] = 'warning'
        elif any('medium' in str(bottlenecks[issue]) for issue in issues):
            bottlenecks['overall_assessment'] = 'minor_issues'
        
        return bottlenecks
    
    def _check_cpu_bottleneck(self) -> Dict[str, any]:
        """Check for CPU bottlenecks."""
        if not PSUTIL_AVAILABLE:
            return {'error': 'psutil not available'}
        
        try:
            # Sample CPU usage multiple times
            cpu_samples = []
            for _ in range(3):
                cpu_samples.append(psutil.cpu_percent(interval=2))
                time.sleep(1)
            
            avg_cpu = sum(cpu_samples) / len(cpu_samples)
            max_cpu = max(cpu_samples)
            
            severity = 'normal'
            if avg_cpu > 90:
                severity = 'critical'
            elif avg_cpu > 80:
                severity = 'high'
            elif avg_cpu > 70:
                severity = 'medium'
            
            return {
                'average_cpu_percent': round(avg_cpu, 1),
                'peak_cpu_percent': round(max_cpu, 1),
                'severity': severity,
                'description': f'CPU usage averaging {avg_cpu:.1f}%'
            }
        
        except Exception as e:
            return {'error': str(e)}
    
    def _check_memory_bottleneck(self) -> Dict[str, any]:
        """Check for memory bottlenecks."""
        if not PSUTIL_AVAILABLE:
            return {'error': 'psutil not available'}
        
        try:
            memory = psutil.virtual_memory()
            swap = psutil.swap_memory()
            
            severity = 'normal'
            issues = []
            
            if memory.percent > 95:
                severity = 'critical'
                issues.append('Virtual memory critically low')
            elif memory.percent > 85:
                severity = 'high'
                issues.append('Virtual memory usage high')
            elif memory.percent > 75:
                severity = 'medium'
                issues.append('Virtual memory usage elevated')
            
            if swap.percent > 50:
                if severity == 'normal':
                    severity = 'medium'
                issues.append(f'Swap usage high ({swap.percent:.1f}%)')
            
            return {
                'memory_usage_percent': memory.percent,
                'swap_usage_percent': swap.percent,
                'available_gb': round(memory.available / (1024**3), 2),
                'severity': severity,
                'issues': issues
            }
        
        except Exception as e:
            return {'error': str(e)}
    
    def _check_disk_bottleneck(self) -> Dict[str, any]:
        """Check for disk bottlenecks."""
        if not PSUTIL_AVAILABLE:
            return {'error': 'psutil not available'}
        
        try:
            disk_issues = []
            max_usage = 0
            severity = 'normal'
            
            for partition in psutil.disk_partitions():
                try:
                    usage = psutil.disk_usage(partition.mountpoint)
                    usage_percent = (usage.used / usage.total) * 100
                    
                    max_usage = max(max_usage, usage_percent)
                    
                    if usage_percent > 95:
                        severity = 'critical'
                        disk_issues.append(f'{partition.mountpoint}: {usage_percent:.1f}% full (critical)')
                    elif usage_percent > 90:
                        if severity not in ['critical']:
                            severity = 'high'
                        disk_issues.append(f'{partition.mountpoint}: {usage_percent:.1f}% full (high)')
                    elif usage_percent > 80:
                        if severity not in ['critical', 'high']:
                            severity = 'medium'
                        disk_issues.append(f'{partition.mountpoint}: {usage_percent:.1f}% full (medium)')
                
                except PermissionError:
                    continue
            
            return {
                'max_disk_usage_percent': round(max_usage, 1),
                'severity': severity,
                'disk_issues': disk_issues
            }
        
        except Exception as e:
            return {'error': str(e)}
    
    def _check_network_bottleneck(self) -> Dict[str, any]:
        """Check for network bottlenecks."""
        if not PSUTIL_AVAILABLE:
            return {'error': 'psutil not available'}
        
        try:
            # Sample network I/O over time
            net_before = psutil.net_io_counters()
            time.sleep(3)
            net_after = psutil.net_io_counters()
            
            bytes_sent_per_sec = (net_after.bytes_sent - net_before.bytes_sent) / 3
            bytes_recv_per_sec = (net_after.bytes_recv - net_before.bytes_recv) / 3
            
            # Convert to Mbps for readability
            mbps_sent = (bytes_sent_per_sec * 8) / (1024 * 1024)
            mbps_recv = (bytes_recv_per_sec * 8) / (1024 * 1024)
            
            severity = 'normal'
            max_throughput = max(mbps_sent, mbps_recv)
            
            # Note: These thresholds are rough estimates
            if max_throughput > 800:  # Near gigabit saturation
                severity = 'high'
            elif max_throughput > 80:   # Near 100Mbps saturation
                severity = 'medium'
            
            return {
                'mbps_sent': round(mbps_sent, 2),
                'mbps_received': round(mbps_recv, 2),
                'errors_in': net_after.errin,
                'errors_out': net_after.errout,
                'severity': severity
            }
        
        except Exception as e:
            return {'error': str(e)}
    
    def identify_resource_hogs(self) -> Dict[str, any]:
        """Identify processes consuming the most resources."""
        if not PSUTIL_AVAILABLE:
            return {'error': 'psutil not available'}
        
        try:
            processes = []
            
            for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent', 'memory_info']):
                try:
                    proc_info = proc.info
                    # Get CPU usage over 1 second
                    proc_info['cpu_percent'] = proc.cpu_percent(interval=1)
                    processes.append(proc_info)
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
            
            # Sort by different metrics
            cpu_hogs = sorted(processes, key=lambda x: x['cpu_percent'] or 0, reverse=True)[:10]
            memory_hogs = sorted(processes, key=lambda x: x['memory_percent'] or 0, reverse=True)[:10]
            
            return {
                'top_cpu_consumers': [
                    {
                        'pid': p['pid'],
                        'name': p['name'],
                        'cpu_percent': round(p['cpu_percent'] or 0, 1)
                    } for p in cpu_hogs
                ],
                'top_memory_consumers': [
                    {
                        'pid': p['pid'],
                        'name': p['name'],
                        'memory_percent': round(p['memory_percent'] or 0, 1),
                        'memory_mb': round((p['memory_info'].rss / (1024 * 1024)), 1) if p['memory_info'] else 0
                    } for p in memory_hogs
                ]
            }
        
        except Exception as e:
            return {'error': str(e)}
    
    def analyze_startup_performance(self) -> Dict[str, any]:
        """Analyze system startup performance."""
        startup_info = {
            'boot_time_analysis': self._get_boot_time_info(),
            'startup_programs': self._get_startup_programs()
        }
        
        return startup_info
    
    def _get_boot_time_info(self) -> Dict[str, any]:
        """Get boot time information."""
        if not PSUTIL_AVAILABLE:
            return {'error': 'psutil not available'}
        
        try:
            boot_time = datetime.fromtimestamp(psutil.boot_time())
            uptime = datetime.now() - boot_time
            
            return {
                'boot_time': boot_time.isoformat(),
                'uptime_seconds': int(uptime.total_seconds()),
                'uptime_human': str(uptime).split('.')[0]
            }
        except Exception as e:
            return {'error': str(e)}
    
    def _get_startup_programs(self) -> Dict[str, any]:
        """Get startup programs information."""
        startup_info = {}
        
        try:
            if self.os_info['os_type'] == 'windows':
                startup_info.update(self._get_windows_startup_programs())
            elif self.os_info['os_type'] == 'darwin':
                startup_info.update(self._get_macos_startup_programs())
            else:
                startup_info.update(self._get_linux_startup_programs())
        except Exception as e:
            startup_info['error'] = str(e)
        
        return startup_info
    
    def _get_windows_startup_programs(self) -> Dict[str, any]:
        """Get Windows startup programs."""
        try:
            code, stdout, stderr = CommandRunner.run_command([
                'powershell', '-Command',
                'Get-CimInstance Win32_StartupCommand | Select-Object Name,Command,Location | ConvertTo-Json'
            ], timeout=15)
            
            startup_programs = json.loads(stdout)
            if not isinstance(startup_programs, list):
                startup_programs = [startup_programs] if startup_programs else []
            
            return {'startup_programs': startup_programs}
        except Exception as e:
            return {'windows_startup_error': str(e)}
    
    def _get_macos_startup_programs(self) -> Dict[str, any]:
        """Get macOS startup programs."""
        startup_info = {}
        
        try:
            # Check Launch Agents and Launch Daemons
            launchd_dirs = [
                '/System/Library/LaunchAgents',
                '/System/Library/LaunchDaemons',
                '/Library/LaunchAgents', 
                '/Library/LaunchDaemons',
                os.path.expanduser('~/Library/LaunchAgents')
            ]
            
            startup_items = []
            for directory in launchd_dirs:
                if os.path.exists(directory):
                    try:
                        items = os.listdir(directory)
                        for item in items:
                            if item.endswith('.plist'):
                                startup_items.append({
                                    'name': item,
                                    'location': directory
                                })
                    except PermissionError:
                        continue
            
            startup_info['launchd_items'] = startup_items
            
        except Exception as e:
            startup_info['macos_startup_error'] = str(e)
        
        return startup_info
    
    def _get_linux_startup_programs(self) -> Dict[str, any]:
        """Get Linux startup programs."""
        startup_info = {}
        
        try:
            # Check systemd services
            if CommandRunner.is_command_available('systemctl'):
                code, stdout, stderr = CommandRunner.run_command([
                    'systemctl', 'list-unit-files', '--type=service', '--state=enabled', '--no-pager'
                ], timeout=10)
                
                enabled_services = []
                for line in stdout.split('\n'):
                    if '.service' in line and 'enabled' in line:
                        service_name = line.split()[0]
                        enabled_services.append(service_name)
                
                startup_info['enabled_services'] = enabled_services[:20]  # Limit output
        
        except Exception as e:
            startup_info['linux_startup_error'] = str(e)
        
        return startup_info
    
    def analyze_disk_performance(self) -> Dict[str, any]:
        """Analyze disk performance."""
        disk_analysis = {
            'disk_speed_test': self._run_disk_speed_test(),
            'disk_health': self._check_disk_health(),
            'fragmentation_info': self._check_disk_fragmentation()
        }
        
        return disk_analysis
    
    def _run_disk_speed_test(self) -> Dict[str, any]:
        """Run basic disk speed test."""
        try:
            import tempfile
            
            # Create temporary file for testing
            with tempfile.NamedTemporaryFile(delete=False) as temp_file:
                temp_path = temp_file.name
            
            # Write test (1MB)
            test_data = b'0' * (1024 * 1024)  # 1MB of data
            
            start_time = time.time()
            with open(temp_path, 'wb') as f:
                for _ in range(10):  # Write 10MB total
                    f.write(test_data)
                    f.flush()
                    os.fsync(f.fileno())
            write_time = time.time() - start_time
            
            # Read test
            start_time = time.time()
            with open(temp_path, 'rb') as f:
                while f.read(1024 * 1024):  # Read in 1MB chunks
                    pass
            read_time = time.time() - start_time
            
            # Clean up
            os.unlink(temp_path)
            
            write_speed_mbps = (10 / write_time) if write_time > 0 else 0
            read_speed_mbps = (10 / read_time) if read_time > 0 else 0
            
            return {
                'write_speed_mbps': round(write_speed_mbps, 2),
                'read_speed_mbps': round(read_speed_mbps, 2),
                'write_time_seconds': round(write_time, 2),
                'read_time_seconds': round(read_time, 2)
            }
        
        except Exception as e:
            return {'error': str(e)}
    
    def _check_disk_health(self) -> Dict[str, any]:
        """Check disk health using available tools."""
        health_info = {}
        
        try:
            if self.os_info['os_type'] == 'windows':
                # Use wmic to check disk health
                code, stdout, stderr = CommandRunner.run_command([
                    'wmic', 'diskdrive', 'get', 'status,size,model'
                ], timeout=10)
                health_info['windows_disk_status'] = stdout
            
            elif CommandRunner.is_command_available('smartctl'):
                # Use smartmontools if available
                code, stdout, stderr = CommandRunner.run_command([
                    'smartctl', '--scan'
                ], timeout=10)
                health_info['smart_scan'] = stdout
            
        except Exception as e:
            health_info['disk_health_error'] = str(e)
        
        return health_info
    
    def _check_disk_fragmentation(self) -> Dict[str, any]:
        """Check disk fragmentation (Windows only)."""
        if self.os_info['os_type'] != 'windows':
            return {'note': 'Fragmentation check only available on Windows'}
        
        try:
            code, stdout, stderr = CommandRunner.run_command([
                'powershell', '-Command',
                'Get-Volume | Where-Object {$_.DriveLetter} | Select-Object DriveLetter,FileSystemType,HealthStatus | ConvertTo-Json'
            ], timeout=15)
            
            volumes = json.loads(stdout)
            if not isinstance(volumes, list):
                volumes = [volumes] if volumes else []
            
            return {'volume_health': volumes}
        
        except Exception as e:
            return {'fragmentation_error': str(e)}
    
    def analyze_network_performance(self) -> Dict[str, any]:
        """Analyze network performance."""
        network_analysis = {
            'network_latency': self._test_network_latency(),
            'dns_performance': self._test_dns_performance(),
            'bandwidth_usage': self._analyze_bandwidth_usage()
        }
        
        return network_analysis
    
    def _test_network_latency(self) -> Dict[str, any]:
        """Test network latency to common servers."""
        latency_results = {}
        
        test_hosts = [
            ('google.com', 'Google DNS'),
            ('8.8.8.8', 'Google Public DNS'),
            ('1.1.1.1', 'Cloudflare DNS')
        ]
        
        for host, description in test_hosts:
            try:
                if self.os_info['os_type'] == 'windows':
                    cmd = ['ping', '-n', '4', host]
                else:
                    cmd = ['ping', '-c', '4', host]
                
                code, stdout, stderr = CommandRunner.run_command(cmd, timeout=10)
                
                # Parse ping results (simplified)
                if code == 0:
                    latency_results[host] = {
                        'description': description,
                        'success': True,
                        'output': stdout[-200:]  # Last 200 chars
                    }
                else:
                    latency_results[host] = {
                        'description': description,
                        'success': False,
                        'error': stderr[:100]
                    }
            
            except Exception as e:
                latency_results[host] = {
                    'description': description,
                    'success': False,
                    'error': str(e)
                }
        
        return latency_results
    
    def _test_dns_performance(self) -> Dict[str, any]:
        """Test DNS resolution performance."""
        dns_results = {}
        
        test_domains = ['google.com', 'microsoft.com', 'github.com']
        
        for domain in test_domains:
            try:
                if self.os_info['os_type'] == 'windows':
                    cmd = ['nslookup', domain]
                else:
                    cmd = ['nslookup', domain]
                
                start_time = time.time()
                code, stdout, stderr = CommandRunner.run_command(cmd, timeout=5)
                dns_time = time.time() - start_time
                
                dns_results[domain] = {
                    'resolution_time_ms': round(dns_time * 1000, 2),
                    'success': code == 0,
                    'output': stdout[:200] if code == 0 else stderr[:200]
                }
            
            except Exception as e:
                dns_results[domain] = {
                    'success': False,
                    'error': str(e)
                }
        
        return dns_results
    
    def _analyze_bandwidth_usage(self) -> Dict[str, any]:
        """Analyze current bandwidth usage."""
        if not PSUTIL_AVAILABLE:
            return {'error': 'psutil not available'}
        
        try:
            # Sample network usage over 5 seconds
            net_before = psutil.net_io_counters()
            time.sleep(5)
            net_after = psutil.net_io_counters()
            
            bytes_sent = net_after.bytes_sent - net_before.bytes_sent
            bytes_recv = net_after.bytes_recv - net_before.bytes_recv
            
            # Calculate rates (per second)
            kb_sent_per_sec = (bytes_sent / 5) / 1024
            kb_recv_per_sec = (bytes_recv / 5) / 1024
            
            return {
                'kb_sent_per_second': round(kb_sent_per_sec, 2),
                'kb_received_per_second': round(kb_recv_per_sec, 2),
                'total_bytes_sent': net_after.bytes_sent,
                'total_bytes_received': net_after.bytes_recv
            }
        
        except Exception as e:
            return {'error': str(e)}
    
    def generate_recommendations(self) -> List[str]:
        """Generate performance optimization recommendations."""
        recommendations = []
        
        try:
            # Analyze current performance and generate suggestions
            snapshot = self.capture_performance_snapshot()
            
            # CPU recommendations
            cpu_usage = snapshot.get('cpu_usage', {}).get('overall_usage_percent', 0)
            if cpu_usage > 80:
                recommendations.append("High CPU usage detected. Consider closing unnecessary applications or upgrading CPU.")
            
            # Memory recommendations
            memory = snapshot.get('memory_usage', {}).get('virtual_memory', {})
            memory_percent = memory.get('used_percent', 0)
            if memory_percent > 80:
                recommendations.append(f"High memory usage ({memory_percent:.1f}%). Consider adding more RAM or closing memory-intensive applications.")
            
            swap_percent = snapshot.get('memory_usage', {}).get('swap_memory', {}).get('used_percent', 0)
            if swap_percent > 25:
                recommendations.append("High swap usage indicates insufficient RAM. Consider upgrading memory.")
            
            # Disk recommendations
            disk_metrics = snapshot.get('disk_usage', {})
            if isinstance(disk_metrics.get('partitions'), list):
                for partition in disk_metrics['partitions']:
                    if partition.get('used_percent', 0) > 90:
                        recommendations.append(f"Disk {partition.get('mountpoint', 'unknown')} is {partition.get('used_percent'):.1f}% full. Consider freeing up space.")
            
            # Process count recommendations
            process_count = snapshot.get('process_count', 0)
            if process_count > 300:
                recommendations.append(f"High process count ({process_count}). Consider reviewing running applications and services.")
            
            # General recommendations
            recommendations.extend([
                "Regularly restart the system to clear memory and apply updates.",
                "Keep the system updated with the latest security patches.",
                "Use antivirus software to protect against malware that can impact performance.",
                "Consider SSD upgrade if using traditional hard drives for better performance.",
                "Monitor startup programs and disable unnecessary ones."
            ])
            
        except Exception as e:
            recommendations.append(f"Error generating recommendations: {str(e)}")
        
        return recommendations


def main():
    """Main function for standalone execution."""
    import argparse
    
    parser = argparse.ArgumentParser(description='System performance analyzer')
    parser.add_argument('--duration', type=int, default=5,
                       help='Analysis duration in minutes (default: 5)')
    parser.add_argument('--output', help='Output file path (JSON format)')
    parser.add_argument('--verbose', action='store_true',
                       help='Enable verbose logging')
    parser.add_argument('--quick', action='store_true',
                       help='Run quick analysis (snapshot only)')
    
    args = parser.parse_args()
    
    # Setup logging
    log_level = 'DEBUG' if args.verbose else 'INFO'
    logger = LogManager.setup_logging(log_level)
    
    # Run analysis
    analyzer = PerformanceAnalyzer(logger)
    
    if args.quick:
        logger.info("Running quick performance analysis")
        analysis = {
            'timestamp': datetime.now().isoformat(),
            'quick_analysis': True,
            'performance_snapshot': analyzer.capture_performance_snapshot(),
            'bottleneck_analysis': analyzer.analyze_bottlenecks(),
            'resource_hogs': analyzer.identify_resource_hogs(),
            'recommendations': analyzer.generate_recommendations()
        }
    else:
        analysis = analyzer.run_full_analysis(args.duration)
    
    # Output results
    if args.output:
        with open(args.output, 'w') as f:
            json.dump(analysis, f, indent=2, default=str)
        print(f"Analysis results saved to {args.output}")
    else:
        # Print summary to console
        print(f"\n=== Performance Analysis Summary ===")
        
        if 'performance_snapshot' in analysis:
            snapshot = analysis['performance_snapshot']
        else:
            snapshot = analysis.get('baseline_performance', {})
        
        # System summary
        if 'system_info' in analysis:
            sys_info = analysis['system_info']
            print(f"System: {sys_info.get('distro', 'unknown')} on {sys_info.get('hostname', 'unknown')}")
        
        # Performance summary
        cpu_usage = snapshot.get('cpu_usage', {}).get('overall_usage_percent')
        if cpu_usage is not None:
            print(f"CPU Usage: {cpu_usage:.1f}%")
        
        memory = snapshot.get('memory_usage', {}).get('virtual_memory', {})
        if memory:
            print(f"Memory Usage: {memory.get('used_percent', 0):.1f}% of {memory.get('total_gb', 0):.1f}GB")
        
        # Bottleneck summary
        bottlenecks = analysis.get('bottleneck_analysis', {})
        overall = bottlenecks.get('overall_assessment', 'unknown')
        print(f"Overall Assessment: {overall.upper()}")
        
        # Top recommendations
        recommendations = analysis.get('recommendations', [])
        if recommendations:
            print(f"\nTop Recommendations:")
            for i, rec in enumerate(recommendations[:3], 1):
                print(f"{i}. {rec}")
        
        print(f"\nTimestamp: {analysis.get('timestamp', 'unknown')}")


if __name__ == '__main__':
    main()