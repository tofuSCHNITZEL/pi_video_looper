# Copyright 2015 Adafruit Industries.
# Author: Tony DiCola
# License: GNU GPLv2, see LICENSE.txt

import configparser
import importlib
import os
import re
import subprocess
import sys
import signal
import time
import pygame
import threading
import logging
import traceback

from multiprocessing import Queue

from .alsa_config import parse_hw_device
from .model import *
from .playlist_builders import build_playlist_m3u
from .pygameThread import PygameThread
from .playerThread import PlayerThread
from .filereaderThread import FileReaderThread

# Basic video looper architecure:
#
# - VideoLooper class contains all the main logic for running the looper program.
#
# - Almost all state is configured in a .ini config file which is required for
#   loading and using the VideoLooper class.
#
# - VideoLooper has loose coupling with file reader and video player classes that
#   are used to find movie files and play videos respectively.  The configuration
#   defines which file reader and video player module will be loaded.
#
# - A file reader module needs to define at top level create_file_reader function
#   that takes as a parameter a ConfigParser config object.  The function should
#   return an instance of a file reader class.  See usb_drive.py and directory.py
#   for the two provided file readers and their public interface.
#
# - Similarly a video player modules needs to define a top level create_player
#   function that takes in configuration.  See omxplayer.py and hello_video.py
#   for the two provided video players and their public interface.
#
# - Future file readers and video players can be provided and referenced in the
#   config to extend the video player use to read from different file sources
#   or use different video players.
class VideoLooper:

    def __init__(self, config_path):
        """Create an instance of the main video looper application class. Must
        pass path to a valid video looper ini configuration file.
        """
        self.commandQueue = Queue()
        # Load the configuration.
        self._config = configparser.ConfigParser()
        if len(self._config.read(config_path)) == 0:
            raise RuntimeError('Failed to find configuration file at {0}, is the application properly installed?'.format(config_path))
        # Load other configuration values.
        logging.basicConfig(level=logging.getLevelName(self._config.get('video_looper', 'console_output'))) 
        self._console_output = True
        self._osd = self._config.getboolean('video_looper', 'osd')
        self._is_random = self._config.getboolean('video_looper', 'is_random')
        
        self._tokenGen = ControlTokenFactory()

        # Get seconds for waittime bewteen files from config
        self._wait_time = self._config.getint('video_looper', 'wait_time')

        # Initialize pygame and display a blank screen.
        try:
            pygameReady = threading.Event()
            self._pgT = PygameThread(self._config, pygameReady, self.commandQueue)
            logging.debug("starting pygame thread")
            self._pgT.start()
            logging.debug("waiting for pygame thread warmup")
            pygameReady.wait()
            logging.debug("pygame ready")
        except Exception as e:
            logging.debug(e) 
            self.quit()

        # Initialize player thread
        try:
            playerReady = threading.Event()
            self._plT = PlayerThread(self._config, playerReady, self.commandQueue)
            logging.debug("starting player thread")
            self._plT.start()
            logging.debug("waiting for player thread warump")
            playerReady.wait()
            logging.debug("player ready")
        except Exception as e:
            logging.debug(e) 
            self.quit()

        # Initialize filereader thread
        try:
            filereaderReady = threading.Event()
            self._frT = FileReaderThread(self._config, filereaderReady, self.commandQueue)
            logging.debug("starting filereader thread")
            self._frT.start()
            logging.debug("waiting for filereader thread warump")
            filereaderReady.wait()
            logging.debug("filereader ready")
        except Exception as e:
            logging.debug(e) 
            self.quit()
        
        # Load ALSA hardware configuration.
        self._alsa_hw_device = parse_hw_device(self._config.get('alsa', 'hw_device'))
        self._alsa_hw_vol_control = self._config.get('alsa', 'hw_vol_control')
        self._alsa_hw_vol_file = self._config.get('alsa', 'hw_vol_file')
        # default ALSA hardware volume (volume will not be changed)
        self._alsa_hw_vol = None
        # Load sound volume file name value
        self._sound_vol_file = self._config.get('omxplayer', 'sound_vol_file')
        # default value to 0 millibels (omxplayer)
        self._sound_vol = 0
        # Set other static internal state.
        self._extensions = '|'.join(self._config.get(self._config.get('video_looper', 'video_player'), 'extensions') \
                                 .translate(str.maketrans('','', ' \t\r\n.')) \
                                 .split(','))
        #self._extensions = '|'.join(self._player.supported_extensions())

        self._running    = True
        self._playbackStopped = False
        #used for not waiting the first time
        self._firstStart = True


        # start keyboard handler thread:
        # Event handling for key press, if keyboard control is enabled
        #if self._keyboard_control:
        #    self._keyboard_thread = threading.Thread(target=self._handle_keyboard_shortcuts, daemon=True)
        #    self._keyboard_thread.start()

    def _print(self, message):
        """Print message to standard output if console output is enabled."""
        if self._console_output:
            print(message)

    def _is_number(self, s):
        try:
            float(s) 
            return True
        except ValueError:
            return False

    def _build_playlist(self):
        """Try to build a playlist (object) from a playlist (file).
        Falls back to an auto-generated playlist with all files.
        """
        if self._config.has_option('playlist', 'path'):
            playlist_path = self._config.get('playlist', 'path')
            if playlist_path != "":
                if os.path.isabs(playlist_path):
                    if not os.path.isfile(playlist_path):
                        self._print('Playlist path {0} does not exist.'.format(playlist_path))
                        return self._build_playlist_from_path()
                        #raise RuntimeError('Playlist path {0} does not exist.'.format(playlist_path))
                else:
                    paths = self._frT.get_paths()
                    
                    if not paths:
                        return Playlist([])
                    
                    for path in paths:
                        maybe_playlist_path = os.path.join(path, playlist_path)
                        if os.path.isfile(maybe_playlist_path):
                            playlist_path = maybe_playlist_path
                            self._print('Playlist path resolved to {0}.'.format(playlist_path))
                            break
                    else:
                        self._print('Playlist path {0} does not resolve to any file.'.format(playlist_path))
                        return self._build_playlist_from_path()
                        #raise RuntimeError('Playlist path {0} does not resolve to any file.'.format(playlist_path))

                basepath, extension = os.path.splitext(playlist_path)
                if extension == '.m3u' or extension == '.m3u8':
                    return build_playlist_m3u(playlist_path)
                else:
                    self._print('Unrecognized playlist format {0}.'.format(extension))
                    return self._build_playlist_from_path()
                    #raise RuntimeError('Unrecognized playlist format {0}.'.format(extension))
            else:
                return self._build_playlist_from_path()
        else:
            return self._build_playlist_from_path()

    def _build_playlist_from_path(self):
        """Search all the file reader paths for movie files with the provided
        extensions.
        """
        # Get list of paths to search from the file reader.
        paths = self._frT.get_paths()
        # Enumerate all movie files inside those paths.
        movies = []
        for path in paths:
            # Skip paths that don't exist or are files.
            if not os.path.exists(path) or not os.path.isdir(path):
                continue

            for x in os.listdir(path):
                # Ignore hidden files (useful when file loaded on usb key from an OSX computer
                if x[0] != '.' and re.search('\.{0}$'.format(self._extensions), x, flags=re.IGNORECASE):
                    repeatsetting = re.search('_repeat_([0-9]*)x', x, flags=re.IGNORECASE)
                    if (repeatsetting is not None):
                        repeat = repeatsetting.group(1)
                    else:
                        repeat = 1
                    basename, extension = os.path.splitext(x)
                    movies.append(Movie('{0}/{1}'.format(path.rstrip('/'), x), basename, repeat))

            # Get the ALSA hardware volume from the file in the usb key
            if self._alsa_hw_vol_file:
                alsa_hw_vol_file_path = '{0}/{1}'.format(path.rstrip('/'), self._alsa_hw_vol_file)
                if os.path.exists(alsa_hw_vol_file_path):
                    with open(alsa_hw_vol_file_path, 'r') as alsa_hw_vol_file:
                        alsa_hw_vol_string = alsa_hw_vol_file.readline()
                        self._alsa_hw_vol = alsa_hw_vol_string
                    
            # Get the video volume from the file in the usb key
            if self._sound_vol_file:
                sound_vol_file_path = '{0}/{1}'.format(path.rstrip('/'), self._sound_vol_file)
                if os.path.exists(sound_vol_file_path):
                    with open(sound_vol_file_path, 'r') as sound_file:
                        sound_vol_string = sound_file.readline()
                        if self._is_number(sound_vol_string):
                            self._sound_vol = int(float(sound_vol_string))
        # Create a playlist with the sorted list of movies.
        return Playlist(sorted(movies))

    def _prepare_to_run_playlist(self, playlist):
        """Display messages when a new playlist is loaded."""
        # If there are movies to play show a countdown first (if OSD enabled),
        # or if no movies are available show the idle message.
        self._pgT.blank_screen()
        self._firstStart = True
        if len(playlist) > 0:
            self._pgT.animate_countdown(len(playlist))
            self._pgT.blank_screen()
        else:
            self._pgT.display_idle_message()


    def _set_hardware_volume(self):
        if self._alsa_hw_vol != None:
            msg = 'setting hardware volume (device: {}, control: {}, value: {})'
            self._print(msg.format(
                self._alsa_hw_device,
                self._alsa_hw_vol_control,
                self._alsa_hw_vol
            ))
            cmd = ['amixer', '-M']
            if self._alsa_hw_device != None:
                cmd.extend(('-c', str(self._alsa_hw_device[0])))
            cmd.extend(('set', self._alsa_hw_vol_control, '--', self._alsa_hw_vol))
            subprocess.check_call(cmd)

    def run(self):
        while self._running:
            cmd = self.commandQueue.get()
            if(isinstance(cmd, GlobalToken)):
                cmd = cmd.getCmd()
                if cmd == "exit":
                    self._running = False
                elif cmd == "reload":
                    logging.debug("reloading payer, rebuilding playlist with these paths: {} then stopping / starting player".format(self._frT.get_paths()))
                    playlist = self._build_playlist()
                    logging.debug("playlist ({}): {} ".format(len(playlist), playlist))
                    self._plT.playPlaylist(playlist)  
                    ##start playing   
                elif cmd == "debug":
                    logging.debug(playlist)       
            elif(isinstance(cmd, PlayerToken)):
                print("playertoken: "+cmd.getCmd())
                cmd = cmd.getCmd()
                if cmd == "skip":
                    self._plT.skip()
            elif(isinstance(cmd, DisplayToken)):
                print("displaytoken: "+cmd.getCmd())
                cmd = cmd.getCmd()
                if cmd == "idle":
                    print("idle")
                elif cmd == "clear":
                    self._pgT.blank_screen()
                    #self._pgT.display_idle_message("waiting for files")

        ##CLEANUP
        logging.debug("starting cleanup of threads")
        try:
            self._pgT.quit()
            self._plT.quit()
            self._frT.quit()
        except Exception as e:
            logging.debug(e)
        
        self._pgT.join()
        self._plT.join()
        self._frT.join()

    def old_run(self):
        """Main program loop.  Will never return!"""
        # Get playlist of movies to play from file reader.
        playlist = self._build_playlist()
        self._prepare_to_run_playlist(playlist)
        self._set_hardware_volume()
        movie = playlist.get_next(self._is_random)
        # Main loop to play videos in the playlist and listen for file changes.
        while self._running:
            # Load and play a new movie if nothing is playing.
            if not self._player.is_playing() and not self._playbackStopped:
                if movie is not None: #just to avoid errors

                    if movie.playcount >= movie.repeats:
                        movie.clear_playcount()
                        movie = playlist.get_next(self._is_random)
                    elif self._player.can_loop_count() and movie.playcount > 0:
                        movie.clear_playcount()
                        movie = playlist.get_next(self._is_random)

                    movie.was_played()

                    if self._wait_time > 0 and not self._firstStart:
                        self._print('Waiting for: {0} seconds'.format(self._wait_time))
                        time.sleep(self._wait_time)
                    self._firstStart = False

                    #generating infotext
                    if self._player.can_loop_count():
                        infotext = '{0} time{1} (player counts loops)'.format(movie.repeats, "s" if movie.repeats>1 else "")
                    else:
                        infotext = '{0}/{1}'.format(movie.playcount, movie.repeats)
                    if len(playlist)==1:
                        infotext = '(endless loop)'

                    # Start playing the first available movie.
                    self._print('Playing movie: {0} {1}'.format(movie, infotext))
                    # todo: maybe clear screen to black so that background (image/color) is not visible for videos with a resolution that is < screen resolution
                    self._player.play(movie, loop=-1 if len(playlist)==1 else None, vol = self._sound_vol)

            # Check for changes in the file search path (like USB drives added)
            # and rebuild the playlist.
            if self._reader.is_changed() and not self._playbackStopped:
                self._print("reader changed, stopping player")
                self._player.stop(3)  # Up to 3 second delay waiting for old 
                                      # player to stop.
                self._print("player stopped")
                # Rebuild playlist and show countdown again (if OSD enabled).
                playlist = self._build_playlist()
                self._prepare_to_run_playlist(playlist)
                self._set_hardware_volume()
                movie = playlist.get_next(self._is_random)

            # Give the CPU some time to do other tasks. low values increase "responsiveness to changes" and reduce the pause between files
            # but increase CPU usage
            # since keyboard commands are handled in a seperate thread this sleeptime mostly influences the pause between files
                        
            time.sleep(0.002)

    def quit(self):
        """Shut down the program"""
        logging.debug("stopping videolooper")
        self.commandQueue.put(self._tokenGen.createToken("global", "exit"))



    def signal_quit(self, signal, frame):
        """Shut down the program, meant to by called by signal handler."""
        self._print("received signal to quit")
        #self.dumpstacks(signal,frame)
        self.quit()

    def dumpstacks(self, signal, frame):
        print ("dumpstacks")
        id2name = dict([(th.ident, th.name) for th in threading.enumerate()])
        code = []
        for threadId, stack in sys._current_frames().items():
            code.append("\n# Thread: %s(%d)" % (id2name.get(threadId,""), threadId))
            for filename, lineno, name, line in traceback.extract_stack(stack):
                code.append('File: "%s", line %d, in %s' % (filename, lineno, name))
                if line:
                    code.append("  %s" % (line.strip()))
        print ("\n".join(code))

# Main entry point.
if __name__ == '__main__':
    # Default config path to /boot.
    config_path = '/boot/video_looper.ini'
    # Override config path if provided as parameter.
    if len(sys.argv) == 2:
        config_path = sys.argv[1]
    # Create video looper.
    videolooper = VideoLooper(config_path)
    # Configure signal handlers to quit on TERM or INT signal.
    signal.signal(signal.SIGTERM, videolooper.signal_quit)
    signal.signal(signal.SIGINT, videolooper.signal_quit)
    # Run the main loop.
    videolooper.run()
