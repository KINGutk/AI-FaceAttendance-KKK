import re

with open('app.py', 'r', encoding='utf-8') as f:
    content = f.read()

pattern = re.compile(
r"(\s+if leave\['email'\]:\s+try:\s+send_leave_status_notification.*?)processed_count \+= 1", 
re.DOTALL
)

replacement = """                    if leave['email']:
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
                        })
                    
                    processed_count += 1"""

if pattern.search(content):
    content = pattern.sub(replacement, content, count=1)
    print("Patched inner email block using regex.")
else:
    print("Regex could not find the inner email block.")

with open('app.py', 'w', encoding='utf-8') as f:
    f.write(content)
