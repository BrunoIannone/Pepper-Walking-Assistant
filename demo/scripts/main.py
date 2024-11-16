import sys
import os
import argparse
import time
import qi

try:
    sys.path.insert(0, os.getenv('MODIM_HOME') + '/src/GUI')
except Exception as e:
    print("Please set MODIM_HOME environment variable to MODIM folder.")
    sys.exit(1)

# Set MODIM_IP to connnect to remote MODIM server

from ws_client import *

from src.actions.position_manager import PositionManager
from src.actions.action_manager import ActionManager
from src.users.user_manager import UserManager
from src.users.user import User, BLIND

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

    action_manager = ActionManager(session)
    print("[INFO] Setting up action manager")

    map_path = get_path('static/maps/map.txt')
    positionManager = PositionManager(map_path)

    users_database_path = get_path('static/users/users.txt')
    print("[INFO] Restoring users from: " + users_database_path)
    user_manager = UserManager.load(users_database_path)

    print("[INFO] Users database:")
    for user in user_manager.users:
        print("[INFO] \t" + user.username + " [" + str(user.userid) + "] [" + ("blind" if user.alevel == BLIND else "deaf") + "] [" + user.lang + "]")

    # while True:
    #    mws.run_interaction(waitForHuman) # Wait for human to position

    if args.uid not in user_manager:

        # Debug, get random user
        # active_user = user_manager.get_random_user()

        # Create a temporary user

        mws.run_interaction(action_manager.record_user)
        status = action_manager.check_status()
        if (status != "failure"):
            if (status == "vocal"):
                alevel = 0
            else:
                alevel = 1
        else:
            print("[INFO] Routine canceled during modality selection")
            mws.run_interaction(action_manager.failure)
            exit(1)

            # continue

        mws.run_interaction(action_manager.ask_language)
        status = action_manager.check_status()
        print("[INFO] Status: " + status)
        if (status != "failure"):
            if (status == "english"):
                language = "en"
            else:
                language = "it"
        else:
            print("[INFO] Routine canceled during language selection")
            mws.run_interaction(action_manager.failure)
            exit(1)
            # continue

        active_user = User(len(user_manager.users), "", alevel, language)

    else:
        # User in db
        active_user = user_manager.find_user_by_id(args.uid)
    print('[INFO] Active user: ' + active_user.username)

    language = active_user.lang
    alevel = active_user.alevel

    # Set the language profile
    if language == "en":
        mws.run_interaction(action_manager.set_profile_en)
    elif language == "it":
        mws.run_interaction(action_manager.set_profile_it)
    else:
        raise ValueError("Invalid language: " + language)

    # Create custom greeting action file
    action_manager.create_custom_greeting(active_user.username, alevel)

    # Ask for help
    if alevel == 0:  # Blindness

        mws.run_interaction(action_manager.custom_greeting)
        time.sleep(2)
        mws.run_interaction(action_manager.blind_ask_help)

        status = action_manager.check_status()
        print('[INFO] User response: ' + status)
        if status != "failure":
            print("[INFO] Blind help procedure starting")
            # status could be 'A', ..., 'E', or something else. The room mapper will tell if it is a valid room
            guide_me(active_user, args.current_room, status, mws, action_manager, positionManager, wtime=args.wtime)
        else:
            print("[INFO] Blind help procedure aborted")
            time.sleep(10)
            # continue

    elif alevel == 1:  # Deafness

        mws.run_interaction(action_manager.custom_greeting)
        time.sleep(2)
        mws.run_interaction(action_manager.deaf_ask_help)

        status = action_manager.check_status()
        print('[INFO] User response: ' + status)
        if status == "yes":
            print("[INFO] Deaf help procedure starting")
            guide_me(active_user, args.current_room, status, mws, action_manager, positionManager, wtime=args.wtime)
        else:
            print("[INFO] Deaf help procedure aborted")
            time.sleep(10)
            # continue

    app.run()