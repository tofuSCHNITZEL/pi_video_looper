from threading import Thread
import importlib, logging, time, pygame
from .model import ControlTokenFactory, DisplayToken

class PlayerThread(Thread):

    def __init__(self, config, ready, commandQueue):
        super().__init__(name="PlayerThread")
        self.ready = ready
        self._config = config
        self._commandQueue = commandQueue
        self._run = True
        logging.debug("player: {} initialising".format(self._config.get('video_looper', 'video_player')))
        self._player = self._load_player()
        self._playlist = None
        self._tokenGen = ControlTokenFactory()
        self._skipmode = self._config.get('video_looper', 'skip')
        if self._skipmode not in ('whole','iteration'): self._skipmode = "whole"

    def quit(self):
        logging.debug("quitting player thread")
        self._run = False
        self._player.stop()

    
    def _load_player(self):
        """Load the configured video player and return an instance of it."""
        module = self._config.get('video_looper', 'video_player')
        return importlib.import_module('.' + module, 'Adafruit_Video_Looper').create_player(self._config)

    def playPlaylist(self, playlist):
        self._playlist = playlist
        #does not necessarily has to stop/restart player - todo: think about it

    def skip(self):
        logging.debug("skipping player mode: {}".format(self._skipmode))
        if self._skipmode == 'whole':
            self._playlist.skip_current()
        self._player.stop()

    def run(self):
        logging.debug("starting player")
        self.ready.set()

        while self._run:
            while self._playlist == None:
                #todo if osd is on.... 
                self._commandQueue.put(self._tokenGen.createToken("display", "idle"))
                time.sleep(1)
            #clear screen...? not after every movie? idk
            #todo: maybe use omxwrapper to send next movie?? maybe in extra omx player class
            movie = self._playlist.get_next()
            #generating infotext
            if self._player.can_loop_count():
                infotext = '{0} time{1} (player counts loops)'.format(movie.repeats, "s" if movie.repeats>1 else "")
            else:
                infotext = '{0}/{1}'.format(movie.playcount, movie.repeats)
            if len(self._playlist)==1:
                infotext = '(endless loop)'
            # Start playing the first available movie.
            logging.info('Playing movie: {0} {1}'.format(movie, infotext))
            # todo: maybe clear screen to black so that background (image/color) is not visible for videos with a resolution that is < screen resolution
            self._player.play(movie, loop=-1 if len(self._playlist)==1 else None, vol = 0)
            logging.debug("playing finished")
            movie.was_played()
            

        logging.debug('player thread end') 