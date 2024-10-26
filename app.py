'''
app.py contains all of the server application
this is where you'll find all of the get/post request handlers
the socket event handlers are inside of socket_routes.py
'''

from flask import Flask, jsonify, render_template, request, abort, url_for, redirect, session,render_template_string
from flask_socketio import SocketIO
from werkzeug.security import generate_password_hash, check_password_hash

import db
import secrets
import os
import friend
import group
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives import hashes
import logging
import knowledge_repo
from debug import d_print

app = Flask(__name__)

# turn of logging
log = logging.getLogger('werkzeug')
log.setLevel(logging.WARNING)

# secret key used to sign the session cookie
app.config['SECRET_KEY'] = secrets.token_hex()
#app.config['PREFERRED_URL_SCHEME'] = 'https'
socketio = SocketIO(app)

# don't remove this!!
import socket_routes

# index page
@app.route("/")
def index():
    return render_template("index.jinja")
'''
@app.route("/welcome")
def welcome():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    
    if request.args.get("username") is None:
        abort(404)
    username = session.get("username")

    return render_template("welcome.jinja",username = username)

'''
'''@app.route("/chat")
def chat():
    return jsonify(url=url_for('home', username=session.get("username")))'''




# login page
@app.route("/login")
def login():
    return render_template("login.jinja")


# handles a post request when the user clicks the log in button
@app.route("/login/user", methods=["POST"])
def login_user():
    if not request.is_json:
        abort(404)

    username = request.json.get("username")
    password = request.json.get("password")

    user = db.get_user(username)
    if user is None:
        return {
            'token': None,
            'url': "Error: User does not exist!"
        }
    
    print(f"(In login_user) The password get from user is {password}")
    print(f"(In login_user) The password get from database is {user.password}")

    if user.password != password:
        return {
            'token': None,
            'url': "Error: Password does not match!"
        }
    
    session['username'] = username
    session['logged_in'] = True

    token = secrets.token_urlsafe(32)

    if not os.path.exists("tokens"):
        os.makedirs("tokens")
    with open(f"tokens/{username}.token", "w") as f:
        f.write(token)

    ret = {
        'token': token, 
        'url': url_for('home', username=request.json.get("username"))
    }

    return ret

@app.route("/signup")
def signup():
    return render_template("signup.jinja")

# handles a post request when the user clicks the signup button
@app.route("/signup/user", methods=["POST"])
def signup_user(): 
    d_print("app.signup_user", "signup called")

    if not request.is_json: 
        abort(404) 

    username = request.json.get("username") 
    password = request.json.get("password") 
    public_key = request.json.get("publicKey") 
    private_key = request.json.get("privateKey") 
    salt = request.json.get("salt") 

    d_print("app.signup_user", "all information(username, password, ...) got")
    d_print("app.signup_user", f"username is {username}")
    d_print("app.signup_user", f"password is {password}")

    if username == "system": 
        d_print("app.signup_user", "username is system, wrong")
        return "Error: Invalid username!" 

    if db.get_user(username) is None: 
        d_print("app.signup_user", "username not occupied, add it to database")
        db.insert_user(username, password, public_key, private_key, salt) 
        return url_for('login') 
    d_print("app.signup_user", "username occupied")
    return "Error: User already exists!" 


# handler when a "404" error happens
@app.errorhandler(404)
def page_not_found(_):
    return render_template('404.jinja'), 404
  
# home page, where the messaging app is
@app.route("/home")
def home():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    
    if request.args.get("username") is None:
        abort(404)

    username = session.get("username")
    session['current_user'] = username
    session.permanent = True
    friends = friend.get_all_friends_of_current_user(username)
    friends_name = friend.get_all_friends_name_of_current_user(username)
    
    friends_online_status = db.get_users_online_status(friends_name)
    user_online_status = db.get_user_online_status(username)
    requests = friend.get_all_request(username)
    requests_to_sender = friend.get_all_request_to_sender(username)
    ban_status = db.get_user_ban_status(username)
    if ban_status:
        ban_status = "true"
    else:
        ban_status = "false"

    id_joined_group = group.get_joined_groups(username)
    joined_groups = []
    for id in id_joined_group:
        name_of_member = group.get_joined_members(id)
        joined_groups.append({id:name_of_member})
    
    roomid_pending_requests = group.pending_invotation(username)
    group_invitations = []
    for id in roomid_pending_requests:
        name_of_member = group.get_joined_members(id)
        group_invitations.append({id:name_of_member})
        
    return render_template("home.jinja", username=session.get("username"), friends=friends, requests = requests,requests_to_sender=requests_to_sender,group_invitations = group_invitations,joined_groups=joined_groups,friends_online_status = friends_online_status, user_online_status = user_online_status,ban_status = ban_status)


@app.route("/add_friend")
def add_friend():
    if request.args.get("friend_name") is None:
        return f"need a friend username"

    current_user = session.get('current_user', None)
    if current_user is None:
        return "session expired, try to re-log in"
    friend_name = request.args.get("friend_name")
    if friend_name == current_user:
        return "You can't send request to yourself"
    
    success = friend.request_friend(current_user, friend_name )
    if success:
        return f"successful to send the friend request to {friend_name}"
    else:
        return f"failed to send the friend request to {friend_name}"
    
@app.route("/reject_friend")
def reject_friend():
    current_user = session.get('current_user', None)
    if current_user is None:
        return "session expired, try to re-log in"
    friend_name = request.args.get("friend_name")
    friend.rejected_friend(current_user, friend_name )
    return f"rejected {friend_name}"

@app.route("/accept_friend")
def accept_friend():
    current_user = session.get('current_user', None)
    if current_user is None:
        return "session expired, try to re-log in"
    friend_name = request.args.get("friend_name")
    success = friend.accept_friend(current_user, friend_name )
    if success:
        return f"successfully accepted the request from {friend_name}"
    else:
        return f"unable to accepet request."
    
@app.route("/delete_friend")
def delete_friend():
    current_user = session.get('current_user', None)
    if current_user is None:
        return "session expired, try to re-log in"
    friend_name = request.args.get("delete_friend_name")   
    success =friend.delete_friend(current_user, friend_name)
    if success:
        return f"deleted {friend_name} from your friendlist"
    else:
        return f"failed to delete {friend_name} from your friendlist"
    
    
    
@app.route("/accept_invitation", methods=['POST'])
def accept_invitation():
    current_user = session.get('current_user', None)
    if current_user is None:
        return "session expired, try to re-log in"
    d_print("accept_invitation", "accept_invitation is called")
    group_info = request.json.get("invitation")
    d_print("accept_invitation", f"The parameter get from client is {group_info}")
    if not group_info:
        return jsonify("No invitation provided"), 400
    group_id = str(next(iter(group_info.keys())))
    success = group.accept_invitation(group_id, current_user)
    if success:
        return "accept the invitation!"
    else:
        return "fail to accept! Already existed in the group or group doesn't exist!"
    
@app.route("/reject_invitation", methods=['POST'])
def reject_invitation():
    current_user = session.get('current_user', None)
    if current_user is None:
        return "session expired, try to re-log in"
    d_print("reject_invitation", "reject_invitation is called")
    group_info = request.json.get("invitation")
    d_print("areject_invitation", f"The parameter get from client is {group_info}")
    if not group_info:
        return jsonify("No invitation provided"), 400
    group_id = str(next(iter(group_info.keys())))
    success = group.reject_invitation(group_id, current_user)
    if success:
        return "reject the invitation!"
    else:
        return "fail to reject!"
    
@app.route("/leave_group", methods=['POST'])
def leave_group():
    current_user = session.get('current_user', None)
    if current_user is None:
        return "session expired, try to re-log in"
    d_print("leave_group", "leave_group is called")
    group_info = request.json.get("group")
    d_print("leave_group", f"The parameter get from client is {group_info}")
    if not group_info:
        return jsonify("No invitation provided"), 400
    group_id = str(next(iter(group_info.keys())))
    success = group.leave_group(group_id, current_user)
    if success:
        return "leaved group!"
    else:
        return "fail to leave!"
    
@app.route("/create_group", methods = ['POST'])
def create_group():
    current_user = session.get('current_user', None)
    if current_user is None:
        return "session expired, try to re-log in"
    d_print("create_group", "create_group is called")
    group_info = request.json.get("invitation_list")
    d_print("create_group", f"The parameter get from client is {group_info}")
    if not group_info:
        return jsonify("No invitation provided"), 400
    success = group.create_new_group(current_user, group_info)
    if success:
        return "Group created!"
    else:
        return "fail to create group!" 
    
    
    
    
    
    
    

##### Knowledge repository  
    
@app.route("/forum")
def forum():
    d_print("forum", "forum is called")
    current_user = session.get('current_user', None)
    if current_user is None:
        return "session expired, try to re-log in"
    user_type = db.get_user_type(current_user)
    user_gender = db.get_user_sex(current_user)
    username = str(current_user)
    category = request.args.get('category', 'default_category')
    post_id = request.cookies.get('postId')
    titles = knowledge_repo.get_all_titles(category)
    if post_id is None:
        post_id = -1

    post_id = int(post_id)
    content = knowledge_repo.get_content(category, post_id)
    sender = knowledge_repo.get_sender(category, post_id)
    timer = knowledge_repo.get_time(category, post_id)
    comments = knowledge_repo.get_comments(category, post_id)

    return render_template("forum.jinja", username=username, user_type=user_type, user_gender=user_gender, titles=titles, category=category, content=content, sender=sender, time=timer, comments=comments,post_id = post_id)


@app.route('/get-post-content')
def get_post_content():
    category = request.args.get('category')
    post_id = request.args.get('id', type=int)
    content = knowledge_repo.get_content(category, post_id)
    sender = knowledge_repo.get_sender(category, post_id)
    time = knowledge_repo.get_time(category, post_id)
    comments = knowledge_repo.get_comments(category, post_id)

    html_content = render_template_string('''
        <div id="content-{{ post_id }}">
            <div id="content">{{ content }}</div>
            <div id="sender">{{ sender }}</div>
            <div id="time">{{ time }}</div>
            
            <div id="modify">
                <!-- Added interaction buttons and comment section -->
                <button onclick="delete_post('{{ post_id }}', '{{ category }}')">Delete Post</button>
                <button onclick="modify()">Modify Post</button>
                <div id="modify" style="display: none;">
                    <textarea id="newContent" placeholder="Enter new content here..."></textarea>
                    <button onclick="modify_post('{{ post_id }}', '{{ category }}')">Submit</button>
                </div>
            </div>
            
            
            
            <div id="post-comment">
                <textarea id="comment-{{ post_id }}" placeholder="Write a comment..."></textarea>
                <button onclick="add_comment('{{ post_id }}', '{{ category }}')">Post Comment</button>
            </div>
            <div id="comments">Comments</div>
            {% if comments %}
            <ul>
                {% for comment in comments %}
                <li>
                    <span>{{ comment.sender }}:</span>
                    <span>{{ comment.content }}</span>
                    
                    <button onclick="delete_comment('{{ category }}','{{ post_id }}','{{ comment.comment_id }}')">Delete</button>
                </li>
                <li> <span>{{ comment.time }}</span></li>
                
                {% endfor %}
            </ul>
            {% else %}
            <p>No comments yet.</p>
            {% endif %}

        </div>
    ''', post_id=post_id, content=content, sender=sender, time=time, comments=comments, category=category)

    return html_content







@app.route("/create_post", methods=['POST'])
def create_post():
    current_user = session.get('current_user', None)
    if current_user is None:
        return "session expired, try to re-log in"
    
    is_ban= db.get_user_ban_status(current_user)
    if is_ban:
        return "sorry, you have been banned. Please contact admin."
    
    category = request.json.get("category")
    content = request.json.get("content")
    title= request.json.get("title")

    op_result = knowledge_repo.add_post(category, current_user, title, content)
    if "success" == op_result:
        return "Post created successfully"
    else:
        return op_result
    
    
    
@app.route("/delete_post", methods=['POST'])
def delete_post():
    current_user = session.get('current_user', None)
    if current_user is None:
        return "session expired, try to re-log in"
    post_id = int(request.json.get("post_id"))
    category = request.json.get("category")
    owner = knowledge_repo.get_sender(category, post_id)
    user_infor = db.get_user(current_user)
    
    if user_infor.type != "admin":   
        if current_user != owner:
            return "you are not able to delete post"   

    op_result = knowledge_repo.del_post(category, post_id)
    if "success" == op_result:
         return "post deleted "
    else:
         return op_result
     
@app.route("/delete_comment", methods=['POST'])
def delete_comment():
    current_user = session.get('current_user', None)
    if current_user is None:
        return "session expired, try to re-log in"
    post_id = int(request.json.get("post_id"))
    comment_id = int(request.json.get("comment_id"))
    category = request.json.get("category")
    owner = knowledge_repo.get_comment_sender(category, post_id,comment_id)
    user_infor = db.get_user(current_user)
    
    if user_infor.type != "admin":   
        if current_user != owner:
            return "you are not able to delete post"   

    op_result = knowledge_repo.del_comment(category, post_id,comment_id)
    if "success" == op_result:
         return "comment deleted "
    else:
         return op_result
     
@app.route("/modify_post", methods=['POST'])
def modify_post():
    current_user = session.get('current_user', None)
    if current_user is None:
        return "session expired, try to re-log in"
    
    is_ban= db.get_user_ban_status(current_user)
    if is_ban:
        return "sorry, you have been banned. Please contact admin."
    post_id = int(request.json.get("post_id"))
    category = request.json.get("category")
    owner = knowledge_repo.get_sender(category, post_id)
    user_infor = db.get_user(current_user)
    new_content = request.json.get("new_content")
    
    if user_infor.type != "admin":   
        if current_user != owner:
            return "you are not able to modify post"   

    op_result = knowledge_repo.modify_post(category, post_id,new_content)
    if "success" == op_result:
         return "post modifyed"
    else:
         return op_result

@app.route("/add_comment", methods=['POST'])
def add_comment():
    current_user = session.get('current_user', None)
    if current_user is None:
        return "session expired, try to re-log in"
    
    is_ban= db.get_user_ban_status(current_user)
    if is_ban:
        return "sorry, you have been banned. Please contact admin."   

    post_id = int(request.json.get("post_id"))
    comment_content = request.json.get("comment")
    sender = str(session['current_user'])
    category = request.json.get("category")
    res = knowledge_repo.add_comment(category, post_id, sender, comment_content)
    return res



##### Settings

@app.route("/update_user_gender", methods=['POST'])
def update_user_gender():
    current_user = session.get('current_user', None)
    if current_user is None:
        return "session expired, try to re-log in"

    new_user_sex = request.json.get("new_user_gender")

    result = db.set_user_sex(current_user, new_user_sex)
    
    d_print("update_user_gender", f"result is {result}")
    
    return result

@app.route("/update_user_major", methods=['POST'])
def update_user_major():
    current_user = session.get('current_user', None)
    if current_user is None:
        return "session expired, try to re-log in"

    new_user_major = request.json.get("new_user_major")

    result = db.set_user_major(current_user, new_user_major)
    
    d_print("update_user_major", f"result is {result}")
    
    return result

@app.route("/update_user_type", methods=['POST'])
def update_user_type():
    current_user = session.get('current_user', None)
    if current_user is None:
        return "session expired, try to re-log in"

    admin_token = request.json.get("admin_token")
    new_user_type = request.json.get("new_user_type")

    if "admin" == admin_token:
        result = db.update_user_type(current_user, new_user_type)
        return result
    else:
        return "Wrong token, update unseccussful"
    
@app.route("/setting")
def setting():
    d_print("setting", "setting is called")
    current_user = session.get('current_user', None)
    if current_user is None:
        return "session expired, try to re-log in"
    user_type= db.get_user_type(current_user)
    user_gender = db.get_user_sex(current_user)
    user_major = db.get_user_major(current_user)
    d_print("setting", f"username is {current_user}")
    username = current_user
    return render_template("setting.jinja", username = username, user_type = user_type, user_gender = user_gender,user_major = user_major)

@app.route("/set_ban", methods=['POST'])
def set_ban():
    current_user = session.get('current_user')
    if current_user is None:
        return jsonify({'message': 'Session expired, try to re-log in'}), 401
    
    data = request.get_json()
    if not data:
        return jsonify({'message': 'Invalid data'}), 400

    username = data.get("ban_username")
    is_ban = data.get("is_ban")
    
    if username is None or is_ban is None:
        return jsonify({'message': 'Missing parameters'}), 400

    res = db.set_user_ban(username, is_ban)
    return jsonify({'message': res})

@app.route("/set_online", methods=['POST'])
def set_online():
    current_user = session.get('current_user')
    if current_user is None:
        return jsonify({'message': 'Session expired, try to re-log in'}), 401
    res = db.set_user_online_status(current_user, True)
    return jsonify({'message': res})

@app.route("/set_offline", methods=['POST'])
def set_offline():
    current_user = session.get('current_user')
    if current_user is None:
        return jsonify({'message': 'Session expired, try to re-log in'}), 401
    res = db.set_user_online_status(current_user, False)
    return jsonify({'message': res})


    

if __name__ == '__main__':
    ssl_context = ('certs/localhost.crt', 'certs/localhost.key')
    socketio.run(app, debug=True, ssl_context=ssl_context)
    #socketio.run(app)