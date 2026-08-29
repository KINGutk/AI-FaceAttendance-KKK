import os, re

with open('app.py', 'r', encoding='utf-8') as f:
    content = f.read()

# ====================================================
# PHASE 7: AI Fixes (AI-001, AI-002, AI-003)
# ====================================================
# AI-002: YOLO loader
yolo_loader = """
def load_yolo_model():
    model_path = os.path.join(os.path.dirname(__file__), 'yolov8n-face.pt')
    if not os.path.exists(model_path):
        try:
            print('[AI] Downloading YOLO model...')
            import urllib.request
            urllib.request.urlretrieve("https://huggingface.co/junjiang/GestureFace/resolve/main/yolov8n-face.pt", model_path)
        except Exception as e:
            print(f'[AI FATAL] Cannot download YOLO model: {e}')
            return None
    try:
        return YOLO(model_path)
    except:
        return None

yolo_model = load_yolo_model()
"""
content = re.sub(r"MODEL_PATH = os\.environ\.get\('YOLO_MODEL_PATH'.*?yolo_model = YOLO\(MODEL_PATH\)", yolo_loader.strip(), content, flags=re.DOTALL)

# AI-003: Size validation in process_frame single mode
size_check = """
            # [AI-003] Reject faces too small for reliable recognition
            if (x2 - x1) < 60 or (y2 - y1) < 60:
                return jsonify({'message': 'Move closer to camera', 'color': 'orange'})
                
            img_crop = img_bgr[y1:y2, x1:x2]
"""
content = re.sub(r"img_crop = img_bgr\[y1:y2, x1:x2\]", size_check.strip(), content, count=1)

# AI-001: ThreadPoolExecutor setup
if 'ai_executor' not in content:
    content = re.sub(r"(import threading)", r"\1\nfrom concurrent.futures import ThreadPoolExecutor\nai_executor = ThreadPoolExecutor(max_workers=4)\n", content)

# ====================================================
# PHASE 9: Final Additions (CQ-001, MF-001)
# ====================================================
audit_log_func = """
def log_audit(action_by, role, action_type, target_table, target_id, old_value, new_value):
    try:
        db = get_db_connection()
        if db:
            cursor = db.cursor()
            cursor.execute('''INSERT INTO audit_logs 
                (action_by, role, action_type, target_table, target_id, old_value, new_value)
                VALUES (%s, %s, %s, %s, %s, %s, %s)''', 
                (action_by, role, action_type, target_table, target_id, str(old_value), str(new_value)))
            db.commit()
    except Exception as e:
        print(f"[AUDIT ERROR] {e}")
"""
if 'def log_audit' not in content:
    content = re.sub(r"(def get_db_connection.*?\n\n)", r"\1" + audit_log_func + "\n", content, flags=re.DOTALL)

with open('app.py', 'w', encoding='utf-8') as f:
    f.write(content)
print("Phases 7 & 9 applied to app.py")

# ====================================================
# PHASE 8: Frontend (FE-001, FE-002)
# ====================================================
with open('templates/live_attendance.html', 'r', encoding='utf-8') as f:
    html = f.read()

fe_fix = """
    // [FE-001] Stop camera on navigation
    window.addEventListener('beforeunload', () => {
      if (stream) stream.getTracks().forEach(track => track.stop());
    });
"""
if 'beforeunload' not in html:
    html = re.sub(r"(const delay = ms => new Promise.*?)\n", r"\1\n" + fe_fix, html)

https_fix = """
    .catch(err => {
      // [FE-002] Handle HTTP vs HTTPS errors silently
      const isHTTP = location.protocol === 'http:';
      const msg = isHTTP
        ? '❌ HTTPS required for camera access. Contact your administrator.'
        : '❌ Camera blocked. Please allow camera access in browser settings.';
      document.getElementById('statusText').innerText = msg;
      console.error(err);
    });
"""
# Replacing the empty catch or basic catch in live_attendance if exists
# Assuming standard navigator.mediaDevices.getUserMedia setup in startCam()
# We will just inject it into the script block
html = re.sub(r"catch\s*\([^\)]*\)\s*\{[^}]*\}", https_fix.strip(), html)

with open('templates/live_attendance.html', 'w', encoding='utf-8') as f:
    f.write(html)
print("Phase 8 applied to live_attendance.html")
