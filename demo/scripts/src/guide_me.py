from automaton.robot_automaton import create_automaton
import time


def guide_me(user, current_room, target_room, modim_web_server, action_manager, position_manager, wtime=10):

    # Check if the destination is a valid room
    if not position_manager.is_valid(current_room):
        print("[ERROR] Invalid current room: " + current_room)
        exit(1)
    if not position_manager.is_valid(target_room):
        print("[ERROR] Invalid target room: " + target_room)
        exit(1)

    print("[INFO] Going from " + current_room + " to " + target_room)

    path = position_manager.compute_path(current_room, target_room, user.alevel)

    if len(path) == 0:
        print("[INFO] No route to " + target_room)
        if user.alevel == 0:    # Blindness
            modim_web_server.run_interaction(action_manager.blind_ask_call)
        else:                   # Deafness
            modim_web_server.run_interaction(action_manager.deaf_ask_call)
        time.sleep(2)

        status = action_manager.check_status()
        if status != "failure":
            print("[INFO] Performing call to room " + target_room)

            if user.alevel == 0:
                modim_web_server.run_interaction(action_manager.blind_call)
            else:
                modim_web_server.run_interaction(action_manager.deaf_call)
            time.sleep(2)

    else:
        print("[INFO] Route to " + target_room + " found: " + str(path))

        # Use the first node of the path to establish which hand to raise
        first_room = path[0]
        arm_picked = 'Right' if first_room.x < 0 else 'Left'
        print("[INFO] Selected " + arm_picked.lower() + " hand to raise")

        # Create the automaton
        robot_automaton = create_automaton(modim_web_server, action_manager, position_manager, wtime=wtime, arm=arm_picked,
                                           alevel=user.alevel)

        # Start
        robot_automaton.start('steady_state')
