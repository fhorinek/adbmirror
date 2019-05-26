#!/usr/bin/env bash

FULLSCREEN=1
QUALITY=80
SIZE=767x418

print_usage() {
    echo -e "USAGE: ${0} [OPTIONS]"
    echo -e ""
    echo -e "OPTIONS:"
    echo -e "-h | --help"
    echo -e "\tdisplays this help and exit"
    echo -e ""
    echo -e "--no-fullscreen"
    echo -e "\tdisable starting the pygame window in fullscreen mode"
    echo -e ""
    echo -e "--quality <0-100>"
    echo -e "\twill set the quality of the streamed picture, 100 being the best"
    echo -e "\tdefaults to ${QUALITY}"
    echo -e ""
    echo -e "--size <WIDTHxHEIGHT>"
    echo -e "\tthe size of the pygame window"
    echo -e "\tdefaults to ${SIZE}"
    echo -e ""
}

while [[ $# -gt 0 ]]; do
    case "$1" in
        -h|--help)
            print_usage
            exit 0
            ;;

        --no-fullscreen)
            FULLSCREEN=0
            shift
            ;;

        --quality)
            QUALITY="$2"
            shift
            shift
            ;;

        --size|--resolution)
            SIZE="$2"
            shift
            shift
            ;;

        *)
            shift
            ;;
    esac
done

if ! which adb > /dev/null; then
    echo "Error: adb not found in path!"
    exit
fi

if ! ps aux | grep adb | grep fork-server > /dev/null; then
    echo " * Starting ADB server"
    sudo adb start-server
fi

echo " * Waiting for device"
adb wait-for-device

#Need to have here do done (because gedit syntax highlight :-D)

echo " * Getting device info"
ABI=$(adb shell getprop ro.product.cpu.abi | tr -d '\r')
SDK=$(adb shell getprop ro.build.version.sdk | tr -d '\r')
REL=$(adb shell getprop ro.build.version.release | tr -d '\r')
DEV_SIZE=$(adb shell wm size | cut -f3 -d' ')


# PIE is only supported since SDK 16
if (($SDK >= 16)); then
    PIE=
else
    PIE=-nopie
fi

echo " * Uploading binaries"
TMP_NAME=adbmirror
TMP_DIR=/tmp/$TMP_NAME/
DEV_DIR=/data/local/tmp/$TMP_NAME/

#make local dir
rm -rf $TMP_DIR
mkdir $TMP_DIR

#minicap
cp bin/minicap/$ABI/minicap$PIE $TMP_DIR

#minicap-shared
if [ -e bin/minicap-shared/android-$REL/$ABI/minicap.so ]; then
    cp bin/minicap-shared/android-$REL/$ABI/minicap.so $TMP_DIR
else
    cp bin/minicap-shared/android-$SDK/$ABI/minicap.so $TMP_DIR
fi

#minitouch
cp bin/minitouch/$ABI/minitouch$PIE $TMP_DIR

#upload
adb push $TMP_DIR $DEV_DIR
#clear tmp
rm -rf $TMP_DIR

if ! adb shell pm list packages | grep jp.co.cyberagent.stf.rotationwatcher > /dev/null; then
    echo " * Installing RotationWatcher.apk"
    adb install bin/RotationWatcher.apk
fi

echo " * Forwarding ports"
adb forward tcp:1313 localabstract:minicap
adb forward tcp:1111 localabstract:minitouch

echo " * Staring GUI"
python gui.py $SIZE $DEV_SIZE $DEV_DIR $QUALITY $FULLSCREEN

echo " * Cleaning up"
adb shell rm -rf $DEV_DIR

