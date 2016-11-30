# adbmirror
Fast screen mirroring via adb

This application is for using your smartphone via remote display.
I am using this to integrate screencast to my car display using OrangePiPC.
It can be used with any linux PC or SBC (RaspberryPi, BabananaPi, *Pi, ...)

I am using binaries from [openstf](https://github.com/openstf)
to stream screen and to emulate touch. Great projet!

## Running
You will need adb, python2.7 and python-pygame to run the application

```
apt install adb python2.7 python-pygame
```

adbmirror contains all necesery files to run the application, no compilation required.

1. Enable **USB debugging** in **Developer options** on your device.
2. Go to the directory and run `./start.sh` script.
3. Approve usb debugging for your computer.
4. Enjoy! 

## How it works
```
start.sh - startup script
 ├check device for SDK, ABI, REL and device resolution
 ├push minicap and minitouch binaries
 ├install RotationWatcher.apk if it is needed
 ├forward ports from device to localhost
 ├start GUI - graphical interface, thread manager
 │ ├spawn capclient thread - read from minicap using socket
 │ │ └run minicap on device via adb
 │ ├spawn touchclient thread - write to minitouch using socket
 │ │ └run minitouch on device via adb
 │ └spawn rotclient thread - read rotation using stdin
 │   └exec RotationWatcher.adb on device via adb
 └Remove binaries from device
```
## Build
There are precompiled binaries adbmirror/bin so this is not necessary. 
 
You can rebuild openstf binaries using script `./build-binaries.sh`

If you want to rebuild **RotationWatcher.apk** follow the instructions inside the submodule

## Common problems
Xiaomi phones might want to have additional permission 
**USB debugging (Security setting)** for 
