import threading


class State(object):

    def __init__(self, name, automaton):
        self.name = name
        self.automaton = automaton

    def on_enter(self):
        """
        Called when the state is entered.
        """
        pass
    
    def on_event(self, event):
        """
        Handle events that are passed to the state. 
        Returns the next state or itself if no transition occurs.
        """
        pass

    def __str__(self):
        return self.name
    

class TimeoutState(State):

    def __init__(self, name, automaton, timeout=None, timeout_event=None):
        super(TimeoutState, self).__init__(name, automaton)
        self.timeout = timeout
        self.timeout_event = timeout_event
        self.timer = None

    def on_enter(self):
        if self.timeout and self.timeout_event:
            self.start_timer()

    def start_timer(self):
        """
        Start a timer to automatically trigger an event after a timeout.
        """
        self.timer = threading.Timer(self.timeout, self.trigger_timeout_event)
        self.timer.start()

    def trigger_timeout_event(self):
        """
        Trigger the timeout event if no other event occurs.
        """
        self.automaton.on_event(self.timeout_event)

    def on_event(self, event):
        
        # Cancel the timer to avoid firing the timout event
        self.cancel_timer()

        # Handle the event received
        # ...

    def cancel_timer(self):
        """
        Cancel the timeout timer if an event is received.
        """
        if self.timer:
            self.timer.cancel()
            self.timer = None

class FiniteStateAutomaton:
    def __init__(self):
        self.states = {}
        self.current_state = None

    def add_state(self, state):
        self.states[state.name] = state

    def start(self, state_name):
        if state_name not in self.states:
            raise ValueError("State '" + state_name + "' does not exist.")            
        self.current_state = self.states[state_name]
        self.current_state.on_enter()

    def change_state(self, state_name):
        if state_name in self.states:
            self.current_state = self.states[state_name]
            self.current_state.on_enter()
        else:
            raise ValueError("State '" + state_name + "' does not exist.")

    def on_event(self, event):
        if self.current_state is None:
            raise ValueError("Automaton has not been initialized yet.")
        self.current_state.on_event(event)
