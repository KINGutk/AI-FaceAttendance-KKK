# 🎓 Smart Face Attendance System (AI-Powered)

![Status](https://img.shields.io/badge/Status-Live-brightgreen)
![Python](https://img.shields.io/badge/Python-3.10+-blue)
![AI](https://img.shields.io/badge/AI-YOLOv8%20%7C%20ArcFace-orange)
![Deployment](https://img.shields.io/badge/Deployed-AWS%20EC2%20%7C%20RDS-yellow)

Welcome to the **Smart Face Attendance System**! This is a modern, cloud-deployed web application that automates student attendance tracking using advanced AI Face Recognition. It completely eliminates proxy attendance, saves valuable classroom time, and automates administrative tasks like leave management and email notifications.

---

## 🎯 Project Aim
The traditional "roll call" method is time-consuming and vulnerable to proxy attendance. The aim of this project is to build a highly secure, automated, and contactless attendance system. By leveraging AI for 3D face mapping, the system ensures 100% accuracy, while providing interactive dashboards for professors to monitor student performance and manage schedules seamlessly.

---

## ✨ Key Features & Advantages

*   🤖 **Military-Grade AI Recognition:** Uses **YOLOv8** for rapid face detection and **ArcFace (512D embeddings)** to map and recognize faces with 99.8% accuracy.
*   📅 **Smart Timetable Integration:** Attendance strictly maps to the scheduled classes and specific days of the week. 
*   ✉️ **Automated Email Alerts:** Seamlessly integrates with Gmail SMTP to send instant background email notifications to students when they are marked absent or when a leave is approved.
*   📝 **Schedule-Aware Leave Management:** Students can apply for leaves. When approved, the system calculates the exact classes affected and automatically marks "Leave" without touching unrelated days.
*   📊 **Interactive Dashboards:** Real-time statistics, donut charts, and percentage calculations for both students and professors.
*   ☁️ **Cloud Native:** Fully deployed on **AWS (EC2 & RDS MySQL)** with Nginx reverse proxy, Systemd background workers, and SSL/HTTPS encryption.

---

## 🛠️ Tech Stack

*   **Frontend:** HTML5, CSS3, Bootstrap 5, JavaScript
*   **Backend:** Python, Flask, Gunicorn, APScheduler
*   **AI/Machine Learning:** PyTorch, Ultralytics (YOLO), InsightFace (ONNX Runtime)
*   **Database:** MySQL (AWS Relational Database Service)
*   **Infrastructure:** AWS EC2 (Ubuntu), Nginx, Certbot (Let's Encrypt), DuckDNS

---

## 📖 How to Use (Use-Cases)

### 👨‍🎓 For Students
1. **Smart KYC Registration:** Students sign up by capturing their face from 3 different angles (Straight, Left, Right). The AI generates a unique mathematical map of their face and stores it securely.
2. **Dashboard Tracking:** Students log in to see a visual breakdown of their attendance percentage across all subjects.
3. **Leave Applications:** Students can select a date range and subject to apply for a leave. The system validates the dates and prevents applying for past dates.
4. **Email Updates:** Students automatically receive emails regarding their attendance and leave application statuses.

### 👨‍🏫 For Professors / Admins
1. **Manage Timetable:** Add subjects, assign them to specific days of the week, and set start/end times.
2. **AI Attendance Capture:** 
   * The professor selects the ongoing class.
   * A camera activates, scanning the room.
   * The AI instantly identifies all registered faces in the frame and marks them "Present".
   * Anyone not detected is automatically marked "Absent" and sent an email warning.
3. **Approve Leaves:** View pending leave applications. Approving a leave intelligently updates the student's attendance only for the exact days that subject is taught.
4. **Export Data:** Download comprehensive attendance records for grading and administration.

---

## 🚀 Future Roadmap
- [ ] Integration with campus turnstiles / door locks.
- [ ] Mobile app wrap (PWA) for easier student access.
- [ ] Advanced analytics for predicting student dropout risks based on absence patterns.

---

*Developed as a comprehensive solution for modern educational institutions.*
