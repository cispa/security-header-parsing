import platform
import os
import shutil
from distutils.dir_util import copy_tree
import subprocess

def main():
	system_name = platform.system().lower()
	if system_name == 'linux':
		system_name = 'linux'
	if system_name == 'windows':
		system_name = 'win'
	if system_name == 'darwin':
		system_name = 'mac'
	
	copy_tree(os.path.join('cmdline-tools/packages',f'cmdline-tools-{system_name}'), 'cmdline-tools/latest')

	cmd = 'yes | ./cmdline-tools/latest/bin/sdkmanager --licenses'
	cmd_output = subprocess.run(cmd, check=True, capture_output=True, text=True, shell=True).stdout.strip()
	print(cmd_output)

	cmd = './cmdline-tools/latest/bin/sdkmanager --update'
	cmd_output = subprocess.run(cmd, check=True, capture_output=True, text=True, shell=True).stdout.strip()
	print(cmd_output)

	cmd = './cmdline-tools/latest/bin/sdkmanager platform-tools emulator'
	cmd_output = subprocess.run(cmd, check=True, capture_output=True, text=True, shell=True).stdout.strip()
	print(cmd_output)

if __name__ == '__main__':
	main()