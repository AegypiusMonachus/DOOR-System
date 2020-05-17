from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.exc import SQLAlchemyError
from werkzeug.security import generate_password_hash, check_password_hash
from App import  common
#from App.app import db
from sqlalchemy  import or_, and_ # sqlalchemy库的或和与操作
db = SQLAlchemy()

class Departments(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    department = db.Column(db.String(250),  unique=True, nullable=False)
    job = db.Column(db.String(250),  unique=True, nullable=False)
    authority_map = db.Column(db.String(250), unique=False, nullable=False)



    def __init__(self, id, department, job="未填写", authority_map="{'user_management': 0, 'dp_install_data': 0,  'dp_collect_data': 0, 'dp_data': 1, 'user_personal_information': 1, 'projects_management': 0}"):
        self.id = id
        self.department = department
        self.job = job
        self.authority_map = authority_map


    def __str__(self):
        return "Departments(id='%s')" % self.id

    def set_password(self, password):
        return generate_password_hash(password)

    def check_password(self, hash, password):
        return check_password_hash(hash, password)

    def get(self, id):
        return self.query.filter_by(id=id).first()

    def get_all(self):
        return self.query.all()

    def add(self, department):
        db.session.add(department)
        return session_commit()

    def update(self, id=0, data_dic=''):
        id = int(id)
        if id == 0:
            return session_commit()
        else:
            result = self.query.filter_by(id=id).first()
            for key in data_dic:
                setattr(result, key, data_dic[key])
            return session_commit()

    def delete(self, id):
        self.query.filter_by(id=id).delete()
        return session_commit()


class Users(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    contact_num = db.Column(db.String(250),  unique=True, nullable=False)
    username = db.Column(db.String(250),  unique=True, nullable=False)
    truename = db.Column(db.String(250), unique=False, nullable=False)
    department = db.Column(db.String(250), unique=False, nullable=False)
    department_id = db.Column(db.Integer)
    password = db.Column(db.String(250))
    usertype = db.Column(db.String(255))
    working_city = db.Column(db.String(250), unique=False, nullable=False)
    projects_index = db.Column(db.BigInteger)
    login_time = db.Column(db.Integer)
    register_time = db.Column(db.DateTime)
    install_app_version = db.Column(db.String(30))


    def __init__(self, id, username, password, contact_num, truename, department, department_id, usertype="common", working_city="", projects_index=0, install_app_version=""):
        self.id = id
        self.username = username
        self.password = password
        self.contact_num = contact_num
        self.department = department
        self.department_id = department_id
        self.usertype = usertype
        self.truename = truename
        self.working_city = working_city
        self.projects_index = projects_index
        self.register_time = common.format_ymdhms_time_now()
        self.install_app_version = install_app_version

    def __str__(self):
        return "Users(id='%s')" % self.id

    def set_password(self, password):
        return generate_password_hash(password)

    def check_password(self, hash, password):
        return check_password_hash(hash, password)

    def get(self, id):
        # return self.query.\
        #             join(Departments, Users.department_id == Departments.id, isouter=True).\
        #             filter(Users.id==id).first()
        user_info, department_info = db.session.query(Users, Departments). \
            join(Departments, Users.department_id == Departments.id, isouter=True). \
            filter(Users.id == id).first()
        return user_info, department_info

    def get_by_username(self, username):

        return db.session.query(Users, Departments). \
                    join(Departments, Users.department_id == Departments.id, isouter=True).\
                    filter(Users.username==username).first()
        # return self.query.\
        #             join(Departments, Users.department_id == Departments.id, isouter=True).\
        #             filter(Users.username==username).first()

    def get_all(self):
        return db.session.query(Users, Departments). \
                    join(Departments, Users.department_id == Departments.id, isouter=True).\
                    all()
        # return self.query. \
        #             join(Departments, Users.department_id == Departments.id, isouter=True).\
        #             all()
        # isouter=True 等于 left join了 要不然默认是inner join
        # 如果想right join，就颠倒下join的前后

    def add(self, user):
        db.session.add(user)
        return session_commit()

    def update(self, id=0, data_dic=''):
        id = int(id)
        if id == 0:
            return session_commit()
        else:
            result = self.query.filter_by(id=id).first()
            print(333333333333333333333)
            print(result.username)
            for key in data_dic:
                if key == 'password':
                    if not data_dic[key]:
                        pass
                    else:
                        setattr(result, key, self.set_password(self, data_dic[key]))
                else:
                    setattr(result, key, data_dic[key])
            db.session.add(result)
            return session_commit()

    def delete(self, id):
        self.query.filter_by(id=id).delete()
        return session_commit()


def session_commit():
    try:
        db.session.commit()
    except SQLAlchemyError as e:
        db.session.rollback()
        reason = str(e)
        return reason