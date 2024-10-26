from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import *
from sqlalchemy.orm import Session
from sqlalchemy import inspect
import sqlite3

db_file = "database/main.db"
DATABASE_URI = 'sqlite:///database/main.db'
engine = create_engine(DATABASE_URI)
Session = sessionmaker(bind=engine)


def delete_user(username):
    session = Session()
    user = session.query(User).filter_by(username=username).first()
    if user:
        session.delete(user)
        session.commit()
        print(f" {username} deleted")
    else:
        print(f"{username} not fuound")
    session.close()

def change_user_password(username, new_password):
    session = Session()
    user = session.query(User).filter_by(username=username).first()
    if user:
        user.password = new_password 
        session.commit()
        print(f"{username} password modified")
    else:
        print(f"{username} not found")
    session.close()

def print_all_table(db_file):
    conn = sqlite3.connect('database/main.db')
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cursor.fetchall()
    for table in tables:
        print(table[0])
    conn.close()

def print_table(db_file, table_name):
    conn = sqlite3.connect(db_file)
    cursor = conn.cursor()

    #test if table exists
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?;", (table_name,))
    if cursor.fetchone() is None:
        print(f"Table '{table_name}' does not exist.")
        conn.close()
        return  
    
    query = f"SELECT * FROM {table_name}"
    cursor.execute(query)
    rows = cursor.fetchall()
    for row in rows:
        print(row)
    conn.close()

def check_table_exists(tableName):
    inspector = inspect(engine)
    return inspector.has_table(tableName)

def delete_friendship(user1_username, user2_username):
    session = Session()
    friendship = session.query(Friendship).filter(
        ((Friendship.user1 == user1_username) & (Friendship.user2 == user2_username)) |
        ((Friendship.user1 == user2_username) & (Friendship.user2 == user1_username))
    ).first()
    if friendship:
        session.delete(friendship)
        session.commit()
        print(f"Friendship between {user1_username} and {user2_username} deleted")
    else:
        print("Friendship not found")
    session.close()
    
def change_friendship_status(user1_username, user2_username, new_status):
    session = Session()
    friendship = session.query(Friendship).filter(
        ((Friendship.user1 == user1_username) & (Friendship.user2 == user2_username)) |
        ((Friendship.user1 == user2_username) & (Friendship.user2 == user1_username))
    ).first()
    if friendship:
        friendship.status = new_status
        session.commit()
        print(f"Status of friendship between {user1_username} and {user2_username} updated to {new_status}")
    else:
        print("Friendship not found")
    session.close()


if __name__ == "__main__":
    print_table(db_file, "user")
    