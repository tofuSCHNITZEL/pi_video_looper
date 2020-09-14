# Copyright 2015 Adafruit Industries.
# Author: Tony DiCola
# License: GNU GPLv2, see LICENSE.txt
import random
from typing import Optional

random.seed()

class Movie:
    """Representation of a movie"""

    def __init__(self, filename: str, title: Optional[str] = None, repeats: int = 1):
        """Create a playlist from the provided list of movies."""
        self.filename = filename
        self.title = title
        self.repeats = int(repeats)
        self.playcount = 0

    def was_played(self):
        if self.repeats > 1:
            # only count up if its necessary, to prevent memory exhaustion if player runs a long time
            self.playcount += 1
        else:
            self.playcount = 1

    def clear_playcount(self):
        self.playcount = 0

    def __lt__(self, other):
        return self.filename < other.filename

    def __eq__(self, other):
        return self.filename == other.filename

    def __str__(self):
        return "{0} ({1})".format(self.filename, self.title) if self.title else self.filename

    def __repr__(self):
        return repr((self.filename, self.title, self.repeats))

class Playlist:
    """Representation of a playlist of movies."""

    def __init__(self, movies):
        """Create a playlist from the provided list of movies."""
        self._movies = movies
        self._index = None

    def get_next(self, is_random) -> Movie:
        """Get the next movie in the playlist. Will loop to start of playlist
        after reaching end.
        """
        # Check if no movies are in the playlist and return nothing.
        if len(self._movies) == 0:
            return None
        # Start Random movie
        if is_random:
            self._index = random.randrange(0, self.length())
        else:
            # Start at the first movie and increment through them in order.
            if self._index is None:
                self._index = 0
            else:
                self._index += 1
            # Wrap around to the start after finishing.
            if self._index >= self.length():
                self._index = 0

        return self._movies[self._index]

    def length(self):
        """Return the number of movies in the playlist."""
        return len(self._movies)

class ControlTokenFactory:
    """ three types of tokens """
    """ player, filereader, global """
    tokenTypes = ["player", "filereader", "global"]

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

class FilereaderToken(ControlToken):
    cmds = ["refresh"]
    def setCmd(self, cmd):
        if cmd in self.cmds:
            self.cmd = cmd

class GlobalToken(ControlToken):
    cmds = ["exit"]
    def setCmd(self, cmd):
        if cmd in self.cmds:
            self.cmd = cmd