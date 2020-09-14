from threading import Thread
import importlib

class FileReaderThread(Thread):

    def __init__(self, config, ready, commandQueue):
        super().__init__()
        self.ready = ready
        self._config = config
        self._commandQueue = commandQueue

    def _load_file_reader(self):
        """Load the configured file reader and return an instance of it."""
        module = self._config.get('video_looper', 'file_reader')
        return importlib.import_module('.' + module, 'Adafruit_Video_Looper').create_file_reader(self._config, None)

    def run(self):
        print("FSreader")
        self.ready.set()