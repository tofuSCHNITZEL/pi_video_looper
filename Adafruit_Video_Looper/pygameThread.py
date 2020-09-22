from threading import Thread
import pygame, os, time,sys
import logging
from .model import *

class PygameThread(Thread):

    def __init__(self, config, ready, commandQueue):
        super().__init__(name="PygameThread")
        self.ready = ready
        self._config = config
        self._commandQueue = commandQueue

        self._bgcolor = list(map(int, self._config.get('video_looper', 'bgcolor')
                                             .translate(str.maketrans('','', ','))
                                             .split()))
        self._fgcolor = list(map(int, self._config.get('video_looper', 'fgcolor')
                                             .translate(str.maketrans('','', ','))
                                             .split()))

        
        self._keyboard_control = self._config.getboolean('video_looper', 'keyboard_control')
        self._bgimage = self._load_bgimage()
        self._screen = None
        self._run = True
        self._tokenGen = ControlTokenFactory()

    def quit(self):
        logging.debug("quitting pygame thread")
        pygame.event.post(pygame.event.Event(pygame.QUIT))
    
    def get_screen(self):
        return self._screen

    def blank_screen(self):
        """Render a blank screen filled with the background color."""
        self._screen.fill(self._bgcolor)
        if self._bgimage is not None:
            rect = self._bgimage.get_rect()
            self._screen.blit(self._bgimage, rect)
        pygame.display.update()

    def display_message(self, message):
        ##TODO##self._print(message)
        # Do nothing else if the OSD is turned off.
        #if not self._osd:
        #    return
        ##TODO##
        # Display idle message in center of screen.
        label = self._render_text(message)
        lw, lh = label.get_size()
        sw, sh = self._screen.get_size()
        self._screen.fill(self._bgcolor)
        self._screen.blit(label, (int(sw/2-lw/2), int(sh/2-lh/2)))
        pygame.display.update()

    def _render_text(self, message, font=None):
        """Draw the provided message and return as pygame surface of it rendered
        with the configured foreground and background color.
        """
        # Default to small font if not provided.
        if font is None:
            font = self._small_font
        return font.render(message, True, self._fgcolor, self._bgcolor)

    def _load_bgimage(self):
        """Load the configured background image and return an instance of it."""
        image = None
        if self._config.has_option('video_looper', 'bgimage'):
            imagepath = self._config.get('video_looper', 'bgimage')
            if imagepath != "" and os.path.isfile(imagepath):
                ##TODO##self._print('Using ' + str(imagepath) + ' as a background')
                image = pygame.image.load(imagepath)
                image = pygame.transform.scale(image, self._size)
        return image

    def animate_countdown(self, amount):
        """Print text with the number of loaded movies and a quick countdown
        message if the on screen display is enabled.
        """
        # Print message to console with number of movies in playlist.
        message = 'Found {0} movie{1}.'.format(amount, 
            's' if amount >= 2 else '')
        #self._print(message)
        # Do nothing else if the OSD is turned off.
        #if not self._osd:
        #    return
        # Draw message with number of movies loaded and animate countdown.
        # First render text that doesn't change and get static dimensions.
        label1 = self._render_text(message + ' Starting playback in:')
        l1w, l1h = label1.get_size()
        sw, sh = self._screen.get_size()
        for i in range(self._config.getint('video_looper', 'countdown_time'), 0, -1):
            # Each iteration of the countdown rendering changing text.
            label2 = self._render_text(str(i), self._big_font)
            l2w, l2h = label2.get_size()
            # Clear screen and draw text with line1 above line2 and all
            # centered horizontally and vertically.
            self._screen.fill(self._bgcolor)
            self._screen.blit(label1, (int(sw/2-l1w/2), int(sh/2-l2h/2-l1h)))
            self._screen.blit(label2, (int(sw/2-l2w/2), int(sh/2-l2h/2)))
            pygame.display.update()
            # Pause for a second between each frame.
            time.sleep(1)

    def display_idle_message(self, message):
        """Print idle message from file reader."""
        # Print message to console.
        #self._print(message)
        # Do nothing else if the OSD is turned off.
        #if not self._osd:
        #    return
        # Display idle message in center of screen.
        label = self._render_text(message)
        lw, lh = label.get_size()
        sw, sh = self._screen.get_size()
        self._screen.fill(self._bgcolor)
        self._screen.blit(label, (int(sw/2-lw/2), int(sh/2-lh/2)))
        # If keyboard control is enabled, display message about it
        #if self._keyboard_control:
        #    label2 = self.render_text('press ESC to quit')
        #    l2w, l2h = label2.get_size()
        #    self._screen.blit(label2, (sw/2-l2w/2, sh/2-l2h/2+lh))
        pygame.display.update()

    def run(self):
        pygame.display.init()
        pygame.font.init()
        pygame.mouse.set_visible(False)
        self._screen = pygame.display.set_mode((0,0), pygame.FULLSCREEN | pygame.NOFRAME)
        self._size = (pygame.display.Info().current_w, pygame.display.Info().current_h)
        self._small_font = pygame.font.Font(None, 50)
        self._big_font   = pygame.font.Font(None, 250)

        self.blank_screen()
        self.ready.set()

        while self._run:
            event = pygame.event.wait()
            if self._keyboard_control and event.type == pygame.KEYDOWN:
                # If pressed key is ESC quit program
                if event.key == pygame.K_ESCAPE:
                    logging.info("ESC was pressed. quitting...")
                    self._commandQueue.put(self._tokenGen.createToken("global", "exit"))
                if event.key == pygame.K_k:
                    logging.info("k was pressed. skipping...")
                    self._commandQueue.put(self._tokenGen.createToken("player", "skip"))
                if event.key == pygame.K_s:
                    logging.info("s was pressed. stopping...")    
                    self._commandQueue.put(self._tokenGen.createToken("player", "stop"))
            if event.type == pygame.QUIT:
                self._run = False

        pygame.display.quit()
        pygame.font.quit()
        logging.debug('pygame thread end')
