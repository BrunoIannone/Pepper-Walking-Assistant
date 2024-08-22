import sys
import time
import os
import random
import subprocess


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

def setProfileEn():
    im.init()

def setProfileIt():
    im.init()
    im.setProfile(['*', '*', 'it', '*'])

def greeting():
    im.execute("custom_greeting")

def deafAskHelp():
    q = im.ask("deaf_ask_help", timeout = 999)
    print("RISPOSTA " + q)
    if (q!='timeout'):
        if q == 'agree':
            required_dest = im.ask('deaf_agree',timeout = 999)

            with open("/home/robot/playground/outcome.txt","w") as file:
                file.write("ok")

            #subprocess.run(['python', '/home/robot/playground/pepper_walking_assistant/assistant/assistant.py'])
           
            ## TODO: Andare in required_dest ( goto(required_dest) )

        else:
            im.execute('deaf_disagree')
            #print("PERCORSO ROBOT " + os.path.dirname(os.path.realpath(__file__ ))) #/home/robot/src/modim/src/GUI  #/home/robot/src/modim/src/GUI/../../../playground
            with open("/home/robot/playground/outcome.txt","w") as file:
                file.write("fail")
            time.sleep(5)
            im.init()
            ## TODO: reset procedure?
    
def blindAskHelp():
    q = im.ask('blind_ask_help',timeout = 999)
    if(q == 'agree'):
        im.execute('blind_agree')
    else:
        im.execute('blind_disagree')
        time.sleep(5)
        im.init()
        ## TODO: reset procedure?        
       
def waitForHuman():
    stop_detection = False
    is_human_detected = False

    #Checking if human stay in front of Pepper more than 2 seconds
    im.robot.startSensorMonitor()
    while not stop_detection:
        while not is_human_detected:
            p = im.robot.sensorvalue() #p is the array with data of all the sensors
            print("SENSOR VALUE " + p)
            is_human_detected = p[1] > 0.0 and p[1] < 1.0 #p[1] is the Front sonar
        if is_human_detected:
            print('*Person detected*')
            time.sleep(2)
            p = im.robot.sensorvalue()
            is_human_detected = p[1] > 0.0 and p[1] < 1.0
            if is_human_detected:
                print('*Person still there*')
                stop_detection = True
            else:
                print('*Person gone*')
    im.robot.stopSensorMonitor()

def recordUser():
    modality = im.ask("record_user",timeout = 999)
    with open("/home/robot/playground/outcome.txt","w") as file:
                file.write(str(modality).strip())

    



if __name__ == "__main__":

    user_db = {"Bruno":["deaf","en"]}#"unknown":[]}#,Bruno":["deaf","en"]}#, "Carla": "blind"} # Dictionary that simulates users' database
   
    mws = ModimWSClient()
    mws.setDemoPathAuto(__file__)

    pwu_obj = PepperWalkingUtils()
    actions_path = pwu_obj.actionsPath()
    
    #while True:
    #    mws.run_interaction(waitForHuman) # Wait for human to position
    active_user = random.choice(user_db.keys()) ##['known','unknown'] ## virtualization of face recognition step
    
    if active_user != 'unknown': ## If the user is already registered

        language = user_db[active_user][1]   #Extract language
        if language == "en":
            mws.run_interaction(setProfileEn)
        else:
            mws.run_interaction(setProfileIt)

            


        disability = user_db[active_user][0] #Extract disability

        pwu_obj.createCustomGreeting(active_user,disability) #Save active username

        if disability == "blind": # If blind
            mws.run_interaction(greeting)
            time.sleep(2)
            mws.run_interaction(blindAskHelp)
            
        
        elif disability == "deaf":
            mws.run_interaction(greeting)
            time.sleep(2)
            mws.run_interaction(deafAskHelp) 
            if(pwu_obj.isSuccess()):
                print("SUCCESS")
                # with open('/home/robot/playground/pepper_walking_assistant/assistant/assistant.py') as file:
                #     exec(file.read())
                subprocess.call(['python', '/home/robot/playground/pepper_walking_assistant/assistant/assistant.py'])

            else:
                print("FAILURE")
    else:
        mws.run_interaction(recordUser)
        
