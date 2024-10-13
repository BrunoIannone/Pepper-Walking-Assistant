import sys
import os
import argparse
import time
import qi

try:
    sys.path.insert(0, os.getenv('MODIM_HOME')+'/src/GUI')
except Exception as e:
    print("Please set MODIM_HOME environment variable to MODIM folder.")
    sys.exit(1)

# Set MODIM_IP to connnect to remote MODIM server

from ws_client import *

from src.actions.position_manager import PositionManager
from src.actions.action_manager import ActionManager
from src.users.user_manager import UserManager
from src.guide_me import guide_me
from src.utils.paths import get_path


if __name__ == "__main__":

    # ----------------------------- Argument parsing ----------------------------- #
    parser = argparse.ArgumentParser()
    parser.add_argument("--pip", type=str, default=os.environ['PEPPER_IP'],
                        help="Robot IP address.  On robot or Local Naoqi: use '127.0.0.1'.")
    parser.add_argument("--pport", type=int, default=9559,
                        help="Naoqi port number")
    parser.add_argument("--current_room", type=str, default="A",
                        help="ID of the room you are currently in")
    parser.add_argument("--target_room", type=str, default="D",
                        help="ID of the room you want to go")
    parser.add_argument("--wtime", type=int, default=60,
                        help="Number of seconds to wait with the hand raised before canceling the procedure")
    parser.add_argument("--uid", type=int, default=-1,
                        help="User id (testing purposes)")

    args = parser.parse_args()

    # Starting application
    pip = args.pip
    pport = args.pport
    try:
        connection_url = "tcp://" + pip + ":" + str(pport)
        app = qi.Application(["Memory Read", "--qi-url=" + connection_url])
    except RuntimeError:
        print("Can't connect to Naoqi at ip \"" + pip + "\" on port " + str(pport) + ".\n"
                                                                                     "Please check your script arguments. Run with -h option for help.")
        sys.exit(1)
    app.start()
    session = app.session
    # app.run()

    # Get the modim client
    mws = ModimWSClient()
    mws.setDemoPathAuto(__file__)

    print("[INFO] Working directory: " + os.getcwd())

    actionManager = ActionManager(session)
    actions_database_path = actionManager.get_actions_path()
    print("[INFO] Generating actions from folder: " + actions_database_path)

    print("[INFO] Generated actions:")
    for action in actionManager.generated_actions:
        print("[INFO] \t" + action)

    map_path = get_path('static/maps/map.txt')
    positionManager = PositionManager(map_path)

    users_database_path = get_path('static/users/users.txt')
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
            mws.run_interaction(actionManager.set_profile_en)
    elif language == "it":
        mws.run_interaction(actionManager.set_profile_it)
    else:
        raise ValueError("Invalid language: " + language)

    # Create custom greeting action file
    if newUser:
        actionManager.create_custom_greeting("", alevel)  # Create a greeting action file for the new user
    else:
        actionManager.create_custom_greeting(active_user.username, alevel)  # Create a greeting action file for the user

    # Ask for help
    if alevel == 0:  # Blindness

        mws.run_interaction(actionManager.custom_greeting)
        time.sleep(2)
        mws.run_interaction(actionManager.blind_ask_help)
        
        status =  actionManager.check_status()
        if(status != "failure"):
            print("[INFO] Blind help procedure starting")
            dest = actionManager.check_status()
            # TODO check the destination is correct
            # guide_me(active_user, args.current_room, args.target_room, mws, actionManager, positionManager, wtime=10)
            guide_me(active_user, args.current_room, dest, mws, actionManager, positionManager, wtime=10)
        else:
            print("[INFO] Blind help procedure aborted")
            time.sleep(10)
            #continue
    
    elif alevel == 1:  # Deafness

        mws.run_interaction(actionManager.custom_greeting)
        time.sleep(2)
        mws.run_interaction(actionManager.deaf_ask_help)

        status =  actionManager.check_status()
        if(status != "failure"):
            print("[INFO] Deaf help procedure starting")
            dest = actionManager.check_status()
            # TODO check the destination is correct
            # guide_me(active_user, args.current_room, args.target_room, mws, actionManager, positionManager, wtime=10)
            guide_me(active_user, args.current_room, dest, mws, actionManager, positionManager, wtime=10)
        else:
            print("[INFO] Deaf help procedure aborted")
            time.sleep(10)
            #continue

    app.run()