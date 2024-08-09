import sys
import time
import os
import random

try:
    sys.path.insert(0, os.getenv('MODIM_HOME')+'/src/GUI')
except Exception as e:
    print "Please set MODIM_HOME environment variable to MODIM folder."
    sys.exit(1)

# Set MODIM_IP to connnect to remote MODIM server

import ws_client
from ws_client import *
import pepper_walking_utils 
from pepper_walking_utils import *
import pickle




def blindGreetingRoutine():
   
    im.init()
    im.setProfile(['*', '*', 'it', '*'])
    name = im.activeUser()
    greeting_message = "Welcome back " + name
    im.executeModality("TTS",greeting_message)

if __name__ == "__main__":

    user_db = {"bruno":"blind"}
    # cmdsever_ip = '127.0.0.1'
    # cmdserver_port = 9101
    # demo_ip = '127.0.0.1'
    # demo_port = 8000

    mws = ModimWSClient()
    mws.setDemoPathAuto(__file__)
    pwu_obj = PepperWalkingUtils()
    
    
    # Specifica il percorso del file
    
    active_user = random.choice(['bruno']) ##['known','unknown'] ## virtualize face recognition 
    
    #mws.setGlobalVar("user_name",active_user)
    if active_user != 'unknown':
        pwu_obj.setUser(active_user)
        disability = user_db[active_user]
        if disability == "blind":
            mws.run_interaction(blindGreetingRoutine)
            
    
    
    #mws.run_interaction(knownUserRoutine)

    # local execution
    #mws.run_interaction(customRoutine)
