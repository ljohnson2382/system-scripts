@echo off
:: Windows system maintenance and troubleshooting script
:: Comprehensive Windows help desk toolkit
:: Author: Loyd Johnson
:: Date: November 2025

setlocal enabledelayedexpansion

echo ===============================================
echo    Windows System Maintenance Tool
echo    Author: Loyd Johnson
echo    Date: November 2025
echo ===============================================

:: Check for administrator privileges
net session >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: This script requires administrator privileges.
    echo Please run as administrator.
    pause
    exit /b 1
)

:MAIN_MENU
cls
echo.
echo ===============================================
echo          WINDOWS SYSTEM MAINTENANCE
echo ===============================================
echo.
echo 1. System Health Check
echo 2. Disk Cleanup and Optimization
echo 3. System Updates
echo 4. Service Management
echo 5. Network Diagnostics
echo 6. User Account Management
echo 7. Registry Maintenance
echo 8. Performance Monitoring
echo 9. Security Scan
echo 10. System Information Report
echo 11. Backup Management
echo 12. Exit
echo.
set /p choice="Select an option (1-12): "

if "%choice%"=="1" goto HEALTH_CHECK
if "%choice%"=="2" goto DISK_MAINTENANCE
if "%choice%"=="3" goto SYSTEM_UPDATES
if "%choice%"=="4" goto SERVICE_MANAGEMENT
if "%choice%"=="5" goto NETWORK_DIAGNOSTICS
if "%choice%"=="6" goto USER_MANAGEMENT
if "%choice%"=="7" goto REGISTRY_MAINTENANCE
if "%choice%"=="8" goto PERFORMANCE_MONITORING
if "%choice%"=="9" goto SECURITY_SCAN
if "%choice%"=="10" goto SYSTEM_INFO
if "%choice%"=="11" goto BACKUP_MANAGEMENT
if "%choice%"=="12" goto EXIT_SCRIPT

echo Invalid choice. Please try again.
pause
goto MAIN_MENU

:HEALTH_CHECK
cls
echo ===============================================
echo           SYSTEM HEALTH CHECK
echo ===============================================
echo.

echo Checking system file integrity...
sfc /scannow

echo.
echo Scanning for system corruption...
DISM /Online /Cleanup-Image /CheckHealth

echo.
echo Running memory diagnostic (will require restart)...
echo Do you want to schedule a memory test on next restart? (Y/N)
set /p memtest="Choice: "
if /i "%memtest%"=="Y" (
    mdsched /f
    echo Memory diagnostic scheduled for next restart.
) else (
    echo Memory diagnostic skipped.
)

echo.
echo Checking disk health...
for %%d in (C D E F G H I J K L M N O P Q R S T U V W X Y Z) do (
    if exist %%d:\ (
        echo Checking drive %%d:...
        chkdsk %%d: /f /r /x >nul 2>&1
        if !errorlevel! equ 0 (
            echo Drive %%d: appears healthy
        ) else (
            echo Drive %%d: may have issues - run 'chkdsk %%d: /f /r' manually
        )
    )
)

echo.
echo Health check completed.
pause
goto MAIN_MENU

:DISK_MAINTENANCE
cls
echo ===============================================
echo        DISK CLEANUP AND OPTIMIZATION
echo ===============================================
echo.

echo Running Disk Cleanup for system drive...
cleanmgr /sagerun:1

echo.
echo Clearing temporary files...
del /q /f /s "%TEMP%\*" >nul 2>&1
del /q /f /s "C:\Windows\Temp\*" >nul 2>&1
del /q /f /s "%USERPROFILE%\AppData\Local\Temp\*" >nul 2>&1

echo.
echo Clearing browser caches...
:: Chrome
del /q /f /s "%USERPROFILE%\AppData\Local\Google\Chrome\User Data\Default\Cache\*" >nul 2>&1
:: Firefox
del /q /f /s "%USERPROFILE%\AppData\Local\Mozilla\Firefox\Profiles\*\cache2\*" >nul 2>&1
:: Edge
del /q /f /s "%USERPROFILE%\AppData\Local\Microsoft\Edge\User Data\Default\Cache\*" >nul 2>&1

echo.
echo Emptying Recycle Bin...
rd /s /q "C:\$Recycle.Bin" >nul 2>&1

echo.
echo Optimizing system drives...
for %%d in (C D E F G H I J K L M N O P Q R S T U V W X Y Z) do (
    if exist %%d:\ (
        echo Optimizing drive %%d:...
        defrag %%d: /O /X
    )
)

echo.
echo Disk maintenance completed.
pause
goto MAIN_MENU

:SYSTEM_UPDATES
cls
echo ===============================================
echo            SYSTEM UPDATES
echo ===============================================
echo.

echo Checking for Windows Updates...
powershell -Command "if (Get-Module -ListAvailable -Name PSWindowsUpdate) { Import-Module PSWindowsUpdate; Get-WindowsUpdate } else { Write-Host 'PSWindowsUpdate module not installed. Installing...'; Install-Module PSWindowsUpdate -Force; Import-Module PSWindowsUpdate; Get-WindowsUpdate }"

echo.
echo Do you want to install available updates? (Y/N)
set /p installUpdates="Choice: "
if /i "%installUpdates%"=="Y" (
    echo Installing updates...
    powershell -Command "Install-WindowsUpdate -AcceptAll -AutoReboot"
) else (
    echo Update installation skipped.
)

echo.
echo Checking driver updates...
pnputil /scan-devices

echo.
echo System updates check completed.
pause
goto MAIN_MENU

:SERVICE_MANAGEMENT
cls
echo ===============================================
echo           SERVICE MANAGEMENT
echo ===============================================
echo.

echo Current service status:
echo.

echo === Critical Services ===
sc query "Themes" | findstr "STATE"
sc query "BITS" | findstr "STATE"
sc query "Spooler" | findstr "STATE"
sc query "Audiosrv" | findstr "STATE"
sc query "Dhcp" | findstr "STATE"

echo.
echo Service management options:
echo 1. View all services
echo 2. Start a service
echo 3. Stop a service
echo 4. Restart a service
echo 5. View service dependencies
echo 6. Back to main menu
echo.

set /p svcChoice="Select option: "

if "%svcChoice%"=="1" (
    services.msc
    goto SERVICE_MANAGEMENT
)
if "%svcChoice%"=="2" (
    set /p serviceName="Enter service name to start: "
    net start "!serviceName!"
    pause
    goto SERVICE_MANAGEMENT
)
if "%svcChoice%"=="3" (
    set /p serviceName="Enter service name to stop: "
    net stop "!serviceName!"
    pause
    goto SERVICE_MANAGEMENT
)
if "%svcChoice%"=="4" (
    set /p serviceName="Enter service name to restart: "
    net stop "!serviceName!"
    net start "!serviceName!"
    pause
    goto SERVICE_MANAGEMENT
)
if "%svcChoice%"=="5" (
    set /p serviceName="Enter service name for dependencies: "
    sc enumdepend "!serviceName!"
    pause
    goto SERVICE_MANAGEMENT
)
if "%svcChoice%"=="6" goto MAIN_MENU

echo Invalid choice.
pause
goto SERVICE_MANAGEMENT

:NETWORK_DIAGNOSTICS
cls
echo ===============================================
echo          NETWORK DIAGNOSTICS
echo ===============================================
echo.

echo Testing network connectivity...
ping google.com -n 4
echo.

echo Testing DNS resolution...
nslookup google.com
echo.

echo Displaying network configuration...
ipconfig /all
echo.

echo Testing network adapter status...
powershell -Command "Get-NetAdapter | Select-Object Name, InterfaceDescription, Status, LinkSpeed"

echo.
echo Network troubleshooting options:
echo 1. Reset TCP/IP stack
echo 2. Flush DNS cache
echo 3. Reset Winsock
echo 4. Release and renew IP
echo 5. Show network usage
echo 6. Back to main menu
echo.

set /p netChoice="Select option: "

if "%netChoice%"=="1" (
    echo Resetting TCP/IP stack...
    netsh int ip reset
    echo Reset complete. Restart required.
    pause
    goto NETWORK_DIAGNOSTICS
)
if "%netChoice%"=="2" (
    echo Flushing DNS cache...
    ipconfig /flushdns
    echo DNS cache cleared.
    pause
    goto NETWORK_DIAGNOSTICS
)
if "%netChoice%"=="3" (
    echo Resetting Winsock...
    netsh winsock reset
    echo Winsock reset complete. Restart recommended.
    pause
    goto NETWORK_DIAGNOSTICS
)
if "%netChoice%"=="4" (
    echo Releasing and renewing IP address...
    ipconfig /release
    ipconfig /renew
    echo IP address renewed.
    pause
    goto NETWORK_DIAGNOSTICS
)
if "%netChoice%"=="5" (
    echo Network usage statistics:
    netstat -e
    pause
    goto NETWORK_DIAGNOSTICS
)
if "%netChoice%"=="6" goto MAIN_MENU

echo Invalid choice.
pause
goto NETWORK_DIAGNOSTICS

:USER_MANAGEMENT
cls
echo ===============================================
echo          USER ACCOUNT MANAGEMENT
echo ===============================================
echo.

echo Current user accounts:
net user
echo.

echo User management options:
echo 1. Create new user account
echo 2. Delete user account
echo 3. Change user password
echo 4. Add user to group
echo 5. View user details
echo 6. Reset user profile
echo 7. Back to main menu
echo.

set /p userChoice="Select option: "

if "%userChoice%"=="1" (
    set /p newUser="Enter new username: "
    set /p newPass="Enter password: "
    net user "!newUser!" "!newPass!" /add
    echo User !newUser! created successfully.
    pause
    goto USER_MANAGEMENT
)
if "%userChoice%"=="2" (
    set /p delUser="Enter username to delete: "
    net user "!delUser!" /delete
    echo User !delUser! deleted.
    pause
    goto USER_MANAGEMENT
)
if "%userChoice%"=="3" (
    set /p changeUser="Enter username: "
    set /p newPass="Enter new password: "
    net user "!changeUser!" "!newPass!"
    echo Password changed for !changeUser!.
    pause
    goto USER_MANAGEMENT
)
if "%userChoice%"=="4" (
    set /p addUser="Enter username: "
    set /p groupName="Enter group name: "
    net localgroup "!groupName!" "!addUser!" /add
    echo User !addUser! added to group !groupName!.
    pause
    goto USER_MANAGEMENT
)
if "%userChoice%"=="5" (
    set /p viewUser="Enter username: "
    net user "!viewUser!"
    pause
    goto USER_MANAGEMENT
)
if "%userChoice%"=="6" (
    echo Profile reset requires manual intervention.
    echo Navigate to C:\Users and rename the problematic profile folder.
    echo Then create a new profile by logging in with the user account.
    pause
    goto USER_MANAGEMENT
)
if "%userChoice%"=="7" goto MAIN_MENU

echo Invalid choice.
pause
goto USER_MANAGEMENT

:REGISTRY_MAINTENANCE
cls
echo ===============================================
echo          REGISTRY MAINTENANCE
echo ===============================================
echo.
echo WARNING: Registry modifications can damage your system.
echo Always create a backup before making changes.
echo.

echo Registry maintenance options:
echo 1. Create registry backup
echo 2. Restore registry backup
echo 3. Clean registry (careful!)
echo 4. View registry information
echo 5. Back to main menu
echo.

set /p regChoice="Select option: "

if "%regChoice%"=="1" (
    set backupPath="C:\Windows\Temp\registry_backup_%date:~-4,4%%date:~-10,2%%date:~-7,2%.reg"
    echo Creating registry backup...
    regedit /e !backupPath! HKEY_LOCAL_MACHINE
    echo Registry backup created: !backupPath!
    pause
    goto REGISTRY_MAINTENANCE
)
if "%regChoice%"=="2" (
    echo Available backup files:
    dir "C:\Windows\Temp\registry_backup_*.reg" /b
    set /p restoreFile="Enter backup filename: "
    regedit /s "C:\Windows\Temp\!restoreFile!"
    echo Registry restored from !restoreFile!
    pause
    goto REGISTRY_MAINTENANCE
)
if "%regChoice%"=="3" (
    echo This will scan and fix common registry issues.
    echo Are you sure? (Y/N)
    set /p confirmClean="Choice: "
    if /i "!confirmClean!"=="Y" (
        sfc /scannow
        echo Registry scan completed.
    ) else (
        echo Registry cleaning cancelled.
    )
    pause
    goto REGISTRY_MAINTENANCE
)
if "%regChoice%"=="4" (
    echo Registry hive sizes:
    dir "%SystemRoot%\System32\config" /s
    pause
    goto REGISTRY_MAINTENANCE
)
if "%regChoice%"=="5" goto MAIN_MENU

echo Invalid choice.
pause
goto REGISTRY_MAINTENANCE

:PERFORMANCE_MONITORING
cls
echo ===============================================
echo        PERFORMANCE MONITORING
echo ===============================================
echo.

echo Current system performance:
echo.

echo === CPU Usage ===
wmic cpu get loadpercentage /value | findstr "LoadPercentage"

echo.
echo === Memory Usage ===
wmic OS get TotalVisibleMemorySize,FreePhysicalMemory /value

echo.
echo === Disk Usage ===
wmic logicaldisk get size,freespace,caption /value

echo.
echo === Running Processes (Top 10 by CPU) ===
powershell -Command "Get-Process | Sort-Object CPU -Descending | Select-Object -First 10 Name, CPU, WorkingSet | Format-Table"

echo.
echo Performance monitoring options:
echo 1. Open Task Manager
echo 2. Open Resource Monitor
echo 3. Open Performance Monitor
echo 4. Generate performance report
echo 5. Check startup programs
echo 6. Back to main menu
echo.

set /p perfChoice="Select option: "

if "%perfChoice%"=="1" (
    taskmgr
    goto PERFORMANCE_MONITORING
)
if "%perfChoice%"=="2" (
    resmon
    goto PERFORMANCE_MONITORING
)
if "%perfChoice%"=="3" (
    perfmon
    goto PERFORMANCE_MONITORING
)
if "%perfChoice%"=="4" (
    echo Generating performance report...
    perfmon /report
    echo Performance report generation started.
    pause
    goto PERFORMANCE_MONITORING
)
if "%perfChoice%"=="5" (
    echo Startup programs:
    wmic startup get caption,command
    pause
    goto PERFORMANCE_MONITORING
)
if "%perfChoice%"=="6" goto MAIN_MENU

echo Invalid choice.
pause
goto PERFORMANCE_MONITORING

:SECURITY_SCAN
cls
echo ===============================================
echo             SECURITY SCAN
echo ===============================================
echo.

echo Running basic security checks...
echo.

echo === Checking Windows Defender Status ===
powershell -Command "Get-MpComputerStatus | Select-Object AntivirusEnabled, RealTimeProtectionEnabled, FullScanAge"

echo.
echo === Checking Firewall Status ===
netsh advfirewall show allprofiles state

echo.
echo === Checking for Suspicious Processes ===
tasklist | findstr /i "suspicious known_malware"

echo.
echo === Checking System Files ===
sfc /verifyonly

echo.
echo Security options:
echo 1. Run Windows Defender scan
echo 2. Update virus definitions
echo 3. Check firewall rules
echo 4. View security events
echo 5. Check user permissions
echo 6. Back to main menu
echo.

set /p secChoice="Select option: "

if "%secChoice%"=="1" (
    echo Starting Windows Defender scan...
    powershell -Command "Start-MpScan -ScanType QuickScan"
    echo Scan started. Check Windows Security for progress.
    pause
    goto SECURITY_SCAN
)
if "%secChoice%"=="2" (
    echo Updating virus definitions...
    powershell -Command "Update-MpSignature"
    echo Virus definitions updated.
    pause
    goto SECURITY_SCAN
)
if "%secChoice%"=="3" (
    echo Current firewall rules:
    netsh advfirewall firewall show rule name=all
    pause
    goto SECURITY_SCAN
)
if "%secChoice%"=="4" (
    echo Recent security events:
    powershell -Command "Get-EventLog -LogName Security -Newest 10 | Select-Object TimeGenerated, EventID, Message"
    pause
    goto SECURITY_SCAN
)
if "%secChoice%"=="5" (
    echo User permissions check:
    whoami /all
    pause
    goto SECURITY_SCAN
)
if "%secChoice%"=="6" goto MAIN_MENU

echo Invalid choice.
pause
goto SECURITY_SCAN

:SYSTEM_INFO
cls
echo ===============================================
echo        SYSTEM INFORMATION REPORT
echo ===============================================
echo.

echo Generating comprehensive system information...

echo === System Summary ===
systeminfo | findstr /C:"Host Name" /C:"OS Name" /C:"OS Version" /C:"System Type" /C:"Total Physical Memory"

echo.
echo === Hardware Information ===
wmic computersystem get manufacturer,model,totalphysicalmemory
wmic cpu get name,maxclockspeed,numberofcores

echo.
echo === Storage Information ===
wmic logicaldisk get caption,size,freespace,filesystem

echo.
echo === Network Information ===
ipconfig | findstr /C:"IPv4" /C:"Subnet" /C:"Gateway"

echo.
echo === Installed Software (Sample) ===
wmic product get name,version | head -20

echo.
echo Do you want to save this information to a file? (Y/N)
set /p saveInfo="Choice: "
if /i "%saveInfo%"=="Y" (
    set infoFile="C:\Windows\Temp\system_info_%date:~-4,4%%date:~-10,2%%date:~-7,2%.txt"
    systeminfo > !infoFile!
    echo System information saved to !infoFile!
) else (
    echo System information not saved.
)

pause
goto MAIN_MENU

:BACKUP_MANAGEMENT
cls
echo ===============================================
echo           BACKUP MANAGEMENT
echo ===============================================
echo.

echo Backup management options:
echo 1. Create system restore point
echo 2. View restore points
echo 3. Backup important user files
echo 4. Schedule automatic backups
echo 5. System image backup
echo 6. Back to main menu
echo.

set /p backupChoice="Select option: "

if "%backupChoice%"=="1" (
    echo Creating system restore point...
    powershell -Command "Checkpoint-Computer -Description 'Help Desk Manual Restore Point' -RestorePointType 'MODIFY_SETTINGS'"
    echo System restore point created.
    pause
    goto BACKUP_MANAGEMENT
)
if "%backupChoice%"=="2" (
    echo Available restore points:
    powershell -Command "Get-ComputerRestorePoint | Select-Object SequenceNumber, CreationTime, Description"
    pause
    goto BACKUP_MANAGEMENT
)
if "%backupChoice%"=="3" (
    set /p backupPath="Enter backup destination path: "
    echo Backing up user documents...
    robocopy "%USERPROFILE%\Documents" "!backupPath!\Documents_Backup" /E /Z /R:3
    robocopy "%USERPROFILE%\Desktop" "!backupPath!\Desktop_Backup" /E /Z /R:3
    echo User file backup completed.
    pause
    goto BACKUP_MANAGEMENT
)
if "%backupChoice%"=="4" (
    echo Opening Windows Backup and Restore...
    sdclt
    goto BACKUP_MANAGEMENT
)
if "%backupChoice%"=="5" (
    echo Opening System Image Backup...
    sdclt
    goto BACKUP_MANAGEMENT
)
if "%backupChoice%"=="6" goto MAIN_MENU

echo Invalid choice.
pause
goto BACKUP_MANAGEMENT

:EXIT_SCRIPT
cls
echo.
echo Thank you for using the Windows System Maintenance Tool.
echo.
echo Script completed by: Loyd Johnson
echo Date: November 2025
echo.
echo For additional help, consult Windows documentation
echo or contact your system administrator.
echo.
pause
exit /b 0