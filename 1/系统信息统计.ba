@echo off
echo ===================================================
echo               Windows System Information
echo ===================================================
echo.

REM 显示操作系统信息
echo ================== Operating System ==================
systeminfo | findstr /B /C:"OS Name" /C:"OS Version" /C:"System Manufacturer" /C:"System Model" /C:"System Type" /C:"Total Physical Memory"

REM 显示处理器信息
echo.
echo ===================== CPU Info ======================
wmic cpu get Name, NumberOfCores, NumberOfLogicalProcessors, MaxClockSpeed, Manufacturer, L2CacheSize /format:list

REM 显示内存信息
echo.
echo ==================== Memory Info ====================
wmic MemoryChip get Capacity, Manufacturer, MemoryType, Speed, PartNumber, SerialNumber /format:list

REM 显示磁盘信息
echo.
echo ==================== Disk Drives ====================
wmic diskdrive get Model, Size, InterfaceType, MediaType, Status /format:list

REM 显示网络适配器信息
echo.
echo =============== Network Adapter Info ================
wmic nic where "NetEnabled=True" get Name, MACAddress, Speed, Manufacturer, NetConnectionID /format:list

REM 显示显卡信息
echo.
echo ================== Video Controller ==================
wmic path win32_videocontroller get Name, AdapterRAM, DriverVersion, VideoProcessor /format:list

REM 显示BIOS信息
echo.
echo ======================== BIOS ========================
wmic bios get Manufacturer, Name, Version, SerialNumber /format:list

REM 显示系统启动时间信息
echo.
echo ==================== System Boot Time ====================
systeminfo | findstr /C:"System Boot Time"

REM 显示主板信息
echo.
echo ==================== Motherboard Info ====================
wmic baseboard get Manufacturer, Product, Version, SerialNumber /format:list

REM 显示声卡信息
echo.
echo ==================== Sound Device Info ====================
wmic sounddev get Name, Manufacturer, Status, DeviceID /format:list

REM 显示电源信息
echo.
echo ==================== Battery Info ====================
wmic path win32_battery get Name, BatteryStatus, EstimatedChargeRemaining /format:list

REM 显示网络配置
echo.
echo ==================== Network Configuration ====================
ipconfig

REM 显示系统热修复
echo.
echo ==================== System Hotfixes ====================
wmic qfe list full

pause
