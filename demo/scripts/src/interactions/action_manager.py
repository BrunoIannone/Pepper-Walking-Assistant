import os

class ActionManager:

    def __init__(self, outcome_path="/home/robot/playground/outcome.txt"):

        # Generate the actions
        self.generated_actions = []
        self.generate_robot_only_actions()

        self.outcome_path = outcome_path

    def recognizedUser(self):
        return True
 
    def getActionsPath(self):
        return os.path.join(os.path.dirname(os.path.realpath(__file__)),"../../../actions/")
    
    def createCustomGreeting(self, user_name, disability):
        with open(os.path.join(self.getActionsPath(), "custom_greeting"), "w") as file:
        
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

    def checkStatus(self):
        status = None
        with open(self.outcome_path, "r") as file:
            status = file.readline().strip()
        return str(status).strip()

    def generate_robot_only_actions(self, actions_path=None):
        """
        Generate the simple actions for which the robot does not expect a complex interaction with the user
        """
        
        # actions_path = self.getActionsPath()
        if actions_path is None:
            actions_path = os.path.join(self.getActionsPath(), 'robotOnly')

        for file_name in os.listdir(actions_path):

            if os.path.isfile(os.path.join(actions_path, file_name)):

                # Generate the function name
                action_tokens = file_name.replace("_", " ").split()
                function_name = ''.join(action_tokens)

                # Define the function dynamically
                def make_action_func(action):
                    def action_func():
                        im.execute(action)

                    return action_func

                # Assign the function to the class
                setattr(self, function_name, make_action_func(file_name))
                self.generated_actions.append(function_name)

    # ------------------------------ Complex actions ----------------------------- #

    def setProfileEn(self):
        im.setProfile(['*', '*', '*', '*'])

    def setProfileIt(self):
        #im.init()
        im.setProfile(['*', '*', 'it', '*'])

    def customGreeting(self):
        im.execute("custom_greeting")

    def deafAskHelp(self):
        q = im.ask("deaf_ask_help", timeout = 999)
        print("RISPOSTA " + q)
        if (q!='timeout'):
            if q == 'agree':
                required_dest = im.ask('deaf_agree',timeout = 999)

                with open(self.outcome_path,"w") as file:
                    file.write(required_dest)

                #subprocess.run(['python', '/home/robot/playground/pepper_walking_assistant/assistant/assistant.py'])
            
                ## TODO: Andare in required_dest ( goto(required_dest) )

            else:
                im.execute('deaf_disagree')
                #print("PERCORSO ROBOT " + os.path.dirname(os.path.realpath(__file__ ))) #/home/robot/src/modim/src/GUI  #/home/robot/src/modim/src/GUI/../../../playground
                with open(self.outcome_path,"w") as file:
                    file.write("failure")
                time.sleep(5)
                im.init()
                ## TODO: reset procedure?
        
    def blindAskHelp(self):
        q = im.ask('blind_ask_help',timeout = 999)
        if(q == 'agree'):
            required_dest = im.ask('blind_agree',timeout = 999)
            with open(self.outcome_path,"w") as file:
                file.write(required_dest)

        else:
            im.execute('blind_disagree')
            with open(self.outcome_path,"w") as file:
                    file.write("failure")
            time.sleep(5)
            im.init()
            ## TODO: reset procedure?        
        
    def waitForHuman(self):
        stop_detection = False
        is_human_detected = False

        #Checking if human stay in front of Pepper more than 2 seconds
        im.robot.startSensorMonitor()
        while not stop_detection:
            while not is_human_detected:
                p = im.robot.sensorvalue() #p is the array with data of all the sensors
                print("SENSOR VALUE " + p)
                is_human_detected = p[1] > 0.0 and p[1] < 1.0 #p[1] is the Front sonar
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

    def recordUser(self):
        modality = im.ask("record_user",timeout = 999)
        print("MODALITY" + modality)
        with open(self.outcome_path,"w") as file:
            file.write(str(modality).strip())
        
    def askLanguage(self):
        modality = im.ask("ask_language",timeout = 999)
        with open(self.outcome_path,"w") as file:
            file.write(str(modality).strip())


