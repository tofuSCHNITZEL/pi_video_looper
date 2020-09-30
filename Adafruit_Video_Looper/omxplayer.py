# Copyright 2015 Adafruit Industries.
# Author: Tony DiCola
# License: GNU GPLv2, see LICENSE.txt
import os
import shutil
import subprocess
import tempfile
import time

from .alsa_config import parse_hw_device

class OMXPlayer:

    def __init__(self, config):
        """Create an instance of a video player that runs omxplayer in the
        background.
        """
        self._process = None
        self._temp_directory = None
        self._load_config(config)

    def __del__(self):
        if self._temp_directory:
            shutil.rmtree(self._temp_directory)

    def _get_temp_directory(self):
        if not self._temp_directory:
            self._temp_directory = tempfile.mkdtemp()
        return self._temp_directory

    def _load_config(self, config):
        self._extensions = config.get('omxplayer', 'extensions') \
                                 .translate(str.maketrans('', '', ' \t\r\n.')) \
                                 .split(',')
        self._extra_args = config.get('omxplayer', 'extra_args').split()
        self._sound = config.get('omxplayer', 'sound').lower()
        assert self._sound in ('hdmi', 'local', 'both', 'alsa'), 'Unknown omxplayer sound configuration value: {0} Expected hdmi, local, both or alsa.'.format(self._sound)
        self._alsa_hw_device = parse_hw_device(config.get('alsa', 'hw_device'))
        if self._alsa_hw_device != None and self._sound == 'alsa':
            self._sound = 'alsa:hw:{},{}'.format(self._alsa_hw_device[0], self._alsa_hw_device[1])
        self._show_titles = config.getboolean('omxplayer', 'show_titles')
        if self._show_titles:
            title_duration = config.getint('omxplayer', 'title_duration')
            if title_duration >= 0:
                m, s = divmod(title_duration, 60)
                h, m = divmod(m, 60)
                self._subtitle_header = '00:00:00,00 --> {:d}:{:02d}:{:02d},00\n'.format(h, m, s)
            else:
                self._subtitle_header = '00:00:00,00 --> 99:59:59,00\n'

    def supported_extensions(self):
        """Return list of supported file extensions."""
        return self._extensions

    def play(self, movie, loop=None, vol=0):
        """Play the provided movie file, optionally looping it repeatedly."""
        self.stop(3)  # Up to 3 second delay to let the old player stop.
        # Assemble list of arguments.
        args = ['omxplayer']
        args.extend(['-o', self._sound])  # Add sound arguments.
        args.extend(self._extra_args)     # Add extra arguments from config.
        if vol is not 0:
            args.extend(['--vol', str(vol)])
        if loop is None:
            loop = movie.repeats
        if loop <= -1:
            args.append('--loop')  # Add loop parameter if necessary.
        if self._show_titles and movie.title:
            srt_path = os.path.join(self._get_temp_directory(), 'video_looper.srt')
            with open(srt_path, 'w') as f:
                f.write(self._subtitle_header)
                f.write(movie.title)
            args.extend(['--subtitles', srt_path])
        args.append(movie.filename)       # Add movie file path.
        # Run omxplayer process and direct standard output to /dev/null.
        #self._process = subprocess.Popen(args,
        #                                 stdout=open(os.devnull, 'wb'),
        #                                 close_fds=True)
        return subprocess.run(args, stdout=open(os.devnull, 'wb'),
                                         close_fds=True)

    def stop(self, block_timeout_sec=0):
        """Stop the video player."""
        subprocess.call(['pkill', '-9', 'omxplayer'])

    @staticmethod
    def can_loop_count():
        return False


def create_player(config):
    """Create new video player based on omxplayer."""
    return OMXPlayer(config)
