from flask import render_template, redirect, url_for, flash, request, session
from app import db
from app.models import User, Category, Book, Request
from sqlalchemy import or_, and_
from datetime import datetime

def register_routes(app):
    @app.route('/')
    def index():
        # Get query parameters
        category_id = request.args.get('category_id')
        filter_param = request.args.get('filter')
        search_query = request.args.get('search', '').strip()

        # Fetch categories
        categories = Category.query.all()

        # Initialize books query
        books_query = Book.query

        # Apply category filter if provided
        if category_id:
            try:
                category_id = int(category_id)
                books_query = books_query.filter_by(book_category=category_id)
            except ValueError:
                pass  # Fallback to no category filter if invalid

        notifications = []
        if 'user_id' in session:
            user = User.query.get(session['user_id'])
            userbooks_query = Book.query.filter_by(book_owner_id=user.user_id)

            # Use userbooks_query if filter=my_books, otherwise use books_query
            active_query = userbooks_query if filter_param == 'my_books' else books_query

            # Apply search filter to the active query
            if search_query:
                search_terms = search_query.split()
                search_conditions = []

                for term in search_terms:
                    if term:  # Skip empty terms
                        title_patterns = [f'{term} %', f'% {term} %', f'% {term}']
                        author_patterns = [f'{term} %', f'% {term} %', f'% {term}']
                        for title_pattern in title_patterns:
                            search_conditions.append(Book.book_title.like(title_pattern))
                        for author_pattern in author_patterns:
                            search_conditions.append(Book.book_author.like(author_pattern))

                    if search_query.replace('-', '').isdigit() and len(search_query.replace('-', '')) == 13:
                        search_conditions.append(Book.book_isbn == search_query.replace('-', ''))

                if search_conditions:
                    active_query = active_query.filter(or_(*search_conditions)).distinct()

            # Execute query to get books
            books = active_query.all()
            userbooks = userbooks_query.all()

            # Fetch sent and received requests
            sent_requests = Request.query.filter_by(sender_id=user.user_id).all()
            received_requests = Request.query.filter_by(receiver_id=user.user_id).all()

            # Combine and prepare notifications
            for req in sent_requests + received_requests:
                book = Book.query.get(req.request_book_id)
                sender_books = db.session.query(Book, Category).join(Category, Book.book_category == Category.category_id).filter(Book.book_owner_id == req.sender_id).all() if req.receiver_id == user.user_id else []
                swap_book = Book.query.get(req.exchange_book_id) if req.exchange_book_id else None
                sender_user = User.query.get(req.sender_id)
                receiver_user = User.query.get(req.receiver_id)
                hours_ago = int((datetime.utcnow() - req.request_date).total_seconds() // 3600)
                status_class = {
                    'Pending': 'badge bg-primary',
                    'Confirmed': 'badge bg-warning',
                    'Approved': 'badge bg-success',
                    'Declined': 'badge bg-danger'
                }.get(req.request_status, 'badge bg-primary')

                notifications.append({
                    'request_id': req.request_id,
                    'book_image_url': book.book_image_url,
                    'book_title': book.book_title,
                    'sender_comment': req.sender_comment,
                    'request_status': req.request_status,
                    'status_class': status_class,
                    'hours_ago': hours_ago,
                    'is_sender': req.sender_id == user.user_id,
                    'book': book,
                    'sender_books': sender_books,
                    'exchange_book_id': req.exchange_book_id,
                    'owner_comment': req.owner_comment,
                    'swap_book': swap_book,
                    'sender_user': sender_user,
                    'receiver_user': receiver_user
                })
            # for req in sent_requests + received_requests:
            #     book = Book.query.get(req.request_book_id)
            #     sender_books = db.session.query(Book, Category).join(Category, Book.book_category == Category.category_id).filter(Book.book_owner_id == req.sender_id).all() if req.receiver_id == user.user_id else []
            #     swap_book = Book.query.get(req.exchange_book_id) if req.exchange_book_id else None
            #     hours_ago = int((datetime.utcnow() - req.request_date).total_seconds() // 3600)
            #     status_class = {
            #         'Pending': 'badge bg-primary',
            #         'Confirmed': 'badge bg-warning',
            #         'Approved': 'badge bg-success'
            #     }.get(req.request_status, 'badge bg-primary')
            #
            #     notifications.append({
            #         'request_id': req.request_id,
            #         'book_image_url': book.book_image_url,
            #         'book_title': book.book_title,
            #         'sender_comment': req.sender_comment,
            #         'request_status': req.request_status,
            #         'status_class': status_class,
            #         'hours_ago': hours_ago,
            #         'is_sender': req.sender_id == user.user_id,
            #         'book': book,
            #         'sender_books': sender_books,
            #         'exchange_book_id': req.exchange_book_id,
            #         'owner_comment': req.owner_comment,
            #         'swap_book': swap_book
            #     })

            # Get book IDs with pending requests by the current user
            pending_request_book_ids = [req.request_book_id for req in sent_requests if req.request_status == 'Pending']
            confirmed_request_book_ids = [req.request_book_id for req in sent_requests if req.request_status == 'Confirmed']
            approved_request_book_ids = [req.request_book_id for req in sent_requests if req.request_status == 'Approved']

            return render_template('index.html', registered=True, user=user, categories=categories, books=books, userbooks=userbooks, category_id=category_id, search_query=search_query, notifications=notifications, pending_request_book_ids=pending_request_book_ids, confirmed_request_book_ids=confirmed_request_book_ids, approved_request_book_ids=approved_request_book_ids)
        else:
            # Apply search filter to books_query for non-logged-in users
            if search_query:
                search_terms = search_query.split()
                search_conditions = []

                for term in search_terms:
                    if term:  # Skip empty terms
                        title_patterns = [f'{term} %', f'% {term} %', f'% {term}']
                        author_patterns = [f'{term} %', f'% {term} %', f'% {term}']
                        for title_pattern in title_patterns:
                            search_conditions.append(Book.book_title.like(title_pattern))
                        for author_pattern in author_patterns:
                            search_conditions.append(Book.book_author.like(author_pattern))

                    if search_query.replace('-', '').isdigit() and len(search_query.replace('-', '')) == 13:
                        search_conditions.append(Book.book_isbn == search_query.replace('-', ''))

                if search_conditions:
                    books_query = books_query.filter(or_(*search_conditions)).distinct()

            books = books_query.all()

            return render_template('index.html', registered=False, user=None, categories=categories, books=books, userbooks=[], category_id=category_id, search_query=search_query, notifications=[], pending_request_book_ids=[], confirmed_request_book_ids=[], approved_request_book_ids=[])

    @app.route('/confirm_request/<int:request_id>', methods=['GET', 'POST'])
    def confirm_request(request_id):
        if 'user_id' not in session:
            flash('Please log in to confirm a request')
            return redirect(url_for('login'))

        req = Request.query.get_or_404(request_id)
        if req.receiver_id != session['user_id']:
            flash('You can only confirm requests sent to you')
            return redirect(url_for('index'))

        book = Book.query.get(req.request_book_id)
        sender = User.query.get(req.sender_id)
        sender_books = db.session.query(Book, Category).join(Category, Book.book_category == Category.category_id).filter(Book.book_owner_id == sender.user_id).all()

        if request.method == 'POST':
            action = request.form.get('action')
            owner_comment = request.form.get('owner_comment')
            exchange_book_id = request.form.get('sender_books')

            if not owner_comment:
                flash('Please provide a comment')
                return redirect(url_for('confirm_request', request_id=request_id))

            try:
                if action == 'confirm':
                    if not exchange_book_id:
                        flash('Please select a book to propose for the swap')
                        return redirect(url_for('confirm_request', request_id=request_id))
                    req.exchange_book_id = int(exchange_book_id)
                    req.owner_comment = owner_comment
                    req.request_status = 'Confirmed'
                elif action == 'decline':
                    req.owner_comment = owner_comment
                    req.request_status = 'Declined'
                else:
                    flash('Invalid action')
                    return redirect(url_for('confirm_request', request_id=request_id))

                db.session.commit()
                return redirect(url_for('index'))
            except Exception as e:
                db.session.rollback()
                flash('An error occurred while processing the request')
                return redirect(url_for('confirm_request', request_id=request_id))

        return render_template('confirmRequest.html', book=book, req=req, sender_books=sender_books)

    # @app.route('/confirm_request/<int:request_id>', methods=['GET', 'POST'])
    # def confirm_request(request_id):
    #     if 'user_id' not in session:
    #         flash('Please log in to confirm a request')
    #         return redirect(url_for('login'))
    #
    #     req = Request.query.get_or_404(request_id)
    #     if req.receiver_id != session['user_id']:
    #         flash('You can only confirm requests sent to you')
    #         return redirect(url_for('index'))
    #
    #     book = Book.query.get(req.request_book_id)
    #     sender = User.query.get(req.sender_id)
    #     sender_books = db.session.query(Book, Category).join(Category, Book.book_category == Category.category_id).filter(Book.book_owner_id == sender.user_id).all()
    #
    #     if request.method == 'POST':
    #         exchange_book_id = request.form.get('sender_books')
    #         owner_comment = request.form.get('owner_comment')
    #
    #         if not exchange_book_id or not owner_comment:
    #             flash('Please select a book and provide a comment')
    #             return redirect(url_for('confirm_request', request_id=request_id))
    #
    #         try:
    #             req.exchange_book_id = int(exchange_book_id)
    #             req.owner_comment = owner_comment
    #             req.request_status = 'Confirmed'
    #             db.session.commit()
    #             # flash('Swap proposal sent successfully!')
    #             return redirect(url_for('index'))
    #         except Exception as e:
    #             db.session.rollback()
    #             flash('An error occurred while confirming the request')
    #             return redirect(url_for('confirm_request', request_id=request_id))
    #
    #     return render_template('confirmRequest.html', book=book, req=req, sender_books=sender_books)

    @app.route('/confirm_swap/<int:request_id>', methods=['POST'])
    def confirm_swap(request_id):
        if 'user_id' not in session:
            flash('Please log in to confirm a swap')
            return redirect(url_for('login'))

        req = Request.query.get_or_404(request_id)
        if req.sender_id != session['user_id']:
            flash('You can only confirm swaps for your own requests')
            return redirect(url_for('index'))

        if req.request_status != 'Confirmed':
            flash('This request is not in a confirmable state')
            return redirect(url_for('index'))

        try:
            req.request_status = 'Approved'
            db.session.commit()
            # flash('Book swap confirmed successfully!')
            return redirect(url_for('index'))
        except Exception as e:
            db.session.rollback()
            flash('An error occurred while confirming the swap')
            return redirect(url_for('index'))

    @app.route('/delete_request/<int:request_id>', methods=['POST'])
    def delete_request(request_id):
        if 'user_id' not in session:
            flash('Please log in to delete a request')
            return redirect(url_for('login'))

        req = Request.query.get_or_404(request_id)
        if req.sender_id != session['user_id'] and req.receiver_id != session['user_id']:
            flash('You can only delete your own requests or requests sent to you')
            return redirect(url_for('index'))

        try:
            db.session.delete(req)
            db.session.commit()
            flash('Request deleted successfully!')
        except Exception as e:
            db.session.rollback()
            flash('An error occurred while deleting the request')
        return redirect(url_for('index'))

    # Existing routes (unchanged for brevity, but included for completeness)
    @app.route('/register', methods=['GET', 'POST'])
    def register():
        if request.method == 'POST':
            username = request.form['username']
            email = request.form['email']
            password = request.form['password']
            password_confirm = request.form['password_confirm']

            if password != password_confirm:
                flash('Passwords do not match')
                return redirect(url_for('register'))

            if User.query.filter_by(email=email).first():
                flash('Email already registered')
                return redirect(url_for('register'))

            if User.query.filter_by(username=username).first():
                flash('Username already taken')
                return redirect(url_for('register'))

            user = User(username=username, email=email)
            user.set_password(password)
            db.session.add(user)
            db.session.commit()
            return redirect(url_for('login'))

        return render_template('register.html')

    @app.route('/login', methods=['GET', 'POST'])
    def login():
        if request.method == 'POST':
            email = request.form['email']
            password = request.form['password']

            user = User.query.filter_by(email=email).first()
            if user and user.check_password(password):
                session['user_id'] = user.user_id
                return redirect(url_for('index'))

            flash('Invalid email or password')
            return redirect(url_for('login'))

        return render_template('login.html')

    @app.route('/logout')
    def logout():
        session.pop('user_id', None)
        return redirect(url_for('index'))

    @app.route('/profile', methods=['POST'])
    def update_profile():
        if 'user_id' not in session:
            flash('Please log in to update your profile')
            return redirect(url_for('login'))

        user = User.query.get(session['user_id'])
        username = request.form['username']
        email = request.form['email']
        password = request.form.get('password')
        password_confirm = request.form.get('password_confirm')

        existing_user = User.query.filter_by(username=username).first()
        if existing_user and existing_user.user_id != user.user_id:
            flash('Username already taken')
            return redirect(url_for('index'))

        existing_email = User.query.filter_by(email=email).first()
        if existing_email and existing_email.user_id != user.user_id:
            flash('Email already registered')
            return redirect(url_for('index'))

        if password and password != password_confirm:
            flash('Passwords do not match')
            return redirect(url_for('index'))

        user.username = username
        user.email = email
        if password:
            user.set_password(password)

        db.session.commit()
        flash('Profile updated successfully')
        return redirect(url_for('index'))

    @app.route('/add_book', methods=['GET', 'POST'])
    def add_book():
        if 'user_id' not in session:
            flash('Please log in to add a book')
            return redirect(url_for('login'))

        if request.method == 'POST':
            book_title = request.form['book_title']
            book_category = request.form['book_category']
            book_image_url = request.form['book_image_url']
            book_author = request.form['book_author']
            book_description = request.form['book_description']
            book_isbn = request.form['book_isbn']

            if not all([book_title, book_category, book_image_url, book_author, book_description, book_isbn]):
                flash('All required fields must be filled')
                return redirect(url_for('add_book'))

            if not Category.query.get(book_category):
                flash('Invalid category selected')
                return redirect(url_for('add_book'))

            user_id = session['user_id']
            new_book = Book(
                book_title=book_title,
                book_category=book_category,
                book_image_url=book_image_url,
                book_author=book_author,
                book_description=book_description,
                book_isbn=book_isbn,
                book_owner_id=user_id
            )

            try:
                db.session.add(new_book)
                db.session.commit()
                flash('Book added successfully!')
                return redirect(url_for('index'))
            except Exception as e:
                db.session.rollback()
                flash('An error occurred while adding the book')
                return redirect(url_for('add_book'))

        return render_template('addbook.html')

    @app.route('/edit_book/<int:book_id>', methods=['GET', 'POST'])
    def edit_book(book_id):
        if 'user_id' not in session:
            flash('Please log in to edit a book')
            return redirect(url_for('login'))

        book = Book.query.get_or_404(book_id)
        if book.book_owner_id != session['user_id']:
            flash('You can only edit your own books')
            return redirect(url_for('index'))

        categories = Category.query.all()

        if request.method == 'POST':
            if request.form.get('delete') == 'true':
                try:
                    db.session.delete(book)
                    db.session.commit()
                    flash('Book deleted successfully!')
                    return redirect(url_for('index'))
                except Exception as e:
                    db.session.rollback()
                    flash('An error occurred while deleting the book')
                    return redirect(url_for('edit_book', book_id=book_id))

            book_title = request.form['book_title']
            book_category = request.form['book_category']
            book_image_url = request.form['book_image_url']
            book_author = request.form['book_author']
            book_description = request.form['book_description']
            book_isbn = request.form['book_isbn']

            if not all([book_title, book_category, book_image_url, book_author, book_description, book_isbn]):
                flash('All required fields must be filled')
                return redirect(url_for('edit_book', book_id=book_id))

            if not Category.query.get(book_category):
                flash('Invalid category selected')
                return redirect(url_for('edit_book', book_id=book_id))

            try:
                book.book_title = book_title
                book.book_category = book_category
                book.book_image_url = book_image_url
                book.book_author = book_author
                book.book_description = book_description
                book.book_isbn = book_isbn

                db.session.commit()
                return redirect(url_for('index'))
            except Exception as e:
                db.session.rollback()
                flash('An error occurred while updating the book')
                return redirect(url_for('edit_book', book_id=book_id))

        return render_template('editbook.html', book=book, categories=categories)

    @app.route('/send_request/<int:book_id>', methods=['POST'])
    def send_request(book_id):
        if 'user_id' not in session:
            flash('Please log in to send a request')
            return redirect(url_for('login'))

        book = Book.query.get_or_404(book_id)
        sender_id = session['user_id']

        if sender_id == book.book_owner_id:
            flash('You cannot send a request for your own book')
            return redirect(url_for('index'))

        request_comment = request.form.get('request_comment')
        if not request_comment:
            flash('Comment is required')
            return redirect(url_for('index'))

        new_request = Request(
            sender_id=sender_id,
            receiver_id=book.book_owner_id,
            request_book_id=book.book_id,
            sender_comment=request_comment
        )

        try:
            db.session.add(new_request)
            db.session.commit()
            return redirect(url_for('index'))
        except Exception as e:
            db.session.rollback()
            flash('An error occurred while sending the request')
            return redirect(url_for('index'))
