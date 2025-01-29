from pymongo import MongoClient
import bcrypt

# Connect to MongoDB
client = MongoClient("mongodb://localhost:27017/")
db = client.blog_db

# Drop existing collections (optional, for a clean slate)
db.users.drop()
db.posts.drop()

# Create collections
users = db.users
posts = db.posts

# Insert an admin user
admin_password = "admin123"
hashed_admin_password = bcrypt.hashpw(admin_password.encode('utf-8'), bcrypt.gensalt())
users.insert_one({
    "username": "admin",
    "password": hashed_admin_password,
    "email": "admin@example.com",
    "is_admin": True
})

# Insert a sample user
user_password = "user123"
hashed_user_password = bcrypt.hashpw(user_password.encode('utf-8'), bcrypt.gensalt())
users.insert_one({
    "username": "test_user",
    "password": hashed_user_password,
    "email": "test@example.com",
    "is_admin": False
})

# Insert sample posts
posts.insert_many([
    {
        "title": "Welcome to the Blog",
        "content": "This is the first post on the blog. Enjoy your stay!",
        "author": "admin",
        "image_path": "",
        "created_at": "2025-01-28T10:00:00"
    },
    {
        "title": "Test User's Post",
        "content": "Hello! This is a test post by a regular user.",
        "author": "test_user",
        "image_path": "",
        "created_at": "2025-01-28T11:00:00"
    }
])

print("Database setup complete!")
