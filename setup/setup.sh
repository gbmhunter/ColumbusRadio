#!/bin/bash

#
# @file               setup.sh
# @author             Geoffrey Hunter <gbmhunter@gmail.com> (www.mbedded.ninja)
# @created            2014-12-31
# @last-modified      2015-01-01
# @brief              RaspberryPi B+ setup script for the ColumbusRadio project.
# @details
#                     See README.rst in repo root dir for more info.

# Download the RPi.GPIO package into user's directory
wget http://sourceforge.net/projects/raspberry-gpio-python/files/raspbian-wheezy/python-rpi.gpio_0.5.8-1_armhf.deb -P ~/

# Install the RPi.GPIO package
sudo dpkg -i ~/python-rpi.gpio_0.5.8-1_armhf.deb

# Remove the download
rm ~/python-rpi.gpio_0.5.8-1_armhf.deb

#--------------------------------------------------------------#
#---- CONFIGURE launcher.sh TO BE RUN EVERYTIME ON STARTUP ----#
#--------------------------------------------------------------#

# Write out current crontab
crontab -l > mycron
# Echo new cron into cron file
echo "@reboot sh ~/ColumbusRadio/hardware-ui/launcher.sh ~/ColumbusRadio/hardware-ui/cronlog 2>&1" >> mycron
# Install new cron file
crontab mycron
# Remove temp cron file
rm mycron

#--------------------------------------------------------------#
#--------------------------- GRAVEYARD ------------------------#
#--------------------------------------------------------------#

# Script to automate the setup of volumio and associated software for the retro-radio project 
#sudo apt-get update
# This next step will take some time (approx. 30-40mins on a fast internet connection)
# This one causes the volumio web interface to not work after restart
#sudo apt-get -y upgrade


#echo "$(tput setaf 1)[+] Updating system...$(tput sgr 0)"
#apt-get -y update; apt-get -y upgrade
#echo "$(tput setaf 1)[+] Installing Git$(tput sgr 0)"
#install git
#apt-get -y install git-core

#echo "$(tput setaf 1)[+] Cloning Volumio from github$(tput sgr 0)"
#git clone the Volumio-WEBUI into our nginx webserver directory
#rm -rf /var/www

# This didn't seem to work! Had to clone from Windows, then copy folder across.
# git was not working, even though it didn't report any errors
#git clone https://github.com/volumio/Volumio-WebUI.git /var/www

#echo "$(tput setaf 1)[+] Setting permissions and copying config files$(tput sgr 0)"
#chmod 775 /var/www/_OS_SETTINGS/etc/rc.local
#chmod 755 /var/www/_OS_SETTINGS/etc/php5/mods-available/apc.ini
#chmod -R 777 /var/www/command/
#chmod -R 777 /var/www/db/
#chmod -R 777 /var/www/inc/

#copy relevant configuration files, preserving permissions
#cp -arp /var/www/_OS_SETTINGS/etc /

#optionally remove git just to clean things up.
#apt-get -y remove git-core
#echo "$(tput setaf 1)[+] All done! please reboot with sudo reboot$(tput sgr 0)"

# Trying to fix python spi-dev module error
# One of these does fix it! Not sure which one
#sudo apt-get install gcc build-essentials

# Install python-dev so we can install the spi-dev module
#sudo apt-get install python-dev

#git clone https://github.com/doceme/py-spidev.git ~/py-spidev
#python ~/py-spidev/setup.py install