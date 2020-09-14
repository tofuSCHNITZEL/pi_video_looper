from threading import Thread
import importlib

class PlayerThread(Thread):

    def __init__(self, config, ready, commandQueue):
        super().__init__()
        self.ready = ready
        self._config = config
        self._commandQueue = commandQueue

    
    def _load_player(self):
        """Load the configured video player and return an instance of it."""
        module = self._config.get('video_looper', 'video_player')
        return importlib.import_module('.' + module, 'Adafruit_Video_Looper').create_player(self._config)

    def run(self):
        print("player")
        self.ready.set()