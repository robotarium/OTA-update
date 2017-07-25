#!/usr/bin/python
import os
import shutil
import sys
import fileinput
import subprocess
import asyncio
import mqtt_interface.mqttInterface as mqttInterface
import json
import argparse
import queue
import socket
import struct
#import mqtt_interface.messages as messages
import GRITSBOT_MESSAGES as MSGS

def mqtt_handler(msg):
   global robotIP_list
   #print('reached callback')
   message = json.loads(msg.payload.decode())
   print("Got message: ", message)
   if(message['msgType'] == MSGS.MSG_HEARTBEAT) & ('IP' in message):
        #print(message)
        if message['IP'] not in robotIP_list:
            robotIP_list.append(message['IP'])
   print(robotIP_list)

def main():
    # initialize MQTT client
    hostPort  = 1884
    hostIP    = '192.168.1.2'
    try:
        mqtt_client = mqttInterface.MQTTInterface(port=hostPort, host=hostIP)
        mqtt_client.start()
    except ConnectionRefusedError as e:
        print("Couldn't connect to MQTT broker at " + str(hostIP) + ":" + str(hostPort) + ". Exiting.")
        return -1

    # create a globally accessible list of robot IPs
    global robotIP_list
    robotIP_list = list()

    #subscribe to the power topics and listen for IP addresses
    robotIndexList = range(101)

    for i in robotIndexList:
        inputTopic = str(i) + "/power_data" # iterate over 100 robots
        mqtt_client.subscribe_with_callback(inputTopic, mqtt_handler)

    number_of_robots = 4
    while len(robotIP_list) != number_of_robots:
        pass

    mqtt_client.stop()
    # ensure firmware has been updated from the repo
    print('reached start of flash code')
    IGNORE_PATTERNS = ('*.git*','GRITSBot_Motor')
    #src_path = "/home/robotarium/Git/RobotariumRepositories/GRITSBot_firmware"
    #dest_path = "/home/robotarium/PlatformIO/1MBFlash_Config/src"
    #backup_path = "/home/robotarium/PlatformIO/1MBFlash_Config/src_backup"
    #shutil.rmtree(backup_path)
    #shutil.copytree(dest_path,backup_path,ignore=shutil.ignore_patterns(*IGNORE_PATTERNS))
    #shutil.rmtree(dest_path)
    #shutil.copytree(src_path,dest_path,ignore=shutil.ignore_patterns(*IGNORE_PATTERNS))

    # flash code onto each robot
    numOfFailures = 0
    config_file = 'platformio.ini'
    for i in range(len(robotIP_list)):
	# Change platformIO.ini file to replace the IP address of the upload port
        f = open(config_file,'r')
        flines = f.readlines();
        flines = flines[:-1]
        f.close()
        f = open(config_file,'w')
        f.writelines(flines)
        f.write('upload_port = ' + robotIP_list[i])
        f.close()
	# Figure out a way to write a command to the PlatformIO terminal interface
        try:
            subprocess.check_output('platformio run --target upload',shell=True)
        except:
            numOfFailures += 1
            print("Failed to flash onto robot with IP %s ",str(robotIP_list[i]))
    print("Finished Flashing. Number of Failures %s",str(numOfFailures))
if __name__ == "__main__":
    main()
