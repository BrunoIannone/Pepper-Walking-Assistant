import os
import math

class ActionManager:

    def __init__(self, session):

        # Set session and services
        self.session = session
        self.as_service = session.service("ALAnimatedSpeech")
        self.bm_service = session.service("ALBehaviorManager")
        self.ap_service = session.service("ALAnimationPlayer")
        self.mo_service = session.service("ALMotion")
        self.me_service = session.service("ALMemory")

        # Generate the actions
        self.generated_actions = []
        self.generate_robot_only_actions()

    def recognized_user(self):
        return True

    def get_actions_path(self):
        return os.path.join(os.path.dirname(os.path.realpath(__file__)), "../../../actions/")

    def create_custom_greeting(self, user_name, disability):
        with open(os.path.join(self.get_actions_path(), "custom_greeting"), "w") as file:

            if disability == 0:  # Blind
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
                    ----""".format((user_name))

            file.write(contenuto)

    def check_status(self):
        status = None
        with open(self.outcome_path, "r") as file:
            status = file.readline().strip()
        return str(status).strip()

    def generate_robot_only_actions(self, actions_path=None):
        """
        Generate the simple actions for which the robot does not expect a complex interaction with the user
        """

        if actions_path is None:
            actions_path = os.path.join(self.get_actions_path(), 'robotOnly')

        for file_name in os.listdir(actions_path):

            if os.path.isfile(os.path.join(actions_path, file_name)):
                # Generate the function name
                # action_tokens = file_name.replace("_", " ").split()
                # function_name = ''.join(action_tokens)
                function_name = file_name

                # Define the function dynamically
                def make_action_func(action):
                    def action_func():
                        im.execute(action)

                    return action_func

                # Assign the function to the class
                setattr(self, function_name, make_action_func(file_name))
                self.generated_actions.append(function_name)

    # ------------------------------ Complex actions ----------------------------- #

    def set_profile_en(self):
        im.setProfile(['*', '*', '*', '*'])

    def set_profile_it(self):
        #im.init()
        im.setProfile(['*', '*', 'it', '*'])

    def custom_greeting(self):
        im.execute("custom_greeting")

    def deaf_ask_help(self):
        q = im.ask("deaf_ask_help", timeout=999)
        print("RISPOSTA " + q)
        if (q != 'timeout'):
            if q == 'agree':
                required_dest = im.ask('deaf_agree', timeout=999)
                with open("/home/robot/playground/outcome.txt","w") as file:
                    file.write(required_dest)

            else:
                im.execute('deaf_disagree')
                with open("/home/robot/playground/outcome.txt","w") as file:
                    file.write("failure")

                time.sleep(5)
                im.init()

    def blind_ask_help(self):
        q = im.ask('blind_ask_help', timeout=999)
        if (q == 'agree'):
            required_dest = im.ask('blind_agree', timeout=999)
            with open("/home/robot/playground/outcome.txt","w") as file:
                file.write(required_dest)

        else:
            im.execute('blind_disagree')
            with open("/home/robot/playground/outcome.txt","w") as file:
                file.write("failure")

            time.sleep(5)
            im.init()

    def blind_ask_cancel(self):
        q = im.ask('blind_ask_cancel', timeout=999)
        if (q == 'agree'):
            with open("/home/robot/playground/outcome.txt","w") as file:
                file.write('result_yes')

        else:
            with open("/home/robot/playground/outcome.txt","w") as file:
                file.write('result_no')

    def deaf_ask_cancel(self):
        q = im.ask('deaf_ask_cancel', timeout=999)
        if (q == 'agree'):
            with open("/home/robot/playground/outcome.txt","w") as file:
                file.write('result_yes')
        else:
            with open("/home/robot/playground/outcome.txt","w") as file:
                file.write('result_no')

    def blind_ask_call(self):
        q = im.ask('blind_ask_call', timeout=999)
        if (q == 'agree'):
            with open("/home/robot/playground/outcome.txt","w") as file:
                file.write('result_yes')
        else:
            with open("/home/robot/playground/outcome.txt","w") as file:
                file.write('result_no')

    def call(self):
        im.execute('call')

    def deaf_ask_call(self):
        q = im.ask('deaf_ask_call', timeout=999)
        if (q == 'agree'):
            with open("/home/robot/playground/outcome.txt","w") as file:
                file.write('result_yes')
        else:
            with open("/home/robot/playground/outcome.txt","w") as file:
                file.write('result_no')

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

    def move_to(self, target_x, target_y):
        try:
            current_x, current_y, current_theta = self.mo_service.getRobotPosition(True)
            delta_x = target_x - current_x
            delta_y = target_y - current_y
            theta = math.atan2(delta_y, delta_x)

            self.mo_service.moveTo(delta_x, delta_y, theta)
            success = True
            if success:
                print("[INFO] Moved to position: ({}, {})".format(target_x, target_y))
            else:
                print("[INFO] Navigation failed or was interrupted")
            return success
        except Exception as e:
            print("[ERROR] Failed to move: {}".format(e))
            return False

    def stop_motion(self):
        try:
            self.mo_service.stopMove()
            current_x, current_y, _ = self.mo_service.getRobotPosition(True)
            print("[INFO] Motion stopped. Current position: ({}, {})".format(current_x, current_y))
        except Exception as e:
            print("[ERROR] Failed to stop motion: {}".format(e))
