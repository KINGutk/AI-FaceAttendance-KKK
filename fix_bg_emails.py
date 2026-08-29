import re

with open('app.py', 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Add send_leave_status_emails_in_background right after send_leave_status_notification block
if "def send_leave_status_emails_in_background" not in content:
    # Find the end of send_leave_status_notification by finding the next function def
    func_pattern = re.compile(r"def send_leave_status_notification.*?(?=def |# =================)", re.DOTALL)
    match = func_pattern.search(content)
    if match:
        insertion_str = """
def send_leave_status_emails_in_background(email_data_list):
    \"\"\"Send leave application status emails in a background thread.\"\"\"
    def email_worker():
        print(f"Background Email Task Started: Sending {len(email_data_list)} leave emails...")
        for i, data in enumerate(email_data_list):
            try:
                # the function already uses app.app_context internally, but just in case
                send_leave_status_notification(
                    data['email'], data['name'], data['status'], data['subject'], 
                    data['start_date'], data['end_date'], data['purpose']
                )
                if i < len(email_data_list) - 1:
                    time.sleep(1)
            except Exception as e:
                print(f"Error in background leave email: {e}")
        print("Background Leave Email Task Completed.")
    
    thread = threading.Thread(target=email_worker)
    thread.daemon = True
    thread.start()

"""
        # Append the new function after send_leave_status_notification
        content = content[:match.end()] + insertion_str + content[match.end():]
        print("Injected send_leave_status_emails_in_background")
    else:
        print("Could not find send_leave_status_notification")


# 2. Update professor_leaves POST logic to use the background emails
old_post_block = """
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
                            print(f"Email sending error: {e}")
                    
                    processed_count += 1
            
            db.commit()
            flash(f"{processed_count} leave application(s) {action} successfully!", "success")
        except Exception as e:
            db.rollback()
            flash(f"Error processing leave: {e}", "error")"""

new_post_block = """
        try:
            processed_count = 0
            email_data_list = []
            
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
                        email_data_list.append({
                            'email': leave['email'],
                            'name': leave['name'],
                            'status': action,
                            'subject': leave['subject_name'] or 'All Subjects',
                            'start_date': leave['start_date'],
                            'end_date': leave['end_date'],
                            'purpose': leave.get('application_purpose')
                        })
                    
                    processed_count += 1
            
            db.commit()
            
            # Send emails in background
            if email_data_list:
                send_leave_status_emails_in_background(email_data_list)
                
            flash(f"{processed_count} leave application(s) {action} successfully! Emails are being sent in background.", "success")
        except Exception as e:
            db.rollback()
            flash(f"Error processing leave: {e}", "error")"""

if old_post_block in content:
    content = content.replace(old_post_block, new_post_block)
    print("Updated professor_leaves to use background emails")
else:
    print("Could not find professor_leaves post block")

with open('app.py', 'w', encoding='utf-8') as f:
    f.write(content)
print("Done writing app.py")
