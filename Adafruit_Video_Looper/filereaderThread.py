from threading import Thread, Timer, Condition
import importlib
import logging, time, glob
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from .model import ControlTokenFactory, GlobalToken
from .usb_drive_mounter import USBDriveMounter
from .file_transfer import FileTransfer

class FileReaderThread(Thread):

    def __init__(self, config, ready, commandQueue):
        super().__init__(name="FileReaderThread")
        self.ready = ready
        self._config = config
        self._commandQueue = commandQueue
        self._usbMounter = None
        self._run = True
        self._tokenGen = ControlTokenFactory()
        self._searchPaths = []
        self._copyMode = self._config.get('copymode', 'mode')

        if self._config.getboolean('usb_drive', 'auto_mount'):
            logging.debug("creating usb mounter")
            self._usbMounter = USBDriveMounter(self._config.get('usb_drive', 'mount_path'), 
                                               self._config.getboolean('usb_drive', 'readonly'),
                                               self._mountHandler,
                                               self._unschedule_all_watchers)
        
        self._observer = Observer()
        logging.debug("using observer type: "+str(type(self._observer).__name__))
        self._observer_event_handler = Handler(self._processPaths)

    def quit(self):
        logging.debug("quitting filereader thread")
        self._unschedule_all_watchers()
        logging.debug("stopping observer")
        self._observer.stop()

    def _processPaths(self):
        logging.debug("processing paths")
        self._commandQueue.put(self._tokenGen.createToken("global", "reload"))
                    
    def get_paths(self):
        return self._searchPaths
    
    def _updateSearchPaths(self):
        self._searchPaths = glob.glob(self._config.get('directory', 'path'))
        logging.debug('searchPaths: {}'.format(self._searchPaths))

    def _unschedule_all_watchers(self):
        logging.debug("unschedule watchers")
        self._observer.unschedule_all()

    def _mountHandler(self, mountedPath):
        copyMode = self._config.get('copymode', 'mode')
        if copyMode in ["add", "replace"] and mountedPath != []:
            logging.debug('copyMode is active ({})'.format(copyMode))
            self._unschedule_all_watchers()
            #handle copyprocess
            #todo: sanity check if path is set to same/kind of mountpath then do not copy
            ft = FileTransfer(self._config)
            ft.copy_files([mountedPath]) #pass list with single entry
            logging.debug('copyMode done')
            del ft
            
        self._scheduleObservers()

    def _scheduleObservers(self):
        self._updateSearchPaths()
        for location in self._searchPaths:
            logging.debug("scheduling observer for {}".format(location))
            self._observer.schedule(self._observer_event_handler, location, recursive=True)
        self._processPaths()

    def run(self):
        #genauer splitten zwischen copy mode und nicht copy mode...????
        logging.debug('starting filechange observer')
        self._observer.start()
        if self._usbMounter is not None:
            logging.debug("starting usb mounter")
            self._usbMounter.start_monitor()
            logging.debug("usb mounter started")
            

        logging.debug("scheduling observers")
        self._scheduleObservers()

        self.ready.set()

        #here we block and wait
        self._observer.join() 
        logging.debug("observer stopped")
      
        if self._usbMounter is not None:
            logging.debug("stopping usb mounter")
            self._usbMounter.stop_monitor()
            logging.debug("usb mounter stopped")
        
        logging.debug('filereader thread end')

class Handler(FileSystemEventHandler):
    
    def __init__(self, functiontoCall):
        super().__init__()
        self._functionToCall = functiontoCall
        self._debounceTimer = self._setupTimer()

    def _setupTimer(self):
        return Timer(3.0, self._functionToCall)

    def on_any_event(self, event):
        if event.is_directory or event.event_type not in ['created','modified','deleted']:
            return None

        logging.debug("filechange event received; resetting timer")
        self._debounceTimer.cancel()
        self._debounceTimer = self._setupTimer()        
        self._debounceTimer.start()
        
        

            