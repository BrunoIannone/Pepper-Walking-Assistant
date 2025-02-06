class User:

    def __init__(self, userid, username, disability, lang='en'):
        self.userid = userid
        self.username = username
        self.disability = disability  # blind/deaf
        self.lang = lang

    def __str__(self):
        return str(self.userid) + ", " + self.username + ", " + self.disability + ", " + self.lang

    @classmethod
    def from_string(cls, user_string):
        userid, username, alevel, lang = user_string.strip().split(',')
        return cls(int(userid), username.strip(), alevel.strip(), lang.strip())