#导入数据库模块
import pymysql
#导入Flask框架，这个框架可以快捷地实现了一个WSGI应用
from flask import Flask
from flask_cors import CORS
from flask import Response
import os
from werkzeug.utils import secure_filename
#from App.datas import excel as ExcelModel
#from App.datas import query
import datetime
import App.config
from datetime import timedelta
from flask_cache import Cache
from App.common import global_obj

cache = Cache()  # 缓存 要更改使用的类型，例如redis，在config改
app = Flask(__name__, static_url_path=config.WEB_STATIC_PATH)

logger = app.logger
global_obj["app"] = app
global_obj["logger"] = logger

long_time_cache = Cache(app, config={"CACHE_TYPE": config.LONG_TIME_CACHE_TYPE})  # 长期缓存

#传递根目录
def create_app(config_filename):

    global app, cache
    app.config.from_object(config_filename)
    app.config['SEND_FILE_MAX_AGE_DEFAULT'] = timedelta(seconds=1) # 将缓存时间设置为1秒
    #app.config = App.config

    # @app.after_request
    # def after_request(response):
    #     response.headers.add('Access-Control-Allow-Origin', '*')
    #     if request.method == 'OPTIONS':
    #         response.headers['Access-Control-Allow-Methods'] = 'DELETE, GET, POST, PUT'
    #         headers = request.headers.get('Access-Control-Request-Headers')
    #         if headers:
    #             response.headers['Access-Control-Allow-Headers'] = headers
    #     return response

    from App.users.model import db
    db.init_app(app)
    import App.users.api as users_api
    users_api.init_api(app)
    import App.datas.api as datas_api
    datas_api.init_api(app)
    import App.projects.api as projects_api
    projects_api.init_api(app)
    import App.datas.api_test as test_api
    test_api.init_api(app)
    import App.web.api as web_api
    web_api.init_api(app)
    import App.server.api as server_api
    server_api.init_api(app)
    import App.others.api as others_api
    others_api.init_api(app)

    cache.init_app(app)


    CORS(app, supports_credentials=True)  # 支持跨域访问
    return app

