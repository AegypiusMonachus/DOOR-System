'''

    version: 0.0.1
    create: 2019-10-25
    update: 2019-10-25
    author: Cong

    tips:
        gunicorn 不支持 argparse!!! 千万别在用gunicorn的时候用 argparse!!!
'''
from flask import jsonify
from App.auth.auths import Auth
import App.common as common
from flask import request
import psutil
import time

def init_api(app):
    # cache = Cache()  # 缓存 要更改使用的类型，例如redis，在config改
    # cache.init_app(app)

    # 获取服务器状态
    @app.route('/server_status', methods=['GET'])
    # @cache.cached(timeout=config.cache_timeout, key_prefix='view')
    def server_status_get():
        app.logger.info("server_status_get")
        app.logger.info("request: %s", request)
        app.logger.info("当前访问用户：%s", request.remote_addr)
        # app.logger.info("Authorization：", request.headers['Authorization'])

        result = Auth.identify(Auth, request)
        # app.logger.info(result)
        app.logger.info("状态: %s 用户: %s ", result.get('status'), result.get('data'))
        if (result['status'] and result['data']):
            pass
        else:
            # return json.dumps(result, ensure_ascii=False)
            pass
            #return jsonify(result)

        cpu_used = str(psutil.cpu_percent()) + "%" # psutil.cpu_percent(interval=1, percpu=True)

        # memory_used = str(float('%.2f' % ((psutil.virtual_memory().total - psutil.virtual_memory().free)/(1024*1024)))) + "MB"
        # memory_free = str(float('%.2f' % (psutil.virtual_memory().free / (1024 * 1024)))) + "MB"
        # memory_total = str(float('%.2f' % (psutil.virtual_memory().total / (1024 * 1024)))) + "MB"
        #
        # disk_used = str(float('%.2f' % (psutil.disk_usage("/").used / (1024 * 1024 * 1024)))) + "GB"
        # disk_free = str(float('%.2f' % (psutil.disk_usage("/").free / (1024 * 1024 * 1024)))) + "GB"
        # disk_total = str(float('%.2f' % (psutil.disk_usage("/").total / (1024 * 1024 * 1024)))) + "GB"

        memory_used = str(float('%.2f' % (psutil.virtual_memory().total - psutil.virtual_memory().free)))
        memory_free = str(float('%.2f' % (psutil.virtual_memory().free )))
        memory_total = str(float('%.2f' % (psutil.virtual_memory().total)))

        disk_used = str(float('%.2f' % (psutil.disk_usage("/").used )))
        disk_free = str(float('%.2f' % (psutil.disk_usage("/").free)))
        disk_total = str(float('%.2f' % (psutil.disk_usage("/").total)))

        download_before = psutil.net_io_counters().bytes_recv
        time.sleep(0.1)
        download_after = psutil.net_io_counters().bytes_recv
        #download = str(float('%.2f' % ((download_after - download_before) / 0.1 / 1024))) + "KB/s"
        download = str(float('%.2f' % ((download_after - download_before) / 0.1)))

        upload_before = psutil.net_io_counters().bytes_sent
        time.sleep(0.1)
        upload_after = psutil.net_io_counters().bytes_sent
        #upload = str(float('%.2f' % ((upload_after - upload_before) / 0.1 / 1024))) + "KB/s"
        upload = str(float('%.2f' % ((upload_after - upload_before) / 0.1)))

        ret = {"CPU": {"used": cpu_used},
               "Memory": {"used": memory_used,
                          "free": memory_free,
                          "total": memory_total},
               "Disk": {"used": disk_used,
                        "free": disk_free,
                        "total": disk_total},
               "Network": {"upload": upload,
                           "download": download,
                           "max_upload": str(20*1024*1024),
                           "max_download": str(100*1024*1024)}
               }

        return jsonify(common.trueReturn(ret, ""))


    # 获取服务器api调用动态
    @app.route('/server_api_status', methods=['GET'])
    # @cache.cached(timeout=config.cache_timeout, key_prefix='view')
    def api_status_get():
        app.logger.info("api_status_get")
        app.logger.info("request: %s", request)
        app.logger.info("当前访问用户：%s", request.remote_addr)
        # app.logger.info("Authorization：", request.headers['Authorization'])

        result = Auth.identify(Auth, request)
        # app.logger.info(result)
        app.logger.info("状态: %s 用户: %s ", result.get('status'), result.get('data'))
        if (result['status'] and result['data']):
            pass
        else:
            # return json.dumps(result, ensure_ascii=False)
            pass
            #return jsonify(result)

        '''
        [{
        "time": "",
        "person": "xxx",
        "api": [],
        }]
        '''

        ret = {"CPU": {"used": cpu_used},
               "Memory": {"used": memory_used,
                          "free": memory_free,
                          "total": memory_total},
               "Disk": {"used": disk_used,
                        "free": disk_free,
                        "total": disk_total},
               "Network": {"upload": upload,
                           "download": download,
                           "max_upload": "10000KB/s",
                           "max_download": "50000KB/s"}
               }

        return jsonify(common.trueReturn(ret, ""))
