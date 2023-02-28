# -*- encoding: utf-8 -*-
"""
Copyright (c) Minu Kim - minu.kim@kaist.ac.kr
Templates from AppSeed.us
"""

import os
import logging
from datetime import date, datetime
import json
from flask import render_template, flash, redirect, url_for, request, jsonify
from flask_login import login_user, logout_user, current_user, login_required
from werkzeug.urls import url_parse
from app import app, db, mail, sitemap
from app.utils.forms import LoginForm, RegisterForm, ResetPasswordForm
from app.utils.forms import ResetPasswordRequestForm
from app.utils.email import send_password_reset_email
from app.models import User, Department, Course
from werkzeug.exceptions import HTTPException, NotFound, abort
from jinja2 import TemplateNotFound
from sqlalchemy import or_, and_
import pandas as pd
import numpy as np
from scipy.stats import beta as beta_function
from sklearn.metrics.pairwise import cosine_similarity


@app.errorhandler(404)
def not_found_error(error):
    return render_template('page-404.html'), 404


@app.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    return render_template('page-500.html'), 500


def time_stamp():
    last_login = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    current_user.last_login = last_login
    db.session.commit()


@app.route('/')
@app.route('/index')
def index():
    if current_user.is_authenticated:
        if current_user.course_info is None:
            current_user.course_info = "{}"
        if current_user.department is None:
            dept = Department(user=current_user)
            current_user.department = dept
            db.session.add(dept)
            db.session.commit()
            reset_department(request_from_app=False)
        time_stamp()
        db.session.commit()
        return render_template('index.html', n1=None, n2=None)
    return render_template('index.html', n1=None, n2=None)


@sitemap.register_generator
def index():
    yield 'index', {}


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
        user = User.query.filter(or_(User.username==username, User.email==username)).first()
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
        return render_template('accounts/reset_password.html', user=current_user, form=form, msg=msg)
    return render_template('accounts/reset_password.html', user=current_user, form=form, msg=None)


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
    time_stamp()
    courses = Course.query.order_by(Course.subject_type).all()
    course_info = json.loads(current_user.course_info)
    gpa_recommendation = course_recommendation(rating='gpa')
    like_recommendation = course_recommendation(rating='like')
    grad_recommendation = bayesian_recommendation()
    return render_template('course_add.html', 
                            courses=courses, 
                            course_info=course_info,
                            gpa_rec=gpa_recommendation,
                            like_rec=like_recommendation,
                            grad_rec=grad_recommendation)


@app.route('/get_course_table', methods=["GET"])
@login_required
def get_course_table():
    time_stamp()
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
    time_stamp()
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
                course_info[str(course.id)] = {"semester": None, "letter": None}
                current_user.course_info = json.dumps(course_info)
        db.session.commit()
        return jsonify()
    # db.session.commit()
    # return jsonify(data)


@app.route('/replace_or_unreplace', methods=["DELETE", "PUT"])
@login_required
def replace_or_unreplace():
    time_stamp()
    data = request.get_json().get('id')
    if current_user.replaced is None:
        current_user.replaced = ""
    if request.method == 'DELETE':
        course_id = "@" + str(data) + "@"
        current_user.replaced = current_user.replaced.replace(course_id, "")
        db.session.commit()
        return jsonify()  # , 203
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
    time_stamp()
    data = request.get_json().get('id')
    if current_user.individual is None:
        current_user.individual = ""
    if request.method == 'DELETE':
        course_id = "@" + str(data) + "@"
        current_user.individual = current_user.individual.replace(course_id, "")
        db.session.commit()
        return jsonify()  # , 203
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
    time_stamp()
    data = request.get_json().get('id')
    if current_user.replaced is None:
        current_user.replaced = ""
    if request.method == 'DELETE':
        course_id = "@" + str(data) + "@"
        current_user.doubly_recognized = current_user.doubly_recognized.replace(course_id, "")
        db.session.commit()
        return jsonify()  # , 203
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
    time_stamp()
    dict_departments = {"MAS": "수리과학과", "PH": "물리학과", "CH": "화학과", "BS": "생명과학과",
                                "ME": "기계공학과", "AE": "항공우주공학과", "EE": "전기및전자공학부", "CE": "건설및환경공학과학과",
                                "CS": "전산학부", "BiS": "바이오및뇌공학과", "CBE": "생명화학공학과", "ID": "산업디자인학과",
                                "IE": "산업및시스템공학과", "MS": "신소재공학과", "NQE": "원자력및양자공학과",
                                "MSB": "기술경영학부", "TS": "융합인재학부"}
    data = request.get_json()
    dept = data.get('dept')
    course_id = str(data.get('course'))
    if request.method == 'PUT':
        if dept is not None:
            recognized = json.loads(current_user.recognized_as)
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


@app.route('/edit_rating', methods=["PUT"])
@login_required
def edit_rating():
    time_stamp()
    data = request.get_json()
    rating_seq = {0: 1, 1: -1, -1: 0}
    if request.method == 'PUT':
        course = Course.query.filter_by(id=data.get('id')).first()
        course_info = json.loads(current_user.course_info)
        try:
            cur_rating = course_info[str(course.id)]['rating']
            new_rating = rating_seq[cur_rating]
            course_info[str(course.id)]['rating'] = new_rating
            current_user.course_info = json.dumps(course_info)
        except KeyError:
            assert 'semester' in course_info[str(course.id)]
            course_info[str(course.id)]['rating'] = 0
            current_user.course_info = json.dumps(course_info)
        db.session.commit()
        return jsonify()
    db.session.commit()
    return jsonify(data)


@app.route('/edit_course', methods=["PUT"])
@login_required
def edit_course():
    time_stamp()
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
            course_info[str(course.id)] = {"semester": semester, 'letter': None}
            current_user.course_info = json.dumps(course_info)
            db.session.commit()
        return jsonify()
    db.session.commit()
    return jsonify(data)


@app.route('/edit_letter', methods=["PUT"])
@login_required
def edit_letter():
    time_stamp()
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
    time_stamp()
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
    complete = 1
    for course in course_info:
        if course_info[course]['semester'] is None:
            complete = 0
    return render_template('course_view.html', course_info=course_info, current_year=current_year, semesters=semesters, complete=complete)


@app.route('/render_graph', methods=["POST"])
@login_required
def render_graph():
    time_stamp()
    info = json.loads(current_user.course_info)
    data, semesters = [], []
    for _, val in info.items():
        if (val['semester'] not in semesters) and (val['semester'] is not None):
            semesters.append(val['semester'])
    semester_order = {"P": 0, "봄학기": 1, "여름학기": 2, "가을학기": 3, "겨울학기": 4}
    semesters.sort(key=lambda x: semester_order[x[1]])
    semesters.sort(key=lambda x: str(x[0]))
    if "AP" in semesters:
        semesters = ["AP"] + semesters[:-1]
    for semester in semesters:
        gpa, _, major, _, omit = current_user.render_gpa(semester=semester)
        if not omit:
            data.append({'semester': semester, 'gpa': gpa, 'major': major})
    return jsonify(data)


@app.route('/add_department', methods=["DELETE", "PUT"])
@login_required
def add_department():
    time_stamp()
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
    time_stamp()
    try:
        data = request.get_json()
        txt = data.get('txt')
        course_dict = json.loads(txt)
    except json.decoder.JSONDecodeError:
        return jsonify()
    courses = []
    for course in course_dict:
        if course["letter"] not in ["R", "W", "U"]:
            courses.append(course)
    course_info = json.loads(current_user.course_info)
    for course in courses:
        actual_course = Course.query.filter_by(course_id=course["course_id"], name=course["name"]).first()
        if actual_course is not None:
            if str(actual_course.id) not in course_info:
                course_info[str(actual_course.id)] = {"semester": None, "letter": course["letter"]}
            if actual_course not in current_user.courses:
                current_user.courses.append(actual_course)
                db.session.commit()
            if course["year"] == 0:
                course_info[str(actual_course.id)]["semester"] = 'AP'
            else:
                course_info[str(actual_course.id)]["semester"] = [course["year"], course["semester"]]
    current_user.course_info = json.dumps(course_info)
    db.session.commit()
    flash("과목이 성공적으로 추가되었습니다.")
    return url_for('course_view')



@app.route('/course_analysis', methods=["GET", "POST"])
@login_required
def course_analysis():
    time_stamp()
    if current_user.department is None:
        dept = Department(user=current_user)
        current_user.department = dept
        db.session.add(dept)
        db.session.commit()
        reset_department(request_from_app=False)
    if current_user.admitted_year is None:
        current_user.admitted_year = 2021
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
def reset_department(request_from_app=True):
    time_stamp()
    def _reset():
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
    if not request_from_app: 
        _reset()
        return None
    data = request.get_json()
    if request.method == 'PUT':
        if data.get('flag') == 1:
            _reset()
            return jsonify()
    db.session.commit()
    return jsonify(data)


@app.route('/techtree', methods=["GET", "POST"])
@login_required
def techtree():
    return render_template('techtree.html')


def bayesian_recommendation(alpha=1, beta=1, num_recommendations=5):
    courses = current_user.courses
    if not courses:
        return []
    course_ids = [c.id for c in courses]
    prior = pd.Series(index=course_ids, dtype='float')
    success = pd.Series(index=course_ids, dtype='float')
    failure = pd.Series(index=course_ids, dtype='float')
    num_users = len(User.query.all())

    for course in Course.query.all():
        success[course.id] = len(course.enrolment)
        failure[course.id] = num_users - len(course.enrolment)

        prereqs = course.prerequisite if course.prerequisite is not None else '[]'
        prereq_codes = json.loads(prereqs)
        success_counts, failure_counts = 0, 0
        for prereq_code in prereq_codes:
            prereq = Course.query.filter_by(code=prereq_code).all()
            success_counts += sum([len(p.enrolment) for p in prereq])
            failure_counts += num_users - success_counts
        prior[course.id] = beta_function(success_counts + alpha, failure_counts + beta).mean()
    
    result = []
    posterior = beta_function(success + alpha, failure + beta).mean() * prior
    recommended_courses = (posterior[~posterior.index.isin(course_ids)]
                           .nlargest(num_recommendations))
    recommended_courses = recommended_courses.to_dict()
    for key, val in recommended_courses.items():
        course = Course.query.filter_by(id=key).first()
        result.append((course, round(val, 2)))
    return result


def course_recommendation(rating='like', num_recommendation=5):
    key = 'letter' if rating == 'gpa' else 'rating'
    letter_to_grade = {"A+": 4.3, "A0": 4.0, "A-": 3.7, "B+": 3.3, "B0": 3.0, "B-": 2.7,
                           "C+": 2.3, "C0": 2.0, "C-": 1.7, "D+": 1.3, "D0": 1.0, "D-": 0.7, "F": 0.0}
    user_course_info = json.loads(current_user.course_info)
    if not current_user.courses:
        return []
    escape = True
    for course_id in user_course_info:
        if key not in user_course_info[course_id]:
            continue
        if user_course_info[course_id][key] is not None:
            escape = True
            break
    if escape:
        return []
    all_courses = Course.query.all()
    all_users = User.query.all()
    utility_dict = dict()
    for user in all_users:
        course_ratings = []
        course_info = json.loads(user.course_info)
        for course in all_courses:
            try:
                score = course_info[str(course.id)][key]
                if key == 'letter':
                    score = letter_to_grade[score]
                course_ratings.append(float(score))
            except KeyError:
                course_ratings.append(0)
        utility_dict[str(user.id)] = course_ratings
    utility = pd.DataFrame.from_dict(utility_dict, orient='index')
    similarity_matrix = cosine_similarity(utility)

    user_index = utility.index.get_loc(str(current_user.id))
    sim_scores = list(enumerate(similarity_matrix[user_index]))
    sim_scores = sorted(sim_scores, key=lambda x: x[1], reverse=True)
    top_users = sim_scores[1:11]
    user_ratings = utility.iloc[[u[0] for u in top_users]].mean()
    top_rated = user_ratings.sort_values(ascending=False).to_dict()
    
    recommended_courses = []
    for course_id in top_rated:
        try:
            course = Course.query.filter_by(id=str(course_id)).first()
            if course not in current_user.courses:
                subject = course.subject_type
                if '전공' in subject or '석/박사' in subject:
                    score = round(top_rated[course_id], 2)
                    recommended_courses.append((course, score))
            if len(recommended_courses) >= num_recommendation:
                break
        except AttributeError:
            pass
    return recommended_courses

