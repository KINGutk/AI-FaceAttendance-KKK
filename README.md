# Face Attendance System

AI-powered attendance management system using **YOLOv8** face detection and **ArcFace** (512D) face recognition. Built for Khushal Degree College.

## Features

- **AI Face Recognition** — Real-time attendance via webcam using YOLOv8 + ArcFace ONNX
- **3-Angle Registration** — Students register with front, left, and right face photos
- **Auto-Absent Marking** — Background scheduler marks absentees after class ends
- **Email Notifications** — Automatic emails for attendance and leave updates
- **Role-Based Access** — Admin, Professor, and Student dashboards
- **Leave Management** — Students apply for leave; professors approve/reject
- **PWA Support** — Installable on mobile devices

## Tech Stack

| Component | Technology |
|---|---|
| Backend | Flask (Python) |
| Database | MySQL 8.0 (AWS RDS compatible) |
| Face Detection | YOLOv8 (Ultralytics) |
| Face Recognition | ArcFace w600k_r50 (ONNX Runtime) |
| WSGI Server | Gunicorn |
| Deployment | Docker / AWS |

## Quick Start

### 1. Clone & Setup

```bash
git clone https://github.com/YOUR_USERNAME/face-attendance-system.git
cd face-attendance-system
```

### 2. Environment Variables

```bash
cp .env.example .env
# Edit .env with your database credentials, email config, etc.
```

### 3. Database Setup

```bash
# Import schema into your MySQL instance
mysql -u root -p < schema.sql
```

### 4. Run Locally

```bash
pip install -r requirements.txt
python app.py
```

### 5. Run with Docker

```bash
docker-compose up --build
```

The app will be available at `http://localhost:5000`

## AWS Deployment

### Using Docker on EC2 / ECS

1. Build and push the Docker image:
   ```bash
   docker build -t face-attendance .
   ```

2. Set up **AWS RDS (MySQL 8.0)** and import `schema.sql`

3. Configure environment variables (`.env` or AWS Secrets Manager)

4. Deploy to ECS/Fargate or EC2 with Docker

### Using Elastic Beanstalk

1. Create a new Elastic Beanstalk environment (Docker platform)
2. Upload the project as a zip or connect your GitHub repo
3. Set environment variables in the EB console

## Project Structure

```
├── app.py                  # Main Flask application (all routes & AI logic)
├── requirements.txt        # Python dependencies
├── schema.sql              # Clean MySQL schema (no test data)
├── Dockerfile              # Production Docker image
├── docker-compose.yml      # Local development with MySQL
├── .env.example            # Environment variable template
├── .gitignore              # Git exclusions
├── .dockerignore           # Docker build exclusions
├── static/
│   ├── css/dashboard.css   # Dashboard styles
│   ├── icons/              # PWA icons
│   ├── manifest.json       # PWA manifest
│   └── service-worker.js   # Service worker
└── templates/              # Jinja2 HTML templates (23 files)
```

## Environment Variables

See [`.env.example`](.env.example) for the full list of required variables.

## License

Private — Khushal Degree College
