#!/bin/bash

# -----------------------------------
# 输出主机名和操作系统信息
echo "-----------------------------------"
echo "Hostname: $(hostname)"
echo "OS Version: $(lsb_release -d | cut -f2-)"
echo "Kernel Version: $(uname -r)"
echo "Uptime: $(uptime -p)"
echo "Last Boot: $(who -b | awk '{print $3, $4}')"
echo "-----------------------------------"

# -----------------------------------
# CPU 信息
echo "CPU Information:"
lscpu | grep -E 'Model name|Socket|Thread|Core|CPU MHz|Hypervisor'
echo "Architecture: $(uname -m)"
echo "CPU Temperature:"
if command -v sensors &> /dev/null; then
    sensors | grep "Core"
else
    echo "sensors command not found. Install via: sudo apt install lm-sensors"
fi
echo "-----------------------------------"

# -----------------------------------
# 内存信息
echo "Memory Information:"
free -h | awk '/^Mem:/ {print "Total Memory: " $2 "\nUsed Memory: " $3 "\nFree Memory: " $4}'
echo "Swap Information:"
free -h | awk '/^Swap:/ {print "Total Swap: " $2 "\nUsed Swap: " $3 "\nFree Swap: " $4}'
echo "-----------------------------------"

# -----------------------------------
# 硬盘信息
echo "Disk Information:"
lsblk -o NAME,SIZE,TYPE,MOUNTPOINT
echo "Disk Usage:"
df -h --total | awk '/^Filesystem|^total/' 
echo "-----------------------------------"

# -----------------------------------
# 显卡信息
echo "GPU Information:"
lspci | grep -i 'vga\|3d\|2d'
if command -v glxinfo &> /dev/null; then
    echo "OpenGL Info:"
    glxinfo | grep "OpenGL" | head -n 3
else
    echo "glxinfo command not found. Install via: sudo apt install mesa-utils"
fi
echo "-----------------------------------"

# -----------------------------------
# 网络信息
echo "Network Information:"
ip -brief address
echo "Default Route:"
ip route | grep default
echo "Nameservers:"
cat /etc/resolv.conf | grep nameserver
echo "-----------------------------------"

# -----------------------------------
# 驱动信息
echo "Driver Information:"
lsmod | head -n 20  # 仅显示前20个加载的模块
echo "-----------------------------------"

# -----------------------------------
# 已安装的软件包信息
echo "Installed Packages (total): $(dpkg-query -l | wc -l)"
echo "First 10 packages:"
dpkg-query -l | head -n 12 | tail -n 10
echo "-----------------------------------"

# -----------------------------------
# 连接的USB设备信息
echo "Connected USB Devices:"
lsusb
echo "-----------------------------------"

# -----------------------------------
# 已加载的服务和守护进程
echo "Loaded Services and Daemons:"
systemctl list-units --type=service --state=running | head -n 10
echo "-----------------------------------"

# -----------------------------------
# 本地时间和时区
echo "Time and Timezone Information:"
timedatectl
echo "-----------------------------------"

# -----------------------------------
echo "System information collected successfully."
