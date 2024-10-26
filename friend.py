from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from models import *
from pathlib import Path
import db

Path("database") \
    .mkdir(exist_ok=True)

engine = create_engine("sqlite:///database/main.db", echo=False)

# manage friend
def request_friend(user1, user2):
    with Session(engine) as session:
        user1_obj = session.get(User, user1)
        user2_obj = session.get(User, user2)
        if user1_obj is None or user2_obj is None:
            return False
        friendship = session.query(Friendship).filter(
        ((Friendship.user1 == user1) & (Friendship.user2 == user2)) 
    ).first()
        if friendship is None:               
            friendship = Friendship(user1=user1, user2=user2, status="requested")
            session.add(friendship)
        if friendship.status == "rejected":
            friendship.status = "requested"
        elif friendship.status == "accepted":
            return False
        session.commit()
        return True


def accept_friend(user1, user2):
    with Session(engine) as session:
        flag = False
        user1_obj = session.get(User, user1)
        user2_obj = session.get(User, user2)
        # Check if both users exist in the database
        if user1_obj is None or user2_obj is None:
            return False
        friendship = session.query(Friendship).filter(
        ((Friendship.user1 ==  user1) & (Friendship.user2 ==  user2)&(Friendship.status == "requested")) 
    ).first()
        if friendship:
            friendship.status = "accepted"
            flag = True
        else:
            friendship = Friendship(user1=user1, user2=user2, status="accepted")
            session.add(friendship)
            
        friendship = session.query(Friendship).filter(
                ((Friendship.user1 ==  user2) & (Friendship.user2 ==  user1)&(Friendship.status == "requested")) 
            ).first()
        if friendship:
            friendship.status = "accepted"   
            flag = True
        else:
            friendship = Friendship(user1=user1, user2=user2, status="accepted")
            session.add(friendship)

        session.commit()
        return flag
            


def rejected_friend(user1, user2):
    with Session(engine) as session:
        flag = False
        user1_obj = session.get(User, user1)
        user2_obj = session.get(User, user2)
        # Check if both users exist in the database
        if user1_obj is None or user2_obj is None:
            return False
        friendship = session.query(Friendship).filter(
        ((Friendship.user1 ==  user1) & (Friendship.user2 ==  user2)&(Friendship.status == "requested")) 
    ).first()
        if friendship:
            friendship.status = "rejected"
            flag = True
            
        friendship = session.query(Friendship).filter(
                ((Friendship.user1 ==  user2) & (Friendship.user2 ==  user1)&(Friendship.status == "requested")) 
            ).first()
        if friendship:
            friendship.status = "rejected"   
            flag = True

        session.commit()
        return flag
    
    
def delete_friend(user1, user2):
        with Session(engine) as session:
            # Check if both users exist
            user1_obj = session.get(User, user1)
            user2_obj = session.get(User, user2)
            if user1_obj is None or user2_obj is None:
                return False


            friendship1 = session.query(Friendship).filter(
                ((Friendship.user1 == user1) & (Friendship.user2 == user2)) |
                ((Friendship.user1 == user2) & (Friendship.user2 == user1))
            ).all()

            if not friendship1:
                return False  

            for friendship in friendship1:
                session.delete(friendship)

            session.commit()
            return True
        
def get_all_friends_name_of_current_user(username: str) -> list:
    with Session(engine) as session:
        remove_duplicate_friendships()
        friends = []     
        for row in session.query(Friendship).filter(Friendship.user1==username).filter(Friendship.status == 'accepted'):
            friends.append(row.user2)
        return friends

def get_all_friends_of_current_user(username: str) -> list:
    with Session(engine) as session:
        remove_duplicate_friendships()
        friends = []
        
        query = session.query(Friendship).filter(Friendship.user1 == username, Friendship.status == 'accepted')
        
        for row in query:
            friend_name = row.user2
            gender = db.get_user_sex(friend_name)
            major = db.get_user_major(friend_name)
            user_type = db.get_user_type(friend_name)
            friend_detail = f"gender: {gender}, type: {user_type}, major: {major}"
            friends.append({"name": friend_name, "detail": friend_detail})
        
        return friends
    
def get_all_request(username: str) -> list:
    with Session(engine) as session:
        remove_duplicate_friendships()
        friends = []
        for row in session.query(Friendship).filter(Friendship.user2==username).filter(Friendship.status == 'requested'):
            friends.append(row.user1)
        return friends
    
def get_all_request_to_sender(username: str) -> list:
    with Session(engine) as session:
        remove_duplicate_friendships()
        friends = []
        for row in session.query(Friendship).filter(Friendship.user1==username).filter(Friendship.status == 'requested'):
            friends.append(row.user2)
        return friends
    
def remove_duplicate_friendships():
    with Session(engine) as session:
        friendships = session.query(Friendship).order_by(Friendship.user1, Friendship.user2, Friendship.status).all()
        
        seen = set()
        duplicates = []

        for friendship in friendships:
            key = (friendship.user1, friendship.user2, friendship.status)
            if key in seen:
                duplicates.append(friendship)
            else:
                seen.add(key)

        for duplicate in duplicates:
            session.delete(duplicate)
        
        session.commit()



if __name__ == "__main__":
    request_friend("1","2")
    print(get_all_friends_of_current_user("2"))
