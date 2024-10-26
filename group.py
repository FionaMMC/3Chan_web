from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
from models import *
from pathlib import Path
import os
import friend

Path("database") \
    .mkdir(exist_ok=True)

engine = create_engine("sqlite:///database/main.db", echo=False)



def create_new_group(initiator_username: str, invited: list):
    with Session(engine) as session:
        try:
            # Create a new GroupList instance
            new_group = GroupList()
            session.add(new_group)
            session.flush()  

            # Add the initiating user with a status of 'joined'
            initiator = session.query(User).filter_by(username=initiator_username).one()
            joined_member = GroupMember(user=initiator, group=new_group, status='joined')
            session.add(joined_member)
            
            existing_members = {member.user.username for member in new_group.members}


            # Process the invited list
            for username in invited:
                if username not in existing_members:
                    user = session.query(User).filter_by(username=username).first()
                    if user:
                        invited_member = GroupMember(user=user, group=new_group, status='invited')
                        session.add(invited_member)
                    else:
                        print(f"User {username} not found and will not be added to the group.")
                else:
                    print(f"User {username} is already a member and will not be added again.")

            # Commit all changes
            session.commit()
            return True
        except SQLAlchemyError as e:
            session.rollback()
            print(f"An error occurred: {e}")
            return False
        
def leave_group(group_id, user_username):
    with Session(engine) as session:
        try:
            member = session.query(GroupMember).filter_by(group_id=group_id, user_username=user_username, status='joined').one_or_none()
            
            if member:
                session.delete(member)
                session.commit()
                print(f"User {user_username} has successfully left the group {group_id}.")
            else:
                # If the member is not found or not joined
                print(f"User {user_username} is not a joined member of group {group_id} or does not exist.")
            cleanup_empty_group(group_id)
        
        except SQLAlchemyError as e:
            session.rollback()
            print(f"Failed to process leave operation: {e}")
def accept_invitation(group_id, user_username):
    with Session(engine) as session:
        try:
            # Check if the user is already a 'joined' member of the group
            if session.query(GroupMember).filter_by(group_id=group_id, user_username=user_username, status='joined').first():
                print(f"User {user_username} is already a joined member of group {group_id}.")
                return False
            
            # Find all invited entries for the user in the group
            invited_members = session.query(GroupMember).filter_by(group_id=group_id, user_username=user_username, status='invited').all()
            
            if invited_members:
                # Change status from 'invited' to 'joined' for all entries
                for member in invited_members:
                    member.status = 'joined'
                session.commit()
                print(f"User {user_username} has accepted the invitation and is now a joined member of group {group_id}.")
                return True
            else:
                print(f"No invitations found for user {user_username} in group {group_id}.")
                return False

        except SQLAlchemyError as e:
            session.rollback()
            print(f"Failed to accept invitation: {e}")
            return False
            
def reject_invitation(group_id, user_username):
    with Session(engine) as session:
        try:
            # Find all invited entries for the user in the group
            invited_members = session.query(GroupMember).filter_by(group_id=group_id, user_username=user_username, status='invited').all()
            
            if invited_members:
                # Delete all invited entries
                for member in invited_members:
                    session.delete(member)
                session.commit()
                print(f"User {user_username} has rejected the invitation and has been removed from the invited list of group {group_id}.")
                return True
            else:
                print(f"No invitations found for user {user_username} in group {group_id}.")
                return False

        except SQLAlchemyError as e:
            session.rollback()
            print(f"Failed to reject invitation: {e}")
            return False

  
def clear_group_members():
    with Session(engine) as session:
        try:
            # Delete all entries from the group_member table
            session.query(GroupMember).delete()
            
            # Commit the changes to the database
            session.commit()
            print("All group members have been removed successfully.")
        except SQLAlchemyError as e:
            # Roll back in case of an error
            session.rollback()
            print(f"Failed to clear group members: {e}")
            
def cleanup_empty_group(group_id):
    with Session(engine) as session:
        try:
            # Check if there are any 'invited' or 'joined' members in the group
            member_count = session.query(GroupMember).filter_by(group_id=group_id).count()
            
            if member_count == 0:
                # No members found, proceed to delete the group
                group_to_delete = session.query(GroupList).filter_by(id=group_id).one_or_none()
                
                if group_to_delete:
                    session.delete(group_to_delete)
                    session.commit()
                    print(f"Group {group_id} has been deleted as it had no members.")
                else:
                    print(f"Group {group_id} not found.")
            else:
                print(f"Group {group_id} has members and cannot be deleted.")

        except SQLAlchemyError as e:
            session.rollback()
            print(f"Failed to delete empty group: {e}")
            
def invite_member(sender_name, receiver_username, group_id):
    with Session(engine) as session:
        try:
            # Retrieve all friends of the sender
            friends = friend.get_all_friends_of_current_user(sender_name)
            if receiver_username not in friends:
                print(f"User {receiver_username} is not in the list of friends of {sender_name}.")
                return
            
            # Check if the receiver exists
            user = session.query(User).filter_by(username=receiver_username).one_or_none()
            if not user:
                print(f"No such user with username: {receiver_username}")
                return
            
            # Check if the receiver is already a member of the group
            existing_member = session.query(GroupMember).filter_by(group_id=group_id, user_username=receiver_username).first()
            if existing_member:
                print(f"User {receiver_username} is already a member of the group {group_id} with status {existing_member.status}.")
                return
            
            # Create a new GroupMember as 'invited'
            new_member = GroupMember(group_id=group_id, user_username=receiver_username, status='invited')
            session.add(new_member)
            session.commit()
            print(f"User {receiver_username} has been successfully invited to group {group_id} by {sender_name}.")

        except SQLAlchemyError as e:
            session.rollback()
            print(f"Failed to invite member: {e}")
            
def get_invited_members(group_id):
    with Session(engine) as session:
        try:
            # Query for all 'invited' members in the specified group
            invited_members = session.query(GroupMember.user_username).filter_by(group_id=group_id, status='invited').all()
            # Extract usernames from the result and return them
            invited_usernames = [member.user_username for member in invited_members]
            return invited_usernames
        except Exception as e:
            print(f"Failed to retrieve invited members: {e}")
            return []
def get_joined_members(group_id):
    with Session(engine) as session:
        try:
            # Query for all 'joined' members in the specified group
            joined_members = session.query(GroupMember.user_username).filter_by(group_id=group_id, status='joined').all()
            # Extract usernames from the result and return them
            joined_usernames = [member.user_username for member in joined_members]
            return joined_usernames
        except Exception as e:
            print(f"Failed to retrieve joined members: {e}")
            return []
def get_joined_groups(user_username):
    with Session(engine) as session:
        try:
            # Query for all group IDs where the user has 'joined' status
            joined_groups = session.query(GroupMember.group_id).filter_by(user_username=user_username, status='joined').all()
            # Extract group IDs from the query results
            joined_group_ids = [group.group_id for group in joined_groups]
            return joined_group_ids
        except Exception as e:
            print(f"Failed to retrieve joined groups for user {user_username}: {e}")
            return []
def pending_invotation(user_username):
    with Session(engine) as session:
        try:
            # Query for all group IDs where the user has 'joined' status
            joined_groups = session.query(GroupMember.group_id).filter_by(user_username=user_username, status='invited').all()
            # Extract group IDs from the query results
            joined_group_ids = [group.group_id for group in joined_groups]
            return joined_group_ids
        except Exception as e:
            print(f"Failed to retrieve joined groups for user {user_username}: {e}")
            return []
