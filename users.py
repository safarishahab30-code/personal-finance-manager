from storage import load_data

new_user = {
    "username": username,
    "password": password,
    "role": role
}

USERS_FILE = "data/users.json"


def get_default_user():
    users = load_data(USERS_FILE)

    for user in users:
        if user["id"] == 1:
            return user

    return None


def get_current_user_id():
    user =get_default_user()

    if user:
        return user["id"]

    return None
