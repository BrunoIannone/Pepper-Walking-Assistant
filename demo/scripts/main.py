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
from src.users.user import User

from src.guide_me import guide_me
from src.utils.paths import get_path


def is_file_empty(file_path):
    try:
        return os.path.isfile(file_path) and os.path.getsize(file_path) == 0
    except Exception as e:
        print("An error occurred: " + str(e))
        return False


if __name__ == "__main__":

    # ----------------------------- Argument parsing ----------------------------- #
    parser = argparse.ArgumentParser()
    parser.add_argument("--pip", type=str, default=os.environ['PEPPER_IP'],
                        help="Robot IP address.  On robot or Local Naoqi: use '127.0.0.1'.")
    parser.add_argument("--pport", type=int, default=9559,
                        help="Naoqi port number")
    parser.add_argument("--current_room", type=str, default="Lobby",
                        help="ID of the room you are currently in")
    parser.add_argument("--target_room", type=str, default="Office",
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

    map_path = get_path("static/maps/map.txt")
    position_manager = PositionManager(map_path)

    users_database_path = get_path("static/users/users.txt")
    print("[INFO] Restoring users from: " + users_database_path)
    user_manager = UserManager.load(users_database_path)

    print("[INFO] Users database:")
    for user in user_manager.users:
        print("[INFO] \t" + str(user))

    if args.uid not in user_manager:

        mws.run_interaction(action_manager.interaction_register_user)

        file_path = "/home/robot/playground/outcome.txt"
        while is_file_empty(file_path):
            time.sleep(0.01)

        # Take the content of the file
        user_data = ""
        with open(file_path, "r") as file:
            lines = file.readlines()
            if len(lines) > 0:
                user_data = lines[0]
        print("[INFO] User data: " + user_data)

        user_tokens = user_data.split()
        if len(user_tokens) > 1:
            alevel = user_tokens[0]
            language = user_tokens[1]
            active_user = User(len(user_manager.users), "Unknown", alevel, language)
            print('[INFO] User created: ' + str(active_user))

            # Dump the new user to file
            user_manager.add_user(active_user)
            user_manager.dump(users_database_path)
            print("[INFO] New user " + active_user.username + " added to the database.")

        else:
            print("[INFO] Unable to create user: invalid data")
            exit(1)

    else:

        # User in db
        active_user = user_manager.find_user_by_id(args.uid)

    print('[INFO] Active user: ' + active_user.username)

    # Set the language profile
    if active_user.lang == "en":
        mws.run_interaction(action_manager.set_profile_en)
    elif active_user.lang == "it":
        mws.run_interaction(action_manager.set_profile_it)
    else:
        raise ValueError("Invalid language: " + active_user.lang)

    # Create custom greeting action file
    action_manager.create_custom_greeting(active_user.username, active_user.disability)
    print("[INFO] Created custom greeting for user " + active_user.username)

    # Call the greeting
    mws.run_interaction(action_manager.custom_greeting)

    if active_user.disability == "blind":
        mws.run_interaction(action_manager.interaction_blind_assist)
    elif active_user.disability == "deaf":
        mws.run_interaction(action_manager.interaction_deaf_assist)
    else:
        raise ValueError("Invalid disability: " + active_user.disability)

    file_path = '/home/robot/playground/outcome.txt'
    while is_file_empty(file_path):
        time.sleep(0.01)

    # Take the content of the file
    dest = ""
    with open(file_path, "r") as file:
        lines = file.readlines()
        dest = lines[0]
    print("[INFO] User replied: " + dest)

    if dest == 'failure':
        print('[INFO] Help procedure aborted')
        exit(1)

    else:

        """
        # Disable security
        action_manager.mo_service.setExternalCollisionProtectionEnabled("All", False)

        guide_me(active_user, args.current_room, dest, mws, action_manager, position_manager, wtime=args.wtime)
        """

# TODO Bruno > check if relevant
# TODO Daniel & Iacopo > yes, totally relevant
app.run()
