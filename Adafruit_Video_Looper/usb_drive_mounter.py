# Copyright 2015 Adafruit Industries.
# Author: Tony DiCola
# License: GNU GPLv2, see LICENSE.txt
import time, os, glob, subprocess, pyudev, logging

class USBDriveMounter:
    """Service for automatically mounting attached USB drives."""

    def __init__(self, root='/mnt/usbdrive', readonly=True, umountFunction = None, mountFunction = None):
        """Create an instance of the USB drive mounter service.  Root is an
        optional parameter which specifies the location and file name prefix for
        mounted drives (a number will be appended to each mounted drive file
        name).  Readonly is a boolean that indicates if the drives should be
        mounted as read-only or not (default false, writable).
        umountFunction is called before unmounting
        mountFunction is called after mounting
        """
        self._root = root
        if self._root.endswith(os.path.sep):
            self._root = self._root[:-1]
        self._readonly = readonly
        self._context = pyudev.Context()
        self.umountFunction = umountFunction
        self.mountFunction = mountFunction

        """Initialize monitoring of USB drive changes."""
        self._monitor = pyudev.Monitor.from_netlink(self._context)
        self._monitor.filter_by('block', 'partition')
        self._observer = pyudev.MonitorObserver(self._monitor, self._monitor_mount)

    def remove_all(self):
        """Unmount and remove mount points for all mounted drives."""
        if self.umountFunction is not None: self.umountFunction()
        logging.debug("unmounting all drives")
        for path in glob.glob(self._root + os.path.sep + '*'):
            logging.debug("unmounting {}".format(path))
            subprocess.call(['umount', '-l', path])
            subprocess.call(['rm', '-r', path])

    def _monitor_mount(self, action, device):
        if device is not None and device['ID_BUS'] == 'usb':
            self.remove_all()
            # Mount each drive under the mount root.
            self.mount_all()


    def mount_all(self):
        """Mount all attached USB drives. """
        for i, node in enumerate(self._nodes()):
            path = self._root + os.path.sep + str(i)
            logging.debug("mounting node {} to {}".format(node, path))
            subprocess.call(['mkdir', '-p', path])
            mount = ['mount']
            if self._readonly:
                mount.append('-r')
            mount.extend([node, path])
            subprocess.check_call(mount)
        if self.mountFunction is not None: self.mountFunction()

    # Enumerate USB drive partitions by path like /dev/sda1, etc.
    def _nodes(self):
        return [x.device_node for x in self._context.list_devices(subsystem='block', DEVTYPE='partition')
                 if 'ID_BUS' in x and x['ID_BUS'] == 'usb']

    def has_nodes(self):
        return self._nodes != []

    def start_monitor(self):
        self.mount_all()
        self._observer.start()

    def stop_monitor(self):
        self.remove_all()
        self._observer.stop()
