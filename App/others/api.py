'''

    version: 0.0.1
    create: 2019-11-14
    update: 2019-11-14
    author: Cong

    tips:
        gunicorn 不支持 argparse!!! 千万别在用gunicorn的时候用 argparse!!!
'''
from flask import jsonify
from App.auth.auths import Auth
import App.common as common
from flask import request
from App import config
import psutil
import time
import tempfile
from App.others import get_MD5
import os

apks_path = config.DY_DATAS_APKS_PATH

def init_api(app):
    # cache = Cache()  # 缓存 要更改使用的类型，例如redis，在config改
    # cache.init_app(app)

    # 获取服务器状态
    @app.route('/apk', methods=['GET', 'POST'])
    # @cache.cached(timeout=config.cache_timeout, key_prefix='view')
    def apk():
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

        if request.method == 'GET':
            request_type = request.args.get("type")

            name = request.args.get("name")

            apks_list = os.listdir(apks_path)
            apks_splits_list_temp = []
            for i in apks_list:
                if name:
                    if name == i.split("_")[0]:
                        apks_splits_list_temp.append([i] + i.split("_"))
                else:
                    apks_splits_list_temp.append([i] + i.split("_"))
            # apks_splits_list = [i.split("_") for i in apks_list]

            apks_splits_list = apks_splits_list_temp
            apks_splits_list.sort(reverse=True)

            if not name:
                ret_msg = ""
            else:
                ret_msg = "返回结果是服务器中name为" + name + "的"

            if request_type == "all":
                ret = []
                for i in apks_splits_list:
                    temp_map = {}
                    temp_map["upload_fath"] = os.path.join(apks_path, i[0])
                    temp_map["name"] = os.path.join(apks_path, i[1])
                    temp_map["version"] = os.path.join(apks_path, i[2])
                    temp_map["version_type"] = os.path.join(apks_path, i[3])
                    ret.append(temp_map)
                ret_msg += "所有的apks信息"
            else:
                # 默认返回最新的apks
                ret = [{"upload_fath": os.path.join(apks_path, apks_splits_list[0][0]),
                                           "name": apks_splits_list[0][1],
                                           "version": apks_splits_list[0][2],
                                           "version_type": apks_splits_list[0][3]}]
                ret_msg += "最新的apk信息"




            return common.trueReturn_json(ret,
                                          ret_msg)


        elif request.method == 'POST':
            #request_json = request.get_json()
            request_data = request.form

            name = request_data.get("name") # apk 名字
            if not name:
                app.logger.info("没有传name参数")
                return common.falseReturn_json("", "没有传name参数")
            version = request_data.get("version") # apk 版本号
            if not version:
                app.logger.info("没有传version参数")
                return common.falseReturn_json("", "没有传version参数")
            version_type = request_data.get("version_type") # apk 版本类型
            if not version_type:
                app.logger.info("没有传version_type参数")
                return common.falseReturn_json("", "没有传version_type参数")

            filename = name + "_" + version + "_" + version_type + ".apk"

            f = request.files['file']
            if not f:
                app.logger.info("没有传file参数")
                return common.falseReturn_json("", "没有传文件")
            temp_file = tempfile.TemporaryFile()
            # app.logger.info(tempfile)

            f.save(temp_file)
            temp_file.seek(0)
            upload_file_MD5 = get_MD5.GetFileMd5_from_file(temp_file)
            app.logger.info("upload_file_MD5: %s", upload_file_MD5)
            filename_pre, filename_suffix = os.path.splitext(filename)
            upload_path = os.path.join(apks_path, filename)
            need_save = 1
            sum = 0
            while (os.path.isfile(os.path.join(apks_path, filename))):  # 入参需要是绝对路径
                # temp_MD5 = get_MD5.GetFileMd5(dydatas_basepath + '/gd_dp_photos/' + city + "/" + filename)
                temp_MD5 = get_MD5.GetFileMd5(os.path.join(apks_path, filename))
                app.logger.info("temp_MD5: %s", temp_MD5)
                if upload_file_MD5 != temp_MD5:
                    sum += 1
                    filename = filename_pre + "_" + str(sum) + '.' + filename_suffix
                else:
                    need_save = 0
                    app.logger.info('本地已经有相同文件了: %s', upload_path)
                    return common.falseReturn_json({"upload_fath": upload_path}, "服务器已经有该文件，请直接用", addition=common.false_Type.exist)
                    break
            upload_path = os.path.join(apks_path, filename)
            upload_file_savename = filename

            if need_save:
                f.stream.seek(0)
                f.save(upload_path)
                app.logger.info("文件保存在：%s", upload_path)

            return common.trueReturn_json({"upload_fath": upload_path}, "成功上传")



