import sys
import time
import os
import random
import subprocess
from src.main import allah
# from src import main


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
    im.setProfile(['*', '*', '*', '*'])

def setProfileIt():
    #im.init()
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
                file.write(required_dest)

            #subprocess.run(['python', '/home/robot/playground/pepper_walking_assistant/assistant/assistant.py'])
           
            ## TODO: Andare in required_dest ( goto(required_dest) )

        else:
            im.execute('deaf_disagree')
            #print("PERCORSO ROBOT " + os.path.dirname(os.path.realpath(__file__ ))) #/home/robot/src/modim/src/GUI  #/home/robot/src/modim/src/GUI/../../../playground
            with open("/home/robot/playground/outcome.txt","w") as file:
                file.write("failure")
            time.sleep(5)
            im.init()
            ## TODO: reset procedure?
    
def blindAskHelp():
    q = im.ask('blind_ask_help',timeout = 999)
    if(q == 'agree'):
        required_dest = im.ask('blind_agree',timeout = 999)
        with open("/home/robot/playground/outcome.txt","w") as file:
            file.write(required_dest)

    else:
        im.execute('blind_disagree')
        with open("/home/robot/playground/outcome.txt","w") as file:
                file.write("failure")
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
def failure():
     im.init()
def recordUser():
    modality = im.ask("record_user",timeout = 999)
    print("MODALITY" + modality)
    with open("/home/robot/playground/outcome.txt","w") as file:
        file.write(str(modality).strip())

    
def askLanguage():
    modality = im.ask("ask_language",timeout = 999)
    with open("/home/robot/playground/outcome.txt","w") as file:
        file.write(str(modality).strip())


if __name__ == "__main__":

        # ----------------------------- Argument parsing ----------------------------- #
    parser = argparse.ArgumentParser()
    parser.add_argument("--pip", type=str, default=os.environ['PEPPER_IP'],
                        help="Robot IP address.  On robot or Local Naoqi: use '127.0.0.1'.")
    parser.add_argument("--pport", type=int, default=9559,
                        help="Naoqi port number")
    parser.add_argument("--current_room", type=str, default="A",
                        help='ID of the room you are currently in')
    parser.add_argument("--target_room", type=str, default="D",
                        help='ID of the room to go to')
    parser.add_argument("--alevel", type=int, default=1,
                        help='Disability level. The higher it is, the more paths are available')
    parser.add_argument("--wtime", type=int, default=60,
                        help='Number of seconds to wait with the hand raised before canceling the procedure')
    parser.add_argument("--lang", type=str, default='en',
                        help='Language')

    args = parser.parse_args()

    user_db = {"Bruno":["deaf","en"]} #"unknown":[]}#,"Bruno":["deaf","en"]}#, "Carla": "blind"} # Dictionary that simulates users' database
   
    mws = ModimWSClient()
    mws.setDemoPathAuto(__file__)

    pwu_obj = PepperWalkingUtils()
    actions_path = pwu_obj.actionsPath()
    
    #while True:
    #    mws.run_interaction(waitForHuman) # Wait for human to position
    active_user = random.choice(user_db.keys()) ##['known','unknown'] ## virtualization of face recognition step
    print(active_user)
    if active_user != 'unknown': ## If the user is already registered

        language = user_db[active_user][1]   #Extract language
        

        disability = user_db[active_user][0] #Extract disability

    else:
        mws.run_interaction(recordUser)
        status =  pwu_obj.checkStatus()
        if(status != "failure"):
            if(status == "vocal"):
                disability = "blind"
            else:
                disability = "deaf"
        else:
            print("[INFO] ROUTINE CANCELED DURING MODALITY SELECTION ")
            mws.run_interaction(failure)
            exit(1)

            #continue
        
        mws.run_interaction(askLanguage)
        status =  pwu_obj.checkStatus()
        print("STATUS "+ status)
        if(status != "failure"):
            if(status == "english"):
                language = "en"
            else:
                language = "it"
        else:
            print("[INFO] ROUTINE CANCELED DURING LANGUAGE SELECTION ")
            mws.run_interaction(failure)
            exit(1)
            #continue

    if language == "en":
            mws.run_interaction(setProfileEn)
    else:
        mws.run_interaction(setProfileIt)
    if active_user == "unknown":
        pwu_obj.createCustomGreeting("",disability) #Save active username
    else:
        pwu_obj.createCustomGreeting(active_user,disability) #Save active username

    if disability == "blind": # If blind
        mws.run_interaction(greeting)
        time.sleep(2)
        mws.run_interaction(blindAskHelp)
        
        status =  pwu_obj.checkStatus()
        if(status != "failure"):
            print("[BLIND] launching assistant.py")
            #subprocess.call(['python', '/home/robot/playground/pepper_walking_assistant/assistant/assistant.py'])
            allah(args, mws)

        else:
            print("[BLIND] aborted")
            time.sleep(10)
            #continue
    
    elif disability == "deaf": # If deaf
        mws.run_interaction(greeting)
        time.sleep(2)
        mws.run_interaction(deafAskHelp)

        status =  pwu_obj.checkStatus()
        if(status != "failure"):
            print("[DEAF] launching assistant.py")
            dest = pwu_obj.checkStatus()
            # subprocess.call(['python', '/home/robot/playground/pepper_walking_assistant/demo/sample/scripts/src/main.py', '--target_room', dest ])
            allah(args, mws)

        else:
            print("[DEAF] aborted")
            time.sleep(10)
            #continue


        
