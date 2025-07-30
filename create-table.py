import sqlite3

# Connect to (or create) the database
con = sqlite3.connect('bookstore.db')
cur = con.cursor()

# Create Users table
cur.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        address TEXT,
        email TEXT UNIQUE,
        password TEXT,
        phone TEXT
    )
''')

# Create Books table
cur.execute('''
    CREATE TABLE IF NOT EXISTS books (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        image TEXT,
        name TEXT,
        author TEXT,
        price REAL,
        description TEXT,
        available INTEGER
    )
''')

# Create Orders table
cur.execute('''
    CREATE TABLE IF NOT EXISTS orders (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        book_id INTEGER,
        FOREIGN KEY(user_id) REFERENCES users(id),
        FOREIGN KEY(book_id) REFERENCES books(id)
    )
''')

# Create Admin table
cur.execute('''
    CREATE TABLE IF NOT EXISTS admin (
        username TEXT,
        password TEXT,
        email TEXT
    )
''')

# Commit and close
con.commit()
con.close()

print("All tables created successfully in bookstore.db.")
