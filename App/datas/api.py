'''

    version: 0.9.0
    create: 2019-03-15
    update: 2019-10-30
    author: Cong

    tips:
        gunicorn 不支持 argparse!!! 千万别在用gunicorn的时候用 argparse!!!
'''
from flask import jsonify
from App.auth.auths import Auth
import App.common as common
#导入数据库模块
import pymysql
# abort 异常
from flask import abort
# 发送文件的
from flask import send_file
#导入前台请求的request模块
import traceback
from flask import request
#导入json
import json
from flask import Response
import os
import tempfile
from werkzeug.utils import secure_filename
from App.datas import excel as ExcelModel
from App.datas import dp_sort
from App.datas import query
from App.datas import export_excel
from App.datas import deliver_excel
from App.datas import receive_excel
#from App.datas.excel import col_name_map
from App.datas import upload_order
from App.others import get_MD5, files_operation
from App.mysql import mysql
import datetime
import App.config as config
import enum
import math
import collections
from App import cache
from App import long_time_cache
from App import logger

#全局变量
datas = [] # 当前页面显示的数据
data_col_name = [] # 数据库列表名
basepath = config.TEMP_DATAS_PATH # 默认路径
dydatas_basepath = config.DY_DATAS_PATH # 永久数据 默认路径
sql_str = '' # 当前的查询sql


class REQUEST_TYPE(enum.IntEnum):
    '''
    col_name 获取列名
    city_name 获取城市名 新建城市名
    picture 上传照片
    collected_picture 上传采集照片
    pictures_list 获取照片列表
    picture_show 返回照片
    picture_check 照片检查
    pictures_package 照片打包
    pictures_package_without_query 照片通过前端传的文件名打包
    pictures_query 照片批量查询并打包
    installed 安装
    installed_sync 安装同步
    installed_batch_sync 安装批量同步
    qrcode_classification 扫二维码分类
    report_excel 获取统计报表
    update_data 修改数据
    scripts 脚本
    dp_num_lack 查找缺的门牌号
    collected_doorplate 插入采集门牌数据
    '''
    col_name, city_name, \
    picture, collected_picture, pictures_list, picture_show, picture_check, pictures_package, pictures_query, pictures_MD5, pictures_package_without_query, \
    installed, installed_sync, installed_batch_sync, \
    qrcode_classification, \
    report_excel, collected_report_excel, \
    update_data, \
    scripts, \
    dp_num_lack, \
    collected_doorplate, collected = range(22)

    @classmethod
    def has_value(cls, value):
        return any(value == item.value for item in cls)

    @classmethod
    def has_key(cls, key):
        return any(key == item.name for item in cls)


'''
城市名拼音，以及对应在的数据库和表名
可用下面的函数直接调取
db_name = "ws_doorplate"
table_name = "fs_dp"
if request.args.get('city'):
#if request.form.get('city'):
# 分情况用if
    db_name = CITY.get_db_name(request.args.get('city'))
    table_name = CITY.get_table_name(request.args.get('city'))
db = pymysql.connect("localhost", "root", "root", db_name)
'''
# 2019-08-10 这两个 map 已经废弃，以后直接在数据库操作
# 增加城市需要在这里增加对应的数据库、表名，以及CITY类增加对应enum
# 新建城市数据库记得新建对应的_history数据库，并且修改成无主键
city_name_table_name_map = {"guangzhou": "gz_orders",
                             "foshan": "fs_dp",
                             "maoming": "maoming_dp"

    }
city_name_db_name_map = {"guangzhou": "ws_doorplate",
                             "foshan": "ws_doorplate",
                             "maoming": "ws_doorplate"
                             }

class CITY():
    @classmethod
    def items(cls):
        city_name_list, city_name_map, city_name_db_map, city_name_table_map = mysql.get_city_name()
        items = list(city_name_map.keys())
        return items

    @classmethod
    def has_value(cls, value):
        city_name_list, city_name_map, city_name_db_map, city_name_table_map = mysql.get_city_name()
        items = list(city_name_map.keys())
        return any(value == items.index(item) for item in items)

    @classmethod
    def has_key(cls, key):
        city_name_list, city_name_map, city_name_db_map, city_name_table_map = mysql.get_city_name()
        items = list(city_name_map.keys())
        return any(key == str(item) for item in items)

    @classmethod
    def get_db_name(cls, key):
        city_name_list, city_name_map, city_name_db_map, city_name_table_map = mysql.get_city_name()
        if cls.has_key(key):
            return city_name_db_map.get(key)
        else:
            return "ws_doorplate" # 默认数据库

    @classmethod
    def get_table_name(cls, key):
        city_name_list, city_name_map, city_name_db_map, city_name_table_map = mysql.get_city_name()
        if cls.has_key(key):
            return city_name_table_map.get(key)
        else:
            return "default_dp"

    @classmethod
    def get_city_name_map(cls):
        city_name_list, city_name_map, city_name_db_map, city_name_table_map = mysql.get_city_name()
        return city_name_map
'''

class CITY():
    city_name_list, city_name_map, city_name_db_map, city_name_table_map = mysql.get_city_name()
    items = list(city_name_map.keys())

    @classmethod
    def has_value(cls, value):
        return any(value == cls.items.index(item) for item in cls.items)

    @classmethod
    def has_key(cls, key):
        return any(key == str(item) for item in cls.items)

    @classmethod
    def get_db_name(cls, key):
        if cls.has_key(key):
            return cls.city_name_db_map.get(key)
        else:
            return "ws_doorplate" # 默认数据库

    @classmethod
    def get_table_name(cls, key):
        if cls.has_key(key):
            return cls.city_name_table_map.get(key)
        else:
            return "gz_orders"
'''

from App.others import pictures_operation # 只能定义在这，不然会导致 pictures_operation import CITY出错

# class CITY(enum.IntEnum):
#     guangzhou, foshan, maoming = range(3)
#
#     @classmethod
#     def has_value(cls, value):
#         return any(value == item.value for item in cls)
#
#     @classmethod
#     def has_key(cls, key):
#         return any(key == item.name for item in cls)
#
#     @classmethod
#     def get_db_name(cls, key):
#         if cls.has_key(key):
#             return city_name_db_name_map.get(key)
#         else:
#             return "ws_doorplate"
#
#     @classmethod
#     def get_table_name(cls, key):
#         if cls.has_key(key):
#             return city_name_table_name_map.get(key)
#         else:
#             return "gz_orders"


class EXCEL_TYPE(enum.IntEnum):
    '''
    order 上传订单
    query 检索数据
    produced_without_query 直接生成生产单不用检索
    produced_with_query 检索数据并用得到的结果生成生产单
    templates 获取excel模板
    '''
    order, query, produced_without_query, produced_with_query, produced_with_query_without_excel, templates = range(6)

    @classmethod
    def has_value(cls, value):
        return any(value == item.value for item in cls)

    @classmethod
    def has_key(cls, key):
        return any(key == item.name for item in cls)

# 检索数据，参数是要查询的条件，以及检索的数据库对象, 表名，以及列名
#@cache.cached(timeout=60 * 2)
@cache.memoize(timeout=config.cache_timeout)
def query_datas(request, db_name, table_name, col_name_list, need_sort=False):
    db = pymysql.connect("localhost", "root", "root", db_name)
    cursor = db.cursor()

    # cursor.execute(
    #     " SELECT column_name FROM information_schema.columns WHERE table_schema='ws_doorplate' AND table_name='gz_orders' ")
    # results = cursor.fetchall()
    # col_name_list = []
    # # logger.info(results)
    # for i in results:
    #     col_name_list.append(str(i[0]))

    # 范围查询
    range_query_key = []
    for key in request.args.keys():
        if key.find('_range') > 0:
            range_query_key.append(key[0:key.find('range') - 1])

    
    # 模糊查询
    query_key = []
    for key in request.args.keys():
        if key.find('_like') > 0:
            query_key.append(key[0:key.find('like') - 1])

    # 精准查询
    accurate_query_key = []
    for key in request.args.keys():
        if key.find('_accurate') > 0:
            accurate_query_key.append(key[0:key.find('accurate') - 1])


    # 获取当前页码，以及每一页需要呈现的数据数
    if request.args.get('_page'):
        page = int(request.args.get('_page'))
    else:
        page = 1

    if request.args.get('_limit'):
        limit = int(request.args.get('_limit'))
        sql_limit = " LIMIT " + str((page - 1) * limit) + "," + str(limit)
    else:
        limit = 10
        sql_limit = " LIMIT " + str((page - 1) * limit) + "," + str(limit)

    sql = ""
    # SQL 查询语句
    #logger.info(str(request.args))
    #sql_limit = " LIMIT " + str((page - 1) * limit) + "," + str(limit)

    if table_name.find("collection") >= 0:


        col_name_final_list = col_name_list

        if need_sort:
            # 做排序用
            village_col = col_name_final_list.index('pcs')
            road_col = col_name_final_list.index('street')
            # doorplate_col = col_name_list.index('dp_num')
            doorplate_col = col_name_final_list.index('dp_num_trans')
        # 模糊查询
        if len(query_key) > 0:
            # logger.info(query_key)
            sql_like_query = ''
            for key in query_key:
                if sql_like_query == '':
                    if key == 'index':
                        sql_like_query += ' WHERE ' + 'cast( `' + key + '` as char )' + ' LIKE \'%' + request.args.get(str(key + '_like')) + '%\''
                    else:
                        sql_like_query += ' WHERE ' + key + ' LIKE \'%' + request.args.get(str(key + '_like')) + '%\''
                else:
                    if key == 'index':
                        sql_like_query += ' AND ' + 'cast( `' + key + '` as char )' + ' LIKE \'%' + request.args.get(str(key + '_like')) + '%\''
                    else:
                        sql_like_query += ' AND ' + key + ' LIKE \'%' + request.args.get(str(key + '_like')) + '%\''
            if request.args.get('_page'):
                sql = "SELECT * FROM " + table_name + sql_like_query + sql_limit
            else:
                sql = "SELECT * FROM " + table_name + sql_like_query + sql_limit
            sql_str = "SELECT * FROM " + table_name + sql_like_query
            cursor.execute("SELECT COUNT(*) FROM " + table_name + sql_like_query)
            count = cursor.fetchall()
            count = int(count[0][0])
        # 精准查询
        elif len(accurate_query_key) > 0:
            # logger.info(query_key)
            sql_accurate_query = ''
            for key in accurate_query_key:
                if sql_accurate_query == '':
                    if key == 'index':
                        sql_accurate_query += ' WHERE ' + 'cast( `' + key + '` as char )' + ' = \'' + request.args.get(
                            str(key + '_accurate')) + '\''
                    else:
                        sql_accurate_query += ' WHERE ' + key + ' = \'' + request.args.get(str(key + '_accurate')) + '\''
                else:
                    if key == 'index':
                        sql_accurate_query += ' AND ' + 'cast( `' + key + '` as char )' + ' = \'' + request.args.get(
                            str(key + '_accurate')) + '\''
                    else:
                        sql_accurate_query += ' AND ' + key + ' = \'' + request.args.get(str(key + '_accurate')) + '\''
            if request.args.get('_page'):
                sql = "SELECT * FROM " + table_name + sql_accurate_query + sql_limit
            else:
                sql = "SELECT * FROM " + table_name + sql_accurate_query + sql_limit
            sql_str = "SELECT * FROM " + table_name + sql_accurate_query
            cursor.execute("SELECT COUNT(*) FROM " + table_name + sql_accurate_query)
            count = cursor.fetchall()
            count = int(count[0][0])
        elif page > 0:
            if request.args.get('_page'):
                sql = "SELECT * FROM " + table_name + sql_limit
            elif sql_limit:
                sql = "SELECT * FROM " + table_name + sql_limit
            else:
                sql = "SELECT * FROM " + table_name
            #sql = "SELECT * FROM " + table_name + sql_limit
            sql_str = "SELECT * FROM " + table_name
            cursor.execute("SELECT COUNT(*) FROM " + table_name)
            count = cursor.fetchall()
            # logger.info(int(count[0][0]))
            count = int(count[0][0])


    else:
        #col_name_list = get_col_name_list(request)
        col_name_projects_list = ["contract_batch", "order_batch", "order_id"]
        col_name_need_list = []
        col_name_need_pure_list = []
        for i in col_name_list:
            if i not in col_name_projects_list:
                col_name_need_pure_list.append(i)
                col_name_need_list.append(table_name+".`"+i+"`")
            else:
                pass

        col_name_final_list = col_name_projects_list + col_name_need_pure_list

        if need_sort:
            # 做排序用
            village_col = col_name_final_list.index('pcs')
            road_col = col_name_final_list.index('street')
            # doorplate_col = col_name_list.index('dp_num')
            doorplate_col = col_name_final_list.index('dp_num_trans')


        sql_head = " SELECT  t1.`contract_batch`, t1.`order_batch`, t1.`order_id`, " + ",".join(col_name_need_list) + " FROM {table_name} "
        sql_head = sql_head.format(table_name=table_name)
        sql_count_head = " SELECT COUNT(*) FROM {table_name}"
        sql_count_head = sql_count_head.format(table_name=table_name)

        projects_condition_sql = ""

        sql_range_query = ''
        # 大于、小于范围查询
        if len(range_query_key) > 0:
            # logger.info(query_key)

            for key in range_query_key:

                sign = request.args.get(str(key + '_range')).split("_")[0]

                value = request.args.get(str(key + '_range')).split("_")[1]

                if len(query_key) == 0 and len(accurate_query_key) == 0:
                    if key == 'index':
                        sql_range_query += ' WHERE ' + 'cast( {table_name}.`' + key + '` as char )' +  sign+  ' \'' + request.args.get(str(key + '_range')).split("_")[1] + '\''
                    else:
                        sql_range_query += ' WHERE {table_name}.' + key + " " + sign + ' \'' + request.args.get(str(key + '_range')).split("_")[1] + '\''
                else:
                    if key == 'index':
                        sql_range_query += ' AND ' + 'cast( {table_name}.`' + key + '` as char )' + " " + sign + ' \'%' + request.args.get(str(key + '_range')).split("_")[1] + '\''
                    else:
                        sql_range_query += ' AND {table_name}.' + key + " " + sign + ' \'' + request.args.get(str(key + '_range')).split("_")[1] + '\''

            sql_range_query = sql_range_query.format(table_name=table_name)

        # 模糊查询
        if len(query_key) > 0:
            # logger.info(query_key)
            sql_like_query = ''
            for key in query_key:
                if key in col_name_projects_list:
                    if projects_condition_sql == "":
                        projects_condition_sql += ' WHERE ' + key + ' LIKE \'%' + request.args.get(str(key + '_like')) + '%\''
                    else:
                        projects_condition_sql += ' AND ' + key + ' LIKE \'%' + request.args.get(str(key + '_like')) + '%\''
                else:
                    if sql_like_query == '':
                        if key == 'index':
                            sql_like_query += ' WHERE ' + 'cast( {table_name}.`' + key + '` as char )' + ' LIKE \'%' + request.args.get(str(key + '_like')) + '%\''
                        else:
                            sql_like_query += ' WHERE {table_name}.' + key + ' LIKE \'%' + request.args.get(str(key + '_like')) + '%\''
                    else:
                        if key == 'index':
                            sql_like_query += ' AND ' + 'cast( {table_name}.`' + key + '` as char )' + ' LIKE \'%' + request.args.get(str(key + '_like')) + '%\''
                        else:
                            sql_like_query += ' AND {table_name}.' + key + ' LIKE \'%' + request.args.get(str(key + '_like')) + '%\''
            projects_sql = " INNER JOIN " \
                           "(SELECT projects.`index`, projects.`contract_batch`, projects.`order_batch`, projects.`order_id` FROM projects " + \
                           projects_condition_sql + \
                           " ) t1 on t1.`index` = {table_name}.`projects_index` "
            sql_like_query = sql_like_query.format(table_name=table_name)
            projects_sql = projects_sql.format(table_name=table_name)
            if request.args.get('_page'):
                sql = sql_head + projects_sql + sql_like_query + sql_range_query + sql_limit
            else:
                sql = sql_head + projects_sql + sql_like_query + sql_range_query + sql_limit
            sql_str = sql_head + projects_sql + sql_like_query
            cursor.execute(sql_count_head + projects_sql + sql_like_query + sql_range_query)
            count = cursor.fetchall()
            count = int(count[0][0])
        # 精准查询
        elif len(accurate_query_key) > 0:
            # logger.info(query_key)
            sql_accurate_query = ''
            for key in accurate_query_key:

                if key in col_name_projects_list:
                    if projects_condition_sql == "":
                        projects_condition_sql += ' WHERE ' + key + ' = \'' + request.args.get(str(key + '_accurate')) + '\''
                    else:
                        projects_condition_sql += ' AND ' + key + ' = \'' + request.args.get(str(key + '_accurate')) + '\''
                else:
                    if sql_accurate_query == '':
                        if key == 'index':
                            sql_accurate_query += ' WHERE ' + 'cast( {table_name}.`' + key + '` as char )' + ' = \'' + request.args.get(
                                str(key + '_accurate')) + '\''
                        else:
                            sql_accurate_query += ' WHERE {table_name}.' + key + ' = \'' + request.args.get(str(key + '_accurate')) + '\''
                    else:
                        if key == 'index':
                            sql_accurate_query += ' AND ' + 'cast( {table_name}.`' + key + '` as char )' + ' = \'' + request.args.get(
                                str(key + '_accurate')) + '\''
                        else:
                            sql_accurate_query += ' AND {table_name}.' + key + ' = \'' + request.args.get(str(key + '_accurate')) + '\''

            projects_sql = " INNER JOIN " \
                           "(SELECT projects.`index`, projects.`contract_batch`, projects.`order_batch`, projects.`order_id` FROM projects " + \
                           projects_condition_sql + \
                           " ) t1 on t1.`index` = {table_name}.`projects_index` "
            sql_accurate_query = sql_accurate_query.format(table_name=table_name)
            projects_sql = projects_sql.format(table_name=table_name)
            if request.args.get('_page'):
                sql = sql_head + projects_sql + sql_accurate_query + sql_range_query + sql_limit
            else:
                sql = sql_head + projects_sql + sql_accurate_query + sql_range_query + sql_limit
            sql_str = sql_head + projects_sql + sql_accurate_query
            cursor.execute(sql_count_head + projects_sql + sql_accurate_query + sql_range_query)

            count = cursor.fetchall()
            count = int(count[0][0])
        elif page > 0:
            projects_sql = " INNER JOIN " \
                           "(SELECT projects.`index`, projects.`contract_batch`, projects.`order_batch`, projects.`order_id` FROM projects " + \
                           projects_condition_sql + \
                           " ) t1 on t1.`index` = {table_name}.`projects_index` "
            projects_sql = projects_sql.format(table_name=table_name)

            if request.args.get('_page'):

                sql = sql_head + projects_sql + sql_range_query + sql_limit
                #sql = "SELECT * FROM " + table_name + sql_range_query +  sql_limit
            elif sql_limit:

                sql = sql_head + projects_sql + sql_range_query + sql_limit
                #sql = "SELECT * FROM " + table_name + sql_range_query + sql_limit
            else:

                sql = sql_head + projects_sql + sql_range_query
                sql = "SELECT * FROM " + projects_sql + sql_range_query
            #sql = "SELECT * FROM " + table_name + sql_limit
            sql_str = "SELECT * FROM " + table_name
            cursor.execute("SELECT COUNT(*) FROM " + table_name + projects_sql + sql_range_query)
            count = cursor.fetchall()
            # logger.info(int(count[0][0]))
            count = int(count[0][0])





    doorplatesList = []

    if sql:
        try:
            # 执行sql语句
            logger.info("查询数据 sql: %s", sql)
            #write_str_to_log(sql)
            cursor.execute(sql)
            results = cursor.fetchall()

            if need_sort:
            # 排序
                results = [list(i) for i in results]
                results = dp_sort.sort(results, village_col, road_col, doorplate_col)

            if len(results) >= 1:
                logger.info("查到相关数据")
                # doorplatesList = []
                global datas
                for r in results:
                    doorplate = {}
                    col = 0
                    for v in r:
                        if type(v) == datetime.datetime:
                            doorplate[col_name_final_list[col]] = v.__str__()
                        else:
                            doorplate[col_name_final_list[col]] = v
                        col += 1
                    doorplatesList.append(doorplate)
                datas = doorplatesList

                db.close()
                return datas, count
            else:
                logger.info("没有相关数据")
                db.close()
                return [], 0
            # 提交到数据库执行
            db.commit()
            #db.close()
        except:
            # 如果发生错误则回滚
            traceback.print_exc()
            db.rollback()
            db.close()
            return [], 0

def get_col_name_list(request):
    col_name_list = []

    db_name = "ws_doorplate"
    table_name = "gz_orders"
    if request.args.get('city'):
        db_name = CITY.get_db_name(request.args.get('city'))
        table_name = CITY.get_table_name(request.args.get('city'))
    db = pymysql.connect("localhost", "root", "123456", db_name)

    # 使用cursor()方法获取操作游标
    cursor = db.cursor()

    # global data_col_name, sql_str

    # 获取列名
    cursor.execute(
        " SELECT column_name FROM information_schema.columns WHERE table_schema=\'" + db_name + "\' AND table_name=\'" + table_name + "\'")
    results = cursor.fetchall()
    col_name_list = []
    # logger.info(results)
    for i in results:
        col_name_list.append(str(i[0]))

    # # logger.info("列名：%s", col_name_list)
    # data_col_name = col_name_list


    return col_name_list

def init_api(app):

    # cache = Cache()  # 缓存 要更改使用的类型，例如redis，在config改
    # cache.init_app(app)

    # 检索数据
    @app.route('/doorplates', methods=['GET'])
    #@cache.cached(timeout=config.cache_timeout, key_prefix='view')
    def doorplates_get():
        app.logger.info("request: %s", request)
        app.logger.info("当前访问用户：%s", request.remote_addr)

        #app.logger.info("Authorization：", request.headers['Authorization'])

        result = Auth.identify(Auth, request)
        app.logger.info(result)
        app.logger.info("状态: %s 用户: %s ", result.get('status'),  result.get('data'))
        if (result['status'] and result['data']):
            pass
        else:
            #return json.dumps(result, ensure_ascii=False)
            #return jsonify(result)
            pass
        col_name_map = mysql.get_col_name_map()

        col_name_list = get_col_name_list(request)

        request_json = request.get_json()

        if request.method == 'GET':

            if request.args.get('type') == REQUEST_TYPE.col_name.name:
                # 获取在col_name_map的字段名与名称的映射，如果不存在则用字段名作为名称
                col_name_list = [[i, col_name_map.get(i) if col_name_map.get(i) else i] for i in col_name_list]

                return jsonify(common.trueReturn({"col_name_list": col_name_list, "col_name_map": col_name_map}, "col_name_list为字段名列表，col_name_map为对应的中文名"))

            elif request.args.get('type') == REQUEST_TYPE.city_name.name:
                city_name_list = []
                city_name_map = {}

                db = pymysql.connect("localhost", "root", "root", "ws_doorplate")
                # 使用cursor()方法获取操作游标
                cursor = db.cursor()

                # 获取列名
                cursor.execute(
                    " SELECT `city`,`city_name_chinese`,`city_db`,`city_table` FROM cities ")
                results = cursor.fetchall()
                # app.logger.info(results)
                for i in results:
                    city_name_list.append([str(i[0]), str(i[1])])
                    city_name_map[str(i[0])] = str(i[1])

                # 关闭数据库连接
                db.close()
                return jsonify(common.trueReturn({"city_name_list": city_name_list, "city_name_map": city_name_map},
                                                 "city_name_list为字段名列表，city_name_map为对应的中文名"))


            else:
                db_name = "ws_doorplate"
                table_name = "fs_dp"
                if request.args.get('city'):
                    db_name = CITY.get_db_name(request.args.get('city'))
                    table_name = CITY.get_table_name(request.args.get('city'))


                datas, count = query_datas(request, db_name, table_name, col_name_list)
                if count == 0:
                    # app.logger.info("没有相关数据")
                    pass

                # jsonStr = json.dumps(datas, ensure_ascii=False)
                # resp = Response(jsonStr)
                # resp.mimetype = 'application/json'
                # resp.headers['x-total-count'] = count
                # resp.headers['access-control-expose-headers'] = 'X-Total-Count'
                # return resp

                jsonStr = json.dumps((common.trueReturn({"doorplates": datas},
                                                 "doorplates为门牌数据")),
                                     ensure_ascii=False,
                                     indent=1)
                resp = Response(jsonStr)
                resp.mimetype = 'application/json'
                resp.headers['x-total-count'] = count
                resp.headers['access-control-expose-headers'] = 'X-Total-Count'
                resp.content_type = 'application/json'
                return resp


    # 数据修改、新增
    @app.route('/doorplates', methods=['PUT', 'POST'])
    # @cache.cached(timeout=60 * 2)
    def doorplates_put_post():
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
            #return jsonify(result)
            pass
        col_name_map = mysql.get_col_name_map()

        col_name_list = get_col_name_list(request)

        request_json = request.get_json()
        if request.method == 'PUT':
            request_type = request_json.get('type')
            if request_type == REQUEST_TYPE.installed.name:
                app.logger.info("登记安装")
                app.logger.info("登记安装人: %s", request_json.get('installed_by'))
                app.logger.info("登记安装的城市为: %s", request_json.get('city'))
                db_name = "ws_doorplate"
                dp_table = "fs_dp"
                if request_json.get('city'):
                    db_name = CITY.get_db_name(request_json.get('city'))
                    dp_table = CITY.get_table_name(request_json.get('city'))

                iden_id = "global_id"
                if request_json.get('city') == "guangzhou":
                    pass

                qrcode = request_json.get('qrcode')
                if not request_json.get('installed_by'):
                    installed_by = "未填写"
                else:
                    installed_by = request_json.get('installed_by')
                installed_coordinate = request_json.get('installed_coordinate')
                if request_json.get('installed_date'):
                    installed_date = request_json.get('installed_date')
                else:
                    #installed_date = "" #2019-09-02
                    installed_date = common.format_ymdhms_time_now()

                if request_json.get('dp_nail_style'):
                    dp_nail_style = request_json.get('dp_nail_style')
                else:
                    #installed_date = "" #2019-09-02
                    dp_nail_style = ""

                db = pymysql.connect("localhost", "root", "root", db_name)
                cursor = db.cursor()

                addition_data = {"cls": 0, "far": 0}
                sync_data = []  # 同步信息数据列表，有无同步，和数据库中的状态
                global_id_query_list = []
                global_id_query_list.append(qrcode)

                select_sql = "SELECT `index`, `installed`, `installed_photos_cls`, `installed_photos_far`, `installed_date`, `global_id` FROM " + dp_table + " WHERE `global_id` = " + "\'" + qrcode + "\'" + " LIMIT 1"

                datas_query_from_db_list = []  # 从数据库中检索出来的数据
                datas_update_list = []  # 需要update到数据库的数据
                global_id_not_in_db_list = []  # 不在数据库中的数据

                if select_sql:
                    try:
                        # app.logger.info(select_sql)
                        cursor.execute(select_sql)
                        temp = cursor.fetchall()
                        # app.logger.info(cursor.fetchall())
                        # app.logger.info(temp)
                        if temp:
                            datas_query_from_db_list = [list(i) for i in temp]
                            global_id_query_from_db_list = [i[-1] for i in datas_query_from_db_list]
                            # 找出数据库中不存在的数据
                            for i in global_id_query_list:
                                if i not in global_id_query_from_db_list:
                                    global_id_not_in_db_list.append(i)
                            addition_data["cls"] = temp[0][2]
                            addition_data["far"] = temp[0][3]
                            if request_type == REQUEST_TYPE.installed_sync.name:
                                if temp[0][1] > 0:
                                    if temp[0][4]:
                                        if temp[0][4].strftime('%Y-%m-%d %H:%M:%S') != "2019-01-01 00:00:00" and \
                                                temp[0][4].strftime(
                                                    '%Y-%m-%d %H:%M:%S') != "2000-01-01 00:00:00" and request_json.get(
                                            'force') != 1:
                                            return jsonify(
                                                common.trueReturn("", "安装信息已经存在，无需登记", addition=addition_data))
                        else:

                            contract_batch = '没有填写' + "_" + common.format_ymd_time_now()
                            #contract_batch = '没有填写'
                            order_batch = '没有填写' + "_" + common.format_ymd_time_now()
                            #order_batch = '没有填写'

                            if request_json.get('projects_index'):
                                projects_index = request_json.get('projects_index')
                                if type(projects_index) != int:
                                    projects_index = int(projects_index)
                                    # contract_batch = '没有填写'
                            else:
                                projects_index = common.format_ymd_time_now_for_filename()
                                #return jsonify(common.falseReturn("", msg="没有传入projects_index"))


                            filename = '没有填写' + "_" + common.format_ymd_time_now()
                            #filename = '没有填写'
                            data_map = {"global_id": qrcode, "installed_by": installed_by, "installed_date": installed_date, "installed_coordinate": installed_coordinate, "installed": 1}
                            # status, msg, update_date, update_num = upload_order.insert_data(filename=filename,
                            #                                                                  contract_batch=contract_batch,
                            #                                                                  order_batch=order_batch,
                            #                                                                  db_name=db_name,
                            #                                                                  db_table_name=dp_table,
                            #                                                                  uploaded_by=installed_by,
                            #                                                                 data_map=data_map)

                            if "collected" not in data_map.keys():
                                data_map["collected"] = 1
                            if "dp_nail_style" not in data_map.keys():
                                if dp_nail_style:
                                    data_map["dp_nail_style"] = dp_nail_style

                            status, msg, update_date, update_num = upload_order.insert_data(filename=filename,
                                                                                            projects_index=projects_index,
                                                                                            db_name=db_name,
                                                                                            db_table_name=dp_table,
                                                                                            uploaded_by=installed_by,
                                                                                            data_map=data_map)
                            if status:
                                app.logger.info("global_id: %s 新增到数据库 %s", qrcode, dp_table)
                            # 提交到数据库执行
                            # db.commit()
                            # 关闭数据库连接
                            db.close()
                            app.logger.info("检查global_id有无错误")
                            cache.clear()
                            return jsonify(common.falseReturn([], "检查global_id有无错误"+"global_id"+qrcode+"新增到数据库"+dp_table, addition=common.false_Type.name_false))
                    except:
                        # 如果发生错误则回滚
                        # traceback.print_exc()
                        db.rollback()
                        # 关闭数据库连接
                        db.close()
                        return jsonify(common.falseReturn([], "上传失败"))

                sql = "UPDATE " + dp_table + " SET `installed`=`installed`+1 " + \
                      ", `installed_by` = " + "\'" + installed_by + "\'" + \
                      ", `installed_coordinate` = " + "\'" + installed_coordinate + "\'"

                if installed_date:
                    sql += ", `installed_date` = " + "\'" + installed_date + "\'"
                else:
                    sql += ", `installed_date` = " + "\'" + datetime.datetime.now().strftime(
                        '%Y-%m-%d %H:%M:%S') + "\'"

                if dp_nail_style:
                    sql += ", `dp_nail_style` = " + "\'" + dp_nail_style + "\'"

                sql += " WHERE `{iden_id}` = " + "\'" + qrcode + "\'"

                sql = sql.format(iden_id=iden_id)

                try:
                    app.logger.info(sql)
                    cursor.execute(sql)
                    # app.logger.info(cursor.fetchall())
                    # 提交到数据库执行
                    db.commit()
                    # 关闭数据库连接
                    db.close()
                    cache.clear()
                    return jsonify(common.trueReturn("", "上传成功", addition=addition_data))
                except:
                    # 如果发生错误则回滚
                    # traceback.print_exc()
                    db.rollback()
                    # 关闭数据库连接
                    db.close()
                    return jsonify(common.falseReturn("", "上传失败"))

                # 提交到数据库执行
                db.commit()
                # 关闭数据库连接
                db.close()

            elif request_type == REQUEST_TYPE.installed_sync.name or request_type == REQUEST_TYPE.installed_batch_sync.name:
                app.logger.info(
                    "安装同步 request_type == REQUEST_TYPE.installed_sync.name or request_type == REQUEST_TYPE.installed_batch_sync.name")
                qrcode = request_json.get('qrcode')
                if not request_json.get('installed_by'):
                    installed_by = "未填写"
                else:
                    installed_by = request_json.get('installed_by')
                #installed_by = request_json.get('installed_by')
                installed_coordinate = request_json.get('installed_coordinate')
                db_name = "ws_doorplate"
                dp_table = "fs_dp"
                if request_json.get('city'):
                    db_name = CITY.get_db_name(request_json.get('city'))
                    dp_table = CITY.get_table_name(request_json.get('city'))

                # app.logger.info("dp_tabledp_tabledp_table", dp_table)
                db = pymysql.connect("localhost", "root", "root", db_name)
                cursor = db.cursor()

                if request_json.get('installed_date'):
                    installed_date = request_json.get('installed_date')
                else:
                    installed_date = ''

                if request_json.get('dp_nail_style'):
                    dp_nail_style = request_json.get('dp_nail_style')
                else:
                    #installed_date = "" #2019-09-02
                    dp_nail_style = ""

                if request_type == REQUEST_TYPE.installed_sync.name:
                    app.logger.info("同步安装数据")
                    app.logger.info("同步人: %s", installed_by)
                    app.logger.info("installed_date: %s", installed_date)
                    app.logger.info("global_id: %s", qrcode)

                installed_datas_len = 0
                if request_type == REQUEST_TYPE.installed_batch_sync.name:
                    app.logger.info("批量同步安装数据")
                    app.logger.info("同步人: %s", installed_by)
                    if request_json.get('installed_datas'):
                        installed_datas = request_json.get('installed_datas')
                    else:
                        installed_datas = []
                    # app.logger.info("installed_dates: ", installed_datas)
                    installed_datas_len = len(installed_datas)
                    app.logger.info("installed_dates_len: %s", installed_datas_len)
                    # app.logger.info("global_id: ", qrcode)
                else:

                    installed_datas = [{"qrcode": request_json.get('qrcode'),
                                        "installed_coordinate": request_json.get('installed_coordinate'),
                                        "installed_date": request_json.get('installed_date')}]
                    if request_json.get('dp_nail_style'):
                        installed_datas[0]["dp_nail_style"] = request_json.get('dp_nail_style')

                addition_data = {"cls": 0, "far": 0}
                sync_data = []  # 同步信息数据列表，有无同步，和数据库中的状态

                # app.logger.info(request_json.get('qrcode'))
                # app.logger.info(request_json.get('installed_by'))
                # app.logger.info(request_json.get('installed_coordinate'))
                global_id_query_list = []
                if request_type == REQUEST_TYPE.installed_batch_sync.name:
                    # select_sql = "SELECT `index`, `installed`, `installed_photos_cls`, `installed_photos_far`, `installed_date` FROM fs_dp WHERE `global_id` in (%s)" % (','.join(['%s'] * installed_datas_len))
                    select_sql = "SELECT `index`, `installed`, `installed_photos_cls`, `installed_photos_far`, `installed_date`, `global_id` FROM " + dp_table + " WHERE `global_id` in (%s)" % (
                        ','.join(['\'' + i['qrcode'] + '\'' for i in installed_datas]))

                    global_id_query_list = [i['qrcode'] for i in installed_datas]
                else:
                    select_sql = "SELECT `index`, `installed`, `installed_photos_cls`, `installed_photos_far`, `installed_date`, `global_id` FROM " + dp_table + " WHERE `global_id` = " + "\'" + qrcode + "\'" + " LIMIT 1"
                    global_id_query_list.append(qrcode)

                datas_query_from_db_list = []  # 从数据库中检索出来的数据
                datas_update_list = []  # 需要update到数据库的数据
                global_id_not_in_db_list = []  # 不在数据库中的数据

                if select_sql:
                    try:
                        # app.logger.info(select_sql)
                        cursor.execute(select_sql)
                        temp = cursor.fetchall()
                        # app.logger.info(cursor.fetchall())
                        # app.logger.info(temp)
                        if temp:
                            datas_query_from_db_list = [list(i) for i in temp]
                            global_id_query_from_db_list = [i[-1] for i in datas_query_from_db_list]
                            # 找出数据库中不存在的数据
                            for i in global_id_query_list:
                                if i not in global_id_query_from_db_list:
                                    global_id_not_in_db_list.append(i)

                            # 2019-09-02
                            #if request_type == REQUEST_TYPE.installed_batch_sync.name:

                            for i in range(len(temp)):
                                temp_map = {}
                                temp_map['index'] = temp[i][0]
                                temp_map['installed'] = temp[i][1]
                                temp_map["cls"] = temp[i][2]
                                temp_map["far"] = temp[i][3]
                                temp_map["installed_date"] = temp[i][4]
                                temp_map["global_id"] = temp[i][5]
                                temp_map["sync"] = 1

                                if temp[i][1] > 0:
                                    if temp[i][4]:
                                        if temp[i][4].strftime('%Y-%m-%d %H:%M:%S') != "2019-01-01 00:00:00" and \
                                                temp[i][4].strftime(
                                                    '%Y-%m-%d %H:%M:%S') != "2000-01-01 00:00:00" and \
                                                temp[i][4].strftime(
                                                    '%Y-%m-%d %H:%M:%S') != "1970-01-01 08:00:00" and request_json.get(
                                            'force') != 1:
                                            temp_map["sync"] = 0
                                # app.logger.info("temp_map %s", temp_map)
                                if temp_map["sync"] or request_json.get('force'):

                                    for j in installed_datas:
                                        if j['qrcode'] == temp_map["global_id"]:
                                            temp_map["sync_installed_date"] = j.get("installed_date")
                                            temp_map["sync_installed_coordinate"] = j["installed_coordinate"]
                                            temp_map["sync_installed_by"] = installed_by
                                            if j.get("dp_nail_style"):
                                                temp_map["dp_nail_style"] = j.get("dp_nail_style")

                                sync_data.append(temp_map)

                            # 2019-09-02
                            # else:
                            #
                            #     addition_data["cls"] = temp[0][2]
                            #     addition_data["far"] = temp[0][3]
                            #     if request_type == REQUEST_TYPE.installed_sync.name:
                            #         if temp[0][1] > 0:
                            #             if temp[0][4]:
                            #                 if temp[0][4].strftime('%Y-%m-%d %H:%M:%S') != "2019-01-01 00:00:00" and \
                            #                         temp[0][4].strftime(
                            #                             '%Y-%m-%d %H:%M:%S') != "2000-01-01 00:00:00" and request_json.get(
                            #                     'force') != 1:
                            #                     return jsonify(
                            #                         common.trueReturn("", "安装信息已经存在，无需登记", addition=addition_data))
                            # 2019-09-02

                            # temp = cursor.fetchall()
                            # app.logger.info(temp[0])
                            # pass
                            # temp = cursor.fetchall()[0]
                        else:
                            # 提交到数据库执行
                            # db.commit()
                            # contract_batch = '没有填写' + "_" + common.format_ymd_time_now()
                            # # contract_batch = '没有填写'
                            # order_batch = '没有填写' + "_" + common.format_ymd_time_now()
                            # # order_batch = '没有填写'
                            # filename = '没有填写' + "_" + common.format_ymd_time_now()
                            # # filename = '没有填写'
                            # data_map = {"global_id": qrcode, "installed_by": installed_by,
                            #             "installed_date": installed_date, "installed_coordinate": installed_coordinate, "installed": 1}
                            # status, msg, update_date, update_num = upload_order.insert_data(filename=filename,
                            #                                                                 contract_batch=contract_batch,
                            #                                                                 order_batch=order_batch,
                            #                                                                 db_name=db_name,
                            #                                                                 db_table_name=dp_table,
                            #                                                                 uploaded_by=installed_by,
                            #                                                                 data_map=data_map)

                            if request_json.get('projects_index'):
                                projects_index = request_json.get('projects_index')
                                if type(projects_index) != int:
                                    projects_index = int(projects_index)
                                    # contract_batch = '没有填写'
                            else:
                                projects_index = common.format_ymd_time_now_for_filename()
                                # return jsonify(common.falseReturn("", msg="没有传入projects_index"))

                            filename = '没有填写' + "_" + common.format_ymd_time_now()
                            # filename = '没有填写'
                            data_map = {"global_id": qrcode, "installed_by": installed_by,
                                        "installed_date": installed_date, "installed_coordinate": installed_coordinate,
                                        "installed": 1}
                            # status, msg, update_date, update_num = upload_order.insert_data(filename=filename,
                            #                                                                  contract_batch=contract_batch,
                            #                                                                  order_batch=order_batch,
                            #                                                                  db_name=db_name,
                            #                                                                  db_table_name=dp_table,
                            #                                                                  uploaded_by=installed_by,
                            #                                                                 data_map=data_map)

                            if "collected" not in data_map.keys():
                                data_map["collected"] = 1
                            if "dp_nail_style" not in data_map.keys():
                                if dp_nail_style:
                                    data_map["dp_nail_style"] = dp_nail_style
                            status, msg, update_date, update_num = upload_order.insert_data(filename=filename,
                                                                                            projects_index=projects_index,
                                                                                            db_name=db_name,
                                                                                            db_table_name=dp_table,
                                                                                            uploaded_by=installed_by,
                                                                                            data_map=data_map)
                            if status:
                                app.logger.info("global_id: %s 新增到数据库 %s", qrcode, dp_table)
                            # 关闭数据库连接
                            db.close()
                            app.logger.info("检查global_id有无错误")
                            cache.clear()
                            return jsonify(common.falseReturn([], "检查global_id有无错误"+"global_id"+qrcode+"新增到数据库"+dp_table, addition=common.false_Type.name_false))
                    except:
                        # 如果发生错误则回滚
                        # traceback.print_exc()
                        db.rollback()
                        # 关闭数据库连接
                        db.close()
                        return jsonify(common.falseReturn([], "上传失败"))

                #if request_type == REQUEST_TYPE.installed_batch_sync.name:
                    # app.logger.info(sync_data)
                    ''' # 2019-06-21
                    for i in sync_data:
                        if i['sync']:
                            sql = "UPDATE fs_dp SET `installed`=`installed`+1 " + \
                                  ", `installed_by` = " + "\'" + i["sync_installed_by"] + "\'" + \
                                  ", `installed_coordinate` = " + "\'" + i["sync_installed_coordinate"] + "\'"

                            if i.get("sync_installed_date"):
                                sql += ", `installed_date` = " + "\'" + i["sync_installed_date"] + "\'"
                            # else:
                            #     sql += ", `installed_date` = " + "\'" + datetime.datetime.now().strftime(
                            #         '%Y-%m-%d %H:%M:%S') + "\'"
                            sql += " WHERE `global_id` = " + "\'" + i['global_id'] + "\'"


                            #app.logger.info(sql)
                            #cursor.execute(sql)
                            try:
                                #app.logger.info(sql)
                                cursor.execute(sql)
                                #app.logger.info(cursor.fetchall())

                            except:
                                # 如果发生错误则回滚
                                #traceback.print_exc()
                                db.rollback()
                                # 关闭数据库连接
                                db.close()
                                return jsonify(common.falseReturn("", "同步失败", addition={"error_sql": sql, "error_datas": i}))
                    '''
                # 2019-06-21
                # 批量更新安装状态
                #app.logger.info("sync_data: %s", sync_data)
                sync_data_final_update = []
                for i in sync_data:
                    if i['sync']:
                        sync_data_final_update.append(i)

                app.logger.info("sync_data_final_update: %s", sync_data_final_update)

                sql_head = "UPDATE " + dp_table + " SET `installed`=(CASE `global_id` "
                # 使用cursor()方法获取操作游标
                cursor = db.cursor()
                step = 1000
                step_num = math.ceil(len(sync_data_final_update) / step)

                # done_count = 0
                for i in range(step_num):
                    temp_data_list = []
                    head = i * step
                    if i == (step_num - 1):
                        tail = len(sync_data_final_update)
                    else:
                        tail = (i + 1) * step

                    sql = sql_head
                    col = 0

                    # add installed
                    for j in sync_data_final_update[head:tail]:
                        temp = " WHEN " + '\'' + j['global_id'] + '\'' + " THEN " + '`installed`+1 '
                        sql += temp
                        col += 1

                    sql += " ELSE installed END) "
                    sql += ", " + " `installed_by`=(CASE `global_id` "

                    # add installed_by
                    for j in sync_data_final_update[head:tail]:
                        temp = " WHEN " + '\'' + j['global_id'] + '\'' + " THEN " + '\'' + j[
                            'sync_installed_by'] + '\''
                        sql += temp
                        col += 1

                    sql += " ELSE installed_by END) "
                    sql += ", " + " `installed_coordinate`=(CASE `global_id` "

                    # add installed_coordinate
                    for j in sync_data_final_update[head:tail]:
                        temp = " WHEN " + '\'' + j['global_id'] + '\'' + " THEN " + '\'' + j[
                            'sync_installed_coordinate'] + '\''
                        sql += temp
                        col += 1

                    sql += " ELSE installed_coordinate END) "
                    sql += ", " + " `installed_date`=(CASE `global_id` "

                    # add installed_date

                    for j in sync_data_final_update[head:tail]:
                        if j.get("sync_installed_date"):
                            temp = " WHEN " + '\'' + j['global_id'] + '\'' + " THEN " + '\'' + j[
                                'sync_installed_date'] + '\''
                        else:
                            temp = " WHEN " + '\'' + j[
                                'global_id'] + '\'' + " THEN " + '\'' + datetime.datetime.now().strftime(
                                '%Y-%m-%d %H:%M:%S') + '\''
                        sql += temp
                        col += 1

                    sql += " ELSE installed_date END) "
                    sql += ", " + " `dp_nail_style`=(CASE `global_id` "

                    for j in sync_data_final_update[head:tail]:
                        if j.get("dp_nail_style"):
                            temp = " WHEN " + '\'' + j['global_id'] + '\'' + " THEN " + '\'' + j[
                                'dp_nail_style'] + '\''
                        sql += temp
                        col += 1
                    sql += " ELSE dp_nail_style END) "

                    sql += "WHERE `global_id` IN (\'%s\') " % (
                        '\',\''.join(list([k["global_id"] for k in sync_data_final_update[head:tail]])))

                    # app.logger.info(sql)
                    try:
                        app.logger.info("批量同步%s", sql)
                        cursor.execute(sql)


                    except:
                        # 如果发生错误则回滚
                        # traceback.print_exc()
                        db.rollback()
                        # 关闭数据库连接
                        db.close()
                        return jsonify(
                            common.falseReturn("", "同步失败", addition={"error_sql": sql, "error_datas": i}))

                    db.commit()
                    app.logger.info('%d/%d done', tail, len(sync_data_final_update))

                db.close()
                cache.clear()
                insert_installed_datas = [] # 需要新增到数据库的数据
                for j in installed_datas:
                    if j.get("qrcode") in global_id_not_in_db_list:
                        insert_installed_datas.append(j)
                for i in insert_installed_datas:

                    if request_json.get('projects_index'):
                        projects_index = request_json.get('projects_index')
                        if type(projects_index) != int:
                            projects_index = int(projects_index)
                            # contract_batch = '没有填写'
                    else:
                        projects_index = common.format_ymd_time_now_for_filename()
                        # return jsonify(common.falseReturn("", msg="没有传入projects_index"))

                    filename = '没有填写' + "_" + common.format_ymd_time_now()
                    # filename = '没有填写'
                    data_map = {"global_id": i.get("qrcode"), "installed_by": installed_by,
                                "installed_date": i.get("installed_date"),
                                "installed_coordinate": i.get("installed_coordinate"), "installed": 1}

                    # status, msg, update_date, update_num = upload_order.insert_data(filename=filename,
                    #                                                                  contract_batch=contract_batch,
                    #                                                                  order_batch=order_batch,
                    #                                                                  db_name=db_name,
                    #                                                                  db_table_name=dp_table,
                    #                                                                  uploaded_by=installed_by,
                    #                                                                 data_map=data_map)

                    if "collected" not in data_map.keys():
                        data_map["collected"] = 1
                    if "dp_nail_style" not in data_map.keys():
                        if i.get("dp_nail_style"):
                            data_map["dp_nail_style"] = i.get("dp_nail_style")
                    status, msg, update_date, update_num = upload_order.insert_data(filename=filename,
                                                                                    projects_index=projects_index,
                                                                                    db_name=db_name,
                                                                                    db_table_name=dp_table,
                                                                                    uploaded_by=installed_by,
                                                                                    data_map=data_map)

                    # contract_batch = '没有填写' + "_" + common.format_ymd_time_now()
                    # # contract_batch = '没有填写'
                    # order_batch = '没有填写' + "_" + common.format_ymd_time_now()
                    # # order_batch = '没有填写'
                    # filename = '没有填写' + "_" + common.format_ymd_time_now()
                    # # filename = '没有填写'
                    # data_map = {"global_id": i.get("qrcode"), "installed_by": installed_by,
                    #             "installed_date": i.get("installed_date"), "installed_coordinate": i.get("installed_coordinate"), "installed": 1}
                    # status, msg, update_date, update_num = upload_order.insert_data(filename=filename,
                    #                                                                 contract_batch=contract_batch,
                    #                                                                 order_batch=order_batch,
                    #                                                                 db_name=db_name,
                    #                                                                 db_table_name=dp_table,
                    #                                                                 uploaded_by=installed_by,
                    #                                                                 data_map=data_map)
                    if status:
                        app.logger.info("global_id: %s 新增到数据库 %s", qrcode, dp_table)
                cache.clear()
                return jsonify(common.trueReturn(sync_data, "同步成功",
                                                 addition={"global_id_not_in_db_list": global_id_not_in_db_list}))

            elif request_type == REQUEST_TYPE.update_data.name:
                '''2019-06-25 version 0.1'''
                app.logger.info("修改数据")
                request_form = request.get_json()
                type = request_form.get('type')
                try:
                    data_city = request_form.get('city')
                    if not CITY.has_key(data_city):
                        return jsonify(common.falseReturn("", "接口请求有问题！前端人员检查传参有无错误"))
                    # data_type = request_form.get('data_type')
                    data_index = request_form.get('index')
                    update_data_map = list(
                        request_form.get('update_data_map'))  # 一个数组map，每一项为i， i[0]为字段名, i[1]为修改的值
                    update_by = request_form.get('update_by')  # 修改人
                    update_date = common.format_ymdhms_time_now()  # 修改时间为现在
                    global_id = ''
                    if request_form.get('global_id'):
                        global_id = request_form.get('global_id')
                    # check_type = request_form.get('check')

                    app.logger.info("要修改的数据的城市是: %s  index: %s  update_data_map: %s", data_city, data_index,
                                    update_data_map)

                    db_name = CITY.get_db_name(data_city)
                    table_name = CITY.get_table_name(data_city)
                    db = pymysql.connect("localhost", "root", "root", db_name)
                    cursor = db.cursor()

                    # 修改数据前先把数据copy一份
                    # table_name+"_history" 是历史表
                    insert_sql = "INSERT INTO " + table_name + "_history " + " SELECT * FROM " + table_name + " WHERE `index`=" + str(
                        data_index)
                    app.logger.info(insert_sql)
                    cursor.execute(insert_sql)
                    db.commit()

                    if update_data_map:
                        set_sql = ""
                        for i, j in enumerate(update_data_map):
                            # if i == 0:
                            #     set_sql = " SET `" + j[0] + "`=\'" + j[1] + "\'"
                            # else:
                            #     set_sql += " , `" + j[0] + "`=\'" + j[1] + "\'"
                            if j[1]:
                                set_sql += " , `" + j[0] + "`=\'" + j[1] + "\'"
                    update_sql = "UPDATE " + table_name + " SET `update_date`=\'" + update_date + "\' , `update_by`=\'" + update_by + "\' " + set_sql + " WHERE " + " `index`=" + str(
                        data_index)
                    app.logger.info(update_sql)
                    cursor.execute(update_sql)
                    db.commit()
                    db.close()
                    # app.logger.info(update_sql)
                    cache.clear()
                    return jsonify(common.trueReturn("", "数据修改成功!"))

                except:
                    db.close()
                    app.logger.info("数据修改不成功，检查传参有无错误")
                    # app.logger.info(update_sql)
                    return jsonify(common.falseReturn("", "数据修改不成功，让前端人员检查传参有无错误"))

            elif request_type == REQUEST_TYPE.qrcode_classification.name:
                '''
                2019-11-06
                目前只针对fs_dp
                '''
                app.logger.info("qrcode_classification 数据")
                request_form = request.get_json()
                try:
                    data_city = request_form.get('city')
                    if not CITY.has_key(data_city):
                        return jsonify(common.falseReturn("", "接口请求有问题！前端人员检查传参city有无错误"))
                    update_date = common.format_ymdhms_time_now()  # 修改时间为现在
                    global_id = ''
                    if request_form.get('global_id'):
                        global_id = request_form.get('global_id')
                    else:
                        return jsonify(common.falseReturn("", "接口请求有问题！前端人员检查传参global_id有无错误"))
                    if request_form.get('classification'):
                        classification = request_form.get('classification')
                    else:
                        classification = "未填写"
                    app.logger.info("要标记的数据的城市是: %s  global_id: %s  qrcode_classification: %s", data_city, global_id, classification)
                    

                    db_name = CITY.get_db_name(data_city)
                    table_name = CITY.get_table_name(data_city)
                    db = pymysql.connect("localhost", "root", "root", db_name)
                    cursor = db.cursor()

                    update_sql = "UPDATE " + table_name + " SET `地址编码状态`=\'" + classification + "\' WHERE " + " `global_id`=\'" + str(
                        global_id) + "\'"

                    app.logger.info(update_sql)
                    cursor.execute(update_sql)
                    db.commit()
                    db.close()
                    # app.logger.info(update_sql)
                    cache.clear()
                    return jsonify(common.trueReturn("", "数据标记成功!"))

                except:
                    db.close()
                    app.logger.info("数据标记不成功，检查传参有无错误")
                    # app.logger.info(update_sql)
                    return jsonify(common.falseReturn("", "数据标记不成功，让前端人员检查传参有无错误"))

            else:
                return jsonify(common.falseReturn("", "接口请求有问题！前端人员检查传参有无错误"))


        elif request.method == 'POST':
            type = request.form.get("type")
            if not type:
                type = request.json.get("type")
            if type == REQUEST_TYPE.city_name.name:
                if request.form.get("city"):
                    city = request.form.get("city")
                else:
                    return jsonify(common.falseReturn("", "city参数有问题！"))
                if request.form.get("city_name_chinese"):
                    city_name_chinese = request.form.get("city_name_chinese")
                else:
                    return jsonify(common.falseReturn("", "city_name_chinese参数有问题！"))
                app.logger.info("新建的城市 %s %s", city, city_name_chinese)


                if CITY.has_key(city):
                    return jsonify(common.falseReturn("", "新建城市数据库出错，已经存在该名字的数据表！", addition=common.false_Type.exist))

                insert_status, city_name_list, city_name_map = mysql.insert_city(city=city,
                                                                                 city_name_chinese=city_name_chinese)
                if insert_status:
                    cache.clear()
                    return jsonify(
                        common.trueReturn({"city_name_list": city_name_list, "city_name_map": city_name_map},
                                          "新建成功"))
                else:
                    return jsonify(common.falseReturn("", "新建城市数据库出错！"))

            #新增采集门牌数据接口
            elif type == REQUEST_TYPE.collected_doorplate.name:


                contract_batch = '没有填写' + "_" + common.format_ymd_time_now()
                # contract_batch = '没有填写'
                order_batch = '没有填写' + "_" + common.format_ymd_time_now()
                # order_batch = '没有填写'
                from_filename = '没有填写' + "_" + common.format_ymd_time_now()
                # filename = '没有填写'
                city = request.json.get("city")
                data_map = request.json.get("data_map")
                db_name = CITY.get_db_name(city)
                table_name = CITY.get_table_name(city)
                if data_map.get("projects_index"):
                    projects_index = data_map.get("projects_index")
                else:
                    if request_json.get('projects_index'):
                        projects_index = request_json.get('projects_index')
                        if type(projects_index) != int:
                            projects_index = int(projects_index)
                            # contract_batch = '没有填写'
                    else:
                        projects_index = common.format_ymd_time_now_for_filename()
                        # return jsonify(common.falseReturn("", msg="没有传入projects_index"))

                if data_map.get("collected_by"):
                    uploaded_by = data_map.get("collected_by")
                else:
                    uploaded_by = "没有填写"

                if request.json.get("force") == 1 or request.json.get("force") == "1":
                    pass
                else:
                    select_sql_head = " select max(`index`) from " + table_name + " where "
                    select_sql_tail = ""
                    for key, value in data_map.items():
                        if key.find("collected") >= 0 or key.find("date") >= 0:
                            pass
                        else:
                            if not select_sql_tail:
                                select_sql_tail = key + "=\"{" + key +"}\""
                            else:
                                select_sql_tail += " and  " + key + "=\"{" + key +"}\""

                    select_sql = select_sql_head + select_sql_tail
                    select_sql = select_sql.format(**data_map)
                    app.logger.info(select_sql)
                    result = mysql.select_by_sql(db_name, select_sql, need_transform=False)
                    if not result[0][0]:
                        pass
                    else:
                        return jsonify(
                            common.falseReturn({"index": result[0][0]},
                                              "门牌数据已经存在, 用index直接进行之后的操作", addition=common.false_Type.exist))

                if "collected" not in data_map.keys():
                    data_map["collected"] = 1

                status, msg, update_date, update_num = upload_order.insert_data(filename=from_filename,
                                                                                projects_index=projects_index,
                                                                                db_name=db_name,
                                                                                db_table_name=table_name,
                                                                                uploaded_by=uploaded_by,
                                                                                data_map=data_map)
                # status, msg, update_date, update_num = upload_order.insert_data(filename=from_filename,
                #                                                                 contract_batch=contract_batch,
                #                                                                 order_batch=order_batch,
                #                                                                 db_name=db_name,
                #                                                                 db_table_name=table_name,
                #                                                                 uploaded_by=uploaded_by,
                #



                # 2019-09-30
                # select_sql = " select max(`index`) from " + table_name + " where uploaded_by=\"{uploaded_by}\" and from_filename=\"{from_filename}\" "
                # select_sql = select_sql.format(uploaded_by=uploaded_by,
                #                                 from_filename=from_filename)
                # result = mysql.select_by_sql(db_name, select_sql, need_transform=False)

                select_status, addition_msg, time_now, result = mysql.select_data(db_name, table_name, data_map, ["index"])
                #print("resultresultresultresult", result)
                insert_data_index = result[0][0]
                #
                # upload_status, upload_path = pictures_operation.upload_picture(save_dir, f, filename)
                #
                #
                #
                # if not upload_status:
                #     msg = '已经有与filename相同命名的照片，' + filename
                #     app.logger.info(msg)

                if status:
                    app.logger.info("index: %s: 新增到数据库: %s \n data_map: %s", str(insert_data_index), table_name, data_map)
                    cache.clear()
                    return jsonify(
                        common.trueReturn({"index": insert_data_index},
                                          "新建成功"))
                else:
                    return jsonify(common.falseReturn("", "新建数据出错！"))

        # elif request.method == 'PUT':
        #     request_type = request_json.get('type')
        #     if request_type == REQUEST_TYPE.installed.name:
        #         app.logger.info("登记安装")
        #         db_name = 'ws_doorplate'
        #         table_name = 'gz_orders'
        #         if request.args.get('city'):
        #             db_name = CITY.get_db_name(request.args.get('city'))
        #             table_name = CITY.get_table_name(request.args.get('city'))
        #
        #         db = pymysql.connect("localhost", "root", "root", db_name)
        #         #db = pymysql.connect("localhost", "root", "root", database_name)
        #         #db = pymysql.connect("localhost", "root", "root", "ws_doorplate")
        #         #     # 使用cursor()方法获取操作游标
        #         cursor = db.cursor()
        #         # app.logger.info(request_json.get('qrcode'))
        #         # app.logger.info(request_json.get('installed_by'))
        #         # app.logger.info(request_json.get('installed_coordinate'))
        #         qrcode = request_json.get('qrcode')
        #         installed_by = request_json.get('installed_by')
        #         installed_coordinate = request_json.get('installed_coordinate')
        #
        #         #select_sql = "SELECT `index` FROM gz_orders WHERE `global_id` = " + "\'" + qrcode + "\'" + " LIMIT 1"
        #         select_sql = "SELECT `index` FROM " + table_name + " WHERE `global_id` = " + "\'" + qrcode + "\'" + " LIMIT 1"
        #
        #         if select_sql:
        #             try:
        #                 # app.logger.info(select_sql)
        #                 cursor.execute(select_sql)
        #                 # app.logger.info(cursor.fetchall())
        #                 if cursor.fetchall():
        #                     pass
        #                 else:
        #                     # 提交到数据库执行
        #                     db.commit()
        #                     # 关闭数据库连接
        #                     db.close()
        #                     return jsonify(common.falseReturn("", "上传失败，检查global_id有无错误"))
        #             except:
        #                 # 如果发生错误则回滚
        #                 # traceback.print_exc()
        #                 db.rollback()
        #                 # 关闭数据库连接
        #                 db.close()
        #                 return jsonify(common.falseReturn("", "上传失败"))
        #
        #         sql = "UPDATE " + table_name + " SET `installed`=`installed`+1 " + \
        #               ", `installed_by` = " + "\'" + installed_by + "\'" + \
        #               ", `installed_coordinate` = " + "\'" + installed_coordinate + "\'" + \
        #               ", `installed_date` = " + "\'" + datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S') + "\'" + \
        #               " WHERE `global_id` = " + "\'" + qrcode + "\'"
        #
        #
        #         if sql:
        #             try:
        #                 app.logger.info(sql)
        #                 cursor.execute(sql)
        #                 # app.logger.info(cursor.fetchall())
        #                 # 提交到数据库执行
        #                 db.commit()
        #                 # 关闭数据库连接
        #                 db.close()
        #                 return jsonify(common.trueReturn("", "上传成功"))
        #             except:
        #                 # 如果发生错误则回滚
        #                 # traceback.print_exc()
        #                 db.rollback()
        #                 # 关闭数据库连接
        #                 db.close()
        #                 return jsonify(common.falseReturn("", "上传失败"))

    @app.route('/excel', methods=['GET', 'POST'])
    def excel():
        app.logger.info("request: %s", request)
        result = Auth.identify(Auth, request)
        username_now = "unknown"
        app.logger.info("状态: %s 用户: %s ", result.get('status'),  result.get('data'))
        if (result['status'] and result['data']):
            #app.logger.info(result)
            username_now = result['data']['username']
        else:
            return json.dumps(result, ensure_ascii=False)

        if request.method == 'GET':
            if request.args.get('type') == EXCEL_TYPE.templates.name:
                templates_files = os.listdir(config.DY_DATAS_TEMPLATES_PATH)
                templates_files_map = {}
                for file in templates_files:
                    templates_files_map[file] = os.path.join(config.DY_DATAS_TEMPLATES_PATH, file)
                return jsonify(common.trueReturn({"templates": templates_files_map}, msg='excel模板'))
            else:
                return jsonify(common.falseReturn("", msg='type有问题'))

        if request.method == 'POST':

            # db_name = "ws_doorplate"
            # db_table_name = "gz_orders"
            if request.form.get('city'):
                db_name = CITY.get_db_name(request.form.get('city'))
                db_table_name = CITY.get_table_name(request.form.get('city'))
                city = request.form.get('city')
            else:
                # 此处预计抛弃
                if request.form.get('db_name'):
                    db_name = request.form.get('db_name')
                else:
                    db_name = 'ws_doorplate'
                if request.form.get('db_table_name'):
                    db_table_name = request.form.get('db_table_name')
                else:
                    db_table_name = 'gz_orders'

            # 获取门牌类型
            if request.form.get('need_dp_type'):
                need_dp_type = request.form.get('need_dp_type')
            else:
                need_dp_type = ''

            # 获取是否标记生产单
            if request.form.get('need_mark_produce'):
                if str(request.form.get('need_mark_produce')).lower() == "false":
                    need_mark_produce = ''
                else:
                    need_mark_produce = request.form.get('need_mark_produce')
            else:
                need_mark_produce = ''

            if request.form.get('type') != EXCEL_TYPE.produced_with_query_without_excel.name:
                app.logger.info("有文件要上传")
                # 保存上传的文件
                app.logger.info(request.files)
                if 'file' not in request.files:
                    resp = Response(str([{'index': '未上传文件'}]))
                    resp.mimetype = 'application/json'
                    resp.headers['x-total-count'] = 1
                    resp.headers['access-control-expose-headers'] = 'X-Total-Count'
                    return resp
                f = request.files['file']
                # basepath = os.path.dirname(__file__)  # 当前文件所在路径
                # app.logger.info(basepath)
                # basepath = "/home/dy_server/doorplates_server/temp_datas"
                # app.logger.info(basepath)

                temp_file = tempfile.TemporaryFile()
                # app.logger.info(tempfile)

                f.save(temp_file)

                temp_file.seek(0)
                upload_file_MD5 = get_MD5.GetFileMd5_from_file(temp_file)
                app.logger.info("upload_file_MD5: %s", upload_file_MD5)
                filename = secure_filename(f.filename)
                filename_pre, filename_suffix = os.path.splitext(filename)
                upload_path = os.path.join(basepath + '/uploads', filename)
                need_save = 1
                sum = 0
                while (os.path.isfile(os.path.join(basepath + '/uploads', filename))):  # 入参需要是绝对路径
                    # temp_MD5 = get_MD5.GetFileMd5(dydatas_basepath + '/gd_dp_photos/' + city + "/" + filename)
                    temp_MD5 = get_MD5.GetFileMd5(os.path.join(basepath + '/uploads', filename))
                    app.logger.info("temp_MD5: %s", temp_MD5)
                    if upload_file_MD5 != temp_MD5:
                        sum += 1
                        filename = filename_pre + "_" + str(sum) + '.' + filename_suffix
                    else:
                        need_save = 0
                        app.logger.info('本地已经有相同文件了: %s', upload_path)
                        break

                # excel_name += '.xls'
                upload_path = os.path.join(basepath + '/uploads', filename)

                upload_file_savename = filename

                if need_save:
                    f.stream.seek(0)
                    f.save(upload_path)
                    app.logger.info("文件保存在：%s", upload_path)
                #
                # filename = secure_filename(f.filename)
                # # filename_pre = filename.split('.')[0]
                # # filename_suffix = filename.split('.')[1]
                # filename_pre, filename_suffix = os.path.splitext(filename)
                # filename = filename_pre + '_' + str(time.time()) + '.' + filename_suffix
                # # 注意：没有的文件夹一定要先创建，不然会提示没有该路径
                # upload_path = os.path.join(basepath + '/uploads', filename)
                # app.logger.info("文件保存在：%s", upload_path)
                # f.save(upload_path)

            # 通过上传的文件直接生成生产单，不检索
            if request.form.get('type') == EXCEL_TYPE.produced_without_query.name:
                # f = request.files['file']
                # f = request.files.get('file')





                produce_excel_path, result_datas, result_col_name_index_map = export_excel.export(upload_path,
                                                                                                  city=city,
                                                                                                  filename=filename,
                                                                                                  need_dp_type=need_dp_type,
                                                                                                  need_order_batch=True,
                                                                                                  need_order_id=True)

                app.logger.info("produce_excel_path: %s", produce_excel_path)

                deliver_excel_path, deliver_result_datas, deliver_result_col_name_index_map = deliver_excel.export(upload_path,
                                                                                                                  city=city,
                                                                                                                  filename=filename,
                                                                                                                  need_dp_type=need_dp_type,
                                                                                                                  need_order_batch=True,
                                                                                                                  need_order_id=True)

                app.logger.info("deliver_excel_path: %s", deliver_excel_path)

                receive_excel_path, receive_result_datas, receive_result_col_name_index_map = receive_excel.export(
                    upload_path,
                    city=city,
                    filename=filename,
                    need_dp_type=need_dp_type,
                    need_order_batch=True,
                    need_order_id=True)

                app.logger.info("receive_excel_path: %s", receive_excel_path)

                #produce_excel_path, result_datas, result_col_name_index_map = export_excel.export(upload_path, filename=filename)
                #app.logger.info(result_datas)

                #global_id_from_upload_datas = [i[result_col_name_index_map['global_id']] for i in result_datas]
                #dp_id_from_upload_datas = [i[result_col_name_index_map['dp_id']] for i in result_datas]
                dp_id_from_upload_datas = []
                if 'dp_id' in result_col_name_index_map.keys():
                    for i in result_datas:
                        if i[result_col_name_index_map['dp_id']]:
                            dp_id_from_upload_datas.append(i[result_col_name_index_map['dp_id']])
                global_id_from_upload_datas = []
                for i in result_datas:
                    if i[result_col_name_index_map['global_id']]:
                        global_id_from_upload_datas.append(i[result_col_name_index_map['global_id']])
                #app.logger.info(dp_id_from_query_datas)
                # if mysql.update_exported_produce(db_name, db_table_name, by_who=username_now, global_id_list=global_id_from_upload_datas):

                if need_mark_produce != '':
                    if mysql.update_exported_produce(db_name, db_table_name, by_who=username_now,
                                                     dp_id_list=dp_id_from_upload_datas, global_id_list=global_id_from_upload_datas):
                        pass
                    else:
                        return common.falseReturn("", "数据库更新导出生产信息失败，联系后台人员",
                                                  addition=common.false_Type.export_produce_false)

                # results.append({'produce_excel_url': produce_excel_path})
                # app.logger.info(produce_excel_path)

                #jsonStr = json.dumps({'produce_excel_url': produce_excel_path}, ensure_ascii=False)

                jsonStr = json.dumps((common.trueReturn({"produce_excel_url": produce_excel_path,
                                                         "deliver_excel_url": deliver_excel_path,
                                                         "receive_excel_url": receive_excel_path},
                                                        "produce_excel_url为生产单下载url, deliver_excel_url为送货单, receive_excel_url为确认单")),
                                     ensure_ascii=False,
                                     indent=1)
                # app.logger.info(jsonStr)
                resp = Response(jsonStr)
                resp.mimetype = 'application/json'
                resp.headers['x-total-count'] = 0  # 减去query_excel_path占用的一个
                resp.headers['access-control-expose-headers'] = 'X-Total-Count'
                resp.content_type = 'application/json'

                # return '成功上传'
                cache.clear()
                return resp

            # 上传订单更新数据
            elif request.form.get('type') == EXCEL_TYPE.order.name:

                if request.form.get('projects_index'):
                    projects_index = request.form.get('projects_index')
                    if type(projects_index) != int:
                        projects_index = int(projects_index)
                        #contract_batch = '没有填写'
                else:
                    return jsonify(common.falseReturn("", msg="没有传入projects_index"))
                app.logger.info("projects_index %s", projects_index)

                if request.form.get('filename'):
                    filename = request.form.get('filename')
                    if filename == '没有填写':
                        filename = '没有填写' + "_" + common.format_ymd_time_now()
                        #filename = '没有填写'
                else:
                    try:
                        #filename = secure_filename(f.filename)
                        filename = str(f.filename)
                    except:
                        filename = '没有填写' + "_" + common.format_ymd_time_now()
                        #filename = '没有填写'

                if db_table_name == "gz_orders" or db_table_name == "shenzhen_dp":
                    global_id_has_NULL_status = upload_order.global_id_has_NULL(upload_path)
                    if not global_id_has_NULL_status: # global_id 有空的
                        app.logger.info("upload_path %s，中没有全球唯一码列或者全球唯一码为空", upload_path)
                        return jsonify(common.falseReturn('', msg="上传的订单全球唯一码有空的！", addition=common.false_Type.global_id_false))

                status, msg, update_date, update_num = upload_order.insert_datas(upload_path, filename=filename, projects_index=projects_index, db_name=db_name, db_table_name=db_table_name, uploaded_by=username_now)
                if status:

                    log_path = config.DY_DATAS_LOG_PATH

                    log_file_path = os.path.join(log_path, "excel_order_update_log.txt")
                    with open(log_file_path, 'a+') as f:
                        f.write('----------\n')
                        temp_str = update_date + '\n数据库: ' + db_name + '\n表: ' + db_table_name + '\n项目ID: ' + str(projects_index) + '\n上传文件保存名: ' + upload_file_savename + '\n格式化文件名' + filename + '\n更新了:' + update_num
                        f.write(temp_str)
                        #f.write('\n----------')
                        f.write('\n')
                        #f.write(update_date)
                    cache.clear()
                    long_time_cache.clear()
                    return jsonify(common.trueReturn({"update_date": update_date}, msg=msg))
                else:
                    return jsonify(common.falseReturn('', msg=msg))


            # 只检索
            elif request.form.get('type') == EXCEL_TYPE.query.name:
                app.logger.info(request.form.get('col_needed'))
                if request.form.get("city"):
                    city = request.form.get("city")
                else:
                    city = "guangzhou"
                if request.form.get('col_needed'):
                    col_name_needed_list = list(request.form.get('col_needed').split(','))
                    if not city == "guangzhou" and 'community' not in col_name_needed_list:
                        col_name_needed_list.append('community')
                else:

                    col_name_needed_list = ['contract_batch', 'order_batch', 'order_id', 'pcs', 'community', 'street', 'dp_num', 'dp_num_trans', 'dp_name', 'dp_id',
                                            'global_id_with_dp_name', 'dp_type', 'dp_size', 'global_id', 'exported_produce']
                    # col_name_needed_list = ['pcs', 'street', 'dp_num', 'dp_num_trans',
                    #                                                 'dp_name', 'dp_id', \
                    #                                                 'global_id_with_dp_name', 'dp_type', 'dp_size',
                    #                                                 'global_id']

                if city == "guangzhou":
                #if city != "maoming" and city != "foshan":
                    results, query_excel_path = query.query(upload_path, col_name_needed_list=col_name_needed_list, db_name = db_name, db_table_name = db_table_name, city=city)
                    #results.append({'query_excel_url': query_excel_path})
                    # results.append({'produce_excel_url': produce_excel_path})
                    # app.logger.info(produce_excel_path)

                    #jsonStr = json.dumps(results, ensure_ascii=False)
                    jsonStr = json.dumps((common.trueReturn({"doorplates": results, "query_excel_url": query_excel_path},
                                                            "query_excel_path为检索结果excel下载url")),
                                         ensure_ascii=False,
                                         indent=1)

                    # app.logger.info(jsonStr)
                    resp = Response(jsonStr)
                    resp.mimetype = 'application/json'
                    resp.headers['x-total-count'] = len(results)
                    resp.headers['access-control-expose-headers'] = 'X-Total-Count'

                    # return '成功上传'
                    return resp
                else:
                    if request.form.get("col_name"):
                        col_name = request.form.get("col_name")
                    else:
                        col_name = "全球唯一码"
                    results, query_excel_path = query.query(upload_path, col_name_needed_list=col_name_needed_list,
                                                            db_name=db_name, db_table_name=db_table_name, city=city, col_name=col_name)
                    #results.append({'query_excel_url': query_excel_path})
                    # results.append({'produce_excel_url': produce_excel_path})
                    # app.logger.info(produce_excel_path)

                    #jsonStr = json.dumps(results, ensure_ascii=False)
                    jsonStr = json.dumps((common.trueReturn({"doorplates": results, "query_excel_url": query_excel_path},
                                           "query_excel_path为检索结果excel下载url")),
                                        ensure_ascii=False,
                                        indent=1)

                    # app.logger.info(jsonStr)
                    resp = Response(jsonStr)
                    resp.mimetype = 'application/json'
                    resp.headers['x-total-count'] = len(results)
                    resp.headers['access-control-expose-headers'] = 'X-Total-Count'
                    resp.content_type = 'application/json'
                    # return '成功上传'
                    return resp


            # 检索并生成生产单
            elif request.form.get('type') == EXCEL_TYPE.produced_with_query.name:
                # f = request.files['file']
                # f = request.files.get('file')
                if request.form.get("city"):
                    city = request.form.get("city")
                else:
                    city = "guangzhou"

                #col_name_needed_list = ['street', 'dp_num', 'dp_num_trans', 'dp_name', 'global_id', 'global_id_with_dp_name', 'pcs']
                app.logger.info(request.form.get('col_needed'))
                if request.form.get('col_needed'):
                    col_name_needed_list = list(request.form.get('col_needed').split(','))
                    if request.form.get('col_needed'):
                        col_name_needed_list = list(request.form.get('col_needed').split(','))
                        if not city == "guangzhou" and 'community' not in col_name_needed_list:
                            col_name_needed_list.append('community')
                else:
                    col_name_needed_list = ['contract_batch', 'order_batch', 'order_id', 'community', 'pcs', 'street', 'dp_num', 'dp_num_trans',
                                            'dp_name', 'dp_id',
                                            'global_id_with_dp_name', 'dp_type', 'dp_size', 'global_id', 'exported_produce']
                    # col_name_needed_list = ['pcs', 'street', 'dp_num', 'dp_num_trans', 'dp_name', 'dp_id',  \
                    #                     'global_id_with_dp_name', 'dp_type', 'dp_size', 'global_id', 'exported_produce']
                if 'exported_produce' not in col_name_needed_list:
                    col_name_needed_list.append('exported_produce')
                # 上传成功后 查询excel
                results, query_excel_path = query.query(upload_path, col_name_needed_list = col_name_needed_list, db_name = db_name, db_table_name = db_table_name, city=city)


                if not results:
                    #results.append({'query_excel_url': query_excel_path, 'produce_excel_url': ""})
                    # results.append({'produce_excel_url': produce_excel_path})
                    # app.logger.info(produce_excel_path)

                    #jsonStr = json.dumps(results, ensure_ascii=False)
                    jsonStr = json.dumps(
                        (common.trueReturn({"doorplates": results,
                                            "query_excel_url": query_excel_path,
                                            "produce_excel_url": "",
                                            "deliver_excel_url": "",
                                            "receive_excel_url": ""},
                                           "query_excel_path为检索结果excel下载url, produce_excel_url为生产单下载url, deliver_excel_url为送货单, receive_excel_url为确认单")),
                        ensure_ascii=False,
                        indent=1)
                    # app.logger.info(jsonStr)
                    resp = Response(jsonStr)
                    resp.mimetype = 'application/json'
                    resp.headers['x-total-count'] = 1
                    resp.headers['access-control-expose-headers'] = 'X-Total-Count'
                    resp.content_type = 'application/json'
                else:

                    produce_excel_path, datas_list, col_name_index_map = export_excel.export(query_excel_path,
                                                                                             city=city,
                                                                                             filename=filename,
                                                                                             need_dp_type=need_dp_type,
                                                                                             need_order_batch=True,
                                                                                             need_order_id=True)
                    app.logger.info("produce_excel_path: %s", produce_excel_path)
                    deliver_excel_path, deliver_result_datas, deliver_result_col_name_index_map = deliver_excel.export(
                        query_excel_path,
                        city=city,
                        filename=filename,
                        need_dp_type=need_dp_type,
                        need_order_batch=True,
                        need_order_id=True)

                    app.logger.info("deliver_excel_path: %s", deliver_excel_path)

                    receive_excel_path, receive_result_datas, receive_result_col_name_index_map = receive_excel.export(
                        query_excel_path,
                        city=city,
                        filename=filename,
                        need_dp_type=need_dp_type,
                        need_order_batch=True,
                        need_order_id=True)

                    app.logger.info("receive_excel_path: %s", receive_excel_path)

                    #global_id_from_query_datas = [i['global_id'] for i in results]
                    #dp_id_from_query_datas = [i['dp_id'] for i in results]
                    dp_id_from_query_datas = []
                    global_id_from_upload_datas = []
                    for i in results:
                        if city == "guangzhou":
                            if i['dp_id']:
                                dp_id_from_query_datas.append(i['dp_id'])
                        if i['global_id']:
                            global_id_from_upload_datas.append(i['global_id'])

                    if need_mark_produce != '':
                        #if mysql.update_exported_produce(db_name, db_table_name, by_who=username_now, global_id_list=global_id_from_query_datas):
                        if mysql.update_exported_produce(db_name, db_table_name, by_who=username_now,
                                                         dp_id_list=dp_id_from_query_datas, global_id_list=global_id_from_upload_datas):
                            pass
                        else:
                            return common.falseReturn("", "数据库更新导出生产信息失败，联系后台人员", addition=common.false_Type.export_produce_false)


                    #results.append({'query_excel_url': query_excel_path, 'produce_excel_url': produce_excel_path})
                    #results.append({'produce_excel_url': produce_excel_path})
                    #app.logger.info(produce_excel_path)

                    #jsonStr = json.dumps(results, ensure_ascii=False)
                    jsonStr = json.dumps(
                        (common.trueReturn({"doorplates": results,
                                            "query_excel_url": query_excel_path,
                                            "produce_excel_url": produce_excel_path,
                                            "deliver_excel_url": deliver_excel_path,
                                            "receive_excel_url": receive_excel_path},
                                           "query_excel_path为检索结果excel下载url, produce_excel_url为生产单下载url, deliver_excel_url为送货单, receive_excel_url为确认单")),
                        ensure_ascii=False,
                        indent=1)
                    # app.logger.info(jsonStr)
                    resp = Response(jsonStr)
                    resp.mimetype = 'application/json'
                    resp.headers['x-total-count'] = len(results)
                    resp.headers['access-control-expose-headers'] = 'X-Total-Count'
                    resp.content_type = 'application/json'

                # return '成功上传'
                cache.clear()
                return resp
            # 通过传送json格式的body，带有需要生成生产单数据的index
            elif request.form.get('type') == EXCEL_TYPE.produced_with_query_without_excel.name:
                app.logger.info("通过前端传入数据index列表生成生产单")

                if request.get_json():
                    request_data = request.get_json()
                else:
                    request_data = request.form

                # print("request.form.get('pictures_filename_list')",request_data.get('pictures_filename_list'))

                if request_data.get("need_all_data") != "" and request_data.get("need_all_data") is not None:
                    data, count = query_datas(request, db_name, db_table_name, ["index"])
                    if count == 0:
                        app.logger.info("没有相关筛选的数据")
                        # results.append({'query_excel_url': query_excel_path, 'produce_excel_url': produce_excel_path})
                        jsonStr = json.dumps((common.trueReturn({"doorplates": [{"dp_name": "没有相关筛选的数据"}],
                                                                 "query_excel_url": "",
                                                                 "produce_excel_url": "",
                                                                 "deliver_excel_url": "",
                                                                 "receive_excel_url": ""},
                                                                "query_excel_path为检索结果excel下载url, produce_excel_url为生产单下载url, deliver_excel_url为送货单, receive_excel_url为确认单")),
                                             ensure_ascii=False,
                                             indent=1)
                        resp = Response(jsonStr)
                        resp.mimetype = 'application/json'
                        resp.headers['x-total-count'] = 1
                        resp.headers['access-control-expose-headers'] = 'X-Total-Count'
                        resp.content_type = 'application/json'
                        return resp
                    #print(data)
                    doorplates_index_list = [i["index"] for i in data]
                else:
                    doorplates_index_list = request_data.get('doorplates_index_list').split(',')
                # print("pictures_filename_list",pictures_filename_list)
                if request_data.get("city"):
                    city = request.form.get("city")
                else:
                    return common.falseReturn({},"没有传入city")
                if not CITY.has_key(city):
                    return common.falseReturn({}, "传入的city值不正确")

                app.logger.info("要生成生产单的数据为: %s", doorplates_index_list)
                doorplates_num = len(doorplates_index_list)
                app.logger.info("数量为：%s", doorplates_num)


                # col_name_needed_list = ['street', 'dp_num', 'dp_num_trans', 'dp_name', 'global_id', 'global_id_with_dp_name', 'pcs']
                app.logger.info(request.form.get('col_needed'))
                if request.form.get('col_needed'):
                    col_name_needed_list = list(request.form.get('col_needed').split(','))
                    if request.form.get('col_needed'):
                        col_name_needed_list = list(request.form.get('col_needed').split(','))
                        if not city == "guangzhou" and 'community' not in col_name_needed_list:
                            col_name_needed_list.append('community')
                else:
                    col_name_needed_list = ['contract_batch', 'order_batch', 'order_id','community', 'pcs', 'street', 'dp_num',
                                            'dp_num_trans',
                                            'dp_name', 'dp_id',
                                            'global_id_with_dp_name', 'dp_type', 'dp_size', 'global_id',
                                            'exported_produce']
                    # col_name_needed_list = ['pcs', 'street', 'dp_num', 'dp_num_trans', 'dp_name', 'dp_id',  \
                    #                     'global_id_with_dp_name', 'dp_type', 'dp_size', 'global_id', 'exported_produce']
                if 'exported_produce' not in col_name_needed_list:
                    col_name_needed_list.append('exported_produce')
                # 上传成功后 查询excel
                file_save_path = config.TEMP_DOWNLOAD_DATAS_PATH
                if file_save_path != os.sep:
                    file_save_path += os.sep
                results, query_excel_path = query.query(file_save_path, col_name_needed_list=col_name_needed_list,
                                                        db_name=db_name, db_table_name=db_table_name, city=city, index_list=doorplates_index_list)

                if not results:
                    #results.append({'query_excel_url': query_excel_path, 'produce_excel_url': ""})

                    # results.append({'produce_excel_url': produce_excel_path})
                    # app.logger.info(produce_excel_path)

                    #jsonStr = json.dumps(results, ensure_ascii=False)
                    jsonStr = json.dumps(
                        (common.trueReturn({"doorplates": results,
                                            "query_excel_url": query_excel_path,
                                            "produce_excel_url": "",
                                            "deliver_excel_url": "",
                                            "receive_excel_url": ""},
                                           "query_excel_path为检索结果excel下载url, produce_excel_url为生产单下载url, deliver_excel_url为送货单, receive_excel_url为确认单")),
                        ensure_ascii=False,
                        indent=1)
                    # app.logger.info(jsonStr)
                    resp = Response(jsonStr)
                    resp.mimetype = 'application/json'
                    resp.headers['x-total-count'] = 1  # 减去query_excel_path占用的一个
                    resp.headers['access-control-expose-headers'] = 'X-Total-Count'
                else:

                    #filename = "网页选择数据生产单_" + common.format_ymdhms_time_now_for_filename()
                    filename = "网页选择数据生产单"
                    produce_excel_path, datas_list, col_name_index_map = export_excel.export(query_excel_path,
                                                                                             city=city,
                                                                                             filename=filename,
                                                                                             need_dp_type=need_dp_type,
                                                                                             need_order_batch=True,
                                                                                                need_order_id=True)

                    app.logger.info("produce_excel_path: %s", produce_excel_path)
                    deliver_excel_path, deliver_result_datas, deliver_result_col_name_index_map = deliver_excel.export(
                        query_excel_path,
                        city=city,
                        filename=filename,
                        need_dp_type=need_dp_type,
                        need_order_batch=True,
                        need_order_id=True)

                    app.logger.info("deliver_excel_path: %s", deliver_excel_path)

                    receive_excel_path, receive_result_datas, receive_result_col_name_index_map = receive_excel.export(
                        query_excel_path,
                        city=city,
                        filename=filename,
                        need_dp_type=need_dp_type,
                        need_order_batch=True,
                        need_order_id=True)

                    app.logger.info("receive_excel_path: %s", receive_excel_path)
                    # global_id_from_query_datas = [i['global_id'] for i in results]
                    # dp_id_from_query_datas = [i['dp_id'] for i in results]
                    dp_id_from_query_datas = []
                    global_id_from_upload_datas = []
                    for i in results:
                        if city == "guangzhou":
                            if i['dp_id']:
                                dp_id_from_query_datas.append(i['dp_id'])
                        if i['global_id']:
                            global_id_from_upload_datas.append(i['global_id'])
                    # if mysql.update_exported_produce(db_name, db_table_name, by_who=username_now, global_id_list=global_id_from_query_datas):

                    if need_mark_produce != '':
                        if mysql.update_exported_produce(db_name, db_table_name, by_who=username_now,
                                                         dp_id_list=dp_id_from_query_datas,
                                                         global_id_list=global_id_from_upload_datas):
                            pass
                        else:
                            return common.falseReturn("", "数据库更新导出生产信息失败，联系后台人员",
                                                      addition=common.false_Type.export_produce_false)

                    #results.append({'query_excel_url': query_excel_path, 'produce_excel_url': produce_excel_path})
                    jsonStr = json.dumps((common.trueReturn({"doorplates": results,
                                                    "query_excel_url": query_excel_path,
                                                    "produce_excel_url": produce_excel_path,
                                                   "deliver_excel_url": deliver_excel_path,
                                                    "receive_excel_url": receive_excel_path},
                                 "query_excel_path为检索结果excel下载url, produce_excel_url为生产单下载url, deliver_excel_url为送货单, receive_excel_url为确认单")),
                        ensure_ascii=False,
                        indent=1)
                    # results.append({'produce_excel_url': produce_excel_path})
                    # app.logger.info(produce_excel_path)

                    #jsonStr = json.dumps(results, ensure_ascii=False)
                    # app.logger.info(jsonStr)
                    resp = Response(jsonStr)
                    resp.mimetype = 'application/json'
                    resp.headers['x-total-count'] = len(results)
                    resp.headers['access-control-expose-headers'] = 'X-Total-Count'
                    resp.content_type = 'application/json'

                # return '成功上传'
                cache.clear()
                return resp
                # 通过传送json格式的body，带有需要生成生产单数据的index

        #resp = Response(str([{'index': '未上传文件，可能是请求有问题'}]))
        resp = Response(json.dumps(
                        (common.falseReturn({"doorplates": [{'index': '未上传文件，可能是请求有问题'}]},
                                           "未上传文件，可能是请求有问题")),
                        ensure_ascii=False,
                        indent=1))
        resp.mimetype = 'application/json'
        resp.headers['x-total-count'] = 1
        resp.headers['access-control-expose-headers'] = 'X-Total-Count'
        resp.content_type = 'application/json'
        return resp

    @app.route('/files', methods=['GET', 'POST'])
    def files():
        app.logger.info("request: %s", request)
        result = Auth.identify(Auth, request)
        app.logger.info("状态: %s 用户: %s ", result.get('status'),  result.get('data'))
        if (result['status'] and result['data']):
            pass
        else:
            #return jsonify(result)
            pass
            #return json.dumps(result, ensure_ascii=False)

        app.logger.info("有文件要下载")
        if request.method == 'GET':
            db_name = "ws_doorplate"
            table_name = "gz_orders"
            if request.args.get('city'):
                db_name = CITY.get_db_name(request.args.get('city'))
                table_name = CITY.get_table_name(request.args.get('city'))


            try:
                path = request.args.get('path')
                # app.logger.info(path)
                if path == 'need_make_excel':

                    col_name_list = get_col_name_list(request)

                    file_sended_path = os.path.join(basepath, 'downloads')

                    datas, count = query_datas(request, db_name, table_name, col_name_list)
                    if count == 0:
                        # app.logger.info("没有相关数据")
                        pass

                    # excel_name = 'total_of_' + len(datas) + "_" + datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S') + '.xls'
                    excel_name = str(len(datas)) + "_" + datetime.datetime.now().strftime('%Y%m%d')
                    # excel_name = datetime.datetime.now().strftime('%Y%m%d')
                    sum = 0
                    # (excel_name, extension) = os.path.splitext(excel_name)
                    # if os.path.isfile(os.path.join(file_sended_path, excel_name)):
                    #     app.logger.info("有重复")
                    for root, dirs, files in os.walk(file_sended_path):
                        # app.logger.info('root_dir: %s', root)  # 当前目录路径
                        # app.logger.info('sub_dirs: %s', dirs)  # 当前路径下所有子目录
                        # app.logger.info('files: %s', files)  # 当前路径下所有非目录子文件
                        for file in files:
                            if file.find(excel_name) == 0:
                                sum += 1

                    if sum == 0:
                        pass
                    else:
                        excel_name = excel_name + "_" + str(sum) + ""
                    excel_name += '.xls'


                    col_needed_list = []
                    if request.args.get('col_needed'):
                        col_needed = request.args.get('col_needed')
                        if col_needed == 'all':
                            col_needed_list = col_name_list
                        else:
                            col_needed_list = col_needed.split(',')
                    # filepath, filename, fullpath = ExcelModel.datas_to_excel(datas, col_name_list=data_col_name, path=basepath, excel_name=excel_name)
                    # filepath, filename, fullpath = ExcelModel.datas_to_excel(datas, col_name_list=data_col_name,
                    #                                                          path=file_sended_path,
                    #                                                          excel_name=excel_name)
                    if col_needed_list:
                        filepath, filename, fullpath = ExcelModel.datas_to_excel(datas, col_name_list=list(col_needed_list),
                                                                             path=file_sended_path,
                                                                             excel_name=excel_name)
                    else:
                        filepath, filename, fullpath = ExcelModel.datas_to_excel(datas,
                                                                                 path=file_sended_path,
                                                                                 excel_name=excel_name)
                    app.logger.info("要下载的文件是：%s \n路径：%s", filename, filepath)

                    if os.path.isfile(fullpath):
                        result = send_file(fullpath, as_attachment=True, attachment_filename=filename)
                        # result.headers["x-suggested-filename"] = filename
                        # result.headers["x-filename"] = filename
                        # result.headers["Access-Control-Expose-Headers"] = 'x-filename'
                        return result
                        # return send_from_directory(filepath, filename, as_attachment=True)
                        # return send_file(path, as_attachment=True, attachment_filename=filename)
                    app.logger.info("下载文件有错误，可能是文件路径不存在")
                    abort(404)

                else:
                    # if os.path.isfile(os.path.join('upload', path)):
                    (filepath, filename) = os.path.split(path)
                    app.logger.info("要下载的文件是：%s \n路径：%s", filename, filepath)
                    if os.path.isfile(path):
                        result = send_file(path, as_attachment=True, attachment_filename=filename)
                        # result.headers["x-suggested-filename"] = filename
                        # result.headers["x-filename"] = filename
                        # result.headers["Access-Control-Expose-Headers"] = 'x-filename'
                        return result
                        # return send_from_directory(filepath, filename, as_attachment=True)
                        # return send_file(path, as_attachment=True, attachment_filename=filename)
                    app.logger.info("下载文件有错误，可能是文件路径不存在")
                    abort(404)

            except:
                app.logger.info("下载文件有错误，可能是GET协议参数不匹配")
                abort(404)

    @app.route('/test', methods=['GET', 'POST'])
    def test():
        app.logger.info("request: %s", request)
        app.logger.info("request.data: %s", request.data)
        app.logger.info("request.form: %s", request.form)
        app.logger.info("request.form[email]: %s", request.form['email'])
        app.logger.info("request.form to dic: %s", dict(request.form))

        a = [1,2,3,4,5]
        app.logger.info("len: %s", len(a))
        app.logger.info("len: %d", len(a))
        #result = request.data

        result = Auth.identify(Auth, request)
        app.logger.info("状态: %s 用户: %s ", result.get('status'),  result.get('data'))
        if (result['status'] and result['data']):
            pass
        else:
            #return json.dumps(result, ensure_ascii=False)
            return jsonify(result)




        return jsonify("test", result)

    @app.route('/token', methods=['GET'])
    def token():
        app.logger.info("request: %s", request)
        if not request.args.get("token"):
            return json.dumps(common.falseReturn('', '没有提供认证token', addition=common.false_Type.token_false), ensure_ascii=False, indent=4)
        token = request.args.get("token")
        result = Auth.check_token(token)
        app.logger.info("状态: %s 用户: %s ", result.get('status'), result.get('data'))
        return json.dumps(result, ensure_ascii=False, indent=4)

    @app.route('/print', methods=['GET', 'POST'])
    def print_test():

        app.logger.info("request: %s", request)
        result = Auth.identify(Auth, request)
        app.logger.info("状态: %s 用户: %s ", result.get('status'),  result.get('data'))
        if (result['status'] and result['data']):
            pass
        else:

            return jsonify(result)
        #     #return json.dumps(result, ensure_ascii=False)
        app.logger.info("当前访问用户：%s", request.remote_addr)
        return jsonify(common.trueReturn('', msg='哈哈哈'))





    # 佛山门牌
    @app.route('/fs_doorplates', methods=['GET', 'POST', 'PUT'])
    def fs_doorplates_old():
        app.logger.info("request: %s", request)
        #app.logger.info(request.headers)

        app.logger.info("当前访问用户：%s", request.remote_addr)

        # app.logger.info("Authorization：", request.headers['Authorization'])

        result = Auth.identify(Auth, request)
        app.logger.info("状态: %s 用户: %s ", result.get('status'),  result.get('data'))
        # app.logger.info(result)
        if (result['status'] and result['data']):
            pass
        else:
            return jsonify(result)
            # return json.dumps(result, ensure_ascii=False)


        request_json = request.get_json()
        #app.logger.info(request_json)

        if request.method == 'PUT':
            request_type = request_json.get('type')
            qrcode = request_json.get('qrcode')
            installed_by = request_json.get('installed_by')
            installed_coordinate = request_json.get('installed_coordinate')
            db_name = "ws_doorplate"
            dp_table = "fs_dp"
            if request_json.get('city'):
                db_name = CITY.get_db_name(request_json.get('city'))
                dp_table = CITY.get_table_name(request_json.get('city'))

            #app.logger.info("dp_tabledp_tabledp_table", dp_table)
            db = pymysql.connect("localhost", "root", "root", db_name)
            cursor = db.cursor()

            if request_json.get('installed_date'):
                installed_date = request_json.get('installed_date')
            else:
                installed_date = ''
            if request_type == REQUEST_TYPE.installed.name:
                app.logger.info("登记安装")
            if request_type == REQUEST_TYPE.installed_sync.name:
                app.logger.info("同步安装数据")
                app.logger.info("同步人: %s", installed_by)
                app.logger.info("installed_date: %s", installed_date)
                app.logger.info("global_id: %s", qrcode)




            installed_datas_len = 0
            if request_type == REQUEST_TYPE.installed_batch_sync.name:
                app.logger.info("批量同步安装数据")
                app.logger.info("同步人: %s", installed_by)
                if request_json.get('installed_datas'):
                    installed_datas = request_json.get('installed_datas')
                else:
                    installed_datas = []
                #app.logger.info("installed_dates: ", installed_datas)
                installed_datas_len = len(installed_datas)
                app.logger.info("installed_dates_len: %s", installed_datas_len)
                #app.logger.info("global_id: ", qrcode)
            addition_data = {"cls": 0, "far": 0}
            sync_data = [] # 同步信息数据列表，有无同步，和数据库中的状态

            # app.logger.info(request_json.get('qrcode'))
            # app.logger.info(request_json.get('installed_by'))
            # app.logger.info(request_json.get('installed_coordinate'))
            global_id_query_list = []
            if request_type == REQUEST_TYPE.installed_batch_sync.name:
                #select_sql = "SELECT `index`, `installed`, `installed_photos_cls`, `installed_photos_far`, `installed_date` FROM fs_dp WHERE `global_id` in (%s)" % (','.join(['%s'] * installed_datas_len))
                select_sql = "SELECT `index`, `installed`, `installed_photos_cls`, `installed_photos_far`, `installed_date`, `global_id` FROM " + dp_table + " WHERE `global_id` in (%s)" % (
                    ','.join(['\'' + i['qrcode'] + '\'' for i in installed_datas]))

                global_id_query_list = [i['qrcode'] for i in installed_datas]
            else:
                select_sql = "SELECT `index`, `installed`, `installed_photos_cls`, `installed_photos_far`, `installed_date`, `global_id` FROM " + dp_table + " WHERE `global_id` = " + "\'" + qrcode + "\'" + " LIMIT 1"
                global_id_query_list.append(qrcode)

            datas_query_from_db_list = [] # 从数据库中检索出来的数据
            datas_update_list = []  # 需要update到数据库的数据
            global_id_not_in_db_list = []  # 不在数据库中的数据


            if select_sql:
                try:
                    #app.logger.info(select_sql)
                    cursor.execute(select_sql)
                    temp = cursor.fetchall()
                    #app.logger.info(cursor.fetchall())
                    #app.logger.info(temp)
                    if temp:
                        datas_query_from_db_list = [list(i) for i in temp]
                        global_id_query_from_db_list = [i[-1] for i in datas_query_from_db_list]
                        # 找出数据库中不存在的数据
                        for i in global_id_query_list:
                            if i not in global_id_query_from_db_list:
                                global_id_not_in_db_list.append(i)

                        if request_type == REQUEST_TYPE.installed_batch_sync.name:

                            for i in range(len(temp)):
                                temp_map = {}
                                temp_map['index'] = temp[i][0]
                                temp_map['installed'] = temp[i][1]
                                temp_map["cls"] = temp[i][2]
                                temp_map["far"] = temp[i][3]
                                temp_map["installed_date"] = temp[i][4]
                                temp_map["global_id"] = temp[i][5]
                                temp_map["sync"] = 1



                                if temp[i][1] > 0:
                                    if temp[i][4]:
                                        if temp[i][4].strftime('%Y-%m-%d %H:%M:%S') != "2019-01-01 00:00:00" and \
                                                temp[i][4].strftime('%Y-%m-%d %H:%M:%S') != "2000-01-01 00:00:00" and  \
                                                temp[i][4].strftime('%Y-%m-%d %H:%M:%S') != "1970-01-01 08:00:00" and request_json.get('force') != 1:
                                                temp_map["sync"] = 0
                                #app.logger.info("temp_map %s", temp_map)
                                if temp_map["sync"] or request_json.get('force'):

                                    for j in installed_datas:

                                        if j['qrcode'] == temp_map["global_id"]:
                                            temp_map["sync_installed_date"] = j.get("installed_date")
                                            temp_map["sync_installed_coordinate"] = j["installed_coordinate"]
                                            temp_map["sync_installed_by"] = installed_by

                                sync_data.append(temp_map)

                        else:

                            addition_data["cls"] = temp[0][2]
                            addition_data["far"] = temp[0][3]
                            if request_type == REQUEST_TYPE.installed_sync.name:
                                if temp[0][1] > 0:
                                    if temp[0][4]:
                                        if temp[0][4].strftime('%Y-%m-%d %H:%M:%S') != "2019-01-01 00:00:00" and temp[0][4].strftime('%Y-%m-%d %H:%M:%S') != "2000-01-01 00:00:00" and request_json.get(
                                                'force') != 1:
                                            return jsonify(common.trueReturn("", "安装信息已经存在，无需登记", addition=addition_data))

                        #temp = cursor.fetchall()
                        #app.logger.info(temp[0])
                        #pass
                        #temp = cursor.fetchall()[0]
                    else:
                        # 提交到数据库执行
                        #db.commit()
                        # 关闭数据库连接
                        db.close()
                        app.logger.info("检查global_id有无错误")
                        return jsonify(common.falseReturn([], "检查global_id有无错误", addition=common.false_Type.name_false))
                except:
                    # 如果发生错误则回滚
                    #traceback.print_exc()
                    db.rollback()
                    # 关闭数据库连接
                    db.close()
                    return jsonify(common.falseReturn([], "上传失败"))

            if request_type == REQUEST_TYPE.installed_batch_sync.name:
                #app.logger.info(sync_data)
                ''' # 2019-06-21
                for i in sync_data:
                    if i['sync']:
                        sql = "UPDATE fs_dp SET `installed`=`installed`+1 " + \
                              ", `installed_by` = " + "\'" + i["sync_installed_by"] + "\'" + \
                              ", `installed_coordinate` = " + "\'" + i["sync_installed_coordinate"] + "\'"

                        if i.get("sync_installed_date"):
                            sql += ", `installed_date` = " + "\'" + i["sync_installed_date"] + "\'"
                        # else:
                        #     sql += ", `installed_date` = " + "\'" + datetime.datetime.now().strftime(
                        #         '%Y-%m-%d %H:%M:%S') + "\'"
                        sql += " WHERE `global_id` = " + "\'" + i['global_id'] + "\'"


                        #app.logger.info(sql)
                        #cursor.execute(sql)
                        try:
                            #app.logger.info(sql)
                            cursor.execute(sql)
                            #app.logger.info(cursor.fetchall())

                        except:
                            # 如果发生错误则回滚
                            #traceback.print_exc()
                            db.rollback()
                            # 关闭数据库连接
                            db.close()
                            return jsonify(common.falseReturn("", "同步失败", addition={"error_sql": sql, "error_datas": i}))
                '''
                # 2019-06-21
                # 批量更新安装状态
                sync_data_final_update = []
                for i in sync_data:
                    if i['sync']:
                        sync_data_final_update.append(i)

                sql_head = "UPDATE " + dp_table + " SET `installed`=(CASE `global_id` "
                # 使用cursor()方法获取操作游标
                cursor = db.cursor()
                step = 1000
                step_num = math.ceil(len(sync_data_final_update) / step)

                # done_count = 0
                for i in range(step_num):
                    temp_data_list = []
                    head = i * step
                    if i == (step_num - 1):
                        tail = len(sync_data_final_update)
                    else:
                        tail = (i + 1) * step

                    sql = sql_head
                    col = 0

                    # add installed
                    for j in sync_data_final_update[head:tail]:
                        temp = " WHEN " + '\'' + j['global_id'] + '\'' + " THEN " + '`installed`+1 '
                        sql += temp
                        col += 1

                    sql += " ELSE installed END) "
                    sql += ", " + " `installed_by`=(CASE `global_id` "

                    # add installed_by
                    for j in sync_data_final_update[head:tail]:
                        temp = " WHEN " + '\'' + j['global_id'] + '\'' + " THEN " + '\'' + j['sync_installed_by'] + '\''
                        sql += temp
                        col += 1

                    sql += " ELSE installed_by END) "
                    sql += ", " + " `installed_coordinate`=(CASE `global_id` "

                    # add installed_coordinate
                    for j in sync_data_final_update[head:tail]:
                        temp = " WHEN " + '\'' + j['global_id'] + '\'' + " THEN " + '\'' + j['sync_installed_coordinate'] + '\''
                        sql += temp
                        col += 1

                    sql += " ELSE installed_coordinate END) "
                    sql += ", " + " `installed_date`=(CASE `global_id` "

                    # add installed_date

                    for j in sync_data_final_update[head:tail]:
                        if j.get("sync_installed_date"):
                            temp = " WHEN " + '\'' + j['global_id'] + '\'' + " THEN " + '\'' + j[
                                'sync_installed_date'] + '\''
                        else:
                            temp = " WHEN " + '\'' + j['global_id'] + '\'' + " THEN " + '\'' + datetime.datetime.now().strftime(
                                '%Y-%m-%d %H:%M:%S') + '\''
                        sql += temp
                        col += 1

                    sql += " ELSE installed_date END) "
                    sql += "WHERE `global_id` IN (\'%s\') " % (
                        '\',\''.join(list([k["global_id"] for k in sync_data_final_update[head:tail]])))

                    #app.logger.info(sql)
                    try:
                        #app.logger.info(sql)
                        cursor.execute(sql)


                    except:
                        # 如果发生错误则回滚
                        # traceback.print_exc()
                        db.rollback()
                        # 关闭数据库连接
                        db.close()
                        return jsonify(
                            common.falseReturn("", "同步失败", addition={"error_sql": sql, "error_datas": i}))

                    db.commit()
                    app.logger.info('%d/%d done' , tail, len(sync_data_final_update))

            else:

                sql = "UPDATE " + dp_table + " SET `installed`=`installed`+1 " + \
                      ", `installed_by` = " + "\'" + installed_by + "\'" + \
                      ", `installed_coordinate` = " + "\'" + installed_coordinate + "\'"

                if installed_date:
                    sql += ", `installed_date` = " + "\'" + installed_date + "\'"
                else:
                    sql += ", `installed_date` = " + "\'" + datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S') + "\'"
                sql += " WHERE `global_id` = " + "\'" + qrcode + "\'"



                try:
                    app.logger.info(sql)
                    cursor.execute(sql)
                    #app.logger.info(cursor.fetchall())
                    # 提交到数据库执行
                    db.commit()
                    # 关闭数据库连接
                    db.close()
                    cache.clear()
                    return jsonify(common.trueReturn("", "上传成功", addition=addition_data))
                except:
                    # 如果发生错误则回滚
                    #traceback.print_exc()
                    db.rollback()
                    # 关闭数据库连接
                    db.close()
                    return jsonify(common.falseReturn("", "上传失败"))

                # 提交到数据库执行
                db.commit()
                # 关闭数据库连接
                db.close()

            db.close()
            cache.clear()
            return jsonify(common.trueReturn(sync_data, "同步成功", addition={"global_id_not_in_db_list": global_id_not_in_db_list}))


        if request.method == 'GET':

            # 查询数据是否存在
            # 连接数据库,此前在数据库中创建数据库dayi_doorplate
            # db = pymysql.connect("localhost", "root", "123456", "dayi_doorplate")
            db = pymysql.connect("localhost", "root", "root", "ws_doorplate")
            # db = pymysql.connect(config.DB_HOST, config.DB_USER, config.DB_PASSWORD, config.DB_NAME)
            # 使用cursor()方法获取操作游标
            cursor = db.cursor()

            # global data_col_name, sql_str

            # 获取列名
            cursor.execute(
                " SELECT column_name FROM information_schema.columns WHERE table_schema='ws_doorplate' AND table_name='fs_dp' ")
            results = cursor.fetchall()
            col_name_list = []
            # app.logger.info(results)
            for i in results:
                col_name_list.append(str(i[0]))

            # app.logger.info("列名：", col_name_list)
            data_col_name = col_name_list
            db.commit()

            datas, count = query_datas(request, "ws_doorplate", "fs_dp", col_name_list)
            if count == 0:
                #app.logger.info("没有相关数据")
                pass
            # return jsonStr
            jsonStr = json.dumps(datas, ensure_ascii=False)
            resp = Response(jsonStr)
            resp.mimetype = 'application/json'
            resp.headers['x-total-count'] = count
            resp.headers['access-control-expose-headers'] = 'X-Total-Count'
            # 关闭数据库连接
            db.close()
            return resp


        return jsonify(common.falseReturn("", "接口错误"))

    @cache.memoize(timeout=config.cache_timeout)  # 设置缓存以及缓存时间 以秒为单位，设置了30分钟
    def pictures_get(request):

        if request.args.get("picture_type") == REQUEST_TYPE.collected.name:
            picture_type = "collected"

        #elif request_type == REQUEST_TYPE.installed.name:
        else:
            # 默认为安装照片
            picture_type = "installed"

        # 获取当前页码，以及每一页需要呈现的数据数
        if request.args.get('_page') and request.args.get('_limit'):
            page = int(request.args.get('_page'))
            limit = int(request.args.get('_limit'))
            sql_limit = " LIMIT " + str((page - 1) * limit) + "," + str(limit)
        else:
            sql_limit = ""

        query_key = []
        for key in request.args.keys():
            # if key.find('like') > 0:
            if key.find('_like') > 0:
                query_key.append(key[0:key.find('like') - 1])

        filter_condition_sql = ""
        #sql_like_query = ''
        if query_key:
            for key in query_key:
                if filter_condition_sql:
                    filter_condition_sql += ' AND ' + key + ' LIKE \'%' + request.args.get(str(key + '_like')) + '%\''
                else:
                    filter_condition_sql += key + ' LIKE \'%' + request.args.get(str(key + '_like')) + '%\''

        # 精准查询
        accurate_query_key = []
        for key in request.args.keys():
            if key.find('_accurate') > 0:
                accurate_query_key.append(key[0:key.find('accurate') - 1])

            # 精准查询
        if len(accurate_query_key) > 0:
            # logger.info(query_key)
            #sql_accurate_query = ''
            for key in accurate_query_key:
                # if filter_condition_sql == '':
                #     if key == 'index':
                #         filter_condition_sql += ' WHERE ' + 'cast( `' + key + '` as char )' + ' = \'' + request.args.get(
                #             str(key + '_accurate')) + '\''
                #     else:
                #         filter_condition_sql += ' WHERE ' + key + ' = \'' + request.args.get(
                #             str(key + '_accurate')) + '\''
                # else:
                if filter_condition_sql == '':
                    if key == 'index':
                        filter_condition_sql += 'cast( `' + key + '` as char )' + ' = \'' + request.args.get(
                            str(key + '_accurate')) + '\''
                    else:
                        filter_condition_sql +=  key + ' = \'' + request.args.get(
                            str(key + '_accurate')) + '\''
                else:
                    if key == 'index':
                        filter_condition_sql += ' AND ' + 'cast( `' + key + '` as char )' + ' = \'' + request.args.get(
                            str(key + '_accurate')) + '\''
                    else:
                        filter_condition_sql += ' AND ' + key + ' = \'' + request.args.get(
                            str(key + '_accurate')) + '\''



        try:

            if request.args.get('city'):
                picture_city = request.args.get('city')
            else:
                picture_city = 'foshan'

            database_name = 'ws_doorplate'
            #if picture_city == "guangzhou":
            if picture_city != "maoming" and picture_city != "foshan":
                #database_name = 'ws_doorplate'
                #table_name = 'gz_orders'
                database_name = CITY.get_db_name(picture_city)
                table_name = CITY.get_table_name(picture_city)
                # db = pymysql.connect("localhost", "root", "root", "丹灶数据库")
                db = pymysql.connect("localhost", "root", "root", database_name)
                # 使用cursor()方法获取操作游标
                cursor = db.cursor()

                # select_sql = "SELECT `index` FROM gis_ordered WHERE `DZBM` = " + "\'" + dzbm + "\'" + " LIMIT 1"
                #select_sql = "SELECT `dp_id`,`installed_photos_cls`,`installed_photos_far`, `street`, `dp_num`, `installed_date`, `dp_name`, `installed_by`, `global_id`, `index`, `installed_photos_cls_check`, `installed_photos_far_check` FROM " + table_name
                if picture_type == "collected":
                    select_sql = "SELECT `dp_id`," \
                                 "`{picture_type}_photos`," \
                                 "`street`, `dp_num`, " \
                                 "`{picture_type}_date`, `dp_name`, " \
                                 "`{picture_type}_by`, `global_id`, `index`, " \
                                 "`{picture_type}_photos_check` FROM " + table_name
                    select_sql = select_sql.format(picture_type=picture_type)
                else:
                    select_sql = "SELECT `dp_id`," \
                                 "`installed_photos_cls`," \
                                 "`installed_photos_far`, `street`, `dp_num`, " \
                                 "`installed_date`, `dp_name`, " \
                                 "`installed_by`, `global_id`, `index`, " \
                                 "`installed_photos_cls_check`, " \
                                "`installed_photos_far_check` FROM " + table_name
                # select_condition = 0
                select_condition = ''
                if request.args.get('district'):
                    district = request.args.get('district')
                    if not select_condition:
                        # select_sql += ' WHERE '
                        # select_condition = 1
                        select_condition += ' WHERE '
                    else:
                        # select_sql += ' AND '
                        select_condition += ' AND '
                    # select_sql += "district=" + '\"' + district + '\"'
                    select_condition += "district=" + '\"' + district + '\"'
                else:
                    district = ''
                if request.args.get('shequ'):
                    shequ = request.args.get('shequ')
                    if not select_condition:
                        # select_sql += ' WHERE '
                        # select_condition = 1
                        select_condition += ' WHERE '
                    else:
                        # select_sql += ' AND '
                        select_condition += ' AND '
                    # select_sql += "community=" + '\"' + shequ + '\"'

                    # 注意，在佛山数据库，是字段名是community，在广州数据库 字段名是pcs
                    select_condition += "pcs=" + '\"' + shequ + '\"'
                else:
                    shequ = ''
                order_by_date = 0
                if request.args.get('date'):
                    date = request.args.get('date')
                    order_by_date = 1
                    if not select_condition:
                        # select_sql += ' WHERE '
                        # select_condition = 1
                        select_condition += ' WHERE '
                    else:
                        # select_sql += ' AND '
                        select_condition += ' AND '
                    # select_sql += "installed_date like " + "\"%" + installed_date + "%\""
                    select_condition += "{picture_type}_date like " + "\"%" + date + "%\""
                    select_condition = select_condition.format(picture_type=picture_type)
                else:
                    installed_date = ''
                # if picture_type == "collected" or picture_type == "installed":
                #     if request.args.get('date'):
                #         date = request.args.get('date')
                #         order_by_date = 1
                #         if not select_condition:
                #             # select_sql += ' WHERE '
                #             # select_condition = 1
                #             select_condition += ' WHERE '
                #         else:
                #             # select_sql += ' AND '
                #             select_condition += ' AND '
                #         # select_sql += "installed_date like " + "\"%" + installed_date + "%\""
                #         select_condition += "{picture_type}_date like " + "\"%" + date + "%\""
                #         select_condition = select_condition.format(picture_type=picture_type)
                #     else:
                #         installed_date = ''
                # else:
                #     if request.args.get('installed_date'):
                #         installed_date = request.args.get('installed_date')
                #         order_by_date = 1
                #         if not select_condition:
                #             # select_sql += ' WHERE '
                #             # select_condition = 1
                #             select_condition += ' WHERE '
                #         else:
                #             # select_sql += ' AND '
                #             select_condition += ' AND '
                #         # select_sql += "installed_date like " + "\"%" + installed_date + "%\""
                #         select_condition += "installed_date like " + "\"%" + installed_date + "%\""
                #     else:
                #         installed_date = ''

                # installed_date_start = '2000-01-01 00:00:00'
                # installed_date_end = common.format_ymdhms_time_now()
                if request.args.get('date_start') or request.args.get('date_end'):
                    date_start = request.args.get('date_start') if request.args.get(
                        'date_start') else '2000-01-01 00:00:00'
                    date_end = request.args.get('date_end') if request.args.get(
                        'date_end') else common.format_ymdhms_time_now()
                    if not select_condition:
                        # select_sql += ' WHERE '
                        # select_condition = 1
                        select_condition += ' WHERE '
                    else:
                        # select_sql += ' AND '
                        select_condition += ' AND '
                    # select_sql += "installed_date like " + "\"%" + installed_date + "%\""
                    select_condition += " {picture_type}_date >= " + "\"" + date_start + "\"" + " AND {picture_type}_date <= " + "\"" + date_end + "\""

                # if picture_type == "collected" or picture_type == "installed":
                #     if request.args.get('date_start') or request.args.get('date_end'):
                #         date_start = request.args.get('date_start') if request.args.get(
                #             'date_start') else '2000-01-01 00:00:00'
                #         date_end = request.args.get('date_end') if request.args.get(
                #             'date_end') else common.format_ymdhms_time_now()
                #         if not select_condition:
                #             # select_sql += ' WHERE '
                #             # select_condition = 1
                #             select_condition += ' WHERE '
                #         else:
                #             # select_sql += ' AND '
                #             select_condition += ' AND '
                #         # select_sql += "installed_date like " + "\"%" + installed_date + "%\""
                #         select_condition += " {picture_type}_date >= " + "\"" + date_start + "\"" + " AND {picture_type}_date <= " + "\"" + date_end + "\""
                #         select_condition = select_condition.format(picture_type=picture_type)
                #
                # else:
                #     if request.args.get('installed_date_start') or request.args.get('installed_date_end'):
                #         installed_date_start = request.args.get('installed_date_start') if request.args.get(
                #             'installed_date_start') else '2000-01-01 00:00:00'
                #         installed_date_end = request.args.get('installed_date_end') if request.args.get(
                #             'installed_date_end') else common.format_ymdhms_time_now()
                #         if not select_condition:
                #             # select_sql += ' WHERE '
                #             # select_condition = 1
                #             select_condition += ' WHERE '
                #         else:
                #             # select_sql += ' AND '
                #             select_condition += ' AND '
                #         # select_sql += "installed_date like " + "\"%" + installed_date + "%\""
                #         select_condition += " installed_date >= " + "\"" + installed_date_start + "\"" + " AND installed_date <= " + "\"" + installed_date_end + "\""
                order_by_by = 0  # 按picture_type人排序
                if request.args.get('by'):
                    picture_type_by = request.args.get('by')
                    order_by_by = 1
                    if not select_condition:
                        # select_sql += ' WHERE '
                        # select_condition = 1
                        select_condition += ' WHERE '
                    else:
                        # select_sql += ' AND '
                        select_condition += ' AND '
                    # select_sql += "installed_by=" + '\"' + installed_by + '\"'
                    select_condition += "{picture_type}_by=" + '\"' + picture_type_by + '\"'
                    select_condition = select_condition.format(picture_type=picture_type)

                else:
                    picture_type_by = ''
                # if picture_type == "collected" or picture_type == "installed":
                #     order_by_by = 0  # 按picture_type人排序
                #     if request.args.get('by'):
                #         picture_type_by = request.args.get('by')
                #         order_by_by = 1
                #         if not select_condition:
                #             # select_sql += ' WHERE '
                #             # select_condition = 1
                #             select_condition += ' WHERE '
                #         else:
                #             # select_sql += ' AND '
                #             select_condition += ' AND '
                #         # select_sql += "installed_by=" + '\"' + installed_by + '\"'
                #         select_condition += "{picture_type}_by=" + '\"' + picture_type_by + '\"'
                #         select_condition = select_condition.format(picture_type=picture_type)
                #
                #     else:
                #         picture_type_by = ''
                # else:
                #     order_by_by = 0 # 按picture_type人排序
                #     if request.args.get('installed_by'):
                #         installed_by = request.args.get('installed_by')
                #         order_by_by = 1
                #         if not select_condition:
                #             # select_sql += ' WHERE '
                #             # select_condition = 1
                #             select_condition += ' WHERE '
                #         else:
                #             # select_sql += ' AND '
                #             select_condition += ' AND '
                #         # select_sql += "installed_by=" + '\"' + installed_by + '\"'
                #         select_condition += "installed_by=" + '\"' + installed_by + '\"'
                #
                #     else:
                #         installed_by = ''
                # select_sql = select_sql + select_condition

                contract_batch = ""
                contract_batch_sql = ""
                if request.args.get('contract_batch'):
                    contract_batch = request.args.get('contract_batch')
                    contract_batch_sql += " contract_batch=" + "\"" + contract_batch + "\""
                    if not select_condition:
                        # select_sql += ' WHERE '
                        # select_condition = 1
                        select_condition += ' WHERE '
                    else:
                        # select_sql += ' AND '
                        select_condition += ' AND '
                    select_condition += contract_batch_sql
                order_batch = ""
                order_batch_sql = ""
                if request.args.get('order_batch'):
                    order_batch = request.args.get('order_batch')
                    order_batch_sql += " order_batch=" + "\"" + order_batch + "\""
                    if not select_condition:
                        # select_sql += ' WHERE '
                        # select_condition = 1
                        select_condition += ' WHERE '
                    else:
                        # select_sql += ' AND '
                        select_condition += ' AND '
                    select_condition += order_batch_sql
                order_id = ""
                order_id_sql = ""
                if request.args.get('order_id'):
                    order_id = request.args.get('order_id')
                    order_id_sql += " order_id=" + "\"" + order_id + "\""
                    if not select_condition:
                        # select_sql += ' WHERE '
                        # select_condition = 1
                        select_condition += ' WHERE '
                    else:
                        # select_sql += ' AND '
                        select_condition += ' AND '
                    select_condition += order_id_sql

                if filter_condition_sql:
                    if not select_condition:
                        # select_sql += ' WHERE '
                        # select_condition = 1
                        select_condition += ' WHERE '
                        select_condition += filter_condition_sql
                    else:
                        # select_sql += ' AND '
                        select_condition += ' AND '
                        select_condition += filter_condition_sql

                select_sql = select_sql + select_condition
                order_by_sql = ""
                if order_by_date:
                    if order_by_sql:
                        order_by_sql += " ,{picture_type}_date "
                    else:
                        order_by_sql += " {picture_type}_date "
                if order_by_by:
                    if order_by_sql:
                        order_by_sql += " ,{picture_type}_by "
                    else:
                        order_by_sql += " {picture_type}_by "

                order_by_sql = order_by_sql.format(picture_type=picture_type)

                # if picture_type == "collected" or picture_type == "installed":
                #     order_by_sql = ""
                #     if order_by_date:
                #         if order_by_sql:
                #             order_by_sql += " ,{picture_type}_date "
                #         else:
                #             order_by_sql += " {picture_type}_date "
                #     if order_by_by:
                #         if order_by_sql:
                #             order_by_sql += " ,{picture_type}_by "
                #         else:
                #             order_by_sql += " {picture_type}_by "
                #
                #     order_by_sql = order_by_sql.format(picture_type=picture_type)
                #
                # else:
                #     order_by_sql = ""
                #     if order_by_date:
                #         if order_by_sql:
                #             order_by_sql += " ,installed_date "
                #         else:
                #             order_by_sql += " installed_date "
                #     if order_by_by:
                #         if order_by_sql:
                #             order_by_sql += " ,installed_by "
                #         else:
                #             order_by_sql += " installed_by "

                # all_select_sql = select_sql + " ORDER BY installed_date, installed_by " + sql_limit

                all_select_datas_len_sql = "SELECT count(`index`) FROM " + table_name + select_condition
                app.logger.info(all_select_datas_len_sql)
                cursor.execute(all_select_datas_len_sql)

                pictures_list_len = cursor.fetchall()
                pictures_list_len = pictures_list_len[0][0]
                app.logger.info("pictures_list_len %s", pictures_list_len)

                if order_by_sql:
                    all_select_sql = select_sql + " ORDER BY " + order_by_sql + sql_limit
                else:
                    all_select_sql = select_sql + sql_limit
                app.logger.info(all_select_sql)
                cursor.execute(all_select_sql)

                result = cursor.fetchall()

                # app.logger.info(result)
                pictures_list_data = []

                pictures_full_path_list = []

                if picture_type == "collected" or picture_type == "installed":
                    for row_data in result:
                        if picture_type == "collected":
                            dp_id = row_data[0]
                            cls = 0
                            far = row_data[1]
                            dp_street = row_data[2]
                            dp_num = row_data[3]
                            date = row_data[4]
                            dp_name = row_data[5]
                            picture_type_by = row_data[6]
                            global_id = row_data[7]
                            index = row_data[8]
                            photos_cls_check = ""
                            photos_far_check = row_data[9]
                        else:
                            dp_id = row_data[0]
                            cls = row_data[1]
                            far = row_data[2]
                            dp_street = row_data[3]
                            dp_num = row_data[4]
                            date = row_data[5]
                            dp_name = row_data[6]
                            picture_type_by = row_data[7]
                            global_id = row_data[8]
                            index = row_data[9]
                            photos_cls_check = row_data[10]
                            photos_far_check = row_data[11]

                        temp_map = {}
                        temp_map["dp_id"] = dp_id
                        if not date:
                            temp_map["date"] = datetime.datetime.strptime('2000-01-01 00:00:00',
                                                                                    '%Y-%m-%d %H:%M:%S')
                        else:
                            temp_map["date"] = date.strftime('%Y-%m-%d %H:%M:%S')
                        # temp_map["name"] = str(district) + str(shequ) + str(dp_street) + str(dp_name)
                        temp_map["cls_list"] = []
                        temp_map["far_list"] = []
                        temp_map["dp_name"] = dp_name
                        temp_map["dp_num"] = dp_num
                        temp_map["street"] = dp_street
                        temp_map["global_id"] = global_id
                        temp_map["by"] = picture_type_by
                        temp_map["index"] = index
                        if picture_type == "collected":
                            temp_map["photos_cls_check"] = photos_cls_check
                        else:
                            temp_map["photos_cls_check"] = photos_cls_check
                        temp_map["photos_far_check"] = photos_far_check

                        if picture_type == "collected":
                            if cls:
                                pass
                                # filename = index + '.jpg'
                                #
                                # sum = 0
                                # while (os.path.isfile(
                                #         os.path.join(config.DY_DATAS_COLLECTED_PICTURES_PATH, picture_city + "/" + filename))):  # 入参需要是绝对路径
                                #
                                #     full_path = os.path.isfile(
                                #         os.path.join(config.DY_DATAS_COLLECTED_PICTURES_PATH, picture_city + "/" + filename))
                                #
                                #     pictures_full_path_list.append(full_path)
                                #
                                #     temp_map["cls_list"].append(filename)
                                #     sum += 1
                                #     # filename = dp_id + '_cj01_' + str(sum) + '.jpg'
                                #
                                #     filename = index + "_" + str(sum) + '.jpg'

                                # pictures_list_data.append(temp_map)
                            if far:
                                filename = str(index) + '_collected.jpg'

                                sum = 0
                                while (os.path.isfile(
                                        os.path.join(config.DY_DATAS_COLLECTED_PICTURES_PATH,
                                                     picture_city + "/" + filename))):  # 入参需要是绝对路径

                                    full_path = os.path.isfile(
                                        os.path.join(config.DY_DATAS_COLLECTED_PICTURES_PATH,
                                                     picture_city + "/" + filename))

                                    pictures_full_path_list.append(full_path)

                                    temp_map["cls_list"].append(filename)
                                    sum += 1
                                    # filename = dp_id + '_cj01_' + str(sum) + '.jpg'

                                    filename = str(index) + "_collected_" + str(sum) + '.jpg'

                                # pictures_list_data.append(temp_map)

                        else:
                            if cls:
                                if picture_city != "guangzhou":
                                    filename = global_id + '_cls.jpg'
                                else:
                                    filename = dp_id + '_cj01.jpg'
                                sum = 0
                                while (os.path.isfile(
                                        dydatas_basepath + '/gd_dp_photos/' + picture_city + "/" + filename)):  # 入参需要是绝对路径

                                    full_path = dydatas_basepath + '/gd_dp_photos/' + picture_city + "/" + filename
                                    pictures_full_path_list.append(full_path)

                                    temp_map["cls_list"].append(filename)
                                    sum += 1
                                    # filename = dp_id + '_cj01_' + str(sum) + '.jpg'
                                    if picture_city != "guangzhou":
                                        filename = global_id + '_cls_' + str(sum) + '.jpg'
                                    else:
                                        filename = dp_id + '_cj01_' + str(sum) + '.jpg'
                                # pictures_list_data.append(temp_map)
                            if far:
                                if picture_city != "guangzhou":
                                    filename = global_id + '_far.jpg'
                                else:
                                    filename = dp_id + '_cj01.jpg'
                                sum = 0
                                while (os.path.isfile(
                                        dydatas_basepath + '/gd_dp_photos/' + picture_city + "/" + filename)):  # 入参需要是绝对路径

                                    full_path = dydatas_basepath + '/gd_dp_photos/' + picture_city + "/" + filename
                                    pictures_full_path_list.append(full_path)

                                    temp_map["far_list"].append(filename)
                                    sum += 1
                                    # filename = dp_id + '_cj01_' + str(sum) + '.jpg'
                                    if picture_city != "guangzhou":
                                        filename = global_id + '_far_' + str(sum) + '.jpg'
                                    else:
                                        filename = dp_id + '_cj01_' + str(sum) + '.jpg'
                        pictures_list_data.append(temp_map)

                        # 加个小排序，按安装时间排序
                        # pictures_list_data.sort(key=lambda i: i["installed_date"])

                    no_pictures_list_data = []

                    # (installed_photos_far<=0 OR installed_photos_cls<=0) 是缺一张就算上
                    # (installed_photos_far<=0 AND installed_photos_cls<=0) 是都缺的
                    if picture_type == "collected":
                        if not select_condition:
                            select_sql = select_sql + " WHERE " + "{picture_type}_photos<=0  AND {picture_type}>0"

                            no_pictures_datas_len_sql = "SELECT count(`index`) FROM " + table_name + " WHERE " + "{picture_type}_photos<=0  AND {picture_type}>0"
                        else:
                            select_sql = select_sql + " AND " + "{picture_type}_photos<=0 AND {picture_type}>0"

                            no_pictures_datas_len_sql = "SELECT count(`index`) FROM " + table_name + select_condition + " AND " + "{picture_type}_photos<=0  AND {picture_type}>0"

                        select_sql = select_sql.format(picture_type=picture_type)
                        no_pictures_datas_len_sql = no_pictures_datas_len_sql.format(picture_type=picture_type)
                    else:
                        if not select_condition:
                            select_sql = select_sql + " WHERE " + "(installed_photos_far<=0 AND installed_photos_cls<=0) AND installed>0"

                            no_pictures_datas_len_sql = "SELECT count(`index`) FROM " + table_name + " WHERE " + "(installed_photos_far<=0 AND installed_photos_cls<=0) AND installed>0"
                        else:
                            select_sql = select_sql + " AND " + "(installed_photos_far<=0 AND installed_photos_cls<=0) AND installed>0"

                            no_pictures_datas_len_sql = "SELECT count(`index`) FROM " + table_name + select_condition + " AND " + "(installed_photos_far<=0 AND installed_photos_cls<=0) AND installed>0"
                    app.logger.info(no_pictures_datas_len_sql)
                    cursor.execute(no_pictures_datas_len_sql)

                    no_pictures_list_len = cursor.fetchall()
                    no_pictures_list_len = no_pictures_list_len[0][0]
                    app.logger.info("no_pictures_list_len %s", no_pictures_list_len)

                    select_sql = select_sql + " ORDER BY {picture_type}_date, {picture_type}_by " + sql_limit
                    select_sql = select_sql.format(picture_type=picture_type)


                    app.logger.info(select_sql)
                    cursor.execute(select_sql)

                    result = cursor.fetchall()


                    for row_data in result:
                        if picture_type == "collected":
                            dp_id = row_data[0]
                            cls = 0
                            far = row_data[1]
                            dp_street = row_data[2]
                            dp_num = row_data[3]
                            date = row_data[4]
                            dp_name = row_data[5]
                            picture_type_by = row_data[6]
                            global_id = row_data[7]
                            index = row_data[8]
                            photos_cls_check = ""
                            photos_far_check = row_data[9]
                        else:
                            dp_id = row_data[0]
                            cls = row_data[1]
                            far = row_data[2]
                            dp_street = row_data[3]
                            dp_num = row_data[4]
                            date = row_data[5]
                            dp_name = row_data[6]
                            picture_type_by = row_data[7]
                            global_id = row_data[8]
                            index = row_data[9]
                            photos_cls_check = row_data[10]
                            photos_far_check = row_data[11]
                        temp_map = {}
                        temp_map["dp_id"] = dp_id
                        if not date:
                            temp_map["date"] = datetime.datetime.strptime('2000-01-01 00:00:00',
                                                                                    '%Y-%m-%d %H:%M:%S')
                        else:
                            temp_map["date"] = date.strftime('%Y-%m-%d %H:%M:%S')
                        # temp_map["name"] = str(district) + str(shequ) + str(dp_street) + str(dp_name)
                        temp_map["no_cls"] = 1
                        temp_map["no_far"] = 1
                        temp_map["dp_name"] = dp_name
                        temp_map["dp_num"] = dp_num
                        temp_map["street"] = dp_street
                        temp_map["by"] = picture_type_by
                        temp_map["global_id"] = global_id
                        temp_map["index"] = index
                        temp_map["photos_cls_check"] = photos_cls_check
                        temp_map["photos_far_check"] = photos_far_check
                        if picture_type == "collected":
                            if cls:
                                pass
                            if far:
                                filename = index + '_collected.jpg'

                                sum = 0
                                while (os.path.isfile(
                                        os.path.join(config.DY_DATAS_COLLECTED_PICTURES_PATH,
                                                     picture_city + "/" + filename))):  # 入参需要是绝对路径

                                    full_path = os.path.isfile(
                                        os.path.join(config.DY_DATAS_COLLECTED_PICTURES_PATH,
                                                     picture_city + "/" + filename))

                                    pictures_full_path_list.append(full_path)

                                    temp_map["cls_list"].append(filename)
                                    sum += 1
                                    # filename = dp_id + '_cj01_' + str(sum) + '.jpg'

                                    filename = index + "_collected_" + str(sum) + '.jpg'
                        else:
                            if cls:

                                if picture_city != "guangzhou":
                                    filename = global_id + '_cls.jpg'
                                else:
                                    filename = dp_id + '_cj01.jpg'
                                sum = 0
                                while (os.path.isfile(
                                        dydatas_basepath + '/gd_dp_photos/' + picture_city + "/" + filename)):  # 入参需要是绝对路径
                                    temp_map["no_cls"] = 0
                                    sum += 1
                                    # filename = dp_id + '_cj01_' + str(sum) + '.jpg'
                                    if picture_city != "guangzhou":
                                        filename = global_id + '_cls_' + str(sum) + '.jpg'
                                    else:
                                        filename = dp_id + '_cj01_' + str(sum) + '.jpg'

                            if far:
                                if picture_city != "guangzhou":
                                    filename = global_id + '_far.jpg'
                                else:
                                    filename = dp_id + '_cj01.jpg'
                                sum = 0
                                while (os.path.isfile(
                                        dydatas_basepath + '/gd_dp_photos/' + picture_city + "/" + filename)):  # 入参需要是绝对路径
                                    temp_map["no_far"] = 0
                                    sum += 1
                                    # filename = dp_id + '_cj01_' + str(sum) + '.jpg'
                                    if picture_city != "guangzhou":
                                        filename = global_id + '_far_' + str(sum) + '.jpg'
                                    else:
                                        filename = dp_id + '_cj01_' + str(sum) + '.jpg'

                        no_pictures_list_data.append(temp_map)

                else:
                    pass
                    # for dp_id, cls, far, dp_street, dp_num, date, dp_name, installed_by, global_id, index, installed_photos_cls_check, installed_photos_far_check in result:
                    #     temp_map = {}
                    #     temp_map["dp_id"] = dp_id
                    #     if not date:
                    #         temp_map["installed_date"] = datetime.datetime.strptime('2000-01-01 00:00:00',
                    #                                                                 '%Y-%m-%d %H:%M:%S')
                    #     else:
                    #         temp_map["installed_date"] = date.strftime('%Y-%m-%d %H:%M:%S')
                    #     # temp_map["name"] = str(district) + str(shequ) + str(dp_street) + str(dp_name)
                    #     temp_map["cls_list"] = []
                    #     temp_map["far_list"] = []
                    #     temp_map["dp_name"] = dp_name
                    #     temp_map["dp_num"] = dp_num
                    #     temp_map["street"] = dp_street
                    #     temp_map["global_id"] = global_id
                    #     temp_map["installed_by"] = installed_by
                    #     temp_map["index"] = index
                    #     temp_map["installed_photos_cls_check"] = installed_photos_cls_check
                    #     temp_map["installed_photos_far_check"] = installed_photos_far_check
                    #     if cls:
                    #         if picture_city != "guangzhou":
                    #             filename = global_id + '_cls.jpg'
                    #         else:
                    #             filename = dp_id + '_cj01.jpg'
                    #         sum = 0
                    #         while (os.path.isfile(
                    #                 dydatas_basepath + '/gd_dp_photos/' + picture_city + "/" + filename)):  # 入参需要是绝对路径
                    #
                    #             full_path = dydatas_basepath + '/gd_dp_photos/' + picture_city + "/" + filename
                    #             pictures_full_path_list.append(full_path)
                    #
                    #             temp_map["cls_list"].append(filename)
                    #             sum += 1
                    #             #filename = dp_id + '_cj01_' + str(sum) + '.jpg'
                    #             if picture_city != "guangzhou":
                    #                 filename = global_id + '_cls' + str(sum) + '.jpg'
                    #             else:
                    #                 filename = dp_id + '_cj01_' + str(sum) + '.jpg'
                    #         # pictures_list_data.append(temp_map)
                    #     if far:
                    #         if picture_city != "guangzhou":
                    #             filename = global_id + '_far.jpg'
                    #         else:
                    #             filename = dp_id + '_cj01.jpg'
                    #         sum = 0
                    #         while (os.path.isfile(
                    #                 dydatas_basepath + '/gd_dp_photos/' + picture_city + "/" + filename)):  # 入参需要是绝对路径
                    #
                    #             full_path = dydatas_basepath + '/gd_dp_photos/' + picture_city + "/" + filename
                    #             pictures_full_path_list.append(full_path)
                    #
                    #             temp_map["far_list"].append(filename)
                    #             sum += 1
                    #             #filename = dp_id + '_cj01_' + str(sum) + '.jpg'
                    #             if picture_city != "guangzhou":
                    #                 filename = global_id + '_far' + str(sum) + '.jpg'
                    #             else:
                    #                 filename = dp_id + '_cj01_' + str(sum) + '.jpg'
                    #     pictures_list_data.append(temp_map)
                    #
                    # # 加个小排序，按安装时间排序
                    # # pictures_list_data.sort(key=lambda i: i["installed_date"])
                    #
                    # no_pictures_list_data = []
                    #
                    # # (installed_photos_far<=0 OR installed_photos_cls<=0) 是缺一张就算上
                    # # (installed_photos_far<=0 AND installed_photos_cls<=0) 是都缺的
                    # if not select_condition:
                    #     select_sql = select_sql + " WHERE " + "(installed_photos_far<=0 AND installed_photos_cls<=0) AND installed>0"
                    #
                    #     no_pictures_datas_len_sql = "SELECT count(`index`) FROM " + table_name + " WHERE " + "(installed_photos_far<=0 AND installed_photos_cls<=0) AND installed>0"
                    # else:
                    #     select_sql = select_sql + " AND " + "(installed_photos_far<=0 AND installed_photos_cls<=0) AND installed>0"
                    #
                    #     no_pictures_datas_len_sql = "SELECT count(`index`) FROM " + table_name + select_condition + " AND " + "(installed_photos_far<=0 AND installed_photos_cls<=0) AND installed>0"
                    # app.logger.info(no_pictures_datas_len_sql)
                    # cursor.execute(no_pictures_datas_len_sql)
                    #
                    # no_pictures_list_len = cursor.fetchall()
                    # no_pictures_list_len = no_pictures_list_len[0][0]
                    # app.logger.info("no_pictures_list_len %s", no_pictures_list_len)
                    #
                    # select_sql = select_sql + " ORDER BY installed_date, installed_by " + sql_limit
                    # app.logger.info(select_sql)
                    # cursor.execute(select_sql)
                    #
                    # result = cursor.fetchall()
                    #
                    # for dp_id, cls, far, dp_street, dp_num, date, dp_name, installed_by, global_id, index, installed_photos_cls_check, installed_photos_far_check in result:
                    #     temp_map = {}
                    #     temp_map["dp_id"] = dp_id
                    #     if not date:
                    #         temp_map["installed_date"] = datetime.datetime.strptime('2000-01-01 00:00:00',
                    #                                                                 '%Y-%m-%d %H:%M:%S')
                    #     else:
                    #         temp_map["installed_date"] = date.strftime('%Y-%m-%d %H:%M:%S')
                    #     # temp_map["name"] = str(district) + str(shequ) + str(dp_street) + str(dp_name)
                    #     temp_map["no_cls"] = 1
                    #     temp_map["no_far"] = 1
                    #     temp_map["dp_name"] = dp_name
                    #     temp_map["dp_num"] = dp_num
                    #     temp_map["street"] = dp_street
                    #     temp_map["installed_by"] = installed_by
                    #     temp_map["global_id"] = global_id
                    #     temp_map["index"] = index
                    #     temp_map["installed_photos_cls_check"] = installed_photos_cls_check
                    #     temp_map["installed_photos_far_check"] = installed_photos_far_check
                    #     if cls:
                    #
                    #         if picture_city != "guangzhou":
                    #             filename = global_id + '_cls.jpg'
                    #         else:
                    #             filename = dp_id + '_cj01.jpg'
                    #         sum = 0
                    #         while (os.path.isfile(
                    #                 dydatas_basepath + '/gd_dp_photos/' + picture_city + "/" + filename)):  # 入参需要是绝对路径
                    #             temp_map["no_cls"] = 0
                    #             sum += 1
                    #             #filename = dp_id + '_cj01_' + str(sum) + '.jpg'
                    #             if picture_city != "guangzhou":
                    #                 filename = global_id + '_cls' + str(sum) + '.jpg'
                    #             else:
                    #                 filename = dp_id + '_cj01_' + str(sum) + '.jpg'
                    #
                    #     if far:
                    #         if picture_city != "guangzhou":
                    #             filename = global_id + '_far.jpg'
                    #         else:
                    #             filename = dp_id + '_cj01.jpg'
                    #         sum = 0
                    #         while (os.path.isfile(
                    #                 dydatas_basepath + '/gd_dp_photos/' + picture_city + "/" + filename)):  # 入参需要是绝对路径
                    #             temp_map["no_far"] = 0
                    #             sum += 1
                    #             #filename = dp_id + '_cj01_' + str(sum) + '.jpg'
                    #             if picture_city != "guangzhou":
                    #                 filename = global_id + '_far' + str(sum) + '.jpg'
                    #             else:
                    #                 filename = dp_id + '_cj01_' + str(sum) + '.jpg'
                    #
                    #     no_pictures_list_data.append(temp_map)

                return  pictures_list_data, pictures_list_len, no_pictures_list_data, no_pictures_list_len, pictures_full_path_list

            else:
                if picture_city == "foshan":
                    database_name = 'ws_doorplate'
                    table_name = 'fs_dp'
                elif picture_city == "maoming":
                    database_name = 'ws_doorplate'
                    table_name = 'maoming_dp'
                else:
                    database_name = CITY.get_db_name(picture_city)
                    table_name = CITY.get_table_name(picture_city)

                # db = pymysql.connect("localhost", "root", "root", "丹灶数据库")
                db = pymysql.connect("localhost", "root", "root", database_name)
                # 使用cursor()方法获取操作游标
                cursor = db.cursor()

                # select_sql = "SELECT `index` FROM gis_ordered WHERE `DZBM` = " + "\'" + dzbm + "\'" + " LIMIT 1"
                if picture_type == "collected":
                    select_sql = "SELECT `global_id`,`{picture_type}_photos`, `street`, `dp_num`, `{picture_type}_date`, `DZMC`, `{picture_type}_by`, `index`, `{picture_type}_photos_check`, `dp_name` FROM " + table_name
                else:
                    select_sql = "SELECT `global_id`,`{picture_type}_photos_cls`,`{picture_type}_photos_far`, `street`, `dp_num`, `{picture_type}_date`, `DZMC`, `{picture_type}_by`, `index`, `{picture_type}_photos_cls_check`, `{picture_type}_photos_far_check`, `dp_name` FROM " + table_name
                select_sql = select_sql.format(picture_type=picture_type)
                # select_condition = 0
                select_condition = ''
                if request.args.get('district'):
                    district = request.args.get('district')
                    if not select_condition:
                        # select_sql += ' WHERE '
                        # select_condition = 1
                        select_condition += ' WHERE '
                    else:
                        # select_sql += ' AND '
                        select_condition += ' AND '
                    # select_sql += "district=" + '\"' + district + '\"'
                    select_condition += "district=" + '\"' + district + '\"'
                else:
                    district = ''
                if request.args.get('shequ'):
                    shequ = request.args.get('shequ')
                    if not select_condition:
                        # select_sql += ' WHERE '
                        # select_condition = 1
                        select_condition += ' WHERE '
                    else:
                        # select_sql += ' AND '
                        select_condition += ' AND '
                    # select_sql += "community=" + '\"' + shequ + '\"'
                    select_condition += "community=" + '\"' + shequ + '\"'
                else:
                    shequ = ''
                if request.args.get('date'):
                    date = request.args.get('date')
                    if not select_condition:
                        # select_sql += ' WHERE '
                        # select_condition = 1
                        select_condition += ' WHERE '
                    else:
                        # select_sql += ' AND '
                        select_condition += ' AND '
                    # select_sql += "installed_date like " + "\"%" + installed_date + "%\""
                    select_condition += "{picture_type}_date like " + "\"%" + date + "%\""
                    select_condition = select_condition.format(picture_type=picture_type)
                else:
                    date = ''

                # select_sql = select_sql + select_condition + sql_like_query
                # installed_date_start = '2000-01-01 00:00:00'
                # installed_date_end = common.format_ymdhms_time_now()
                if request.args.get('date_start') or request.args.get('date_end'):
                    date_start = request.args.get('date_start') if request.args.get(
                        'date_start') else '2000-01-01 00:00:00'
                    date_end = request.args.get('date_end') if request.args.get(
                        'date_end') else common.format_ymdhms_time_now()
                    if not select_condition:
                        # select_sql += ' WHERE '
                        # select_condition = 1
                        select_condition += ' WHERE '
                    else:
                        # select_sql += ' AND '
                        select_condition += ' AND '
                    # select_sql += "installed_date like " + "\"%" + installed_date + "%\""
                    select_condition += " {picture_type}_date >= " + "\"" + date_start + "\"" + " AND {picture_type}_date <= " + "\"" + date_end + "\""
                    select_condition = select_condition.format(picture_type=picture_type)

                if request.args.get('by'):
                    picture_type_by = request.args.get('by')
                    if not select_condition:
                        # select_sql += ' WHERE '
                        # select_condition = 1
                        select_condition += ' WHERE '
                    else:
                        # select_sql += ' AND '
                        select_condition += ' AND '
                    # select_sql += "installed_by=" + '\"' + installed_by + '\"'
                    select_condition += "{picture_type}_by=" + '\"' + picture_type_by + '\"'
                    select_condition = select_condition.format(picture_type=picture_type)
                else:
                    picture_type_by = ''

                contract_batch = ""
                contract_batch_sql = ""
                if request.args.get('contract_batch'):
                    contract_batch = request.args.get('contract_batch')
                    contract_batch_sql += " contract_batch=" + "\"" + contract_batch + "\""
                    if not select_condition:
                        # select_sql += ' WHERE '
                        # select_condition = 1
                        select_condition += ' WHERE '
                    else:
                        # select_sql += ' AND '
                        select_condition += ' AND '
                    select_condition += contract_batch_sql
                order_batch = ""
                order_batch_sql = ""
                if request.args.get('order_batch'):
                    order_batch = request.args.get('order_batch')
                    order_batch_sql += " order_batch=" + "\"" + order_batch + "\""
                    if not select_condition:
                        # select_sql += ' WHERE '
                        # select_condition = 1
                        select_condition += ' WHERE '
                    else:
                        # select_sql += ' AND '
                        select_condition += ' AND '
                    select_condition += order_batch_sql
                order_id = ""
                order_id_sql = ""
                if request.args.get('order_id'):
                    order_id = request.args.get('order_id')
                    order_id_sql += " order_id=" + "\"" + order_id + "\""
                    if not select_condition:
                        # select_sql += ' WHERE '
                        # select_condition = 1
                        select_condition += ' WHERE '
                    else:
                        # select_sql += ' AND '
                        select_condition += ' AND '
                    select_condition += order_id_sql

                if filter_condition_sql:
                    if not select_condition:
                        # select_sql += ' WHERE '
                        # select_condition = 1
                        select_condition += ' WHERE '
                        select_condition += filter_condition_sql
                    else:
                        # select_sql += ' AND '
                        select_condition += ' AND '
                        select_condition += filter_condition_sql

                all_select_datas_len_sql = "SELECT count(`index`) FROM " + table_name + select_condition
                app.logger.info(all_select_datas_len_sql)
                cursor.execute(all_select_datas_len_sql)

                pictures_list_len = cursor.fetchall()
                pictures_list_len = pictures_list_len[0][0]
                app.logger.info("pictures_list_len %s", pictures_list_len)

                select_sql = select_sql + select_condition
                all_select_sql = select_sql + " ORDER BY {picture_type}_date, {picture_type}_by " + sql_limit
                all_select_sql = all_select_sql.format(picture_type=picture_type)
                app.logger.info(all_select_sql)
                cursor.execute(all_select_sql)

                result = cursor.fetchall()

                # app.logger.info(result)
                pictures_list_data = []
                pictures_full_path_list = []

                #for global_id, cls, far, dp_street, dp_num, date, DZMC, installed_by, index, installed_photos_cls_check, installed_photos_far_check in result:
                for row_data in result:
                    if picture_type == "collected":
                        global_id = row_data[0]
                        cls = 0
                        far = row_data[1]
                        dp_street = row_data[2]
                        dp_num = row_data[3]
                        date = row_data[4]
                        DZMC = row_data[5]
                        picture_type_by = row_data[6]
                        index = row_data[7]
                        photos_cls_check = ""
                        photos_far_check = row_data[8]
                        dp_name = row_data[9]
                    else:
                        global_id = row_data[0]
                        cls = row_data[1]
                        far = row_data[2]
                        dp_street = row_data[3]
                        dp_num = row_data[4]
                        date = row_data[5]
                        DZMC = row_data[6]
                        picture_type_by = row_data[7]
                        index = row_data[8]
                        photos_cls_check = row_data[9]
                        photos_far_check = row_data[10]
                        dp_name = row_data[11]
                    temp_map = {}
                    temp_map["global_id"] = global_id
                    if not date:
                        temp_map["date"] = datetime.datetime.strptime('2000-01-01 00:00:00',
                                                                                '%Y-%m-%d %H:%M:%S')
                    else:
                        temp_map["date"] = date.strftime('%Y-%m-%d %H:%M:%S')
                    # temp_map["name"] = str(district) + str(shequ) + str(dp_street) + str(dp_num)
                    temp_map["cls_list"] = []
                    temp_map["far_list"] = []
                    temp_map["DZMC"] = DZMC
                    temp_map["dp_name"] = dp_name
                    temp_map["dp_num"] = dp_num
                    temp_map["street"] = dp_street
                    temp_map["by"] = picture_type_by
                    temp_map["index"] = index
                    temp_map["photos_cls_check"] = photos_cls_check
                    temp_map["photos_far_check"] = photos_far_check
                    if picture_type == "collected":
                        if cls:
                            pass
                        if far:
                            filename = str(index) + '_collected.jpg'

                            sum = 0
                            while (os.path.isfile(
                                    os.path.join(config.DY_DATAS_COLLECTED_PICTURES_PATH,
                                                 picture_city + "/" + filename))):  # 入参需要是绝对路径

                                full_path = os.path.isfile(
                                    os.path.join(config.DY_DATAS_COLLECTED_PICTURES_PATH,
                                                 picture_city + "/" + filename))

                                pictures_full_path_list.append(full_path)

                                temp_map["cls_list"].append(filename)
                                sum += 1
                                # filename = dp_id + '_cj01_' + str(sum) + '.jpg'

                                filename = str(index) + "_collected_" + str(sum) + '.jpg'
                    else:
                        if cls:

                            filename = global_id + '_cls.jpg'
                            sum = 0
                            while (os.path.isfile(
                                    dydatas_basepath + '/gd_dp_photos/' + picture_city + "/" + filename)):  # 入参需要是绝对路径

                                full_path = dydatas_basepath + '/gd_dp_photos/' + picture_city + "/" + filename
                                pictures_full_path_list.append(full_path)

                                temp_map["cls_list"].append(filename)
                                sum += 1
                                filename = global_id + '_cls_' + str(sum) + '.jpg'
                            # pictures_list_data.append(temp_map)
                        if far:
                            filename = global_id + '_far.jpg'
                            sum = 0
                            while (os.path.isfile(
                                    dydatas_basepath + '/gd_dp_photos/' + picture_city + "/" + filename)):  # 入参需要是绝对路径

                                full_path = dydatas_basepath + '/gd_dp_photos/' + picture_city + "/" + filename
                                pictures_full_path_list.append(full_path)

                                temp_map["far_list"].append(filename)
                                sum += 1
                                filename = global_id + '_far_' + str(sum) + '.jpg'
                    pictures_list_data.append(temp_map)

                # 加个小排序，按安装时间排序
                # pictures_list_data.sort(key=lambda i: i["installed_date"])

                no_pictures_list_data = []

                # (installed_photos_far<=0 OR installed_photos_cls<=0) 是缺一张就算上
                # (installed_photos_far<=0 AND installed_photos_cls<=0) 是都缺的
                if not select_condition:
                    select_sql = select_sql + " WHERE " + "(installed_photos_far<=0 AND installed_photos_cls<=0) AND installed>0"
                    no_pictures_datas_len_sql = "SELECT count(`index`) FROM " + table_name + " WHERE " + "(installed_photos_far<=0 AND installed_photos_cls<=0) AND installed>0"
                else:
                    select_sql = select_sql + " AND " + "(installed_photos_far<=0 AND installed_photos_cls<=0) AND installed>0"

                    no_pictures_datas_len_sql = "SELECT count(`index`) FROM " + table_name + select_condition + " AND " + "(installed_photos_far<=0 AND installed_photos_cls<=0) AND installed>0"
                app.logger.info(no_pictures_datas_len_sql)
                cursor.execute(no_pictures_datas_len_sql)

                no_pictures_list_len = cursor.fetchall()
                no_pictures_list_len = no_pictures_list_len[0][0]
                app.logger.info("no_pictures_list_len %s", no_pictures_list_len)

                select_sql = select_sql + " ORDER BY installed_date, installed_by " + sql_limit
                app.logger.info(select_sql)
                cursor.execute(select_sql)

                result = cursor.fetchall()

                #for global_id, cls, far, dp_street, dp_num, date, DZMC, installed_by, index, installed_photos_cls_check, installed_photos_far_check in result:
                for row_data in result:
                    if picture_type == "collected":
                        global_id = row_data[0]
                        cls = 0
                        far = row_data[1]
                        dp_street = row_data[2]
                        dp_num = row_data[3]
                        date = row_data[4]
                        DZMC = row_data[5]
                        picture_type_by = row_data[6]
                        index = row_data[7]
                        photos_cls_check = ""
                        photos_far_check = row_data[8]
                        dp_name = row_data[9]
                    else:
                        global_id = row_data[0]
                        cls = row_data[1]
                        far = row_data[2]
                        dp_street = row_data[3]
                        dp_num = row_data[4]
                        date = row_data[5]
                        DZMC = row_data[6]
                        picture_type_by = row_data[7]
                        index = row_data[8]
                        photos_cls_check = row_data[9]
                        photos_far_check = row_data[10]
                        dp_name = row_data[11]
                    temp_map = {}
                    temp_map["global_id"] = global_id
                    if not date:
                        temp_map["date"] = datetime.datetime.strptime('2000-01-01 00:00:00',
                                                                                '%Y-%m-%d %H:%M:%S')
                    else:
                        temp_map["date"] = date.strftime('%Y-%m-%d %H:%M:%S')
                    # temp_map["name"] = str(district) + str(shequ) + str(dp_street) + str(dp_num)
                    temp_map["no_cls"] = 1
                    temp_map["no_far"] = 1
                    temp_map["DZMC"] = DZMC
                    temp_map["dp_name"] = dp_name
                    temp_map["dp_num"] = dp_num
                    temp_map["street"] = dp_street
                    temp_map["by"] = picture_type_by
                    temp_map["index"] = index
                    temp_map["photos_cls_check"] = photos_cls_check
                    temp_map["photos_far_check"] = photos_far_check
                    if cls:

                        filename = global_id + '_cls.jpg'
                        sum = 0
                        while (os.path.isfile(
                                dydatas_basepath + '/gd_dp_photos/' + picture_city + "/" + filename)):  # 入参需要是绝对路径
                            temp_map["no_cls"] = 0
                            sum += 1
                            filename = global_id + '_cls_' + str(sum) + '.jpg'

                    if far:
                        filename = global_id + '_far.jpg'
                        sum = 0
                        while (os.path.isfile(
                                dydatas_basepath + '/gd_dp_photos/' + picture_city + "/" + filename)):  # 入参需要是绝对路径
                            temp_map["no_far"] = 0
                            sum += 1
                            filename = global_id + '_far_' + str(sum) + '.jpg'
                    no_pictures_list_data.append(temp_map)

                return pictures_list_data, pictures_list_len, no_pictures_list_data, no_pictures_list_len, pictures_full_path_list


        except:

            return jsonify(common.falseReturn('', "查询照片列表失败, 检查你的参数 " + str(request.args)))

    # 门牌照片上传
    @app.route('/pictures', methods=['GET', 'POST', 'PUT'])
    def pictures():
        app.logger.info("request: %s", request)

        # result = Auth.identify(Auth, request)
        # app.logger.info("状态: %s 用户: %s ", result.get('status'),  result.get('data'))
        # if (result['status'] and result['data']):
        #     pass
        # else:
        #     #return jsonify(result)
        #     pass


            # return json.dumps(result, ensure_ascii=False)
        # app.logger.info(request.data)
        # #app.logger.info(request.headers)
        # app.logger.info(request.form)
        # app.logger.info(request.json)
        # app.logger.info(request.stream)
        # app.logger.info(request.input_stream)
        # app.logger.info(request.get_data())
        # app.logger.info(request.stream.read())
        # request_json = request.get_json()
        msg = ""
        # if request.method == 'OPTIONS':
        #
        #     jsonStr = json.dumps(datas, ensure_ascii=False)
        #     resp = Response(jsonStr)
        #     resp.mimetype = 'application/json'
        #     resp.headers['Access-Control-Allow-Origin'] = '*'
        #     resp.status_code = 200
        #     return resp

        if request.method == 'PUT':
            result = Auth.identify(Auth, request)
            app.logger.info("状态: %s 用户: %s ", result.get('status'), result.get('data'))
            if (result['status'] and result['data']):
                pass
            else:
                # return jsonify(result)
                pass

            request_form = request.get_json()
            type = request_form.get('type')
            if type == REQUEST_TYPE.picture_check.name:
                try:
                    app.logger.info("检查照片")
                    picture_city = request_form.get('city')
                    picture_type = request_form.get('picture_type')
                    picture_index = request_form.get('index')
                    if request_form.get('global_id'):
                     global_id = request_form.get('global_id')
                    check_type = request_form.get('check')
                    app.logger.info("要修改的照片的城市是: %s index: %s check_type: %s picture_type: %s", picture_city, picture_index, check_type, picture_type)

                    db_name = CITY.get_db_name(picture_city)
                    table_name = CITY.get_table_name(picture_city)
                    db = pymysql.connect("localhost", "root", "root", db_name)
                    cursor = db.cursor()

                    set_type = "installed_photos_cls_check"
                    if picture_type=='far':
                        set_type = "installed_photos_far_check"
                    elif picture_type=='cls':
                        set_type = "installed_photos_cls_check"

                    if request.form.get('installed_photos_check_by'):
                        installed_photos_check_by = request.form.get('installed_photos_check_by')
                    else:
                        try:
                            installed_photos_check_by = result['data']['username']
                        except:
                            installed_photos_check_by = "未知"

                    installed_photos_check_date = common.format_ymdhms_time_now()

                    update_sql = "UPDATE " + table_name + " SET `" + set_type + "`=\'" + check_type + "\', installed_photos_{picture_type}_check_by=\"{installed_photos_check_by}\" " + \
                                                                                                      ", installed_photos_{picture_type}_check_date=\"{installed_photos_check_date}\" " + \
                                                                                                      "  WHERE " + " `index`=" + str(picture_index)
                    update_sql = update_sql.format(picture_type=picture_type, installed_photos_check_by=installed_photos_check_by, installed_photos_check_date=installed_photos_check_date)
                    cursor.execute(update_sql)
                    db.commit()
                    db.close()
                    #app.logger.info(update_sql)
                    cache.clear()
                    return jsonify(common.trueReturn("", "照片审核成功"))

                except:
                    db.close()
                    app.logger.info("照片审核不成功，检查传参有无错误")
                    app.logger.info(update_sql)
                    return jsonify(common.falseReturn("", "照片审核不成功，让前端人员检查传参有无错误"))

            elif type == REQUEST_TYPE.pictures_MD5.name:
                app.logger.info("照片MD5更新")

                db_name = config.DB_NAME # 默认数据库
                table_name = config.PICTURES_MD5_TABLE_NAME
                pictures_path = config.DY_DATAS_PICTURES_PATH
                picture_city = request_form.get('city')
                if not request_form.get('city'):
                    app.logger.info("所有城市的照片MD5都将更新")
                    picture_city = ""
                else:
                    picture_city = request_form.get('city')
                    app.logger.info("要更新照片MD5的城市为%s", picture_city)
                    #pictures_path = os.path.join(pictures_path, picture_city)

                status, total_update_list = pictures_operation.update_MD5_db(db_name, table_name, pictures_path, picture_city=picture_city)

                if status:
                    cache.clear()
                    app.logger.info("照片MD5更新成功")
                    return jsonify(common.trueReturn("", "照片MD5更新成功"))
                else:
                    app.logger.info("照片MD5更新不成功")
                    return jsonify(common.falseReturn("", "照片MD5更新不成功，让前端人员检查传参有无错误"))



        elif request.method == 'GET':
            if request.form.get('type'):
                type = request.form.get('type')
            elif request.args.get('type'):
                type = request.args.get('type')
            elif request.get_json().get('type'):
                type = request.get_json().get('type')
            else:
                return jsonify(common.falseReturn("", "获取照片MD5不成功，让前端人员检查传参有无错误，可能是body传type出错"))

            if type == REQUEST_TYPE.picture_show.name:

                app.logger.info("获取照片")
                picture_path = config.DY_DATAS_PICTURES_PATH
                picture_city = request.args.get('city')
                picture_name = request.args.get('name')


                if request.args.get("picture_type") == REQUEST_TYPE.collected.name:
                    picture_type = "collected"

                    picture_path_with_city = os.path.join(config.DY_DATAS_COLLECTED_PICTURES_PATH, picture_city)
                    filename = os.path.join(picture_path_with_city, picture_name)

                # elif request_type == REQUEST_TYPE.installed.name:
                else:
                    # 默认为安装照片
                    picture_type = "installed"



                    picture_path_with_city = os.path.join(picture_path, picture_city)
                    filename = os.path.join(picture_path_with_city, picture_name)

                return send_file(filename, mimetype='image/jpeg')

            elif type == REQUEST_TYPE.pictures_MD5.name:

                app.logger.info("获取照片MD5")
                if not request.form.get('city'):
                    app.logger.info("获取所有城市的照片MD5")
                    picture_city = ""
                else:
                    picture_city = request.form.get('city')
                    app.logger.info("要获取照片MD5的城市为%s", picture_city)

                if not request.form.get('iden_id_batch'):
                    picture_batch_list = []
                else:
                    picture_batch_list = request.form.get('iden_id_batch').strip().split(",")
                    picture_batch_list = [str(i).strip() for i in picture_batch_list]
                    app.logger.info("要查询的照片iden_id数组大小为%s", str(len(picture_batch_list)))

                if not request.form.get('MD5_batch'):
                    picture_MD5_batch_list = []
                else:
                    picture_MD5_batch_list = request.form.get('MD5_batch').strip().split(",")
                    picture_MD5_batch_list = [str(i).strip() for i in picture_MD5_batch_list]
                    app.logger.info("要查询的照片MD5数组大小为%s", str(len(picture_MD5_batch_list)))

                #print(picture_batch_list)

                db_name = config.DB_NAME  # 默认数据库
                table_name = config.PICTURES_MD5_TABLE_NAME

                status, file_MD5_map = pictures_operation.get_MD5(db_name, table_name, city=picture_city, picture_batch_list=picture_batch_list, picture_MD5_batch_list=picture_MD5_batch_list)

                if status:
                    return jsonify(common.trueReturn({"file_MD5_map": file_MD5_map}, "获取照片MD5成功"))
                else:
                    app.logger.info("获取照片MD5不成功")
                    return jsonify(common.falseReturn("", "获取照片MD5不成功，让前端人员检查传参有无错误"))

            # elif type == REQUEST_TYPE.pictures_package.name:
            #
            #     app.logger.info("照片打包")
            #     '''
            #     返回照片压缩包的下载路径
            #     '''
            #     picture_path = config.DY_DATAS_PICTURES_PATH
            #     picture_city = request.args.get('city')
            #     picture_name = request.args.get('name')
            #
            #     picture_path_with_city = os.path.join(picture_path, picture_city)
            #     filename = os.path.join(picture_path_with_city, picture_name)
            #
            #     return send_file(filename, mimetype='image/jpeg')

            elif type == REQUEST_TYPE.pictures_list.name or type == REQUEST_TYPE.pictures_package.name:

                try:
                    pictures_list_data, pictures_list_len, no_pictures_list_data, no_pictures_list_len, pictures_full_path_list = pictures_get(request)
                except:
                    return jsonify(common.falseReturn('', "查询照片列表失败, 检查你的参数 " + str(request.args)))

                if type == REQUEST_TYPE.pictures_list.name:

                    return jsonify(common.trueReturn(
                        {"pictures_list": pictures_list_data, "no_pictures_list": no_pictures_list_data,
                         "pictures_list_len": pictures_list_len, "no_pictures_list_len": no_pictures_list_len},
                        "查询照片列表成功"))
                elif type == REQUEST_TYPE.pictures_package.name:

                    app.logger.info("打包照片")
                    pictures_number = len(pictures_full_path_list)
                    app.logger.info("数量为：%s", pictures_number)
                    #print("pictures_full_path_list", pictures_full_path_list)
                    picture_zip_path = files_operation.files_to_zip(pictures_full_path_list)
                    if picture_zip_path:
                        return jsonify(common.trueReturn(
                            {"picture_zip_path": picture_zip_path, "pictures_number": pictures_number}, "打包照片成功"))
                    else:
                        return jsonify(common.falseReturn({"picture_zip_path": picture_zip_path}, "打包照片失败"))

            elif type == REQUEST_TYPE.pictures_package_without_query.name:
                app.logger.info("通过前端传入文件名列表打包照片")

                if request.get_json():
                    request_data = request.get_json()
                else:
                    request_data = request.form

                #print("request.form.get('pictures_filename_list')",request_data.get('pictures_filename_list'))
                pictures_filename_list = request_data.get('pictures_filename_list').split(',')
                #print("pictures_filename_list",pictures_filename_list)
                city = request_data.get('city')
                pictures_full_path_list = []

                for i in pictures_filename_list:
                    pictures_full_path_list.append(os.path.join(config.DY_DATAS_PICTURES_PATH, city+'/'+i))
                pictures_number = len(pictures_full_path_list)
                app.logger.info("打包的文件为: %s", pictures_full_path_list)

                app.logger.info("数量为：%s", pictures_number)
                picture_zip_path = files_operation.files_to_zip(pictures_full_path_list)
                if picture_zip_path:
                    return jsonify(common.trueReturn(
                        {"picture_zip_path": picture_zip_path, "pictures_number": pictures_number}, "打包照片成功"))
                else:
                    return jsonify(common.falseReturn({"picture_zip_path": picture_zip_path}, "打包照片失败"))



        elif request.method == 'POST':
            result = Auth.identify(Auth, request)
            app.logger.info("状态: %s 用户: %s ", result.get('status'), result.get('data'))
            if (result['status'] and result['data']):
                pass
            else:
                # return jsonify(result)
                pass

            if not request.form.get('type') or request.form.get('type') == REQUEST_TYPE.picture.name:
                app.logger.info("有照片要上传")
                app.logger.info(request.files)
                if 'file' not in request.files:
                    return jsonify(common.falseReturn("", "上传失败，可能file参数不对"))
                f = request.files['file']
                # app.logger.info(f)
                # app.logger.info(type(f))

                # app.logger.info(request.form)
                city = str(request.form.get('city'))
                if not city:
                    city = "未填写"
                filename = str(request.form.get('filename'))
                # if city == "foshan":
                # 注意：没有的文件夹一定要先创建，不然会提示没有该路径

                #filename = secure_filename(filename) # 2019-10-29 注释
                filename_pre = filename.split('.')[0]
                #global_id = filename.split('.')[0].split('_')[0]
                select_col_data = filename.split('.')[0].split('_')[0]
                picture_type = filename.split('.')[0].split('_')[1]
                filesuffix = filename.split('.')[1]

                save_dir = config.DY_DATAS_PICTURES_PATH + "/" + city + "/"

                if not os.path.isdir(save_dir):
                    files_operation.make_dirs(save_dir)


                upload_status, upload_path = pictures_operation.upload_picture(save_dir, f, filename)

                if not upload_status:
                    return jsonify(
                        common.falseReturn('', '已经有与filename相同命名的照片且md5完全一致，' + filename, addition=common.false_Type.exist))

                database_name = 'ws_doorplate'
                table_name = 'fs_dp'


                # 照片的上传用的select id
                # 广州为 门牌id
                # 其他城市 默认全球唯一码
                select_col = "global_id"
                if city == "foshan":
                    database_name = 'ws_doorplate'
                    table_name = 'fs_dp'
                if city == "guangzhou":
                    database_name = 'ws_doorplate'
                    table_name = 'gz_orders'
                    select_col = "dp_id"
                    picture_type = "far"
                if city == "maoming":
                    database_name = 'ws_doorplate'
                    table_name = 'maoming_dp'
                else:
                    database_name = CITY.get_db_name(city)
                    table_name = CITY.get_table_name(city)

                # db = pymysql.connect("localhost", "root", "root", "丹灶数据库")
                db = pymysql.connect("localhost", "root", "root", database_name)
                # 使用cursor()方法获取操作游标
                cursor = db.cursor()

                # select_sql = "SELECT `index` FROM gis_ordered WHERE `DZBM` = " + "\'" + dzbm + "\'" + " LIMIT 1"

                select_sql = "SELECT `index` FROM " + table_name + " WHERE `{select_col}` = " + "\'{select_col_data}\'" + " LIMIT 1"
                select_sql = select_sql.format(select_col=select_col, select_col_data=select_col_data)

                if select_sql:
                    try:
                        # app.logger.info(select_sql)
                        cursor.execute(select_sql)
                        # app.logger.info(cursor.fetchall())
                        if cursor.fetchall():
                            pass
                        else:
                            # 提交到数据库执行
                            db.commit()
                            # 关闭数据库连接
                            db.close()
                            return jsonify(common.falseReturn("", "检查照片名称有无错误", addition=common.false_Type.global_id_false))
                    except:
                        # 如果发生错误则回滚
                        # traceback.print_exc()
                        db.rollback()
                        # 关闭数据库连接
                        db.close()
                        return jsonify(common.falseReturn("", "上传失败"))

                # sql = "UPDATE gis_ordered  SET `installed_photos`=`installed_photos`+1 " + \
                #       " WHERE `DZBM` = " + "\'" + dzbm + "\'"

                # sql = "UPDATE " + table_name + " SET `installed_photos_" + picture_type + "`=`installed_photos_" + picture_type + "`+1 " + \
                #       " WHERE `global_id` = " + "\'" + global_id + "\'"

                if request.form.get('installed_photos_upload_by'):
                    installed_photos_upload_by = request.form.get('installed_photos_upload_by')
                else:
                    installed_photos_upload_by = "未知"

                installed_photos_upload_date = common.format_ymdhms_time_now()
                # installed_photos_upload_date = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                # installed_photos_upload_date = datetime.datetime.now().strftime(common.format_ymdhms_time)

                sql = "UPDATE " + table_name + " SET `installed_photos_{picture_type}`=`installed_photos_{picture_type}`+1 , " + \
                                               "installed_photos_{picture_type}_upload_by=\"{installed_photos_upload_by}\", " + \
                                               "installed_photos_{picture_type}_upload_date=\"{installed_photos_upload_date}\" " + \
                          " WHERE `{select_col}` = " + "\'{select_col_data}\'"


                sql = sql.format(picture_type=picture_type,
                                 select_col=select_col,
                                 select_col_data=select_col_data,
                                 installed_photos_upload_by=installed_photos_upload_by,
                                 installed_photos_upload_date=installed_photos_upload_date)
                print(sql)

                if sql:
                    try:
                        app.logger.info(sql)
                        cursor.execute(sql)
                        # app.logger.info(cursor.fetchall())
                        # 提交到数据库执行
                        db.commit()
                        # 关闭数据库连接
                        db.close()
                        cache.clear()

                        '''
                        更新MD5数据库
                        insert_photos_MD5_data_list=[[city、file_name、iden_id、MD5]]
                        '''
                        insert_photos_files_list = [upload_path]
                        insert_photos_MD5_status = pictures_operation.update_MD5_db(database_name,
                                                                                    config.PICTURES_MD5_TABLE_NAME,
                                                                                    picture_city=city,
                                                                                    files_list=insert_photos_files_list,
                                                                                    only_insert=True)
                        if not insert_photos_MD5_status:
                            addtion_msg = "上传成功，更新到数据库成功，照片文件成功保存，但更新到MD5数据库失败。"
                            #     return jsonify(common.falseReturn("", "上传失败！更新到数据库成功，照片文件成功解压缩，但更新到MD5数据库失败"))
                        else:
                            addtion_msg = "上传成功，更新到数据库成功，照片文件成功保存，更新到MD5数据库成功。"

                        return jsonify(common.trueReturn("", addtion_msg + msg))
                    except:
                        # 如果发生错误则回滚
                        # traceback.print_exc()
                        db.rollback()
                        # 关闭数据库连接
                        db.close()
                        return jsonify(common.falseReturn("", "上传失败"))

            elif request.form.get('type') == REQUEST_TYPE.collected_picture.name:
                app.logger.info("有采集照片要上传")
                app.logger.info(request.files)
                if 'file' not in request.files:
                    return jsonify(common.falseReturn("", "上传失败，可能file参数不对"))
                f = request.files['file']
                # app.logger.info(f)
                # app.logger.info(type(f))

                # app.logger.info(request.form)
                city = str(request.form.get('city'))
                if not city:
                    city = "未填写"
                filename = str(request.form.get('filename'))
                # 注意：没有的文件夹一定要先创建，不然会提示没有该路径
                filename = secure_filename(filename)
                filename_pre = filename.split('.')[0]
                select_col_data = filename.split('.')[0].split('_')[0]
                #picture_type = filename.split('.')[0].split('_')[1]
                filesuffix = filename.split('.')[1]

                save_dir = config.DY_DATAS_COLLECTED_PICTURES_PATH + "/" + city + "/"

                if not os.path.isdir(save_dir): # 目录不存在时新建目录
                    files_operation.make_dirs(save_dir)

                upload_status, upload_path = pictures_operation.upload_picture(save_dir, f, filename)

                if not upload_status:
                    return jsonify(
                        common.falseReturn('', '已经有与filename相同命名的照片且md5完全一致，' + filename, addition=common.false_Type.exist))

                database_name = 'ws_doorplate'
                table_name = 'fs_dp'

                # 照片的上传用的select id
                # 广州为 门牌id
                # 其他城市 默认全球唯一码
                select_col = "index"
                if city == "foshan":
                    database_name = 'ws_doorplate'
                    table_name = 'fs_dp'
                if city == "guangzhou":
                    database_name = 'ws_doorplate'
                    table_name = 'gz_orders'
                if city == "maoming":
                    database_name = 'ws_doorplate'
                    table_name = 'maoming_dp'
                else:
                    database_name = CITY.get_db_name(city)
                    table_name = CITY.get_table_name(city)

                # db = pymysql.connect("localhost", "root", "root", "丹灶数据库")
                db = pymysql.connect("localhost", "root", "root", database_name)
                # 使用cursor()方法获取操作游标
                cursor = db.cursor()

                # select_sql = "SELECT `index` FROM gis_ordered WHERE `DZBM` = " + "\'" + dzbm + "\'" + " LIMIT 1"

                select_sql = "SELECT `index` FROM " + table_name + " WHERE `{select_col}` = " + "\'{select_col_data}\'" + " LIMIT 1"
                select_sql = select_sql.format(select_col=select_col, select_col_data=select_col_data)

                if select_sql:
                    try:
                        # app.logger.info(select_sql)
                        cursor.execute(select_sql)
                        # app.logger.info(cursor.fetchall())
                        if cursor.fetchall():
                            pass
                        else:
                            # 提交到数据库执行
                            db.commit()
                            # 关闭数据库连接
                            db.close()
                            return jsonify(
                                common.falseReturn("", "检查照片名称有无错误", addition=common.false_Type.name_false))
                    except:
                        # 如果发生错误则回滚
                        # traceback.print_exc()
                        db.rollback()
                        # 关闭数据库连接
                        db.close()
                        return jsonify(common.falseReturn("", "上传失败"))

                # sql = "UPDATE gis_ordered  SET `installed_photos`=`installed_photos`+1 " + \
                #       " WHERE `DZBM` = " + "\'" + dzbm + "\'"

                # sql = "UPDATE " + table_name + " SET `installed_photos_" + picture_type + "`=`installed_photos_" + picture_type + "`+1 " + \
                #       " WHERE `global_id` = " + "\'" + global_id + "\'"

                if request.form.get('upload_by'):
                    upload_by = request.form.get('upload_by')
                else:
                    upload_by = "未知"

                upload_date = common.format_ymdhms_time_now()
                # installed_photos_upload_date = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                # installed_photos_upload_date = datetime.datetime.now().strftime(common.format_ymdhms_time)

                sql = "UPDATE " + table_name + " SET `collected_photos`=`collected_photos`+1 , " + \
                      "collected_photos_upload_by=\"{collected_photos_upload_by}\", " + \
                      "collected_photos_upload_date=\"{collected_photos_upload_date}\" " + \
                      " WHERE `{select_col}` = " + "\'{select_col_data}\'"

                sql = sql.format(select_col=select_col,
                                 select_col_data=select_col_data,
                                 collected_photos_upload_by=upload_by,
                                 collected_photos_upload_date=upload_date)
                print(sql)

                if sql:
                    try:
                        app.logger.info(sql)
                        cursor.execute(sql)
                        # app.logger.info(cursor.fetchall())
                        # 提交到数据库执行
                        db.commit()
                        # 关闭数据库连接
                        db.close()
                        cache.clear()

                        '''
                        更新MD5数据库
                        insert_photos_MD5_data_list=[[city、file_name、iden_id、MD5]]
                        '''
                        insert_photos_files_list = [upload_path]
                        insert_photos_MD5_status = pictures_operation.update_MD5_db(database_name,
                                                                                    config.PICTURES_MD5_TABLE_NAME,
                                                                                    picture_city=city,
                                                                                    files_list=insert_photos_files_list,
                                                                                    only_insert=True)
                        if not insert_photos_MD5_status:
                            addtion_msg = "上传成功，更新到数据库成功，照片文件成功保存，但更新到MD5数据库失败。"
                            #     return jsonify(common.falseReturn("", "上传失败！更新到数据库成功，照片文件成功解压缩，但更新到MD5数据库失败"))
                        else:
                            addtion_msg = "上传成功，更新到数据库成功，照片文件成功保存，更新到MD5数据库成功。"

                        return jsonify(common.trueReturn("", addtion_msg + msg))
                    except:
                        # 如果发生错误则回滚
                        # traceback.print_exc()
                        db.rollback()
                        # 关闭数据库连接
                        db.close()
                        return jsonify(common.falseReturn("", "上传失败"))

            elif request.form.get('type') == REQUEST_TYPE.pictures_package.name:
                '''
                照片压缩包上传
                2019-07-25
                version 0.8
                '''
                app.logger.info("照片压缩包上传")

                if request.form.get("city"):
                    city = request.form.get("city")
                else:
                    city = ""
                if not city or not CITY.has_key(city):
                    return jsonify(common.falseReturn("", "上传失败！未传city参数，或者城市不存在"))

                if request.form.get("picture_type") == REQUEST_TYPE.collected.name:
                    picture_type = "collected"
                    test_unzip_path = os.path.join(config.DY_DATAS_COLLECTED_PICTURES_PATH, city)

                # elif request_type == REQUEST_TYPE.installed.name:
                else:
                    # 默认为安装照片
                    picture_type = "installed"
                    test_unzip_path = os.path.join(config.DY_DATAS_PICTURES_PATH, city)
                app.logger.info("照片类型picture_type：%s", picture_type)

                if request.form.get("only_check"): # 只进行查重操作
                    only_check = int(request.form.get("only_check"))
                else:
                    only_check = 0
                if request.form.get("file_from"): # 文件来源
                    file_from = request.form.get("file_from")
                else:
                    try:
                        file_from = request.files['file'].filename
                    except:
                        file_from = "未填写"
                    print("file_from: ", file_from)
                #if request.form.get("installed_by"):
                if request.form.get("by"):
                    #installed_by = request.form.get("installed_by")
                    picture_type_by = request.form.get("by")
                    app.logger.info("安装/采集 人: %s", picture_type_by)
                else:
                    picture_type_by = ""
                    app.logger.info("没有传安装人参数，不更新安装人")
                if request.form.get("mark") == 1 or request.form.get("mark") == str(1):
                    mark_picture_type = int(request.form.get("mark"))
                    app.logger.info("标记安装/采集")
                else:
                    mark_picture_type = 0
                    app.logger.info("不标记安装")

                if request.form.get("date"):
                    picture_type_date = str(request.form.get("date"))
                    app.logger.info("更新安装/采集日期 %s", picture_type_date)
                else:
                    picture_type_date = ""

                if request.form.get('photos_upload_by'):
                    picture_type_photos_upload_by = request.form.get('photos_upload_by')
                else:
                    try:
                        picture_type_photos_upload_by = result['data']['username']
                    except:
                        picture_type_photos_upload_by = "未知"

                picture_type_photos_upload_date = common.format_ymdhms_time_now()






                app.logger.info("城市 %s", city)

                if request.form.get("upload_path"):
                    upload_path = request.form.get("upload_path")
                else:
                    try:
                        f = request.files['file']
                    except:
                        return jsonify(common.falseReturn("", "上传失败！未传file"))
                    temp_file = tempfile.TemporaryFile()
                    f.save(temp_file)
                    temp_file.seek(0)
                    upload_file_MD5 = get_MD5.GetFileMd5_from_file(temp_file)
                    app.logger.info("upload_file_MD5 %s", upload_file_MD5)
                    #filename_pre = "imgs_" + file_from + "_" + common.format_ymdhms_time_now_for_filename()
                    filename_pre = "imgs_" + file_from
                    filesuffix = 'zip'
                    filename = filename_pre + '.' + filesuffix
                    raw_filename = filename
                    file_need_save = 1
                    sum = 0
                    while (os.path.isfile(os.path.join(config.TEMP_DOWNLOAD_DATAS_PATH, filename))):  # 入参需要是绝对路径
                        # temp_MD5 = get_MD5.GetFileMd5(dydatas_basepath + '/gd_dp_photos/' + city + "/" + filename)
                        temp_MD5 = get_MD5.GetFileMd5(os.path.join(config.TEMP_DOWNLOAD_DATAS_PATH, filename))
                        app.logger.info("temp_MD5 %s", temp_MD5)
                        if upload_file_MD5 != temp_MD5:
                            sum += 1
                            filename = filename_pre + "_" + str(sum) + '.' + filesuffix
                        else:
                            file_need_save = 0
                            break

                    upload_path = os.path.join(config.TEMP_DOWNLOAD_DATAS_PATH, filename)
                    if file_need_save == 1:
                        f.stream.seek(0)
                        f.save(upload_path)
                    app.logger.info("文件保存在：%s", upload_path)

                database_name = 'ws_doorplate'
                table_name = 'fs_dp'
                if city == "foshan":
                    database_name = 'ws_doorplate'
                    table_name = 'fs_dp'
                if city == "guangzhou":
                    database_name = 'ws_doorplate'
                    table_name = 'gz_orders'
                if city == "maoming":
                    database_name = 'ws_doorplate'
                    table_name = 'maoming_dp'
                else:
                    database_name = CITY.get_db_name(city)
                    table_name = CITY.get_table_name(city)

                
                
                status, files_name_list = files_operation.zip_to_files(upload_path, test_unzip_path, namelist=1, picture_type=picture_type)
                if not status:
                    return jsonify(common.falseReturn("", "上传失败！解压过程中出错"))

                #if only_check:
                    # status, files_name_list, saved_files_name_list, not_saved_files_name_list \
                    #     = files_operation.zip_to_files(upload_path, test_unzip_path, need_save=0)
                    # saved_files_id_list = []
                    # for i in saved_files_name_list:
                    #     try:
                    #         saved_files_id_list.append(i.split("_")[0])
                    #     except:
                    #         pass
                    # not_saved_files_id_list = []
                    # for i in not_saved_files_name_list:
                    #     try:
                    #         not_saved_files_id_list.append(i.split("_")[0])
                    #     except:
                    #         pass
                    # return jsonify(common.trueReturn({"saved_files_name_list": saved_files_name_list,
                    #                                   "saved_files_name_list_len": len(saved_files_name_list),
                    #                                   "saved_files_id_list": saved_files_id_list,
                    #                                   "saved_files_id_list_len": len(saved_files_id_list),
                    #                                   "not_saved_files_name_list": not_saved_files_name_list,
                    #                                   "not_saved_files_name_list_len": len(not_saved_files_name_list),
                    #                                   "not_saved_files_id_list": not_saved_files_id_list,
                    #                                   "not_saved_files_id_list_len": len(not_saved_files_id_list),
                    #                                   "upload_path": upload_path}, "上传成功"))
                global_id_far_list = []
                global_id_cls_list = []
                global_id_far_file_list = []
                global_id_cls_file_list = []
                for i in files_name_list:
                    (filepath, temp_file) = os.path.split(i)
                    if not temp_file:
                        continue
                    elif temp_file.find('cls') >= 0 and temp_file[0] != '.':
                        global_id_cls_list.append(temp_file.split('_')[0])
                        global_id_cls_file_list.append(i)
                        #app.logger.info(i)
                    elif (temp_file.find('far') >= 0 or temp_file.find('cj01') >= 0) and temp_file[0] != '.':
                        global_id_far_list.append(temp_file.split('_')[0])
                        global_id_far_file_list.append(i)
                        #app.logger.info(i)
                    elif city == "guangzhou" and temp_file[0] != '.':
                    #elif city != "maoming" and city != "foshan" and temp_file[0] != '.':
                        # 临时为广州门牌处理
                        global_id_far_list.append(os.path.splitext(temp_file)[0])
                        global_id_far_file_list.append(i)
                if only_check:
                    status, files_name_list, saved_files_name_list, not_saved_files_name_list \
                        = files_operation.zip_to_files(upload_path, test_unzip_path, members=global_id_cls_file_list + global_id_far_file_list, need_save=0)
                    saved_files_id_list = []
                    for i in saved_files_name_list:
                        try:
                            saved_files_id_list.append(i.split("_")[0])
                        except:
                            pass
                    not_saved_files_id_list = []
                    for i in not_saved_files_name_list:
                        try:
                            not_saved_files_id_list.append(i.split("_")[0])
                        except:
                            pass
                    return jsonify(common.trueReturn({"saved_files_name_list": saved_files_name_list,
                                                      "saved_files_name_list_len": len(saved_files_name_list),
                                                      "saved_files_id_list": saved_files_id_list,
                                                      "saved_files_id_list_len": len(saved_files_id_list),
                                                      "not_saved_files_name_list": not_saved_files_name_list,
                                                      "not_saved_files_name_list_len": len(not_saved_files_name_list),
                                                      "not_saved_files_id_list": not_saved_files_id_list,
                                                      "not_saved_files_id_list_len": len(not_saved_files_id_list),
                                                      "upload_path": upload_path}, "上传成功"))
                #app.logger.info("global_id_far_list", global_id_far_list)
                #app.logger.info("global_id_cls_list", global_id_cls_list)
                #if city != "maoming" and city != "foshan":
                else:
                    if city =="guangzhou":
                        if global_id_far_list:
                            update_photos_status = mysql.update_photos(database_name,
                                                                       table_name,
                                                                       picture_type=picture_type,
                                                                       dp_id_far_list=global_id_far_list,
                                                                       picture_type_by=picture_type_by,
                                                                       mark_picture_type=mark_picture_type,
                                                                       picture_type_date=picture_type_date,
                                                                       picture_type_photos_upload_by=picture_type_photos_upload_by,
                                                                       picture_type_photos_upload_date=picture_type_photos_upload_date,
                                                                       file_from=file_from)
                            if update_photos_status:

                                status, files_name_list, saved_files_name_list, not_saved_files_name_list \
                                    = files_operation.zip_to_files(upload_path, test_unzip_path, members=global_id_far_file_list, city=city)
                                if not status:
                                    return jsonify(common.falseReturn("", "上传失败！更新到数据库成功，但照片文件并未成功解压缩"))
                            else:
                                return jsonify(common.falseReturn("", "上传失败！更新到数据库时出错"))
                        if status:
                            cache.clear()  # 清除缓存
                            saved_files_id_list = []
                            for i in saved_files_name_list:
                                try:
                                    saved_files_id_list.append(i.split("_")[0])
                                except:
                                    pass
                            not_saved_files_id_list = []
                            for i in not_saved_files_name_list:
                                try:
                                    not_saved_files_id_list.append(i.split("_")[0])
                                except:
                                    pass
                            '''
                            更新MD5数据库
                            insert_photos_MD5_data_list=[[city、file_name、iden_id、MD5]]
                            '''
                            insert_photos_MD5_status = False
                            if len(saved_files_name_list) > 0:
                                insert_photos_files_list = [
                                    os.path.join(os.path.join(config.DY_DATAS_PICTURES_PATH, city), i) for i in
                                    saved_files_name_list]
                                insert_photos_MD5_status = pictures_operation.update_MD5_db(database_name,
                                                                                            config.PICTURES_MD5_TABLE_NAME,
                                                                                            picture_city=city,
                                                                                            files_list=insert_photos_files_list,
                                                                                            only_insert=True)
                            else:
                                app.logger.info("saved_files_name_list 为空，不需要更新MD5数据库")

                            if not insert_photos_MD5_status:
                                addtion_msg = "上传成功，更新到数据库成功，照片文件成功解压缩，但更新到MD5数据库失败，可能是照片已经存在不需要更新"
                                #     return jsonify(common.falseReturn("", "上传失败！更新到数据库成功，照片文件成功解压缩，但更新到MD5数据库失败"))
                            else:
                                addtion_msg = "上传成功，更新到数据库成功，照片文件成功解压缩, 更新到MD5数据库成功"
                            return jsonify(common.trueReturn({"saved_files_name_list": saved_files_name_list,
                                                              "saved_files_name_list_len": len(saved_files_name_list),
                                                              "saved_files_id_list": saved_files_id_list,
                                                              "saved_files_id_list_len": len(saved_files_id_list),
                                                              "not_saved_files_name_list": not_saved_files_name_list,
                                                              "not_saved_files_name_list_len": len(not_saved_files_name_list),
                                                              "not_saved_files_id_list": not_saved_files_id_list,
                                                              "not_saved_files_id_list_len": len(not_saved_files_id_list),
                                                              "upload_path": upload_path}, addtion_msg))
                    else:
                        cls_saved_files_name_list = []
                        cls_not_saved_files_name_list = []
                        if global_id_cls_list:
                            update_photos_status = mysql.update_photos(database_name,
                                                                       table_name,
                                                                       picture_type=picture_type,
                                                                       global_id_cls_list=global_id_cls_list,
                                                                       picture_type_by=picture_type_by,
                                                                       mark_picture_type=mark_picture_type,
                                                                       picture_type_date=picture_type_date,
                                                                       picture_type_photos_upload_by=picture_type_photos_upload_by,
                                                                       picture_type_photos_upload_date=picture_type_photos_upload_date,
                                                                       file_from=file_from)

                            if update_photos_status:
                                status, cls_files_name_list, cls_saved_files_name_list, cls_not_saved_files_name_list \
                                    = files_operation.zip_to_files(upload_path, test_unzip_path, members=global_id_cls_file_list)
                                if not status:
                                    return jsonify(common.falseReturn("", "上传失败！更新到数据库成功，但照片文件并未成功解压缩"))
                            else:
                                return jsonify(common.falseReturn("", "上传失败！更新到数据库时出错"))
                        far_saved_files_name_list = []
                        far_not_saved_files_name_list = []
                        if global_id_far_list:
                            update_photos_status = mysql.update_photos(database_name,
                                                                       table_name,
                                                                       picture_type=picture_type,
                                                                       global_id_far_list=global_id_far_list,
                                                                       picture_type_by=picture_type_by,
                                                                       mark_picture_type=mark_picture_type,
                                                                       picture_type_date=picture_type_date,
                                                                       picture_type_photos_upload_by=picture_type_photos_upload_by,
                                                                       picture_type_photos_upload_date=picture_type_photos_upload_date,
                                                                       file_from=file_from)

                            if update_photos_status:

                                status, far_files_name_list, far_saved_files_name_list, far_not_saved_files_name_list \
                                    = files_operation.zip_to_files(upload_path, test_unzip_path, members=global_id_far_file_list)
                                if not status:
                                    return jsonify(common.falseReturn("", "上传失败！更新到数据库成功，但照片文件并未成功解压缩"))
                            else:
                                return jsonify(common.falseReturn("", "上传失败！更新到数据库时出错"))
                        if status:
                            cache.clear()  # 清除缓存
                            saved_files_name_list = cls_saved_files_name_list + far_saved_files_name_list
                            not_saved_files_name_list = cls_not_saved_files_name_list + far_not_saved_files_name_list
                            saved_files_id_list = []
                            for i in saved_files_name_list:
                                try:
                                    saved_files_id_list.append(i.split("_")[0])
                                except:
                                    pass
                            not_saved_files_id_list = []
                            for i in not_saved_files_name_list:
                                try:
                                    not_saved_files_id_list.append(i.split("_")[0])
                                except:
                                    pass
                            '''
                            更新MD5数据库
                            insert_photos_MD5_data_list=[[city、file_name、iden_id、MD5]]
                            '''
                            insert_photos_files_list = [
                                os.path.join(os.path.join(config.DY_DATAS_PICTURES_PATH, city), i)
                                for i in saved_files_name_list]
                            insert_photos_MD5_status = pictures_operation.update_MD5_db(database_name,
                                                                                        config.PICTURES_MD5_TABLE_NAME,
                                                                                        picture_city=city,
                                                                                        files_list=insert_photos_files_list,
                                                                                        only_insert=True)
                            if not insert_photos_MD5_status:
                                addtion_msg = "上传成功，更新到数据库成功，照片文件成功解压缩，但更新到MD5数据库失败"
                                #     return jsonify(common.falseReturn("", "上传失败！更新到数据库成功，照片文件成功解压缩，但更新到MD5数据库失败"))
                            else:
                                addtion_msg = "上传成功，更新到数据库成功，照片文件成功解压缩, 更新到MD5数据库成功"
                            return jsonify(common.trueReturn({"saved_files_name_list": saved_files_name_list,
                                                              "saved_files_name_list_len": len(saved_files_name_list),
                                                              "saved_files_id_list": saved_files_id_list,
                                                              "saved_files_id_list_len": len(saved_files_id_list),
                                                              "not_saved_files_name_list": not_saved_files_name_list,
                                                              "not_saved_files_name_list_len": len(not_saved_files_name_list),
                                                              "not_saved_files_id_list": not_saved_files_id_list,
                                                              "not_saved_files_id_list_len": len(not_saved_files_id_list),
                                                              "upload_path": upload_path}, addtion_msg))
                # return jsonify(common.trueReturn("", "上传成功"))

            elif request.form.get('type') == REQUEST_TYPE.pictures_query.name:
                '''
                通过 门牌id，或者 global_id Excel 查询照片列表，打包下载
                '''
                if request.form.get("city"):
                    city = request.form.get("city")
                else:
                    city = ""
                if request.form.get("col_name"):
                    col_name = request.form.get("col_name")
                else:
                    col_name = "门牌id"
                database_name = 'ws_doorplate'
                table_name = 'fs_dp'
                if city == "foshan":
                    database_name = 'ws_doorplate'
                    table_name = 'fs_dp'
                if city == "guangzhou":
                    database_name = 'ws_doorplate'
                    table_name = 'gz_orders'
                if city == "maoming":
                    database_name = 'ws_doorplate'
                    table_name = 'maoming_dp'
                else:
                    database_name = CITY.get_db_name(city)
                    table_name = CITY.get_table_name(city)
                try:
                    f = request.files['file']
                    filename = request.files['file'].filename
                except:
                    return jsonify(common.falseReturn("", "上传失败！未传file"))

                temp_upload_path = os.path.join(config.TEMP_UPLOAD_DATAS_PATH, filename)
                upload_path = files_operation.upload_file(f, config.TEMP_UPLOAD_DATAS_PATH, filename)
                query_list = query.load_Excel_for_special(upload_path, col_name=col_name)

                #app.logger.info("query_list %s", query_list)

                pictures_full_path_list = []
                for i in query_list:
                    if city == "guangzhou":
                        filename = i + '_cj01.jpg'
                        sum = 0
                        while (os.path.isfile(
                                dydatas_basepath + '/gd_dp_photos/' + city + "/" + filename)):  # 入参需要是绝对路径
                            full_path = dydatas_basepath + '/gd_dp_photos/' + city + "/" + filename
                            pictures_full_path_list.append(full_path)
                            sum += 1
                            filename = i + '_cj01_' + str(sum) + '.jpg'
                    else:
                        filename = i + '_far.jpg'
                        sum = 0
                        while (os.path.isfile(
                                dydatas_basepath + '/gd_dp_photos/' + city + "/" + filename)):  # 入参需要是绝对路径
                            full_path = dydatas_basepath + '/gd_dp_photos/' + city + "/" + filename
                            pictures_full_path_list.append(full_path)
                            sum += 1
                            filename = i + '_far_' + str(sum) + '.jpg'
                        filename = i + '_cls.jpg'
                        sum = 0
                        while (os.path.isfile(
                                dydatas_basepath + '/gd_dp_photos/' + city + "/" + filename)):  # 入参需要是绝对路径
                            full_path = dydatas_basepath + '/gd_dp_photos/' + city + "/" + filename
                            pictures_full_path_list.append(full_path)
                            sum += 1
                            filename = i + '_cls_' + str(sum) + '.jpg'

                app.logger.info("打包照片")
                pictures_number = len(pictures_full_path_list)
                app.logger.info("数量为：%s", pictures_number)
                picture_zip_path = files_operation.files_to_zip(pictures_full_path_list)
                if picture_zip_path:
                    return jsonify(common.trueReturn({"picture_zip_path": picture_zip_path, "pictures_number": pictures_number}, "打包照片成功"))
                else:
                    return jsonify(common.falseReturn({"picture_zip_path": picture_zip_path}, "打包照片失败"))

            elif request.form.get('type') == REQUEST_TYPE.pictures_package_without_query.name:
                app.logger.info("通过前端传入文件名列表打包照片")

                if request.get_json():
                    request_data = request.get_json()
                else:
                    request_data = request.form

                #print("request.form.get('pictures_filename_list')",request_data.get('pictures_filename_list'))
                pictures_filename_list = request_data.get('pictures_filename_list').split(',')
                #print("pictures_filename_list",pictures_filename_list)
                city = request_data.get('city')
                pictures_full_path_list = []

                for i in pictures_filename_list:
                    pictures_full_path_list.append(os.path.join(config.DY_DATAS_PICTURES_PATH, city+'/'+i))
                pictures_number = len(pictures_full_path_list)
                app.logger.info("打包的文件为: %s", pictures_full_path_list)

                app.logger.info("数量为：%s", pictures_number)
                picture_zip_path = files_operation.files_to_zip(pictures_full_path_list)
                if picture_zip_path:
                    return jsonify(common.trueReturn(
                        {"picture_zip_path": picture_zip_path, "pictures_number": pictures_number}, "打包照片成功"))
                else:
                    return jsonify(common.falseReturn({"picture_zip_path": picture_zip_path}, "打包照片失败"))



        return jsonify(common.falseReturn("", "可能是请求有问题"))

    @cache.memoize(timeout=config.cache_timeout) # 设置缓存以及缓存时间
    def dp_status_get(request):
        request_json = request.args
        msg = ""

        app.logger.info("查询状态")

        city = request_json.get('city')  # 获取查询城市

        if not city:
            city = "foshan"

        # if city == "foshan":

        request_type = str(request_json.get('type'))  # 获取查询类型

        district = request_json.get('district')  # 获取查询地区， 例如 佛山西樵
        app.logger.info(district)
        if not district:
            district = ''

        installed_date_sql = ""
        if request_json.get('installed_date'):
            installed_date = request_json.get('installed_date')
            installed_date_sql = " AND installed_date like " + "\"%" + installed_date + "%\""

        # installed_date_start = '2000-01-01 00:00:00'
        # installed_date_end = common.format_ymdhms_time_now()
        if request_json.get('installed_date_start') or request_json.get('installed_date_end'):
            # installed_date_start = request_json.get('installed_date_start')
            # installed_date_end = request_json.get('installed_date_end')
            installed_date_start = request_json.get('installed_date_start') if request_json.get(
                'installed_date_start') else '2000-01-01 00:00:00'
            installed_date_end = request_json.get('installed_date_end') if request_json.get(
                'installed_date_end') else common.format_ymdhms_time_now()
            installed_date_sql = " AND installed_date >= " + "\"" + installed_date_start + "\"" + " AND installed_date <= " + "\"" + installed_date_end + "\""

        # installed_by_sql = ""
        # if request_json.get('installed_by'):
        #     installed_by = request_json.get('installed_by')
        #     installed_by_sql = " AND installed_by = " + installed_by





        # if request_type == REQUEST_TYPE.installed.name:
        #     app.logger.info("查询安装状态")
        #     # app.logger.info(request_json.get('qrcode'))
        #     # app.logger.info(request_json.get('installed_by'))
        #     # app.logger.info(request_json.get('installed_coordinate'))
        #     # dzbm = filename.split('.')[0]
        #     try:
        #         database_name = CITY.get_db_name(city)
        #         table_name = CITY.get_table_name(city)
        #     except:
        #         database_name = 'ws_doorplate'
        #         table_name = 'fs_dp'
        #     # if city == "foshan":
        #     #     database_name = 'ws_doorplate'
        #     #     table_name = 'fs_dp'
        #     # if city == "guangzhou":
        #     #     database_name = 'ws_doorplate'
        #     #     table_name = 'gz_orders'
        #     # if city == "maoming":
        #     #     database_name = 'ws_doorplate'
        #     #     table_name = 'maoming_dp'
        #
        #
        #     # 之后数据库转移后再启用
        #     db = pymysql.connect("localhost", "root", "root", database_name)
        #     # db = pymysql.connect("localhost", "root", "root", "丹灶数据库")
        #
        #     # 使用cursor()方法获取操作游标
        #     cursor = db.cursor()
        #
        #     # 按安装人进行统计安装数量
        #     select_sql_head = "SELECT installed_by, COUNT(installed), COUNT(installed_photos_cls>0 or NULL), COUNT(installed_photos_far>0 or NULL), MIN(installed_date), MAX(installed_date) FROM "
        #     # if district == 'all':
        #     #     district_sql = ""
        #     #     if community:
        #     #         #if city == "guangzhou":
        #     #         if city != "maoming" and city != "foshan":
        #     #             district_sql += " AND pcs=" + "\"" + community + "\""
        #     #         else:
        #     #             district_sql += " AND community=" + "\"" + community + "\""
        #     #
        #     # else:
        #     #     district_sql = " AND district=" + "\"" + district + "\""
        #     #     # district_sql = ""
        #     #     if community:
        #     #         #if city == "guangzhou":
        #     #         if city != "maoming" and city != "foshan":
        #     #             district_sql += " AND pcs=" + "\"" + community + "\""
        #     #         else:
        #     #             district_sql += " AND community=" + "\"" + community + "\""
        #     condition_sql = ""
        #     if district:
        #         condition_sql += " AND district=" + "\"" + district + "\""
        #     town = ""
        #     if request_json.get('town'):
        #         town = request_json.get('town')
        #         condition_sql += " AND town=" + "\"" + town + "\""
        #
        #     pcs = ""
        #     if request_json.get('pcs'):
        #         pcs = request_json.get('pcs')
        #         condition_sql += " AND pcs=" + "\"" + pcs + "\""
        #     community = ""
        #     if request_json.get('community'):
        #         community = request_json.get('community')
        #         condition_sql += " AND community=" + "\"" + community + "\""
        #
        #
        #     # 增加 like 模糊匹配 筛选
        #     query_key = []
        #     for key in request.args.keys():
        #         # if key.find('like') > 0:
        #         if key.find('_like') > 0 and request.args.get(key):
        #             query_key.append(key[0:key.find('like') - 1])
        #
        #     sql_like_query = ''
        #     if query_key:
        #         for key in query_key:
        #             sql_like_query += ' AND ' + key + ' LIKE \'%' + request.args.get(str(key + '_like')) + '%\''
        #             # if sql_like_query:
        #             #     sql_like_query += ' AND ' + key + ' LIKE \'%' + request.args.get(str(key + '_like')) + '%\''
        #             # else:
        #             #     sql_like_query += key + ' LIKE \'%' + request.args.get(str(key + '_like')) + '%\''
        #
        #     contract_batch = ""
        #     contract_batch_sql = ""
        #     contract_batch_where_sql = ""
        #     if request_json.get('contract_batch'):
        #         contract_batch = request_json.get('contract_batch')
        #         contract_batch_sql += " AND contract_batch=" + "\"" + contract_batch + "\""
        #         contract_batch_where_sql += " WHERE contract_batch=" + "\"" + contract_batch + "\""
        #     order_batch = ""
        #     order_batch_sql = ""
        #     order_batch_where_sql = ""
        #     if request_json.get('order_batch'):
        #         order_batch = request_json.get('order_batch')
        #         order_batch_sql += " AND order_batch=" + "\"" + order_batch + "\""
        #         order_batch_where_sql += " WHERE order_batch=" + "\"" + order_batch + "\""
        #     order_id = ""
        #     order_id_sql = ""
        #     order_id_where_sql = ""
        #     if request_json.get('order_id'):
        #         order_id = request_json.get('order_id')
        #         order_id_sql += " AND order_id=" + "\"" + order_id + "\""
        #         order_id_where_sql += " WHERE order_id=" + "\"" + order_id + "\""
        #
        #     '''
        #     select_sql_tail = " WHERE installed>=1" + district_sql + " GROUP BY installed_by"
        #
        #     select_sql_installed_by = select_sql_head + "gis_ordered" + select_sql_tail
        #
        #     # 按安装人进行统计安装数量
        #     select_sql_installed_total_num = "SELECT COUNT(installed), COUNT(installed_photos)  FROM " + "gis_ordered" + " WHERE installed>=1" + district_sql
        #
        #     # 统计所有门牌数量
        #     select_sql_dp_num = "SELECT COUNT(installed)  FROM " + "gis_ordered" + " WHERE installed>=0 AND 地址编码状态=\"可做蓝牌\"" + district_sql
        #     '''
        #
        #     # 之后数据库转移后再启用
        #
        #     # 按安装人和时间分组进行统计安装数量
        #     # select_sql_tail = " WHERE installed>=1" + district_sql + " GROUP BY installed_by"
        #
        #     # 筛选条件 都是and
        #     filter_sql = condition_sql + installed_date_sql + contract_batch_sql + order_batch_sql + order_id_sql + sql_like_query
        #     # select_sql_tail = " WHERE installed>=1" + district_sql + installed_date_sql + contract_batch_sql + order_batch_sql + order_id_sql + sql_like_query + " GROUP BY installed_by"
        #     select_sql_tail = " WHERE installed>=1" + filter_sql + " GROUP BY installed_by"
        #
        #     select_sql_installed_by = select_sql_head + table_name + select_sql_tail
        #
        #     # 按地区和时间以及新增的批号等进行统计安装数量
        #     ##select_sql_installed_total_num = "SELECT COUNT(installed), COUNT(installed_photos>0 or NULL)  FROM " + table_name + " WHERE installed>=1" + "" + district_sql
        #     # select_sql_installed_total_num = "SELECT COUNT(installed), COUNT(installed_photos_cls>0 or NULL), COUNT(installed_photos_far>0 or NULL)  FROM " + table_name + " WHERE installed>=1" + "" + district_sql + installed_date_sql + contract_batch_sql + order_batch_sql + order_id_sql + sql_like_query
        #     select_sql_installed_total_num = "SELECT COUNT(installed), COUNT(installed_photos_cls>0 or NULL), COUNT(installed_photos_far>0 or NULL)  FROM " + table_name + " WHERE installed>=1 " + filter_sql
        #
        #     # 统计筛选条件下所有门牌数量
        #     # select_sql_dp_num = "SELECT COUNT(installed)  FROM " + table_name + " WHERE installed>=0" + district_sql
        #     select_sql_dp_num = "SELECT COUNT(installed)  FROM " + table_name + " WHERE installed>=0" + condition_sql + contract_batch_sql + order_batch_sql + order_id_sql + sql_like_query
        #
        #     # district下的所有community，合同批号、订单批号、订单号
        #     # if district == "all":
        #     #     #if city == "guangzhou":
        #     #     if city != "maoming" and city != "foshan":
        #     #         sq_district_sql = "SELECT distinct pcs FROM " + table_name
        #     #     else:
        #     #         sq_district_sql = "SELECT distinct community FROM " + table_name
        #     #
        #     #     if contract_batch_where_sql:
        #     #         sq_district_sql = sq_district_sql + contract_batch_where_sql + contract_batch_sql + order_batch_sql
        #     #
        #     #     distinct_contract_batch_sql = "SELECT distinct contract_batch FROM " + table_name
        #     #     distinct_order_batch_sql = "SELECT distinct order_batch  FROM " + table_name
        #     #     distinct_order_id_sql = "SELECT distinct order_id FROM " + table_name
        #     #
        #     #     if contract_batch_where_sql:
        #     #         distinct_order_batch_sql += contract_batch_where_sql
        #     #         distinct_order_id_sql += contract_batch_where_sql
        #     #     if contract_batch_where_sql and order_batch_where_sql:
        #     #         distinct_order_id_sql += order_batch_where_sql
        #     # else:
        #     #     #if city == "guangzhou":
        #     #     if city != "maoming" and city != "foshan":
        #     #         sq_district_sql = "SELECT distinct pcs FROM " + table_name + " WHERE district=" + "\"" + district + "\"" + installed_date_sql + contract_batch_sql + order_batch_sql
        #     #     else:
        #     #         sq_district_sql = "SELECT distinct community FROM " + table_name + " WHERE district=" + "\"" + district + "\"" + installed_date_sql + contract_batch_sql + order_batch_sql
        #     #
        #     #     distinct_contract_batch_sql = "SELECT distinct contract_batch FROM " + table_name + " WHERE district=" + "\"" + district + "\""
        #     #     distinct_order_batch_sql = "SELECT distinct order_batch  FROM " + table_name + " WHERE district=" + "\"" + district + "\"" + installed_date_sql
        #     #     distinct_order_id_sql = "SELECT distinct order_id FROM " + table_name + " WHERE district=" + "\"" + district + "\"" + installed_date_sql + contract_batch_sql
        #
        #     filter_sql = condition_sql + contract_batch_sql + order_batch_sql + order_id_sql + sql_like_query
        #     filter_sql = filter_sql + contract_batch_sql + order_batch_sql + order_id_sql
        #
        #     if filter_sql.find("where") < 0 and filter_sql.find("WHERE") < 0:
        #         filter_sql = filter_sql.replace("AND", "WHERE", 1)
        #
        #     app.logger.info("filter_sqlfilter_sqlfilter_sql: %s", filter_sql)
        #
        #     # 条件下所有town
        #     town_district_sql = "SELECT distinct town FROM " + table_name + filter_sql
        #
        #     # 条件下所有pcs
        #     pcs_district_sql = "SELECT distinct pcs FROM " + table_name + filter_sql
        #
        #     # 条件下所有community
        #     community_district_sql = "SELECT distinct community FROM " + table_name + filter_sql
        #
        #     distinct_contract_batch_sql = "SELECT distinct contract_batch FROM " + table_name + filter_sql
        #     distinct_order_batch_sql = "SELECT distinct order_batch  FROM " + table_name + filter_sql
        #     distinct_order_id_sql = "SELECT distinct order_id FROM " + table_name + filter_sql
        #
        #
        #
        #     try:
        #         app.logger.info(distinct_contract_batch_sql)
        #         #app.logger.info(select_sql_installed_by)
        #
        #         # cursor.execute(distinct_contract_batch_sql)
        #         # distinct_contract_batch_list = cursor.fetchall()
        #         # distinct_contract_batch_list = [i[0] if i[0] else "" for i in distinct_contract_batch_list]
        #         distinct_contract_batch_list = mysql.select_by_sql_with_long_time_cache(database_name, distinct_contract_batch_sql)
        #         distinct_contract_batch_list = [i[0] for i in distinct_contract_batch_list]
        #     except:
        #         app.logger.info(distinct_contract_batch_sql)
        #         distinct_contract_batch_list = []
        #     try:
        #         # app.logger.info(select_sql)
        #         # app.logger.info(select_sql_installed_by)
        #         app.logger.info(distinct_order_batch_sql)
        #
        #         # cursor.execute(distinct_order_batch_sql)
        #         # distinct_order_batch_list = cursor.fetchall()
        #         # distinct_order_batch_list = [i[0] if i[0] else "" for i in distinct_order_batch_list]
        #         distinct_order_batch_list = mysql.select_by_sql_with_long_time_cache(database_name, distinct_order_batch_sql)
        #         distinct_order_batch_list = [i[0] for i in distinct_order_batch_list]
        #     except:
        #         app.logger.info(distinct_order_batch_sql)
        #         distinct_order_batch_list = []
        #     try:
        #         # app.logger.info(select_sql)
        #         # app.logger.info(select_sql_installed_by)
        #         app.logger.info(distinct_order_id_sql)
        #
        #         # cursor.execute(distinct_order_id_sql)
        #         # distinct_order_id_list = cursor.fetchall()
        #         # distinct_order_id_list = [i[0] if i[0] else "" for i in distinct_order_id_list]
        #         distinct_order_id_list = mysql.select_by_sql_with_long_time_cache(database_name,
        #                                                                              distinct_order_id_sql)
        #         distinct_order_id_list = [i[0] for i in distinct_order_id_list]
        #     except:
        #         app.logger.info(distinct_order_id_sql)
        #         distinct_order_id_list = []
        #
        #     # 所有district
        #     district_list_sql = "SELECT distinct district FROM " + table_name
        #
        #     # # 所有town
        #     # town_district_sql = "SELECT distinct town FROM " + table_name
        #     #
        #     # # 所有pcs
        #     # pcs_district_sql = "SELECT distinct pcs FROM " + table_name
        #
        #     try:
        #
        #         # app.logger.info(select_sql)
        #         app.logger.info(select_sql_installed_by)
        #         cursor.execute(select_sql_installed_by)
        #         installed_by = cursor.fetchall()
        #
        #         # 可以获取查询字段名字
        #         # test_col = cursor.description
        #         # app.logger.info(test_col)
        #         app.logger.info(select_sql_installed_total_num)
        #         cursor.execute(select_sql_installed_total_num)
        #         installed_total_num_result = cursor.fetchall()
        #         installed_total_num = installed_total_num_result[0][0]
        #         uploaded_photos_cls_total_num = int(installed_total_num_result[0][1])
        #         uploaded_photos_far_total_num = int(installed_total_num_result[0][2])
        #
        #         app.logger.info(select_sql_dp_num)
        #         cursor.execute(select_sql_dp_num)
        #         dp_num = cursor.fetchall()
        #         dp_total_num = dp_num[0][0]
        #
        #         app.logger.info(community_district_sql)
        #         # cursor.execute(community_district_sql)
        #         # community_list = [i[0] for i in cursor.fetchall()]
        #         community_list = mysql.select_by_sql_with_long_time_cache(database_name,
        #                                                                   community_district_sql)
        #         community_list = [i[0] for i in community_list]
        #
        #         app.logger.info(district_list_sql)
        #         # cursor.execute(district_list_sql)
        #         # district_list = [i[0] for i in cursor.fetchall()]
        #         district_list = mysql.select_by_sql_with_long_time_cache(database_name,
        #                                                                  district_list_sql)
        #         district_list = [i[0] for i in district_list]
        #
        #         app.logger.info(town_district_sql)
        #         # cursor.execute(town_district_sql)
        #         # town_list = [i[0] for i in cursor.fetchall()]
        #         town_list = mysql.select_by_sql_with_long_time_cache(database_name,
        #                                                                  town_district_sql)
        #         town_list = [i[0] for i in town_list]
        #
        #         app.logger.info(pcs_district_sql)
        #         # cursor.execute(pcs_district_sql)
        #         # pcs_list = [i[0] for i in cursor.fetchall()]
        #         pcs_list = mysql.select_by_sql_with_long_time_cache(database_name,
        #                                                              pcs_district_sql)
        #         pcs_list = [i[0] for i in pcs_list]
        #
        #         # app.logger.info(installed_by)
        #         app.logger.info(installed_total_num)
        #         app.logger.info(uploaded_photos_cls_total_num)
        #         app.logger.info(uploaded_photos_far_total_num)
        #         app.logger.info(dp_num)
        #         # app.logger.info(sq_list)
        #         CITY_items = CITY.items()
        #         for i in installed_by:
        #             if not i[4]:
        #             #if not i[5]:
        #                 i[4] = datetime.datetime.strptime("2000-01-01 00:00:00")
        #             if not i[5]:
        #                 i[5] = datetime.datetime.strptime("2000-01-01 00:00:00")
        #         return_data = {
        #             "installed_status": [{"name": i[0],
        #                                   "installed_num": i[1],
        #                                   "installed_photos_cls_num": i[2],
        #                                   "installed_photos_far_num": i[3],
        #                                   "min_installed_date": i[4].strftime('%Y-%m-%d %H:%M:%S'),
        #                                   "max_installed_date": i[5].strftime('%Y-%m-%d %H:%M:%S'),
        #                                   } for i in installed_by],
        #             "installed_total_num": installed_total_num,
        #             "uploaded_photos_cls_total_num": uploaded_photos_cls_total_num,
        #             "uploaded_photos_far_total_num": uploaded_photos_far_total_num,
        #             "dp_total_num": dp_total_num,
        #             "district_list": district_list,
        #             "town_list": town_list,
        #             "pcs_list": pcs_list,
        #             "community_list": community_list,
        #             'city_list': [i for i in CITY_items],
        #             "installed_status_count": len(installed_by),
        #             "contract_batch_list": distinct_contract_batch_list,
        #             "order_batch_list": distinct_order_batch_list,
        #             "order_id_list": distinct_order_id_list
        #         }
        #
        #         if installed_by:
        #
        #             # return_data = {
        #             #     "installed_statue": installed_by,
        #             #     "installed_total_num": installed_total_num,
        #             #     "uploaded_photos_total_num": uploaded_photos_total_num,
        #             #     "dp_total_num": dp_total_num,
        #             #     "sq_list": sq_list
        #             #
        #             # }
        #             # 提交到数据库执行
        #             db.commit()
        #             # 关闭数据库连接
        #             db.close()
        #             return jsonify(common.trueReturn(return_data, "查询成功"))
        #         else:
        #             # return_data = {
        #             #     "installed_statue": installed_by,
        #             #     "installed_total_num": installed_total_num,
        #             #     "uploaded_photos_total_num": uploaded_photos_total_num,
        #             #     "dp_total_num": dp_total_num,
        #             #     "sq_list": sq_list
        #             #
        #             # }
        #             # 提交到数据库执行
        #             db.commit()
        #             # 关闭数据库连接
        #             db.close()
        #             return jsonify(common.falseReturn(return_data, "查询无结果"))
        #
        #     except:
        #         app.logger.info(select_sql_installed_by)
        #         app.logger.info(select_sql_installed_total_num)
        #         app.logger.info(select_sql_dp_num)
        #         app.logger.info(community_district_sql)
        #         app.logger.info(district_list_sql)
        #         # app.logger.info(installed_by)
        #         app.logger.info(installed_total_num)
        #         app.logger.info(uploaded_photos_cls_total_num)
        #         app.logger.info(uploaded_photos_far_total_num)
        #         app.logger.info(dp_num)
        #         # 如果发生错误则回滚
        #         # traceback.print_exc()
        #         db.rollback()
        #         # 关闭数据库连接
        #         db.close()
        #         app.logger.info("查询接口/dp_status有错误")
        #         return jsonify(common.falseReturn("", "检查查询参数有无错误"))

        if request.args.get('type') == REQUEST_TYPE.report_excel.name:
            app.logger.info("下载安装统计表")
            if not request.args.get('city'):
                return common.falseReturn("", "没有传入城市参数！")
            else:
                city = request.args.get('city')
                db_name = CITY.get_db_name(city)
                table_name = CITY.get_table_name(city)
            if not request.args.get('date_type'):
                #return common.falseReturn("", "没有传入start_date参数！")
                date_type = "installed_date"
            else:
                date_type = request.args.get('date_type')
            if not request.args.get('picture_type'):
                #return common.falseReturn("", "没有传入picture_type参数！")
                picture_type = "installed" # 默认是安装的
            else:
                picture_type = request.args.get('picture_type')
            if not request.args.get('start_date'):
                #return common.falseReturn("", "没有传入start_date参数！")
                start_date = "1970-01-01 08:00:00"
            else:
                start_date = request.args.get('start_date')
            if not request.args.get('end_date'):
                end_date = common.format_ymdhms_time_now()
            else:
                end_date = request.args.get('end_date')
            if not request.args.get('by'):
                picture_type_by = ''
            else:
                picture_type_by = request.args.get('by')
            if not request.args.get('report_type'):
                # return common.falseReturn("", "没有传入report_type参数！")
                pass
            else:
                report_type = request.args.get('report_type')
            if not request.args.get('group_by'):
                #return common.falseReturn("", "没有传入group_by参数！")
                group_by = "installed_by"
            else:
                group_by = request.args.get('group_by')
                # if group_by.find("installed_by") < 0:
                #     group_by += ",installed_by"
            if not request.args.get('type'):
                return common.falseReturn("", "没有传入type参数！")
            else:
                type = request.args.get('type')
            if not request.args.get('report_date_type'):
                #return common.falseReturn("", "没有传入report_date_type参数！")
                report_date_type = "month"
            else:
                report_date_type = request.args.get('report_date_type')

            picture_type_by_sql = " AND {picture_type}_by = " + "\"" + picture_type_by + "\"" if picture_type_by else ""
            picture_type_by_sql = picture_type_by_sql.format(picture_type=picture_type)
            date_sql = " AND {date_type} >= " + "\"" + start_date + "\"" + " AND {date_type} <= " + "\"" + end_date + "\""
            date_sql = date_sql.format(date_type=date_type)
            # date_sql = " AND {picture_type}_date >= " + "\"" + start_date + "\"" + " AND {picture_type}_date <= " + "\"" + end_date + "\""
            # date_sql = date_sql.format(picture_type=picture_type)
            #upload_date_sql = " AND installed_date >= " + "\"" + start_date + "\"" + " AND installed_date <= " + "\"" + end_date + "\""

            #app.logger.info("group_by %s", group_by)
            
            group_by = group_by.split(",")

            day_date_format = " DATE_FORMAT(`installed_date`, '%Y-%m-%d') "

            if report_date_type == "day":
                group_by.append(day_date_format)

            filter_sql = ""

            filter_sql = date_sql + picture_type_by_sql

            #group_by_list =

            # count_photos_far_sql = "SELECT COUNT(`installed_photos_far`>0 or NULL), `installed_by` FROM fs_dp GROUP BY `installed_by`"
            # count_photos_far_results = mysql.select_by_sql(db_name, count_photos_far_sql)
            # app.logger.info(count_photos_far_results)
            # count_photos_cls_sql = "SELECT COUNT(`installed_photos_far`>0 or NULL), `installed_by` FROM fs_dp GROUP BY `installed_by`"
            # count_photos_cls_results = mysql.select_by_sql(db_name, count_photos_cls_sql)
            # app.logger.info(count_photos_cls_results)

            #if picture_type == REQUEST_TYPE.installed.name


            count_installed_info_sql = " SELECT COUNT(installed>0 or NULL), " \
                                       "COUNT(installed_photos_far>0 or NULL), " \
                                       "COUNT(installed_photos_cls>0 or NULL), " \
                                       "COUNT(installed_photos_far>0 or NULL) + COUNT(installed_photos_cls>0 or NULL) as total_photos, " + ",".join(group_by) + " FROM " + \
            table_name + " WHERE installed_by is not NULL " +  filter_sql \
                                       + " GROUP BY  " + ",".join(group_by)

            if report_date_type == "day":
                count_installed_info_sql += " ORDER BY " + day_date_format + " ASC "

            print(count_installed_info_sql)
            results = mysql.select_by_sql(db_name, count_installed_info_sql)
            print(results)

            if report_date_type == "day":
                #results = sorted(results, key=lambda x: (x[-2], x[-1])) # 按日期和安装人排序
                results = sorted(results, key=lambda x: (x[-1])) # 只按日期排序

            if not results:
                return jsonify(common.falseReturn({"report_excel_path": ""}, "查询未成功，可能是没有相关数据，或者筛选的列有问题。检查选择的列以及条件是否有错误"))

            #col_name_map = ExcelModel.col_name_map
            col_name_map = mysql.get_col_name_map()

            data_map = collections.OrderedDict() # keys是有序字典，先加入的在前面

            for i, value in enumerate(results):
                col_index = 0
                if i == 0:
                    data_map['安装数量'] = [value[col_index]]
                    col_index += 1
                    data_map['安装远照片'] = [value[col_index]]
                    col_index += 1
                    data_map['安装近照片'] = [value[col_index]]
                    col_index += 1
                    data_map['照片总数'] = [value[col_index]]
                    col_index += 1
                    #data_map['安装人'] = [value[3]]
                    for j in group_by:
                        j = col_name_map.get(j) if col_name_map.get(j) else j
                        if j == day_date_format:
                            j = "安装日期"
                        data_map[j] = [value[col_index]]
                        col_index += 1
                else:
                    data_map['安装数量'].append(value[col_index])
                    col_index += 1
                    data_map['安装远照片'].append(value[col_index])
                    col_index += 1
                    data_map['安装近照片'].append(value[col_index])
                    col_index += 1
                    data_map['照片总数'].append(value[col_index])
                    col_index += 1
                    #data_map['安装人'].append(value[3])
                    for j in group_by:
                        j = col_name_map.get(j) if col_name_map.get(j) else j
                        if j == day_date_format:
                            j = "安装日期"
                        data_map[j].append([value[col_index]])
                        col_index += 1
            app.logger.info(data_map)
            title_info = []
            title_info.append(["门牌安装数据统计"])
            title_info.append(["时间段: ", start_date, end_date])
            report_excel_path = ExcelModel.data_map_to_excel(data_map, path=config.TEMP_DOWNLOAD_DATAS_PATH, excel_name='report_' + common.format_ymdhms_time_now_for_filename() + '.xls', title_info=title_info)
            return jsonify(common.trueReturn({"report_excel_path": report_excel_path}, "查询成功"))

        elif request_type == REQUEST_TYPE.collected.name or request_type == REQUEST_TYPE.installed.name:
            app.logger.info("查询采集状态")
            
            if request_type == REQUEST_TYPE.collected.name:
                dp_status_type = "collected"
            elif request_type == REQUEST_TYPE.installed.name:
                dp_status_type = "installed"
            date_sql = ""
            if request_json.get('date'):
                date = request_json.get('date')
                date_sql = " AND {dp_status_type}_date like " + "\"%" + date + "%\""
                date_sql = date_sql.format(dp_status_type=dp_status_type)

            if request_json.get('date_start') or request_json.get('date_end'):
                date_start = request_json.get('date_start') if request_json.get(
                    'date_start') else '2000-01-01 00:00:00'
                date_end = request_json.get('date_end') if request_json.get(
                    'date_end') else common.format_ymdhms_time_now()
                date_sql = " AND {dp_status_type}_date >= " + "\"" + date_start + "\"" + " AND {dp_status_type}_date <= " + "\"" + date_end + "\""
                date_sql = date_sql.format(dp_status_type=dp_status_type)
            # if request_type == REQUEST_TYPE.collected.name:
            #     dp_status_type = "collected"
            #     date_sql = ""
            #     if request_json.get('date'):
            #         date = request_json.get('date')
            #         date_sql = " AND {dp_status_type}_date like " + "\"%" + date + "%\""
            #         date_sql = date_sql.format(dp_status_type=dp_status_type)
            #
            #     # installed_date_start = '2000-01-01 00:00:00'
            #     # installed_date_end = common.format_ymdhms_time_now()
            #     if request_json.get('date_start') or request_json.get('date_end'):
            #         # installed_date_start = request_json.get('installed_date_start')
            #         # installed_date_end = request_json.get('installed_date_end')
            #         date_start = request_json.get('date_start') if request_json.get(
            #             'date_start') else '2000-01-01 00:00:00'
            #         date_end = request_json.get('date_end') if request_json.get(
            #             'date_end') else common.format_ymdhms_time_now()
            #         date_sql = " AND {dp_status_type}_date >= " + "\"" + date_start + "\"" + " AND {dp_status_type}_date <= " + "\"" + date_end + "\""
            #         date_sql = date_sql.format(dp_status_type=dp_status_type)
            # elif request_type == REQUEST_TYPE.installed.name:
            #     dp_status_type = "installed"
            #     date_sql = ""
            #     if request_json.get('installed_date'):
            #         installed_date = request_json.get('installed_date')
            #         date_sql = " AND installed_date like " + "\"%" + installed_date + "%\""
            #
            #     # installed_date_start = '2000-01-01 00:00:00'
            #     # installed_date_end = common.format_ymdhms_time_now()
            #     if request_json.get('installed_date_start') or request_json.get('installed_date_end'):
            #         # installed_date_start = request_json.get('installed_date_start')
            #         # installed_date_end = request_json.get('installed_date_end')
            #         installed_date_start = request_json.get('installed_date_start') if request_json.get(
            #             'installed_date_start') else '2000-01-01 00:00:00'
            #         installed_date_end = request_json.get('installed_date_end') if request_json.get(
            #             'installed_date_end') else common.format_ymdhms_time_now()
            #         date_sql = " AND installed_date >= " + "\"" + installed_date_start + "\"" + " AND installed_date <= " + "\"" + installed_date_end + "\""
            #

            district = request_json.get('district')  # 获取查询地区， 例如 佛山西樵
            app.logger.info(district)
            if not district:
                district = ''




            try:
                database_name = CITY.get_db_name(city)
                table_name = CITY.get_table_name(city)
            except:
                database_name = 'ws_doorplate'
                table_name = 'fs_dp'

            # 之后数据库转移后再启用
            db = pymysql.connect("localhost", "root", "root", database_name)
            # db = pymysql.connect("localhost", "root", "root", "丹灶数据库")

            # 使用cursor()方法获取操作游标
            cursor = db.cursor()

            # 按dp_status_type人进行统计安装数量
            #select_sql_head = "SELECT installed_by, COUNT(installed), COUNT(installed_photos_cls>0 or NULL), COUNT(installed_photos_far>0 or NULL), MIN(installed_date), MAX(installed_date) FROM "
            if dp_status_type == "collected":
                select_sql_head = "SELECT {dp_status_type}_by, COUNT({dp_status_type}), COUNT({dp_status_type}_photos>0 or NULL), MIN({dp_status_type}_date), MAX({dp_status_type}_date) FROM "
            elif dp_status_type == "installed":
                select_sql_head = "SELECT {dp_status_type}_by, COUNT({dp_status_type}), COUNT({dp_status_type}_photos_cls>0 or NULL), COUNT({dp_status_type}_photos_far>0 or NULL), MIN({dp_status_type}_date), MAX({dp_status_type}_date) FROM "

            select_sql_head = select_sql_head.format(dp_status_type=dp_status_type)
            condition_sql = ""
            if district:
                condition_sql += " AND district=" + "\"" + district + "\""
            town = ""
            if request_json.get('town'):
                town = request_json.get('town')
                condition_sql += " AND town=" + "\"" + town + "\""

            pcs = ""
            if request_json.get('pcs'):
                pcs = request_json.get('pcs')
                condition_sql += " AND pcs=" + "\"" + pcs + "\""
            community = ""
            if request_json.get('community'):
                community = request_json.get('community')
                condition_sql += " AND community=" + "\"" + community + "\""

            # 增加 like 模糊匹配 筛选
            query_key = []
            for key in request.args.keys():
                # if key.find('like') > 0:
                if key.find('_like') > 0 and request.args.get(key):
                    query_key.append(key[0:key.find('like') - 1])

            sql_like_query = ''
            if query_key:
                for key in query_key:
                    sql_like_query += ' AND ' + key + ' LIKE \'%' + request.args.get(str(key + '_like')) + '%\''

            contract_batch = ""
            contract_batch_sql = ""
            contract_batch_where_sql = ""
            if request_json.get('contract_batch'):
                contract_batch = request_json.get('contract_batch')
                contract_batch_sql += " AND contract_batch=" + "\"" + contract_batch + "\""
                contract_batch_where_sql += " WHERE contract_batch=" + "\"" + contract_batch + "\""
            order_batch = ""
            order_batch_sql = ""
            order_batch_where_sql = ""
            if request_json.get('order_batch'):
                order_batch = request_json.get('order_batch')
                order_batch_sql += " AND order_batch=" + "\"" + order_batch + "\""
                order_batch_where_sql += " WHERE order_batch=" + "\"" + order_batch + "\""
            order_id = ""
            order_id_sql = ""
            order_id_where_sql = ""
            if request_json.get('order_id'):
                order_id = request_json.get('order_id')
                order_id_sql += " AND order_id=" + "\"" + order_id + "\""
                order_id_where_sql += " WHERE order_id=" + "\"" + order_id + "\""



            # 筛选条件 都是and
            filter_sql = condition_sql + date_sql + contract_batch_sql + order_batch_sql + order_id_sql + sql_like_query
            select_sql_tail = " WHERE {dp_status_type}>=1" + filter_sql + " GROUP BY {dp_status_type}_by"
            select_sql_tail = select_sql_tail.format(dp_status_type=dp_status_type)

            select_sql_by = select_sql_head + table_name + select_sql_tail

            # 按地区和时间以及新增的批号等进行统计安装数量

            if dp_status_type == "collected":
                select_sql_total_num = "SELECT COUNT({dp_status_type}), COUNT({dp_status_type}_photos>0 or NULL)  FROM " + table_name + " WHERE {dp_status_type}>=1 " + filter_sql
            elif dp_status_type == "installed":
                select_sql_total_num = "SELECT COUNT({dp_status_type}), COUNT({dp_status_type}_photos_cls>0 or NULL), COUNT({dp_status_type}_photos_far>0 or NULL)  FROM " + table_name + " WHERE {dp_status_type}>=1 " + filter_sql
            select_sql_total_num = select_sql_total_num.format(dp_status_type=dp_status_type)

            # 统计筛选条件下所有门牌数量
            select_sql_dp_num = "SELECT COUNT({dp_status_type})  FROM " + table_name + " WHERE {dp_status_type}>=0" + condition_sql + contract_batch_sql + order_batch_sql + order_id_sql + sql_like_query
            select_sql_dp_num = select_sql_dp_num.format(dp_status_type=dp_status_type)



            filter_sql = condition_sql + contract_batch_sql + order_batch_sql + order_id_sql + sql_like_query
            filter_sql = filter_sql + contract_batch_sql + order_batch_sql + order_id_sql

            if filter_sql.find("where") < 0 and filter_sql.find("WHERE") < 0:
                filter_sql = filter_sql.replace("AND", "WHERE", 1)

            app.logger.info("filter_sqlfilter_sqlfilter_sql: %s", filter_sql)

            # 条件下所有town
            town_district_sql = "SELECT distinct town FROM " + table_name + filter_sql

            # 条件下所有pcs
            pcs_district_sql = "SELECT distinct pcs FROM " + table_name + filter_sql

            # 条件下所有community
            community_district_sql = "SELECT distinct community FROM " + table_name + filter_sql

            distinct_contract_batch_sql = "SELECT distinct contract_batch FROM " + table_name + filter_sql
            distinct_order_batch_sql = "SELECT distinct order_batch  FROM " + table_name + filter_sql
            distinct_order_id_sql = "SELECT distinct order_id FROM " + table_name + filter_sql

            try:
                app.logger.info(distinct_contract_batch_sql)
                # app.logger.info(select_sql_installed_by)

                # cursor.execute(distinct_contract_batch_sql)
                # distinct_contract_batch_list = cursor.fetchall()
                # distinct_contract_batch_list = [i[0] if i[0] else "" for i in distinct_contract_batch_list]
                distinct_contract_batch_list = mysql.select_by_sql_with_long_time_cache(database_name,
                                                                                        distinct_contract_batch_sql)
                distinct_contract_batch_list = [i[0] for i in distinct_contract_batch_list]
            except:
                app.logger.info(distinct_contract_batch_sql)
                distinct_contract_batch_list = []
            try:
                # app.logger.info(select_sql)
                # app.logger.info(select_sql_installed_by)
                app.logger.info(distinct_order_batch_sql)

                # cursor.execute(distinct_order_batch_sql)
                # distinct_order_batch_list = cursor.fetchall()
                # distinct_order_batch_list = [i[0] if i[0] else "" for i in distinct_order_batch_list]
                distinct_order_batch_list = mysql.select_by_sql_with_long_time_cache(database_name,
                                                                                     distinct_order_batch_sql)
                distinct_order_batch_list = [i[0] for i in distinct_order_batch_list]
            except:
                app.logger.info(distinct_order_batch_sql)
                distinct_order_batch_list = []
            try:
                # app.logger.info(select_sql)
                # app.logger.info(select_sql_installed_by)
                app.logger.info(distinct_order_id_sql)

                # cursor.execute(distinct_order_id_sql)
                # distinct_order_id_list = cursor.fetchall()
                # distinct_order_id_list = [i[0] if i[0] else "" for i in distinct_order_id_list]
                distinct_order_id_list = mysql.select_by_sql_with_long_time_cache(database_name,
                                                                                  distinct_order_id_sql)
                distinct_order_id_list = [i[0] for i in distinct_order_id_list]
            except:
                app.logger.info(distinct_order_id_sql)
                distinct_order_id_list = []

            # 所有district
            district_list_sql = "SELECT distinct district FROM " + table_name

            # # 所有town
            # town_district_sql = "SELECT distinct town FROM " + table_name
            #
            # # 所有pcs
            # pcs_district_sql = "SELECT distinct pcs FROM " + table_name

            try:

                # app.logger.info(select_sql)
                app.logger.info(select_sql_by)
                cursor.execute(select_sql_by)
                dp_status_type_by = cursor.fetchall()

                # 可以获取查询字段名字
                # test_col = cursor.description
                # app.logger.info(test_col)
                app.logger.info(select_sql_total_num)
                cursor.execute(select_sql_total_num)
                total_num_result = cursor.fetchall()
                total_num = total_num_result[0][0]

                if dp_status_type == "collected":
                    uploaded_photos_far_total_num = int(total_num_result[0][1])
                elif dp_status_type == "installed":
                    uploaded_photos_cls_total_num = int(total_num_result[0][1])
                    uploaded_photos_far_total_num = int(total_num_result[0][2])

                app.logger.info(select_sql_dp_num)
                cursor.execute(select_sql_dp_num)
                dp_num = cursor.fetchall()
                dp_total_num = dp_num[0][0]

                app.logger.info(community_district_sql)
                # cursor.execute(community_district_sql)
                # community_list = [i[0] for i in cursor.fetchall()]
                community_list = mysql.select_by_sql_with_long_time_cache(database_name,
                                                                          community_district_sql)
                community_list = [i[0] for i in community_list]

                app.logger.info(district_list_sql)
                # cursor.execute(district_list_sql)
                # district_list = [i[0] for i in cursor.fetchall()]
                district_list = mysql.select_by_sql_with_long_time_cache(database_name,
                                                                         district_list_sql)
                district_list = [i[0] for i in district_list]

                app.logger.info(town_district_sql)
                # cursor.execute(town_district_sql)
                # town_list = [i[0] for i in cursor.fetchall()]
                town_list = mysql.select_by_sql_with_long_time_cache(database_name,
                                                                     town_district_sql)
                town_list = [i[0] for i in town_list]

                app.logger.info(pcs_district_sql)
                # cursor.execute(pcs_district_sql)
                # pcs_list = [i[0] for i in cursor.fetchall()]
                pcs_list = mysql.select_by_sql_with_long_time_cache(database_name,
                                                                    pcs_district_sql)
                pcs_list = [i[0] for i in pcs_list]

                # app.logger.info(installed_by)
                app.logger.info(total_num)

                app.logger.info(uploaded_photos_far_total_num)
                app.logger.info(dp_num)
                # app.logger.info(sq_list)
                CITY_items = CITY.items()

                if dp_status_type == "collected":
                    for i in dp_status_type_by:
                        if not i[3]:
                            i[3] = datetime.datetime.strptime("2000-01-01 00:00:00")
                        if not i[4]:
                            i[4] = datetime.datetime.strptime("2000-01-01 00:00:00")
                    return_data = {
                        "status": [{"name": i[0],
                                    "num": i[1],
                                    "photos_cls_num": 0,
                                    "photos_far_num": i[2],
                                    "min_date": i[3].strftime('%Y-%m-%d %H:%M:%S'),
                                    "max_date": i[4].strftime('%Y-%m-%d %H:%M:%S'),
                                    } for i in dp_status_type_by],
                        "total_num": total_num,
                        "uploaded_photos_far_total_num": uploaded_photos_far_total_num,
                        "dp_total_num": dp_total_num,
                        "district_list": district_list,
                        "town_list": town_list,
                        "pcs_list": pcs_list,
                        "community_list": community_list,
                        'city_list': [i for i in CITY_items],
                        "status_count": len(dp_status_type_by),
                        "contract_batch_list": distinct_contract_batch_list,
                        "order_batch_list": distinct_order_batch_list,
                        "order_id_list": distinct_order_id_list
                    }
                elif dp_status_type == "installed":

                    for i in dp_status_type_by:
                        if not i[4]:
                        #if not i[5]:
                            i[4] = datetime.datetime.strptime("2000-01-01 00:00:00")
                        if not i[5]:
                            i[5] = datetime.datetime.strptime("2000-01-01 00:00:00")
                    return_data = {
                        "status": [{"name": i[0],
                                              "num": i[1],
                                              "photos_cls_num": i[2],
                                              "photos_far_num": i[3],
                                              "min_date": i[4].strftime('%Y-%m-%d %H:%M:%S'),
                                              "max_date": i[5].strftime('%Y-%m-%d %H:%M:%S'),
                                              } for i in dp_status_type_by],
                        "total_num": total_num,
                        "uploaded_photos_cls_total_num": uploaded_photos_cls_total_num,
                        "uploaded_photos_far_total_num": uploaded_photos_far_total_num,
                        "dp_total_num": dp_total_num,
                        "district_list": district_list,
                        "town_list": town_list,
                        "pcs_list": pcs_list,
                        "community_list": community_list,
                        'city_list': [i for i in CITY_items],
                        "status_count": len(dp_status_type_by),
                        "contract_batch_list": distinct_contract_batch_list,
                        "order_batch_list": distinct_order_batch_list,
                        "order_id_list": distinct_order_id_list
                    }
                    # return_data = {
                    #             "installed_status": [{"name": i[0],
                    #                                   "installed_num": i[1],
                    #                                   "installed_photos_cls_num": i[2],
                    #                                   "installed_photos_far_num": i[3],
                    #                                   "min_installed_date": i[4].strftime('%Y-%m-%d %H:%M:%S'),
                    #                                   "max_installed_date": i[5].strftime('%Y-%m-%d %H:%M:%S'),
                    #                                   } for i in dp_status_type_by],
                    #             "installed_total_num": total_num,
                    #             "uploaded_photos_cls_total_num": uploaded_photos_cls_total_num,
                    #             "uploaded_photos_far_total_num": uploaded_photos_far_total_num,
                    #             "dp_total_num": dp_total_num,
                    #             "district_list": district_list,
                    #             "town_list": town_list,
                    #             "pcs_list": pcs_list,
                    #             "community_list": community_list,
                    #             'city_list': [i for i in CITY_items],
                    #             "installed_status_count": len(dp_status_type_by),
                    #             "contract_batch_list": distinct_contract_batch_list,
                    #             "order_batch_list": distinct_order_batch_list,
                    #             "order_id_list": distinct_order_id_list
                    #         }


                if dp_status_type_by:

                    # return_data = {
                    #     "installed_statue": installed_by,
                    #     "installed_total_num": installed_total_num,
                    #     "uploaded_photos_total_num": uploaded_photos_total_num,
                    #     "dp_total_num": dp_total_num,
                    #     "sq_list": sq_list
                    #
                    # }
                    # 提交到数据库执行
                    db.commit()
                    # 关闭数据库连接
                    db.close()
                    return jsonify(common.trueReturn(return_data, "查询成功"))
                else:
                    # return_data = {
                    #     "installed_statue": installed_by,
                    #     "installed_total_num": installed_total_num,
                    #     "uploaded_photos_total_num": uploaded_photos_total_num,
                    #     "dp_total_num": dp_total_num,
                    #     "sq_list": sq_list
                    #
                    # }
                    # 提交到数据库执行
                    db.commit()
                    # 关闭数据库连接
                    db.close()
                    return jsonify(common.falseReturn(return_data, "查询无结果"))

            except:
                app.logger.info(select_sql_by)
                app.logger.info(select_sql_total_num)
                app.logger.info(select_sql_dp_num)
                app.logger.info(community_district_sql)
                app.logger.info(district_list_sql)
                # app.logger.info(installed_by)
                #app.logger.info(total_num)
                #app.logger.info(uploaded_photos_far_total_num)
                #app.logger.info(dp_num)
                # 如果发生错误则回滚
                # traceback.print_exc()
                db.rollback()
                # 关闭数据库连接
                db.close()
                app.logger.info("查询接口/dp_status有错误")
                return jsonify(common.falseReturn("", "检查查询参数有无错误"))

        elif request.args.get('type') == REQUEST_TYPE.collected_report_excel.name:
            app.logger.info("下载门牌采集统计表")

            if request.args.get('type') == REQUEST_TYPE.collected_report_excel.name:
                dp_status_type = "collected"
            #elif request.args.get('type' == REQUEST_TYPE.installed.name:
            else:
                dp_status_type = "installed"
                
            if not request.args.get('city'):
                return common.falseReturn("", "没有传入城市参数！")
            else:
                city = request.args.get('city')
                db_name = CITY.get_db_name(city)
                table_name = CITY.get_table_name(city)
            if not request.args.get('date_type'):
                # return common.falseReturn("", "没有传入start_date参数！")
                date_type = "{dp_status_type}_date"
                date_type = date_type.format(dp_status_type=dp_status_type)
            else:
                date_type = request.args.get('date_type')
            if not request.args.get('start_date'):
                # return common.falseReturn("", "没有传入start_date参数！")
                start_date = "1970-01-01 08:00:00"
            else:
                start_date = request.args.get('start_date')
            if not request.args.get('end_date'):
                end_date = common.format_ymdhms_time_now()
            else:
                end_date = request.args.get('end_date')
            if not request.args.get('by'):
                dp_status_type_by = ''
            else:
                dp_status_type_by = request.args.get('by')
            if not request.args.get('report_type'):
                # return common.falseReturn("", "没有传入report_type参数！")
                pass
            else:
                report_type = request.args.get('report_type')
            if not request.args.get('group_by'):
                # return common.falseReturn("", "没有传入group_by参数！")
                group_by = "by"
            else:
                group_by = request.args.get('group_by')
                # if group_by.find("installed_by") < 0:
                #     group_by += ",installed_by"
            if not request.args.get('type'):
                return common.falseReturn("", "没有传入type参数！")
            else:
                type = request.args.get('type')

            if not request.args.get('report_date_type'):
                #return common.falseReturn("", "没有传入report_date_type参数！")
                report_date_type = "month"
            else:
                report_date_type = request.args.get('report_date_type')

            dp_status_type_by_by_sql = " AND {dp_status_type}_by = " + "\"" + dp_status_type_by + "\"" if dp_status_type_by else ""
            dp_status_type_by_by_sql = dp_status_type_by_by_sql.format(dp_status_type=dp_status_type)
            date_sql = " AND {date_type} >= " + "\"" + start_date + "\"" + " AND {date_type} <= " + "\"" + end_date + "\""
            date_sql = date_sql.format(date_type=date_type)
            # upload_date_sql = " AND installed_date >= " + "\"" + start_date + "\"" + " AND installed_date <= " + "\"" + end_date + "\""

            # app.logger.info("group_by %s", group_by)

            group_by = group_by.split(",")
            #group_by = [dp_status_type + "_" + i for i in group_by]

            day_date_format = " DATE_FORMAT(`installed_date`, '%Y-%m-%d') "

            if report_date_type == "day":
                group_by.append(day_date_format)


            filter_sql = ""

            filter_sql = date_sql + dp_status_type_by_by_sql

            # group_by_list =

            # count_photos_far_sql = "SELECT COUNT(`installed_photos_far`>0 or NULL), `installed_by` FROM fs_dp GROUP BY `installed_by`"
            # count_photos_far_results = mysql.select_by_sql(db_name, count_photos_far_sql)
            # app.logger.info(count_photos_far_results)
            # count_photos_cls_sql = "SELECT COUNT(`installed_photos_far`>0 or NULL), `installed_by` FROM fs_dp GROUP BY `installed_by`"
            # count_photos_cls_results = mysql.select_by_sql(db_name, count_photos_cls_sql)
            # app.logger.info(count_photos_cls_results)
            count_info_sql = " SELECT COUNT({dp_status_type}>0 or NULL), COUNT({dp_status_type}_photos>0 or NULL), " + ",".join(
                group_by) + " FROM " + \
                                       table_name + " WHERE {dp_status_type}_by is not NULL " + filter_sql \
                                       + " GROUP BY  " + ",".join(group_by)


            if report_date_type == "day":
                count_info_sql += " ORDER BY " + day_date_format + " ASC "



            count_info_sql = count_info_sql.format(dp_status_type=dp_status_type)
            print(count_info_sql)
            results = mysql.select_by_sql(db_name, count_info_sql)
            print(results)


            if report_date_type == "day":
                # results = sorted(results, key=lambda x: (x[-2], x[-1])) # 按日期和安装人排序
                results = sorted(results, key=lambda x: (x[-1]))  # 只按日期排序

            if not results:
                return jsonify(
                    common.falseReturn({"report_excel_path": ""}, "查询未成功，可能是没有相关数据，或者筛选的列有问题。检查选择的列以及条件是否有错误"))

            # col_name_map = ExcelModel.col_name_map
            col_name_map = mysql.get_col_name_map()

            data_map = collections.OrderedDict()  # keys是有序字典，先加入的在前面

            for i, value in enumerate(results):
                col_index = 0
                if i == 0:
                    data_map['数量'] = [value[col_index]]
                    col_index += 1
                    data_map['远照片'] = [value[col_index]]
                    #col_index += 1
                    data_map['近照片'] = [0]
                    #col_index += 1
                    data_map['总数'] = [value[col_index]]
                    col_index += 1
                    # data_map['安装人'] = [value[3]]
                    for j in group_by:
                        j = col_name_map.get(j) if col_name_map.get(j) else j

                        if j == day_date_format:
                            j = "日期"
                        data_map[j] = [value[col_index]]
                        col_index += 1
                else:
                    data_map['数量'].append(value[col_index])
                    col_index += 1
                    data_map['远照片'].append(value[col_index])
                    #col_index += 1
                    data_map['近照片'].append(0)
                    #col_index += 1
                    data_map['总数'].append(value[col_index])
                    col_index += 1
                    # data_map['安装人'].append(value[3])
                    for j in group_by:
                        j = col_name_map.get(j) if col_name_map.get(j) else j

                        if j == day_date_format:
                            j = "日期"
                        data_map[j].append([value[col_index]])
                        col_index += 1
            app.logger.info(data_map)
            title_info = []
            title_info.append([CITY.get_city_name_map()[city] + "门牌采集数据统计"])
            title_info.append(["时间段: ", start_date, end_date])
            report_excel_path = ExcelModel.data_map_to_excel(data_map, path=config.TEMP_DOWNLOAD_DATAS_PATH,
                                                             excel_name='report_' + common.format_ymdhms_time_now_for_filename() + '.xls',
                                                             title_info=title_info)
            return jsonify(common.trueReturn({"report_excel_path": report_excel_path}, "查询成功"))


        # # return '成功上传'
        # return jsonify(common.trueReturn("", "上传成功"))

        return jsonify(common.falseReturn("", "查询未成功，可能是请求有问题"))

    # 安装情况获取
    @app.route('/dp_status', methods=['GET', 'POST'])
    def dp_status():
        app.logger.info("request: %s", request)
        app.logger.info("dp_status %s", request)
        result = Auth.identify(Auth, request)
        app.logger.info("状态: %s 用户: %s ", result.get('status'),  result.get('data'))
        if (result['status'] and result['data']):
            pass
        else:
            return jsonify(result)
            # return json.dumps(result, ensure_ascii=False)

        if request.method == 'GET':
            return dp_status_get(request)
        else:
            return jsonify(common.falseReturn("", "查询未成功，可能是请求有问题"))

    @app.route('/scripts', methods=['GET', 'POST'])
    def script():
        app.logger.info("request: %s", request)
        result = Auth.identify(Auth, request)
        username_now = "unknown"
        app.logger.info("状态: %s 用户: %s ", result.get('status'), result.get('data'))
        if (result['status'] and result['data']):
            # app.logger.info(result)
            username_now = result['data']['username']
        else:
            #return json.dumps(result, ensure_ascii=False)
            return jsonify(result)

        if request.method == 'GET':
            if request.args.get('type') == REQUEST_TYPE.scripts.name:
                if not os.path.isdir(config.DY_DATAS_SCRIPTS_PATH):
                    os.makedirs(config.DY_DATAS_SCRIPTS_PATH)
                scripts_files = os.listdir(config.DY_DATAS_SCRIPTS_PATH)
                scripts_files_map = {}
                for file in scripts_files:
                    scripts_files_map[file] = os.path.join(config.DY_DATAS_SCRIPTS_PATH, file)
                return jsonify(common.trueReturn({"scripts": scripts_files_map}, msg='scripts脚本'))
            else:
                return jsonify(common.falseReturn("", msg='type有问题'))

        if request.method == 'POST':
            if request.form.get('type') == REQUEST_TYPE.scripts.name:
                if not os.path.isdir(config.DY_DATAS_SCRIPTS_PATH):
                    os.mkdir(config.DY_DATAS_SCRIPTS_PATH)
                scripts_file = request.files.get("file")
                upload_path = os.path.join(config.DY_DATAS_SCRIPTS_PATH, scripts_file.filename)
                scripts_file.save(upload_path)
                app.logger.info("文件保存在：%s", upload_path)
                return jsonify(common.trueReturn({"path": upload_path}, msg='脚本上传成功'))
            else:
                return jsonify(common.falseReturn("", msg='type有问题'))

