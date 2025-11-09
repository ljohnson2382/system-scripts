# System Scripts - Cross-Platform Automation Toolkit

A comprehensive automation toolkit for managing system updates, health checks, maintenance, and help desk troubleshooting across Linux distributions, macOS, and Windows. Built with Python for portability, logging, and cross-platform compatibility.

**Author:** Loyd Johnson  
**Project Status:** Active Development  
**Latest Update:** November 2025

## 🎯 Vision & Philosophy

This toolkit represents my journey in developing scalable, modular solutions for freelance systems administration and IT support work. The project emphasizes:

- **Modularity**: Each script is self-contained and reusable across different client environments
- **Clarity**: Well-documented code with comprehensive logging for easy troubleshooting
- **Cross-Platform Compatibility**: Solutions that work seamlessly across Linux distributions, macOS, and Windows
- **Professional Standards**: Production-ready scripts designed for repeatable use in enterprise environments
- **Continuous Learning**: Each iteration incorporates new skills and best practices in Python development

## 🚀 Features

### Core Automation
- **Cross-Platform Support**: Debian/Ubuntu, Arch/Manjaro, Fedora/RHEL/CentOS, macOS, and Windows
- **Automatic OS Detection**: Intelligently detects your distribution and runs the appropriate update script
- **Comprehensive Health Checks**: Disk space, memory, services, network connectivity, and more
- **Flexible Configuration**: JSON-based configs with multiple presets (default, security-only, conservative, aggressive)
- **Robust Logging**: Detailed logs with configurable levels and both file/console output
- **Safety First**: Pre/post-update health checks with configurable abort conditions
- **Modular Design**: Clean, well-documented Python modules that can be used independently

### Help Desk & Troubleshooting
- **Network Diagnostics**: Comprehensive network troubleshooting with cross-platform support
- **System Information Gathering**: Complete hardware/software inventory and analysis
- **Performance Analysis**: Real-time performance monitoring and bottleneck identification
- **Windows Support**: Native Windows batch scripts and PowerShell modules
- **Interactive Tools**: Menu-driven interfaces for IT support tasks
- **Professional Reporting**: JSON output for automation and reporting integration

## 📁 Project Structure

```
system-scripts/
├── auto_update.py              # Main orchestrator script
├── utils/                      # Core utilities and helpers
│   └── system_utils.py        #   OS detection, logging, command execution
├── scripts/                    # Platform-specific scripts and tools
│   ├── common/                #   Shared components
│   │   └── health_checks.py   #     System health monitoring
│   ├── helpdesk/              #   Help desk troubleshooting tools
│   │   ├── network_diagnostics.py    #     Network troubleshooting toolkit
│   │   ├── system_info.py            #     System information gathering
│   │   └── performance_analyzer.py   #     Performance analysis and optimization
│   ├── windows/               #   Windows-specific tools
│   │   ├── windows_maintenance.bat   #     Interactive maintenance script
│   │   └── windows_powershell_utils.ps1  #  PowerShell utility functions
│   ├── debian/                #   Debian/Ubuntu updates
│   │   └── auto_update.py     #     Uses unattended-upgrades
│   ├── arch/                  #   Arch Linux updates  
│   │   └── auto_update.py     #     Uses pacman + AUR helpers
│   ├── fedora/                #   Fedora/RHEL updates
│   │   └── auto_update.py     #     Uses dnf/yum
│   └── macos/                 #   macOS updates
│       └── auto_update.py     #     Uses softwareupdate + Homebrew
├── configs/                    # Configuration files
│   ├── update_config.json     #   Default configuration
│   ├── security_only.json     #   Security updates only
│   ├── conservative.json      #   Minimal changes, maximum safety
│   └── aggressive.json        #   Full automation with auto-reboot
└── logs/                      # Log files (auto-created)
```

## 🔧 Installation

### Prerequisites

**All Platforms:**
- Python 3.6+ 
- `psutil` Python package (`pip install psutil`)

**Linux:**
- `sudo` access for system updates
- Package manager (`apt`, `pacman`, `dnf`/`yum`) 

**Windows:**
- Administrator privileges for system maintenance
- PowerShell 5.1+ (included with Windows 10/11)
- Optional: PSWindowsUpdate module for advanced update management

**Arch Linux (Optional):**
- AUR helper (`yay`, `paru`, `trizen`) for AUR package updates

**macOS (Optional):**
- Homebrew for package management
- `mas` (Mac App Store CLI) for App Store updates: `brew install mas`

### Setup

1. **Clone the repository:**
   ```bash
   git clone <repository-url> system-scripts
   cd system-scripts
   ```

2. **One-Click Environment Setup:**

   **🚀 Quick Setup (Recommended) - Automated Installation:**
   
   Choose the setup script for your platform:
   
   ```bash
   # Windows (PowerShell or Command Prompt)
   setup.bat
   
   # Linux/macOS (Terminal)  
   chmod +x setup.sh
   ./setup.sh
   
   # Cross-platform Python script (any system)
   python setup_environment.py
   ```
   
   **What these scripts do:**
   - ✅ Check Python version compatibility (3.6+ required)
   - ✅ Create virtual environment in `venv/` directory
   - ✅ Upgrade pip to latest version
   - ✅ Install all required dependencies (`psutil`, `requests`)
   - ✅ Verify installation by testing imports
   - ✅ Display next steps and usage instructions

   **⚠️ Important**: These scripts create the virtual environment but **do not automatically activate it**. You'll need to activate it manually (see step 3).

3. **Activate Virtual Environment** (Required for each session):

   After running setup, activate the virtual environment:
   
   ```bash
   # Windows (PowerShell)
   venv\Scripts\Activate.ps1
   
   # Windows (Command Prompt)  
   venv\Scripts\activate.bat
   
   # Linux/macOS
   source venv/bin/activate
   ```
   
   **You'll know it's activated when you see `(venv)` at the start of your command prompt.**

4. **Verify Installation:**
   ```bash
   # Test core functionality
   python auto_update.py --check-prereq
   
   # Test help desk tools
   python scripts/helpdesk/system_info.py
   python scripts/helpdesk/network_diagnostics.py
   ```

5. **When You're Done Working:**
   ```bash
   # Deactivate virtual environment
   deactivate
   ```

---

### 🔄 **Daily Workflow:**

Every time you want to use the toolkit:

1. **Navigate to project directory:**
   ```bash
   cd system-scripts
   ```

2. **Activate virtual environment:**
   ```bash
   # Windows PowerShell
   venv\Scripts\Activate.ps1
   
   # Linux/macOS
   source venv/bin/activate
   ```

3. **Use the tools** (with `(venv)` showing in your prompt)

4. **Deactivate when done:**
   ```bash
   deactivate
   ```

---

### 🛠️ **Alternative: Manual Setup**

If you prefer manual control:

   ```bash
   # Create virtual environment
   python -m venv venv
   
   # Activate virtual environment
   # Windows:
   venv\Scripts\activate
   # Linux/macOS:
   source venv/bin/activate
   
   # Install dependencies
   pip install -r requirements.txt
   
   # For development (optional):
   pip install -r requirements-dev.txt
   ```

## 📋 Dependencies

✅ **All dependencies are pre-installed in the virtual environment!**

The toolkit has minimal external dependencies that are automatically installed during setup:

**✅ Pre-installed in Virtual Environment:**
- `psutil>=5.8.0` - System and process monitoring *(already installed)*
- `requests>=2.25.0` - HTTP operations for network tests *(already installed)*

**✅ Python Standard Library** (no installation required):
- `os`, `sys`, `platform`, `subprocess`, `json`, `logging`, `socket`
- `datetime`, `time`, `tempfile`, `argparse`, `typing`

**Development dependencies** (optional, for contributors):
- `pytest`, `black`, `flake8`, `mypy` for testing and code quality
- Install with: `pip install -r requirements-dev.txt`

**🎯 Ready to Use**: After running the setup script, all required dependencies are available in the `venv/` directory. Simply activate the environment and start using the tools!

## 🎯 Quick Start

### Basic Usage

Run updates with default settings:
```bash
python auto_update.py
```

Show what would be done (dry run):
```bash
python auto_update.py --dry-run
```

Use a specific configuration:
```bash
python auto_update.py --config configs/security_only.json
```

### Command Line Options

```bash
python auto_update.py [OPTIONS]

Options:
  --config, -c FILE         Use custom configuration file
  --dry-run, -n            Show what would be done without making changes  
  --verbose, -v            Enable verbose logging
  --security-only          Install security updates only (where supported)
  --no-reboot              Disable automatic reboot/restart
  --force                  Force updates even if health checks fail
  --check-prereq           Check prerequisites and exit
  --list-supported         List supported distributions and exit
```

### Platform-Specific Examples

**Debian/Ubuntu:**
```bash
# Security updates only
python auto_update.py --security-only

# Full update with custom config
python auto_update.py --config configs/conservative.json
```

**Arch Linux:**
```bash
# Include AUR packages (requires AUR helper)
python scripts/arch/auto_update.py --aur

# System packages only
python auto_update.py --config configs/arch_no_aur.json
```

**Fedora/RHEL:**
```bash
# Security updates only
python auto_update.py --security-only

# Update with firmware
python scripts/fedora/auto_update.py --config configs/aggressive.json
```

**macOS:**
```bash
# All updates (system + App Store + Homebrew)
python auto_update.py

# System updates only
python auto_update.py --no-homebrew --no-app-store
```

**Windows:**
```batch
# Interactive maintenance menu (run as Administrator)
scripts\windows\windows_maintenance.bat

# PowerShell utilities
powershell -ExecutionPolicy Bypass -File scripts\windows\windows_powershell_utils.ps1
```

## ⚙️ Configuration

### Configuration Files

The toolkit uses JSON configuration files located in the `configs/` directory:

- **`update_config.json`**: Default balanced configuration
- **`security_only.json`**: Only security updates, minimal changes
- **`conservative.json`**: Maximum safety, manual conflict resolution
- **`aggressive.json`**: Full automation with auto-reboot

### Configuration Structure

```json
{
  "general": {
    "log_level": "INFO",
    "timeout_minutes": 60,
    "pre_update_health_check": true,
    "post_update_health_check": true,
    "backup_important_configs": true
  },
  
  "health_checks": {
    "disk_warning_threshold": 80,
    "disk_critical_threshold": 90,
    "memory_warning_threshold": 80,
    "check_services": ["ssh"],
    "check_ports": [22, 80, 443],
    "remote_hosts": ["google.com:80", "8.8.8.8:53"]
  },
  
  "debian": {
    "auto_reboot": false,
    "unattended_upgrade": true,
    "package_blacklist": []
  },
  
  "arch": {
    "update_aur": false,
    "aur_helper": "yay",
    "clean_cache": true
  },
  
  "fedora": {
    "install_security_only": false,
    "remove_old_kernels": true,
    "max_kernels_to_keep": 3
  },
  
  "macos": {
    "update_homebrew": true,
    "update_app_store": true,
    "homebrew_cleanup": true
  }
}
```

### Creating Custom Configurations

1. Copy an existing configuration:
   ```bash
   cp configs/update_config.json configs/my_config.json
   ```

2. Edit the settings:
   ```bash
   nano configs/my_config.json
   ```

3. Use your configuration:
   ```bash
   python auto_update.py --config configs/my_config.json
   ```

## 🔍 Health Checks

The toolkit includes comprehensive health monitoring:

### System Health Checks
- **Disk Space**: Monitors all mounted filesystems with configurable thresholds
- **Memory Usage**: Tracks RAM and swap usage
- **System Load**: CPU load average (Linux/macOS) or CPU percentage (Windows)
- **Uptime**: System boot time and uptime
- **Service Status**: Checks if specified services are running
- **Port Monitoring**: Verifies that specified ports are listening
- **Network Connectivity**: Tests connection to remote hosts

### Health Check Configuration
```json
"health_checks": {
  "disk_warning_threshold": 80,
  "disk_critical_threshold": 90,
  "memory_warning_threshold": 80,
  "ssh_timeout": 5,
  "check_services": ["ssh", "systemd-resolved", "nginx"],
  "check_ports": [22, 80, 443, 3306],
  "remote_hosts": [
    "google.com:80",
    "your-server.com:22",
    "8.8.8.8:53"
  ]
}
```

### Running Health Checks Standalone
```bash
python scripts/common/health_checks.py
```

## 🛠️ Help Desk & Troubleshooting Tools

The toolkit includes comprehensive help desk utilities for system troubleshooting and user support.

### Network Diagnostics

Comprehensive network troubleshooting toolkit with cross-platform support:

```bash
# Run full network diagnostics
python scripts/helpdesk/network_diagnostics.py --full

# Test specific connectivity
python scripts/helpdesk/network_diagnostics.py --ping-test --dns-test

# Check network interfaces
python scripts/helpdesk/network_diagnostics.py --interfaces

# Test specific ports
python scripts/helpdesk/network_diagnostics.py --port-scan --host example.com --ports 80,443,22
```

**Features:**
- Network interface detection and analysis
- DNS resolution testing and timing
- Connectivity tests (ping, traceroute)
- Port scanning and service detection
- Bandwidth assessment and monitoring
- Route table analysis
- Cross-platform Windows/Unix support

### System Information Gathering

Complete system inventory and analysis:

```bash
# Generate comprehensive system report
python scripts/helpdesk/system_info.py

# Save detailed report to file
python scripts/helpdesk/system_info.py --output system_report.json

# Verbose output with debug information
python scripts/helpdesk/system_info.py --verbose
```

**Collected Information:**
- Hardware details (CPU, memory, storage, graphics)
- Software inventory (OS, applications, packages)
- Network configuration and statistics
- Storage usage and health
- Running processes and services
- Recent system logs and events
- Performance metrics and uptime

### Performance Analysis

Advanced performance monitoring and optimization:

```bash
# Run full 5-minute performance analysis
python scripts/helpdesk/performance_analyzer.py

# Quick performance snapshot
python scripts/helpdesk/performance_analyzer.py --quick

# Extended 15-minute analysis with detailed reporting
python scripts/helpdesk/performance_analyzer.py --duration 15 --output perf_analysis.json
```

**Analysis Features:**
- Real-time performance monitoring
- Bottleneck identification (CPU, memory, disk, network)
- Resource usage tracking over time
- Process and service analysis
- Startup performance evaluation
- Disk I/O and network performance testing
- Optimization recommendations
- Performance trending and alerts

### Windows-Specific Tools

#### Windows Maintenance Script

Interactive batch script for comprehensive Windows maintenance:

```batch
# Run as Administrator
scripts\windows\windows_maintenance.bat
```

**Available Functions:**
1. **System Health Check** - SFC, DISM, memory diagnostics
2. **Disk Cleanup** - Temp files, browser cache, optimization
3. **System Updates** - Windows Update management
4. **Service Management** - Start/stop/restart services
5. **Network Diagnostics** - Connectivity and configuration
6. **User Account Management** - Create, modify, reset accounts
7. **Registry Maintenance** - Backup, restore, cleanup
8. **Performance Monitoring** - Real-time system metrics
9. **Security Scanning** - Windows Defender, firewall checks
10. **System Information** - Comprehensive reporting
11. **Backup Management** - Restore points, file backups

#### Windows PowerShell Utilities

Professional PowerShell module with advanced functions:

```powershell
# Import the module
Import-Module scripts\windows\windows_powershell_utils.ps1

# Get comprehensive system information
Get-SystemInfo

# Run system health diagnostics
Test-SystemHealth

# Perform disk cleanup
Invoke-DiskCleanup -IncludeBrowserCache -EmptyRecycleBin

# Manage Windows services
Manage-WindowsServices -Action List
Manage-WindowsServices -Action Restart -ServiceName "Spooler"

# Test network connectivity
Test-NetworkConnectivity

# Get performance metrics
Get-PerformanceMetrics

# Manage Windows updates
Manage-WindowsUpdates -Action Check
Manage-WindowsUpdates -Action Install

# Create system restore point
New-SystemRestorePoint -Description "Before maintenance"

# Manage user accounts
Manage-UserAccounts -Action List
Manage-UserAccounts -Action Create -Username "newuser" -Password "SecurePass123"
```

**PowerShell Functions:**
- `Get-SystemInfo` - Complete system information gathering
- `Test-SystemHealth` - Comprehensive health validation
- `Invoke-DiskCleanup` - Automated cleanup operations
- `Manage-WindowsServices` - Service management utilities
- `Test-NetworkConnectivity` - Network diagnostics and testing
- `Get-PerformanceMetrics` - Real-time performance data
- `Manage-WindowsUpdates` - Update management and installation
- `New-SystemRestorePoint` - System restore point creation
- `Manage-UserAccounts` - User account administration
- `Test-Administrator` - Admin privilege verification

## 🔐 Security Considerations

### Privileges
- Most operations require `sudo` access
- Use `--dry-run` to preview changes before applying
- Scripts validate permissions before attempting privileged operations

### Safety Features
- Pre-update health checks can abort updates if system is unhealthy
- Configuration backups before making changes
- Package database backups (where supported)
- Configurable package blacklists/exclusions
- Timeout protection for all operations

### Best Practices
1. **Test First**: Always run `--dry-run` in new environments
2. **Start Conservative**: Begin with `conservative.json` configuration
3. **Monitor Logs**: Check logs in `/var/log/auto_update_tracker.log`
4. **Gradual Automation**: Manually verify a few runs before enabling auto-reboot
5. **Have Rollback Plan**: Know how to restore from backups

## 🤖 Automation & Scheduling

### Cron Setup

Add to your crontab for regular execution:

```bash
# Edit crontab
crontab -e

# Daily updates at 2 AM
0 2 * * * /usr/bin/python3 /path/to/system-scripts/auto_update.py --config /path/to/system-scripts/configs/security_only.json

# Weekly full updates on Sunday at 3 AM
0 3 * * 0 /usr/bin/python3 /path/to/system-scripts/auto_update.py --config /path/to/system-scripts/configs/update_config.json
```

### Systemd Timer (Linux)

Create a systemd service and timer:

```ini
# /etc/systemd/system/auto-update.service
[Unit]
Description=System Auto Update
After=network.target

[Service]
Type=oneshot
User=root
ExecStart=/usr/bin/python3 /opt/system-scripts/auto_update.py
WorkingDirectory=/opt/system-scripts
```

```ini
# /etc/systemd/system/auto-update.timer
[Unit]
Description=Run auto-update daily
Requires=auto-update.service

[Timer]
OnCalendar=daily
Persistent=true

[Install]
WantedBy=timers.target
```

Enable the timer:
```bash
sudo systemctl enable --now auto-update.timer
```

### macOS launchd

Create a LaunchDaemon plist:

```xml
<!-- /Library/LaunchDaemons/com.system-scripts.auto-update.plist -->
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.system-scripts.auto-update</string>
    <key>ProgramArguments</key>
    <array>
        <string>/usr/bin/python3</string>
        <string>/opt/system-scripts/auto_update.py</string>
    </array>
    <key>StartCalendarInterval</key>
    <dict>
        <key>Hour</key>
        <integer>2</integer>
        <key>Minute</key>
        <integer>0</integer>
    </dict>
</dict>
</plist>
```

Load the daemon:
```bash
sudo launchctl load /Library/LaunchDaemons/com.system-scripts.auto-update.plist
```

## 📊 Logging & Monitoring

### Log Files

Logs are written to:
- **Linux**: `/var/log/auto_update_tracker.log` (fallback: `./logs/`)
- **macOS**: `~/Library/Logs/system-scripts/auto_update_tracker.log`
- **Windows**: `~/Documents/system-scripts/logs/auto_update_tracker.log`

### Log Format

```
2024-11-08 14:30:15 - system_scripts - INFO - Starting Debian/Ubuntu update cycle
2024-11-08 14:30:16 - system_scripts - INFO - Running pre-update health check
2024-11-08 14:30:17 - system_scripts - INFO - Disk space check: / 45.2% used (OK)
2024-11-08 14:30:18 - system_scripts - INFO - Memory usage: 34.5% (OK)
2024-11-08 14:30:20 - system_scripts - INFO - Updating package lists
2024-11-08 14:30:25 - system_scripts - INFO - Found 23 available updates (5 security)
2024-11-08 14:30:26 - system_scripts - INFO - Running unattended upgrades
2024-11-08 14:32:15 - system_scripts - INFO - Update cycle completed with status: success
```

### Monitoring Integration

The toolkit outputs JSON-structured results that can be integrated with monitoring systems:

```python
# Example monitoring integration
import json
import subprocess

result = subprocess.run(
    ['python', 'auto_update.py', '--config', 'configs/security_only.json'],
    capture_output=True, text=True
)

if result.returncode == 0:
    # Parse results for monitoring
    data = json.loads(result.stdout)
    send_to_monitoring_system(data)
```

## 🐛 Troubleshooting

### Common Issues

**Permission Denied Errors:**
- Ensure your user has `sudo` access
- Check that scripts have execute permissions
- Verify log directory is writable

**Package Manager Not Found:**
- Ensure the appropriate package manager is installed
- Check that PATH includes package manager location
- Verify OS detection is working: `python auto_update.py --check-prereq`

**Health Checks Failing:**
- Review health check thresholds in configuration
- Use `--force` to bypass health checks (not recommended)
- Run health checks standalone to diagnose: `python scripts/common/health_checks.py`

**Timeouts:**
- Increase `timeout_minutes` in configuration
- Check network connectivity for package downloads
- Consider running during off-peak hours

### Debug Mode

Enable verbose logging for troubleshooting:
```bash
python auto_update.py --verbose --dry-run
```

### Platform-Specific Issues

**Debian/Ubuntu:**
- Ensure `unattended-upgrades` package is installed
- Check repository configuration in `/etc/apt/sources.list`
- Verify GPG keys for repositories

**Arch Linux:**
- Install an AUR helper for AUR package support: `yay`, `paru`, or `trizen`
- Update mirrorlist if package downloads are slow
- Check for conflicting packages that need manual resolution

**Fedora/RHEL:**
- Ensure `dnf` or `yum` is available
- Check repository configuration in `/etc/yum.repos.d/`
- Install `dnf-automatic` for automatic update scheduling

**macOS:**
- Install Homebrew for package management
- Install `mas` for App Store updates: `brew install mas`
- Sign into App Store for `mas` to work properly

**Windows:**
- Run scripts as Administrator for system-level operations
- Install PSWindowsUpdate module for advanced update features: `Install-Module PSWindowsUpdate`
- Ensure Windows Update service is running
- Check Windows Firewall if network diagnostics fail

## 🤝 Contributing

Contributions are welcome! Here's how to contribute:

1. **Fork the repository**
2. **Create a feature branch**: `git checkout -b feature/new-distro-support`
3. **Make your changes** following the existing code style
4. **Add tests** if applicable
5. **Update documentation** for new features
6. **Submit a pull request**

### Code Style
- Follow PEP 8 for Python code
- Use meaningful variable and function names
- Include docstrings for all functions and classes
- Add type hints where appropriate
- Write comprehensive error handling

### Adding Support for New Distributions

1. Create a new directory: `scripts/newdistro/`
2. Implement `auto_update.py` with the required interface:
   ```python
   class NewDistroUpdater:
       def __init__(self, config=None, logger=None):
           pass
       
       def run_update_cycle(self) -> Dict[str, any]:
           pass
   ```
3. Update `auto_update.py` to include the new distribution
4. Add configuration options to sample configs
5. Update documentation

## 📄 License

This project is released under the MIT License. See `LICENSE` file for details.

## 🆘 Support

- **Issues**: Report bugs and request features via GitHub Issues
- **Documentation**: This README and inline code documentation
- **Examples**: See `configs/` directory for configuration examples
- **Help Desk Tools**: Use built-in diagnostic tools for troubleshooting
  - Run `python scripts/helpdesk/system_info.py` for system analysis
  - Use `python scripts/helpdesk/network_diagnostics.py` for network issues
  - Execute `python scripts/helpdesk/performance_analyzer.py` for performance problems

## 📧 Contact

**Author**: Loyd Johnson  
**Date**: November 2025

---

## 🗺️ Project Roadmap & Future Development

### Current Status: **Phase 2 - Help Desk Integration** ✅

This project follows a phased development approach, with each phase building upon previous capabilities while introducing new functionality.

#### ✅ **Phase 1: Core Automation Foundation** (Completed)
- **Update Automation**: Cross-platform update scripts for Linux distributions and macOS
- **OS Detection**: Intelligent platform identification and routing
- **Health Monitoring**: Pre/post-update system health validation
- **Configuration Management**: JSON-based configuration with multiple presets
- **Logging Framework**: Comprehensive logging with configurable levels
- **Safety Mechanisms**: Abort conditions and validation checks

#### ✅ **Phase 2: Help Desk Integration** (Completed)
- **Network Diagnostics**: Comprehensive network troubleshooting toolkit
- **System Information**: Complete hardware/software inventory collection
- **Performance Analysis**: Real-time monitoring and bottleneck identification
- **Windows Support**: Native batch and PowerShell implementations
- **Professional Documentation**: Complete user guides and SOPs

#### 🔄 **Phase 3: Security & Hardening** (In Planning)
- **SSH Hardening**: Automated SSH configuration and key management
- **Firewall Management**: Platform-specific firewall setup and rule management
- **Security Auditing**: Vulnerability scanning and compliance checking
- **Certificate Management**: SSL/TLS certificate monitoring and renewal
- **Access Control**: User permission auditing and management

#### 📋 **Phase 4: Service Management** (Planned)
- **Service Monitoring**: Automated service health checks and restart logic
- **Process Management**: Resource monitoring and automatic optimization
- **Dependency Tracking**: Service relationship mapping and validation
- **Performance Baselines**: Historical performance tracking and alerting
- **Auto-Remediation**: Intelligent problem detection and resolution

#### 🔧 **Phase 5: Backup & Recovery** (Planned)
- **Backup Automation**: Scheduled system and data backups
- **Restore Procedures**: Automated recovery workflows
- **Configuration Backup**: System configuration versioning
- **Disaster Recovery**: Complete system restoration procedures
- **Data Integrity**: Backup verification and validation

#### 📊 **Phase 6: Reporting & Integration** (Future)
- **Dashboard Interface**: Web-based monitoring and management console
- **API Development**: RESTful API for external integrations
- **Notification Systems**: Email, webhook, and SMS alerting
- **Report Generation**: Automated system reports and analytics
- **Client Portal**: Multi-tenant management capabilities

#### 🏗️ **Phase 7: Enterprise Features** (Future Vision)
- **Centralized Management**: Multi-system orchestration
- **Role-Based Access**: Enterprise authentication and authorization
- **Compliance Reporting**: Automated compliance validation
- **Custom Modules**: Plugin architecture for specialized tasks
- **High Availability**: Redundant system support

### Development Philosophy

**Iterative Enhancement**: Each phase builds upon proven foundations while introducing new capabilities that address real-world freelance IT challenges.

**Client-Driven Features**: New functionality is prioritized based on frequency of use in actual client environments and common IT support scenarios.

**Code Quality Focus**: Every release emphasizes:
- Comprehensive testing and validation
- Clear documentation and examples
- Backward compatibility maintenance
- Security best practices implementation
- Performance optimization and monitoring

**Professional Growth**: This project serves as a showcase of evolving skills in:
- Python development and best practices
- Cross-platform system administration
- Enterprise-level tool development
- Documentation and project management
- DevOps and automation methodologies

---

## 📚 Development Documentation

### Architecture Decisions

**Language Choice**: Python 3.6+ for maximum compatibility and readability  
**Design Pattern**: Modular, object-oriented design with clear separation of concerns  
**Configuration**: JSON-based configuration for easy modification and validation  
**Logging**: Structured logging with configurable levels and output destinations  
**Error Handling**: Comprehensive exception handling with graceful degradation  

### Code Quality Standards

- **PEP 8 Compliance**: Consistent code formatting and style
- **Type Hints**: Static type checking for improved reliability
- **Docstrings**: Comprehensive function and class documentation
- **Modular Design**: Reusable components with clear interfaces
- **Testing**: Unit tests and integration testing (planned)

### Skills Demonstrated

**Python Development**:
- Object-oriented programming and design patterns
- Cross-platform compatibility handling
- Package management and virtual environments
- Error handling and logging best practices
- Type hinting and documentation standards

**System Administration**:
- Multi-platform package management (apt, pacman, dnf, homebrew)
- System monitoring and health checking
- Network diagnostics and troubleshooting
- Performance analysis and optimization
- Windows administration (PowerShell, batch scripting)

**DevOps Practices**:
- Version control and project organization
- Dependency management and environment isolation
- Configuration management and templating
- Documentation and maintenance procedures
- Security considerations and best practices

---

## 🚨 Standard Operating Procedures (SOPs)

### SOP-001: System Information Gathering

**Purpose**: Collect comprehensive system information for troubleshooting and documentation

**When to Use**:
- Initial system assessment for new clients
- Before major system changes or updates
- When investigating performance issues
- For compliance and inventory documentation

**Procedure**:

1. **Environment Preparation**
   ```bash
   # Activate virtual environment
   venv\Scripts\activate  # Windows
   source venv/bin/activate  # Linux/macOS
   
   # Verify dependencies
   python -c "import psutil; print('Dependencies OK')"
   ```

2. **Basic System Information**
   ```bash
   # Run system info gathering
   python scripts/helpdesk/system_info.py
   
   # Save detailed report
   python scripts/helpdesk/system_info.py --output system_report_$(date +%Y%m%d).json
   ```

3. **Analysis and Documentation**
   - Review hardware specifications for compatibility
   - Check software inventory for licensing compliance
   - Verify system resources meet application requirements
   - Document any anomalies or concerns

4. **Follow-up Actions**
   - File report in client documentation system
   - Schedule follow-up for any identified issues
   - Update asset management database

**Expected Outputs**:
- Console summary with key system metrics
- Detailed JSON report (if --output specified)
- Log entries in system-scripts log file

**Troubleshooting**:
- **Permission Errors**: Run with appropriate privileges (Administrator/sudo)
- **Missing psutil**: Reinstall dependencies with `pip install -r requirements.txt`
- **Incomplete Data**: Check for system restrictions or security software interference

---

### SOP-002: Network Connectivity Troubleshooting

**Purpose**: Diagnose and resolve network connectivity issues using systematic approach

**When to Use**:
- User reports internet or network connectivity problems
- Applications failing to connect to remote services
- Slow network performance complaints
- Before and after network configuration changes

**Procedure**:

1. **Initial Assessment**
   ```bash
   # Run basic network diagnostics
   python scripts/helpdesk/network_diagnostics.py
   
   # Test specific hosts if known issues
   python scripts/helpdesk/network_diagnostics.py --hosts google.com github.com company-server.local
   ```

2. **Systematic Testing**
   
   **Layer 1-2 (Physical/Data Link)**:
   - Verify cable connections and link lights
   - Check network adapter status in device manager
   
   **Layer 3 (Network)**:
   - Verify IP configuration: `ipconfig /all` (Windows) or `ip addr show` (Linux)
   - Test default gateway connectivity
   
   **Layer 4+ (Transport/Application)**:
   - DNS resolution testing (included in script)
   - Port connectivity testing (if specific services affected)

3. **Advanced Diagnostics** (if basic tests indicate issues)
   ```bash
   # Windows PowerShell advanced diagnostics
   powershell -ExecutionPolicy Bypass -Command "Import-Module ./scripts/windows/windows_powershell_utils.ps1; Test-NetworkConnectivity"
   
   # Manual testing for specific issues
   ping 8.8.8.8  # Test external connectivity
   nslookup google.com  # Test DNS resolution
   tracert google.com  # Trace route to destination
   ```

4. **Resolution Steps**
   
   **Common Issues and Fixes**:
   - **No connectivity**: Check cables, restart network adapter
   - **DNS issues**: Flush DNS cache, try alternate DNS servers
   - **Slow performance**: Check for interference, update drivers
   - **Intermittent issues**: Check for power management settings

5. **Verification**
   ```bash
   # Re-run diagnostics to confirm resolution
   python scripts/helpdesk/network_diagnostics.py
   ```

**Expected Outputs**:
- Overall network health status (HEALTHY/WARNING/CRITICAL)
- DNS resolution test results
- Ping test results with response times
- Network performance assessment

**Escalation Criteria**:
- Hardware failures requiring replacement
- ISP-related issues requiring provider contact
- Complex routing issues requiring network administrator
- Security-related blocks requiring firewall configuration

---

### SOP-003: Performance Issue Investigation

**Purpose**: Systematically identify and resolve system performance bottlenecks

**When to Use**:
- Users report slow system performance
- Applications running slower than expected
- High resource utilization alerts
- Before system optimization or upgrades

**Procedure**:

1. **Performance Baseline Capture**
   ```bash
   # Quick performance snapshot
   python scripts/helpdesk/performance_analyzer.py --quick
   
   # Extended monitoring for intermittent issues
   python scripts/helpdesk/performance_analyzer.py --duration 15
   ```

2. **Analysis Phase**
   
   **CPU Analysis**:
   - Check overall CPU utilization
   - Identify top CPU-consuming processes
   - Look for sustained high usage patterns
   
   **Memory Analysis**:
   - Monitor RAM utilization percentage
   - Check for excessive swap usage
   - Identify memory-intensive applications
   
   **Disk Analysis**:
   - Check disk space availability
   - Monitor disk I/O patterns
   - Identify storage bottlenecks
   
   **Network Analysis**:
   - Monitor network throughput
   - Check for excessive network activity
   - Identify bandwidth-consuming processes

3. **Bottleneck Identification**
   
   Review performance analyzer recommendations:
   - **CPU Bottleneck**: High sustained CPU usage (>80%)
   - **Memory Bottleneck**: RAM usage >85% or high swap usage
   - **Disk Bottleneck**: High disk usage percentage or slow I/O
   - **Network Bottleneck**: Bandwidth saturation or high latency

4. **Resolution Implementation**
   
   **CPU Issues**:
   - Identify and close unnecessary applications
   - Check for malware or runaway processes
   - Consider CPU upgrade for sustained high loads
   
   **Memory Issues**:
   - Close memory-intensive applications
   - Add more RAM if consistently over 80% usage
   - Check for memory leaks in applications
   
   **Disk Issues**:
   - Free up disk space (use disk cleanup tools)
   - Defragment traditional hard drives
   - Consider SSD upgrade for better performance
   
   **Network Issues**:
   - Limit bandwidth-heavy applications during work hours
   - Check for background update processes
   - Consider network infrastructure upgrades

5. **Verification and Monitoring**
   ```bash
   # Re-run performance analysis
   python scripts/helpdesk/performance_analyzer.py --quick
   
   # Windows-specific performance monitoring
   # Run as Administrator:
   scripts\windows\windows_maintenance.bat
   # Select option 8: Performance Monitoring
   ```

**Expected Outputs**:
- Performance metrics summary (CPU, memory, disk, network)
- Bottleneck analysis with severity levels
- Resource utilization trends over time
- Optimization recommendations

**Documentation Requirements**:
- Before and after performance metrics
- Actions taken and their effectiveness
- Long-term monitoring recommendations
- Hardware upgrade recommendations if applicable

---

### SOP-004: Windows System Maintenance

**Purpose**: Perform comprehensive Windows system maintenance and optimization

**When to Use**:
- Monthly scheduled maintenance
- After malware removal
- Before major software installations
- When system performance degrades

**Prerequisites**:
- Administrator privileges required
- System backup recommended before major changes
- Close all non-essential applications

**Procedure**:

1. **System Health Assessment**
   ```batch
   # Run comprehensive maintenance script as Administrator
   scripts\windows\windows_maintenance.bat
   # Select Option 1: System Health Check
   ```

2. **Disk Maintenance**
   ```batch
   # From maintenance script, select Option 2: Disk Cleanup
   # This performs:
   # - Temporary file cleanup
   # - Browser cache clearing
   # - Recycle bin emptying
   # - Disk optimization
   ```

3. **System Updates**
   ```batch
   # Select Option 3: System Updates
   # Verify Windows Update service status
   # Install available security updates
   ```

4. **Service Optimization**
   ```powershell
   # Using PowerShell utilities
   Import-Module ./scripts/windows/windows_powershell_utils.ps1
   
   # Check system status
   Get-SystemInfo
   Test-SystemHealth
   
   # Performance optimization
   Get-PerformanceMetrics
   ```

5. **Security Validation**
   ```batch
   # From maintenance script, select Option 9: Security Scan
   # Verify Windows Defender status
   # Check firewall configuration
   # Review security event logs
   ```

6. **System Backup**
   ```batch
   # Select Option 11: Backup Management
   # Create system restore point
   # Backup critical user data
   ```

**Maintenance Schedule**:
- **Weekly**: Quick health check and performance review
- **Monthly**: Full maintenance including cleanup and updates
- **Quarterly**: Comprehensive security review and optimization
- **Annually**: Complete system assessment and hardware evaluation

**Quality Assurance**:
- Verify system boots properly after maintenance
- Test critical applications function correctly
- Confirm network connectivity remains stable
- Document any issues or anomalies discovered

---

### SOP-005: Emergency System Recovery

**Purpose**: Rapid system assessment and basic recovery procedures for critical system failures

**When to Use**:
- System won't boot properly
- Critical services are failing
- Suspected system corruption
- After malware incidents

**Immediate Response** (First 15 minutes):

1. **Initial Assessment**
   ```bash
   # If system is accessible, gather critical information
   python scripts/helpdesk/system_info.py --output emergency_assessment.json
   
   # Check system logs for critical errors
   # Linux: journalctl -p err -n 50
   # Windows: Get-EventLog -LogName System -EntryType Error -Newest 10
   ```

2. **Network Isolation** (if security incident suspected)
   - Disconnect from network to prevent data loss or lateral movement
   - Document time of isolation for incident response

3. **Data Protection**
   - Identify critical data that needs immediate backup
   - Use portable storage if system is accessible

**Recovery Procedures**:

1. **Boot and System Validation**
   ```bash
   # If system boots, run comprehensive diagnostics
   python scripts/helpdesk/performance_analyzer.py --quick
   python scripts/helpdesk/network_diagnostics.py
   ```

2. **Windows-Specific Recovery**
   ```batch
   # Run as Administrator if possible
   scripts\windows\windows_maintenance.bat
   # Options 1 (Health Check) and 2 (System Repair)
   
   # System file integrity
   sfc /scannow
   DISM /Online /Cleanup-Image /RestoreHealth
   ```

3. **Linux-Specific Recovery**
   ```bash
   # Check filesystem integrity
   sudo fsck /dev/sdX
   
   # Review system logs
   sudo journalctl -xe
   ```

**Escalation Triggers**:
- Hardware failure indicators
- Filesystem corruption beyond automatic repair
- Evidence of security compromise
- Data loss requiring professional recovery

**Documentation Requirements**:
- Time of incident and discovery
- Initial symptoms and error messages
- Actions taken and results
- Recovery time and final status
- Lessons learned and prevention measures

---

**⚠️ Important**: This toolkit performs system-level changes. Always test thoroughly in a non-production environment before deploying to critical systems. Use `--dry-run` mode to preview changes before applying them.

**🔐 Security Notice**: Help desk tools may require administrator/root privileges. Always follow security best practices and principle of least privilege when deploying in production environments.

**📈 Project Growth**: This toolkit represents ongoing professional development in systems administration, Python programming, and DevOps practices. Each release incorporates new skills and industry best practices.