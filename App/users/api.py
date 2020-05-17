from flask import jsonify, request
from App.users.model import Users, Departments
from App.auth.auths import Auth
from .. import common
import datetime
from sqlalchemy  import or_, and_
import json
import ast



def init_api(app):
    @app.route('/register', methods=['POST'])
    def register():
        """
        用户注册
        :return: json
        """
        print(request.get_json())
        #print(json.loads(request.get_json()))
        #print(type(request.get_json()))
        #print(request.form.to_dict())
        #request_form = request.form.to_dict()
        request_form = request.get_json()
        contact_num = request_form.get('contact_num') if request_form.get('contact_num') else '未填写'
        username = request_form.get('username')
        #truename = request_form.get('truename')
        truename = request_form.get('truename') if request_form.get('truename') else '未填写'
        password = request_form.get('password')
        department = request_form.get('department') if request_form.get('department') else '未填写'
        department_id = request_form.get('department_id') if request_form.get('department_id') else 0
        usertype = request_form.get('usertype') if request_form.get('usertype') else 'common'
        working_city = request_form.get('working_city') if request_form.get('working_city') else '未填写'
        projects_index = request_form.get('projects_index') if request_form.get('projects_index') else 0

        #print(request.form)

        isExist = Users.query.filter(Users.username == username).count()
        if isExist > 0:
            return jsonify(common.falseReturn('', '用户注册失败, 已经有该登陆名', addition=common.false_Type.exist))

        isExist = Users.query.filter(Users.truename == truename).count()
        if isExist > 0:
            return jsonify(common.falseReturn('', '用户注册失败, 已经同名用户，推荐真实姓名后加数字进行标示', addition=common.false_Type.exist))


        # 最后一条记录及其ID
        #lastUserRecord = Users.query.order_by('id').first()
        #lastUserRecord = Users.query.order_by(-Users.id).limit(1)
        lastUserRecord = Users.query.order_by(-Users.id).first()
        #print(lastUserRecord)
        if (lastUserRecord is None):
            newRecordId = 1
        else:
            newRecordId = lastUserRecord.id + 1

        user = Users(id=newRecordId,
                     contact_num=contact_num,
                     username=username,
                     password=Users.set_password(Users, password),
                     truename=truename,
                     department=department,
                     department_id=department_id,
                     usertype=usertype,
                     working_city=working_city,
                     projects_index=projects_index)
        Users.add(Users, user)
        userInfo, department = Users.get(Users, user.id)
        print(userInfo)
        if not userInfo.login_time:
            userInfo_login_time_for_ret = 0
        else:
            userInfo_login_time_for_ret = userInfo.login_time
        if userInfo:
            try:
                ret_authority_map = ast.literal_eval(department.authority_map)
            except:
                ret_authority_map = {}[department.authority_map] = department.authority_map
            returnUser = {
                'id': userInfo.id,
                'username': userInfo.username,
                'truename': userInfo.truename,
                'contact_num': userInfo.contact_num,
                'department_id': userInfo.department_id,
                'department': department.department if department else "无填写",
                'job': department.job if department else "无填写",
                'authority_map': ret_authority_map,
                'usertype': userInfo.usertype,
                'working_city': userInfo.working_city,
                'projects_index': userInfo.projects_index,
                'login_time': datetime.datetime.fromtimestamp(float(userInfo_login_time_for_ret)).strftime('%Y-%m-%d %H:%M:%S')
            }
            return jsonify(common.trueReturn(returnUser, "用户注册成功"))
        else:
            return jsonify(common.falseReturn('', '用户注册失败'))


    @app.route('/login', methods=['POST'])
    def login():
        """
        用户登录
        :return: json
        """
        request_form = request.get_json()
        username = request_form.get('username')
        password = request_form.get('password')
        if (not username or not password):
            return jsonify(common.falseReturn('', '用户名和密码不能为空'))
        else:
            return Auth.authenticate(Auth, username, password)


    @app.route('/user', methods=['GET'])
    def get():
        """
        获取用户信息
        :return: json
        """

        result = Auth.identify(Auth, request)
        if (result['status'] and result['data']):
            pass
        else:
            pass

        all = request.args.get('all')
        if int(all) == 1:
            users = Users.get_all(Users)
            returnUser = []
            for user, department in users:

                #print("typeuser.register_time", type(user.register_time))
                if not user.login_time:
                    login_time = 0
                else:
                    login_time = user.login_time

                try:
                    ret_authority_map = ast.literal_eval(department.authority_map)
                except:
                    ret_authority_map = {}[department.authority_map] = department.authority_map
                returnUser.append({
                'id': user.id,
                'username': user.username,
                'truename': user.truename,
                'contact_num': user.contact_num,
                'department_id': user.department_id,
                'department': department.department if department else "无填写",
                'job': department.job if department else "无填写",
                'authority_map': ret_authority_map,
                'usertype': user.usertype,
                'working_city': user.working_city,
                'projects_index': user.projects_index,
                'login_time': datetime.datetime.fromtimestamp(float(login_time)).strftime('%Y-%m-%d %H:%M:%S'),
                'register_time': user.register_time.strftime('%Y-%m-%d %H:%M:%S')
                })
                #print(user)

        elif int(all) == 0:
            if not result['status']:
                return jsonify(result)
            user, department = Users.get(Users, result['data']['id'])
            if not user.login_time:
                login_time = 0
            else:
                login_time = user.login_time
            try:
                ret_authority_map = ast.literal_eval(department.authority_map)
            except:
                ret_authority_map = {}[department.authority_map] = department.authority_map
            returnUser = [{
                'id': user.id,
                'username': user.username,
                'truename': user.truename,
                'contact_num': user.contact_num,
                'department_id': user.department_id,
                'department': department.department if department else "无填写",
                'job': department.job if department else "无填写",
                'authority_map': ret_authority_map,
                'usertype': user.usertype,
                'working_city': user.working_city,
                'projects_index': user.projects_index,
                'login_time': datetime.datetime.fromtimestamp(float(login_time)).strftime('%Y-%m-%d %H:%M:%S'),
                'register_time': user.register_time.strftime('%Y-%m-%d %H:%M:%S')

            }]
        elif int(all) == -1:
            user, department = Users.get_by_username(Users, request.args.get('username'))
            print(user)
            if user:
                if not user.login_time:
                    login_time = 0
                else:
                    login_time = user.login_time
                try:
                    ret_authority_map = ast.literal_eval(department.authority_map)
                except:
                    ret_authority_map = {}[department.authority_map] = department.authority_map
                returnUser = [{
                    'id': user.id,
                    'username': user.username,
                    'truename': user.truename,
                    'contact_num': user.contact_num,
                    'department_id': user.department_id,
                    'department': department.department if department else "无填写",
                    'job': department.job if department else "无填写",
                    'authority_map': ret_authority_map,
                    'usertype': user.usertype,
                    'working_city': user.working_city,
                    'projects_index': user.projects_index,
                    'login_time': datetime.datetime.fromtimestamp(float(login_time)).strftime('%Y-%m-%d %H:%M:%S'),
                    'register_time': user.register_time.strftime('%Y-%m-%d %H:%M:%S')

                }]
            else:
                result = common.falseReturn("", "找不到该用户信息", {"users_count": 0})
                return jsonify(result)
        result = common.trueReturn(returnUser, "请求成功", {"users_count": len(returnUser)})
        return jsonify(result)


    @app.route('/user', methods=['PUT'])
    def put():
        """
        修改用户信息
        :return: json
        """
        request_form = request.get_json()
        print(1111111111)
        print(request_form)
        result = Auth.identify(Auth, request)
        print(22222222222222222)
        print(result)
        if (result['status'] and result['data']):
            #user = Users.get(Users, result['data'])

            if request_form.get("username"):
                isExist = Users.query.filter(and_(Users.username == request_form.get("username"), Users.id != request_form.get("id"))).count()
                if isExist > 0:
                    return jsonify(common.falseReturn('', '用户修改信息失败, 已经有该登陆名'))
            if request_form.get("truename"):
                isExist = Users.query.filter(and_(Users.truename == request_form.get("truename"), Users.id != request_form.get("id"))).count()
                if isExist > 0:
                    return jsonify(common.falseReturn('', '用户修改信息失败, 已经同名用户，推荐真实姓名后加数字进行标示'))

            Users.update(Users, request_form['id'], request_form)
            user, department = Users.get(Users, request_form['id'])
            try:
                ret_authority_map = ast.literal_eval(department.authority_map)
            except:
                ret_authority_map = {}[department.authority_map] = department.authority_map
            returnUser = {
                'id': user.id,
                'username': user.username,
                'truename': user.truename,
                'department_id': user.department_id,
                'department': department.department if department else "无填写",
                'job': department.job if department else "无填写",
                'authority_map': ret_authority_map,
                'contact_num': user.contact_num,
                'usertype': user.usertype,
                'working_city': user.working_city,
                'projects_index': user.projects_index,
                'login_time': user.login_time
            }
            result = common.trueReturn(returnUser, "修改成功")
        return jsonify(result)

    @app.route('/user', methods=['DELETE'])
    def delete():
        """
        删除用户信息
        :return: json
        """
        request_form = request.get_json()
        result = Auth.identify(Auth, request)
        if (result['status'] and result['data']):
            # user = Users.get(Users, result['data'])
            Users.delete(Users, request_form['id'])
            result = common.trueReturn("", "删除成功")
        return jsonify(result)


    @app.route('/department', methods=['POST'])
    def department_register():
        """
        部门职位新增接口
        :return: json
        """
        print(request.get_json())
        request_form = request.get_json()
        department = request_form.get('department') if request_form.get('department') else '未填写'
        job = request_form.get('job') if request_form.get('job') else '未填写'
        authority_map = request_form.get('authority_map') if request_form.get('authority_map') else '{"dp_data": 1,"dp_install_data": 1,"user_management": 0,"user_personal_information": 1,"projects_management": 0}'
        #authority_map = json.loads(authority_map)
        #authority_map = json.str(authority_map)

        isExist = Departments.query.filter(and_(Departments.department == department, Departments.job == job)).count()
        if isExist > 0:
            return jsonify(common.falseReturn('', '职位新增失败, 已经有该职位'))

        # 最后一条记录及其ID
        # lastUserRecord = Users.query.order_by('id').first()
        # lastUserRecord = Users.query.order_by(-Users.id).limit(1)
        lastUserRecord = Departments.query.order_by(-Departments.id).first()
        # print(lastUserRecord)
        if (lastUserRecord is None):
            newRecordId = 1
        else:
            newRecordId = lastUserRecord.id + 1

        new_department = Departments(id=newRecordId,
                                     department=department,
                                     job=job,
                                     authority_map=authority_map)
        Departments.add(Departments, new_department)
        department_info = Departments.get(Departments, new_department.id)
        print(department_info)
        try:
            ret_authority_map = ast.literal_eval(department_info.authority_map)
        except:
            ret_authority_map = {}[department_info.authority_map] = department_info.authority_map
        if department_info:
            returnUser = {
                'id': department_info.id,
                'department': department_info.department,
                'job': department_info.job,
                'authority_map': ret_authority_map
            }
            return jsonify(common.trueReturn(returnUser, "职位新增成功"))
        else:
            return jsonify(common.falseReturn('', '职位新增失败'))

    @app.route('/department', methods=['GET'])
    def department_get():
        """
        获取部门职位信息
        :return: json
        """

        result = Auth.identify(Auth, request)
        if (result['status'] and result['data']):
            pass
        else:
            pass

        des_id = request.args.get('id') if request.args.get('id') else None
        if des_id:
            department = Departments.get(Departments, des_id)
            print(department)
            if department:
                try:
                    ret_authority_map = ast.literal_eval(department.authority_map)
                except:
                    ret_authority_map = {}[department.authority_map] = department.authority_map
                ret = [{
                    'id': department.id,
                    'department': department.department,
                    'job': department.job,
                    'authority_map': ret_authority_map

                }]
            else:
                result = common.falseReturn("", "找不到该部门职位信息", {"departments_count": 0})
                return jsonify(result)
        else:
            departments = Departments.get_all(Departments)
            ret = []
            for department in departments:
                try:
                    ret_authority_map = ast.literal_eval(department.authority_map)
                except:
                    ret_authority_map = {}[department.authority_map] = department.authority_map
                ret.append({
                    'id': department.id,
                    'department': department.department,
                    'job': department.job,
                    'authority_map': ret_authority_map
                })

        # elif int(all) == -1:
        #     department = Departments.get_by_departmentname(Departments, request.args.get('department'))
        #     print(department)
        #     if department:
        #         ret = [{
        #             'id': department.id,
        #             'department': department.department,
        #             'job': department.job,
        #             'authority_map': department.authority_map
        #
        #         }]
        #     else:
        #         result = common.falseReturn("", "找不到该部门职位信息", {"departments_count": 0})
        #         return jsonify(result)
        result = common.trueReturn(ret, "请求成功", {"departments_count": len(ret)})
        return jsonify(result)

    @app.route('/department', methods=['PUT'])
    def department_put():
        """
        修改部门职位信息
        :return: json
        """
        request_form = request.get_json()
        result = Auth.identify(Auth, request)
        if (result['status'] and result['data']):
            # user = Users.get(Users, result['data'])
            Departments.update(Departments, request_form['id'], request_form)
            department = Departments.get(Departments, request_form['id'])
            try:
                ret_authority_map = ast.literal_eval(department.authority_map)
            except:
                ret_authority_map = {}[department.authority_map] = department.authority_map
            ret = {
                'id': department.id,
                'department': department.department,
                'job': department.job,
                'authority_map': ret_authority_map

            }
            result = common.trueReturn(ret, "修改成功")

        return jsonify(result)

    @app.route('/department', methods=['DELETE'])
    def department_delete():
        """
        删除部门职位信息
        :return: json
        """
        request_form = request.get_json()
        result = Auth.identify(Auth, request)
        if (result['status'] and result['data']):
            # user = Users.get(Users, result['data'])
            Departments.delete(Departments, request_form['id'])
            result = common.trueReturn("", "删除成功")
        return jsonify(result)
