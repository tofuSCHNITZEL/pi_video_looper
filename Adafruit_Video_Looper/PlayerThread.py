from threading import Thread
import importlib, logging, time

class PlayerThread(Thread):

    def __init__(self, config, ready, commandQueue):
        super().__init__(name="PlayerThread")
        self.ready = ready
        self._config = config
        self._commandQueue = commandQueue
        self._run = True

    def quit(self):
        logging.debug("quitting player thread")
        self._run = False

    
    def _load_player(self):
        """Load the configured video player and return an instance of it."""
        module = self._config.get('video_looper', 'video_player')
        return importlib.import_module('.' + module, 'Adafruit_Video_Looper').create_player(self._config)

    def run(self):
        print("player")
        self.ready.set()

        while self._run:
            time.sleep(1)

        logging.debug('player thread end')