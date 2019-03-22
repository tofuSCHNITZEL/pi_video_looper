from setuptools import setup, find_packages

setup(name              = 'Bitconnect_Video_Looper',
      version           = '1.2.4',
      author            = 'Tobias Perschon',
      author_email      = 'tp@bitconnect.at',
      description       = 'Based on the Adafruit Video Looper this application turns your Raspberry Pi into a dedicated looping video playback device.',
      license           = 'GNU GPLv2',
      url               = 'https://github.com/tofuSCHNITZEL/pi_video_looper',
      install_requires  = ['pyudev','pygame'],
      packages          = find_packages())
