from app import db
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

class User(db.Model):
    __tablename__ = 'users'
    user_id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class Category(db.Model):
    __tablename__ = 'categories'
    category_id = db.Column(db.Integer, primary_key=True)
    category_name = db.Column(db.String(100), unique=True, nullable=False)

class Book(db.Model):
    __tablename__ = 'books'
    book_id = db.Column(db.Integer, primary_key=True)
    book_title = db.Column(db.String(100), nullable=False)
    book_category = db.Column(db.Integer, db.ForeignKey('categories.category_id'), nullable=False)
    book_image_url = db.Column(db.String(200))  # URL or file path for the book image
    book_author = db.Column(db.String(255), nullable=False)
    book_description = db.Column(db.Text)
    book_isbn = db.Column(db.String(13), unique=False, nullable=False)  # ISBN is unique
    book_owner_id = db.Column(db.Integer, db.ForeignKey('users.user_id'), nullable=False)

class Comment(db.Model):
    __tablename__ = 'comments'
    comment_id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.user_id'), nullable=False)
    book_id = db.Column(db.Integer, db.ForeignKey('books.book_id'), nullable=False)
    rating = db.Column(db.Integer, nullable=False)
    comment = db.Column(db.String(255), unique=False, nullable=False)

class Request(db.Model):
    __tablename__ = 'requests'
    request_id = db.Column(db.Integer, primary_key=True)
    request_date = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    sender_id = db.Column(db.Integer, db.ForeignKey('users.user_id'), nullable=False)
    receiver_id = db.Column(db.Integer, db.ForeignKey('users.user_id'), nullable=False)
    request_book_id = db.Column(db.Integer, db.ForeignKey('books.book_id'), nullable=False)
    exchange_book_id = db.Column(db.Integer, db.ForeignKey('books.book_id'))
    sender_comment = db.Column(db.String(255), unique=False)
    owner_comment = db.Column(db.String(255), unique=False)
    request_status = db.Column(db.String(255), default='Pending', nullable=False)
