import sys
import os
import argparse
import time


try:
    sys.path.insert(0, os.getenv('MODIM_HOME')+'/src/GUI')
except Exception as e:
    print("Please set MODIM_HOME environment variable to MODIM folder.")
    sys.exit(1)

# Set MODIM_IP to connnect to remote MODIM server

from ws_client import *

from src.interactions.action_manager import ActionManager
from src.users.user_manager import UserManager
from src.guide_me import guide_me


def path_utils(relative_path):
    """
    Returns the path of the required file relative to the current one
    """
    return os.path.abspath(os.path.join(os.path.dirname(os.path.realpath(__file__)), relative_path))


if __name__ == "__main__":

        # ----------------------------- Argument parsing ----------------------------- #
    parser = argparse.ArgumentParser()
    parser.add_argument("--pip", type=str, default=os.environ['PEPPER_IP'],
                        help="Robot IP address.  On robot or Local Naoqi: use '127.0.0.1'.")
    parser.add_argument("--pport", type=int, default=9559,
                        help="Naoqi port number")
    parser.add_argument("--current_room", type=str, default="A",
                        help="ID of the room you are currently in")
    parser.add_argument("--wtime", type=int, default=60,
                        help="Number of seconds to wait with the hand raised before canceling the procedure")
    parser.add_argument("--uid", type=int, default=-1,
                        help="User id (testing purposes)")
    """
    parser.add_argument("--target_room", type=str, default="D",
                        help='ID of the room to go to')
    parser.add_argument("--alevel", type=int, default=1,
                        help='Disability level. The higher it is, the more paths are available')
    parser.add_argument("--lang", type=str, default='en',
                        help='Language')
    """

    args = parser.parse_args()

    # Get the modim client
    mws = ModimWSClient()
    mws.setDemoPathAuto(__file__)

    print("[INFO] Working directory: " + os.getcwd())

    actionManager = ActionManager()
    actions_database_path = actionManager.getActionsPath()
    print("[INFO] Generating actions from folder: " + actions_database_path)

    print("[INFO] Generated actions:")
    for action in actionManager.generated_actions:
        print("[INFO] \t" + action)

    users_database_path = path_utils('../static/users/users.txt')
    print("[INFO] Restoring users from: " + users_database_path)
    userManager = UserManager.load(users_database_path)
    
    print("[INFO] Users database:")
    for user in userManager.users:
        print("[INFO] \t" + user.username + " [" + str(user.alevel) + "]")

    #while True:
    #    mws.run_interaction(waitForHuman) # Wait for human to position

    """
    TODO remove userid: at startup the robot waits for the human; if a human is present, it
    uses face recognition to identify him and if not found it starts the register procedure
    """
    newUser = False
    if args.uid == -1:
        active_user = userManager.get_random_user()  # Debug, get random user
    else:
        active_user = userManager.find_user_by_id(args.uid)
    print('[INFO] Active user: ' + active_user.username)

    language = active_user.lang
    alevel = active_user.alevel
    
    """
    else:
        mws.run_interaction(actionManager.recordUser)
        status =  actionManager.checkStatus()
        if(status != "failure"):
            if(status == "vocal"):
                disability = "blind"
            else:
                disability = "deaf"
        else:
            print("[INFO] Routine canceled during modality selection ")
            mws.run_interaction(actionManager.failure)
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
    """

    # Set the language profile
    if language == "en":
            mws.run_interaction(actionManager.setProfileEn)
    elif language == "it":
        mws.run_interaction(actionManager.setProfileIt)
    else:
        raise ValueError("Invalid language: " + language)

    # Create custom greeting action file
    if newUser:
        actionManager.createCustomGreeting("", alevel)  # Create a greeting action file for the new user
    else:
        actionManager.createCustomGreeting(active_user.username, alevel)  # Create a greeting action file for the user 

    # Ask for help
    if alevel == 0:  # Blindness

        mws.run_interaction(actionManager.customGreeting)
        time.sleep(2)
        mws.run_interaction(actionManager.blindAskHelp)
        
        status =  actionManager.checkStatus()
        if(status != "failure"):
            print("[INFO] Blind help procedure starting")
            # guide_me(args, mws)
        else:
            print("[INFO] Blind help procedure aborted")
            time.sleep(10)
            #continue
    
    elif alevel == 1:  # Deafness

        mws.run_interaction(actionManager.customGreeting)
        time.sleep(2)
        mws.run_interaction(actionManager.deafAskHelp)

        status =  actionManager.checkStatus()
        if(status != "failure"):
            print("[INFO] Deaf help procedure starting")
            dest = actionManager.checkStatus()
            # TODO take the destination from the output file 
            # subprocess.call(['python', '/home/robot/playground/pepper_walking_assistant/demo/sample/scripts/src/main.py', '--target_room', dest ])
            # guide_me(args, mws)
        else:
            print("[INFO] Deaf help procedure aborted")
            time.sleep(10)
            #continue
