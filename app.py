from flask import Flask, render_template, request, redirect, session, Response
import sqlite3
import csv

app = Flask(__name__)
app.secret_key = 'secret123'

# Database connection
def get_db():
    conn = sqlite3.connect('database.db')
    return conn

# Home
@app.route('/')
def home():
    return redirect('/login')

# Register
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        password = request.form['password']

        conn = get_db()
        conn.execute("INSERT INTO users (name, email, password) VALUES (?, ?, ?)",
                     (name, email, password))
        conn.commit()

        return redirect('/login')

    return render_template('register.html')

# Login
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        # ADMIN LOGIN
        if email == "admin@gmail.com" and password == "admin123":
            session.clear()
            session['admin'] = True
            return redirect('/admin')

        # USER LOGIN
        conn = get_db()
        user = conn.execute("SELECT * FROM users WHERE email=? AND password=?",
                            (email, password)).fetchone()

        if user:
            session.clear()
            session['user'] = user[0]
            return redirect('/dashboard')

    return render_template('login.html')

# Dashboard
@app.route('/dashboard')
def dashboard():
    if 'user' not in session:
        return redirect('/login')

    user_id = session['user']
    conn = get_db()

    total = conn.execute("SELECT COUNT(*) FROM complaints WHERE user_id=?", (user_id,)).fetchone()[0]
    pending = conn.execute("SELECT COUNT(*) FROM complaints WHERE status='Pending' AND user_id=?", (user_id,)).fetchone()[0]
    resolved = conn.execute("SELECT COUNT(*) FROM complaints WHERE status='Resolved' AND user_id=?", (user_id,)).fetchone()[0]
    inprogress = conn.execute("SELECT COUNT(*) FROM complaints WHERE status='In Progress' AND user_id=?", (user_id,)).fetchone()[0]

    return render_template('dashboard.html',
                           total=total,
                           pending=pending,
                           resolved=resolved,
                           inprogress=inprogress)

# Add Complaint
@app.route('/complaint', methods=['GET', 'POST'])
def complaint():
    if 'user' not in session:
        return redirect('/login')

    if request.method == 'POST':
        text = request.form['text']
        user_id = session['user']

        conn = get_db()
        conn.execute("INSERT INTO complaints (user_id, text, status) VALUES (?, ?, ?)",
                     (user_id, text, 'Pending'))
        conn.commit()

        return redirect('/dashboard')

    return render_template('complaint.html')

# View Complaints
@app.route('/my_complaints')
def my_complaints():
    if 'user' not in session:
        return redirect('/login')

    user_id = session['user']
    conn = get_db()

    search = request.args.get('search', '')
    status = request.args.get('status', '')

    query = "SELECT * FROM complaints WHERE user_id=?"
    params = [user_id]

    if search:
        query += " AND text LIKE ?"
        params.append(f"%{search}%")

    if status:
        query += " AND status=?"
        params.append(status)

    data = conn.execute(query, params).fetchall()

    return render_template('my_complaints.html', complaints=data)

# Admin Panel
@app.route('/admin')
def admin():
    if 'admin' not in session:
        return redirect('/login')

    conn = get_db()
    data = conn.execute("""
    SELECT complaints.id, users.name, users.email, complaints.text, complaints.status
    FROM complaints
    JOIN users ON complaints.user_id = users.id
    """).fetchall()
    return render_template('admin.html', complaints=data)

# Update Status
@app.route('/update_status/<int:id>/<status>')
def update_status(id, status):
    if 'admin' not in session:
        return redirect('/login')

    conn = get_db()
    conn.execute("UPDATE complaints SET status=? WHERE id=?", (status, id))
    conn.commit()
    return redirect('/admin')

# Delete
@app.route('/delete/<int:id>')
def delete(id):
    if 'user' not in session:
        return redirect('/login')

    conn = get_db()
    conn.execute("DELETE FROM complaints WHERE id=?", (id,))
    conn.commit()
    return redirect('/my_complaints')

# Edit
@app.route('/edit/<int:id>', methods=['GET', 'POST'])
def edit(id):
    if 'user' not in session:
        return redirect('/login')

    conn = get_db()

    if request.method == 'POST':
        text = request.form['text']
        conn.execute("UPDATE complaints SET text=? WHERE id=?", (text, id))
        conn.commit()
        return redirect('/my_complaints')

    data = conn.execute("SELECT * FROM complaints WHERE id=?", (id,)).fetchone()
    return render_template('edit.html', complaint=data)

# Download
@app.route('/download')
def download():
    if 'user' not in session:
        return redirect('/login')

    user_id = session['user']
    conn = get_db()

    data = conn.execute("SELECT * FROM complaints WHERE user_id=?", (user_id,)).fetchall()

    def generate():
        yield "ID,Complaint,Status\n"
        for row in data:
            yield f"{row[0]},{row[2]},{row[3]}\n"

    return Response(generate(),
                    mimetype='text/csv',
                    headers={"Content-Disposition": "attachment;filename=complaints.csv"})

# Logout
@app.route('/logout')
def logout():
    session.clear()
    return redirect('/login')

# Run
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False) 