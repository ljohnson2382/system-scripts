# Windows PowerShell Help Desk Utilities
# Comprehensive PowerShell toolkit for Windows system administration
# Author: Loyd Johnson
# Date: November 2025

# Function to check if running as administrator
function Test-Administrator {
    $currentUser = [Security.Principal.WindowsIdentity]::GetCurrent()
    $principal = New-Object Security.Principal.WindowsPrincipal($currentUser)
    return $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
}

# Function to get system information
function Get-SystemInfo {
    Write-Host "=== System Information ===" -ForegroundColor Green
    
    $computerInfo = Get-ComputerInfo
    $os = Get-CimInstance -ClassName Win32_OperatingSystem
    $cpu = Get-CimInstance -ClassName Win32_Processor
    $memory = Get-CimInstance -ClassName Win32_PhysicalMemory
    
    $info = [PSCustomObject]@{
        ComputerName = $computerInfo.CsName
        OSName = $os.Caption
        OSVersion = $os.Version
        OSArchitecture = $os.OSArchitecture
        LastBootTime = $os.LastBootUpTime
        TotalMemoryGB = [Math]::Round(($memory | Measure-Object Capacity -Sum).Sum / 1GB, 2)
        CPUName = $cpu.Name
        CPUCores = $cpu.NumberOfCores
        CPUThreads = $cpu.NumberOfLogicalProcessors
        Domain = $computerInfo.CsDomain
        WindowsVersion = $computerInfo.WindowsVersion
        InstallDate = $os.InstallDate
    }
    
    return $info
}

# Function to check system health
function Test-SystemHealth {
    Write-Host "=== System Health Check ===" -ForegroundColor Green
    
    $healthReport = @{
        SFCResult = $null
        DISMResult = $null
        EventLogErrors = $null
        DiskHealth = @()
        ServiceStatus = @()
        MemoryDiagnostic = $null
    }
    
    # Check SFC
    Write-Host "Running System File Checker..." -ForegroundColor Yellow
    try {
        $sfcResult = & sfc /verifyonly 2>&1
        $healthReport.SFCResult = if ($LASTEXITCODE -eq 0) { "Clean" } else { "Issues Found" }
    } catch {
        $healthReport.SFCResult = "Error: $($_.Exception.Message)"
    }
    
    # Check DISM
    Write-Host "Checking system image health..." -ForegroundColor Yellow
    try {
        $dismResult = & DISM /Online /Cleanup-Image /CheckHealth 2>&1
        $healthReport.DISMResult = if ($LASTEXITCODE -eq 0) { "Healthy" } else { "Issues Found" }
    } catch {
        $healthReport.DISMResult = "Error: $($_.Exception.Message)"
    }
    
    # Check recent errors in event log
    Write-Host "Checking recent system errors..." -ForegroundColor Yellow
    try {
        $recentErrors = Get-WinEvent -FilterHashtable @{LogName='System'; Level=2; StartTime=(Get-Date).AddDays(-7)} -MaxEvents 10 -ErrorAction SilentlyContinue
        $healthReport.EventLogErrors = $recentErrors.Count
    } catch {
        $healthReport.EventLogErrors = "Unable to check"
    }
    
    # Check disk health
    Write-Host "Checking disk health..." -ForegroundColor Yellow
    $disks = Get-PhysicalDisk
    foreach ($disk in $disks) {
        $healthReport.DiskHealth += [PSCustomObject]@{
            FriendlyName = $disk.FriendlyName
            HealthStatus = $disk.HealthStatus
            OperationalStatus = $disk.OperationalStatus
            Size = [Math]::Round($disk.Size / 1GB, 2)
        }
    }
    
    # Check critical services
    Write-Host "Checking critical services..." -ForegroundColor Yellow
    $criticalServices = @('Themes', 'BITS', 'Spooler', 'Audiosrv', 'Dhcp', 'Dnscache', 'EventLog')
    foreach ($serviceName in $criticalServices) {
        $service = Get-Service -Name $serviceName -ErrorAction SilentlyContinue
        if ($service) {
            $healthReport.ServiceStatus += [PSCustomObject]@{
                Name = $service.Name
                Status = $service.Status
                StartType = $service.StartType
            }
        }
    }
    
    return $healthReport
}

# Function to perform disk cleanup
function Invoke-DiskCleanup {
    param(
        [string[]]$Drives = @("C:"),
        [switch]$IncludeBrowserCache,
        [switch]$EmptyRecycleBin
    )
    
    Write-Host "=== Disk Cleanup ===" -ForegroundColor Green
    
    $cleanupResults = @{
        TempFilesCleared = 0
        BrowserCacheCleared = 0
        RecycleBinEmptied = $false
        SpaceFreed = 0
    }
    
    # Clear temporary files
    Write-Host "Clearing temporary files..." -ForegroundColor Yellow
    $tempPaths = @(
        $env:TEMP,
        "C:\Windows\Temp",
        "$env:USERPROFILE\AppData\Local\Temp"
    )
    
    foreach ($path in $tempPaths) {
        if (Test-Path $path) {
            try {
                $beforeSize = (Get-ChildItem $path -Recurse -Force -ErrorAction SilentlyContinue | Measure-Object Length -Sum).Sum
                Get-ChildItem $path -Recurse -Force -ErrorAction SilentlyContinue | Remove-Item -Recurse -Force -ErrorAction SilentlyContinue
                $afterSize = (Get-ChildItem $path -Recurse -Force -ErrorAction SilentlyContinue | Measure-Object Length -Sum).Sum
                $cleanupResults.TempFilesCleared += ($beforeSize - $afterSize)
            } catch {
                Write-Warning "Could not clean: $path"
            }
        }
    }
    
    # Clear browser cache if requested
    if ($IncludeBrowserCache) {
        Write-Host "Clearing browser caches..." -ForegroundColor Yellow
        $browserPaths = @(
            "$env:USERPROFILE\AppData\Local\Google\Chrome\User Data\Default\Cache",
            "$env:USERPROFILE\AppData\Local\Microsoft\Edge\User Data\Default\Cache",
            "$env:USERPROFILE\AppData\Local\Mozilla\Firefox\Profiles\*\cache2"
        )
        
        foreach ($path in $browserPaths) {
            if (Test-Path $path) {
                try {
                    $beforeSize = (Get-ChildItem $path -Recurse -Force -ErrorAction SilentlyContinue | Measure-Object Length -Sum).Sum
                    Get-ChildItem $path -Recurse -Force -ErrorAction SilentlyContinue | Remove-Item -Recurse -Force -ErrorAction SilentlyContinue
                    $afterSize = (Get-ChildItem $path -Recurse -Force -ErrorAction SilentlyContinue | Measure-Object Length -Sum).Sum
                    $cleanupResults.BrowserCacheCleared += ($beforeSize - $afterSize)
                } catch {
                    Write-Warning "Could not clean browser cache: $path"
                }
            }
        }
    }
    
    # Empty recycle bin if requested
    if ($EmptyRecycleBin) {
        Write-Host "Emptying Recycle Bin..." -ForegroundColor Yellow
        try {
            Clear-RecycleBin -Force -ErrorAction SilentlyContinue
            $cleanupResults.RecycleBinEmptied = $true
        } catch {
            Write-Warning "Could not empty Recycle Bin"
        }
    }
    
    return $cleanupResults
}

# Function to manage Windows services
function Manage-WindowsServices {
    param(
        [ValidateSet("List", "Start", "Stop", "Restart", "Status")]
        [string]$Action = "List",
        [string]$ServiceName
    )
    
    Write-Host "=== Service Management ===" -ForegroundColor Green
    
    switch ($Action) {
        "List" {
            return Get-Service | Sort-Object Status, Name
        }
        "Start" {
            if ($ServiceName) {
                try {
                    Start-Service -Name $ServiceName -ErrorAction Stop
                    return "Service '$ServiceName' started successfully"
                } catch {
                    return "Error starting service '$ServiceName': $($_.Exception.Message)"
                }
            }
        }
        "Stop" {
            if ($ServiceName) {
                try {
                    Stop-Service -Name $ServiceName -ErrorAction Stop
                    return "Service '$ServiceName' stopped successfully"
                } catch {
                    return "Error stopping service '$ServiceName': $($_.Exception.Message)"
                }
            }
        }
        "Restart" {
            if ($ServiceName) {
                try {
                    Restart-Service -Name $ServiceName -ErrorAction Stop
                    return "Service '$ServiceName' restarted successfully"
                } catch {
                    return "Error restarting service '$ServiceName': $($_.Exception.Message)"
                }
            }
        }
        "Status" {
            if ($ServiceName) {
                return Get-Service -Name $ServiceName -ErrorAction SilentlyContinue
            }
        }
    }
}

# Function to test network connectivity
function Test-NetworkConnectivity {
    Write-Host "=== Network Connectivity Test ===" -ForegroundColor Green
    
    $testResults = @{
        InternetConnectivity = $null
        DNSResolution = $null
        NetworkAdapters = @()
        IPConfiguration = $null
        Ping = @()
    }
    
    # Test internet connectivity
    Write-Host "Testing internet connectivity..." -ForegroundColor Yellow
    try {
        $testResults.InternetConnectivity = Test-Connection -ComputerName "8.8.8.8" -Count 2 -Quiet
    } catch {
        $testResults.InternetConnectivity = $false
    }
    
    # Test DNS resolution
    Write-Host "Testing DNS resolution..." -ForegroundColor Yellow
    try {
        $dnsTest = Resolve-DnsName -Name "google.com" -ErrorAction Stop
        $testResults.DNSResolution = $true
    } catch {
        $testResults.DNSResolution = $false
    }
    
    # Get network adapter information
    Write-Host "Getting network adapter information..." -ForegroundColor Yellow
    $adapters = Get-NetAdapter | Where-Object { $_.Status -eq "Up" }
    foreach ($adapter in $adapters) {
        $testResults.NetworkAdapters += [PSCustomObject]@{
            Name = $adapter.Name
            InterfaceDescription = $adapter.InterfaceDescription
            Status = $adapter.Status
            LinkSpeed = $adapter.LinkSpeed
            MacAddress = $adapter.MacAddress
        }
    }
    
    # Get IP configuration
    Write-Host "Getting IP configuration..." -ForegroundColor Yellow
    $testResults.IPConfiguration = Get-NetIPConfiguration | Where-Object { $_.NetAdapter.Status -eq "Up" }
    
    # Ping common hosts
    Write-Host "Testing connectivity to common hosts..." -ForegroundColor Yellow
    $testHosts = @("google.com", "microsoft.com", "8.8.8.8", "1.1.1.1")
    foreach ($host in $testHosts) {
        try {
            $pingResult = Test-Connection -ComputerName $host -Count 2 -ErrorAction Stop
            $avgResponseTime = ($pingResult | Measure-Object ResponseTime -Average).Average
            $testResults.Ping += [PSCustomObject]@{
                Host = $host
                Success = $true
                AverageResponseTime = $avgResponseTime
            }
        } catch {
            $testResults.Ping += [PSCustomObject]@{
                Host = $host
                Success = $false
                Error = $_.Exception.Message
            }
        }
    }
    
    return $testResults
}

# Function to get performance metrics
function Get-PerformanceMetrics {
    Write-Host "=== Performance Metrics ===" -ForegroundColor Green
    
    $metrics = @{
        CPU = $null
        Memory = $null
        Disk = @()
        Network = $null
        Processes = @()
        Timestamp = Get-Date
    }
    
    # CPU usage
    Write-Host "Getting CPU metrics..." -ForegroundColor Yellow
    $cpu = Get-CimInstance -ClassName Win32_Processor
    $cpuUsage = (Get-Counter "\Processor(_Total)\% Processor Time" -SampleInterval 1 -MaxSamples 2 | Select-Object -ExpandProperty CounterSamples | Select-Object -Last 1).CookedValue
    
    $metrics.CPU = [PSCustomObject]@{
        Name = $cpu.Name
        Cores = $cpu.NumberOfCores
        LogicalProcessors = $cpu.NumberOfLogicalProcessors
        CurrentUsagePercent = [Math]::Round($cpuUsage, 2)
        MaxClockSpeed = $cpu.MaxClockSpeed
    }
    
    # Memory usage
    Write-Host "Getting memory metrics..." -ForegroundColor Yellow
    $os = Get-CimInstance -ClassName Win32_OperatingSystem
    $totalMemory = $os.TotalVisibleMemorySize * 1KB
    $freeMemory = $os.FreePhysicalMemory * 1KB
    $usedMemory = $totalMemory - $freeMemory
    $memoryUsagePercent = [Math]::Round(($usedMemory / $totalMemory) * 100, 2)
    
    $metrics.Memory = [PSCustomObject]@{
        TotalGB = [Math]::Round($totalMemory / 1GB, 2)
        UsedGB = [Math]::Round($usedMemory / 1GB, 2)
        FreeGB = [Math]::Round($freeMemory / 1GB, 2)
        UsagePercent = $memoryUsagePercent
    }
    
    # Disk usage
    Write-Host "Getting disk metrics..." -ForegroundColor Yellow
    $disks = Get-CimInstance -ClassName Win32_LogicalDisk | Where-Object { $_.DriveType -eq 3 }
    foreach ($disk in $disks) {
        $metrics.Disk += [PSCustomObject]@{
            Drive = $disk.DeviceID
            TotalGB = [Math]::Round($disk.Size / 1GB, 2)
            FreeGB = [Math]::Round($disk.FreeSpace / 1GB, 2)
            UsedGB = [Math]::Round(($disk.Size - $disk.FreeSpace) / 1GB, 2)
            UsagePercent = [Math]::Round((($disk.Size - $disk.FreeSpace) / $disk.Size) * 100, 2)
            FileSystem = $disk.FileSystem
        }
    }
    
    # Network usage
    Write-Host "Getting network metrics..." -ForegroundColor Yellow
    $networkAdapters = Get-CimInstance -ClassName Win32_PerfRawData_Tcpip_NetworkInterface | Where-Object { $_.Name -notlike "*Loopback*" -and $_.Name -notlike "*Isatap*" }
    if ($networkAdapters) {
        $adapter = $networkAdapters | Select-Object -First 1
        $metrics.Network = [PSCustomObject]@{
            Name = $adapter.Name
            BytesReceivedPerSec = $adapter.BytesReceivedPerSec
            BytesSentPerSec = $adapter.BytesSentPerSec
            PacketsReceivedPerSec = $adapter.PacketsReceivedPerSec
            PacketsSentPerSec = $adapter.PacketsSentPerSec
        }
    }
    
    # Top processes by CPU
    Write-Host "Getting process metrics..." -ForegroundColor Yellow
    $processes = Get-Process | Sort-Object CPU -Descending | Select-Object -First 10
    foreach ($process in $processes) {
        $metrics.Processes += [PSCustomObject]@{
            Name = $process.ProcessName
            ID = $process.Id
            CPU = [Math]::Round($process.CPU, 2)
            WorkingSetMB = [Math]::Round($process.WorkingSet / 1MB, 2)
            Handles = $process.Handles
        }
    }
    
    return $metrics
}

# Function to manage Windows updates
function Manage-WindowsUpdates {
    param(
        [ValidateSet("Check", "Install", "List", "History")]
        [string]$Action = "Check"
    )
    
    Write-Host "=== Windows Update Management ===" -ForegroundColor Green
    
    # Check if PSWindowsUpdate module is available
    $psWindowsUpdateModule = Get-Module -ListAvailable -Name PSWindowsUpdate
    if (-not $psWindowsUpdateModule) {
        Write-Host "Installing PSWindowsUpdate module..." -ForegroundColor Yellow
        try {
            Install-Module PSWindowsUpdate -Force -ErrorAction Stop
            Import-Module PSWindowsUpdate
        } catch {
            return "Error installing PSWindowsUpdate module: $($_.Exception.Message)"
        }
    } else {
        Import-Module PSWindowsUpdate
    }
    
    switch ($Action) {
        "Check" {
            Write-Host "Checking for available updates..." -ForegroundColor Yellow
            try {
                return Get-WUList
            } catch {
                return "Error checking for updates: $($_.Exception.Message)"
            }
        }
        "Install" {
            Write-Host "Installing updates..." -ForegroundColor Yellow
            try {
                return Install-WindowsUpdate -AcceptAll -AutoReboot
            } catch {
                return "Error installing updates: $($_.Exception.Message)"
            }
        }
        "List" {
            Write-Host "Listing available updates..." -ForegroundColor Yellow
            try {
                return Get-WUList -Verbose
            } catch {
                return "Error listing updates: $($_.Exception.Message)"
            }
        }
        "History" {
            Write-Host "Getting update history..." -ForegroundColor Yellow
            try {
                return Get-WUHistory | Select-Object -First 20
            } catch {
                return "Error getting update history: $($_.Exception.Message)"
            }
        }
    }
}

# Function to create system restore point
function New-SystemRestorePoint {
    param(
        [string]$Description = "Help Desk Manual Restore Point"
    )
    
    Write-Host "=== Creating System Restore Point ===" -ForegroundColor Green
    
    try {
        Checkpoint-Computer -Description $Description -RestorePointType "MODIFY_SETTINGS"
        return "System restore point created successfully: $Description"
    } catch {
        return "Error creating restore point: $($_.Exception.Message)"
    }
}

# Function to manage user accounts
function Manage-UserAccounts {
    param(
        [ValidateSet("List", "Create", "Enable", "Disable", "ResetPassword")]
        [string]$Action = "List",
        [string]$Username,
        [string]$Password,
        [string]$FullName
    )
    
    Write-Host "=== User Account Management ===" -ForegroundColor Green
    
    switch ($Action) {
        "List" {
            return Get-LocalUser | Select-Object Name, Enabled, LastLogon, Description
        }
        "Create" {
            if ($Username -and $Password) {
                try {
                    $securePassword = ConvertTo-SecureString $Password -AsPlainText -Force
                    New-LocalUser -Name $Username -Password $securePassword -FullName $FullName -Description "Created by Help Desk"
                    return "User account '$Username' created successfully"
                } catch {
                    return "Error creating user account: $($_.Exception.Message)"
                }
            } else {
                return "Username and password are required"
            }
        }
        "Enable" {
            if ($Username) {
                try {
                    Enable-LocalUser -Name $Username
                    return "User account '$Username' enabled successfully"
                } catch {
                    return "Error enabling user account: $($_.Exception.Message)"
                }
            }
        }
        "Disable" {
            if ($Username) {
                try {
                    Disable-LocalUser -Name $Username
                    return "User account '$Username' disabled successfully"
                } catch {
                    return "Error disabling user account: $($_.Exception.Message)"
                }
            }
        }
        "ResetPassword" {
            if ($Username -and $Password) {
                try {
                    $securePassword = ConvertTo-SecureString $Password -AsPlainText -Force
                    Set-LocalUser -Name $Username -Password $securePassword
                    return "Password reset successfully for user '$Username'"
                } catch {
                    return "Error resetting password: $($_.Exception.Message)"
                }
            } else {
                return "Username and new password are required"
            }
        }
    }
}

# Export functions for use in other scripts
Export-ModuleMember -Function *

# Display help information
function Show-HelpDeskMenu {
    Write-Host "===============================================" -ForegroundColor Cyan
    Write-Host "    Windows PowerShell Help Desk Utilities"    -ForegroundColor Cyan
    Write-Host "    Author: Loyd Johnson"                        -ForegroundColor Cyan
    Write-Host "    Date: November 2025"                         -ForegroundColor Cyan
    Write-Host "===============================================" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "Available Functions:" -ForegroundColor Green
    Write-Host "  Get-SystemInfo                 - Get comprehensive system information"
    Write-Host "  Test-SystemHealth              - Run system health checks"
    Write-Host "  Invoke-DiskCleanup             - Perform disk cleanup operations"
    Write-Host "  Manage-WindowsServices         - Manage Windows services"
    Write-Host "  Test-NetworkConnectivity       - Test network connectivity"
    Write-Host "  Get-PerformanceMetrics         - Get system performance metrics"
    Write-Host "  Manage-WindowsUpdates          - Manage Windows updates"
    Write-Host "  New-SystemRestorePoint         - Create system restore point"
    Write-Host "  Manage-UserAccounts            - Manage user accounts"
    Write-Host "  Test-Administrator             - Check if running as administrator"
    Write-Host ""
    Write-Host "Example Usage:" -ForegroundColor Yellow
    Write-Host "  Get-SystemInfo"
    Write-Host "  Test-SystemHealth"
    Write-Host "  Invoke-DiskCleanup -IncludeBrowserCache -EmptyRecycleBin"
    Write-Host "  Manage-WindowsServices -Action List"
    Write-Host "  Test-NetworkConnectivity"
    Write-Host ""
}

# Display menu if script is run directly
if ($MyInvocation.InvocationName -eq "&") {
    Show-HelpDeskMenu
}