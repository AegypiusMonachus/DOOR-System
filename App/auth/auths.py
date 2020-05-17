import jwt, datetime, time
from flask import jsonify
from App.users.model import Users
from .. import config
from .. import common
import ast

class Auth():
    @staticmethod
    def encode_auth_token(user_id, login_time):
        """
        生成认证Token
        :param user_id: int
        :param login_time: int(timestamp)
        :return: string
        """
        try:
            payload = {
                'exp': datetime.datetime.utcnow() + datetime.timedelta(days=0, seconds=10),
                'iat': datetime.datetime.utcnow(),
                'iss': 'ken',
                'data': {
                    'id': user_id,
                    'login_time': login_time
                }
            }
            return jwt.encode(
                payload,
                config.SECRET_KEY,
                algorithm='HS256'
            )
        except Exception as e:
            return e

    @staticmethod
    def decode_auth_token(auth_token):
        """
        验证Token
        :param auth_token:
        :return: integer|string
        """
        addition = ""
        try:
            # payload = jwt.decode(auth_token, app.config.get('SECRET_KEY'), leeway=datetime.timedelta(seconds=10))
            # 取消过期时间验证
            payload = jwt.decode(auth_token, config.SECRET_KEY, options={'verify_exp': False})
            if ('data' in payload and 'id' in payload['data']):
                return payload, addition
            else:
                #return 'Token过期', addition
                raise jwt.InvalidTokenError
        except jwt.ExpiredSignatureError:
            addition = common.false_Type.token_expired
            return 'Token过期', addition
        except jwt.InvalidTokenError:
            addition = common.false_Type.token_false
            return '无效Token', addition


    def authenticate(self, username, password):
        """
        用户登录，登录成功返回token，写将登录时间写入数据库；登录失败返回失败原因
        :param password:
        :return: json
        """
        userInfo = Users.query.filter_by(username=username).first()
        if (userInfo is None):
            return jsonify(common.falseReturn('', '找不到用户'))
        else:
            if (Users.check_password(Users, userInfo.password, password)):
                user, department = Users.get(Users, userInfo.id)
                try:
                    ret_authority_map = ast.literal_eval(department.authority_map)
                except:
                    ret_authority_map = {}[department.authority_map] = department.authority_map

                login_time = int(time.time())
                userInfo.login_time = login_time
                Users.update(Users)
                token = self.encode_auth_token(userInfo.id, login_time)
                data = {}
                data['token'] = token.decode()
                data['authority_map'] = ret_authority_map
                data['usertype'] = userInfo.usertype
                data['id'] = userInfo.id
                data['username'] = userInfo.username
                print(token)
                return jsonify(common.trueReturn(data, '登录成功'))
            else:
                return jsonify(common.falseReturn('', '密码不正确'))

    @classmethod
    def check_token(self, auth_token):
        payload, addition = self.decode_auth_token(auth_token)
        try:
            if 'data' not in payload.keys():
                result = common.falseReturn('', payload, addition=common.false_Type.token_changed)
            else:
                if not isinstance(payload, str):
                    user, department = Users.get(Users, payload['data']['id'])
                    if (user is None):
                        result = common.falseReturn('', '找不到该用户信息')
                    else:
                        if (user.login_time == payload['data']['login_time']):

                            # if int(time.time()) > payload['exp']: # 这个是判断过期的
                            #     result = common.falseReturn('', 'Token已过期，请重新登录')
                            #     return result
                            result = common.trueReturn({"id": user.id, "username": user.username}, '请求成功')
                            # result = common.trueReturn(str(user.id) + "过期时间" + str(payload['exp']) + "登陆时间" + str(payload['data']['login_time']) + '现在时间' + str(int(time.time())), '请求成功')
                        else:
                            result = common.falseReturn('', 'Token已更改，请重新登录获取',
                                                        addition=common.false_Type.token_changed)
                else:
                    result = common.falseReturn('', payload, addition=addition)
        except:
            result = common.falseReturn('', "token有错误！", addition=addition)


        return result

    def identify(self, request):
        """
        用户鉴权
        :return: list
        """
        auth_header = request.headers.get('Authorization')
        #print("auth_header", auth_header)
        if (auth_header):
            auth_tokenArr = auth_header.split(" ")
            if (not auth_tokenArr or auth_tokenArr[0] != 'JWT' or len(auth_tokenArr) != 2):
                result = common.falseReturn('', '请传递正确的验证头信息', addition=common.false_Type.token_false)
            else:
                auth_token = auth_tokenArr[1]
                result = self.check_token(auth_token)
                # payload, addition = self.decode_auth_token(auth_token)
                # if not isinstance(payload, str):
                #     user = Users.get(Users, payload['data']['id'])
                #     if (user is None):
                #         result = common.falseReturn('', '找不到该用户信息')
                #     else:
                #         if (user.login_time == payload['data']['login_time']):
                #
                #             # if int(time.time()) > payload['exp']: # 这个是判断过期的
                #             #     result = common.falseReturn('', 'Token已过期，请重新登录')
                #             #     return result
                #             result = common.trueReturn({"id": user.id, "username": user.username}, '请求成功')
                #             #result = common.trueReturn(str(user.id) + "过期时间" + str(payload['exp']) + "登陆时间" + str(payload['data']['login_time']) + '现在时间' + str(int(time.time())), '请求成功')
                #         else:
                #             result = common.falseReturn('', 'Token已更改，请重新登录获取', addition=common.false_Type.token_changed)
                # else:
                #     result = common.falseReturn('', payload, addition=addition)
        else:
            result = common.falseReturn('', '没有提供认证token', addition=common.false_Type.token_false)
        return result