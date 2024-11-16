from automaton import TimeoutState, State, FiniteStateAutomaton
from ..utils.limits import joint_limits
from ..utils.postures import default_posture, left_arm_raised, right_arm_raised
import time


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
        if self.automaton.alevel == 0:
            self.automaton.modim_web_server.run_interaction(self.automaton.action_manager.blind_walking)
            print('[INFO] Telling the user we are about to start walking')
        else:
            self.automaton.modim_web_server.run_interaction(self.automaton.action_manager.deaf_walking)
            print('[INFO] Showing walking icon on screen')
        time.sleep(2)

        while not self.automaton.position_manager.is_path_complete():
            next_target = self.automaton.position_manager.get_next_target()
            if next_target is None:
                print('[INFO] Path completed')
                break

            target_x, target_y = next_target.x, next_target.y
            success = self.automaton.action_manager.move_to(target_x, target_y)

            # TODO remove delay
            time.sleep(0.5)

            if not success:
                print('[INFO] Failed to move to the next target')
                break

        print('[INFO] Reached the goal' if self.automaton.position_manager.is_path_complete()
              else '[INFO] Navigation interrupted')

        # Showing goal icon and telling the user he reached the goal
        if self.automaton.alevel == 0:
            self.automaton.modim_web_server.run_interaction(self.automaton.action_manager.blind_goal)
        else:
            self.automaton.modim_web_server.run_interaction(self.automaton.action_manager.deaf_goal)

    def on_event(self, event):
        super(MovingState, self).on_event(event)
        if event == 'hand_released':
            self.automaton.action_manager.stop_motion()
            self.automaton.change_state('ask_state')
        elif event == 'goal_reached':
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

    def __init__(self, automaton, timeout=10):
        super(AskState, self).__init__('ask_state', automaton, timeout=timeout, timeout_event='steady_state')

    def on_enter(self):
        super(AskState, self).on_enter()
        print("[INFO] Entering Ask State")

        # Behavior
        if self.automaton.alevel == 0:  # Blindness
            self.automaton.modim_web_server.run_interaction(self.automaton.action_manager.blind_ask_cancel)
            print('[INFO] Asking the user if he wants to cancel the procedure')
        elif self.automaton.alevel == 1:
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
        elif event == 'hand_touched':
            self.automaton.change_state('moving_state')
        elif event == 'time_elapsed':
            self.automaton.change_state('quit_state')


class RobotAutomaton(FiniteStateAutomaton):

    def __init__(self, modim_web_server, action_manager, position_manager, arm='Left', alevel=0):
        super(RobotAutomaton, self).__init__()
        self.modim_web_server = modim_web_server
        self.action_manager = action_manager
        self.position_manager = position_manager
        self.arm = arm
        self.alevel = alevel

        # Connect the touch event to the automata
        touch_event = "Hand" + arm + "BackTouched"
        self.touch_subscriber = self.action_manager.me_service.subscriber(touch_event)
        self.touch_subscriber.signal.connect(self.on_hand_touch_change)

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
                print('[INFO] Instructing user with alevel=0 arm=Left')
                self.modim_web_server.run_interaction(self.action_manager.left_blind_walk_hold_hand)
            else:
                print('[INFO] Instructing user with alevel=0 arm=Right')
                self.modim_web_server.run_interaction(self.action_manager.right_blind_walk_hold_hand)
        elif self.alevel == 1:
            if self.arm == 'Left':
                print('[INFO] Instructing user with alevel=1 arm=Left')
                self.modim_web_server.run_interaction(self.action_manager.left_deaf_walk_hold_hand)
            else:
                print('[INFO] Instructing user with alevel=1 arm=Right')
                self.modim_web_server.run_interaction(self.action_manager.right_deaf_walk_hold_hand)
        time.sleep(2)
    
    def release_resources(self):
        # self.action_manager.touch_subscriber.signal.disconnect()
        pass


def create_automaton(modim_web_server, action_manager, position_manager, wtime=10, arm='Left', alevel=0):
    automaton = RobotAutomaton(modim_web_server, action_manager, position_manager, arm=arm, alevel=alevel)

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
