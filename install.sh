#!/bin/sh

# Error out if anything fails.
set -e

# Make sure script is run as root.
if [ "$(id -u)" != "0" ]; then
  echo "Must be run as root with sudo! Try: sudo ./install.sh"
  exit 1
fi


echo "Installing dependencies..."
echo "=========================="
apt update && apt -y install python3 python3-pip python3-pygame supervisor omxplayer

echo "Installing video_looper program..."
echo "=================================="
mkdir -p /mnt/usbdrive0 # This is very important if you put your system in readonly after
pip3 install setuptools
python3 setup.py install --force
cp ./assets/video_looper.ini /boot/video_looper.ini

echo "Configuring video_looper to run on start..."
echo "==========================================="
cp ./assets/video_looper.conf /etc/supervisor/conf.d/
service supervisor restart

echo "Finished!"