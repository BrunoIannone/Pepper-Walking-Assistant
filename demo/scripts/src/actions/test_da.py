import math
import threading
from datetime import datetime

from demo.scripts.src.automaton.automaton import TimeoutState


class MovementTimeoutState(TimeoutState):

    def __init__(self, automaton):

        self.current_room_index = 0
        self.current_room = automaton.position_manager.path[self.current_room_index]
        self.next_room = automaton.position_manager.path[self.current_room_index + 1]
        self.distance = self.current_room.distance(self.next_room)

        # The automaton.action_manager controls the movement (among other actions) and
        # it knows the velocity of the robot
        # velocity = space / time
        # time = space / velocity
        self.total_time = self.distance / automaton.action_manager.default_lin_vel

        super(MovementTimeoutState, self).__init__(
            'moving_state',
            automaton,
            timeout=self.total_time,
            timeout_event='node_reached'
        )

    def on_enter(self):
        super(MovementTimeoutState, self).on_enter()

        # TODO for now, suppose only linear motion

        time_now = datetime.now()
        delta_time = self.total_time - time_now
        self.automaton.action_manager.set_speed(delta_time)

    def on_event(self, event):
        super(MovementTimeoutState, self).on_event(event)

        # Stop the motion
        self.automaton.action_manager.stop_motion()

        if event == 'hand_released':
            self.automaton.change_state('ask_state')
        elif event == 'node_reached':

            # Take next node
            self.current_room = self.next_room
            self.current_room_index += 1
            self.next_room = self.automaton.position_manager.path[self.current_room_index]



            if self.current_room is None:
                self.automaton.change_state('moving_state')

        elif event == 'goal_reached':
            self.automaton.change_state('quit_state')
