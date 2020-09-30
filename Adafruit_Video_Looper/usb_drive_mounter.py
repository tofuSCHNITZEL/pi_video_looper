# Copyright 2015 Adafruit Industries.
# Author: Tony DiCola
# License: GNU GPLv2, see LICENSE.txt
import time, os, glob, subprocess, pyudev, logging

class USBDriveMounter:
    """Service for automatically mounting attached USB drives."""

    def __init__(self, root='/mnt/usbdrive', readonly=True, mountFunction = None, umountFunction = None):
        """Create an instance of the USB drive mounter service.  Root is an
        optional parameter which specifies the location and file name prefix for
        mounted drives (a number will be appended to each mounted drive file
        name).  Readonly is a boolean that indicates if the drives should be
        mounted as read-only or not (default false, writable).
        umountFunction is called before unmounting
        mountFunction is called after mounting
        """
        self._mountroot = root.rstrip(os.path.sep)
        self._readonly = readonly
        self._context = pyudev.Context()
        self.umountFunction = umountFunction
        self.mountFunction = mountFunction
        self._mounts = {}

        """Initialize monitoring of USB drive changes."""
        self._monitor = pyudev.Monitor.from_netlink(self._context)
        self._monitor.filter_by('block', 'partition')
        self._observer = pyudev.MonitorObserver(self._monitor, self._monitor_mount, name="USBDriveMounter")

    def remove_all(self):
        """Unmount and remove mount points for all mounted drives."""
        if self.umountFunction is not None: self.umountFunction()
        logging.debug("unmounting all drives")
        for device in list(self._mounts):
            self._unmount(device)

    def _monitor_mount(self, action, device):
        if device is not None and device['ID_BUS'] == 'usb' and action == 'add':
            self._mount(device.device_node)
        elif device is not None and device['ID_BUS'] == 'usb' and action == 'remove':
            self._unmount(device.device_node)

    def _mount(self, device):
        """mounts given device"""
        mountIndex = len(self._mounts)
        mountpath = self._mountroot + os.path.sep + str(mountIndex)
        logging.debug("mounting device {} to {}".format(device, mountpath))
        subprocess.run(['mkdir', '-p', mountpath])
        mount = ['mount']
        if self._readonly:
            mount.append('-r')
        mount.extend([device, mountpath])
        subprocess.run(mount, check=True)
        self._mounts[device] = mountpath
        if self.mountFunction is not None: self.mountFunction(mountpath)
        return mountpath

    def _unmount(self, device):
        if device in self._mounts.keys():
            mountpath = self._mounts[device]
            logging.debug("unmounting {} from {}".format(device, mountpath))
            if subprocess.run(['umount', '-l', mountpath]).returncode == 0:
                subprocess.run(['rm', '-r', mountpath])
            del self._mounts[device]


    def _mount_all(self):
        """Mount all attached USB drives. """
        for node in self._nodes():
            self._mount(node)

    # Enumerate USB drive partitions by path like /dev/sda1, etc.
    def _nodes(self):
        return [x.device_node for x in self._context.list_devices(subsystem='block', DEVTYPE='partition')
                 if 'ID_BUS' in x and x['ID_BUS'] == 'usb']

    def has_nodes(self):
        return self._nodes != []

    def start_monitor(self):
        self.remove_all()
        self._mount_all()
        self._observer.start()

    def stop_monitor(self):
        self.remove_all()
        self._observer.stop()
