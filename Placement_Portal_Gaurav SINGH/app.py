import os
from werkzeug.utils import secure_filename
from flask import Flask, render_template, request, redirect, url_for, flash
from config import Config
from models import db, User, Student, Company, PlacementDrive, Application

app = Flask(__name__)
app.config.from_object(Config)

# ================= UPLOAD FOLDER SETUP =================
UPLOAD_FOLDER = 'static/resumes'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

db.init_app(app)

# ================= HOME =================
@app.route("/")
def home():
    return render_template("index.html")

# ================= LOGIN =================
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")

        user = User.query.filter_by(email=email).first()

        if not user or not user.check_password(password):
            flash("Invalid email or password")
            return redirect(url_for("login"))

        # --- ADMIN LOGIN ---
        if user.role == "admin":
            total_students = Student.query.count()
            total_companies = Company.query.count()
            pending_approvals = Company.query.filter_by(approval_status="pending").count()
            active_drives = PlacementDrive.query.filter_by(status="approved").count()
            
            return render_template("admin/dashboard.html", 
                                   s_count=total_students, 
                                   c_count=total_companies, 
                                   p_count=pending_approvals, 
                                   d_count=active_drives)

        # --- STUDENT LOGIN ---
        elif user.role == "student":
            student = Student.query.filter_by(user_id=user.id).first()
            if not student:
                flash("Student profile not found")
                return redirect(url_for("login"))
            if student.placement_status == "blacklisted":
                flash("You are blacklisted")
                return redirect(url_for("login"))
            return render_template("student/dashboard.html", student=student)

        # --- COMPANY LOGIN ---
        elif user.role == "company":
            company = Company.query.filter_by(user_id=user.id).first()
            if not company:
                flash("Company profile not found")
                return redirect(url_for("login"))
            if company.approval_status != "approved":
                flash("Company not approved yet")
                return redirect(url_for("login"))
            return render_template("company/dashboard.html", company=company)

    return render_template("login.html")

# ================= REGISTER STUDENT =================
@app.route("/register/student", methods=["GET", "POST"])
def register_student():
    if request.method == "POST":
        full_name = request.form.get("full_name")
        email = request.form.get("email")
        password = request.form.get("password")
        roll_no = request.form.get("roll_no")
        course = request.form.get("course")
        branch = request.form.get("branch")
        cgpa = request.form.get("cgpa")
        phone = request.form.get("phone")

        if User.query.filter_by(email=email).first():
            flash("Email already exists")
            return redirect(url_for("register_student"))

        if Student.query.filter_by(roll_no=roll_no).first():
            flash("Roll number exists")
            return redirect(url_for("register_student"))

        user = User(email=email, role="student")
        user.set_password(password)

        db.session.add(user)
        db.session.flush()

        student = Student(
            user_id=user.id,
            full_name=full_name,
            roll_no=roll_no,
            course=course,
            branch=branch,
            cgpa=float(cgpa),
            phone=phone,
            placement_status="active"
        )

        db.session.add(student)
        db.session.commit()
        flash("Student Registered")
        return redirect(url_for("login"))

    return render_template("register_student.html")

# ================= REGISTER COMPANY =================
@app.route("/register/company", methods=["GET", "POST"])
def register_company():
    if request.method == "POST":
        company_name = request.form.get("company_name")
        email = request.form.get("email")
        password = request.form.get("password")
        hr_name = request.form.get("hr_name")
        hr_email = request.form.get("hr_email")
        hr_contact = request.form.get("hr_contact")
        website = request.form.get("website")
        description = request.form.get("description")

        if User.query.filter_by(email=email).first():
            flash("Email exists")
            return redirect(url_for("register_company"))

        user = User(email=email, role="company")
        user.set_password(password)

        db.session.add(user)
        db.session.flush()

        company = Company(
            user_id=user.id,
            company_name=company_name,
            hr_name=hr_name,
            hr_email=hr_email,
            hr_contact=hr_contact,
            website=website,
            description=description,
            approval_status="pending"
        )

        db.session.add(company)
        db.session.commit()
        flash("Company Registered. Wait for approval.")
        return redirect(url_for("login"))

    return render_template("register_company.html")

# ================= ADMIN ROUTES =================
# 1. Manage Students
@app.route("/admin/students")
def show_students():
    search_query = request.args.get('search')
    if search_query:
        students = Student.query.filter(Student.full_name.ilike(f"%{search_query}%")).all()
    else:
        students = Student.query.all()
    return render_template("admin/students.html", students=students)

@app.route("/admin/blacklist-student/<int:student_id>")
def blacklist_student(student_id):
    student = Student.query.get_or_404(student_id)
    student.placement_status = "blacklisted"
    db.session.commit()
    flash("Student Blacklisted")
    return redirect(url_for("show_students"))

# 2. Manage Companies
@app.route("/admin/companies")
def show_companies():
    companies = Company.query.all()
    return render_template("admin/companies.html", companies=companies)

@app.route("/admin/approve-company/<int:company_id>")
def approve_company(company_id):
    company = Company.query.get_or_404(company_id)
    company.approval_status = "approved"
    db.session.commit()
    flash("Company Approved")
    return redirect(url_for("show_companies"))

@app.route("/admin/reject-company/<int:company_id>")
def reject_company(company_id):
    company = Company.query.get_or_404(company_id)
    company.approval_status = "rejected"
    db.session.commit()
    flash("Company Rejected")
    return redirect(url_for("show_companies"))

@app.route("/admin/blacklist-company/<int:company_id>")
def blacklist_company(company_id):
    company = Company.query.get_or_404(company_id)
    company.approval_status = "blacklisted"
    db.session.commit()
    flash("Company Blacklisted")
    return redirect(url_for("show_companies"))

# 3. Manage Drives
@app.route("/admin/drives")
def show_drives():
    drives = PlacementDrive.query.all()
    return render_template("admin/drives.html", drives=drives)

@app.route("/admin/approve-drive/<int:drive_id>")
def approve_drive(drive_id):
    drive = PlacementDrive.query.get_or_404(drive_id)
    drive.status = "approved"
    db.session.commit()
    flash("Placement Drive Approved!")
    return redirect(url_for("show_drives"))

# ================= COMPANY ROUTES =================
@app.route("/company/create-drive", methods=["GET", "POST"])
def create_drive():
    if request.method == "POST":
        company_email = request.form.get("company_email")
        job_title = request.form.get("job_title")
        job_description = request.form.get("job_description")
        eligibility_criteria = request.form.get("eligibility_criteria")
        application_deadline = request.form.get("application_deadline")

        user = User.query.filter_by(email=company_email, role="company").first()

        if not user:
            flash("Error: No approved company found with this email! Please check your email address.", "danger")
            return redirect(url_for("create_drive"))

        company = Company.query.filter_by(user_id=user.id).first()

        drive = PlacementDrive(
            company_id=company.id,
            job_title=job_title,
            job_description=job_description,
            eligibility_criteria=eligibility_criteria,
            application_deadline=application_deadline,
            status="pending"
        )

        db.session.add(drive)
        db.session.commit()
        flash("Drive Created Successfully! Wait for Admin approval.", "success")
        return redirect(url_for("create_drive"))

    return render_template("company/create_drive.html")

@app.route("/company/applications/<int:drive_id>")
def company_applications(drive_id):
    drive = PlacementDrive.query.get_or_404(drive_id)
    applications = Application.query.filter_by(drive_id=drive_id).all()
    return render_template("company/applications.html", applications=applications, drive=drive)

@app.route("/company/update-status/<int:application_id>/<status>")
def update_application_status(application_id, status):
    application = Application.query.get_or_404(application_id)
    application.status = status
    db.session.commit()
    flash(f"Student Application {status}!", "success")
    return redirect(url_for("company_applications", drive_id=application.drive_id))

# ================= STUDENT ROUTES =================
@app.route("/student/drives")
def student_drives():
    drives = PlacementDrive.query.filter_by(status="approved").all()
    return render_template("student/drives.html", drives=drives)

@app.route("/student/apply/<int:drive_id>", methods=["GET", "POST"])
def apply_drive(drive_id):
    drive = PlacementDrive.query.get_or_404(drive_id)
    
    if request.method == "POST":
        student_email = request.form.get("student_email")
        user = User.query.filter_by(email=student_email, role="student").first()
        
        if not user:
            flash("Error: No student account found with this email.", "danger")
            return redirect(url_for("apply_drive", drive_id=drive.id))
            
        student = Student.query.filter_by(user_id=user.id).first()
        
        existing = Application.query.filter_by(student_id=student.id, drive_id=drive.id).first()
        if existing:
            flash("You have already applied for this drive!", "warning")
            return redirect(url_for("student_drives"))

        application = Application(student_id=student.id, drive_id=drive.id, status="Applied")
        db.session.add(application)
        db.session.commit()
        
        flash("Successfully Applied for the Job!", "success")
        return redirect(url_for("student_drives"))

    return render_template("student/apply_drive.html", drive=drive)

@app.route("/student/applications/<student_email>")
def student_applications(student_email):
    user = User.query.filter_by(email=student_email, role="student").first()
    if not user:
        flash("Student profile not found.", "danger")
        return redirect(url_for('login'))
        
    student = Student.query.filter_by(user_id=user.id).first()
    applications = Application.query.filter_by(student_id=student.id).all()
    return render_template("student/applications.html", applications=applications)

# ===== EDIT STUDENT PROFILE & UPLOAD RESUME =====
@app.route("/student/edit-profile/<student_email>", methods=["GET", "POST"])
def edit_student_profile(student_email):
    user = User.query.filter_by(email=student_email, role="student").first()
    if not user:
        flash("User not found!", "danger")
        return redirect(url_for('login'))
        
    student = Student.query.filter_by(user_id=user.id).first()

    if request.method == "POST":
        student.phone = request.form.get("phone")
        student.cgpa = request.form.get("cgpa")

        resume = request.files.get("resume")
        if resume and resume.filename != '':
            filename = secure_filename(resume.filename)
            unique_filename = f"{student.roll_no}_{filename}"
            resume.save(os.path.join(app.config['UPLOAD_FOLDER'], unique_filename))
            student.resume_file = unique_filename

        db.session.commit()
        flash("Profile & Resume Updated Successfully!", "success")
        return redirect(url_for('edit_student_profile', student_email=student_email))

    return render_template("student/edit_profile.html", student=student, email=student_email)


# ================= INITIALIZATION =================
def create_admin():
    admin_email = "admin@placement.com"
    admin = User.query.filter_by(email=admin_email).first()
    if not admin:
        admin = User(email=admin_email, role="admin")
        admin.set_password("admin123")
        db.session.add(admin)
        db.session.commit()
        print("Admin Created: admin@placement.com / admin123")

with app.app_context():
    db.create_all()
    create_admin()

if __name__ == "__main__":
    app.run(debug=True)