#!/usr/bin/env python

#
# @file               hardware-ui.py
# @author             Geoffrey Hunter <gbmhunter@gmail.com> (www.mbedded.ninja)
# @created            2014-12-31
# @last-modified      2015-01-01
# @brief              Controls the "hardware" UI on the ColumbusRadio.
# @details
#                     See README.rst in repo root dir for more info.
#

# All modules included by default with python on the RaspberryPi except for the RPi.GPIO


import time
import os

# Used to control the GPIO pins on the RaspberryPi
import RPi.GPIO as GPIO

# Used to send http command to volumio player (for next track pot)
import urllib2

# To catch socket timeout error which can occur when checking for internet connection
import socket

# Used for hold-off on potentiometer triggers (next track pot)
import time

# The next 3 import's are used for running code that will turn of the bulb when this script exits
#import atexit
#import signal
import sys

# For putting the internet check stuff in it's own thred, because
# it is too slow to run inside the main loop
import threading



#---------------------------------#
#------------- CONFIG ------------#
#---------------------------------#

# @brief    Debug flag. Set to 1 to print debug messages.
DEBUG = 1

#----- HARDWARE SETUP -----#

# Numers are the GPIO number (e.g. GPIO11) NOT the pin number on the header (which would be pin 23 on the B+)
SPICLK = 11
SPIMISO = 9
SPIMOSI = 10
SPICS = 8

# @brief    The GPIO number that the gate to the N-Ch MOSFET which switches on the bulb is connected to.
# @details  Active-high logic. Connected to GPIO 17 (Pin 11).
CONN_BULB = 17 

#----- GENERAL CONFIG ------#

# @brief    The period in milliseconds between each iteration of the main loop. Note that the
#           actual time will be slightly longer and variable due to the processing time of the loop
#           not being taken into account (could be much longer when checking for internet connection)
MAIN_LOOP_PERIOD_MS = 250

# @brief    The time in milliseconds between each check to see if we are connected to the internet
INTERNET_CHECK_PERIOD_MS = 10*1000

# @brief    The URL to check. Currently this is set to a Google server
INTERNET_CHECK_URL = 'http://74.125.228.100'

# @brief    The maximum time to spend waiting for a response from INTERNET_CHECK_URL before timing out.
INTERNET_CHECK_TIMEOUT_S = 5

# @brief    The HTTP command to send that will cause volumio to change to the next track.
# @details  This will change if you change the name of volumio!
NEXT_TRACK_COMMAND = 'http://columbus/command/?cmd=next'

# @brief    The number of ADC channels on the MCP3008 IC to read
NUM_CHANNELS_TO_READ = 2

# @brief    The desired flash rate for the "I'm not connected to the internet" bulb
BULB_FLASH_PERIOD_MS = 2000

VOL_POT_CH_NUM = 0                          # Connected to channel 0
VOL_POT_TOLERANCE = 10                      # Standard tolerance for the volume pot.

NEXT_TRACK_POT_CH_NUM = 1                   # Connected to channel 1
NEXT_TRACK_POT_TOLERANCE = 10               # Need a higher tolerance for the next track pot as it has a high resistance (around 7MR), and is worn.
NEXT_TRACK_POT_MAX_TRIGGER_RATE_MS = 2000   # Maximum rate that next track events can fire at when the next track pot is turned.

#---------------------------------#
#---------- GPIO SETUP -----------#
#---------------------------------#
 
GPIO.setmode(GPIO.BCM)

# set up the SPI interface pins
GPIO.setup(SPIMOSI, GPIO.OUT)
GPIO.setup(SPIMISO, GPIO.IN)
GPIO.setup(SPICLK, GPIO.OUT)
GPIO.setup(SPICS, GPIO.OUT)

# Bulb GPIO drives gate of MOSFET that switches bulb on
GPIO.setup(CONN_BULB, GPIO.OUT)

#--------------------------------------------#
#---------- INTERNET CHECK THREAD -----------#
#--------------------------------------------#

# @brief    Determines if we have internet access
# @details  urllib2.URLError can occur when connection between computer and router is severed.
#           socket.timeout can occur if connection between router and phone line is severed.
def InternetOn():
    try:
        response=urllib2.urlopen(INTERNET_CHECK_URL, timeout = INTERNET_CHECK_TIMEOUT_S)
        return True
    except urllib2.URLError:
        print "Timeout!"
    except socket.timeout:
        print "Socket timeout!"

    return False


class InternetCheck(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)
        # A flag to notify the thread that it should finish up and exit
        self.kill_received = False

    def run(self):
        while not self.kill_received:
            self.do_something()

    def do_something(self):

        print 'InternetCheck.do_something() called.'

        # @brief    Used to remember the last time we checked to see if we are connected to the internet
        lastInternetCheckTimeMs = 0

        lastBulbFlashTimeMs = 0

        # Used to remember the state of the bulb (e.g. on or off) for flashing purposes
        # when we can't find a connection to the internet
        bulbState = False


        '''if(exitInternetCheckThread is False):
            print 'Exiting InternetCheckThread...'
            sys.exit(0)
            return'''

        # Get the current time in milli-seconds
        currTimeMs = int(round(time.time() * 1000))
       
        # See if it is time to check for an internet connection
        if(currTimeMs > lastInternetCheckTimeMs + INTERNET_CHECK_PERIOD_MS):

            if DEBUG:
                print "Checking for internet connection..."

            # Now lets see if we are connected to the internet
            areWeConnected = InternetOn()
            #areWeConnected = False

            if DEBUG:
                if areWeConnected:
                    print "InternetOn returned True!"
                else:
                    print "InternetOn returned False!"

            # Update lastInternetCheckTimeMs
            lastInternetCheckTimeMs = currTimeMs

        # END | if(currTimeMs > lastInternetCheckTimeMs + INTERNET_CHECK_PERIOD_MS):

        # Perform "internet connected" related tasks that can't be inside the slow-running "internet check" loop above
        if areWeConnected:
            # We are connected to the internet, lets keep the bulb on
            GPIO.output(CONN_BULB, True)
        else:
            if(currTimeMs > lastBulbFlashTimeMs + BULB_FLASH_PERIOD_MS):

                # Toggle the bulb
                bulbState = not bulbState
                GPIO.output(CONN_BULB, bulbState)

                lastBulbFlashTimeMs = currTimeMs
        # END | if areWeConnected:

        time.sleep(5.0)
    # END | def do_something(self):
# END | class InternetCheck(threading.Thread):


#----------------------------------------------------#
#---------------- KNOB CONTROL THREAD ---------------#
#----------------------------------------------------#


# @brief    Read's SPI data from MCP3008 chip, 8 possible adc's (0 thru 7).
# @details  Bit-bangs the data, does not use the SPI peripheral.
def ReadAdc(adcnum, clockpin, mosipin, misopin, cspin):
    if ((adcnum > 7) or (adcnum < 0)):
        return -1
    GPIO.output(cspin, True)

    GPIO.output(clockpin, False)  # start clock low
    GPIO.output(cspin, False)     # bring CS low

    commandout = adcnum
    commandout |= 0x18  # start bit + single-ended bit
    commandout <<= 3    # we only need to send 5 bits here
    for i in range(5):
            if (commandout & 0x80):
                    GPIO.output(mosipin, True)
            else:
                    GPIO.output(mosipin, False)
            commandout <<= 1
            GPIO.output(clockpin, True)
            GPIO.output(clockpin, False)

    adcout = 0
    # read in one empty bit, one null bit and 10 ADC bits
    for i in range(12):
            GPIO.output(clockpin, True)
            GPIO.output(clockpin, False)
            adcout <<= 1
            if (GPIO.input(misopin)):
                    adcout |= 0x1

    GPIO.output(cspin, True)
    
    adcout >>= 1       # first bit is 'null' so drop it
    return adcout
# END | def ReadAdc(adcnum, clockpin, mosipin, misopin, cspin):



# @brief    A class to hold all the information for a single potentiometer.
class Potentiometer:
    channelNum = 0

    # @brief    This variable stores the last ADC value which caused a 'has changed' event to occur.
    lastRead = 0

    # @brief    Gets set to true if a 'has changed' event occurs. This must be reset to False manually after handling the event. 
    hasChanged = False

    # @brief    Used to store the time in milli-seconds since the potentiometer "hasChanged" event was triggered.
    lastChangedMs = 0

    # @brief    Used to determine the maximum rate the "has changed" event will fire at.
    maxTrigRateMs = 0

    # @brief    The latest ADC value reading from the potentiometer gets stored in this variable.
    adcVal = 0
    changedBy = 0

    # This prevents jitter due to noise
    tolerance = 5
# END | class Potentiometer:

# @brief    Class to control the 2 active dials on front of the Columbus radio.
# @details  This class measures the ADC readings from the 2 potentiometers, filters the results, and
#           sends appropriate commands based on these results to control the volume and 'next track' 
#           functionality respectively.
class KnobControl(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)
        # A flag to notify the thread that it should finish up and exit
        self.kill_received = False


        self.firstTime = True

         # This keeps track of the last pot values
        self.potentiometers = []

        # Populate list with required number of potentiometer objects
        for i in range (0, NUM_CHANNELS_TO_READ):
            self.potentiometers.append(Potentiometer())

        # Set each potentiometer to the correct ADC IC channel
        self.potentiometers[0].channelNum = VOL_POT_CH_NUM
        self.potentiometers[0].tolerance = VOL_POT_TOLERANCE

        self.potentiometers[1].channelNum = NEXT_TRACK_POT_CH_NUM

        # Tweak tolerances individually (if change from default is desired)
        self.potentiometers[1].tolerance = NEXT_TRACK_POT_TOLERANCE

        # Only allow the "next track" pot to fire an event every 2s max
        self.potentiometers[1].maxTrigRateMs = NEXT_TRACK_POT_MAX_TRIGGER_RATE_MS

    def run(self):
        while not self.kill_received:
            self.do_something()

    def do_something(self):

        print 'KnobControl.do_something() called.'

        # Get the current time in milli-seconds
        currTimeMs = int(round(time.time() * 1000))

        # MEASURE POTENTIOMETER VALUES AND RAISE EVENTS IF TRIGGERED
        for i in range (0, NUM_CHANNELS_TO_READ):
        
            # we'll assume that the pot didn't move
            self.potentiometers[i].hasChanged = False
     
            # Read the analog pin
            self.potentiometers[i].adcVal = ReadAdc(self.potentiometers[i].channelNum, SPICLK, SPIMOSI, SPIMISO, SPICS)

            # Prevent "potentiometer changed" events the first time through
            if self.firstTime:
                self.potentiometers[i].lastRead = self.potentiometers[i].adcVal

            if(currTimeMs < self.potentiometers[i].lastChangedMs + self.potentiometers[i].maxTrigRateMs):
                self.potentiometers[i].lastRead = self.potentiometers[i].adcVal
               

            # How much has it changed since the last read?
            self.potentiometers[i].changedBy = abs(self.potentiometers[i].adcVal - self.potentiometers[i].lastRead)
     
            #if DEBUG:
                #print "trim_pot:", potentiometers[i].adcVal
                #print "pot_adjust:", potentiometers[i].changedBy
                #print "last_read", potentiometers[i].lastRead
     
            if (self.potentiometers[i].changedBy > self.potentiometers[i].tolerance):
                # Sent hasChanged event to true. Code below will handle these events on a pot-by-pot basis
                self.potentiometers[i].hasChanged = True

                if DEBUG:
                    print "hasChanged set to True."
                    print "changedBy = ",  self.potentiometers[i].changedBy
                    print "lastChangedMs = ", self.potentiometers[i].lastChangedMs
                    print "currTimMs = ", currTimeMs

                self.potentiometers[i].lastChangedMs = currTimeMs
     
        # END | for i in range (0, NUM_CHANNELS_TO_READ):

        # firstTime will now be false until script is restarted
        self.firstTime = False

        # PROCESS POTENTIOMETER EVENTS

        # Potentiometer 0 is for controlling the volume
        if(self.potentiometers[0].hasChanged):
            setVolume = self.potentiometers[0].adcVal / 10.24           # convert 10bit adc0 (0-1024) trim pot read into 0-100 volume level
            setVolume = round(setVolume)          # round out decimal value
            setVolume = int(setVolume)            # cast volume as integer

            print 'Volume = {volume}%' .format(volume = setVolume)

            # Build up a command-line command
            setVolCmd = 'sudo amixer cset numid=1 -- {volume}% > /dev/null' .format(volume = setVolume)

            # Send the set volume command to the system and run as if from the command-line
            os.system(setVolCmd)

            # Save the potentiometer reading for the next loop
            self.potentiometers[0].lastRead = self.potentiometers[0].adcVal

            #potentiometers[0].hasChanged = False

        # Potentiometer 1 is for going to the next track
        if(self.potentiometers[1].hasChanged):

            print 'Skipping to next track...'


            # DEBUG: the mpc command didn't work, so I ended up having to send a http command to the volumio player instead

            # Build up a command-line command
            #nextTrackCmd = 'mpc next > /dev/null'

            # Send the set volume command to the system and run as if from the command-line
            #os.system(nextTrackCmd)        

            # This way works!
            urlResponse = urllib2.urlopen(NEXT_TRACK_COMMAND)

            # Save the potentiometer reading for the next loop
            self.potentiometers[1].lastRead = self.potentiometers[1].adcVal
        # END | if(potentiometers[1].hasChanged):

        # hang out and do nothing for a half second
        time.sleep(0.5)
    # END | def do_something(self):
# END | class KnobControl(threading.Thread):

# @brief    main() function for script.
# @details  Starts up the individual threads and controls their execution.
def main(args):

    threads = []

    #----- START THE THREADS -----#

    # Start the internet check thread
    print 'Starting the internet check thread...'
    t = InternetCheck()
    threads.append(t)        
    t.start()
    print 'Internet check thread started...'

    # Start the knob control thread
    print 'Starting the knob control thread...'
    t = KnobControl()
    threads.append(t)        
    t.start()
    print 'Knob control thread started...'

    #----- MONITOR THE THREADS -----#

    while len(threads) > 0:
        if DEBUG:
            print 'len(threads) = ', len(threads)
        
        try:
            if DEBUG:
                print 'In try block.'
            # Join all threads using a timeout so it doesn't block
            # Filter out threads which have been joined or are None
            for i in range(len(threads)):
                # Make sure thread still exists
                if threads[i] is not None:
                    if DEBUG:
                        print 'Attemping to join()...'
                    threads[i].join(1)
                    if threads[i].isAlive() is False:
                        if DEBUG:
                            print 'isAlive() is False, removing thread from list...'
                        threads.pop(i)
            if DEBUG:
                print 'Exiting try block...'
        except KeyboardInterrupt:
            print "Ctrl-c received! Sending kill to threads..."
            for t in threads:
                t.kill_received = True
        except Exception as e:
            print "Unknown exception caught! Sending kill to threads...", e
            for t in threads:
                t.kill_received = True

    print 'main() is returning...'

if __name__ == '__main__':
    main(sys.argv)

#----------------------------------------------------#
#--------------------- GRAVEYARD --------------------#
#----------------------------------------------------#
    

#------ SETUP EXIT HANDLER -------#

'''
def ExitHandler(signal, frame):
    print 'ExitHandler called.'
    # Turn of the bulb
    GPIO.output(CONN_BULB, False)
    print 'Signalling for thread to stop...'
    internetCheckThread.stop()
    print 'Waiting for internetCheckThread to exit...'
    internetCheckThread.join()
    print 'Python script hard-ui-v2.py is exiting!'
    sys.exit(0)

#atexit.register(ExitHandler)
signal.signal(signal.SIGINT, ExitHandler)'''

#------ THREADING -------#

#t1 = threading.Thread(target=InternetCheckThread)
#t1.start()
#t1.join()