import os
import argparse

from actions.position_manager import PositionManager
from map.room_mapper import RoomMapper
from users.user_manager import UserManager
from utils.paths import get_path
from automaton.automaton import FiniteStateAutomaton
from automaton.robot_automaton import RobotAutomaton, create_automaton
from actions.action_manager import ActionManager


def guide_me(user, current_room, target_room, modim_web_server, action_manager, position_manager, wtime=10):

    path = position_manager.compute_path(current_room, target_room, user.alevel)

    if len(path) == 0:
        if user.alevel == 0:    # Blindness
            modim_web_server.run_interaction(action_manager.blind_ask_call)
        else:                   # Deafness
            modim_web_server.run_interaction(action_manager.deaf_ask_call)

        status = action_manager.check_status()
        if (status != "failure"):
            print("[INFO] Performing call to " + target_room + " room")
            modim_web_server.run_interaction(action_manager.call)

    # Use the first node of the path to establish which hand to raise
    first_room = path[0]
    arm_picked = 'Right' if first_room.x < 0 else 'Left'
    print("[INFO] Selected " + arm_picked.lower() + " hand to raise")
    
    # Create the automaton
    robot_automaton = create_automaton(modim_web_server, action_manager, position_manager, wtime=wtime, arm=arm_picked,
                                       alevel=user.alevel)

    # Start
    robot_automaton.start('steady_state')


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
    parser.add_argument("--wtime", type=int, default=60,
                        help='Number of seconds to wait with the hand raised before canceling the procedure')

    args = parser.parse_args()
    
    current_room = args.current_room
    target_room = args.target_room

    # ------------------------------ Action Manager ------------------------------ #

    action_manager = ActionManager()

    # ------------------------------- User Manager ------------------------------- #
    users_database_path = get_path('demo/static/users/users.txt')
    print("[INFO] Restoring users from: " + users_database_path)
    user_manager = UserManager.load(users_database_path)
    active_user = user_manager.get_random_user()
    print("[INFO] Active user        : " + str(active_user.username))
    
    # ------------------------------------ Map ----------------------------------- #
    map_path = get_path('demo/static/maps/map.txt')
    print("[INFO] Restoring map from : " + map_path)
    map = RoomMapper.from_file(map_path)
    distance, path = map.shortest_path(current_room, target_room, active_user.alevel)
    print("[INFO] Current room       : " + str(current_room))
    print("[INFO] Target room        : " + str(target_room))
    print("[INFO] Accessibility level: " + str(active_user.alevel))
    print("[INFO] Path               : " + str(path))

    # Take the respective node object for each element in the path (ids) (the nodes also contain the coordinates)
    path_nodes = [map.rooms[node] for node in path]

    # Start the procedure
    map_path = get_path('demo/static/maps/map.txt')
    print("[INFO] Restoring map from : " + map_path)
    position_manager = PositionManager(map_path)

    # Start the procedure
    guide_me(active_user, current_room, target_room, None, action_manager, position_manager, args.wtime)
