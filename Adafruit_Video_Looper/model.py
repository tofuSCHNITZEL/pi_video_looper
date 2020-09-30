# Copyright 2015 Adafruit Industries.
# Author: Tony DiCola
# License: GNU GPLv2, see LICENSE.txt
import random, logging
from typing import Optional

random.seed()

class Movie:
    """Representation of a movie"""

    def __init__(self, filename: str, title: Optional[str] = None, repeats: int = 1):
        """Create a playlist from the provided list of movies."""
        self.filename = filename
        self.title = title
        self.repeats = int(repeats)
        self.playcount = 1

    def was_played(self):
        self.playcount += 1

    def clear_playcount(self):
        self.playcount = 1

    def is_done(self):
        return self.playcount > self.repeats

    def __lt__(self, other):
        return self.filename < other.filename

    def __eq__(self, other):
        return self.filename == other.filename

    def __str__(self):
        return "{} ({})".format(self.filename, self.title) if self.title else self.filename

    def __repr__(self):
        return repr((self.filename, self.title, self.repeats))

class Playlist:
    """Representation of a playlist of movies."""

    def __init__(self, movies):
        """Create a playlist from the provided list of movies."""
        self._movies = movies
        self._index = None
        self._skip = False

    def get_next(self, is_random = False) -> Movie:
        """Get the next movie in the playlist. Will loop to start of playlist
        after reaching end.
        """
        # Check if no movies are in the playlist and return nothing.
        if len(self) == 0:
            return None

        # Start Random movie
        if is_random:
            self._index = random.randrange(0, len(self))
        elif not self._skip:
            # Start at the first movie and increment through them in order.
            if self._index is None:
                self._index = 0
            elif self._movies[self._index].is_done():
                #check if movie has played often enough^
                self._movies[self._index].clear_playcount()
                self._index += 1
            # Wrap around to the start after finishing.
            if self._index >= len(self):
                self._index = 0
        
        self._skip = False
        return self._movies[self._index]
    
    def skip_current(self):
        self._movies[self._index].playcount = 0 #seems kinda hacky to me....
        self._index += 1
        if self._index >= len(self):
            self._index = 0
        self._skip = True
        
    def __len__(self):
        return len(self._movies)

    def __str__(self):
        info = "Playlist ({}): ".format(len(self))
        for movie in self._movies:
            info = info + str(movie) + " "
        return info

class ControlTokenFactory:
    """ three types of tokens """
    """ player, filereader, global """
    tokenTypes = ["player", "filereader", "global", "display"]

    def createToken(self, tokentype, cmd):
        """Returns Token type"""
        if tokentype not in self.tokenTypes:
            return False
        targetclass = tokentype.capitalize()+"Token"
        return globals()[targetclass](cmd)

class ControlToken():
    def __init__(self, cmd):
        self.cmd = cmd

    def getCmd(self):
        return self.cmd

    def __str__(self):
        return "Type: "+str(self.__class__)+" cmd: "+self.cmd


class PlayerToken(ControlToken):
    cmds = ["play", "pause", "stop"]
    def setCmd(self, cmd):
        if cmd in self.cmds:
            self.cmd = cmd

class DisplayToken(ControlToken):
    cmds = ["idle"]
    def setCmd(self, cmd):
        if cmd in self.cmds:
            self.cmd = cmd
#class FilereaderToken(ControlToken):
#    cmds = ["reload"]
#    def setCmd(self, cmd):
#        if cmd in self.cmds:
#            self.cmd = cmd

class GlobalToken(ControlToken):
    cmds = ["exit", "reload", "debug"]
    def setCmd(self, cmd):
        if cmd in self.cmds:
            self.cmd = cmd