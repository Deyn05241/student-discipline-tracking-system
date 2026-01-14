# app.py
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import or_
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user
from werkzeug.security import generate_password_hash, check_password_hash
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, IntegerField, SelectField, DateField, TextAreaField
from wtforms.validators import DataRequired, Email, Optional
from datetime import datetime
import calendar, os

app = Flask(__name__)
app.config['SECRET_KEY'] = os.urandom(12)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///site.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128))

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class Student(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    age = db.Column(db.Integer)
    gender = db.Column(db.String(10))
    grade_level = db.Column(db.String(20))
    section = db.Column(db.String(20))
    strand = db.Column(db.String(50))
    offenses = db.relationship('Offense', backref='student', lazy=True)

class Offense(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('student.id'), nullable=False)
    offense_type = db.Column(db.String(20), nullable=False)
    category = db.Column(db.String(50))
    subtype = db.Column(db.String(100))
    date = db.Column(db.Date, nullable=False)
    description = db.Column(db.Text)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Forms
class LoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Login')

class RegisterForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Register')

class StudentForm(FlaskForm):
    name = StringField('Name', validators=[DataRequired()])
    age = IntegerField('Age', validators=[DataRequired()])
    gender = SelectField('Gender', choices=[('Male', 'Male'), ('Female', 'Female')], validators=[DataRequired()])
    
    grade_level = SelectField(
        'Grade Level',
        choices=[('11', 'Grade 11'), ('12', 'Grade 12')],
        validators=[DataRequired()]
    )
    
    section = SelectField(
        'Section',
        choices=[('A', 'A'), ('B', 'B'), ('C', 'C'), ('D', 'D'), ('E', 'E'), ('F', 'F')],
        validators=[DataRequired()]
    )
    
    strand = SelectField(
        'Strand',
        choices=[
            ('STEM', 'STEM'),
            ('HUMSS', 'HUMSS'),
            ('ABM', 'ABM')
        ],
        validators=[DataRequired()]
    )
    
    submit = SubmitField('Submit')

class OffenseForm(FlaskForm):
    offense_type = SelectField('Type', choices=[('warning', 'Warning'), ('minor', 'Minor'), ('major', 'Major')], validators=[DataRequired()])
    category = SelectField('Category',
                          choices=[
                              ('', '— Select Category —'),
                              ('Academic', 'Academic'),
                              ('Behavioral', 'Behavioral'),
                              ('Attendance', 'Attendance'),
                              ('Uniform', 'Uniform/Dress Code'),
                              ('Property', 'Property Damage/Theft'),
                              ('Safety', 'Safety/Threat'),
                              ('Other', 'Other')
                          ],
                          validators=[DataRequired()])
    subtype = StringField('Subtype / Specific Offense',
                         validators=[Optional()])
    date = DateField('Date', validators=[DataRequired()])
    description = TextAreaField('Description')
    submit = SubmitField('Submit')

# Routes
@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegisterForm()
    if form.validate_on_submit():
        if User.query.filter_by(email=form.email.data).first():
            flash('Email already registered.')
            return redirect(url_for('register'))
        user = User(email=form.email.data)
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash('Registration successful. Please log in.')
        return redirect(url_for('login'))
    return render_template('register.html', form=form)

@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and user.check_password(form.password.data):
            login_user(user)
            return redirect(url_for('students'))
        flash('Invalid email or password.')
    return render_template('login.html', form=form)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/')
@login_required
def index():
    return redirect(url_for('students'))

@app.route('/students')
@login_required
def students():
    students = Student.query.all()
    return render_template('students.html', students=students)

@app.route('/student/add', methods=['GET', 'POST'])
@login_required
def add_student():
    form = StudentForm()
    if form.validate_on_submit():
        student = Student(
            name=form.name.data,
            age=form.age.data,
            gender=form.gender.data,
            grade_level=form.grade_level.data,
            section=form.section.data,
            strand=form.strand.data
        )
        db.session.add(student)
        db.session.commit()
        flash('Student added successfully.')
        return redirect(url_for('students'))
    return render_template('student_form.html', form=form, title='Add Student')

@app.route('/student/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def edit_student(id):
    student = Student.query.get_or_404(id)
    form = StudentForm(obj=student)
    if form.validate_on_submit():
        student.name = form.name.data
        student.age = form.age.data
        student.gender = form.gender.data
        student.grade_level = form.grade_level.data
        student.section = form.section.data
        student.strand = form.strand.data
        db.session.commit()
        flash('Student updated successfully.')
        return redirect(url_for('students'))
    return render_template('student_form.html', form=form, title='Edit Student')

@app.route('/student/<int:id>/delete', methods=['POST'])
@login_required
def delete_student(id):
    student = Student.query.get_or_404(id)
    
    Offense.query.filter_by(student_id=id).delete()
    db.session.delete(student)
    db.session.commit()
    flash('Student deleted successfully.')
    return redirect(url_for('students'))

@app.route('/student/<int:id>/offenses')
@login_required
def offenses(id):
    student = Student.query.get_or_404(id)
    offenses = Offense.query.filter_by(student_id=id).all()
    return render_template('offenses.html', student=student, offenses=offenses)

@app.route('/student/<int:id>/offense/add', methods=['GET', 'POST'])
@login_required
def add_offense(id):
    student = Student.query.get_or_404(id)
    form = OffenseForm()
    if form.validate_on_submit():
        offense = Offense(
            student_id=student.id,
            offense_type=form.offense_type.data,
            category=form.category.data,
            subtype=form.subtype.data,
            date=form.date.data,
            description=form.description.data
        )
        db.session.add(offense)
        db.session.commit()
        flash('Offense added successfully.')
        return redirect(url_for('offenses', id=student.id))
    return render_template('offense_form.html', form=form, title='Add Offense', student=student)

@app.route('/offense/<int:id>/delete', methods=['POST'])
@login_required
def delete_offense(id):
    offense = Offense.query.get_or_404(id)
    student_id = offense.student_id
    db.session.delete(offense)
    db.session.commit()
    flash('Offense deleted successfully.')
    return redirect(url_for('offenses', id=student_id))

@app.route('/graphs')
@login_required
def graphs():
    return render_template('graphs.html')

@app.route('/api/offenses_by_type_grade')
@login_required
def offenses_by_type_grade():
    from sqlalchemy import func
    
    # Group by grade and offense_type
    results = db.session.query(
        Student.grade_level,
        Offense.offense_type,
        func.count(Offense.id).label('count')
    ).join(Offense, Student.id == Offense.student_id)\
     .group_by(Student.grade_level, Offense.offense_type)\
     .all()

    data = {}
    for grade, offense_type, count in results:
        if grade not in data:
            data[grade] = {'warning': 0, 'minor': 0, 'major': 0}
        data[grade][offense_type] = count

    return jsonify(data)

@app.route('/api/offenses_by_gender_grade')
@login_required
def offenses_by_gender_grade():
    from sqlalchemy import func
    results = db.session.query(
        Student.grade_level,
        Student.gender,
        func.count(Offense.id).label('count')
    ).join(Offense, Student.id == Offense.student_id).group_by(
        Student.grade_level, Student.gender
    ).all()

    data = {}
    for grade, gender, count in results:
        if grade not in data:
            data[grade] = {'Male': 0, 'Female': 0}
        data[grade][gender] = count
    return jsonify(data)

@app.route('/student/<int:id>/calendar')
@login_required
def calendar_view(id):
    student = Student.query.get_or_404(id)
    year = request.args.get('year', datetime.now().year, type=int)
    month = request.args.get('month', datetime.now().month, type=int)
    if month < 1 or month > 12:
        month = datetime.now().month

    start_date = datetime(year, month, 1)
    _, last_day = calendar.monthrange(year, month)
    end_date = datetime(year, month, last_day)

    offenses = Offense.query.filter(
        Offense.student_id == id,
        Offense.date >= start_date.date(),
        Offense.date <= end_date.date()
    ).order_by(Offense.date).all()

    from collections import defaultdict
    offense_dates = defaultdict(list)

    for offense in offenses:
        day = offense.date.day
        detail = f"{offense.offense_type.capitalize()} - {offense.description or 'No description'} ({offense.date.strftime('%Y-%m-%d')})"
        offense_dates[day].append(detail)

    month_days = calendar.monthcalendar(year, month)
    month_name = calendar.month_name[month]

    prev_month = month - 1 if month > 1 else 12
    prev_year = year if month > 1 else year - 1
    next_month = month + 1 if month < 12 else 1
    next_year = year if month < 12 else year + 1

    return render_template(
        'calendar.html',
        student=student,
        month_days=month_days,
        year=year,
        month=month,
        month_name=month_name,
        offense_dates=offense_dates,
        prev_month=prev_month,
        prev_year=prev_year,
        next_month=next_month,
        next_year=next_year
    )

@app.route('/analytics/all_offenses')
@login_required
def all_offenses():
    search = request.args.get('search', '').strip()
    page = request.args.get('page', 1, type=int)
    per_page = 20

    query = Offense.query.join(Student).order_by(Offense.date.desc())

    if search:
        search_term = f"%{search}%"
        query = query.filter(
            or_(
                Student.name.ilike(search_term),
                Offense.description.ilike(search_term),
                Offense.offense_type.ilike(search_term)
            )
        )

    pagination = query.paginate(page=page, per_page=per_page, error_out=False)
    offenses = pagination.items

    return render_template(
        'all_offenses.html',
        offenses=offenses,
        pagination=pagination,
        search=search
    )



if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
