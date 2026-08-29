import os, re

with open('app.py', 'r', encoding='utf-8') as f:
    content = f.read()

# ====================================================
# PHASE 4: Worker Desync (BUG-001)
# ====================================================
if '_cache_last_loaded = 0' not in content:
    cache_vars = """
# [BUG-001] Shared cache variables for workers
import time
_cache_last_loaded = 0
_cached_encodings_mat = []
_cached_names = []
_cached_rolls = []

"""
    # Insert after imports
    content = re.sub(r"(import numpy as np\n)", r"\1" + cache_vars, content)

    # In process_frame, inject cache loading
    cache_loader = """
    global _cache_last_loaded, _cached_encodings_mat, _cached_names, _cached_rolls
    current_time = time.time()
    if current_time - _cache_last_loaded > 60:
        if os.path.exists("face_cache.npz"):
            data = np.load("face_cache.npz", allow_pickle=True)
            _cached_encodings_mat = data['encodings']
            _cached_names = data['names']
            _cached_rolls = data['rolls']
            _cache_last_loaded = current_time

"""
    content = re.sub(r"(@app\.route\('/process_frame', methods=\['POST'\]\)\ndef process_frame\(\):\n\s*db = None\n)", r"\1" + cache_loader, content)
    content = re.sub(r"KNOWN_ENCODINGS_MAT", "_cached_encodings_mat", content)
    content = re.sub(r"KNOWN_NAMES", "_cached_names", content)
    content = re.sub(r"KNOWN_ROLLS", "_cached_rolls", content)

# ====================================================
# PHASE 5: Data Layer (PERF-002, DB-002)
# ====================================================
# PERF-002: Save images to disk instead of DB
def signup_replace(m):
    return """
            # [PERF-002] Save raw base64 to disk, store paths in DB
            os.makedirs('faces', exist_ok=True)
            student_dir = os.path.join('faces', f"{roll_no}_{name.replace(' ', '_')}")
            os.makedirs(student_dir, exist_ok=True)
            
            face_paths = []
            for idx, b64 in enumerate(face_samples):
                file_path = os.path.join(student_dir, f"sample_{idx}.jpg")
                img_data = decode_b64_image(b64)
                if img_data is not None:
                    cv2.imwrite(file_path, img_data)
                    face_paths.append(file_path)
                    
            face_data_json = json.dumps(face_paths)
"""
content = re.sub(r"\s*face_data_json = json\.dumps\(face_samples\)", signup_replace, content)

# DB-002: Soft Deletes
content = re.sub(r"cursor\.execute\(\"DELETE FROM students WHERE id = %s\", \(student_id,\)\)", 
                 r"cursor.execute(\"UPDATE students SET status = 'deleted' WHERE id = %s\", (student_id,))", content)
# Update listing queries to ignore deleted
content = re.sub(r"SELECT \* FROM students(?! WHERE)", r"SELECT * FROM students WHERE status != 'deleted'", content)

# ====================================================
# PHASE 6: Query Optimization (PERF-003)
# ====================================================
# Replace loop with executemany in save_manual_attendance
def bulk_insert_replace(m):
    return """
        # [PERF-003] Bulk insert optimized
        insert_data = []
        update_data = []
        for student_id, status in attendance_data.items():
            cursor.execute("SELECT id FROM attendance WHERE student_id = %s AND class_id = %s AND date = %s", (student_id, class_id, date))
            existing = cursor.fetchone()
            if existing:
                update_data.append((status, class_time, existing['id']))
            else:
                insert_data.append((student_id, class_id, date, class_time, status))
                
        if insert_data:
            cursor.executemany("INSERT IGNORE INTO attendance (student_id, class_id, date, time, status, method) VALUES (%s, %s, %s, %s, %s, 'manual')", insert_data)
        if update_data:
            cursor.executemany("UPDATE attendance SET status = %s, time = %s, method = 'manual' WHERE id = %s", update_data)
"""
content = re.sub(r"\s*for student_id, status in attendance_data\.items\(\):\n.*?cursor\.execute\(\"INSERT INTO attendance.*?manual'\)\", \(student_id, class_id, date, class_time, status\)\)", bulk_insert_replace, content, flags=re.DOTALL)

with open('app.py', 'w', encoding='utf-8') as f:
    f.write(content)
print("Phases 4-6 applied")
