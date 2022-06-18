import crud
import schemas
from database import DBContext
from flask import request, render_template, redirect, abort
from flask_login import login_user, logout_user, login_required, current_user
import os
from passlib.apps import custom_app_context as pwd_context
from flask.views import MethodView
from app import login_manager

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
    
def superuser_only(block=True):
    if current_user.is_superuser:
        return True
    elif block:
        return abort(403)
    else:
        return False


@login_manager.user_loader
def get_user(user_id: str):
    user = None
    with DBContext() as db:
        user = crud.get_user(db, user_id)
    return user

class LoginView(MethodView):
    def get(self):
        if request.method == "GET":
            return render_template("login.html")
            
    def post(self):
        username = request.form["username"]
        password = request.form["password"]
        user = None
        with DBContext() as db:
            user = crud.get_user_by_username(username=username, db=db)
        if not user:
            return render_template("login.html", message="Invalid username or password")
        is_valid =  pwd_context.verify(password, user.password)
        if not is_valid:
            return render_template("login.html", message="Invalid username or password")
        login_user(user, remember=True)

        return redirect("/")


class CoursesView(MethodView):
    @login_required
    def get(self):
        courses = []    
        if superuser_only(block=False):
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

@login_required
class CourseTopView(MethodView):
    def get(self, course_id):
        texts = []
        course=None
        superuser_only(block=True)
        with DBContext() as db:
            course = crud.get_course(db, course_id=course_id)
            texts = crud.get_texts_by_course_id(db, course.id)
        if course == None or texts == None:
            return abort(404)
        return render_template(
            "course_top.html",
            texts=texts,
            user = current_user,
            course = course
        )
    def post(self, course_id):
        if request.form.get('_method') == "DELETE":
            with DBContext() as db:
                crud.delete_course(db, course_id)
        return redirect("/courses")

@login_required
class ManageCourseView(MethodView):
    def get(self, course_id, param):
        superuser_only(block=True)
        with DBContext() as db:
            course = crud.get_course(db, course_id=course_id)
        if course == None:
            return abort(404)
        if param == "create":
            return render_template(
                "create_text.html",
                user = current_user,
                course=course,
                type="create"
            )
        elif param == "edit":
            return render_template(
                "create_course.html",
                user = current_user,
                course=course,
                type="edit"
            )
        return abort(400)

    def post(self, course_id, param):
        superuser_only(block=True)
        if param == "create":
            text_name = request.form["name"]
            description = request.form["description"]
            contents = request.form["contents"]
            order_id = request.form["order_id"] if request.form["order_id"] else "0"
            with DBContext() as db:
                course = crud.get_course(db, course_id=course_id)
            if course == None:
                return abort(404)
            text = schemas.Text(name=text_name, description=description, contents=contents, course_id=course.id)
            if not order_id.isdigit() or not text_name or not contents or not course_id:
                text.order_id=0
                return render_template(
                    "create_text.html",
                    user = current_user,
                    course=course,
                    text=text,
                    message="invalid order id",
                    type="craete"
                )
            order_id = int(order_id)
            text.order_id = order_id
            with DBContext() as db:
                crud.create_text(db, text)
            return redirect("/course/"+str(course_id))

        if param == "edit":
            course_name = request.form["course_name"]
            description = request.form["description"]
            with DBContext() as db:
                course_info = schemas.Course(id=course_id, name=course_name, description=description)
                crud.update_course(db, course_info)
            return redirect("/courses")
        return "Invalid URL", 400

@login_required
class CreateCourseView(MethodView):
    def get(self, param):
        superuser_only(block=True)
        if param != "create":
            return "Invalid URL", 400
        return render_template(
            "create_course.html",
            user = current_user,
            type="create"
        )

    def post(self, param):
        superuser_only(block=True)
        if param != "create":
            return "Invalid URL", 400
        course_name = request.form["course_name"]
        description = request.form["description"]
        course = schemas.Course(name=course_name, description=description)
        if not course_name:
            return render_template(
                "create_course.html",
                user = current_user,
                course=course,
                type="create",
                message="Invalid course name",
            )
        with DBContext() as db:
            course_info = schemas.Course(name=course_name, description=description)
            crud.create_course(db, course_info)
        return redirect("/courses")

@login_required
class TextView(MethodView):
    def get(self, text_id):
        if not check_user_parmission(text_id=text_id) or not superuser_only(block=False):
            return abort(403)
        with DBContext() as db:
            text = crud.get_text(db, text_id=text_id)
            course_id = text.course_id
            all_texts = crud.get_texts_by_course_id(db, course_id)
        if not text or not course_id or not all_texts:
            return "Something wrong...", 500
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

    def post(self, text_id):
        if request.form.get('_method') == "DELETE":
            course_id = 0
            with DBContext() as db:
                text = crud.get_text(db, text_id=text_id)
                course_id = text.course_id
            with DBContext() as db:
                crud.delete_text(db, text_id)
        return redirect("/course/"+str(course_id))

@login_required
class ManageTextView(MethodView):
    def get(self, text_id, param):
        if param == "edit":
            with DBContext() as db:
                text = crud.get_text(db, text_id=text_id)
            return render_template(
                "create_text.html",
                user = current_user,
                text=text,
                type="edit"
            )
        
    def post(self, text_id, param):
        if param == "edit":
            with DBContext() as db:
                text = crud.get_text(db, text_id=text_id)
            name = request.form["name"] if request.form["name"] else text.name
            description = request.form["description"] if request.form["description"] else text.description
            contents = request.form["contents"] if request.form["contents"] else text.contents
            text_info = schemas.Text(course_id=text.course_id, id=text.id, name=name, contents=contents, description=description)
            with DBContext() as db:
                crud.update_text(db, text=text_info)
            return redirect(f"/text/{text.id}")

@login_required
class TopView(MethodView):
    def get(self):
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

@login_required
class LogoutView(MethodView):
    def get(self):
        logout_user()
        return redirect("/login")

@login_required
class ProfileView(MethodView):
    def get(self):
        pass

    def post(self):
        pass


@login_manager.unauthorized_handler
def unauthorized():
    return redirect('/login')