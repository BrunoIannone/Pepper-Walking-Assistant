import time

def set_profile_en():
    im.setProfile(['*', '*', '*', '*'])

def set_profile_it():
    im.setProfile(['*', '*', 'it', '*'])

def custom_greeting():

    """
    im.execute("custom_greeting")

    time.sleep(2)

    q = im.ask('blind_ask_help', timeout=999)
    with open("/home/robot/playground/outcome.txt", "w") as file:
        file.write(q)
    while q != 'failure':

        with open("/home/robot/playground/outcome.txt", "w") as file:
            file.write(q)
        if q == 'yes':
            b = im.ask('blind_agree', timeout=999)
            print(b)
            while b not in ['A', 'B', 'C', 'D', 'E']:
                break
        else:
            return
    """

    im.init()

    im.execute("custom_greeting")
    time.sleep(2)

    help_response = im.ask('blind_ask_help', timeout=999)  # Use blind_ask_help action file

    im.executeModality('TTS', 'User said: ' + help_response)

    if help_response.lower().strip() == "yes":

        destination = im.ask('blind_agree', timeout=999)  # Use blind_agree action file

        im.executeModality('TTS', 'User selected room: ' + destination)
        # im.executeModality('TEXT_default', 'Are you interested in any particular work?')

        if destination in ["A", "B", "C", "D", "E"]:
            with open("/home/robot/playground/outcome.txt", "w") as file:
                file.write('GO TO ' + destination)

        im.executeModality('TTS', 'Done writing on file')

    elif help_response == "no":
        im.execute('blind_disagree')  # Exit if the user doesn't need help
    else:
        im.executeModality("TTS", "Pepper di merda: [" + help_response + "]")

# ----------------------------- Blind interaction ---------------------------- #

def blind_ask_help():

    q = im.ask('blind_ask_help', timeout=999)
    while q != 'failure':
        with open("/home/robot/playground/outcome.txt","w") as file:
            file.write(q)

def blind_agree():
    q = im.ask('blind_agree', timeout=999)

def blind_ask_cancel():
    q = im.ask('blind_ask_cancel', timeout=999)
    with open("/home/robot/playground/outcome.txt","w") as file:
        file.write(q)

def blind_ask_call():
    q = im.ask('blind_ask_call', timeout=999)
    with open("/home/robot/playground/outcome.txt", "w") as file:
        file.write(q)
