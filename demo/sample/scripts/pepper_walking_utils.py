class PepperWalkingUtils():
    def __init__(self):
        self.running = True

    def recognizedUser(self):
        return True


    def setUser(self,user_name):
        with open("/home/robot/playground/test.txt", "w") as file:
            file.write(user_name)