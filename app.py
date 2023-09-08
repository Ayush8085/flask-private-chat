from flask import Flask, jsonify, render_template, request, redirect, session, url_for,flash
from flask_socketio import SocketIO, emit

from db import add_friend, add_messages, create_user, delete_request, get_friends, get_messages, get_requests, get_user, get_users, send_request,block_user,is_user_blocked,unblock_user

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secretkey'
socketio = SocketIO(app)

users = {}

@app.route('/<recipient>', methods=['GET', 'POST'])
def home(recipient):
    try:
        sender = session['username']
        recipient = recipient

        messages = get_messages(sender, recipient)
        return render_template('index.html', user=sender, recipient=recipient, messages=messages)
    except:
        return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():

    if request.method == 'POST':
        username = request.form.get('username')
        user = get_user(username)

        if user:
            session['username'] = username
        else:
            create_user(username)
            session['username'] = username
        
        return redirect(url_for('connect_to_user'))

    return render_template('login.html')

@app.route('/users', methods=['GET', 'POST'])
def connect_to_user():
    current_user = session['username']
    users = get_users(current_user)
    requests = get_requests(current_user)
    if not requests:
        requests = []

    for user in users:
        print("YES")
        if user in requests:
            users.remove(user)

    friends = get_friends(current_user)
    if not friends:
        friends = []
    print("Users:", users)
    print("Requests:", requests)
    print("Friends:", friends)

    # return jsonify(users)
    return render_template('users.html', users=users, requests=requests, friends=friends, current_user=current_user)

@app.route('/send_friend_request/<recipient>', methods=['GET', 'POST'])
def send_friend_request(recipient):
    sender = session['username']
    send_request(sender, recipient)
    return redirect(url_for('connect_to_user'))

@app.route('/accept_friend_request/<recipient>', methods=['GET', 'POST'])
def accept_friend_request(recipient):
    sender = session['username']
    add_friend(recipient, sender)
    print(f'{sender} and {recipient} are friends now!')
    return redirect(url_for('connect_to_user'))
    
@app.route('/reject_friend_request/<recipient>', methods=['GET', 'POST'])
def reject_friend_request(recipient):
    sender = session['username']
    delete_request(sender, recipient)
    return redirect(url_for('connect_to_user'))

@socketio.on('connect')
def get_username():
    users[session['username']] = request.sid
    print("Users:", users)



@socketio.on('private_message')
def private_message(data):
    recipient_session_id = None  # Initialize it to None

    try:
        recipient_session_id = users[data['username']]
    except:
        print("Recipient is not online!!")

    message = data['message']
    sender = session['username']
    recipient = data['username']

    # Check if sender has blocked the recipient
    blocked_message = is_user_blocked(sender, recipient)
    
    if blocked_message:
        print("haaa")
        print(blocked_message)  # Log the blocked message
        # Emit a JSON response indicating that the user is blocked
        if recipient_session_id:
            emit('new_private_message', {"message": f"{sender} has blocked you"}, room=recipient_session_id)
    else:
        # Add code here to block the recipient from sending a message to the sender
        sender_blocked_message = is_user_blocked(recipient, sender)
        
        if sender_blocked_message:
            print("Sender has blocked recipient.")
            # Emit a JSON response indicating that the sender has blocked the recipient
            if recipient_session_id:
                emit('new_private_message', {"message": "Sender has blocked the recipient."}, room=recipient_session_id)
        else:
            # If neither is blocked, proceed with sending the message and storing it
            add_messages(sender, recipient, message)
            print("Message sent.")
            
            new_data = {
                'message': message,
                'recipient': recipient,
                'sender': sender
            }

            if recipient_session_id:
                emit('new_private_message', new_data, room=recipient_session_id)







# Update the route to accept both GET and POST requests
@app.route('/block_user/<recipient>', methods=['GET', 'POST'])
def block_user_route(recipient):
    current_user = session.get('username')
    if current_user:
        block_user(current_user, recipient)
        return jsonify(f'You have blocked {recipient}.', 'success')
    return redirect(url_for('connect_to_user'))


# Route to unblock another user
@app.route('/unblock_user/<recipient>', methods=['POST'])
def unblock_user_route(recipient):
    current_user = session.get('username')
    if current_user:
        unblock_user(current_user, recipient)
        return jsonify(f'You have unblocked {recipient}.', 'success')
    return redirect(url_for('connect_to_user'))

    

if __name__ == '__main__':
    socketio.run(app, debug=True)