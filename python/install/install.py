# install.py
# Version: 1.0.0
# Installs dependences needed for Dancy Pi
# Author: Nazmus Nasir
# Website: https://www.easyprogramming.net

import os
from shutil import copy2


def install_dependencies():
    print("================== Start Installing PIP ==================")
    os.system("sudo apt install python3-pip -y")
    print("================== Completed Installing PIP ==================")

    print("================== Start Updating PIP ==================")
    os.system("sudo pip3 install --upgrade pip")
    print("================== Completed Updating PIP ==================")

    print("================== Start Installing Setuptools and Libatlas ==================")
    os.system("sudo apt install python-setuptools libatlas-base-dev -y")
    print("================== Completed Installing Setuptools and Libatlas ==================")

    print("================== Start Installing Fortran ==================")
    os.system("sudo apt install libatlas3-base libgfortran5 -y")
    print("================== Completed Installing Fortran ==================")

    print("================== Start Installing Numpy, Scipy, PyAudio, PyQtgraph ==================")
    os.system("sudo apt install python-numpy python-scipy python-pyaudio python-pyqtgraph -y")
    os.system("sudo pip3 install numpy scipy==1.4.1 pyaudio pyqtgraph")
    print("================== Completed Installing Numpy, Scipy, PyAudio, PyQtgraph ==================")

    print("================== Start Installing rpi_ws281x ==================")
    os.system("sudo pip3 install rpi_ws281x")
    print("================== Completed Installing rpi_ws281x ==================")


def replace_asound():
    print("================== Copying asound.conf ==================")
    copy2('asound.conf', '/etc/asound.conf')
    print("================== Completed copying to /etc/asound.conf ==================")


def edit_alsa_conf():
    print("================== Creating backup of alsa.conf ==================")
    copy2('/usr/share/alsa/alsa.conf', '/usr/share/alsa/alsa.conf.bak')
    print("================== Completed backup of alsa.conf -> alsa.conf.bak ==================")

    print("================== Replacing text in alsa.conf ==================")
    with open('/usr/share/alsa/alsa.conf', 'r') as file:
        filedata = file.read()
        filedata = filedata.replace("defaults.ctl.card 0", "defaults.ctl.card 1")
        filedata = filedata.replace("defaults.pcm.card 0", "defaults.pcm.card 1")
        filedata = filedata.replace("pcm.front cards.pcm.front", "# pcm.front cards.pcm.front")
        filedata = filedata.replace("pcm.rear cards.pcm.rear", "# pcm.rear cards.pcm.rear")
        filedata = filedata.replace("pcm.center_lfe cards.pcm.center_lfe", "# pcm.center_lfe cards.pcm.center_lfe")
        filedata = filedata.replace("pcm.side cards.pcm.side", "# pcm.side cards.pcm.side")
        filedata = filedata.replace("pcm.surround21 cards.pcm.surround21", "# pcm.surround21 cards.pcm.surround21")
        filedata = filedata.replace("pcm.surround40 cards.pcm.surround40", "# pcm.surround40 cards.pcm.surround40")
        filedata = filedata.replace("pcm.surround41 cards.pcm.surround41", "# pcm.surround41 cards.pcm.surround41")
        filedata = filedata.replace("pcm.surround50 cards.pcm.surround50", "# pcm.surround50 cards.pcm.surround50")
        filedata = filedata.replace("pcm.surround51 cards.pcm.surround51", "# pcm.surround51 cards.pcm.surround51")
        filedata = filedata.replace("pcm.surround71 cards.pcm.surround71", "# pcm.surround71 cards.pcm.surround71")
        filedata = filedata.replace("pcm.iec958 cards.pcm.iec958", "# pcm.iec958 cards.pcm.iec958")
        filedata = filedata.replace("pcm.spdif iec958", "# pcm.spdif iec958")
        filedata = filedata.replace("pcm.hdmi cards.pcm.hdmi", "# pcm.hdmi cards.pcm.hdmi")
        filedata = filedata.replace("pcm.modem cards.pcm.modem", "# pcm.modem cards.pcm.modem")
        filedata = filedata.replace("pcm.phoneline cards.pcm.phoneline", "# pcm.phoneline cards.pcm.phoneline")
    with open('/usr/share/alsa/alsa.conf', 'w') as file:
        file.write(filedata)

    print("================== Completed replacing text in alsa.conf ==================")


install_dependencies()
replace_asound()
edit_alsa_conf()
