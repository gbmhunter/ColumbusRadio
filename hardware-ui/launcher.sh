#!/bin/bash
#
# @file               launcher.sh
# @author             Geoffrey Hunter <gbmhunter@gmail.com> (www.mbedded.ninja)
# @created            2014-12-31
# @last-modified      2015-01-01
# @brief              Script designed to be launched by crontab at startup to start the ColumbusRadio "hardware" UI python script.
# @details
#                     See README.rst in repo root dir for more info.
#
# Launch python script, that should be in the same
# directory as this file, however, we still need to specify the
# absolute path
# This assumes the ColumbusRadio repo was cloned into ~/ColumbusRadio
sudo python ~/ColumbusRadio/hardware-ui/hardware-ui.py 