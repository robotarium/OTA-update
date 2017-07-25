#!/usr/bin/python
import os
import shutil
import sys
import fileinput
import subprocess

IGNORE_PATTERNS = ('*.git*','GRITSBot_Motor')
# MAKE SURE FIRMWARE HAS BEEN UPDATED FROM THE GIT REPO
#src_path = "C:\\Siddharth\\Git\\GRITSBot_firmware\\"
src_path = "/home/robotarium/Git/RobotariumRepositories/GRITSBot_firmware"
#dest_path = "C:\\Siddharth\\esp8266\\robotarium_platformio\\src\\"
dest_path = "/home/robotarium/PlatformIO/1MBFlash_Config/src"
backup_path = "/home/robotarium/PlatformIO/1MBFlash_Config/src_backup"
shutil.rmtree(backup_path)
shutil.copytree(dest_path,backup_path,ignore=shutil.ignore_patterns(*IGNORE_PATTERNS))
shutil.rmtree(dest_path)
shutil.copytree(src_path,dest_path,ignore=shutil.ignore_patterns(*IGNORE_PATTERNS))

# NOW FLASH CODE TO EACH ROBOT
config_file = 'platformio.ini'
for i in range(len(sys.argv)-1):
	# Change platformIO.ini file to replace the IP address of the upload port 
	f = open(config_file,'r')
	flines = f.readlines();
	flines = flines[:-1]
	f.close()
	f = open(config_file,'w')
	f.writelines(flines)
	f.write('upload_port = ' + sys.argv[i+1])
	f.close()
	# Figure out a way to write a command to the PlatformIO terminal interface 
 	output = subprocess.check_output('platformio run --target upload',shell=True)
