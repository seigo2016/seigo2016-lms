from flask import Flask
from flask_login import LoginManager
from dotenv import load_dotenv
import os

load_dotenv(override=True)

login_manager = LoginManager()
app = Flask(__name__, static_folder='web/static', template_folder='web/templates')
app.config['SECRET_KEY'] = os.getenv("SECRET_KEY")
login_manager.init_app(app)

from web.error_handling import *

app.register_error_handler(400, handle_bad_request)
app.register_error_handler(403, handle_unauthorized_request)

from web.route import *
app.add_url_rule('/login', view_func=LoginView.as_view('loginView'), methods=["GET", "POST"])
app.add_url_rule('/logout', view_func=LogoutView.as_view('logoutView'), methods=["GET"])
app.add_url_rule('/profile/<string:param>', view_func=ProfileView.as_view('profileManageView'), methods=["GET", "POST"])
app.add_url_rule('/profile', view_func=ProfileView.as_view('profileView'), methods=["GET", "POST"])
app.add_url_rule('/courses', view_func=CoursesView.as_view('coursesView'), methods=["GET"])
app.add_url_rule('/', view_func=TopView.as_view('topView'), methods=["GET"])
app.add_url_rule('/course/<int:course_id>', view_func=CourseTopView.as_view('courseTopView'), methods=["GET", "POST"])
app.add_url_rule('/course/<int:course_id>/<string:param>', view_func=ManageCourseView.as_view('manageCourseView'), methods=["GET", "POST"])
app.add_url_rule('/course/<string:param>', view_func=CreateCourseView.as_view('CreateCourseView'), methods=["GET", "POST"])
app.add_url_rule('/text/<string:text_id>/<param>', view_func=ManageTextView.as_view('ManageTextView'), methods=["GET", "POST"])
app.add_url_rule('/text/<int:text_id>', view_func=TextView.as_view('TextView'), methods=["GET", "POST"])
app.add_url_rule('/users', view_func=UsersView.as_view("AllUsersView"), methods=["GET"])
app.add_url_rule('/users/<string:param>', view_func=UsersView.as_view("UsersView"), methods=["GET", "POST"])
app.add_url_rule('/user/<string:username>', view_func=UserTopView.as_view("UserTopView"), methods=["GET"])
app.add_url_rule('/user/<string:username>/<string:param>', view_func=ManageUserView.as_view("ManageUserView"), methods=["GET", "POST"])
print("Start")