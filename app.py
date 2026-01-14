import os
import sqlite3
from flask import Flask, render_template, request, redirect, session, flash
from datetime import datetime

app = Flask(__name__)
app.secret_key = "library_secret"

def connect_db():
    db_path = os.path.join(app.root_path, "library.db")
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    db = connect_db()
    db.executescript("""
    CREATE TABLE IF NOT EXISTS admin (
        admin_id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE,
        password TEXT
    );
    CREATE TABLE IF NOT EXISTS books (
        bookid INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        author TEXT,
        category TEXT
    );
    CREATE TABLE IF NOT EXISTS students (
        studentid INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        department TEXT NOT NULL,
        year INTEGER NOT NULL
    );
    CREATE TABLE IF NOT EXISTS issued_books (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        studentid INTEGER,
        bookid INTEGER,
        issue_date TEXT, 
        due_date TEXT, 
        return_date TEXT, 
        fine REAL DEFAULT 0.0,
        FOREIGN KEY(studentid) REFERENCES students(studentid),
        FOREIGN KEY(bookid) REFERENCES books(bookid)
    );
    """)
    # Check if admin exists, if not create a default one
    admin = db.execute("SELECT * FROM admin").fetchone()
    if not admin:
        db.execute("INSERT INTO admin (username, password) VALUES (?, ?)", ("admin", "admin123"))
    db.commit()
    db.close()

# Initialize DB on startup
init_db()

# ---------- LOGIN ----------
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        db = connect_db()
        admin = db.execute("SELECT * FROM admin WHERE username=? AND password=?", (username, password)).fetchone()
        db.close()

        if admin:
            session["admin"] = username
            return redirect("/")
        else:
            flash("Invalid username or password")
    
    return render_template("login.html")

@app.route("/logout")
def logout():
    session.pop("admin", None)
    return redirect("/login")

def login_required():
    return "admin" in session

# ---------- HOME ----------
@app.route("/")
def index():
    if not login_required():
        return redirect("/login")
    return render_template("index.html")

# ---------- MENUS ----------
@app.route("/books")
def books_menu():
    if not login_required():
        return redirect("/login")
    return render_template("books_menu.html")

@app.route("/students")
def students_menu():
    if not login_required():
        return redirect("/login")
    return render_template("students_menu.html")

@app.route("/issued_books")
def issued_menu():
    if not login_required():
        return redirect("/login")
    return render_template("issued_menu.html")

# ---------- BOOKS CRUD ----------
@app.route("/add_book", methods=["GET","POST"])
def add_book():
    if not login_required():
        return redirect("/login")
    if request.method=="POST":
        name = request.form["name"]
        author = request.form["author"]
        category = request.form["category"]
        db = connect_db()
        db.execute("INSERT INTO books (name, author, category) VALUES (?, ?, ?)", (name, author, category))
        db.commit()
        db.close()
        return redirect("/view_books")
    return render_template("add_book.html")

@app.route("/view_books")
def view_books():
    if not login_required():
        return redirect("/login")
    search = request.args.get("q", "")
    db = connect_db()
    
    query = """
        SELECT b.*, 
               CASE WHEN i.id IS NOT NULL THEN 'Issued' ELSE 'Available' END as status
        FROM books b
        LEFT JOIN issued_books i ON b.bookid = i.bookid AND i.return_date IS NULL
    """
    
    if search:
        query += " WHERE b.name LIKE ? OR b.author LIKE ? OR b.category LIKE ?"
        query += " ORDER BY b.bookid"
        books = db.execute(query, (f"%{search}%", f"%{search}%", f"%{search}%")).fetchall()
    else:
        query += " ORDER BY b.bookid"
        books = db.execute(query).fetchall()
        
    db.close()
    return render_template("view.html", books=books, search_query=search)

@app.route("/update_book/<int:id>", methods=["GET","POST"])
def update_book(id):
    if not login_required():
        return redirect("/login")
    db = connect_db()
    book = db.execute("SELECT * FROM books WHERE bookid=?", (id,)).fetchone()
    if request.method=="POST":
        db.execute("UPDATE books SET name=?, author=?, category=? WHERE bookid=?", (request.form["name"], request.form["author"], request.form["category"], id))
        db.commit()
        db.close()
        return redirect("/view_books")
    db.close()
    return render_template("update_book.html", book=book)

@app.route("/delete_book/<int:id>")
def delete_book(id):
    if not login_required():
        return redirect("/login")
    db = connect_db()
    db.execute("DELETE FROM books WHERE bookid=?", (id,))
    db.commit()
    db.close()
    return redirect("/view_books")

# ---------- STUDENTS CRUD ----------
@app.route("/add_student", methods=["GET","POST"])
def add_student():
    if not login_required():
        return redirect("/login")
    if request.method=="POST":
        name = request.form["name"]
        department = request.form["department"]
        year = request.form["year"]
        db = connect_db()
        db.execute("INSERT INTO students (name, department, year) VALUES (?, ?, ?)", (name, department, year))
        db.commit()
        db.close()
        return redirect("/view_students")
    return render_template("add_student.html")

@app.route("/view_students")
def view_students():
    if not login_required():
        return redirect("/login")
    search = request.args.get("q", "")
    db = connect_db()
    
    if search:
        students = db.execute("SELECT * FROM students WHERE name LIKE ? OR department LIKE ? ORDER BY studentid", (f"%{search}%", f"%{search}%")).fetchall()
    else:
        students = db.execute("SELECT * FROM students ORDER BY studentid").fetchall()
        
    db.close()
    return render_template("view.html", students=students, search_query=search)

@app.route("/update_student/<int:id>", methods=["GET","POST"])
def update_student(id):
    if not login_required():
        return redirect("/login")
    db = connect_db()
    student = db.execute("SELECT * FROM students WHERE studentid=?", (id,)).fetchone()
    if request.method=="POST":
        db.execute("UPDATE students SET name=?, department=?, year=? WHERE studentid=?", (request.form["name"], request.form["department"], request.form["year"], id))
        db.commit()
        db.close()
        return redirect("/view_students")
    db.close()
    return render_template("update_student.html", student=student)

@app.route("/delete_student/<int:id>")
def delete_student(id):
    if not login_required():
        return redirect("/login")
    db = connect_db()
    db.execute("DELETE FROM students WHERE studentid=?", (id,))
    db.commit()
    db.close()
    return redirect("/view_students")

# ---------- ISSUED BOOKS ----------
@app.route("/add_issued", methods=["GET","POST"])
def add_issued():
    if not login_required():
        return redirect("/login")
    db = connect_db()
    students = db.execute("SELECT * FROM students").fetchall()
    books = db.execute("SELECT * FROM books WHERE bookid NOT IN (SELECT bookid FROM issued_books WHERE return_date IS NULL)").fetchall()
    if request.method=="POST":
        student_id = request.form["student_id"]
        book_id = request.form["book_id"]
        issue_date = request.form["issue_date"]
        due_date = request.form["due_date"]
        db.execute("INSERT INTO issued_books (studentid, bookid, issue_date, due_date) VALUES (?, ?, ?, ?)", (student_id, book_id, issue_date, due_date))
        db.commit()
        db.close()
        return redirect("/view_issued")
    db.close()
    return render_template("add_issued.html", students=students, books=books)

@app.route("/view_issued")
def view_issued():
    if not login_required():
        return redirect("/login")
    db = connect_db()
    issued = db.execute("""
        SELECT i.id, i.studentid, i.bookid, s.name as student_name, b.name as book_name, i.issue_date, i.due_date, i.return_date, i.fine
        FROM issued_books i
        JOIN students s ON i.studentid = s.studentid
        JOIN books b ON i.bookid = b.bookid
        ORDER BY i.id
    """).fetchall()
    db.close()
    return render_template("view.html", issued=issued)

@app.route("/delete_issued/<int:id>")
def delete_issued(id):
    if not login_required():
        return redirect("/login")
    db = connect_db()
    db.execute("DELETE FROM issued_books WHERE id=?", (id,))
    db.commit()
    db.close()
    return redirect("/view_issued")

@app.route("/update_issued/<int:id>", methods=["GET","POST"])
def update_issued(id):
    if not login_required():
        return redirect("/login")
    db = connect_db()
    issued = db.execute("SELECT * FROM issued_books WHERE id=?", (id,)).fetchone()
    students = db.execute("SELECT * FROM students").fetchall()
    books = db.execute("""
        SELECT * FROM books 
        WHERE bookid NOT IN (SELECT bookid FROM issued_books WHERE return_date IS NULL)
        OR bookid = ?
    """, (issued["bookid"],)).fetchall()
    if request.method=="POST":
        db.execute("UPDATE issued_books SET studentid=?, bookid=?, issue_date=?, due_date=? WHERE id=?", (request.form["student_id"], request.form["book_id"], request.form["issue_date"], request.form["due_date"], id))
        db.commit()
        db.close()
        return redirect("/view_issued")
    db.close()
    return render_template("update_issued.html", issued=issued, students=students, books=books)

@app.route("/return_book/<int:id>", methods=["GET", "POST"])
def return_book(id):
    if not login_required():
        return redirect("/login")
    db = connect_db()
    issued = db.execute("""
        SELECT i.*, s.name as student_name, b.name as book_name 
        FROM issued_books i 
        JOIN students s ON i.studentid = s.studentid 
        JOIN books b ON i.bookid = b.bookid 
        WHERE i.id=?
    """, (id,)).fetchone()
    
    if request.method == "POST":
        return_date_str = request.form["return_date"]
        due_date_str = issued["due_date"]
        
        # If due_date is missing (for old records), use issue_date
        if not due_date_str:
            due_date_str = issued["issue_date"]
            
        # Calculate fine
        d1 = datetime.strptime(due_date_str, "%Y-%m-%d")
        d2 = datetime.strptime(return_date_str, "%Y-%m-%d")
        
        fine = 0
        if d2 > d1:
            diff = (d2 - d1).days
            fine = diff * 5 # ₹5 per day
            
        db.execute("UPDATE issued_books SET return_date=?, fine=? WHERE id=?", (return_date_str, fine, id))
        db.commit()
        db.close()
        flash(f"Book returned. Fine: ₹{fine}")
        return redirect("/view_issued")
    
    today = datetime.now().strftime("%Y-%m-%d")
    db.close()
    return render_template("return_book.html", issued=issued, today=today)

# ---------- RUN APP ----------
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)