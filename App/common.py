import datetime
from flask import jsonify

logger = "" # 程序启动后App的__init__.py中会给它赋对象

global_obj = {} # 全局对象保存字典 # 目前启动后会保存的是 app logger

#format_ymdhms_time_now = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S') # 在定义的时候时间就固定了，所以需要换种方式
'''
format_ymdhms_time_now = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
format_ymd_time_now = datetime.datetime.now().strftime('%Y-%m-%d')
format_ymd_time_now_for_filename = datetime.datetime.now().strftime('%Y%m%d')
format_ymdhms_time_now_for_filename = datetime.datetime.now().strftime('%Y%m%d%H%M%S')
'''

#format_ymdhms_time = '%Y-%m-%d %H:%M:%S'


def format_ymdhms_time_now():
    return datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
def format_ymd_time_now():
    return datetime.datetime.now().strftime('%Y-%m-%d')
def format_ymd_time_now_for_filename():
    return datetime.datetime.now().strftime('%Y%m%d')
def format_ymdhms_time_now_for_filename():
    return datetime.datetime.now().strftime('%Y%m%d%H%M%S')


class False_Type():
    # 安装
    exist = {} # 已存在

    # 导出生产单
    export_produce_false = {}  # token改变

    global_id_false = {} # global_id错误
    name_false = {}  # 名称错误

    # token相关
    token_false = {} # token错误
    token_expired = {} # token过期
    token_changed = {}  # token改变



    def __init__(self):
        self.exist = self.setType("exist")
        self.global_id_false = self.setType("global_id_false")
        self.token_false = self.setType("token_false")
        self.token_expired = self.setType("token_expired")
        self.token_changed = self.setType("token_changed")
        self.export_produce_false = self.setType("export_produce_false")
        self.name_false = self.setType("name_false")

    def setType(self, str):
        return {self.__class__.__name__: str}

class True_Type():
    def __init__(self):
        pass

    def setType(self, str):
        return {self.__class__.__name__: str}

false_Type = False_Type()
true_Type = True_Type()


# 正确的返回
def trueReturn(data, msg, addition=""):
    return {
        "status": True,
        "addition": addition,
        "data": data,
        "msg": msg
    }

# 错误的返回
def falseReturn(data, msg, addition=""):
    return {
        "status": False,
        "addition": addition,
        "data": data,
        "msg": msg
    }

# 正确的返回
def trueReturn_json(data, msg, addition=""):
    return jsonify({
        "status": True,
        "addition": addition,
        "data": data,
        "msg": msg
    })

# 错误的返回
def falseReturn_json(data, msg, addition=""):
    return jsonify({
        "status": False,
        "addition": addition,
        "data": data,
        "msg": msg
    })

