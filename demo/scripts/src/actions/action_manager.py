import os
import time


class ActionManager:

    def __init__(self, session):

        # Set session and services
        self.session = session
        self.as_service = session.service("ALAnimatedSpeech")
        self.bm_service = session.service("ALBehaviorManager")
        self.ap_service = session.service("ALAnimationPlayer")
        self.mo_service = session.service("ALMotion")
        self.me_service = session.service("ALMemory")

        # Linear and angular velocities
        self.default_lin_vel = 0.15

    def recognized_user(self):
        return True

    def get_actions_path(self):
        return os.path.join(os.path.dirname(os.path.realpath(__file__)), "../../../actions/")

    def create_custom_greeting(self, user_name, disability):
        with open(os.path.join(self.get_actions_path(), "custom_greeting"), "w") as file:

            if disability == "blind":  # Blind
                contenuto = """IMAGE
                    <*, *, *, *>:  img/hello.png
                    ----
                    TEXT
                    <*,*,it,*>: Accogliendo l'utente... {0}
                    <*,*,*,*>:  Welcoming the user... {0}
                    ----
                    TTS
                    <*,*,it,*>: Ciao! Benvenuto {0}
                    <*,*,*,*>:  Hello! Welcome {0}
                    ----""".format(user_name)

            else:  # Deaf
                contenuto = """IMAGE
                    <*, *, *, *>:  img/hello.png
                    ----
                    TEXT
                    <*,*,it,*>: Benvenuto {0}
                    <*,*,*,*>:  Welcome {0}
                    ----
                    GESTURE
                    <*,*,*,*>: animations/Stand/Gestures/Hey_1
                    ----""".format(user_name)

            file.write(contenuto)

    def check_status(self):
        with open("/home/robot/playground/outcome.txt", "r") as file:
            status = file.readline().strip()
        return str(status).strip()

    def set_profile_en(self):
        im.setProfile(['*', '*', '*', '*'])

    def set_profile_it(self):
        # im.init()
        im.setProfile(['*', '*', 'it', '*'])

    def custom_greeting(self):
        im.execute("custom_greeting")
        time.sleep(2)

    def interaction_register_user(self):

        # Default values
        line = ""

        modality = im.ask("record_user", timeout=999)
        if modality == "touch":
            line += "deaf"
        elif modality == "vocal":
            line += "blind"
        else:
            line = "failure"

        language = im.ask("ask_language", timeout=999)
        if language == "failure":
            line = "failure"
        else:
            line += (" " + language)

        with open('/home/robot/playground/outcome.txt', 'w') as file:
            file.write(line)

    # ----------------------------- Blind interaction ---------------------------- #

    def interaction_blind_assist(self):
        user_response = im.ask('blind_ask_help', timeout=999)
        if user_response == 'yes':
            dest = im.ask('blind_agree', timeout=999)
            with open('/home/robot/playground/outcome.txt', 'w') as file:
                file.write(dest)
        else:
            with open('/home/robot/playground/outcome.txt', 'w') as file:
                file.write('failure')

    def blind_agree(self):
        q = im.ask('blind_agree', timeout=999)
        with open("/home/robot/playground/outcome.txt", "w") as file:
            file.write(q)

    def blind_disagree(self):
        im.execute('blind_disagree')
        time.sleep(2)

    def blind_ask_cancel(self):
        q = im.ask('blind_ask_cancel', timeout=999)
        with open("/home/robot/playground/outcome.txt","w") as file:
            file.write(q)

    def blind_ask_call(self):
        q = im.ask('blind_ask_call', timeout=999)
        with open("/home/robot/playground/outcome.txt", "w") as file:
            file.write(q)
        time.sleep(2)

    # ----------------------------- Deaf interaction ----------------------------- #

    def interaction_deaf_assist(self):
        user_response = im.ask('deaf_ask_help', timeout=999)
        if user_response == 'yes':
            dest = im.ask('deaf_agree', timeout=999)
            with open('/home/robot/playground/outcome.txt', 'w') as file:
                file.write(dest)
        else:
            with open('/home/robot/playground/outcome.txt', 'w') as file:
                file.write('failure')

    def deaf_agree(self):
        q = im.ask('deaf_agree', timeout=999)
        with open("/home/robot/playground/outcome.txt", "w") as file:
            file.write(q)

    def deaf_disagree(self):
        im.execute('deaf_disagree')
        time.sleep(2)

    def deaf_ask_cancel(self):
        q = im.ask('deaf_ask_cancel', timeout=999)
        if q == 'yes':
            with open("/home/robot/playground/outcome.txt","w") as file:
                file.write('yes')
        else:
            with open("/home/robot/playground/outcome.txt","w") as file:
                file.write('failure')

    def deaf_ask_call(self):
        q = im.ask('deaf_ask_call', timeout=999)
        with open("/home/robot/playground/outcome.txt", "w") as file:
            file.write(q)
        time.sleep(2)

    # ---------------------------------- General --------------------------------- #

    def deaf_call(self):
        im.execute('deaf_call')
        time.sleep(10)

    def blind_call(self):
        im.execute('blind_call')
        time.sleep(10)

    def blind_walking(self):
        im.execute('blind_walking')

    def deaf_walking(self):
        im.execute('deaf_walking')

    def blind_goal(self):
        im.execute('blind_goal')

    def deaf_goal(self):
        im.execute('deaf_goal')

    def welcome(self):
        im.execute('welcome')

    def left_blind_walk_hold_hand(self):
        im.execute('left_blind_walk_hold_hand')

    def right_blind_walk_hold_hand(self):
        im.execute('right_blind_walk_hold_hand')

    def left_deaf_walk_hold_hand(self):
        im.execute('left_deaf_walk_hold_hand')

    def right_deaf_walk_hold_hand(self):
        im.execute('right_deaf_walk_hold_hand')

    def wait_for_human(self):
        stop_detection = False
        is_human_detected = False

        #Checking if human stay in front of Pepper more than 2 seconds
        im.robot.startSensorMonitor()
        while not stop_detection:
            while not is_human_detected:
                p = im.robot.sensorvalue()  #p is the array with data of all the sensors
                print("SENSOR VALUE " + p)
                is_human_detected = p[1] > 0.0 and p[1] < 1.0  #p[1] is the Front sonar
            if is_human_detected:
                print('*Person detected*')
                time.sleep(2)
                p = im.robot.sensorvalue()
                is_human_detected = p[1] > 0.0 and p[1] < 1.0
                if is_human_detected:
                    print('*Person still there*')
                    stop_detection = True
                else:
                    print('*Person gone*')
        im.robot.stopSensorMonitor()

    def failure(self):
        im.init()

    def record_user(self):
        modality = im.ask("record_user", timeout=999)
        print("MODALITY" + modality)
        with open("/home/robot/playground/outcome.txt","w") as file:
                file.write(str(modality).strip())

    def ask_language(self):
        modality = im.ask("ask_language", timeout=999)
        with open("/home/robot/playground/outcome.txt","w") as file:
                file.write(str(modality).strip())

    def stop_motion(self):
        try:
            self.mo_service.stopMove()
            current_x, current_y, _ = self.mo_service.getRobotPosition(True)
            print("[INFO] Motion stopped. Current position: ({}, {})".format(current_x, current_y))
        except Exception as e:
            print("[ERROR] Failed to stop motion: {}".format(e))
