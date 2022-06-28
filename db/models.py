
from sqlalchemy import Boolean, Column, ForeignKey, Integer, String

from .database import Base
from flask_login import UserMixin

class User(Base, UserMixin):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    username = Column(String, unique=True)
    mail_address = Column(String)
    password = Column(String)
    memo = Column(String)
    is_active = Column(Boolean, default=True)
    is_superuser = Column(Boolean, default=False)
    

class Text(Base):
    __tablename__ = "texts"
    id = Column(Integer, primary_key=True)
    name = Column(String)
    contents = Column(String)
    memo = Column(String)
    description = Column(String)
    course_id = Column(Integer, ForeignKey("courses.id"))
    order_id = Column(Integer)

class Course(Base):
    __tablename__ = "courses"
    id = Column(Integer, primary_key=True)
    name = Column(String)
    memo = Column(String)
    description = Column(String)

class UsersCourses(Base):
    __tablename__ = "users_courses"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    course_id = Column(Integer, ForeignKey("courses.id"))

class UsersTexts(Base):
    __tablename__ = "users_texts"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    text_id = Column(Integer, ForeignKey("texts.id"))

