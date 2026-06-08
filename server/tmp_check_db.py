import sqlite3, os

db_path = r'C:\Users\Хозяин\.local\share\opencode\opencode.db'
if os.path.exists(db_path):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = cursor.fetchall()
    print('Tables:', tables)
    for t in tables:
        try:
            cursor.execute(f'SELECT * FROM [{t[0]}] LIMIT 5')
            rows = cursor.fetchall()
            print(f'{t[0]}: {rows}')
        except Exception as e:
            print(f'{t[0]}: ERROR {e}')
    conn.close()
else:
    print('DB not found')
