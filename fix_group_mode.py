import re

with open('app.py', 'r', encoding='utf-8') as f:
    content = f.read()

group_mode_route = """

@app.route('/process_frame_group', methods=['POST'])
def process_frame_group():
    db = None
    cursor = None
    try:
        if KNOWN_ENCODINGS_MAT is None:
            load_known_faces()

        data = request.json
        image_data = data.get('image')
        if not image_data:
            return jsonify({"message": "No Image", "results": [], "class_info": "--", "faces_detected": 0})

        img = decode_b64_image(image_data)
        if img is None:
            return jsonify({"message": "Decode error", "results": [], "class_info": "--", "faces_detected": 0})

        db = get_db_connection()
        if not db:
            return jsonify({"message": "DB connection error", "results": [], "class_info": "--", "faces_detected": 0})
        cursor = db.cursor(dictionary=True)
        
        now = get_pkt_now()
        date_today = now.date()
        time_now = now.strftime("%H:%M:%S")
        day_name = now.strftime("%A")
        
        prof_filter = ""
        params = [day_name, time_now, time_now]
        if session.get('role') == 'professor':
            prof_filter = " AND professor_id=%s"
            params.append(session.get('user_id'))
            
        cursor.execute(
            f"SELECT * FROM classes WHERE day_of_week=%s AND start_time<=%s AND end_time>=%s{prof_filter} LIMIT 1",
            tuple(params)
        )
        current_class = cursor.fetchone()
        class_info = f"{current_class['subject_name']} ({current_class['semester']})" if current_class else "No Active Class"

        if KNOWN_ENCODINGS_MAT is None or len(KNOWN_ENCODINGS_MAT) == 0:
            return jsonify({"message": "DB Empty", "results": [], "class_info": class_info, "faces_detected": 0})

        small = cv2.resize(img, (0, 0), fx=0.5, fy=0.5)
        yolo_res = yolo_model(small, verbose=False)
        faces = [box for r in yolo_res for box in r.boxes if box.conf[0] >= 0.5]

        if not faces:
            return jsonify({"message": "No face detected", "results": [], "class_info": class_info, "faces_detected": 0})

        results = []
        email_data_list = []
        
        for box in faces:
            x1, y1, x2, y2 = [v * 2 for v in map(int, box.xyxy[0])]
            
            # Minimum face size filter to prevent false positives in group mode
            if (x2 - x1) < 60 or (y2 - y1) < 60:
                continue

            face_crop = img[y1:y2, x1:x2]
            if face_crop.size == 0:
                continue

            query_emb = get_face_embedding(face_crop)
            sims = np.dot(KNOWN_ENCODINGS_MAT, query_emb)
            best_idx = int(np.argmax(sims))
            best_sim = float(sims[best_idx])

            GROUP_THRESHOLD = 0.50  # Stricter for group mode
            
            if best_sim < GROUP_THRESHOLD:
                results.append({"status": "unknown"})
                continue
                
            student_id = KNOWN_STUDENT_IDS[best_idx]
            
            cursor.execute("SELECT * FROM students WHERE id=%s", (student_id,))
            student = cursor.fetchone()
            if not student:
                continue

            if not current_class:
                results.append({
                    "status": "wrong_class",
                    "name": student['name'],
                    "roll": student['roll_no']
                })
                continue
                
            if student['semester'] != current_class['semester']:
                results.append({
                    "status": "wrong_class",
                    "name": student['name'],
                    "roll": student['roll_no']
                })
                continue

            cursor.execute(
                "SELECT * FROM attendance WHERE student_id=%s AND class_id=%s AND date=%s",
                (student['id'], current_class['id'], date_today)
            )
            existing = cursor.fetchone()

            if existing:
                if existing['status'] == 'Present':
                    results.append({
                        "status": "already",
                        "name": student['name'],
                        "roll": student['roll_no']
                    })
                continue

            # Mark Attendance
            cursor.execute(
                "INSERT INTO attendance (student_id, class_id, date, time, status, method) VALUES (%s, %s, %s, %s, 'Present', 'system')",
                (student['id'], current_class['id'], date_today, time_now)
            )
            db.commit()
            
            results.append({
                "status": "marked",
                "name": student['name'],
                "roll": student['roll_no']
            })
            
            update_detection(student['name'], student['roll_no'], class_info, "present", f"✔ {student['name']} marked Present in Group Mode")

            if student['email']:
                email_data_list.append({
                    'student_email': student['email'],
                    'student_name': student['name'],
                    'status': 'Present',
                    'subject': current_class['subject_name'],
                    'date': date_today.strftime('%Y-%m-%d'),
                    'time': time_now
                })

        if email_data_list:
            send_attendance_emails_in_background(email_data_list)

        return jsonify({
            "results": results, 
            "class_info": class_info,
            "faces_detected": len(faces)
        })

    except Exception as e:
        print(f"Group Mode Error: {e}")
        return jsonify({"message": str(e), "results": [], "class_info": "--", "faces_detected": 0})
    finally:
        if cursor: cursor.close()
        if db: db.close()

"""

if "def process_frame_group" not in content:
    # Insert right before def active_class() or process_frame
    pattern = re.compile(r"def process_frame\(\):.*?(?=\n@app\.route)", re.DOTALL)
    match = pattern.search(content)
    if match:
        content = content[:match.end()] + group_mode_route + content[match.end():]
        with open('app.py', 'w', encoding='utf-8') as f:
            f.write(content)
        print("Successfully added process_frame_group endpoint!")
    else:
        print("Could not find process_frame to insert after.")
else:
    print("process_frame_group already exists.")
