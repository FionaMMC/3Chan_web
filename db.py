'''
db
database file, containing all the logic to interface with the sql database
'''
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
from models import *
from pathlib import Path
import os
import friend

# creates the database directory
Path("database") \
    .mkdir(exist_ok=True)

# "database/main.db" specifies the database file
# change it if you wish
# turn echo = True to display the sql output
engine = create_engine("sqlite:///database/main.db", echo=False)

# initializes the database
Base.metadata.create_all(engine)

# inserts a user to the database
def insert_user(username: str, password: str, public_key: str, private_key: str, salt: str):
    with Session(engine) as session:
        user = User(username=username, password=password, pubKey=public_key, priKey=private_key, salt=salt, sex="secret", type="student", major="secret")
        session.add(user)
        session.commit()

# gets a user from the database
def get_user(username: str):
    with Session(engine) as session:
        return session.get(User, username)

def set_user_sex(username: str, sex: str):
    with Session(engine) as session:
        user = session.get(User, username)
        if user is None:
            return "User not found."
        user.sex = sex
        session.commit()
        return f"{username}'s gender updated successfully. Please refresh to view the new profile."
    
def set_user_major(username: str, major: str):
    with Session(engine) as session:
        user = session.get(User, username)
        if user is None:
            return "User not found."
        user.major = major
        session.commit()
        return f"{username}'s major updated successfully. Please refresh to view the new profile."

def update_user_username(username: str, new_username: str):
    with Session(engine) as session:
        user = session.get(User, username)
        if user is None:
            return "User not found."
        
        if session.query(User).filter(User.username == new_username).first() is not None:
            return "New username already taken."
        
        try:
            # Update username
            user.username = new_username

            # Update friendships
            friendships = session.query(Friendship).filter(
                (Friendship.user1 == username) | (Friendship.user2 == username)).all()
            for friendship in friendships:
                if friendship.user1 == username:
                    friendship.user1 = new_username
                if friendship.user2 == username:
                    friendship.user2 = new_username
            
            # Rename token file if it exists
            token_file_old = f"tokens/{username}.token"
            token_file_new = f"tokens/{new_username}.token"
            if os.path.exists(token_file_old):
                os.rename(token_file_old, token_file_new)

            session.commit()
            return "Username updated successfully."
        except IntegrityError:
            # Rollback if update failed
            session.rollback()
            return "Failed to update username due to database error."
        
def update_user_password(username: str, new_hashed_password: str):
    with Session(engine) as session:
        user = session.get(User, username)
        if user is None:
            return "User not found."
        user.password = new_hashed_password
        session.commit()
        return f"{username}'s password updated successfully."
    
def update_user_type(username: str, new_user_type: str):
    with Session(engine) as session:
        user = session.get(User, username)
        if user is None:
            return "User not found."
        user.type = new_user_type
        session.commit()
        return f"{username}'s user type updated successfully. Please refresh to view the new profile."
    
    
def get_user_type(username: str):
    with Session(engine) as session:
        user = session.get(User, username)
        if user:
            return  user.type
        else:
            return "User not found."

def get_user_major(username: str):
    with Session(engine) as session:
        user = session.get(User, username)
        if user:
            return  user.major
        else:
            return "User not found."


def get_user_sex(username: str):
    with Session(engine) as session:
        user = session.get(User, username)
        if user:
            return user.sex
        else:
            return "User not found."
     
def set_user_online_status(username: str, online: bool):
    with Session(engine) as session:
        online_user = session.query(OnlineUser).filter_by(username=username).first()
        
        if online_user:
            online_user.is_online = online
        else:
            online_user = OnlineUser(username=username, is_online=online)
            session.add(online_user)
            
        session.commit()
        return "setted your status!"
    
        
def get_user_online_status(username: str) -> bool:
    with Session(engine) as session:
        online_user = session.query(OnlineUser).filter_by(username=username).first()
        
        if online_user:
            return online_user.is_online
        else:
            return False
        
        
def get_users_online_status(name_list: list) -> list:
    with Session(engine) as session:
        online_users = session.query(OnlineUser).filter(OnlineUser.username.in_(name_list)).all()
        online_users_dict = {user.username: user.is_online for user in online_users}
        return [online_users_dict.get(name, False) for name in name_list]
    
def set_user_ban(username: str, is_ban: bool):
    with Session(engine) as session:
        ban_user = session.query(Banuser).filter_by(username=username).first()
        
        if ban_user:
            ban_user.is_ban = is_ban
        else:
            ban_user = Banuser(username=username, is_ban=is_ban)
            session.add(ban_user)
            
        session.commit()
        return f"updated ban status."
          
def get_user_ban_status(username: str) -> bool:
    with Session(engine) as session:
        ban_user = session.query(Banuser).filter_by(username=username).first()
        
        if ban_user:
            return ban_user.is_ban
        else:
            return False

if __name__ == '__main__':
    update_user_type("1", "admin")