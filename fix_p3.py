import re

with open('app.py', 'r', encoding='utf-8') as f:
    content = f.read()

new_db_code = """
import mysql.connector.pooling

# [PERF-001] Module-level Database Connection Pool
db_host = os.environ.get('DB_HOST', 'localhost')
pool_params = {
    'pool_name': 'face_attendance_pool',
    'pool_size': 10,
    'pool_reset_session': True,
    'host': db_host,
    'port': int(os.environ.get('DB_PORT', 3306)),
    'user': os.environ.get('DB_USER', 'root'),
    'password': os.environ.get('DB_PASS', ''),
    'database': os.environ.get('DB_NAME', 'face_attendance_db')
}

if db_host != 'localhost' and db_host != '127.0.0.1':
    pool_params['ssl_disabled'] = False
    if os.environ.get('DB_SSL_CA'):
        pool_params['ssl_ca'] = os.environ.get('DB_SSL_CA')

try:
    db_pool = mysql.connector.pooling.MySQLConnectionPool(**pool_params)
except Exception as e:
    print(f"[FATAL] Failed to initialize DB Pool: {e}")
    db_pool = None

def get_db_connection():
    if not db_pool:
        return None
    try:
        return db_pool.get_connection()
    except mysql.connector.errors.PoolError as e:
        print(f'[DB POOL ERROR] {e}')
        return None
"""

content = re.sub(r"def get_db_connection\(\):.*?return None\n", new_db_code.strip() + "\n", content, flags=re.DOTALL)

with open('app.py', 'w', encoding='utf-8') as f:
    f.write(content)
print("Phase 3 applied")
