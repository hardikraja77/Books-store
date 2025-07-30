from flask import Flask, render_template, request, redirect, session
import sqlite3
import os
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = 'your_secret_key'

UPLOAD_FOLDER = 'static/uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

def get_db():
    con = sqlite3.connect('bookstore.db')
    con.row_factory = sqlite3.Row  # This enables dictionary-style access
    return con

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Home page - show all books
@app.route('/')
def home():
    con = get_db()
    cur = con.cursor()
    cur.execute("SELECT * FROM books")
    books = cur.fetchall()
    con.close()
    return render_template('index.html', books=books)

@app.route('/login', methods=['GET', 'POST'])
def login():
    next_url = request.args.get('next') or '/'
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        con = get_db()
        cur = con.cursor()
        cur.execute("SELECT * FROM users WHERE email=? AND password=?", (email, password))
        user = cur.fetchone()
        con.close()
        if user:
            session['user_id'] = user[0]
            return redirect(next_url)
        else:
            return "Invalid login"
    return render_template('login.html', next=next_url)


@app.route('/order/<int:book_id>')
def order(book_id):
    if 'user_id' not in session:
        # Not logged in, redirect to login with next URL to return
        return redirect(f'/login?next=/order/{book_id}')

    user_id = session['user_id']
    con = get_db()
    cur = con.cursor()
    cur.execute("INSERT INTO orders (user_id, book_id) VALUES (?, ?)", (user_id, book_id))
    con.commit()
    con.close()
    return "✅ Order Placed Successfully!"


@app.route('/admin')
def admin():
    if 'admin_id' not in session:
        return redirect('/admin/login')

    con = get_db()
    cur = con.cursor()
    cur.execute("""
        SELECT orders.id, users.name AS user_name, users.email, books.name AS book_name, books.author
        FROM orders
        JOIN users ON orders.user_id = users.id
        JOIN books ON orders.book_id = books.id
    """)
    orders = cur.fetchall()
    con.close()
    return render_template('admin.html', orders=orders)


# Create admin manually
@app.route('/create-admin')
def create_admin():
    con = get_db()
    cur = con.cursor()
    try:
        cur.execute("INSERT INTO admin (username, email, password) VALUES (?, ?, ?)",
                    ('Raja', 'raja@gmail.com', 'admin'))
        con.commit()
        return "Admin user created!"
    except sqlite3.IntegrityError:
        return "Admin already exists!"
    finally:
        con.close()

# Admin login
@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        con = get_db()
        cur = con.cursor()
        cur.execute("SELECT * FROM admin WHERE email=? AND password=?", (email, password))
        admin = cur.fetchone()
        con.close()
        if admin:
            session['admin_id'] = admin[0]
            return redirect('/admin')
        else:
            return "Invalid admin login"
    return render_template('admin_login.html')

# Show all orders
@app.route('/admin/orders')
def admin_orders():
    if 'admin_id' not in session:
        return redirect('/admin/login')

    con = get_db()
    cur = con.cursor()
    cur.execute("""
    SELECT orders.id, users.name AS user_name, users.email, books.name AS book_name, books.author
    FROM orders
    JOIN users ON orders.user_id = users.id
    JOIN books ON orders.book_id = books.id
""")
    orders = cur.fetchall()
    con.close()
    return render_template('orders.html', orders=orders)


# Admin: Add a book
@app.route('/admin/add_book', methods=['POST'])
def add_book():
    if 'admin_id' not in session:
        return redirect('/admin/login')

    image_file = request.files['image_file']
    if image_file and allowed_file(image_file.filename):
        filename = secure_filename(image_file.filename)
        os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        image_file.save(filepath)
        image_url = f"/static/uploads/{filename}"
    else:
        return "Invalid image file"

    name = request.form['name']
    author = request.form['author']
    price = request.form['price']
    description = request.form['description']
    available = request.form.get('available', '1')  # Default to available

    con = get_db()
    cur = con.cursor()
    cur.execute("""
        INSERT INTO books (image, name, author, price, description, available)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (image_url, name, author, price, description, available))
    con.commit()
    con.close()
    return redirect('/admin')


@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        password = request.form['password']
        con = get_db()
        cur = con.cursor()
        try:
            cur.execute("INSERT INTO users (name, email, password) VALUES (?, ?, ?)", (name, email, password))
            con.commit()
            return redirect('/login')
        except sqlite3.IntegrityError:
            return "Email already registered"
        finally:
            con.close()
    return render_template('signup.html')


@app.route("/admin/delete_book/<int:book_id>", methods=["POST"])
def delete_book(book_id):
    con = get_db()
    cur = con.cursor()
    cur.execute("DELETE FROM books WHERE id = ?", (book_id,))
    con.commit()
    con.close()
    return redirect("/admin")

@app.route("/admin/edit_book/<int:book_id>", methods=["GET", "POST"])
def edit_book(book_id):
    con = get_db()
    cur = con.cursor()

    if request.method == "POST":
        name = request.form["name"]
        author = request.form["author"]
        price = request.form["price"]
        description = request.form["description"]
        available = request.form["available"]

        cur.execute("""
            UPDATE books 
            SET name=?, author=?, price=?, description=?, available=?
            WHERE id=?
        """, (name, author, price, description, available, book_id))

        con.commit()
        con.close()
        return redirect("/admin")
    
    else:
        cur.execute("SELECT * FROM books WHERE id=?", (book_id,))
        book = cur.fetchone()
        con.close()

        if book:
            # Convert sqlite Row to dictionary if needed
            book_dict = {
                "id": book[0],
                "image_path": book[1],
                "name": book[2],
                "author": book[3],
                "price": book[4],
                "description": book[5],
                "available": book[6]
            }
            return render_template("edit_book.html", book=book_dict)
        else:
            return "Book not found", 404


if __name__ == '__main__':
    app.run(debug=True)
