import os, re

with open('app.py', 'r', encoding='utf-8') as f:
    content = f.read()

# PHASE 1
if 'ADMIN_USER env var not set' not in content:
    startup_code = """
app.secret_key = os.environ.get('SECRET_KEY', 'fallback_secret_key_123')

# [SEC-001] Startup safety check
if not os.environ.get('ADMIN_USER'):
    raise RuntimeError('ADMIN_USER env var not set')
"""
    content = re.sub(r"app\.secret_key = [^\n]*", startup_code.strip(), content)

login_route_new = """
@app.route('/login', methods=['GET', 'POST'])
def login():
    if session.get('role') == 'admin':
        return redirect(url_for('index'))
    if request.method == 'POST':
        user, pwd = request.form['username'], request.form['password']
        
        # [SEC-001] Check that ADMIN_USER is populated
        admin_user = os.environ.get('ADMIN_USER')
        if not admin_user:
            return "Server Configuration Error: Admin credentials not set.", 500
            
        if user == admin_user and pwd == os.environ.get('ADMIN_PASS', ''):
            session['logged_in'], session['role'] = True, 'admin'
            return redirect(url_for('index'))
        return render_template('login.html', error="❌ Invalid credentials")
    return render_template('login.html')
"""
content = re.sub(r"@app\.route\('/login', methods=\['GET', 'POST'\]\)\ndef login\(\):.*?(?=\n@app\.route|\n\n#)", login_route_new.strip(), content, flags=re.DOTALL)
content = re.sub(r"@app\.route\('/dashboard_stats'\)\ndef dashboard_stats\(\):", "@app.route('/dashboard_stats')\n@login_required\ndef dashboard_stats():", content)

# PHASE 2
if 'MAX_CONTENT_LENGTH' not in content:
    config_code = """
app.config['MAX_CONTENT_LENGTH'] = 10 * 1024 * 1024
app.config['SESSION_COOKIE_SECURE'] = True
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'

@app.errorhandler(413)
def request_entity_too_large(error):
    return jsonify({'error': 'Payload too large', 'max_size': '10MB'}), 413
"""
    content = re.sub(r"(raise RuntimeError\('ADMIN_USER env var not set'\))", r"\1\n" + config_code, content)

# Fix SQLi in forgot_password
sqli1_fix = """
            ALLOWED_TABLES = {'student': 'students', 'professor': 'professors'}
            if role not in ALLOWED_TABLES:
                flash('Invalid role specified.', 'danger')
                return redirect(url_for('login'))
            table = ALLOWED_TABLES[role]
            cursor.execute("SELECT id FROM " + table + " WHERE email = %s", (email,))
"""
content = re.sub(r"table = 'students' if role == 'student' else 'professors'\s*cursor\.execute\(f\"SELECT id FROM \{table\} WHERE email = %s\", \(email,\)\)", sqli1_fix.strip(), content)

# Fix SQLi in reset_password
sqli2_fix = """
            ALLOWED_TABLES = {'student': 'students', 'professor': 'professors'}
            if role not in ALLOWED_TABLES:
                flash('Invalid role specified.', 'danger')
                return redirect(url_for('login'))
            table = ALLOWED_TABLES[role]
            hashed_pw = generate_password_hash(new_password)
            
            cursor.execute("UPDATE " + table + " SET password = %s WHERE email = %s", (hashed_pw, email))
"""
content = re.sub(r"table = 'students' if role == 'student' else 'professors'\s*hashed_pw = generate_password_hash\(new_password\)\s*cursor\.execute\(f\"UPDATE \{table\} SET password = %s WHERE email = %s\", \(hashed_pw, email\)\)", sqli2_fix.strip(), content)

with open('app.py', 'w', encoding='utf-8') as f:
    f.write(content)
print("Updated successfully")
