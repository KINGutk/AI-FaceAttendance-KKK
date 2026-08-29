import re

with open('app.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Replace the email sending block inside the leave approval loop
old_email_block = """                    if leave['email']:
                        try:
                            send_leave_status_notification(
                                leave['email'], leave['name'], action, leave['subject_name'] or 'All Subjects',
                                leave['start_date'], leave['end_date'], leave.get('application_purpose')
                            )
                        except Exception as e:
                            print(f"Email sending error: {e}")"""

new_email_block = """                    if leave['email']:
                        if 'email_data_list' not in locals():
                            email_data_list = []
                        email_data_list.append({
                            'email': leave['email'],
                            'name': leave['name'],
                            'status': action,
                            'subject': leave['subject_name'] or 'All Subjects',
                            'start_date': leave['start_date'],
                            'end_date': leave['end_date'],
                            'purpose': leave.get('application_purpose')
                        })"""

if old_email_block in content:
    content = content.replace(old_email_block, new_email_block)
    print("Patched inner email collection block")
else:
    print("Could not find inner email block")


# Replace the flash message at the end of the POST handler to send the collected emails
old_flash_block = """            db.commit()
            flash(f"{processed_count} leave application(s) {action} successfully!", "success")
        except Exception as e:"""

new_flash_block = """            db.commit()
            
            # Send emails in background
            if 'email_data_list' in locals() and email_data_list:
                send_leave_status_emails_in_background(email_data_list)
                
            flash(f"{processed_count} leave application(s) {action} successfully! Notifications are being sent in the background.", "success")
        except Exception as e:"""

if old_flash_block in content:
    content = content.replace(old_flash_block, new_flash_block)
    print("Patched flash message block")
else:
    print("Could not find flash block")

with open('app.py', 'w', encoding='utf-8') as f:
    f.write(content)
print("Done writing app.py")
