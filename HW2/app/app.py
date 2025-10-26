import os
import time
from flask import Flask, request, redirect, url_for
import psycopg2
from psycopg2.extras import RealDictCursor

app = Flask(__name__)

def get_db_connection():
    retries = 5
    while retries > 0:
        try:
            conn = psycopg2.connect(
                host=os.environ.get('DB_HOST'),
                database=os.environ.get('DB_NAME'),
                user=os.environ.get('DB_USER'),
                password=os.environ.get('DB_PASSWORD')
            )
            return conn
        except psycopg2.OperationalError:
            retries -= 1
            print("База данных недоступна, пробую снова...")
            time.sleep(5)
    raise Exception("Не удалось подключиться к базе данных")

def init_db():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS tasks (
            id SERIAL PRIMARY KEY,
            title TEXT NOT NULL,
            is_done BOOLEAN DEFAULT FALSE,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
        );
    """)
    cur.execute("SELECT COUNT(*) FROM tasks;")
    if cur.fetchone()[0] == 0:
        cur.execute("INSERT INTO tasks (title) VALUES (%s), (%s);",
                    ("Настроить Docker Compose", "Проверить сохранение данных"))
    
    conn.commit()
    cur.close()
    conn.close()

@app.route('/')
def index():
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    cur.execute('SELECT * FROM tasks ORDER BY created_at;')
    tasks = cur.fetchall()
    cur.close()
    conn.close()

    html = """
    <html>
        <head><title>To-Do List</title></head>
        <body>
            <h1>Список задач</h1>
            <form action="/add" method="post">
                <input type="text" name="title" required>
                <button type="submit">Добавить задачу</button>
            </form>
            <ul style="list-style: none; padding: 0;">
    """
    for task in tasks:
        text_style = "text-decoration: line-through;" if task['is_done'] else ""
        html += f"""
            <li style="margin: 10px 0; display: flex; align-items: center;">
                <form action="/toggle/{task['id']}" method="post" style="margin-right: 10px;">
                    <input type="checkbox" {'checked' if task['is_done'] else ''} onchange="this.form.submit()">
                </form>
                <span style="{text_style}">{task['title']}</span>
                <form action="/delete/{task['id']}" method="post" style="margin-left: auto;">
                    <button type="submit" style="color: red; border: none; background: none; cursor: pointer;">&times;</button>
                </form>
            </li>
        """
    html += "</ul></body></html>"
    return html

@app.route('/add', methods=['POST'])
def add_task():
    task_title = request.form['title']
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("INSERT INTO tasks (title) VALUES (%s);", (task_title,))
    conn.commit()
    cur.close()
    conn.close()
    return redirect(url_for('index'))

@app.route('/toggle/<int:task_id>', methods=['POST'])
def toggle_task(task_id):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("UPDATE tasks SET is_done = NOT is_done WHERE id = %s;", (task_id,))
    conn.commit()
    cur.close()
    conn.close()
    return redirect(url_for('index'))

@app.route('/delete/<int:task_id>', methods=['POST'])
def delete_task(task_id):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM tasks WHERE id = %s;", (task_id,))
    conn.commit()
    cur.close()
    conn.close()
    return redirect(url_for('index'))

if __name__ == '__main__':
    init_db()
    app.run(host='0.0.0.0', port=5000)