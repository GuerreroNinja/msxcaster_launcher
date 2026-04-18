# MSX CASTER Launcher
This little python script for Linux launches the program msx-caster. It let's you select the CAS file via dialog, select the profile from a dropdown menu and launch msx-caster. It also saves your previous selections in .config/msxcaster_launcher
INSTALLATION INSTRUCTIONS

You have to build msx-caster from xesco github and python dependencies. For Fedora:

sudo dnf install -y python3-pip python3-qt6 git gcc make cmake xterm konsole

pip install --user PyQt6

git clone https://github.com/xesco/msx-caster.git

cd msx-caster

make

sudo cp cast /usr/bin/
