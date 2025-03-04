from user import User
import random


class UserManager:

    def __init__(self):
        self.users = []

    @staticmethod
    def load(file_path):
        user_manager = UserManager()
        with open(file_path, 'r') as file:
            for line in file:
                user_manager.users.append(User.from_string(line))
        return user_manager

    def add_user(self, user):
        self.users.append(user)

    def add_users(self, users):
        for user in users:
            self.add_user(user)

    def get_all_users(self):
        return self.users

    def get_random_user(self):
        return random.choice(self.users)

    def find_user_by_username(self, username):
        for user in self.users:
            if user.username == username:
                return user
        return None

    def find_user_by_id(self, userid):
        for user in self.users:
            if user.userid == userid:
                return user
        return None

    def dump(self, file_path):
        with open(file_path, 'w') as file:
            for user in self.users:
                file.write(str(user) + '\n')

    def __iter__(self):
        return iter(self.users)

    def __contains__(self, userid):
        return any(user.userid == userid for user in self.users)

# Example usage
if __name__ == "__main__":

    # Load users from the file
    # user_manager = UserManager.load("../../../static/users/users.txt")
    user_manager = UserManager()

    user_0 = User(0, "Daniel", "blind", "it")
    user_1 = User(1, "Iacopo", "deaf", "en")
    user_2 = User(2, "Bruno", "deaf", "it")
    user_3 = User(3, "Pepper", "blind", "en")
    users = [user_0, user_1, user_2]
    user_manager.add_users(users)

    # Retrieve all users
    users = user_manager.get_all_users()
    for user in users:
        print(user)

    # Dump users back to the file
    user_manager.dump("../../../static/users/users.txt")
