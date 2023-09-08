from pymongo import MongoClient
from datetime import datetime

import pymongo

client = MongoClient('mongodb://localhost:27017')
chat_db = client.get_database('PrivateChatApp')

users_collection = chat_db.get_collection('users')
messages_collection = chat_db.get_collection('messages')
friends_collection = chat_db.get_collection('friends')

def create_user(username):
    users_collection.create_index([('username', 1)], unique=True)
    return users_collection.insert_one({'username': username})

def get_users(loggedin_user):
    users = list(users_collection.find({'username': {'$ne': loggedin_user}}, projection={'username': 1}))
    return users if users else None

def get_user(username):
    user = users_collection.find_one({'username': username})
    return user if user else None

def add_messages(sender, recipient, message):
    messages_collection.insert_one({'sender': sender, 'recipient': recipient, 'message': message, 'created_at': datetime.now()})

def get_messages(sender, recipient):
    messages = messages_collection.find({
        '$or': [
            {'sender': sender, 'recipient': recipient},
            {'sender': recipient, 'recipient': sender}
        ]
    }).sort('timestamp', pymongo.ASCENDING)

    message_list = []
    for message in messages:
        message_list.append({
            'sender': message['sender'],
            'recipient': message['recipient'],
            'message': message['message'],
            'created_at': message['created_at']
        })

    return message_list

def send_request(sender, recipient):
    friends_collection.insert_one({'sender': sender, 'recipient': recipient, 'status': 'pending'})

def delete_request(sender, recipient):
    friends_collection.delete_one({'sender': recipient, 'recipient': sender, 'status': 'pending'})

def get_requests(username):
    requests = list(friends_collection.find({'recipient': username, 'status': 'pending'}))
    return requests if requests else None

def add_friend(sender, recipient):
    friends_collection.update_one({'sender': sender, 'recipient': recipient}, {'$set': {'status': 'accepted'}})

def get_friends(username):
    friends = list(friends_collection.find({
        '$or': [
            {'sender': username,'status': 'accepted'},
            {'recipient': username,'status': 'accepted'}
        ]
    }))
    # friends = list(friends_collection.find({'sender': username, 'status': 'accepted'}))
    return friends if friends else None


# Function to block a user
def block_user(current_user, user_to_block):
    # Assuming 'current_user' is the user performing the blocking
    # Update the 'blocked_users' array for 'current_user'
    users_collection.update_one(
        {"username": current_user},
        {"$addToSet": {"blocked_users": user_to_block}}
    )


# Function to check if a user is blocked by another user
def is_user_blocked(sender_username, recipient_username):
    sender = users_collection.find_one({"username": sender_username})
    if sender and "blocked_users" in sender:
        if recipient_username in sender["blocked_users"]:
            return "User has blocked you"  # Return the specific message
    return False


# Function to unblock a user
def unblock_user(current_user, user_to_unblock):
    users_collection.update_one(
        {"username": current_user},
        {"$pull": {"blocked_users": user_to_unblock}}
    )