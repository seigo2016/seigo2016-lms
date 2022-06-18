import crud
import schemas
from database import DBContext
from flask import Flask, request, render_template, redirect
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from dotenv import load_dotenv
import os
from passlib.apps import custom_app_context as pwd_context
from flask.views import View

load_dotenv(override=True)

login_manager = LoginManager()
app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv("SECRET_KEY")
login_manager.init_app(app)

def check_user_parmission(course_id = None, text_id = None):
    with DBContext() as db:
        user_id = current_user.id
        user_courses = crud.get_users_courses_by_user_id(db, user_id)
        if current_user.is_superuser:
            return True
        if course_id:
            for user_course in user_courses:
                if user_course.course_id == course_id:
                    return True
            return False
        if text_id:
            text = crud.get_text(db, text_id)
            for user_course in user_courses:
                if user_course.course_id == text.course_id:
                    return True
            return False
    
def superuser_only():
    if current_user.is_superuser:
        return True
    return False

@login_manager.user_loader
def get_user(user_id: str):
    user = None
    with DBContext() as db:
        user = crud.get_user(db, user_id)
    return user


@app.route('/login', methods=["GET", "POST"])
def login():
    if request.method == "GET":
        return render_template(
            "login.html"
        )
    elif request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        user = None
        with DBContext() as db:
            user = crud.get_user_by_username(username=username, db=db)
        if not user:
            return "Incorrect username or password", 400
        is_valid =  pwd_context.verify(password, user.password)
        if not is_valid:
            return "Incorrect username or password", 400

        login_user(user, remember=True)
        return redirect("/")


@app.route("/courses", methods=["GET"])
@login_required
def get_courses():
    # ユーザーの持っているコースを表示
    courses = []    
    if superuser_only():
        with DBContext() as db:
            courses = crud.get_courses(db)
    else:
        with DBContext() as db:
            courses_info = crud.get_users_courses_by_user_id(db, current_user.id)
            courses = []
            for course in courses_info:
                c = crud.get_course(db, course.course_id)
                courses.append(c.__dict__)
    return render_template(
        "courses_list.html",
        courses=courses,
        user=current_user,
    )



@app.route("/course/<course_id>/<param>", methods=["GET", "POST"])
@app.route("/course/<course_id>", methods=["GET", "POST"])
@login_required
def get_course(course_id, param=None):
    if course_id and param =="create" and request.method == "GET":
        if not superuser_only():
            return "You don't have permission to access this course", 400  
        return render_template(
            "create_text.html",
            user = current_user,
            course_id=course_id
        )
    elif course_id and param =="create" and request.method == "POST":
        if not superuser_only():
            return "You don't have permission to access this course", 400
        text_name = request.form["name"]
        description = request.form["description"]
        contents = request.form["contents"]
        order_id = request.form["order_id"] if request.form["order_id"] else "0"
        if not order_id.isdigit():
            return
        order_id = int(order_id)
        with DBContext() as db:
            text_info = schemas.Text(name=text_name, description=description, course_id=course_id, contents=contents, order_id=order_id)
            crud.create_text(db, text_info)
        return redirect("/course/"+course_id)

    if course_id and param =="edit" and request.method == "GET":
        if not superuser_only():
            return "You don't have permission to access this course", 400
        course = None
        with DBContext() as db:
            course = crud.get_course(db, course_id=course_id)
        return render_template(
            "create_course.html",
            user = current_user,
            course_id=course_id,
            course=course
        )

    elif course_id and param =="edit" and request.method == "POST":
        if not superuser_only():
            return "You don't have permission to access this course", 400
        course_name = request.form["course_name"]
        description = request.form["description"]
        with DBContext() as db:
            course_info = schemas.Course(id=course_id, name=course_name, description=description)
            crud.update_course(db, course_info)
        return redirect("/courses")
        
    
    if course_id == "create" and request.method == "GET":
        if not superuser_only():
            return "You don't have permission to access this course", 400
        return render_template(
            "create_course.html",
            user = current_user,
        )
    elif course_id == "create" and request.method == "POST":
        if not superuser_only():
            return "You don't have permission to access this course", 400
        course_name = request.form["course_name"]
        description = request.form["description"]
        with DBContext() as db:
            course_info = schemas.Course(name=course_name, description=description)
            crud.create_course(db, course_info)
        return redirect("/courses")

    # コースを表示
    texts = []
    with DBContext() as db:
        if not check_user_parmission(course_id=course_id):
            return "You don't have permission to access this course", 400
        course = crud.get_course(db, course_id=course_id)
        texts = crud.get_texts_by_course_id(db, course.id)
    return render_template(
        "course_top.html",
        texts=texts,
        user = current_user,
        course_id = course_id
    )


@app.route("/text/<text_id>/<param>", methods=["GET", "POST"])
@app.route("/text/<text_id>", methods=["GET"])
@login_required
def get_text(text_id, param=None):
    if param == "edit" and request.method == "GET":
        with DBContext() as db:
            text = crud.get_text(db, text_id=text_id)
        return render_template(
            "create_text.html",
            user = current_user,
            text=text
        )

    elif param == "edit" and request.method == "POST":
        with DBContext() as db:
            text = crud.get_text(db, text_id=text_id)
        name = request.form["name"] if request.form["name"] else text.name
        description = request.form["description"] if request.form["description"] else text.description
        contents = request.form["contents"] if request.form["contents"] else text.contents
        text_info = schemas.Text(course_id=text.course_id, id=text.id, name=name, contents=contents, description=description)
        with DBContext() as db:
            crud.update_text(db, text=text_info)
        return redirect(f"/text/{text.id}")

    # テキストを表示
    if not check_user_parmission(text_id=text_id) or not superuser_only():
        return "You don't have permission to access this text", 400
    with DBContext() as db:
        text = crud.get_text(db, text_id=text_id)
        course_id = text.course_id
        all_texts = crud.get_texts_by_course_id(db, course_id)
    if not text or not course_id or not all_texts:
        return "Something Wrong", 500
    text_order_id = text.order_id
    is_current_text = False
    prev_text_id = -1
    next_text_id = -1
    for t in all_texts:
        if t.order_id == text_order_id:
            is_current_text = True
        elif is_current_text:
            next_text_id = t.id
            break
        else:
            prev_text_id = t.id
    text.contents=text.contents.replace("`", "\`")
    return render_template(
        "text_page.html",
        text=text,
        next_text_id=next_text_id,
        prev_text_id=prev_text_id,
        user = current_user,
    )

@app.route("/", methods=["GET"])
@login_required
def top():
    # ユーザーの持っているコースを表示
    courses = []
    with DBContext() as db:
        courses = crud.get_users_courses_by_user_id(db, current_user.id)
        courses_info = []
        for course in courses:
            c = crud.get_course(db, course.course_id)
            courses_info.append(c.__dict__)
    return render_template(
        "top.html",
        courses=courses_info,
        user = current_user,
    )

@app.route("/logout", methods=["GET"])
@login_required
def logout():
    logout_user()
    return redirect("/login")

@app.route("/profile", methods=["GET"])
@login_required
def show_profile():
    pass

@login_manager.unauthorized_handler
def unauthorized():
    return redirect('/login')


if __name__ == '__main__':
    app.run(debug=True)