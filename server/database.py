user_statuses = {}

def update_user_status(user, status):
    user_statuses[user] = status

def get_user_status(user):
    return user_statuses.get(user, 'offline')

def get_online_users():
    return [user for user, status in user_statuses.items() if status == 'online']