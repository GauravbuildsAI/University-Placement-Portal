from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()

# ================= USER =================
class User(db.Model):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    student = db.relationship("Student", backref="user", uselist=False, cascade="all, delete")
    company = db.relationship("Company", backref="user", uselist=False, cascade="all, delete")

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

# ================= STUDENT =================
class Student(db.Model):
    __tablename__ = "students"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), unique=True, nullable=False)
    full_name = db.Column(db.String(100), nullable=False)
    roll_no = db.Column(db.String(50), unique=True, nullable=False)
    course = db.Column(db.String(100), nullable=False)
    branch = db.Column(db.String(100), nullable=False)
    cgpa = db.Column(db.Float, nullable=False)
    phone = db.Column(db.String(20), nullable=False)
    placement_status = db.Column(db.String(50), default="Not Placed")
    status = db.Column(db.String(20), default="active")
    
    # ⭐ NAYA COLUMN RESUME UPLOAD KE LIYE
    resume_file = db.Column(db.String(255), nullable=True)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)

# ================= COMPANY =================
class Company(db.Model):
    __tablename__ = "companies"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), unique=True, nullable=False)
    company_name = db.Column(db.String(120), nullable=False)
    hr_name = db.Column(db.String(100), nullable=False)
    hr_email = db.Column(db.String(120), nullable=False)
    hr_contact = db.Column(db.String(20), nullable=False)
    website = db.Column(db.String(200))
    description = db.Column(db.Text)
    approval_status = db.Column(db.String(20), default="pending")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

# ================= PLACEMENT DRIVE =================
class PlacementDrive(db.Model):
    __tablename__ = "placement_drives"
    id = db.Column(db.Integer, primary_key=True)
    company_id = db.Column(db.Integer, db.ForeignKey("companies.id"), nullable=False)
    job_title = db.Column(db.String(120), nullable=False)
    job_description = db.Column(db.Text, nullable=False)
    eligibility_criteria = db.Column(db.Text, nullable=False)
    application_deadline = db.Column(db.String(30), nullable=False)
    status = db.Column(db.String(20), default="pending")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    company = db.relationship("Company", backref="drives")

# ================= APPLICATION =================
class Application(db.Model):
    __tablename__ = "applications"
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey("students.id"), nullable=False)
    drive_id = db.Column(db.Integer, db.ForeignKey("placement_drives.id"), nullable=False)
    status = db.Column(db.String(20), default="Applied")
    applied_at = db.Column(db.DateTime, default=datetime.utcnow)

    student = db.relationship("Student", backref="applications")
    drive = db.relationship("PlacementDrive", backref="applications")

    __table_args__ = (
        db.UniqueConstraint("student_id", "drive_id", name="unique_student_drive"),
    )