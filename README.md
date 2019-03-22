# pi_video_looper

An application to turn your Raspberry Pi into a dedicated looping video playback device.
Can be used in art installations, fairs, theatre, events, infoscreens, advertisment etc...

Easy to use out of the box but also has a lot of settings to make it fit your use case.

If you miss a feature just post an issue here on github.

#### new in v1.2.6
- added ntfs and exfat support for the usb drive

#### new in v1.2.5
 - hello_video now has an internal loop counter, so there will be no gap between each iteration of a video (also no wait_time)
 - wait_time is skipped if the playlist is starting for the first time
 - use generic application name

#### new in v1.2.4
 - hello_video returns with no_hello_video option for install.sh in case building should fail again

#### new in v1.2.3
 - add \_repeat_Nx to any file to have the file repeated N times before playing the next file

#### new in v1.2.2
 - option for wait time between videos
 - added enable.sh

#### new in v1.2.1
 - option for displaying an image instead of a blank screen between videos

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

there is also a setting that controls, if files on the drive should replace the existing files or get added.
this ini setting can be overruled by placing a file named "replace" or "add" on the drive.
the default mode is "replace"

Note: files with the same name always get overwritten

#### notable things:
* you can have one video repeated X times before playing the next by adding _repeat_Nx to the filename of a video ,
where N is a positive number
    * with hello_video there is no gap when a video is repeated but there is a small gap between different videos
    * with omxplayer there will also be a short gap between the repeats
    
* if you have only one video then omxplayer can also loop seamlessly (and wth audio)


#### trouble shooting:
* nothing happening (screen flashes once) when in copymode and new drive is plugged in?
    * check if you have the "password file" on your drive (see copymode explained above)

#### how to install:
sudo ./install.sh