#!/usr/bin/env bash

if ! which ndk-build > /dev/null; then
	echo "Error: ndk-build not found in path!"
	exit
fi

if ! which git > /dev/null; then
	echo "Error: git not found in path!"
	exit
fi

echo " * Downloading binaries *"
echo
git submodule init
git submodule update
echo

echo " * Building minicap *"
echo
cd minicap
git submodule init
git submodule update
ndk-build
cd ..
echo

echo " * Building minitouch *"
echo
cd minitouch
git submodule init
git submodule update
ndk-build
cd ..
echo

echo " * Moving binaries *"
rm -rf adbmirror/bin/*
cp -r minicap/libs adbmirror/bin/minicap
cp -r minicap/jni/minicap-shared/aosp/libs adbmirror/bin/minicap-shared
cp -r minitouch/libs adbmirror/bin/minitouch

echo " * Done *"
echo

