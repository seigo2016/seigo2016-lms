from sqlalchemy.orm import Session
from . import models
from . import schemas

# ユーザー
def get_user(db: Session, user_id: int):
    return db.query(models.User).filter(models.User.id == user_id).first()

def get_user_by_username(db: Session, username: str):
    return db.query(models.User).filter(models.User.username == username).first()

def get_users(db: Session):
    return db.query(models.User).all()

def create_user(db: Session, user: schemas.User):
    db_user = models.User(**user.dict())
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

def update_user(db: Session, user: schemas.User):
    db_user = db.query(models.User).filter(models.User.id == user.id).first()
    if db_user:
        db_user.username = user.username
        db_user.mail_address = user.mail_address
        db_user.memo = user.memo if user.memo != None else db_user.memo
    
    db.commit()
    db.refresh(db_user)
    return db_user

def update_user_password(db: Session, user:schemas.User, new_password: str):
    db_user = db.query(models.User).filter(models.User.id == user.id).first()
    if db_user:
        db_user.password = new_password

    db.commit()    
    db.refresh(db_user)
    return db_user

# テキスト
def get_text(db: Session, text_id: int):
    return db.query(models.Text).filter(models.Text.id == text_id).first()

def get_texts(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.Text).offset(skip).limit(limit).all()

def get_texts_by_course_id(db: Session, course_id: int):
    return db.query(models.Text).filter(models.Text.course_id == course_id).order_by(models.Text.order_id).all()

def create_text(db: Session, text_info: schemas.Text):
    text = models.Text()
    text.name = text_info.name
    text.description = text_info.description
    text.course_id = text_info.course_id
    text.contents = text_info.contents
    text.order_id = text_info.order_id
    db.add(text)
    db.commit()
    db.refresh(text)
    return text.id

def update_text(db: Session, text: schemas.Text):
    db_text = db.query(models.Text).filter(models.Text.id == text.id).first()
    if db_text:
        db_text.name = text.name if text.name != None else db_text.name
        db_text.contents = text.contents if text.contents != None else db_text.contents
        db_text.description = text.description if text.description != None else db_text.description
        db_text.order_id = text.order_id if text.order_id != None else db_text.order_id
        db_text.memo = text.memo if text.memo != None else db_text.memo
    db.commit()
    db.refresh(db_text)
    return db_text

def delete_text(db: Session, text_id: int):
    db_text = db.query(models.Text).filter(models.Text.id == text_id).first()
    if db_text:
        db.delete(db_text)
    db.commit()

# コース
def get_course(db: Session, course_id: int):
    return db.query(models.Course).filter(models.Course.id == course_id).first()

def get_courses(db: Session):
    return db.query(models.Course).all()

def create_course(db: Session, course_info: schemas.Course):
    course = models.Course()
    course.name = course_info.name
    course.description = course_info.description
    db.add(course)
    return db.commit()

def update_course(db: Session, course: schemas.Course):
    db_course = db.query(models.Course).filter(models.Course.id == course.id).first()
    if db_course:
        db_course.name = course.name
        db_course.memo = course.memo
        db_course.description = course.description
    db.commit()
    db.refresh(db_course)
    return db_course

def delete_course(db: Session, course_id: int):
    db_course = db.query(models.Course).filter(models.Course.id == course_id).first()
    if db_course:
        db.delete(db_course)
    db.commit()
    return db_course

# ユーザーとコースの紐づけ
def create_users_courses(db: Session, users_courses: schemas.UsersCourses):
    db_users_courses = models.UsersCourses(**users_courses.dict())
    db.add(db_users_courses)
    db.commit()
    db.refresh(db_users_courses)
    return db_users_courses

def delete_users_courses(db: Session, users_courses: schemas.UsersCourses):
    db_user_course = db.query(models.UsersCourses).filter(models.UsersCourses.user_id == users_courses.user_id, models.UsersCourses.course_id == users_courses.course_id).first()
    if db_user_course:
        db.delete(db_user_course)
    db.commit()
    return db_user_course

# ユーザーとコースの紐づけの更新
def update_user_courses(db: Session, user_id: int, course_id:int):
    db_user_course = db.query(models.UsersCourses).filter(models.UsersCourses.user_id == user_id, models.UsersCourses.course_id == course_id).first()
    if db_user_course:
        db_user_course.user_id = user_id
        db_user_course.course_id = course_id
    else:
        models.UsersCourses(user_id=user_id, course_id=course_id)
        db_user_course = create_users_courses(db, schemas.UsersCourses(user_id=user_id, course_id=course_id))
        db.add(db_user_course)
    db.commit()
    db.refresh(db_user_course)
    return db_user_course

# ユーザーに割り当てられているコース
def get_users_courses_by_user_id(db: Session, user_id: int):
    return db.query(models.UsersCourses).filter(models.UsersCourses.user_id == user_id).all()

def get_users_courses_by_course_id(db: Session, course_id: int):
    return db.query(models.UsersCourses).filter(models.UsersCourses.course_id == course_id).all()

def check_user_courses(db: Session, user_id: int, course_id: int):
    return db.query(models.UsersCourses).filter(models.UsersCourses.user_id == user_id, models.UsersCourses.course_id== course_id).first()

def add_user_text(db: Session, user_id, text_id):
    db_user_text = models.UsersTexts(user_id = user_id, text_id=text_id)
    db.add(db_user_text)
    db.commit()
    db.refresh(db_user_text)
    return db_user_text

# ユーザーのテキスト完了フラグ更新
def update_user_text_complete_state(db: Session, user_id: int, text_id: int):
    db_user_text = db.query(models.UsersTexts).filter(models.UsersTexts.user_id == user_id, models.UsersTexts.text_id == text_id).first()
    if db_user_text:
        db_user_text.is_completed = not db_user_text.is_completed
        db.commit()
        db.refresh(db_user_text)
    return db_user_text

def get_user_text_complete_state(db: Session, user_id: int, text_id: int):
    db_user_text = db.query(models.UsersTexts).filter(models.UsersTexts.user_id == user_id, models.UsersTexts.text_id == text_id).first()
    if db_user_text:
        return db_user_text.is_completed

    return None
