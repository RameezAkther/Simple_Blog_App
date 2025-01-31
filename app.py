from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from pymongo import MongoClient
from datetime import datetime
import bcrypt
from bson import ObjectId
import random
from markdown import markdown
from bleach import clean

# App Configuration
app = Flask(__name__)
app.secret_key = 'mlops_project_2'

# MongoDB Configuration
client = MongoClient('mongodb://localhost:27017/')
db = client.blog_db
users = db.users
posts = db.posts
comments = db.comments

# Random placeholder images for cards
PLACEHOLDER_IMAGES = [
    "https://img.freepik.com/free-vector/hand-drawn-butterfly-illustration_52683-114320.jpg?t=st=1738167531~exp=1738171131~hmac=8e13f4793a1f039b0c5de6c401ba3ba3cf2b03c773ba4a1003e3c4c6637c1c08",
    "https://img.freepik.com/free-vector/gradient-japanese-temple-with-lake_52683-45004.jpg?t=st=1738167531~exp=1738171131~hmac=9a199a405e63485307c324243ff90418776a24955fc2ec954f2d61abafccc045",
    "https://img.freepik.com/free-vector/flat-rafting-illustration_52683-104747.jpg?t=st=1738167531~exp=1738171131~hmac=4b24f6d1f66d20822938319a8596759f5a342d7f27a18bc9621765ce1c6999a9",
    "https://img.freepik.com/free-vector/hand-drawn-chinese-zodiac-animal-illustration_52683-103775.jpg?t=st=1738167531~exp=1738171131~hmac=bae50269aef8afe63a82e2fe90f4615f45d9749519891c7e3eb7acdd08affb32",
    "https://img.freepik.com/free-vector/gradient-flower-field-background_23-2150565151.jpg?t=st=1738167531~exp=1738171131~hmac=4a8498253c3629162e565d31b6029152690b8bb046808b827bc40d3fec8b9c3b",
    "https://img.freepik.com/free-vector/gradient-universe-background_23-2149635763.jpg?t=st=1738167531~exp=1738171131~hmac=4064dcf124fc0c78238e616000ce3106fbf2d77dc8c9a8c8bbe2819802720bbf"
]

# Home Route
@app.route('/')
def home():
    all_posts = list(posts.find().sort("created_at", -1))
    return render_template('index.html', posts=all_posts)

# User Registration
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        email = request.form['email']
        if users.find_one({"username": username}):
            flash('Username already exists!', 'danger')
            return redirect(url_for('register'))
        hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
        users.insert_one({"username": username, "password": hashed_password, "is_admin": False, "email": email})
        flash('Registration successful! Please login.', 'success')
        return redirect(url_for('login'))
    return render_template('register.html')

# User Login
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = users.find_one({"username": username})
        if user and bcrypt.checkpw(password.encode('utf-8'), user['password']):
            session['username'] = username
            session['is_admin'] = user.get('is_admin', False)
            flash('Login successful!', 'success')
            return redirect(url_for('home'))
        flash('Invalid username or password!', 'danger')
    return render_template('login.html')

# User Logout
@app.route('/logout')
def logout():
    session.clear()
    flash('Logged out successfully!', 'success')
    return redirect(url_for('home'))

# View Post
@app.route('/post/<post_id>')
def view_post(post_id):
    post = posts.find_one({"_id": ObjectId(post_id)})
    if not post:
        flash('Post not found.', 'danger')
        return redirect(url_for('home'))
    raw_html = markdown(post['content'])
    post['content'] = clean(raw_html, tags=['h1', 'h2', 'h3', 'p', 'strong', 'em', 'ul', 'ol', 'li', 'a', 'img'], attributes={'a': ['href'], 'img': ['src', 'alt', 'title']})
    post_comments = list(comments.find({"post_id": ObjectId(post_id)}).sort("created_at", -1))
    print(post_comments)
    return render_template('view_post.html', post=post, comments=post_comments)

# Add Post
@app.route('/add', methods=['GET', 'POST'])
def add_post():
    if 'username' not in session:
        return redirect(url_for('login'))
    if request.method == 'POST':
        title = request.form['title']
        content = request.form['markdown']
        image_url = request.form['image_url']
        if not image_url:
            image_url = random.choice(PLACEHOLDER_IMAGES)
        posts.insert_one({
            "title": title,
            "content": content,
            "image_url" : image_url,
            "author": session['username'],
            "created_at": datetime.now()
        })
        flash('Post added successfully!', 'success')
        return redirect(url_for('home'))
    return render_template('add_post.html')

# Update Post
@app.route('/edit/<post_id>', methods=['GET', 'POST'])
def edit_post(post_id):
    if 'username' not in session:
        return redirect(url_for('login'))
    post = posts.find_one({"_id": ObjectId(post_id)})
    if not post or post['author'] != session['username']:
        flash('You do not have permission to edit this post.', 'danger')
        return redirect(url_for('home'))
    if request.method == 'POST':
        title = request.form['title']
        content = request.form['markdown']
        image_url = request.form['image_url']
        if not image_url:
            image_url = random.choice(PLACEHOLDER_IMAGES)
        posts.update_one({"_id": ObjectId(post_id)}, {"$set": {"title": title, "content": content, "image_url": image_url}})
        flash('Post updated successfully!', 'success')
        return redirect(url_for('home'))
    return render_template('edit_post.html', post=post)

# Delete Post
@app.route('/delete/<post_id>')
def delete_post(post_id):
    if 'username' not in session:
        return redirect(url_for('login'))
    post = posts.find_one({"_id": ObjectId(post_id)})
    if not post:
        flash('Post not found.', 'danger')
        return redirect(url_for('home'))
    if post['author'] != session['username'] and not session.get('is_admin'):
        flash('You do not have permission to delete this post.', 'danger')
        return redirect(url_for('home'))
    posts.delete_one({"_id": ObjectId(post_id)})
    flash('Post deleted successfully!', 'success')
    return redirect(url_for('home'))

@app.route('/delete_user/<user_id>')
def delete_user(user_id):
    if not session.get('is_admin'):
        flash("Unauthorized action!", "danger")
        return redirect(url_for('admin'))

    users.delete_one({"_id": ObjectId(user_id)})
    flash("User deleted successfully!", "success")
    return redirect(url_for('admin'))

# Comment on Post
@app.route('/comment/<post_id>', methods=['POST'])
def add_comment(post_id):
    if 'username' not in session:
        flash('You must be logged in to comment.', 'danger')
        return redirect(url_for('login'))
    
    content = request.form['comment']
    if not content.strip():
        flash('Comment cannot be empty.', 'danger')
        return redirect(url_for('view_post', post_id=post_id))
    
    comment = {
        "post_id": ObjectId(post_id),
        "author": session['username'],
        "content": content,
        "created_at": datetime.now(),
        "upvotes": 0,
        "downvotes": 0
    }
    comments.insert_one(comment)
    flash('Comment added successfully!', 'success')
    return redirect(url_for('view_post', post_id=post_id))

@app.route('/upvote/<comment_id>', methods=['POST'])
def upvote_comment(comment_id):
    if 'username' not in session:
        return jsonify({"error": "You need to log in to vote"}), 401
    
    user = session['username']
    comment = comments.find_one({"_id": ObjectId(comment_id)})

    if not comment:
        return jsonify({"error": "Comment not found"}), 404

    voters = comment.get("voters", {})

    if voters.get(user) == "upvote":
        return jsonify({"error": "You have already upvoted"}), 400
    elif voters.get(user) == "downvote":
        # If the user previously downvoted, remove that and add an upvote
        comments.update_one({"_id": ObjectId(comment_id)}, {
            "$inc": {"upvotes": 1, "downvotes": -1},
            "$set": {f"voters.{user}": "upvote"}
        })
    else:
        # Normal upvote
        comments.update_one({"_id": ObjectId(comment_id)}, {
            "$inc": {"upvotes": 1},
            "$set": {f"voters.{user}": "upvote"}
        })

    updated_comment = comments.find_one({"_id": ObjectId(comment_id)})
    return jsonify({"upvotes": updated_comment["upvotes"], "downvotes": updated_comment["downvotes"]})


@app.route('/downvote/<comment_id>', methods=['POST'])
def downvote_comment(comment_id):
    if 'username' not in session:
        return jsonify({"error": "You need to log in to vote"}), 401
    
    user = session['username']
    comment = comments.find_one({"_id": ObjectId(comment_id)})

    if not comment:
        return jsonify({"error": "Comment not found"}), 404

    voters = comment.get("voters", {})

    if voters.get(user) == "downvote":
        return jsonify({"error": "You have already downvoted"}), 400
    elif voters.get(user) == "upvote":
        # If the user previously upvoted, remove that and add a downvote
        comments.update_one({"_id": ObjectId(comment_id)}, {
            "$inc": {"upvotes": -1, "downvotes": 1},
            "$set": {f"voters.{user}": "downvote"}
        })
    else:
        # Normal downvote
        comments.update_one({"_id": ObjectId(comment_id)}, {
            "$inc": {"downvotes": 1},
            "$set": {f"voters.{user}": "downvote"}
        })

    updated_comment = comments.find_one({"_id": ObjectId(comment_id)})
    return jsonify({"upvotes": updated_comment["upvotes"], "downvotes": updated_comment["downvotes"]})


# Delete Comment
@app.route('/delete_comment/<comment_id>/<post_id>')
def delete_comment(comment_id, post_id):
    comment = comments.find_one({"_id": ObjectId(comment_id)})

    if not comment:
        flash('Comment not found.', 'danger')
        return redirect(url_for('view_post', post_id=post_id))

    if session.get('username') == comment['author'] or session.get('is_admin'):
        comments.delete_one({"_id": ObjectId(comment_id)})
        flash('Comment deleted successfully.', 'success')
    else:
        flash('You are not authorized to delete this comment.', 'danger')

    return redirect(url_for('view_post', post_id=post_id))

# Admin View for All Posts
@app.route('/admin')
def admin():
    if not session.get('is_admin'):
        flash("Unauthorized access!", "danger")
        return redirect(url_for('home'))

    users_collection = users.find()
    total_users = users.count_documents({})
    total_blogs = posts.count_documents({})

    # Fetch user details along with blog count
    user_list = []
    for user in users_collection:
        blog_count = posts.count_documents({"author": user['username']})
        user_list.append({
            "_id": user["_id"],
            "username": user["username"],
            "email": user["email"],
            "blog_count": blog_count
        })

    return render_template('admin.html', users=user_list, total_users=total_users, total_blogs=total_blogs)

# Run the App
if __name__ == '__main__':
    app.run(debug=True)
