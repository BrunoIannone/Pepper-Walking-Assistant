import sys
import os
import argparse
import qi

try:
    sys.path.insert(0, os.getenv('MODIM_HOME') + '/src/GUI')
except Exception as e:
    print("Please set MODIM_HOME environment variable to MODIM folder.")
    sys.exit(1)

# Set MODIM_IP to connnect to remote MODIM server

from ws_client import *

from src.automaton.robot_automaton import create_automaton
from src.actions.position_manager import PositionManager
from src.actions.action_manager import ActionManager
from src.users.user_manager import UserManager
from src.utils.paths import get_path
from src.users.user import User


if __name__ == "__main__":

    # ----------------------------- Argument parsing ----------------------------- #
    parser = argparse.ArgumentParser()
    parser.add_argument("--pip", type=str, default=os.environ['PEPPER_IP'],
                        help="Robot IP address.  On robot or Local Naoqi: use '127.0.0.1'.")
    parser.add_argument("--pport", type=int, default=9559,
                        help="Naoqi port number")
    parser.add_argument("--current_room", type=str, default="Lobby",
                        help="ID of the room you are currently in")
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

        user_data = action_manager.check_status()
        print("[INFO] User data: " + user_data)

        user_tokens = user_data.split()
        if len(user_tokens) > 1:
            alevel = user_tokens[0]
            language = user_tokens[1]
            active_user = User(len(user_manager.users), "", alevel, language)
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

    result = action_manager.check_status()
    if result == 'failure':
        print('[INFO] Help procedure aborted')

        if active_user.disability == "blind":
            mws.run_interaction(action_manager.blind_disagree)
        else:
            mws.run_interaction(action_manager.deaf_disagree)

        mws.run_interaction(action_manager.failure)

        exit(1)

    else:

        # Disable security
        # action_manager.disable_security_features()

        current_room = args.current_room
        target_room = result

        # Check if the destination is a valid room
        if not position_manager.is_valid(current_room):
            print("[ERROR] Invalid current room: " + current_room)
            exit(1)
        if not position_manager.is_valid(target_room):
            print("[ERROR] Invalid target room: " + target_room)
            exit(1)

        print("[INFO] Current room: " + current_room)
        print("[INFO] Target room: " + target_room)

        # Check if we are in the target room
        if current_room == target_room:
            print("[INFO] We already are in the target room: " + current_room)
            exit(1)

        # Go on guiding the user to the target

        path = position_manager.compute_path(current_room, target_room, active_user.disability)

        # No route to target room
        if len(path) == 0:

            print("[INFO] No route to " + target_room)

            if active_user.disability == "blind":  # Blindness
                mws.run_interaction(action_manager.blind_ask_call)
            else:  # Deafness
                mws.run_interaction(action_manager.deaf_ask_call)

            status = action_manager.check_status()
            if status != "failure":
                print("[INFO] Performing call to room " + target_room)

                if active_user.disability == "blind":
                    mws.run_interaction(action_manager.blind_call)
                else:
                    mws.run_interaction(action_manager.deaf_call)

            else:
                print("[INFO] User declined the call.")

                if active_user.disability == "blind":
                    mws.run_interaction(action_manager.blind_disagree)
                else:
                    mws.run_interaction(action_manager.deaf_disagree)

                mws.run_interaction(action_manager.failure)
                exit(1)

        else:

            print("[INFO] Route to " + target_room + ":")
            print("[INFO] " + " -> ".join([room.name for room in path]))

            # Create the automaton
            robot_automaton = create_automaton(
                mws,
                action_manager,
                position_manager,
                timeout=args.wtime,
                disability=active_user.disability
            )

            # Start
            robot_automaton.start('steady_state')

app.run()
