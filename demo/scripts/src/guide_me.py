import os
import argparse
from map.room_mapper import RoomMapper
from users.user_manager import UserManager
from utils.paths import get_path
from automaton.automaton import FiniteStateAutomaton
from automaton.robot_automaton import RobotAutomaton, create_automaton
from actions.action_manager import ActionManager


def guide_me(user, path, modim_web_server, action_manager, wtime=10):

    # Use the first node of the path to establish which hand to raise
    first_room = path[0]  # Node
    first_x = first_room.x
    arm_picked = 'Right' if first_x < 0 else 'Left'
    print("[INFO] Selected " + arm_picked.lower() + " hand to raise")

    # Create the automaton
    robot_automaton = create_automaton(modim_web_server, action_manager, wtime=wtime, arm=arm_picked, alevel=user.alevel)


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
    guide_me(active_user, path_nodes, None, action_manager)
