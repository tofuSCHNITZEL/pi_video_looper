from setuptools import setup, find_packages
setup(name              = 'Pi_Video_Looper',
      version           = '1.2.5',
      author            = 'Tobias Perschon',
      author_email      = 'tobias@perschon.at',
      description       = 'Based on the Adafruit Video Looper this application turns your Raspberry Pi into a dedicated looping video playback device.',
      license           = 'GNU GPLv2',
      url               = 'https://github.com/tofuSCHNITZEL/pi_video_looper',
      install_requires  = ['pyudev','pygame'],
      packages          = find_packages())
