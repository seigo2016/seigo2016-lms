from sqlalchemy.orm import Session
import models
import schemas

# ユーザー
def get_user(db: Session, user_id: int):
    return db.query(models.User).filter(models.User.id == user_id).first()

def get_user_by_username(db: Session, username: str):
    return db.query(models.User).filter(models.User.username == username).first()

def get_users(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.User).offset(skip).limit(limit).all()

def create_user(db: Session, user: schemas.User):
    db_user = models.User(**user.dict())
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

def update_user(db: Session, user_id: int, user: schemas.User):
    db_user = db.query(models.User).filter(models.User.id == user_id).first()
    if db_user:
        db_user.username = user.username
        db_user.mail_address = user.mail_address
        db_user.password = user.password
        db_user.memo = user.memo
        db_user.is_active = user.is_active
        db_user.is_superuser = user.is_superuser
    
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
    print(text.order_id, type(text.order_id))
    db.add(text)
    return db.commit()

def update_text(db: Session, text: schemas.Text):
    db_text = db.query(models.Text).filter(models.Text.id == text.id).first()
    if db_text:
        db_text.name = text.name
        db_text.contents = text.contents
        db_text.memo = text.memo
        db_text.description = text.description
        db_text.order_id = text.order_id
    db.commit()
    db.refresh(db_text)
    return db_text


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

# ユーザーとコースの紐づけ
def create_users_courses(db: Session, users_courses: schemas.UsersCourses):
    db_users_courses = models.UsersCourses(**users_courses.dict())
    db.add(db_users_courses)
    db.commit()
    db.refresh(db_users_courses)
    return db_users_courses

# ユーザーとコースの紐づけの更新
def update_users_courses(db: Session, users_courses_id: int, users_courses: schemas.UsersCourses):
    db_users_courses = db.query(models.UsersCourses).filter(models.UsersCourses.id == users_courses_id).first()
    if db_users_courses:
        db_users_courses.user_id = users_courses.user_id
        db_users_courses.course_id = users_courses.course_id
    
    db.commit()
    db.refresh(db_users_courses)
    return db_users_courses

# ユーザーに割り当てられているコース
def get_users_courses_by_user_id(db: Session, user_id: int):
    return db.query(models.UsersCourses).filter(models.UsersCourses.user_id == user_id).all()

def check_user_courses(db: Session, user_id: int, course_id: int):
    return db.query(models.UsersCourses).filter(models.UsersCourses.user_id == user_id, models.UsersCourses.course_id== course_id).first()