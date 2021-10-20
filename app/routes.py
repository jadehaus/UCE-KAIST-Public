# -*- encoding: utf-8 -*-
"""
Copyright (c) Minu Kim - minu.kim@kaist.ac.kr
Templates from AppSeed.us
"""

import os
import logging
from datetime import date
import json
from flask import render_template, flash, redirect, url_for, request, jsonify
from flask_login import login_user, logout_user, current_user, login_required
from werkzeug.urls import url_parse
from app import app, db
from app.forms import LoginForm, RegisterForm, ResetPasswordForm
from app.models import User, Department, Course
from werkzeug.exceptions import HTTPException, NotFound, abort
from jinja2 import TemplateNotFound


@app.errorhandler(404)
def not_found_error(error):
    return render_template('page-404.html'), 404


@app.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    return render_template('page-500.html'), 500


@app.route('/')
@app.route('/index')
def index():
    if current_user.is_authenticated:
        if current_user.id == 1:
            num_users = User.query.count()
            num_subjects = Course.query.count()
            return render_template('index.html', n1=num_users, n2=num_subjects)
        if current_user.course_info is None:
            current_user.course_info = "{}"
        if current_user.department is None:
            dept = Department(user=current_user)
            dept.is_advanced_major = 0
            dept.is_individually_designed = 0
            dept.major = ""
            dept.double_major = ""
            dept.minor = ""
            current_user.department = dept
            db.session.add(dept)
            db.session.commit()
        if current_user.replaced is None:
            current_user.replaced = ""
        if current_user.doubly_recognized is None:
            current_user.doubly_recognized = ""
        if current_user.individual is None:
            current_user.individual = ""
        if current_user.recognized_as is None:
            current_user.recognized_as = "{}"
        db.session.commit()
        return render_template('index.html', n1=None, n2=None)
    return render_template('index.html', n1=None, n2=None)


# Logout user
@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('index'))


# Register a new user
@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegisterForm(request.form)
    msg = None
    success = False
    if request.method == 'GET':
        return render_template('accounts/register.html', form=form, msg=msg)

    if current_user.is_authenticated:
        return redirect(url_for('index'))

    if form.validate_on_submit():
        if not request.form.get('agree'):
            msg = '개인정보 보호방침 동의에 체크해 주세요.'
            return render_template('accounts/register.html', form=form, msg=msg)
        if User.query.filter_by(username=form.username.data).first() is not None:
            msg = '이미 사용된 아이디입니다. <a href="' + url_for('login') + '">로그인하기.</a>'
            return render_template('accounts/register.html', form=form, msg=msg)
        if User.query.filter_by(email=form.email.data).first() is not None:
            msg = '이미 사용중인 이메일 주소입니다. <a href="' + url_for('login') + '">로그인하기.</a>'
            return render_template('accounts/register.html', form=form, msg=msg)
        user = User(username=form.username.data, email=form.email.data)
        user.set_password(form.password.data)
        user.admitted_year = form.year.data
        db.session.add(user)
        db.session.commit()
        msg = '회원가입이 완료되었습니다. <a href="' + url_for('login') + '">로그인하기.</a>'
        return redirect(url_for('login'))
    return render_template('accounts/register.html', form=form, msg=msg, success=success)


# Authenticate user
@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = LoginForm(request.form)
    remember = request.form.get('remember')
    msg = None
    if form.validate_on_submit():
        username = request.form.get('username', '', type=str)
        user = User.query.filter_by(username=username).first()
        if user is None or not user.check_password(form.password.data):
            msg = "계정 정보가 잘못되었습니다. 다시 시도해주세요."
            return render_template('accounts/login.html', form=form, msg=msg)
        login_user(user, remember=remember)
        next_page = request.args.get('next')
        if not next_page or url_parse(next_page).netloc != '':
            next_page = url_for('index')
        return redirect(next_page)
    return render_template('accounts/login.html', form=form, msg=msg)


@app.route('/reset_password', methods=['GET', 'POST'])
def reset_password():
    if not current_user.is_authenticated:
        return redirect(url_for('index'))
    form = ResetPasswordForm()
    if form.validate_on_submit():
        current_user.set_password(form.password.data)
        db.session.commit()
        msg = '비밀번호가 정상적으로 변경되었습니다.'
        return render_template('accounts/reset_password.html', form=form, msg=msg)
    return render_template('accounts/reset_password.html', form=form, msg=None)


@app.route('/info', methods=['GET'])
def info():
    return render_template('info.html')


@app.route('/privacy', methods=['GET'])
def privacy():
    return render_template('privacy.html')


@app.route('/withdraw', methods=['DELETE'])
def withdraw():
    if current_user.is_authenticated:
        current_user.courses = []
        db.session.commit()
        dept = current_user.department
        db.session.delete(dept)
        user = User.query.filter_by(id=current_user.id).first()
        db.session.delete(user)
        db.session.commit()
        return url_for('login')
    return url_for('index')


@app.route('/course_add', methods=["GET"])
@login_required
def course_add():
    courses = Course.query.order_by(Course.subject_type).all()
    course_info = json.loads(current_user.course_info)
    return render_template('course_add.html', courses=courses, course_info=course_info)


@app.route('/get_course_table', methods=["GET"])
@login_required
def get_course_table():
    courses = Course.query.order_by(Course.subject_type).all()
    data = {"data": []}
    for course in courses:
        data["data"].append({'department': course.department,
                             'type': course.subject_type,
                             'code': course.code,
                             'name': course.name,
                             'credit': course.credit,
                             'taken': 1 if (course in current_user.courses) else 0,
                             'id': course.id})
    return jsonify(data)


@app.route('/add_or_delete_course', methods=["DELETE", "PUT"])
@login_required
def add_or_delete_course():
    data = request.get_json()
    if request.method == 'DELETE':
        course = Course.query.filter_by(id=data.get('id')).first()
        try:
            course_info = json.loads(current_user.course_info)
            course_info.pop(str(course.id))
            current_user.course_info = json.dumps(course_info)
            current_user.courses.remove(course)
        except ValueError:
            pass
        except KeyError:
            pass
        db.session.commit()
        return jsonify()  # , 203

    elif request.method == 'PUT':
        course = Course.query.filter_by(id=data.get('id')).first()
        if course not in current_user.courses:
            current_user.courses.append(course)
            course_info = json.loads(current_user.course_info)
            if str(course.id) not in course_info:
                # course_info[str(course.id)] = {"semester": None, "letter": None}
                course_info[str(course.id)] = {"semester": None}
                current_user.course_info = json.dumps(course_info)
        db.session.commit()
        return jsonify()

    db.session.commit()
    return jsonify(data)


@app.route('/replace_or_unreplace', methods=["DELETE", "PUT"])
@login_required
def replace_or_unreplace():
    data = request.get_json().get('id')
    if current_user.replaced is None:
        current_user.replaced = ""
    if request.method == 'DELETE':
        course_id = "@" + str(data) + "@"
        current_user.replaced = current_user.replaced.replace(course_id, "")
        db.session.commit()
        return jsonify()

    elif request.method == 'PUT':
        course_id = "@" + str(data) + "@"
        current_user.replaced += course_id
        db.session.commit()
        return jsonify()

    db.session.commit()
    return jsonify(data)


@app.route('/individual_or_not', methods=["DELETE", "PUT"])
@login_required
def individual_or_not():
    data = request.get_json().get('id')
    if current_user.individual is None:
        current_user.individual = ""
    if request.method == 'DELETE':
        course_id = "@" + str(data) + "@"
        current_user.individual = current_user.individual.replace(course_id, "")
        db.session.commit()
        return jsonify()

    elif request.method == 'PUT':
        course_id = "@" + str(data) + "@"
        current_user.individual += course_id
        db.session.commit()
        return jsonify()

    db.session.commit()
    return jsonify(data)


@app.route('/double_or_undouble', methods=["DELETE", "PUT"])
@login_required
def double_or_undouble():
    data = request.get_json().get('id')
    if current_user.replaced is None:
        current_user.replaced = ""
    if request.method == 'DELETE':
        course_id = "@" + str(data) + "@"
        current_user.doubly_recognized = current_user.doubly_recognized.replace(course_id, "")
        db.session.commit()
        return jsonify()

    elif request.method == 'PUT':
        course_id = "@" + str(data) + "@"
        current_user.doubly_recognized += course_id
        db.session.commit()
        return jsonify()

    db.session.commit()
    return jsonify(data)


@app.route('/recognize', methods=["DELETE", "PUT"])
@login_required
def recognize():
    data = request.get_json()
    dept = data.get('dept')
    course_id = str(data.get('course'))
    if request.method == 'PUT':
        if dept is not None:
            recognized = json.loads(current_user.recognized_as)
            dict_departments = {"MAS": "수리과학과", "PH": "물리학과", "CH": "화학과", "BS": "생명과학과",
                                "ME": "기계공학과", "AE": "항공우주공학과", "EE": "전기및전자공학부", "CE": "건설및환경공학과학과",
                                "CS": "전산학부", "BiS": "바이오및뇌공학과", "CBE": "생명화학공학과", "ID": "산업디자인학과",
                                "IE": "산업및시스템공학과", "MS": "신소재공학과", "NQE": "원자력및양자공학과",
                                "MSB": "기술경영학부", "TS": "융합인재학부"}
            dict_department_names = {}
            for key, item in dict_departments.items():
                dict_department_names[item] = key
            if dept == "None":
                try:
                    recognized.pop(course_id)
                except KeyError:
                    pass
            else:
                recognized[course_id] = dict_department_names[dept]
            current_user.recognized_as = json.dumps(recognized)

        db.session.commit()
        return jsonify()

    db.session.commit()
    return jsonify(data)


@app.route('/edit_course', methods=["PUT"])
@login_required
def edit_course():
    data = request.get_json()
    semester = data.get('semester')
    if request.method == 'PUT':
        course = Course.query.filter_by(id=data.get('id')).first()
        try:
            course_info = json.loads(current_user.course_info)
            course_info[str(course.id)]['semester'] = semester
            current_user.course_info = json.dumps(course_info)
            db.session.commit()
        except KeyError:
            course_info = json.loads(current_user.course_info)
            course_info[str(course.id)] = {"semester": semester}
            current_user.course_info = json.dumps(course_info)
            db.session.commit()
        return jsonify()

    db.session.commit()
    return jsonify(data)


@app.route('/edit_letter', methods=["PUT"])
@login_required
def edit_letter():
    data = request.get_json()
    if request.method == 'PUT':
        course = Course.query.filter_by(id=data.get('id')).first()
        try:
            course_info = json.loads(current_user.course_info)
            course_info[str(course.id)]['letter'] = data.get('letter')
            current_user.course_info = json.dumps(course_info)
            db.session.commit()
        except KeyError:
            course_info = json.loads(current_user.course_info)
            course_info[str(course.id)] = {"letter": data.get('letter'), 'semester': None}
            current_user.course_info = json.dumps(course_info)
            db.session.commit()
        return jsonify()

    db.session.commit()
    return jsonify(data)


@app.route('/course_view', methods=["GET", "POST"])
@login_required
def course_view():
    current_year = date.today().year
    if current_user.course_info is None:
        current_user.course_info = "{}"
        db.session.commit()
    course_info = json.loads(current_user.course_info)
    semesters = []
    for _, val in course_info.items():
        if (val['semester'] not in semesters) and (val['semester'] is not None):
            semesters.append(val['semester'])
    semester_order = {"P": 0, "봄학기": 1, "여름학기": 2, "가을학기": 3, "겨울학기": 4}
    semesters.sort(key=lambda x: semester_order[x[1]])
    semesters.sort(key=lambda x: str(x[0]))
    return render_template('course_view.html', course_info=course_info, year=current_year, semesters=semesters)


@app.route('/add_department', methods=["DELETE", "PUT"])
@login_required
def add_department():
    data = request.get_json()
    advanced = data.get('advanced')
    individual = data.get('individual')
    major = data.get('major')
    doubles = data.get('double')
    minors = data.get('minor')
    year = data.get('year')
    if request.method == 'PUT':
        if year is not None:
            current_user.admitted_year = year
        if advanced is not None:
            if advanced:
                current_user.department.is_advanced_major = 1
            else:
                current_user.department.is_advanced_major = 0
        if individual is not None:
            if individual:
                current_user.department.is_individually_designed = 1
            else:
                current_user.department.is_individually_designed = 0
                current_user.individual = ""
        if major is not None:
            current_user.department.major = major
            current_user.department.double_major = ""
            current_user.department.minor = ""
        if doubles:
            current_user.department.double_major = ""
            for double in doubles:
                if double == "@":
                    current_user.department.double_major = ""
                    break
                current_user.department.double_major += "@" + double + "@"
        print(current_user.department.double_major)

        if minors:
            current_user.department.minor = ""
            for minor in minors:
                if minor == "@":
                    current_user.department.minor = ""
                    break
                if minor in current_user.department.double_major:
                    continue
                current_user.department.minor += "@" + minor + "@"

        current_user.department.validate_major()
        db.session.commit()
        return jsonify()

    db.session.commit()
    return jsonify(data)


@app.route('/quick_add', methods=["GET", "PUT"])
@login_required
def quick_add():
    try:
        data = request.get_json()
        txt = data.get('txt')
        course_dict = json.loads(txt)
    except json.decoder.JSONDecodeError:
        return jsonify()

    courses = course_dict
    course_info = json.loads(current_user.course_info)
    for course in courses:
        actual_course = Course.query.filter_by(course_id=course["course_id"], name=course["name"]).first()
        if actual_course is not None:
            if str(actual_course.id) in course_info:
                if course["year"] == 0:
                    course_info[str(actual_course.id)]["semester"] = 'AP'
                else:
                    course_info[str(actual_course.id)]["semester"] = [course["year"], course["semester"]]
            if actual_course not in current_user.courses:
                current_user.courses.append(actual_course)
                if course["year"] == 0:
                    course_info[str(actual_course.id)] = {"semester": 'AP'}
                else:
                    course_info[str(actual_course.id)] = {"semester": [course["year"], course["semester"]]}
                db.session.commit()
    current_user.course_info = json.dumps(course_info)
    db.session.commit()
    flash("과목이 성공적으로 추가되었습니다.")
    return url_for('course_view')


@app.route('/course_analysis', methods=["GET", "POST"])
@login_required
def course_analysis():
    if current_user.department is None:
        dept = Department(user=current_user)
        dept.is_advanced_major = 0
        dept.is_individually_designed = 0
        dept.major = ""
        dept.double_major = ""
        dept.minor = ""
        current_user.department = dept
        db.session.add(dept)
        db.session.commit()
    if current_user.admitted_year is None:
        current_user.admitted_year = 2021
        db.session.commit()
    if current_user.recognized_as is None:
        current_user.recognized_as = "{}"
        db.session.commit()
    if current_user.doubly_recognized is None:
        current_user.doubly_recognized = ""
        db.session.commit()
    if current_user.replaced is None:
        current_user.replaced = ""
        db.session.commit()
    if current_user.individual is None:
        current_user.individual = ""
        db.session.commit()
    if current_user.is_authenticated:
        recognized = json.loads(current_user.recognized_as)
        dict_departments = {"MAS": "수리과학과", "PH": "물리학과", "CH": "화학과", "BS": "생명과학과",
                            "ME": "기계공학과", "AE": "항공우주공학과", "EE": "전기및전자공학부", "CE": "건설및환경공학과학과",
                            "CS": "전산학부", "BiS": "바이오및뇌공학과", "CBE": "생명화학공학과", "ID": "산업디자인학과",
                            "IE": "산업및시스템공학과", "MS": "신소재공학과", "NQE": "원자력및양자공학과",
                            "MSB": "기술경영학부", "TS": "융합인재학부"}
        dict_department_names = {}
        for key, item in dict_departments.items():
            dict_department_names[item] = key
    return render_template('course_analysis.html', recognized=recognized, names=dict_department_names)


@app.route('/reset_department', methods=["GET", "PUT"])
@login_required
def reset_department():
    data = request.get_json()
    if request.method == 'PUT':
        if data.get('flag') == 1:
            current_user.department.major = ""
            current_user.department.double_major = ""
            current_user.department.minor = ""
            current_user.department.is_advanced_major = 0
            current_user.department.is_individually_designed = 0
            current_user.individual = ""
            current_user.replaced = ""
            current_user.doubly_recognized = ""
            current_user.recognized_as = "{}"
            db.session.commit()
            return jsonify()
    db.session.commit()
    return jsonify(data)
