from automaton import TimeoutState, State, FiniteStateAutomaton
from utils.limits import joint_limits
from utils.postures import default_posture, left_arm_raised, right_arm_raised
import math


# ---------------------------------- States ---------------------------------- #

class SteadyState(TimeoutState):

    def __init__(self, automaton, timeout=10):
        super(SteadyState, self).__init__('steady_state', automaton, timeout=timeout, timeout_event='time_elapsed')

    def on_enter(self):
        super(SteadyState, self).on_enter()
        print("[INFO] Entering Steady State")

        # Behavior

        self.automaton.perform_movement(joint_values=default_posture)
        print('[INFO] Resetting posture')

        self.automaton.instruct()
        print('[INFO] Giving blind/deaf instructions on how to start')

        self.automaton.perform_movement(joint_values=left_arm_raised if self.automaton.arm == 'Left' else right_arm_raised, speed=0.25)
        print("[INFO] Raising " + self.automaton.arm.lower() + " hand")

    def on_event(self, event):
        super(SteadyState, self).on_event(event)
        if event == 'hand_touched':
            self.automaton.change_state('moving_state')
        elif event == 'time_elapsed':
            self.automaton.change_state('quit_state')


class MovingState(State):

    def __init__(self, automaton):
        super(MovingState, self).__init__('moving_state', automaton)

    def on_enter(self):
        super(MovingState, self).on_enter()
        print('[INFO] Entering Moving State')

        # Behavior 

        self.automaton.show_walk_message()
        print('[INFO] Showing walking icon on screen')

        # TODO setup this
        global current_x, current_y
        global at_goal
        global node_index
        while not at_goal:
            print('[INFO] At goal status: {}'.format(at_goal))
            print('[INFO] Node index: {}'.format(node_index))
            print('[INFO] Current target: {}'.format(coords[node_index]))
            current_target_x, current_target_y = coords[node_index]
            theta = math.atan2(current_target_y - current_y, current_target_x - current_x)
            print('[INFO] Current theta: {}'.format(theta))
            print('[INFO] Moving to: ' + str(current_target_x) + ', ' + str(current_target_y))
            success = move_to(current_target_x, current_target_y, theta)
            print('[INFO] Success state for {}: {}'.format(node_index, success))
            if success:
                node_index += 1
            if node_index == len(coords):
                print('[INFO] Success in exit if')
                at_goal = True

        print('[INFO] Success Exited from while loop')

    # TODO setup this
    def on_event(self, event):
        super(MovingState, self).on_event(event)
        if event == 'hand_released':
            stop_motion()
            self.automaton.change_state('ask_state')


class QuitState(State):

    def __init__(self, automaton):
        super(QuitState, self).__init__('quit_state', automaton)

    def on_enter(self):
        super(QuitState, self).on_enter()
        print('[INFO] Entering Quit State')

        # Go back to default position
        self.automaton.perform_movement(joint_values=default_posture)
        print('[INFO] Resetting posture')

        # Unsubscribe from signals
        # global touch_subscriber, word_subscriber, sr_service
        # sr_service.unsubscribe("pepper_walking_assistant_ASR")
        # word_subscriber.signal.disconnect()
        # touch_subscriber.signal.disconnect()

        self.automaton.release_resources()
        print('[INFO] Releasing resources')

        print("[INFO] Done")


class HoldHandState(TimeoutState):

    def __init__(self, automaton, timeout=10):
        super(HoldHandState, self).__init__('hold_hand_state', automaton, timeout=timeout, timeout_event='time_elapsed')

    def on_enter(self):
        super(HoldHandState, self).on_enter()
        print('[INFO] Entering Hold Hand State')

        # Behavior

        self.automaton.instruct()
        print('[INFO] Giving blind/deaf instructions on how to start')

    def on_event(self, event):
        super(HoldHandState, self).on_event(event)
        if event == 'hand_touched':
            self.automaton.change_state('moving_state')
        elif event == 'time_elapsed':
            self.automaton.change_state('quit_state')


class AskState(TimeoutState):

    def __init__(self, automaton, timeout=10, alevel=0):
        super(AskState, self).__init__('ask_state', automaton, timeout=timeout, timeout_event='steady_state')
        self.alevel = alevel

    def on_enter(self):
        super(AskState, self).on_enter()
        print("[INFO] Entering Ask State")

        # Behavior

        self.automaton.ask_cancel()
        print('[INFO] Asking the user if he wants to cancel the procedure')

        result = self.automaton.action_manager.check_status()
        print('[INFO] Obtained response: ' + result)
        self.automaton.on_event(result)  # Can be 'result_yes' or 'result_no'

    def on_event(self, event):
        super(AskState, self).on_event(event)
        if event == 'response_yes':
            self.automaton.change_state('quit_state')
        elif event == 'response_no':
            self.automaton.change_state('hold_hand_state')
        elif event == 'hand_touched':
            self.automaton.change_state('moving_state')
        elif event == 'time_elapsed':
            self.automaton.change_state('quit_state')


class RobotAutomaton(FiniteStateAutomaton):

    def __init__(self, modim_web_server, action_manager, arm='Left', alevel=0):
        super(RobotAutomaton, self).__init__()
        self.modim_web_server = modim_web_server
        self.action_manager = action_manager
        self.arm = arm
        self.alevel = alevel

        # Connect the touch event to the automata
        touch_event = "Hand" + arm + "BackTouched"
        touch_subscriber = self.action_manager.me_service.subscriber(touch_event)
        touch_subscriber.signal.connect(self.on_hand_touch_change)

    # ----------------------------- Utility functions ---------------------------- #

    def on_hand_touch_change(self, value):
        """
        Callback function triggered when the hand touch event occurs.
        Dispatch the event to the automata.
        """
        print("[INFO] Hand touch value changed: " + str(value))
        if value == 0.0:
            self.on_event('hand_released')
        else:
            self.on_event('hand_touched')

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
        self.action_manager.mo_service.setStiffnesses('Body', 1.0)

        for joint_name, joint_value in joint_values.items():
            if joint_limits[joint_name][0] <= joint_value <= joint_limits[joint_name][1]:
                self.action_manager.mo_service.setAngles(joint_name, joint_value, speed, _async=_async)

    def instruct(self):
        """
        Give instructions on how to start to the user. Instructions can be shown on the tablet (deaf user) 
        or said by the robot (blind user)
        """
        if self.alevel == 0:  # Blindness
            if self.arm == 'Left':
                self.modim_web_server.run_interaction(self.action_manager.left_deaf_walk_handle)
            else:
                self.modim_web_server.run_interaction(self.action_manager.right_deaf_walk_handle)
        elif self.alevel == 1:
            if self.arm == 'Left':
                self.modim_web_server.run_interaction(self.action_manager.left_blind_walk_handle)
            else:
                self.modim_web_server.run_interaction(self.action_manager.right_blind_walk_handle)

    def show_walk_message(self):
        """
        Show the walking icon on screen
        """
        self.modim_web_server.run_interaction(self.action_manager.walking)

    def ask_cancel(self):
        """
        Ask the user if he wants to cancel the procedure
        """
        if self.alevel == 0:  # Blindness
            self.modim_web_server.run_interaction(self.action_manager.blind_ask_cancel)
        elif self.alevel == 1:
            self.modim_web_server.run_interaction(self.action_manager.deaf_ask_cancel)


def create_automaton(modimWebServer, actionManager, wtime=10, arm='Left', alevel=0):

    automaton = RobotAutomaton(modimWebServer, actionManager, arm=arm, alevel=alevel)

    # Define and add states to the automaton
    steady_state = SteadyState(automaton, timeout=wtime)
    moving_state = MovingState(automaton)
    ask_state = AskState(automaton, timeout=wtime)
    hold_hand_state = HoldHandState(automaton, timeout=wtime)
    quit_state = QuitState(automaton)

    for state in [steady_state, moving_state, ask_state, hold_hand_state, quit_state]:
        automaton.add_state(state)

    # automaton.start('steady_state')

    return automaton
