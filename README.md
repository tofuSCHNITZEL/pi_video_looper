# pi_video_looper
Application to turn your Raspberry Pi into a dedicated looping video playback device.

#### new in v1.2.0:

 - reworked for python3
 - new copymode
 - removed hello_video
 - countdowntime setting
 - keyboard control (quiting the player)
 
#### copymode explained:
when a usb drive with video files is plugged in, they are copied onto the rpi. (with progress bar)

to protect the player from "hostile" drives a file must be present on the drive that has a filename 
as defined in the password setting in the ini file (default: videopi)

there is also a setting that controls if files on the drive should replace the existing files or get added.
this ini setting can be overruled by placing a file named "replace" or "add" on the drive
the default mode is "replace"

Note: files with the same name always get overwritten

#### how to install:
sudo ./install.sh