from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
import os

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///students.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.secret_key = os.environ.get('FLASK_SECRET', 'dev-secret')

db = SQLAlchemy(app)

class Student(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    age = db.Column(db.Integer, nullable=True)
    major = db.Column(db.String(120), nullable=True)

    def __repr__(self):
        return f"<Student {self.name} ({self.email})>"

@app.before_first_request
def create_tables_and_seed():
    db.create_all()
    if Student.query.count() == 0:
        sample = [
            Student(name="Alice Johnson", email="alice@example.com", age=20, major="Mathematics"),
            Student(name="Bob Smith", email="bob@example.com", age=22, major="Computer Science"),
            Student(name="Carol Lee", email="carol@example.com", age=21, major="Biology"),
        ]
        db.session.bulk_save_objects(sample)
        db.session.commit()

@app.route('/')
def index():
    q = request.args.get('q', '').strip()
    if q:
        # simple search by name, email, or major
        search = f"%{q}%"
        students = Student.query.filter(
            (Student.name.ilike(search)) |
            (Student.email.ilike(search)) |
            (Student.major.ilike(search))
        ).all()
    else:
        students = Student.query.order_by(Student.id).all()
    return render_template('index.html', students=students, q=q)

@app.route('/add', methods=['GET', 'POST'])
def add_student():
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        email = request.form.get('email', '').strip()
        age = request.form.get('age') or None
        major = request.form.get('major', '').strip()
        if not name or not email:
            flash("Name and email are required.", "danger")
            return redirect(url_for('add_student'))
        try:
            age_val = int(age) if age else None
        except ValueError:
            flash("Age must be a number.", "danger")
            return redirect(url_for('add_student'))
        student = Student(name=name, email=email, age=age_val, major=major or None)
        try:
            db.session.add(student)
            db.session.commit()
            flash("Student added.", "success")
            return redirect(url_for('index'))
        except Exception as e:
            db.session.rollback()
            flash(f"Error adding student: {e}", "danger")
            return redirect(url_for('add_student'))
    return render_template('add_edit.html', action="Add", student=None)

@app.route('/edit/<int:student_id>', methods=['GET', 'POST'])
def edit_student(student_id):
    student = Student.query.get_or_404(student_id)
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        email = request.form.get('email', '').strip()
        age = request.form.get('age') or None
        major = request.form.get('major', '').strip()
        if not name or not email:
            flash("Name and email are required.", "danger")
            return redirect(url_for('edit_student', student_id=student_id))
        try:
            age_val = int(age) if age else None
        except ValueError:
            flash("Age must be a number.", "danger")
            return redirect(url_for('edit_student', student_id=student_id))
        student.name = name
        student.email = email
        student.age = age_val
        student.major = major or None
        try:
            db.session.commit()
            flash("Student updated.", "success")
            return redirect(url_for('index'))
        except Exception as e:
            db.session.rollback()
            flash(f"Error updating student: {e}", "danger")
            return redirect(url_for('edit_student', student_id=student_id))
    return render_template('add_edit.html', action="Edit", student=student)

@app.route('/view/<int:student_id>')
def view_student(student_id):
    student = Student.query.get_or_404(student_id)
    return render_template('view.html', student=student)

@app.route('/delete/<int:student_id>', methods=['POST'])
def delete_student(student_id):
    student = Student.query.get_or_404(student_id)
    try:
        db.session.delete(student)
        db.session.commit()
        flash("Student deleted.", "success")
    except Exception as e:
        db.session.rollback()
        flash(f"Error deleting student: {e}", "danger")
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)