from db import crud
from db import schemas
from db.database import DBContext
from flask import request, render_template, redirect, abort
from flask_login import login_user, logout_user, login_required, current_user
from passlib.apps import custom_app_context as pwd_context
from flask.views import MethodView
from app import login_manager
from typing import List

def get_diff_courses(user_id: int, new_user_courses_ids:List[int]):
    current_user_courses_ids = []
    with DBContext() as db:
        user_courses = crud.get_users_courses_by_user_id(db, user_id)
        for user_course in user_courses:
            current_user_courses_ids.append(user_course.course_id)
        add_courses = list(set(new_user_courses_ids) - set(current_user_courses_ids))
        del_courses = list(set(current_user_courses_ids) - set(new_user_courses_ids))

    return add_courses, del_courses

def check_user_parmission(course_id:int = None, text_id:int = None):
    if current_user.is_superuser:
        return True
    with DBContext() as db:
        user_id = current_user.id
        user_courses = crud.get_users_courses_by_user_id(db, user_id)
        if course_id:
            for user_course in user_courses:
                if user_course.course_id == course_id:
                    return True
            return abort(403)
        if text_id:
            text = crud.get_text(db, text_id)
            for user_course in user_courses:
                if user_course.course_id == text.course_id:
                    return True
            return abort(403)

def superuser_only(block: bool = True):
    if current_user.is_superuser:
        return True
    elif block:
        return abort(403)
    else:
        return False


@login_manager.user_loader
def get_user(user_id: str):
    with DBContext() as db:
        user = crud.get_user(db, int(user_id))
    return user

class LoginView(MethodView):
    def get(self):
        return render_template("login.html", title="ログイン")

    def post(self):
        username = request.form["username"]
        password = request.form["password"]
        with DBContext() as db:
            user = crud.get_user_by_username(username=username, db=db)
        if not user:
            return render_template("login.html", message="Invalid username or password", username=username, title="ログイン")
        is_valid =  pwd_context.verify(password, user.password)
        if not is_valid:
            return render_template("login.html", message="Invalid username or password", username=username, title="ログイン")
        login_user(user, remember=True)
        return redirect("/")

class LogoutView(MethodView):
    @login_required
    def get(self):
        logout_user()
        return redirect("/login")

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
            "course/courses_list.html",
            courses=courses,
            current_user=current_user,
            title="コース一覧"
        )

class CourseTopView(MethodView):
    @login_required
    def get(self, course_id:int):
        superuser_only(block=False)
        check_user_parmission(course_id=course_id)
        with DBContext() as db:
            course = crud.get_course(db, course_id=course_id)
            texts = crud.get_texts_by_course_id(db, course.id)
        if not(course or texts):
            return abort(404)
        return render_template(
            "course/course_top.html",
            texts=texts,
            current_user = current_user,
            course = course,
            title=f"TOP | {course.name}"
        )

    @login_required
    def post(self, course_id:int):
        if request.form.get('_method') == "DELETE":
            with DBContext() as db:
                crud.delete_course(db, course_id)
        return redirect("/courses")

class ManageCourseView(MethodView):
    @login_required
    def get(self, course_id:int, param:str):
        superuser_only(block=True)
        with DBContext() as db:
            course = crud.get_course(db, course_id=course_id)
        if course == None:
            return abort(404)
        if param == "create":
            return render_template(
                "text/create_text.html",
                course = course,
                type="create",
                title="テキスト作成"
            )
        elif param == "edit":
            return render_template(
                "course/create_course.html",
                course = course,
                type = "edit",
                title="テキスト編集"
            )
        return abort(400)

    @login_required
    def post(self, course_id:int, param:str):
        print(param)
        superuser_only(block=True)
        if param == "create":
            text_name = request.form["text-name"]
            description = request.form["description"]
            contents = request.form["contents"]
            order_id = request.form["order-id"] if request.form["order-id"] else "0"
            with DBContext() as db:
                course = crud.get_course(db, course_id=course_id)
            if course == None:
                return abort(404)
            text = schemas.Text(name=text_name, description=description, contents=contents, course_id=course.id)
            if not order_id.isdigit() or not text_name or not contents or not course_id:
                text.order_id=0
                return render_template(
                    "text/create_text.html",
                    course = course,
                    text = text,
                    message = "invalid order id",
                    type = "craete",
                    title="テキスト作成"
                )
            order_id = int(order_id)
            text.order_id = order_id
            with DBContext() as db:
                crud.create_text(db, text)
            return redirect("/course/"+str(course_id))

        if param == "edit":
            course_name = request.form["course-name"]
            description = request.form["description"]
            with DBContext() as db:
                course_info = schemas.Course(id=course_id, name=course_name, description=description)
                crud.update_course(db, course_info)
            return redirect("/courses")

        return abort(400)

class CreateCourseView(MethodView):
    @login_required
    def get(self, param:str):
        superuser_only(block=True)
        if param != "create":
            return abort(400)
        return render_template(
            "course/create_course.html",
            type = "create",
            title="コース作成"
        )

    @login_required
    def post(self, param:str):
        print("CreateCourseView")
        superuser_only(block=True)
        if param != "create":
            return abort(400)
        course_name = request.form["course-name"]
        description = request.form["description"]
        course = schemas.Course(name=course_name, description=description)
        if not course_name:
            return render_template(
                "course/create_course.html",
                course = course,
                type = "create",
                message = "Invalid course name",
                title="コース作成"
            )
        with DBContext() as db:
            course_info = schemas.Course(name=course_name, description=description)
            crud.create_course(db, course_info)
        return redirect("/courses")

class TextView(MethodView):
    @login_required
    def get(self, text_id:int):
        check_user_parmission(text_id=text_id)
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
            "text/text_page.html",
            text=text,
            next_text_id=next_text_id,
            prev_text_id=prev_text_id,
            current_user = current_user,
            title=f"{text.name}"
        )

    @login_required
    def post(self, text_id:int):
        if request.form.get('_method') == "DELETE":
            course_id = 0
            with DBContext() as db:
                text = crud.get_text(db, text_id=text_id)
                course_id = text.course_id
            with DBContext() as db:
                crud.delete_text(db, text_id)
        return redirect("/course/"+str(course_id))

class ManageTextView(MethodView):
    @login_required
    def get(self, text_id:int, param:str):
        if param == "edit":
            with DBContext() as db:
                text = crud.get_text(db, text_id=text_id)
            return render_template(
                "text/create_text.html",
                text=text,
                type="edit",
                title=f"テキスト編集"
            )
        
    @login_required
    def post(self, text_id:int, param:str):
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

class TopView(MethodView):
    @login_required
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
            current_user = current_user,
            title="トップ"
        )

class UsersView(MethodView):
    @login_required
    def get(self, param:str=None):
        superuser_only()
        if param == "create":
            courses = []
            with DBContext() as db:
                courses = crud.get_courses(db)
            return render_template(
                "user/create_user.html",
                courses = courses,
                type="create",
                title= "ユーザー作成",
            )
        elif not param:
            with DBContext() as db:
                users = crud.get_users(db)
            return render_template(
                "user/users.html",
                users = users,
                current_user=current_user,
                title="ユーザー一覧"
            )

    @login_required
    def post(self, param:str):
        superuser_only()
        if param == "create":
            username = request.form["username"]
            password = request.form["password"]
            hashed_password = pwd_context.hash(password)
            mail_address = request.form["mail-address"]
            courses = request.form.getlist("courses")
            user = schemas.User(username=username, password=hashed_password, mail_address=mail_address)
            if not username or not password or not mail_address:
                return render_template(
                    "user/create_user.html",
                    user = user,
                    type="create",
                    message="Invalid username, password or email",
                    title="ユーザー作成",
                )
            with DBContext() as db:
                user = crud.create_user(db, user)
                for course in courses:
                    user_course = schemas.UsersCourses(user_id=user.id, course_id=course)
                    crud.create_users_courses(db, user_course)
            return redirect("/users")

class UserTopView(MethodView):
    @login_required
    def get(self, username:str):
        superuser_only()
        with DBContext() as db:
            user = crud.get_user_by_username(db, username)
        if not user:
            return abort(404)
        courses = []
        with DBContext() as db:
            user_courses = crud.get_users_courses_by_user_id(db, user.id)
            for c in user_courses:
                courses.append(crud.get_course(db, c.course_id))
        return render_template(
            "user/user.html",
            user = user,
            courses = courses,
            current_user=current_user,
            title=f"トップ | {user.username}"
        )

class ManageUserView(MethodView):
    @login_required
    def get(self, username:str, param:str):
        superuser_only()
        courses = []
        with DBContext() as db:
            user_current_info = crud.get_user_by_username(db, username)
            courses = crud.get_courses(db)
            current_courses = crud.get_users_courses_by_user_id(db, user_current_info.id)
        current_courses_id = []
        for c in current_courses:
            current_courses_id.append(c.course_id)
        if param == "edit":
            return render_template(
                "user/create_user.html",
                type="edit",
                courses=courses,
                current_courses_id=current_courses_id,
                user=user_current_info,
                title=f"ユーザー編集 | {user_current_info.username}"
            )
        elif param == "reset":
            return render_template(
                "user/reset_password.html",
                user=user_current_info,
                title=f"パスワードリセット | {user_current_info.username}"
            )

    @login_required
    def post(self, username:str, param:str):
        superuser_only()
        if param == "edit":
            username = request.form["username"]
            mail_address = request.form["email-address"]
            with DBContext() as db:
                user_current_info = crud.get_user_by_username(db, username)
            user = schemas.User(id=user_current_info.id, username=username, mail_address=mail_address, password=user_current_info.password)
            courses = [int(c) for c in request.form.getlist("courses")]
            if not username or not mail_address:
                return render_template(
                    "user/create_user.html",
                    user = user,
                    type="edit",
                    message="Invalid username or email",
                    title=f"ユーザー編集 | {user.username}"
                )
            with DBContext() as db:
                assert isinstance(user.id, int)
                add_courses, del_courses = get_diff_courses(user_id=user.id, new_user_courses_ids=courses)
                crud.update_user(db, user)

                for course in add_courses:
                    course = schemas.UsersCourses(user_id=user.id, course_id=course)
                    crud.create_users_courses(db, course)

                for course in del_courses:
                    course = schemas.UsersCourses(user_id=user.id, course_id=course)
                    crud.delete_users_courses(db, course)

            return redirect("/user/"+username)
        elif param == "reset":
            new_password = request.form["new-password"]
            with DBContext() as db:
                user = crud.get_user_by_username(db=db, username=username)
                hashed_new_password = pwd_context.hash(new_password)
                crud.update_user_password(db, user, hashed_new_password)
            return redirect("/user/"+username)
        # TODO delete or deactivate user


class ProfileView(MethodView):
    @login_required
    def get(self, param:str=None):
        with DBContext() as db:
            user = crud.get_user_by_username(db, current_user.username)
        if not user:
            return abort(404)
        courses = []
        with DBContext() as db:
            user_courses = crud.get_users_courses_by_user_id(db, user.id)
            for c in user_courses:
                courses.append(crud.get_course(db, c.course_id))
        if param == "edit":
            return render_template(
                "user/edit_profile.html",
                user = user,
                courses = courses,
                current_user=current_user,
                title=f"プロフィール編集 | {user.username}",
            )
        return render_template(
            "user/profile.html",
            user = user,
            courses = courses,
            current_user=current_user,
            title=f"プロフィール | {user.username}",
        )
    
    @login_required
    def post(self, param:str):
        if param == "edit":
            old_password = request.form["old-password"]
            new_password = request.form["new-password"]
            with DBContext() as db:
                user = crud.get_user_by_username(username=current_user.username, db=db)
            is_valid =  pwd_context.verify(old_password, user.password)
            if not is_valid:
                courses = []
                with DBContext() as db:
                    user_courses = crud.get_users_courses_by_user_id(db, user.id)
                for c in user_courses:
                    courses.append(crud.get_course(db, c.course_id))
                return render_template(
                    "user/edit_profile.html",
                    user = user,
                    courses = courses,
                    current_user=current_user,
                    title=f"プロフィール編集 | {user.username}",
                )
            hashed_new_password = pwd_context.hash(new_password)
            with DBContext() as db:
                crud.update_user_password(db, user, hashed_new_password)

            return redirect("/profile")
                
            


@login_manager.unauthorized_handler
def unauthorized():
    return redirect('/login')
