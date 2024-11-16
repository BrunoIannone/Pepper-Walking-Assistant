import math
import threading
from datetime import datetime

from demo.scripts.src.automaton.automaton import TimeoutState


class MovementTimeoutState(TimeoutState):
    def __init__(self, automaton):
        super(MovementTimeoutState, self).__init__(
            'movement_state',
            automaton,
            timeout=10,
            timeout_event='node_reached'
        )
        self.start_time = None
        self.remaining_time = None
        self.movement_timer = None
        self.distance = None

    def initialize_movement(self, distance):
        """Initialize or update movement parameters for a new segment"""
        velocity = self.automaton.action_manager.lin_vel
        self.distance = distance
        self.remaining_time = abs(distance / velocity) if distance else 10
        self.timeout = self.remaining_time

    def on_enter(self):
        if self.movement_timer:
            self.movement_timer.cancel()
            self.movement_timer = None

        print("Starting/Resuming movement with remaining time:", self.remaining_time)
        self.start_time = datetime.now()
        self.automaton.action_manager.set_speed(self.remaining_time)

        self.movement_timer = threading.Timer(self.remaining_time, self._on_timeout)
        self.movement_timer.start()

    def on_event(self, event):
        super(MovementTimeoutState, self).on_event(event)

        if event == 'hand_released':
            elapsed = (datetime.now() - self.start_time).total_seconds()
            self.remaining_time = max(0, self.remaining_time - elapsed)

            self.automaton.action_manager.stop_motion()
            if self.movement_timer:
                self.movement_timer.cancel()
                self.movement_timer = None

            print("Movement interrupted. Remaining time:", self.remaining_time)
            self.automaton.change_state('ask_state')

        elif event == 'node_reached':
            print("Node reached")

            if self.movement_timer:
                self.movement_timer.cancel()
                self.movement_timer = None

            next_target = self.automaton.position_manager.get_next_target()
            if next_target is None:
                print("Path completed")
                self.automaton.change_state('quit_state')
            else:
                current_x, current_y, theta = self.automaton.action_manager.mo_service.getRobotPosition(True)
                next_distance = math.sqrt(
                    (next_target.x - current_x) ** 2 +
                    (next_target.y - current_y) ** 2
                )

                self.initialize_movement(next_distance)
                self.automaton.change_state('movement_state')

    def _on_timeout(self):
        self.automaton.on_event('node_reached')

    def __del__(self):
        if self.movement_timer:
            self.movement_timer.cancel()
            self.movement_timer = None