import qi
import argparse
import math
import time
import sys
import os

import qi

try:
    sys.path.insert(0, os.getenv('MODIM_HOME') + '/src/GUI')
except Exception as e:
    print("Please set MODIM_HOME environment variable to MODIM folder.")
    sys.exit(1)

from ws_client import *


class ActionManager:

    def __init__(self, session):

        self.session = session

        self.mo_service = session.service("ALMotion")

    def get_actions_path(self):
        return "/home/robot/playground/Pepper-Walking-Assistant/demo/actions/"

    def set_profile_en(self):
        im.setProfile(['*', '*', '*', '*'])

    def set_profile_it(self):
        # im.init()
        im.setProfile(['*', '*', 'it', '*'])

    def interaction_register_user(self):

        # Default values
        line = ""

        modality = im.ask("record_user", timeout=999)
        if modality == "touch":
            line += "1"
        elif modality == "vocal":
            line += "0"
        else:
            line = "failure"

        language = im.ask("ask_language", timeout=999)
        if language == "failure":
            line = "failure"
        else:
            line += (", " + language)

        with open('/home/robot/playground/outcome.txt', 'w') as file:
            file.write(line)

    def interaction_blind_assist(self):
        user_response = im.ask('blind_ask_help', timeout=999)
        if user_response == 'yes':
            dest = im.ask('blind_agree', timeout=999)
            with open('/home/robot/playground/outcome.txt', 'w') as file:
                file.write(dest)
        else:
            with open('/home/robot/playground/outcome.txt', 'w') as file:
                file.write('failure')

    def interaction_deaf_assist(self):
        user_response = im.ask('deaf_ask_help', timeout=999)
        if user_response == 'yes':
            dest = im.ask('deaf_agree', timeout=999)
            with open('/home/robot/playground/outcome.txt', 'w') as file:
                file.write(dest)
        else:
            with open('/home/robot/playground/outcome.txt', 'w') as file:
                file.write('failure')


def is_file_empty(file_path):
    try:
        return os.path.isfile(file_path) and os.path.getsize(file_path) == 0
    except Exception as e:
        print("An error occurred: " + str(e))
        return False


parser = argparse.ArgumentParser()
parser.add_argument("--pip", type=str, default=os.environ.get('PEPPER_IP', '127.0.0.1'),
                    help="Robot IP address. Default is '127.0.0.1'.")
parser.add_argument("--pport", type=int, default=9559,
                    help="Naoqi port number. Default is 9559.")
args = parser.parse_args()

pip = args.pip
pport = args.pport

print("Connecting to tcp://" + pip + ":" + str(pport))

# Starting application
try:
    connection_url = "tcp://" + pip + ":" + str(pport)
    app = qi.Application(["Move", "--qi-url=" + connection_url])
except RuntimeError:
    print("Can't connect to Naoqi at ip " + str(pip) + " on port " + str(pport) + ".\n"
                                                                                  "Please check your script arguments. Run with -h option for help.")
    sys.exit(1)

app.start()
session = app.session
print("[INFO] Setting up session")

# Get the modim client
mws = ModimWSClient()
mws.setDemoPathAuto(__file__)
print("[INFO] Setting up Modim")

action_manager = ActionManager(session)
print("[INFO] Setting up action manager")

# TODO
#   1. run interaction to retrieve user data (wait with while)
#   2. write everything on file using \t as separator
#   3. read the line and split by \t


name = 'Daniel'
user_id = 0
alevel = 'blind'
language = 'it'

print("[INFO] Retrieving user")
print("[INFO] Selected user: " + name + " (" + str(user_id) + ") | " + alevel + " | " + language)

# Set the language profile
if language == "en":
    mws.run_interaction(action_manager.set_profile_en)
elif language == "it":
    mws.run_interaction(action_manager.set_profile_it)
else:
    raise ValueError("Invalid language: " + language)

if alevel == "blind":
    mws.run_interaction(action_manager.interaction_blind_assist)
elif alevel == "deaf":
    mws.run_interaction(action_manager.interaction_deaf_assist)
else:
    raise ValueError("Invalid alevel: " + alevel)

file_path = '/home/robot/playground/outcome.txt'
while is_file_empty(file_path):
    time.sleep(0.01)

# The file now contains the required destination
dest = None
with open(file_path, "r") as file:
    lines = file.readlines()
    if len(lines) > 0:
        dest = lines[0]

print("[INFO] Destination: " + str(dest))

app.run()
