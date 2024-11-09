
class User:

    def __init__(self, userid, username, alevel, lang='en'):
        self.userid = userid
        self.username = username
        self.alevel = alevel  # 0 = blind, 1 = deaf
        self.lang = lang

    def __str__(self):
        return self.userid + ", " + self.username + ", " + self.alevel + ", " + self.lang

    @classmethod
    def from_string(cls, user_string):
        userid, username, alevel, lang = user_string.strip().split(',')
        return cls(int(userid), username.strip(), int(alevel), lang.strip())