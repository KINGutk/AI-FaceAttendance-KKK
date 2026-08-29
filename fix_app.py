import re

with open('app.py', 'r', encoding='utf-8') as f:
    content = f.read()

# 1. student_dashboard logic
pattern_sd = re.compile(r"@app\.route\('/student_dashboard'\).*?return render_template\('student_dashboard\.html'.*?\n", re.DOTALL)
new_sd = """@app.route('/student_dashboard')
def student_dashboard():
    if session.get('role') != 'student':
        return redirect(url_for('student_login'))
    db = get_db_connection()
    if not db:
        return "Database connection error", 500
    cursor = db.cursor(dictionary=True)
    
    # Get student semester
    cursor.execute("SELECT semester FROM students WHERE id=%s", (session['user_id'],))
    student_data = cursor.fetchone()
    student_semester = student_data['semester'] if student_data else None

    # Get Attendance Data
    cursor.execute(\"\"\"
        SELECT c.subject_name, COUNT(a.id) as total_classes,
               SUM(CASE WHEN a.status='Present' THEN 1 ELSE 0 END) as presents,
               ROUND(SUM(CASE WHEN a.status='Present' THEN 1 ELSE 0 END) * 100.0 / COUNT(a.id), 1) as percentage
        FROM attendance a JOIN classes c ON a.class_id=c.id
        WHERE a.student_id=%s GROUP BY c.subject_name
    \"\"\", (session['user_id'],))
    attendance_data = cursor.fetchall()

    # Get Leaves with Professor Name
    cursor.execute(\"\"\"
        SELECT l.*, MAX(p.name) as professor_name
        FROM leaves l
        LEFT JOIN classes c ON l.subject_name = c.subject_name AND c.semester = %s
        LEFT JOIN professors p ON c.professor_id = p.id
        WHERE l.student_id = %s
        GROUP BY l.id
        ORDER BY l.created_at DESC
    \"\"\", (student_semester, session['user_id']))
    leaves = cursor.fetchall()

    # Get Donut Chart Stats
    cursor.execute(\"\"\"
        SELECT 
            SUM(CASE WHEN status='Present' THEN 1 ELSE 0 END) as total_present,
            SUM(CASE WHEN status='Absent' THEN 1 ELSE 0 END) as total_absent,
            SUM(CASE WHEN status='Leave' THEN 1 ELSE 0 END) as total_leave
        FROM attendance 
        WHERE student_id=%s
    \"\"\", (session['user_id'],))
    overall_stats = cursor.fetchone()
    if not overall_stats['total_present'] and not overall_stats['total_absent'] and not overall_stats['total_leave']: 
        overall_stats = {'total_present': 0, 'total_absent': 0, 'total_leave': 0}

    # Get Timetable
    timetable = []
    if student_semester:
        cursor.execute(\"\"\"
            SELECT c.subject_name, c.day_of_week, c.start_time, c.end_time, p.name as professor_name
            FROM classes c
            LEFT JOIN professors p ON c.professor_id = p.id
            WHERE c.semester = %s
            ORDER BY FIELD(c.day_of_week, 'Monday','Tuesday','Wednesday','Thursday','Friday','Saturday','Sunday'), c.start_time
        \"\"\", (student_semester,))
        
        from datetime import datetime
        raw_timetable = cursor.fetchall()
        for t in raw_timetable:
            if hasattr(t['start_time'], 'seconds'):
                t['start_time'] = (datetime.min + t['start_time']).time().strftime("%I:%M %p")
            if hasattr(t['end_time'], 'seconds'):
                t['end_time'] = (datetime.min + t['end_time']).time().strftime("%I:%M %p")
            timetable.append(t)

    cursor.close()
    db.close()

    return render_template('student_dashboard.html', attendance_data=attendance_data, leaves=leaves, student_name=session['name'], overall_stats=overall_stats, timetable=timetable)\n"""

if pattern_sd.search(content):
    content = pattern_sd.sub(new_sd, content, count=1)
    print("Patched student_dashboard")

# 2. apply_leave
old_apply_leave = """            if subject_name:
                cursor.execute(
                    "INSERT INTO leaves (student_id, subject_name, application_purpose, application_text, start_date, end_date, status) VALUES (%s, %s, %s, %s, %s, %s, 'Pending')",
                    (logged_in_student_id, subject_name, application_purpose, application_text, start_date, end_date)
                )
            else:
                cursor.execute(
                    "INSERT INTO leaves (student_id, subject_name, application_purpose, application_text, start_date, end_date, status) VALUES (%s, %s, %s, %s, %s, %s, 'Pending')",
                    (logged_in_student_id, None, application_purpose, application_text, start_date, end_date)
                )"""

new_apply_leave = """            if subject_name:
                cursor.execute(
                    "INSERT INTO leaves (student_id, subject_name, application_purpose, application_text, start_date, end_date, status) VALUES (%s, %s, %s, %s, %s, %s, 'Pending')",
                    (logged_in_student_id, subject_name, application_purpose, application_text, start_date, end_date)
                )
            else:
                cursor.execute("SELECT DISTINCT subject_name FROM classes WHERE semester = %s", (student['semester'],))
                student_subjects = cursor.fetchall()
                if student_subjects:
                    for sub in student_subjects:
                        cursor.execute(
                            "INSERT INTO leaves (student_id, subject_name, application_purpose, application_text, start_date, end_date, status) VALUES (%s, %s, %s, %s, %s, %s, 'Pending')",
                            (logged_in_student_id, sub['subject_name'], application_purpose, application_text, start_date, end_date)
                        )
                else:
                    cursor.execute(
                        "INSERT INTO leaves (student_id, subject_name, application_purpose, application_text, start_date, end_date, status) VALUES (%s, %s, %s, %s, %s, %s, 'Pending')",
                        (logged_in_student_id, None, application_purpose, application_text, start_date, end_date)
                    )"""

content = content.replace(old_apply_leave, new_apply_leave)
print("Patched apply_leave")

# 3. professor_leaves
pattern_pl = re.compile(r"@app\.route\('/professor_leaves', methods=\['GET', 'POST'\]\).*?return render_template\('professor_leaves\.html'.*?\n", re.DOTALL)

new_pl = """@app.route('/professor_leaves', methods=['GET', 'POST'])
@professor_required
def professor_leaves():
    professor_id = session['user_id']
    db = get_db_connection()
    if not db:
        return "Database connection error", 500
    cursor = db.cursor(dictionary=True)

    if request.method == 'POST':
        leave_ids = request.form.getlist('leave_ids')
        action = request.form.get('action')

        if not leave_ids:
            flash("No leaves selected to process.", "warning")
            return redirect(url_for('professor_leaves'))

        try:
            processed_count = 0
            for l_id in leave_ids:
                cursor.execute(\"\"\"
                    SELECT l.*, s.name, s.email, s.semester
                    FROM leaves l
                    JOIN students s ON l.student_id = s.id
                    WHERE l.id = %s
                \"\"\", (l_id,))
                leave = cursor.fetchone()

                if leave:
                    cursor.execute("UPDATE leaves SET status = %s WHERE id = %s", (action, l_id))

                    if action == 'Approved':
                        student_id = leave['student_id']
                        subject_name = leave['subject_name']
                        semester = leave['semester']
                        start_date = leave['start_date']
                        end_date = leave['end_date']

                        if isinstance(start_date, str):
                            start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
                        if isinstance(end_date, str):
                            end_date = datetime.strptime(end_date, '%Y-%m-%d').date()

                        current_date = start_date
                        while current_date <= end_date:
                            day_name = current_date.strftime('%A')
                            if subject_name:
                                cursor.execute("SELECT id FROM classes WHERE subject_name = %s AND semester = %s AND day_of_week = %s", (subject_name, semester, day_name))
                            else:
                                cursor.execute("SELECT id FROM classes WHERE semester = %s AND day_of_week = %s", (semester, day_name))

                            target_classes = cursor.fetchall()

                            for cls in target_classes:
                                class_id = cls['id']
                                cursor.execute("DELETE FROM attendance WHERE student_id = %s AND class_id = %s AND date = %s", (student_id, class_id, current_date))
                                cursor.execute(\"\"\"
                                    INSERT INTO attendance (student_id, class_id, date, time, status, method)
                                    VALUES (%s, %s, %s, NOW(), 'Leave', 'system')
                                \"\"\", (student_id, class_id, current_date))

                            current_date += timedelta(days=1)

                    if leave['email']:
                        try:
                            send_leave_status_notification(
                                leave['email'], leave['name'], action, leave['subject_name'] or 'All Subjects',
                                leave['start_date'], leave['end_date'], leave.get('application_purpose')
                            )
                        except Exception as e:
                            print(f"Email error: {e}")
                    
                    processed_count += 1
            
            db.commit()
            flash(f"{processed_count} leave application(s) {action} successfully!", "success")
        except Exception as e:
            db.rollback()
            flash(f"Error processing leave: {e}", "error")

        return redirect(url_for('professor_leaves'))

    # GET request
    cursor.execute(\"\"\"
        SELECT DISTINCT l.*, s.name, s.roll_no, s.semester
        FROM leaves l
        JOIN students s ON l.student_id = s.id
        WHERE l.status = 'Pending'
        AND (
            l.subject_name IN (
                SELECT subject_name FROM classes WHERE professor_id = %s
            )
            OR (
                (l.subject_name IS NULL OR l.subject_name = '')
                AND s.semester IN (
                    SELECT semester FROM classes WHERE professor_id = %s
                )
            )
        )
        ORDER BY l.start_date DESC
    \"\"\", (professor_id, professor_id))

    raw_pending = cursor.fetchall()
    
    grouped_pending = {}
    for l in raw_pending:
        key = f"{l['student_id']}_{l['start_date']}_{l['end_date']}_{str(l['application_purpose'])[:20]}"
        if key not in grouped_pending:
            grouped_pending[key] = {
                'name': l['name'],
                'roll_no': l['roll_no'],
                'semester': l['semester'],
                'start_date': l['start_date'],
                'end_date': l['end_date'],
                'application_purpose': l['application_purpose'],
                'application_text': l['application_text'],
                'leaves': []
            }
        grouped_pending[key]['leaves'].append(l)
    
    grouped_pending_list = list(grouped_pending.values())

    cursor.execute(\"\"\"
        SELECT DISTINCT l.*, s.name, s.roll_no, s.semester
        FROM leaves l
        JOIN students s ON l.student_id = s.id
        WHERE l.status != 'Pending'
        AND (
            l.subject_name IN (
                SELECT subject_name FROM classes WHERE professor_id = %s
            )
            OR (
                (l.subject_name IS NULL OR l.subject_name = '')
                AND s.semester IN (
                    SELECT semester FROM classes WHERE professor_id = %s
                )
            )
        )
        ORDER BY l.start_date DESC
    \"\"\", (professor_id, professor_id))

    historical_leaves = cursor.fetchall()

    cursor.close()
    db.close()

    return render_template('professor_leaves.html', grouped_pending_list=grouped_pending_list, historical_leaves=historical_leaves)\n"""

if pattern_pl.search(content):
    content = pattern_pl.sub(new_pl, content, count=1)
    print("Patched professor_leaves")

with open('app.py', 'w', encoding='utf-8') as f:
    f.write(content)
