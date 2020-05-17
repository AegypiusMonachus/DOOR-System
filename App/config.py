DB_USER = 'root'
DB_PASSWORD = '123456'
#DB_PASSWORD = '123456'
DB_HOST = 'localhost'
DB_HOST_TEST_LAN = '192.168.1.100'
#DB_HOST_TEST_WAN = 'wan_ip'
DB_DB = 'ws_doorplate'
#DB_DB = 'test'
DB_NAME = 'ws_doorplate'

#DEBUG = True
DEBUG = True
PORT = 2333
HOST = "0.0.0.0"
SECRET_KEY = "dy_111"
THREADED = True
PROCESSES = 2

JSON_AS_ASCII = False #  让jsonify返回的json串支持中文显示

SQLALCHEMY_TRACK_MODIFICATIONS = False
SQLALCHEMY_DATABASE_URI = 'mysql://' + DB_USER + ':' + DB_PASSWORD + '@' + DB_HOST + '/' + DB_DB
SQLALCHEMY_POOL_SIZE = 5000 # 数据库连接池的大小
SQLALCHEMY_MAX_OVERFLOW = 5000 # 控制在连接池达到最大值后可以创建的连接数。当这些额外的连接使用后回收到连接池后将会被断开和抛弃。保证连接池只有设置的大小
SQLALCHEMY_ENGINE_OPTIONS = {"pool_pre_ping": True} # 连接前先ping
SQLALCHEMY_POOL_RECYCLE = 60 # 60秒不用就回收

TEMP_DATAS_PATH = "/home/dy_server/temp_datas" # 临时数据存储位置
TEMP_UPLOAD_DATAS_PATH = "/home/dy_server/temp_datas/uploads" # 临时上传数据存储位置
TEMP_DOWNLOAD_DATAS_PATH = "/home/dy_server/temp_datas/downloads" # 临时下载数据存储位置
DY_DATAS_PATH = "/home/dy_datas" # 数据存储位置
DY_DATAS_PICTURES_PATH = "/home/dy_datas/gd_dp_photos" # 安装照片存储位置
DY_DATAS_COLLECTED_PICTURES_PATH = "/home/dy_datas/collection_photos" # 采集照片存储位置
DY_DATAS_LOG_PATH = "/home/dy_datas/log" # 日志存储位置
DY_DATAS_TEMPLATES_PATH = "/home/dy_datas/templates" # 模板存储位置
DY_DATAS_SCRIPTS_PATH = "/home/dy_datas/scripts" # 脚本存储位置
DY_DATAS_APKS_PATH = "/home/dy_datas/apks" # 门牌安装apk存储位置


WEB_PATH = "/home/dy_websites/dist/" # 网页路径
ROOT_WEB_PATH = "/home/dy_websites/root_web/" # 网页路径
WEB_STATIC_PATH = "/home/dy_websites/dist/static/" # 网页静态文件路径

WEB_DEMO_PATH = "/home/dy_websites/dp_quickdemo/dist/"  # DEMO网页路径
WEB_STATIC_DEMO_PATH = "/home/dy_websites/dp_quickdemo/dist/static/"  # DEMO 网页静态文件路径

DEVELOPMENT_WEB_PATH = "/home/dy_websites/development_web/" # 网页路径
DEVELOPMENT_WEB_JS_PATH = "/home/dy_websites/development_web/js/" # 网页静态文件路径
DEVELOPMENT_WEB_CSS_PATH = "/home/dy_websites/development_web/css/" # 网页静态文件路径



#RUN_LOG_PATH = "/home/dy_server/log" # 运行时的log路径

# 缓存
#CACHE_TYPE = 'simple' # 也可以用redis
CACHE_TYPE = 'filesystem' # 也可以用redis
CACHE_DIR = "/home/dy_server/temp_datas/downloads/cache"
cache_timeout = 60 * 60 * 24 # 24小时的缓存时间
long_cache_timeout = 60 * 60 * 24 # 24小时的缓存时间
#cache_timeout = 60 * 15 # 15分钟的缓存时间
#cache_timeout = 1 # 1秒的缓存时间

PICTURES_MD5_TABLE_NAME = "pictures_MD5"

LONG_TIME_CACHE_TYPE = 'simple' # 也可以用redis
