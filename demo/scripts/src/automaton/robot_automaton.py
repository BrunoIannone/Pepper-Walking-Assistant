import math
import threading

from automaton import TimeoutState, State, FiniteStateAutomaton
from ..utils.limits import joint_limits
from ..utils.postures import default_posture
import time


# ---------------------------------- States ---------------------------------- #

class SteadyState(TimeoutState):

    def __init__(self, automaton):
        super(SteadyState, self).__init__('steady_state', automaton, timeout=automaton.timeout, timeout_event='time_elapsed')

    def on_enter(self):
        super(SteadyState, self).on_enter()
        print("[INFO] Entering Steady State")

        self.automaton.perform_movement(joint_values=default_posture)
        print('[INFO] Resetting posture')

        self.automaton.instruct()
        print('[INFO] Giving blind/deaf instructions on how to start')

    def on_event(self, event):
        super(SteadyState, self).on_event(event)
        if event == 'head_touched':
            self.automaton.change_state('moving_state')
        elif event == 'time_elapsed':
            self.automaton.change_state('quit_state')



class GoalState(TimeoutState):

    def __init__(self, automaton):
        super(GoalState, self).__init__('goal_state', automaton, timeout=3, timeout_event='time_elapsed')

    def on_enter(self):
        super(GoalState, self).on_enter()
        print('[INFO] Entering Goal State')

        # Signaling the user it should step back
        if self.automaton.disability == "blind":
            self.automaton.modim_web_server.run_interaction(self.automaton.action_manager.blind_goal)
        else:
            self.automaton.modim_web_server.run_interaction(self.automaton.action_manager.deaf_goal)
        print('[INFO] Signaling the user we reached the goal')

    def on_event(self, event):
        super(GoalState, self).on_event(event)
        if event == 'time_elapsed':
            self.automaton.change_state('quit_state')

class QuitState(State):

    def __init__(self, automaton):
        super(QuitState, self).__init__('quit_state', automaton)

    def on_enter(self):
        super(QuitState, self).on_enter()
        print('[INFO] Entering Quit State')

        # Go back to default position
        self.automaton.perform_movement(joint_values=default_posture)
        print('[INFO] Resetting posture')

        # Signaling the user it should step back
        if self.automaton.disability == "blind":
            self.automaton.modim_web_server.run_interaction(self.automaton.action_manager.blind_disagree)
        else:
            self.automaton.modim_web_server.run_interaction(self.automaton.action_manager.deaf_disagree)
        print('[INFO] Signaling the user it should step back')

        self.automaton.release_resources()
        print('[INFO] Releasing resources')

        print("[INFO] Done")
        exit(1)

    def on_event(self, event):
        super(QuitState, self)

class HoldHandState(TimeoutState):

    def __init__(self, automaton):
        super(HoldHandState, self).__init__('hold_hand_state', automaton, timeout=automaton.timeout, timeout_event='time_elapsed')

    def on_enter(self):
        super(HoldHandState, self).on_enter()
        print('[INFO] Entering Hold Hand State')

        # Behavior

        self.automaton.instruct()
        print('[INFO] Giving blind/deaf instructions on how to start')

    def on_event(self, event):
        super(HoldHandState, self).on_event(event)
        if event == 'head_touched':
            self.automaton.change_state('moving_state')
        elif event == 'time_elapsed':
            self.automaton.change_state('quit_state')


class AskState(TimeoutState):

    def __init__(self, automaton):
        super(AskState, self).__init__('ask_state', automaton, timeout=automaton.timeout, timeout_event='steady_state')

    def on_enter(self):
        super(AskState, self).on_enter()
        print("[INFO] Entering Ask State")

        if self.automaton.disability == "blind":
            self.automaton.modim_web_server.run_interaction(self.automaton.action_manager.blind_ask_cancel)
            print('[INFO] Asking the user if he wants to cancel the procedure')
        elif self.automaton.disability == "deaf":
            self.automaton.modim_web_server.run_interaction(self.automaton.action_manager.deaf_ask_cancel)
            print('[INFO] Showing buttons for the user to choose if he wants to cancel the procedure')

        result = self.automaton.action_manager.check_status()
        print('[INFO] Obtained response: ' + result)
        self.automaton.on_event(result)  # Can be 'result_yes' or 'result_no'

    def on_event(self, event):
        super(AskState, self).on_event(event)
        if event == 'result_yes':
            self.automaton.change_state('quit_state')
        elif event == 'result_no':
            self.automaton.change_state('hold_hand_state')
        elif event == 'head_touched':
            self.automaton.change_state('moving_state')
        elif event == 'time_elapsed':
            self.automaton.change_state('quit_state')


class RobotAutomaton(FiniteStateAutomaton):

    def __init__(self,
                 modim_web_server,
                 action_manager,
                 position_manager,
                 disability=0,
                 timeout=60,
                 default_lin_vel=0.15
                 ):
        super(RobotAutomaton, self).__init__()
        self.modim_web_server = modim_web_server
        self.action_manager = action_manager
        self.position_manager = position_manager
        self.disability = disability
        self.timeout = timeout
        self.default_lin_vel = default_lin_vel

        # Connect the touch event to the automata
        touch_event = "MiddleTactilTouched"
        self.touch_subscriber = self.action_manager.me_service.subscriber(touch_event)
        self.touch_id = self.touch_subscriber.signal.connect(self.on_head_touch_change)

    # ----------------------------- Utility functions ---------------------------- #

    def on_head_touch_change(self, value):
        """
        Callback function triggered when the head touch event occurs.
        Dispatch the event to the automata.
        """
        print("[INFO] Head touch value changed: " + str(value))
        if value == 0.0:
            self.on_event('head_released')
        else:
            self.on_event('head_touched')

    def perform_animation(self, animation, _async=True):
        """
        Perform a predefined animation. The animation should be visible by the behavior_manager 
        among the installed behaviors, otherwise it is silently discarded 
        """
        behaviors = self.action_manager.bm_service.getInstalledBehaviors()

        if animation in behaviors:
            self.action_manager.ap_service.run(animation, _async=_async)

    def perform_movement(self, joint_values, speed=1.0, _async=True):
        """
        Perform the motion specified by the provided joint values. Joint values
        should be in the allowed range, otherwise the value is silently discarded
        """

        # Enable stiffness
        # self.action_manager.mo_service.setStiffnesses(["LArm", "RArm"], 1.0)

        # Perform movement
        for joint_name, joint_value in joint_values.items():
            if joint_limits[joint_name][0] <= joint_value <= joint_limits[joint_name][1]:
                self.action_manager.mo_service.setAngles(joint_name, joint_value, speed, _async=_async)

        time.sleep(2)

        # Disable arm stiffness during walking
        # self.action_manager.mo_service.setStiffnesses(["LArm", "RArm"], 0.5)

    def instruct(self):
        """
        Give instructions on how to start to the user. Instructions can be shown on the tablet (deaf user) 
        or said by the robot (blind user)
        """
        print("[INFO] Instructing (" + self.disability + ") user")
        if self.disability == "blind":
            self.modim_web_server.run_interaction(self.action_manager.blind_walk_hold_head)
        else:
            self.modim_web_server.run_interaction(self.action_manager.deaf_walk_hold_head)
    
    def release_resources(self):
        self.touch_subscriber.signal.disconnect(self.touch_id)

def create_automaton(modim_web_server, action_manager, position_manager, **kwargs):

    automaton = RobotAutomaton(
        modim_web_server,
        action_manager,
        position_manager,
        **kwargs
    )

    # Define and add states to the automaton
    steady_state = SteadyState(automaton)
    moving_state = MovingState(automaton)
    ask_state = AskState(automaton)
    hold_hand_state = HoldHandState(automaton)
    goal_state = GoalState(automaton)
    quit_state = QuitState(automaton)

    for state in [steady_state, moving_state, ask_state, hold_hand_state, goal_state, quit_state]:
        automaton.add_state(state)

    return automaton
