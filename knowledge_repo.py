import json
import os
from datetime import datetime, timedelta
from debug import d_print, d_error
import utils

def add_post(category, sender, title,content):
    # knowledge repo filepath
    os.makedirs('knowledge_repo', exist_ok=True)
    filepath = f'knowledge_repo/{category}.json'
    
    # Check existence
    if not os.path.exists(filepath):
        posts = []
    else:
        with open(filepath, 'r') as file:
            posts = json.load(file)
    
    # Find the smallest unused post_id
    existing_ids = {post['post_id'] for post in posts}
    post_id = 0
    while post_id in existing_ids:
        post_id += 1
    
    # Get current system time
    current_time = utils.get_current_sydney_time()
    
    new_post = {
        "post_id": post_id,
        "sender": sender,
        "title" : title,
        "content": content,
        "time": current_time,
        "comments": []
    }
    posts.append(new_post)

    with open(filepath, 'w') as file:
        json.dump(posts, file, indent=4)
    
    d_print('add_post', f'post added successfully, post_id: {post_id}, in {category}')
    return "success"

def del_post(category, post_id):
    filepath = f'knowledge_repo/{category}.json'

    if not os.path.exists(filepath):
        d_error("del_post", "No post in this category")
        return "No post in this category"

    with open(filepath, 'r') as file:
        posts = json.load(file)
    
    original_count = len(posts)
    posts = [post for post in posts if post['post_id'] != post_id]

    # If the length of the posts list has changed, a post was deleted
    if len(posts) < original_count:
        with open(filepath, 'w') as file:
            json.dump(posts, file, indent=4)
        d_print("del_post", f"Post with ID {post_id} has been deleted from the category '{category}'")
        return "success"
    else:
        d_error("del_post", f"No post with ID {post_id} found in the category '{category}'")
        return "No post with id found"
    
def modify_post(category, post_id, new_content):
    filepath = f'knowledge_repo/{category}.json'

    if not os.path.exists(filepath):
        d_error("modify_post", "No post in this category")
        return "No post in this category"

    # Read the existing posts
    with open(filepath, 'r') as file:
        posts = json.load(file)
    
    for post in posts:
        if post['post_id'] == post_id:
            current_time = utils.get_current_sydney_time()

            post['content'] = new_content
            post['time'] = current_time

            # Write the updated posts back to the file
            with open(filepath, 'w') as file:
                json.dump(posts, file, indent=4)

            d_print('modify_post', f'post modified successfully in {category}, post id {post_id}')
            return "success"

    d_error('modify_post', f'No post with id {post_id} found in {category}')
    return "No post with id found"

def add_comment(category, post_id, sender, content):
    filepath = f'knowledge_repo/{category}.json'

    if not os.path.exists(filepath):
        print(category)
        d_error("add_comment", "No post in this category")
        return "No post in this category"

    # Read the existing posts
    with open(filepath, 'r') as file:
        posts = json.load(file)
    
    for post in posts:
        if post['post_id'] == post_id:
            # Get the list of existing comment_ids to find the smallest unused comment_id
            existing_ids = {comment['comment_id'] for comment in post.get('comments', [])}
            comment_id = 0
            while comment_id in existing_ids:
                comment_id += 1

            current_time = utils.get_current_sydney_time()

            new_comment = {
                "comment_id": comment_id,
                "sender": sender,
                "content": content,
                "time": current_time
            }

            # Append the new comment to the post's comments list
            post.setdefault('comments', []).append(new_comment)

            # Write the updated posts back to the file
            with open(filepath, 'w') as file:
                json.dump(posts, file, indent=4)

            d_print('add_comment', f'comment add successfully to {category}, post id {post_id}. The comment id is {comment_id}')
            return "success"

    d_error('add_comment', f'No post with id {post_id} found in {category}')
    return "No post with id found"

def del_comment(category, post_id, comment_id):
    filepath = f'knowledge_repo/{category}.json'

    # Check if the category file exists
    if not os.path.exists(filepath):
        d_error("del_comment", "No post in this category")
        return "No post in this category"

    # Read the existing posts
    with open(filepath, 'r') as file:
        posts = json.load(file)

    # Variable to track if the comment was deleted
    comment_deleted = False

    # Iterate over posts to find the specified post
    for post in posts:
        if post['post_id'] == post_id:
            post_found = True
            # Extract the comments list
            comments = post.get('comments', [])
            # Remove the comment with the specified comment_id
            original_count = len(comments)
            comments = [comment for comment in comments if comment['comment_id'] != comment_id]
            # Check if any comment was deleted
            if len(comments) < original_count:
                post['comments'] = comments
                comment_deleted = True
                break
    
    if not post_found:
        d_error('del_comment', f'No post with id {post_id} found in {category}')
        return "No post with id found"

    if comment_deleted:
        # Write the updated posts back to the file
        with open(filepath, 'w') as file:
            json.dump(posts, file, indent=4)
        d_print("del_comment", f"Comment with ID {comment_id} has been deleted from post ID {post_id} in the category '{category}'")
    else:
        d_error("del_comment", f"No comment with ID {comment_id} found in post ID {post_id}" in {category})
        return f"No comment with id{comment_id} found"

    return "success"


def get_content(category, post_id):
    filepath = f'knowledge_repo/{category}.json'
    with open(filepath, 'r') as file:
        posts = json.load(file)
    for post in posts:
        if post['post_id'] == post_id:
            return post.get('content', 'Content not found')
    return 'Post not found'

def get_title(category, post_id):
    filepath = f'knowledge_repo/{category}.json'
    with open(filepath, 'r') as file:
        posts = json.load(file)
    for post in posts:
        if post['post_id'] == post_id:
            return post.get('title', 'Title not found')
    return 'Post not found'

def get_time(category, post_id):
    filepath = f'knowledge_repo/{category}.json'
    with open(filepath, 'r') as file:
        posts = json.load(file)
    for post in posts:
        if post['post_id'] == post_id:
            return post.get('time', 'Time not found')
    return 'Post not found'

def get_comments(category, post_id):
    filepath = f'knowledge_repo/{category}.json'
    with open(filepath, 'r') as file:
        posts = json.load(file)
    for post in posts:
        if post['post_id'] == post_id:
            return post.get('comments', [])
    return 'Post not found'

def get_comment_sender(category, post_id, comment_id):
    comments = get_comments(category, post_id)
    if comments == 'Post not found':
        return 'Post not found'
    
    for comment in comments:
        if comment['comment_id'] == comment_id:
            return comment.get('sender', 'Sender not found')
    
    return 'Comment not found'

def get_sender(category, post_id):
    filepath = f'knowledge_repo/{category}.json'
    with open(filepath, 'r') as file:
        posts = json.load(file)
    for post in posts:
        if post['post_id'] == post_id:
            return post.get('sender', 'Sender not found')
    return 'Post not found'
    
def get_all_titles(category):
    filepath = f'knowledge_repo/{category}.json'
    with open(filepath, 'r') as file:
        posts = json.load(file)
    titles = []
    for post in posts:
        title = post.get('title', 'Title not found')
        id = post.get("post_id")
        titles.append({id: title})

    return titles

if __name__ == "__main__":
    # del_post("software_engineering", 2)
    #add_post("software_engineering", "2", "test2","hello")
    
    comments = get_content("software_engineering" , 1)
    print(comments)