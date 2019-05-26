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
abi=$(adb shell getprop ro.product.cpu.abi | tr -d '\r')
sdk=$(adb shell getprop ro.build.version.sdk | tr -d '\r')
rel=$(adb shell getprop ro.build.version.release | tr -d '\r')
dev_size=$(adb shell wm size | cut -f3 -d' ')

# PIE is only supported since SDK 16
if (($sdk >= 16)); then
    pie=
else
    pie=-nopie
fi

echo " * Uploading binaries"
tmp_name=adbmirror
tmp_dir=/tmp/$tmp_name/
dev_dir=/data/local/tmp/$tmp_name/

#make local dir
rm -rf $tmp_dir
mkdir $tmp_dir

#minicap
cp bin/minicap/$abi/minicap$pie $tmp_dir

#minicap-shared
if [ -e bin/minicap-shared/android-$rel/$abi/minicap.so ]; then
    cp bin/minicap-shared/android-$rel/$abi/minicap.so $tmp_dir
else
    cp bin/minicap-shared/android-$sdk/$abi/minicap.so $tmp_dir
fi

#minitouch
cp bin/minitouch/$abi/minitouch$pie $tmp_dir

#upload
adb push $tmp_dir $dev_dir
#clear tmp
rm -rf $tmp_dir

if ! adb shell pm list packages | grep jp.co.cyberagent.stf.rotationwatcher > /dev/null; then
    echo " * Installing RotationWatcher.apk"
    adb install bin/RotationWatcher.apk
fi

echo " * Forwarding ports"
adb forward tcp:1313 localabstract:minicap
adb forward tcp:1111 localabstract:minitouch

echo " * Staring GUI"
python gui.py $SIZE $dev_size $dev_dir $QUALITY $FULLSCREEN

echo " * Cleaning up"
adb shell rm -rf $dev_dir

