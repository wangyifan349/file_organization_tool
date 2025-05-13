#!/bin/bash

# 确保所有命令不被中断而终止脚本的执行
set -e

# 更新并升级系统的现有软件包
echo "Updating and upgrading system packages..."
sudo apt update && sudo apt upgrade -y
echo "-----------------------------------"

# 检查并安装最新的稳定内核
echo "Checking and installing the latest stable kernel..."
if ! grep -q '^deb .*-kernel-.*' /etc/apt/sources.list /etc/apt/sources.list.d/*; then
    echo "Enabling kernel repository..."
    sudo add-apt-repository -y ppa:canonical-kernel-team/ppa
fi
sudo apt update
sudo apt install -y linux-generic linux-image-generic linux-headers-generic
echo "Please reboot your system to apply the latest kernel updates."
echo "-----------------------------------"

# 禁用和移除更多的传感器相关服务
echo "Removing more sensor-related services and packages if present..."
PACKAGES_TO_REMOVE=("iio-sensors-proxy" "guvcview" "fwupd" "thermald")
for pkg in "${PACKAGES_TO_REMOVE[@]}"; do
    if dpkg -l | grep -q $pkg; then
        echo "Removing $pkg..."
        sudo apt purge -y $pkg
    else
        echo "$pkg is not installed."
    fi
done
echo "-----------------------------------"

# 禁用自动更新
echo "Disabling automatic updates and unattended upgrades..."
sudo systemctl disable apt-daily.timer
sudo systemctl disable apt-daily-upgrade.timer
echo "Automatic updates and unattended upgrades disabled."
echo "-----------------------------------"

# 禁用错误报告
echo "Disabling error reporting..."
sudo systemctl disable apport.service
if [ -f /etc/default/apport ]; then
    sudo sed -i 's/enabled=1/enabled=0/' /etc/default/apport
    echo "Error reporting is disabled."
else
    echo "The apport configuration file was not found."
fi
echo "-----------------------------------"

# 安装 GNOME Tweak Tool，用于字体大小和 UI 自定义
echo "Installing GNOME Tweak Tool for font size and UI customization..."
sudo apt install -y gnome-tweak-tool
echo "You can adjust font size and other UI settings in GNOME Tweaks."
echo "-----------------------------------"

# 安装 GNOME System Monitor，用于监视系统进程
echo "Installing GNOME System Monitor..."
sudo apt install -y gnome-system-monitor
echo "You can monitor system processes using GNOME System Monitor."
echo "-----------------------------------"

# 安装硬件信息查看工具（如：硬信息）
echo "Installing Hardinfo for system information..."
sudo apt install -y hardinfo
echo "Use Hardinfo for detailed hardware information analysis."
echo "-----------------------------------"
apt install -y wget curl git build-essential vim nano net-tools htop unzip zip software-properties-common apt-transport-https ca-certificates lsb-release gnupg gnupg2 gnupg-agent dirmngr gpgv gpgsm python3-pip python3-venv tmux screen rsync ufw tree jq bc






# 总结安装
echo "Setup completed. Please review system changes and restart for kernel updates."




# 禁用交换分区
echo "Disabling swap..."
sudo swapoff -a
echo "Swap disabled temporarily."

# 修改 /etc/fstab 文件以永久禁用交换
echo "Updating /etc/fstab to disable swap permanently..."
sudo sed -i '/ swap / s/^\(.*\)$/#\1/g' /etc/fstab
echo "/etc/fstab updated to disable swap."

# 设置加密的 DNS 配置
echo "Configuring DNS over TLS..."
RESOLVED_CONF="/etc/systemd/resolved.conf"

# 如果 resolved.conf 不存在，创建一个新的
if [ ! -f "$RESOLVED_CONF" ]; then
    sudo touch "$RESOLVED_CONF"
fi

# 写入或更新 DNS 配置
sudo bash -c "cat > $RESOLVED_CONF" <<EOL
[Resolve]
DNS=1.1.1.1 1.0.0.1         # Cloudflare DNS
DNSOverTLS=yes              # Enable DNS over TLS
FallbackDNS=9.9.9.9 8.8.8.8 # Quad9 and Google DNS as fallback
EOL

echo "DNS over TLS configured with Cloudflare, Quad9, and Google DNS."

# 重启 systemd-resolved 服务以应用更改
echo "Restarting systemd-resolved service..."
sudo systemctl restart systemd-resolved
echo "systemd-resolved service restarted."

# 检查 /etc/resolv.conf 是否正确链接到 systemd 的解析器
if [ "$(readlink /etc/resolv.conf)" != "/run/systemd/resolve/stub-resolv.conf" ]; then
    echo "Linking /etc/resolv.conf to /run/systemd/resolve/stub-resolv.conf..."
    sudo rm -f /etc/resolv.conf
    sudo ln -s /run/systemd/resolve/stub-resolv.conf /etc/resolv.conf
    echo "Linked /etc/resolv.conf to systemd's resolver."
fi



# 删除与传感器相关的软件包，禁用传感器功能
echo "Removing sensor-related packages..."
PACKAGES_TO_REMOVE=("iio-sensors-proxy" "fwupd" "thermald")
for pkg in "${PACKAGES_TO_REMOVE[@]}"; do
    if dpkg -l | grep -q $pkg; then
        echo "Removing $pkg..."
        sudo apt purge -y $pkg
    else
        echo "$pkg is not installed."
    fi
done

# 设置系统代理（全局环境代理变量）
echo "Setting system proxy..."
PROXY_HTTP="http://127.0.0.1:10809"
PROXY_HTTPS="http://127.0.0.1:10809"
# 添加代理配置到环境变量文件
{
    echo "export http_proxy=$PROXY_HTTP"
    echo "export https_proxy=$PROXY_HTTPS"
    echo "export HTTP_PROXY=$PROXY_HTTP"
    echo "export HTTPS_PROXY=$PROXY_HTTPS"
} | sudo tee /etc/profile.d/proxy.sh > /dev/null
# 加载代理配置
source /etc/profile.d/proxy.sh
# 为 APT 设置代理
echo "Configuring APT to use proxy..."
APT_CONF="/etc/apt/apt.conf.d/95proxies"
echo "Acquire::http::Proxy \"$PROXY_HTTP\";" | sudo tee "$APT_CONF"
echo "Acquire::https::Proxy \"$PROXY_HTTPS\";" | sudo tee -a "$APT_CONF"
# 设置加密的 DNS 配置
echo "Configuring DNS over TLS..."
RESOLVED_CONF="/etc/systemd/resolved.conf"
sudo bash -c "cat > $RESOLVED_CONF" <<EOL
[Resolve]
DNS=1.1.1.1 1.0.0.1         # Cloudflare DNS
DNSOverTLS=yes              # Enable DNS over TLS
FallbackDNS=9.9.9.9 8.8.8.8 # Quad9 and Google DNS as fallback
EOL

sudo systemctl restart systemd-resolved

# 确保 /etc/resolv.conf 正确链接到 systemd
sudo ln -sf /run/systemd/resolve/stub-resolv.conf /etc/resolv.conf




