'''

    version: 0.2.1
    update: 2019-05-08
    author: Cong

'''
from flask import jsonify
from App.auth.auths import Auth
from .. import common
import pymysql
import traceback
from flask import request
import os
import tempfile
from werkzeug.utils import secure_filename
from App.datas import dp_sort
from App.others import get_MD5
import datetime
import App.config as config
import enum
import time


# 全局变量
datas = [] # 当前页面显示的数据
data_col_name = [] # 数据库列表名
#basepath = "/home/dy_server/doorplates_server/temp_datas" # 默认路径
basepath = config.TEMP_DATAS_PATH # 默认路径
dydatas_basepath = config.DY_DATAS_PATH # 永久数据 默认路径
sql_str = '' # 当前的查询sql


class REQUEST_TYPE(enum.IntEnum):
    installed, picture = range(2)

    @classmethod
    def has_value(cls, value):
        return any(value == item.value for item in cls)

    @classmethod
    def has_key(cls, key):
        return any(key == item.name for item in cls)

class CITY(enum.IntEnum):
    guangzhou, foshan = range(2)

    @classmethod
    def has_value(cls, value):
        return any(value == item.value for item in cls)

    @classmethod
    def has_key(cls, key):
        return any(key == item.name for item in cls)

# 检索数据，参数是要查询的条件，以及检索的数据库对象, 表名，以及列名
def query_datas(request, db, table_name, col_name_list, need_sort=False):


    cursor = db.cursor()

    # cursor.execute(
    #     " SELECT column_name FROM information_schema.columns WHERE table_schema='ws_doorplate' AND table_name='gz_orders' ")
    # results = cursor.fetchall()
    # col_name_list = []
    # # print(results)
    # for i in results:
    #     col_name_list.append(str(i[0]))
    if need_sort:
        # 做排序用
        village_col = col_name_list.index('pcs')
        road_col = col_name_list.index('street')
        # doorplate_col = col_name_list.index('dp_num')
        doorplate_col = col_name_list.index('dp_num_trans')

    query_key = []
    for key in request.args.keys():
        if key.find('like') > 0:
            query_key.append(key[0:key.find('like') - 1])

    # 获取当前页码，以及每一页需要呈现的数据数
    if request.args.get('_page'):
        page = int(request.args.get('_page'))
    else:
        page = 1

    if request.args.get('_limit'):
        limit = int(request.args.get('_limit'))
        sql_limit = " LIMIT " + str((page - 1) * limit) + "," + str(limit)
    else:
        limit = 0
        sql_limit = ""

    sql = ""
    # SQL 查询语句
    #print(str(request.args))
    #sql_limit = " LIMIT " + str((page - 1) * limit) + "," + str(limit)

    if len(query_key) > 0:
        # print(query_key)
        sql_like_query = ''
        for key in query_key:
            if sql_like_query == '':
                sql_like_query += ' WHERE ' + key + ' LIKE \'%' + request.args.get(str(key + '_like')) + '%\''
            else:
                sql_like_query += ' AND ' + key + ' LIKE \'%' + request.args.get(str(key + '_like')) + '%\''
        if request.args.get('_page'):
            sql = "SELECT * FROM " + table_name + sql_like_query + sql_limit
        else:
            sql = "SELECT * FROM " + table_name + sql_like_query
        sql_str = "SELECT * FROM " + table_name + sql_like_query
        cursor.execute("SELECT COUNT(*) FROM " + table_name + sql_like_query)
        count = cursor.fetchall()
        count = int(count[0][0])
    elif page > 0:
        if request.args.get('_page'):
            sql = "SELECT * FROM " + table_name + sql_limit
        else:
            sql = "SELECT * FROM " + table_name
        #sql = "SELECT * FROM " + table_name + sql_limit
        sql_str = "SELECT * FROM " + table_name
        cursor.execute("SELECT COUNT(*) FROM " + table_name)
        count = cursor.fetchall()
        # print(int(count[0][0]))
        count = int(count[0][0])



    doorplatesList = []

    if sql:
        try:
            # 执行sql语句
            print(sql)
            cursor.execute(sql)
            results = cursor.fetchall()

            if need_sort:
            # 排序
                results = [list(i) for i in results]
                results = dp_sort.sort(results, village_col, road_col, doorplate_col)

            if len(results) >= 1:
                print("查到相关数据")
                # doorplatesList = []
                global datas
                for r in results:
                    doorplate = {}
                    col = 0
                    for v in r:
                        if type(v) == datetime.datetime:
                            doorplate[col_name_list[col]] = v.__str__()
                        else:
                            doorplate[col_name_list[col]] = v
                        col += 1
                    doorplatesList.append(doorplate)
                datas = doorplatesList

                return datas, count
            else:
                print("没有相关数据")
                return [], 0
            # 提交到数据库执行
            db.commit()
        except:
            # 如果发生错误则回滚
            traceback.print_exc()
            db.rollback()
            return [], 0


def init_api(app):

    # test
    @app.route('/test_api', methods=['GET'])
    def test_api():
        time.sleep(5)
        return jsonify(common.trueReturn('', 'test！' + str(time.asctime( time.localtime(time.time()) ))))


    # 佛山门牌照片上传
    @app.route('/pictures_test', methods=['GET', 'POST'])
    def pictures_test():
        result = Auth.identify(Auth, request)
        if (result['status'] and result['data']):
            pass
        else:
            pass
            #return json.dumps(result, ensure_ascii=False)
        # print(request.data)
        # #print(request.headers)
        # print(request.form)
        # print(request.json)
        # print(request.stream)
        # print(request.input_stream)
        # print(request.get_data())
        # print(request.stream.read())
        # request_json = request.get_json()
        msg = ""

        print("有照片要上传")
        if request.method == 'POST':
            print(request.files)
            if 'file' not in request.files:
                return jsonify(common.falseReturn("", "上传失败，可能file参数不对"))
            f = request.files['file']
            #print(f)
            #print(type(f))


            #print(request.form)
            city = str(request.form.get('city'))
            filename = str(request.form.get('filename'))
            #if city == CITY.foshan.name:
            # 注意：没有的文件夹一定要先创建，不然会提示没有该路径
            filename = secure_filename(filename)
            filename_pre = filename.split('.')[0]
            global_id = filename.split('.')[0].split('_')[0]
            pictures_type = filename.split('.')[0].split('_')[1]
            filesuffix = filename.split('.')[1]
            #upload_path = os.path.join(dydatas_basepath + '/gd_dp_photos/' + city, filename)
            sum = 0

            '''
            for root, dirs, files in os.walk(dydatas_basepath + '/gd_dp_photos/' + city):
                # print('root_dir:', root)  # 当前目录路径
                # print('sub_dirs:', dirs)  # 当前路径下所有子目录
                # print('files:', files)  # 当前路径下所有非目录子文件
                for file in files:
                    if file.find(filename_pre) == 0:
                        sum += 1
            if sum == 0:
                filename = filename_pre + '.' + filesuffix
            else:
                msg = "---但是已经有该相同名字的图片了，检查下DZBM和图片类型是否正确，如果都正确，则是重复上传"
                filename = filename_pre + "_" + str(sum) + '.' + filesuffix
            #filename = global_id + "(" + str(sum) + ")" + '.' + filesuffix
            '''

            temp_file = tempfile.TemporaryFile()
            #print(tempfile)


            f.save(temp_file)


            temp_file.seek(0)
            upload_file_MD5 = get_MD5.GetFileMd5_from_file(temp_file)
            print("upload_file_MD5", upload_file_MD5)

            filename = filename_pre + '.' + filesuffix
            while(os.path.isfile(dydatas_basepath + '/gd_dp_photos/' + city + "/" + filename)):  # 入参需要是绝对路径
                # temp_MD5 = get_MD5.GetFileMd5(dydatas_basepath + '/gd_dp_photos/' + city + "/" + filename)
                temp_MD5 = get_MD5.GetFileMd5(dydatas_basepath + '/gd_dp_photos/' + city + "/" + filename)
                print("temp_MD5", temp_MD5)
                if upload_file_MD5 != temp_MD5:
                    sum += 1
                    filename = filename_pre + "_" + str(sum) + '.' + filesuffix
                else:
                    return jsonify(common.falseReturn('', '已经有与filename相同命名的照片，' + filename, addition=common.false_Type.exist))

            #excel_name += '.xls'
            upload_path = os.path.join(dydatas_basepath + '/gd_dp_photos/' + city, filename)

            print("文件保存在：", upload_path)

            f.stream.seek(0)
            f.save(upload_path)
            #print(filename.split('.'))

            request_type = str(request.form.get('type'))
            if request_type == REQUEST_TYPE.picture.name:
                print("登记安装")
                # print(request_json.get('qrcode'))
                # print(request_json.get('installed_by'))
                # print(request_json.get('installed_coordinate'))
                #dzbm = filename.split('.')[0]

                database_name = 'fs_doorplate'
                if city == CITY.foshan.name:
                    database_name = 'fs_doorplate'
                    table_name = 'fs_dp'
                if city == CITY.guangzhou.name:
                    database_name = 'ws_doorplate'
                    table_name = 'gz_orders'

                #db = pymysql.connect("localhost", "root", "root", "丹灶数据库")
                db = pymysql.connect("localhost", "root", "root", database_name)
                # 使用cursor()方法获取操作游标
                cursor = db.cursor()

                #select_sql = "SELECT `index` FROM gis_ordered WHERE `DZBM` = " + "\'" + dzbm + "\'" + " LIMIT 1"
                select_sql = "SELECT `index` FROM " + table_name + " WHERE `global_id` = " + "\'" + global_id + "\'" + " LIMIT 1"

                if select_sql:
                    try:
                        # print(select_sql)
                        cursor.execute(select_sql)
                        # print(cursor.fetchall())
                        if cursor.fetchall():
                            pass
                        else:
                            # 提交到数据库执行
                            db.commit()
                            # 关闭数据库连接
                            db.close()
                            return jsonify(common.falseReturn("", "检查照片名称有无错误"))
                    except:
                        # 如果发生错误则回滚
                        # traceback.print_exc()
                        db.rollback()
                        # 关闭数据库连接
                        db.close()
                        return jsonify(common.falseReturn("", "上传失败"))

                # sql = "UPDATE gis_ordered  SET `installed_photos`=`installed_photos`+1 " + \
                #       " WHERE `DZBM` = " + "\'" + dzbm + "\'"


                sql = "UPDATE "+ table_name + " SET `installed_photos_" + pictures_type + "`=`installed_photos_" + pictures_type + "`+1 " + \
                      " WHERE `global_id` = " + "\'" + global_id + "\'"

                if sql:
                    try:
                        print(sql)
                        cursor.execute(sql)
                        # print(cursor.fetchall())
                        # 提交到数据库执行
                        db.commit()
                        # 关闭数据库连接
                        db.close()
                        return jsonify(common.trueReturn("", "上传成功" + msg))
                    except:
                        # 如果发生错误则回滚
                        # traceback.print_exc()
                        db.rollback()
                        # 关闭数据库连接
                        db.close()
                        return jsonify(common.falseReturn("", "上传失败"))

            # # return '成功上传'
            # return jsonify(common.trueReturn("", "上传成功"))

        return jsonify(common.falseReturn("", "未上传照片，可能是请求有问题"))





    # # 佛山门牌照片数据更新脚本
    # @app.route('/update_photo_test', methods=['GET', 'POST'])
    # def update_photo():
    #     result = Auth.identify(Auth, request)
    #     if (result['status'] and result['data']):
    #         pass
    #     else:
    #         pass
    #
    #     print("开始更新")
    #     msg = ""
    #     if request.method == 'POST':
    #
    #
    #         # print(request.form)
    #         city = str(request.form.get('city'))
    #
    #         # if city == CITY.foshan.name:
    #         # 注意：没有的文件夹一定要先创建，不然会提示没有该路径
    #
    #         # db = pymysql.connect("localhost", "root", "root", "丹灶数据库")
    #         db = pymysql.connect("localhost", "root", "root", "fs_doorplate")
    #         # 使用cursor()方法获取操作游标
    #         cursor = db.cursor()
    #         sum = 0
    #         for root, dirs, files in os.walk(dydatas_basepath + '/gd_dp_photos/' + city):
    #             # print('root_dir:', root)  # 当前目录路径
    #             # print('sub_dirs:', dirs)  # 当前路径下所有子目录
    #             # print('files:', files)  # 当前路径下所有非目录子文件
    #             for file in files:
    #                 filename = secure_filename(file)
    #                 global_id = filename.split('.')[0].split('_')[0]
    #                 pictures_type = filename.split('.')[0].split('_')[1]
    #
    #
    #
    #
    #
    #                 sql = "UPDATE fs_dp SET `installed_photos_" + pictures_type + "`=`installed_photos_" + pictures_type + "`+1 " + \
    #                       " WHERE `global_id` = " + "\'" + global_id + "\'"
    #
    #                 if sql:
    #                     try:
    #                         #print(sql)
    #                         cursor.execute(sql)
    #                         # print(cursor.fetchall())
    #                         # 提交到数据库执行
    #                         db.commit()
    #                         sum += 1
    #
    #                     except:
    #                         # 如果发生错误则回滚
    #                         # traceback.print_exc()
    #                         db.rollback()
    #         # 关闭数据库连接
    #         db.close()
    #     msg += "总共更新了：" + str(sum) + "个数据"
    #     return jsonify(common.trueReturn("", "上传成功" + msg))
    #
    #
    # # 检索数据 代码备份
    # @app.route('/doorplates111', methods=['GET'])
    # def getDataRequest111():
    #
    #     print("当前访问用户：", request.remote_addr)
    #
    #     # print("Authorization：", request.headers['Authorization'])
    #
    #     result = Auth.identify(Auth, request)
    #     # print(result)
    #     if (result['status'] and result['data']):
    #         pass
    #     else:
    #         pass
    #         # return json.dumps(result, ensure_ascii=False)
    #     # 查询数据是否存在
    #     # 连接数据库,此前在数据库中创建数据库dayi_doorplate
    #     # db = pymysql.connect("localhost", "root", "123456", "dayi_doorplate")
    #     # db = pymysql.connect("localhost", "root", "root", "ws_doorplate")
    #     db = pymysql.connect(config.DB_HOST, config.DB_USER, config.DB_PASSWORD, config.DB_NAME)
    #     # 使用cursor()方法获取操作游标
    #     cursor = db.cursor()
    #
    #     global data_col_name, sql_str
    #
    #     # 获取列名
    #     cursor.execute(
    #         " SELECT column_name FROM information_schema.columns WHERE table_schema='ws_doorplate' AND table_name='gz_orders' ")
    #     results = cursor.fetchall()
    #     col_name_list = []
    #     # print(results)
    #     for i in results:
    #         col_name_list.append(str(i[0]))
    #
    #     # print("列名：", col_name_list)
    #     data_col_name = col_name_list
    #     db.commit()
    #
    #     # print(request.args)
    #     # print(type(request.args))
    #     query_key = []
    #     for key in request.args.keys():
    #         if key.find('like') > 0:
    #             query_key.append(key[0:key.find('like') - 1])
    #
    #     # 获取当前页码，以及每一页需要呈现的数据数
    #     if request.args.get('_page'):
    #         page = int(request.args.get('_page'))
    #     else:
    #         page = 0
    #     if request.args.get('_limit'):
    #         limit = int(request.args.get('_limit'))
    #     else:
    #         limit = 0
    #
    #     sql = ""
    #     # SQL 查询语句
    #     print(str(request.args))
    #     sql_limit = " LIMIT " + str((page - 1) * limit) + "," + str(limit)
    #     # if len(str(request.args.get('doorID')))
    #     # if request.args.get('dp_id'):
    #     #     sql = "SELECT * FROM gz_orders WHERE dp_id='%s' " % (request.args.get('dp_id'))
    #     # if request.args.get('dp_id_like'):
    #     #     sql = "SELECT * FROM gz_orders WHERE dp_id like '%%%s%%' " % (request.args.get('dp_id_like'))
    #     # if request.args.get('fix'):
    #     #     sql = "SELECT * FROM gz_orders WHERE fix='%s' " % (request.args.get('fix'))
    #     # if request.args.get('pcs_like'):
    #     #     sql = "SELECT * FROM gz_orders WHERE pcs like '%%%s%%' " % (request.args.get('pcs_like'))
    #     # if request.args.get('order_id'):
    #     #     sql = "SELECT * FROM gz_orders WHERE order_id='%s' " % (request.args.get('order_id'))
    #
    #     if len(query_key) > 0:
    #         # print(query_key)
    #         sql_like_query = ''
    #         for key in query_key:
    #             # print(key)
    #             # print(request.args.get(str(key + '_like')))
    #             if sql_like_query == '':
    #                 sql_like_query += 'WHERE ' + key + ' LIKE \'%' + request.args.get(str(key + '_like')) + '%\''
    #             else:
    #                 sql_like_query += ' AND ' + key + ' LIKE \'%' + request.args.get(str(key + '_like')) + '%\''
    #
    #         sql = "SELECT * FROM gz_orders " + sql_like_query + sql_limit
    #         sql_str = "SELECT * FROM gz_orders " + sql_like_query
    #         # print(sql)
    #         # print("SELECT COUNT(*) FROM gz_orders " + sql_like_query)
    #         cursor.execute("SELECT COUNT(*) FROM gz_orders " + sql_like_query)
    #         count = cursor.fetchall()
    #         # print(int(count[0][0]))
    #         count = int(count[0][0])
    #     # if request.args.get('pcs_like'):
    #     #     sql = "SELECT * FROM gz_orders WHERE pcs like '%%%s%%' " % (request.args.get('pcs_like'))
    #     #     sql = sql + sql_limit
    #     #     cursor.execute("SELECT COUNT(*) FROM gz_orders WHERE pcs like '%%%s%%'" % (request.args.get('pcs_like')))
    #     #     count = cursor.fetchall()
    #     #     print(int(count[0][0]))
    #     #     count = int(count[0][0])
    #     elif page > 0:
    #         # sql = "SELECT * FROM gz_orders ORDER BY dp_id LIMIT '%d' " % (request.args.get('order_id'))
    #
    #         sql = "SELECT * FROM gz_orders" + sql_limit
    #         sql_str = "SELECT * FROM gz_orders "
    #         cursor.execute("SELECT COUNT(*) FROM gz_orders")
    #         count = cursor.fetchall()
    #         # print(int(count[0][0]))
    #         count = int(count[0][0])
    #
    #     # sql = "SELECT * FROM usersTable WHERE name='%s' AND password='%s' " % (request.args.get('doorID'), \
    #     #                                                                     request.args.get('password'))
    #     # print(sql)
    #     # count = 0
    #     # resp = Response("Foo bar baz")
    #
    #     doorplatesList = []
    #     if sql:
    #         try:
    #             # 执行sql语句
    #             print(sql)
    #             cursor.execute(sql)
    #             results = cursor.fetchall()
    #             # print(len(results))
    #             # print(results)
    #
    #             # doorplatesList.append({'x-total-count': len(results)})
    #
    #             if len(results) >= 1:
    #                 print("查到相关数据")
    #
    #                 # doorplatesList = []
    #                 global datas
    #                 for r in results:
    #                     # print(r[23], end=' ')
    #                     # print(r[4], end=' ')
    #                     # print(r[2], end=' ')
    #                     # print("---")
    #                     doorplate = {}
    #
    #                     col = 0
    #                     for v in r:
    #                         doorplate[col_name_list[col]] = v
    #                         col += 1
    #                     # doorplate['contract_batch'] = r[0]
    #                     # doorplate['order_batch'] = r[1]
    #                     # doorplate['from_filename'] = r[2]
    #                     # doorplate['distirct_id'] = r[3]
    #                     # doorplate['order_id'] = r[4]
    #                     # doorplate['dp_id'] = r[5]
    #                     # doorplate['district'] = r[6]
    #                     # doorplate['pcs'] = r[7]
    #                     # doorplate['street'] = r[8]
    #                     # doorplate['dp_name'] = r[9]
    #                     # doorplate['dp_num'] = r[10]
    #                     # doorplate['dp_size'] = r[11]
    #                     # doorplate['dp_nail_style'] = r[12]
    #                     # doorplate['producer'] = r[13]
    #                     # doorplate['produce_date'] = r[14]
    #                     # doorplate['installer'] = r[15]
    #                     # doorplate['factory_batch'] = r[16]
    #                     # doorplate['factory_index'] = r[17]
    #                     # doorplate['applicant'] = r[18]
    #                     # doorplate['contact_number'] = r[19]
    #                     # doorplate['jump'] = r[20]
    #                     # doorplate['fix'] = r[21]
    #                     # doorplate['dp_type'] = r[22]
    #                     # doorplate['global_id'] = r[23]
    #                     # doorplate['index'] = r[24]
    #                     doorplatesList.append(doorplate)
    #                 '''data['code'] = 0
    #                 data['success'] = 'True'
    #                 data['page_count'] = len(doorplatesList)/limit
    #                 data['page'] = page
    #                 data['result'] = doorplatesList[(page - 1) * limit:(page) * limit]'''
    #
    #                 datas = doorplatesList
    #                 # if page==0 and limit == 0:
    #                 #     data = doorplatesList
    #                 # else:
    #                 #     data = doorplatesList[(page - 1) * limit:(page) * limit]
    #
    #                 # data['x-total-count'] = len(doorplatesList)
    #                 jsonStr = json.dumps(datas, ensure_ascii=False)
    #
    #                 # print(jsonStr)
    #                 # decode_json = json.loads(jsonStr)
    #                 # print(decode_json)
    #
    #                 # return jsonStr
    #                 resp = Response(jsonStr)
    #                 resp.mimetype = 'application/json'
    #                 # resp.headers['x-total-count'] = len(results)
    #                 resp.headers['x-total-count'] = count
    #                 resp.headers['access-control-expose-headers'] = 'X-Total-Count'
    #                 # return Response(jsonStr, mimetype='application/json')
    #                 # 关闭数据库连接
    #                 db.close()
    #                 return resp
    #             else:
    #                 print("没有相关数据")
    #                 # return jsonStr
    #                 resp = Response(str([]))
    #                 resp.mimetype = 'application/json'
    #                 # resp.headers['x-total-count'] = len(results)
    #                 resp.headers['x-total-count'] = count
    #                 resp.headers['access-control-expose-headers'] = 'X-Total-Count'
    #                 # return Response(jsonStr, mimetype='application/json')
    #                 # 关闭数据库连接
    #                 db.close()
    #                 return resp
    #             # 提交到数据库执行
    #             db.commit()
    #         except:
    #             # 如果发生错误则回滚
    #             traceback.print_exc()
    #             db.rollback()
    #     # else:
    #     #     data = {}
    #     #     '''data['code'] = 0
    #     #     data['success'] = 'True'
    #     #     data['page_count'] = len(doorplatesList)/limit
    #     #     data['page'] = page
    #     #     data['result'] = doorplatesList[(page - 1) * limit:(page) * limit]'''
    #     #     # data = doorplatesList[(page - 1) * limit:(page) * limit]
    #     #     data = doorplatesList
    #     #     jsonStr = json.dumps(data, ensure_ascii=False)
    #     #
    #     #     print(jsonStr)
    #     #     # decode_json = json.loads(jsonStr)
    #     #     # print(decode_json)
    #     #
    #     #     #return jsonStr
    #     #     #return Response(jsonStr, mimetype='application/json')
    #     #     resp = Response(jsonStr)
    #     #     resp.mimetype = 'application/json'
    #     #     #resp.headers['x-total-count'] = len(doorplatesList)
    #     #     resp.headers['x-total-count'] = count
    #     #     resp.headers['access-control-expose-headers'] = 'X-Total-Count'
    #     #     return resp
    #     # 关闭数据库连接
    #     db.close()
