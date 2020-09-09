from threading import Thread

class PlayerThread(Thread):

    def __init__(self):
        super().__init__()

    def run(self):
        print("player")