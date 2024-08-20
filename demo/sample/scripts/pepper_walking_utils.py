import os
class PepperWalkingUtils():
    def __init__(self):
        self.running = True

    def recognizedUser(self):
        return True
 
    def actionsPath(self):
        return os.path.join(os.path.dirname(os.path.realpath(__file__ )),"../actions/")
    
    def createCustomGreeting(self, user_name,disability):
        with open("/home/robot/src/modim/demo/sample/actions/custom_greeting", "w") as file:
        
            if disability == "blind": #Blind
                contenuto = """IMAGE
<*, *, *, *>:  img/welcome.jpg
----
TTS
<*,*,it,*>: Ciao! Benvenuto {0}
<*,*,*,*>:  Hello! Welcome {0}
----""".format(user_name)
                
            else:                     #Deaf
                contenuto = """IMAGE
<*, *, *, *>:  img/welcome.jpg
----
TEXT_title
<*, *, *, *>:  Welcome to Diag
----
TEXT
<*,*,it,*>: Benvenuto {0}
<*,*,*,*>:  Welcome {0}
----
GESTURE
<*,*,*,*>: animations/Stand/Gestures/Hey_1
----""".format((user_name))
                
            file.write(contenuto)
