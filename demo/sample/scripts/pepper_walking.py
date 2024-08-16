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




def Greeting():
    im.init()
    im.setProfile(['*', '*', 'it', '*'])
    im.execute("custom_greeting")

    


    


if __name__ == "__main__":

    ## TODO: aggiungere human detection con sensori

    user_db = {"bruno":"deaf"} # Dictionary that simulates users' database
   
    mws = ModimWSClient()
    mws.setDemoPathAuto(__file__)

    pwu_obj = PepperWalkingUtils()
    actions_path = pwu_obj.actionsPath()
    active_user = random.choice(user_db.keys()) ##['known','unknown'] ## virtualization of face recognition step
    
    if active_user != 'unknown': ## If the user is already registered

        disability = user_db[active_user] #Extract disability
        pwu_obj.createCustomGreeting(active_user,disability) #Save active username

        if disability == "blind": # If blind
            mws.run_interaction(Greeting)   
        
        elif disability == "deaf":
            mws.run_interaction(Greeting)   
            