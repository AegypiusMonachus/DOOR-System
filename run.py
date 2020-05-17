from App import create_app
import App.config as config
import logging
import logging.handlers
import os
from App import app

def create_dirs():
    if not os.path.isdir(config.DY_DATAS_LOG_PATH):
        os.makedirs(config.DY_DATAS_LOG_PATH)


def new_app():
    # 创建环境目录
    create_dirs()
    # 设置日志的记录等级
    logging.basicConfig(level=logging.DEBUG, datefmt="%Y-b%-d %H:%M:%S")  # 调试debug级
    # logging.basicConfig()from flask_cache import make_template_fragment_key

    # 创建日志记录器，指明日志保存的路径、每个日志文件的最大大小、保存的日志文件个数上限
    # file_log_handler = logging.handlers.RotatingFileHandler(config.DY_DATAS_LOG_PATH, maxBytes=1024 * 1024 * 100, backupCount=100)
    # 每天一次日志
    file_log_handler = logging.handlers.TimedRotatingFileHandler(os.path.join(config.DY_DATAS_LOG_PATH, "running_log"), 'D',
                                                                 1, 0)
    file_log_handler.suffix = "%Y%m%d-%H%M%S.log"
    # 创建日志记录的格式 日志等级 输入日志信息的文件名 行数 日志信息
    formatter = logging.Formatter('%(asctime)s %(levelname)s %(filename)s:%(lineno)d %(message)s')
    # 为刚创建的日志记录器设置日志记录格式
    file_log_handler.setFormatter(formatter)
    # 为全局的日志工具对象（flask app使用的）添加日志记录器
    logging.getLogger().addHandler(file_log_handler)


    app = create_app('App.config')


    return app


if __name__ == '__main__':

    app = new_app()

    app.run(debug=config.DEBUG, host=config.HOST, port=config.PORT, threaded=config.THREADED)

