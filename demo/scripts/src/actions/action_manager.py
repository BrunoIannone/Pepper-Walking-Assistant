import os
import math
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
        self.default_lin_vel = 0.3
        self.default_ang_vel = 0.7

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
        with open("/home/robot/playground/outcome.txt", "r") as file:
            status = file.readline().strip()
        return str(status).strip()

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
        if q != 'timeout':
            if q == 'yes':
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
        if q == 'yes':
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
        if q == 'yes':
            with open("/home/robot/playground/outcome.txt","w") as file:
                file.write('result_yes')

        else:
            with open("/home/robot/playground/outcome.txt","w") as file:
                file.write('result_no')

    def deaf_ask_cancel(self):
        q = im.ask('deaf_ask_cancel', timeout=999)
        if q == 'yes':
            with open("/home/robot/playground/outcome.txt","w") as file:
                file.write('result_yes')
        else:
            with open("/home/robot/playground/outcome.txt","w") as file:
                file.write('result_no')

    def blind_ask_call(self):
        q = im.ask('blind_ask_call', timeout=999)
        if q == 'yes':
            with open("/home/robot/playground/outcome.txt","w") as file:
                file.write('result_yes')
        else:
            with open("/home/robot/playground/outcome.txt","w") as file:
                file.write('result_no')

    def deaf_call(self):
        im.execute('deaf_call')

    def blind_call(self):
        im.execute('blind_call')

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

    def blind_agree(self):
        q = im.execute('blind_agree', timeout=999)
        with open("/home/robot/playground/outcome.txt", "w") as file:
            file.write(q)

    def deaf_agree(self):
        q = im.execute('deaf_agree', timeout=999)
        with open("/home/robot/playground/outcome.txt", "w") as file:
            file.write(q)

    def deaf_ask_call(self):
        q = im.ask('deaf_ask_call', timeout=999)
        if q == 'agree':
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

    def set_speed(self, lin_vel, ang_vel, dtime):
        self.mo_service.move(lin_vel, 0, ang_vel)
        time.sleep(dtime)
        self.mo_service.stopMove()

    """
    def move_to(self, target_x, target_y):
        try:
            current_x, current_y, current_theta = self.mo_service.getRobotPosition(True)
            delta_x = target_x - current_x
            delta_y = target_y - current_y
            theta = math.atan2(delta_y, delta_x)

            self.mo_service.moveTo(current_x, current_y, theta)
            self.mo_service.moveTo(delta_x, delta_y, theta)

            # TODO remove this
            success = True

            if success:
                print("[INFO] Moved to position: ({}, {})".format(target_x, target_y))
            else:
                print("[INFO] Navigation failed or was interrupted")
            return success
        except Exception as e:
            print("[ERROR] Failed to move: {}".format(e))
            return False
    """

    def move_to(self, target_x, target_y):
        try:
            current_x, current_y, current_theta = self.mo_service.getRobotPosition(True)

            delta_x = target_x - current_x
            delta_y = target_y - current_y
            target_theta = math.atan2(delta_y, delta_x)

            distance = math.sqrt(delta_x ** 2 + delta_y ** 2)
            angle_diff = target_theta - current_theta

            # Normalize angle to [-pi, pi]
            while angle_diff > math.pi:
                angle_diff -= 2 * math.pi
            while angle_diff < -math.pi:
                angle_diff += 2 * math.pi

            if abs(angle_diff) > 0.1:
                rotation_time = abs(angle_diff / self.default_ang_vel)
                self.mo_service.move(0, 0, math.copysign(self.default_ang_vel, angle_diff))
                time.sleep(rotation_time)
                self.mo_service.stopMove()


            if distance > 0.1:
                movement_time = distance / self.default_lin_vel
                self.mo_service.move(self.default_lin_vel, 0, 0)
                time.sleep(movement_time)
                self.mo_service.stopMove()


            final_x, final_y, _ = self.mo_service.getRobotPosition(True)
            print("Moved from ({:.2f}, {:.2f}) to ({:.2f}, {:.2f})"
                  .format(current_x, current_y, final_x, final_y))

            return True

        except Exception as e:
            print("[ERROR] Failed to move: {}".format(e))
            self.mo_service.stopMove()
            return False

    def stop_motion(self):
        try:
            self.mo_service.stopMove()
            current_x, current_y, _ = self.mo_service.getRobotPosition(True)
            print("[INFO] Motion stopped. Current position: ({}, {})".format(current_x, current_y))
        except Exception as e:
            print("[ERROR] Failed to stop motion: {}".format(e))
