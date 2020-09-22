# Copyright 2019 bitconnect
# Author: Tobias Perschon
# License: GNU GPLv2, see LICENSE.txt
import glob
import os
import shutil
import re
import pygame
import time


class FileTransfer(object):

    def __init__(self, config, screen):
        self._config = config
        self._screen = screen
        self._load_config(config)
        self._pygame_init(config)

        if not os.path.exists(self._target_path):
            os.makedirs(self._target_path)

    def _pygame_init(self, config):
        self._bgcolor = (52,52,52)
        self._fgcolor = (149,193,26)
        self._bordercolor = (255,255,255)
        self._fontcolor = (255,255,255)
        self._font = pygame.font.Font(None, 40)

        #positions and sizes:
        self.screenwidth = pygame.display.Info().current_w
        self.screenheight = pygame.display.Info().current_h
        self.pwidth=0.8*self.screenwidth
        self.pheight=0.05*self.screenheight
        self.borderthickness = 2

        #create rects:
        self.borderrect   =  pygame.Rect((self.screenwidth / 2) - (self.pwidth / 2),
                                         (self.screenheight / 2) - (self.pheight / 2),
                                         self.pwidth,
                                         self.pheight)


    def _load_config(self, config):
        self._mount_path = config.get('usb_drive', 'mount_path')
        self._target_path = config.get('directory', 'path')
        self._copy_mode = config.get('copymode', 'mode')
        self._copyloader = config.getboolean('copymode', 'copyloader')
        self._password = config.get('copymode', 'password')

        #needs to be changed to a more generic approach to support other players
        self._extensions = '|'.join(config.get(config.get('video_looper', 'video_player'), 'extensions') \
                                 .translate(str.maketrans('','', ' \t\r\n.')) \
                                 .split(','))

    #this is called from the outside
    def copy_files(self, sourcepaths):
        self._clear_screen()

        copy_mode = self._copy_mode
        copy_mode_info = "(from config)"
        for path in sourcepaths:
            if not os.path.exists(path) or not os.path.isdir(path):
                continue

            ##sanitycheck for source = target
            #if  in path:
            #    self._draw_info_text("source {} and target {} are the same".format(path,self._target_path))
            #    time.sleep(5)
            #    self._clear_screen()
            #    continue

            #check password
            if not self._password == "":
                if not self._check_file_exists('{0}/{1}'.format(path.rstrip('/'), self._password)):
                    continue

            #override copymode?
            if self._check_file_exists('{0}/{1}'.format(path.rstrip('/'), 'replace')):
                copy_mode = "replace"
                copy_mode_info = "(overridden)"
            if self._check_file_exists('{0}/{1}'.format(path.rstrip('/'), 'add')):
                copy_mode = "add"
                copy_mode_info = "(overridden)"
            if self._check_file_exists('{0}/{1}'.format(path.rstrip('/'), 'replace')) \
                    and self._check_file_exists('{0}/{1}'.format(path.rstrip('/'), 'add')):
                copy_mode = self._copy_mode
                copy_mode_info = "(from config)"

            #inform about copymode
            self._draw_info_text("Mode: " + copy_mode + " " + copy_mode_info)

            if copy_mode == "replace":
                # iterate over target path for deleting:
                for x in os.listdir(self._target_path):
                    if x[0] is not '.' and re.search('\.{0}$'.format(self._extensions), x, flags=re.IGNORECASE):
                        os.remove('{0}/{1}'.format(self._target_path.rstrip('/'), x))

            # iterate over source path for copying:
            for x in os.listdir(path):
                if x[0] is not '.' and re.search('\.{0}$'.format(self._extensions), x, flags=re.IGNORECASE):
                    #copy file
                    self._copy_with_progress('{0}/{1}'.format(path.rstrip('/'), x), '{0}/{1}'.format(self._target_path.rstrip('/'), x))

            #copy loader image
            if self._copyloader:
                loader_file_path = '{0}/{1}'.format(path.rstrip('/'), 'loader.png')
                if os.path.exists(loader_file_path):
                    self._clear_screen()
                    self._draw_info_text("Copying splashscreen file...")
                    time.sleep(2)
                    self._copy_with_progress(loader_file_path,'/home/pi/loader.png')
                    
    def _draw_copy_progress(self, copied, total):
        perc = 100 * copied / total
        assert (isinstance(perc, float))
        assert (0. <= perc <= 100.)

        progressrect =  pygame.Rect((self.screenwidth / 2) - (self.pwidth / 2) + self.borderthickness,
                                                                (self.screenheight / 2) - (self.pheight / 2) + self.borderthickness,
                                                                (self.pwidth-(2*self.borderthickness))*(perc/100),
                                                                self.pheight - (2*self.borderthickness))


        #border
        pygame.draw.rect(self._screen, self._bordercolor, self.borderrect, self.borderthickness)
        #progress
        pygame.draw.rect(self._screen, self._fgcolor, progressrect)
        #progress_text
        self._draw_progress_text(str(int(round(perc)))+"%")

        pygame.display.update(self.borderrect)

    def _draw_info_text(self, message):
        label1 = self._font.render(message, True, self._fontcolor, self._bgcolor)
        l1w, l1h = label1.get_size()
        self._screen.blit(label1, (self.screenwidth / 2 - l1w / 2, self.screenheight / 2 - l1h - self.pheight/2 - 3*self.borderthickness))
        pygame.display.update()

    def _draw_progress_text(self, progress):
        label1 = self._font.render(progress, True, self._bgcolor, self._fgcolor)
        l1w, l1h = label1.get_size()
        self._screen.blit(label1, (self.screenwidth / 2 - l1w / 2, self.screenheight / 2 - l1h / 2 + self.borderthickness))

    def _clear_screen(self, full=True):
        if full:
            self._screen.fill(self._bgcolor)
            pygame.display.update()
        else:
            self._screen.fill(self._bgcolor,self.borderrect)
            pygame.display.update(self.borderrect)

    #checks for file without and with any extension
    def _check_file_exists(self,file):
        return (glob.glob(file + ".*") + glob.glob(file)) != []

    def _copyfile(self, src, dst, *, follow_symlinks=True):
        """Copy data from src to dst.

        If follow_symlinks is not set and src is a symbolic link, a new
        symlink will be created instead of copying the file it points to.

        """
        if shutil._samefile(src, dst):
            raise shutil.SameFileError("{!r} and {!r} are the same file".format(src, dst))

        for fn in [src, dst]:
            try:
                st = os.stat(fn)
            except OSError:
                # File most likely does not exist
                pass
            else:
                # XXX What about other special files? (sockets, devices...)
                if shutil.stat.S_ISFIFO(st.st_mode):
                    raise shutil.SpecialFileError("`%s` is a named pipe" % fn)

        if not follow_symlinks and os.path.islink(src):
            os.symlink(os.readlink(src), dst)
        else:
            size = os.stat(src).st_size
            with open(src, 'rb') as fsrc:
                with open(dst, 'wb') as fdst:
                    self._copyfileobj(fsrc, fdst, callback=self._draw_copy_progress, total=size)
        return dst

    def _copyfileobj(self, fsrc, fdst, callback, total, length=16 * 1024):
        copied = 0
        while True:
            buf = fsrc.read(length)
            if not buf:
                break
            fdst.write(buf)
            copied += len(buf)
            callback(copied, total=total)

    def _copy_with_progress(self, src, dst, *, follow_symlinks=True):
        if os.path.isdir(dst):
            dst = os.path.join(dst, os.path.basename(src))

        # clear screen before copying
        self._clear_screen(False)

        self._copyfile(src, dst, follow_symlinks=follow_symlinks)
        # shutil.copymode(src, dst)
        return dst