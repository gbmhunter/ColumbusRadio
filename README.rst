=============
ColumbusRadio
=============

------------------------------------
Repo for the Columbus radio project.
------------------------------------

.. image:: https://cloud.githubusercontent.com/assets/2396869/5591755/1e6c20a0-91ec-11e4-837a-a8c3f228c028.jpg  
	:height: 500px
	:align: right

- Author: gbmhunter <gbmhunter@gmail.com> (www.mbedded.ninja)
- Created: 2015-01-01
- Last Modified: 2015-01-01
- Version: v1.0.0.0
- Company: MbeddedNinja
- Project: ColumbusRadio
- Language: Bash, Python
- Compiler: n/a
- uC Model: n/a
- Computer Architecture: RaspberryPi with Volumio v1.51 image.
- Operating System: 
- Documentation Format: Doxygen
- License: GPLv3

.. role:: bash(code)
	:language: bash

Description
===========

Repo for the Columbus radio project. Contains code which sets up the RaspberryPi/Volumio platform and implements the hardware UI.

Installation
============

1. Clone the git repo onto your local storage.
2. Download the Volumio v1.51 SD card image and write to SD card.
3. Insert SD card into RaspberryPi B+ and connect ethernet cable.
4. Go to :code:`volumio.local/` on your browser. Naviagte to the settings and rename the :code:`volumio` to :code:`columbus`.
4. Copy repository onto the RaspberryPi. This can be done with the following rsync command on a UNIX host system:
   :bash:`rsync -avz /home/gbmhunter/GoogleDrive/Projects/ColumbusRadio/ root@columbus:~/ColumbusRadio
5. SSH into the RaspberryPi as the root user with the command:
   :bash:`ssh -l root volumio`
   Note: The default password is :code:`volumio`.
6. Run the setup script with the command:
   :bash:`sh ~/ColumbusRadio/setup/setup.sh`.
   This should download all dependecies, install them, and then setup the hardware UI python script to run on startup.
7. Reboot the RaspberryPi to start the hardware UI script.
8. Done! The RaspberryPi/volumio is now configured correctly for the ColumbusRadio project.

Issues
======

See GitHub Issues.
	
FAQ
===

1. I entered the wrong Spotify credentials into volumio the first time around and now I can't get Spotify to work

Volumio v1.51 has a bug where if you don't get the Spotify credentials right the first time around, it won't work at all. You have to re-image the SD card and get them right the first time around.

Changelog
=========

========= ========== ===================================================================================================
Version    Date       Comment
========= ========== ===================================================================================================
v1.0.0.0  2015-01-01 Initial commit. Columbus radio up and running. Hardware UI script working with two threads (one for controlling the radio's knobs, and the other for monitoring internet connectivity). Setup script added, but may not work correctly, as it has been un-tested after some minor tweaks where done.
========= ========== ===================================================================================================