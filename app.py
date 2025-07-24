from flask import Flask, render_template, request, redirect, url_for, send_from_directory
import os
import sqlite3
from datetime import datetime

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'  # مجلد لحفظ الملفات المرفوعة
app.config['DATABASE'] = 'platform.db'  # اسم قاعدة البيانات

# التأكد من وجود مجلد الرفع
if not os.path.exists(app.config['UPLOAD_FOLDER']):
    os.makedirs(app.config['UPLOAD_FOLDER'])

# --- تهيئة قاعدة البيانات ---
def init_db():
    with sqlite3.connect(app.config['DATABASE']) as conn:
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS files (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                filename TEXT NOT NULL,
                filepath TEXT NOT NULL,
                upload_date DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS lessons (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                description TEXT,
                file_id INTEGER,
                FOREIGN KEY (file_id) REFERENCES files (id)
            )
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                description TEXT,
                due_date DATETIME,
                completed BOOLEAN DEFAULT 0
            )
        ''')
        conn.commit()

# استدعاء تهيئة قاعدة البيانات عند بدء التشغيل
with app.app_context():
    init_db()

# --- دوال قاعدة البيانات ---
def get_db_connection():
    conn = sqlite3.connect(app.config['DATABASE'])
    conn.row_factory = sqlite3.Row  # لارجاع النتائج كقاموس
    return conn

# --- مسارات التطبيق ---

@app.route('/')
def index():
    conn = get_db_connection()
    files = conn.execute('SELECT * FROM files').fetchall()
    lessons = conn.execute('SELECT * FROM lessons').fetchall()
    tasks = conn.execute('SELECT * FROM tasks').fetchall()
    conn.close()
    return render_template('index.html', files=files, lessons=lessons, tasks=tasks)

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return "No file part"
    file = request.files['file']
    if file.filename == '':
        return "No selected file"
    if file:
        filename = file.filename
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('INSERT INTO files (filename, filepath) VALUES (?, ?)', (filename, filepath))
        conn.commit()
        conn.close()

        return redirect(url_for('index'))

@app.route('/uploads/<filename>')
def download_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

@app.route('/add_lesson', methods=['POST'])
def add_lesson():
    title = request.form['title']
    description = request.form['description']
    file_id = request.form['file_id']

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('INSERT INTO lessons (title, description, file_id) VALUES (?, ?, ?)', (title, description, file_id))
    conn.commit()
    conn.close()

    return redirect(url_for('index'))

@app.route('/add_task', methods=['POST'])
def add_task():
    title = request.form['title']
    description = request.form['description']
    due_date_str = request.form['due_date']  # استلام التاريخ كسلسلة نصية

    # تحويل السلسلة النصية إلى كائن datetime
    due_date = datetime.strptime(due_date_str, '%Y-%m-%d')

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('INSERT INTO tasks (title, description, due_date) VALUES (?, ?, ?)', (title, description, due_date))
    conn.commit()
    conn.close()

    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)