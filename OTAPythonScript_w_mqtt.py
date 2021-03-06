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
import time
#import mqtt_interface.messages as messages
import GRITSBOT_MESSAGES as MSGS

def mqtt_handler(msg):
   global robot_list
   #print('reached callback')
   message = json.loads(msg.payload.decode())
   if(message['msgType'] == MSGS.MSG_HEARTBEAT) & ('IP' in message):
        robot_index, mqttTopic = msg.topic.split('/')
        if robot_index not in robot_list:
            robot_list[robot_index] = message['IP']
   print(robot_list)

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
    global robot_list
    robot_list = dict()
    # enter expected number of robots to be flashed
    robotNumberRange = {23}
    expectedNumOfRobots = len(robotNumberRange)
    #subscribe to the power topics and listen for IP addresses
    for robot_index in robotNumberRange:
            inputTopic = str(robot_index) + "/power_data" # iterate over robots
            mqtt_client.subscribe_with_callback(inputTopic, mqtt_handler)
    startTime = time.time()
    while len(robot_list) != expectedNumOfRobots:
    	currentTime = time.time()
    	if (currentTime - startTime) > 20:
                print("Failed to hear back from some robots")
                break
    mqtt_client.stop()
    # ensure firmware has been updated from the repo
    print('reached start of flash code')
    IGNORE_PATTERNS = ('*.git*','GRITSBot_Motor')
    src_path = "/home/robotarium/Git/RobotariumRepositories/GRITSBot_firmware"
    dest_path = "/home/robotarium/PlatformIO/1MBFlash_Config/src"
    backup_path = "/home/robotarium/PlatformIO/1MBFlash_Config/src_backup"
    shutil.rmtree(backup_path)
    shutil.copytree(dest_path,backup_path,ignore=shutil.ignore_patterns(*IGNORE_PATTERNS))
    shutil.rmtree(dest_path)
    shutil.copytree(src_path,dest_path,ignore=shutil.ignore_patterns(*IGNORE_PATTERNS))

    # flash code onto each robot
    config_file = 'platformio.ini'
    failedToFlash = list()
    for k in robot_list:
	# Change platformIO.ini file to replace the IP address of the upload port
        f = open(config_file,'r')
        flines = f.readlines();
        flines = flines[:-1]
        f.close()
        f = open(config_file,'w')
        f.writelines(flines)
        f.write('upload_port = ' + robot_list[k])
        f.close()
	# Use shell command to perform a PlatformIO flash
        try:
            subprocess.check_output('platformio run --target upload',shell=True)
        except:
            print("Could not flash robot with ID " + str(k))
            failedToFlash.append(k)
    print('Flashing Complete')
    # list robots which never connected
    if len(robotNumberRange) != len(robot_list):
        print("Robot IDs which failed to connect")
        for i in robotNumberRange:
            if str(i) not in robot_list:
                print(i)
    # list robots which connected but couldn't be reflashed successfully
    if len(failedToFlash) != 0:
        print("Robot IDs which connected but failed to reflash")
        print(failedToFlash)
if __name__ == "__main__":
    main()
