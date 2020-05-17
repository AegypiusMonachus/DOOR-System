'''

    version: 0.9.0
    create: 2019-03-15
    update: 2019-10-25
    author: Cong

    tips:
        gunicorn 不支持 argparse!!! 千万别在用gunicorn的时候用 argparse!!!
'''
from flask import jsonify
from App.auth.auths import Auth
import App.common as common
# 导入数据库模块
import pymysql
# abort 异常
from flask import abort
# 发送文件的
from flask import send_file
# 导入前台请求的request模块
import traceback
from flask import request
# 导入json
import json
from flask import Response
import os
import tempfile
from werkzeug.utils import secure_filename
from App.datas import excel as ExcelModel
from App.datas import dp_sort
from App.datas import query
from App.datas import export_excel
# from App.datas.excel import col_name_map
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
from App.datas.api import CITY


class PROJECTS_REQUEST_TYPE(enum.IntEnum):
    '''
    projects 项目
    projects_status_static 获取项目管理状态统计
    projects_status_detail 获取项目管理状态详细
    projects_test
    '''
    projects, projects_status_static, projects_status_detail, projects_test = range(4)

    @classmethod
    def has_value(cls, value):
        return any(value == item.value for item in cls)

    @classmethod
    def has_key(cls, key):
        return any(key == item.name for item in cls)

# 默认 不获取详细表
#@long_time_cache.memoize(timeout=config.long_cache_timeout)
def get_projects_status(city, detail=False):
    if detail:
        db_name = CITY.get_db_name(city)
        table_name = CITY.get_table_name(city)


        select_city_sql = " WHERE projects.`city`=\"" + city + "\" "

        # 精准查询
        accurate_query_key = []
        for key in request.args.keys():
            if key.find('_accurate') > 0:
                accurate_query_key.append(key[0:key.find('accurate') - 1])

        sql_accurate_query = ''
        if len(accurate_query_key) > 0:
            # logger.info(query_key)
            for key in accurate_query_key:
                if key == 'index':
                    sql_accurate_query += ' AND ' + 'cast( projects.`' + key + '` as char )' + ' = \'' + request.args.get(
                        str(key + '_accurate')) + '\''
                else:
                    sql_accurate_query += ' AND projects.`' + key + '` = \'' + request.args.get(str(key + '_accurate')) + '\''

        condition_sql = select_city_sql + sql_accurate_query

        # select_sql = "SELECT projects.`contract_batch`, projects.`order_batch`, projects.`order_id`, COUNT(*)," \
        #              "COUNT(installed>0 or NULL), COUNT(installed_photos_cls>0 or NULL), COUNT(installed_photos_far>0 or NULL), " \
        #              "projects.`index`" \
        #              " FROM {table_name} INNER JOIN projects ON projects.`index`={table_name}.`projects_index` " + condition_sql + \
        #              " GROUP BY projects.`index` "
        #              #" GROUP BY projects.`index`, `contract_batch`,`order_batch`,`order_id` "

        select_sql = "SELECT projects.`contract_batch`," \
                     " projects.`order_batch`," \
                     " projects.`order_id`," \
                     " IFNULL(COUNT_1, 0)," \
                     " IFNULL(COUNT_2, 0)," \
                     " IFNULL(COUNT_3, 0), " \
                     "IFNULL(COUNT_4, 0)," \
                     " projects.`index`, " \
                     " projects.`project_name`, " \
                     " projects.`director` " \
                     "FROM projects left JOIN " \
                     "(SELECT `projects_index`, " \
                     "COUNT(*) as COUNT_1, " \
                     "COUNT(installed>0 or NULL) as COUNT_2, " \
                     "COUNT(installed_photos_cls>0 or NULL) as COUNT_3," \
                     "COUNT(installed_photos_far>0 or NULL) as COUNT_4 " \
                     "FROM {table_name} GROUP BY `projects_index`) t1 ON projects.`index` = t1.`projects_index`" \
                     + condition_sql

        select_sql = select_sql.format(table_name=table_name)
        result = mysql.select_by_sql_with_long_time_cache(db_name, select_sql)
        details_list = []
        details_map = {}
        total_temp_map = {}
        total_dp_nums = 0
        total_installed_nums = 0
        total_installed_photos_cls_nums = 0
        total_installed_photos_far_nums = 0


        for i in result:

            if i[0] not in total_temp_map.keys():
                total_temp_map[i[0]] = {}
            if i[1] not in total_temp_map[i[0]].keys():
                total_temp_map[i[0]][i[1]] = {}
                total_temp_map[i[0]][i[1]] = []
            total_temp_map[i[0]][i[1]].append({"contract_batch": i[0],
                                                "order_batch": i[1],
                                                "order_id": i[2],
                                                "doorplates_nums": i[3],
                                               "installed_nums": i[4],
                                               "installed_photos_cls_nums": i[5],
                                               "installed_photos_far_nums": i[6],
                                               "index": i[7],
                                               "project_name": i[8],
                                               "director": i[9]})
            total_dp_nums += i[3]
            total_installed_nums += i[4]
            total_installed_photos_cls_nums += i[5]
            total_installed_photos_far_nums += i[6]

        for contract_batch, order_batch_map in total_temp_map.items():
            temp_map = {}
            temp_map["contract_batch"] = contract_batch
            temp_map["order_batch_nums"] = len(total_temp_map[contract_batch])
            temp_map["order_batch_list"] = []
            temp_order_id_nums_for_temp_map = 0
            temp_dp_nums_for_temp_map = 0
            temp_installed_nums_for_temp_map = 0
            temp_installed_photos_cls_nums_for_temp_map = 0
            temp_installed_photos_far_nums_for_temp_map = 0
            for order_batch, order_id_list in total_temp_map[contract_batch].items():
                order_batch_map = {}
                order_batch_map["contract_batch"] = contract_batch
                order_batch_map["order_batch"] = order_batch
                order_batch_map["order_id_nums"] = len(order_id_list)
                temp_order_id_nums_for_temp_map += len(order_id_list)
                order_batch_map["order_id_list"] = order_id_list
                dp_nums = 0
                temp_installed_nums = 0
                temp_installed_photos_cls_nums = 0
                temp_installed_photos_far_nums = 0
                for i in order_id_list:
                    dp_nums += i["doorplates_nums"]
                    temp_installed_nums += i["installed_nums"]
                    temp_installed_photos_cls_nums += i["installed_photos_cls_nums"]
                    temp_installed_photos_far_nums += i["installed_photos_far_nums"]
                order_batch_map["doorplates_nums"] = dp_nums
                temp_dp_nums_for_temp_map += dp_nums
                order_batch_map["installed_nums"] = temp_installed_nums
                temp_installed_nums_for_temp_map += temp_installed_nums
                order_batch_map["installed_photos_cls_nums"] = temp_installed_photos_cls_nums
                temp_installed_photos_cls_nums_for_temp_map += temp_installed_photos_cls_nums
                order_batch_map["installed_photos_far_nums"] = temp_installed_photos_far_nums
                temp_installed_photos_far_nums_for_temp_map += temp_installed_photos_far_nums
                temp_map["order_batch_list"].append(order_batch_map)
            temp_map["order_id_nums"] = temp_order_id_nums_for_temp_map
            temp_map["doorplates_nums"] = temp_dp_nums_for_temp_map
            temp_map["installed_nums"] = temp_installed_nums_for_temp_map
            temp_map["installed_photos_cls_nums"] = temp_installed_photos_cls_nums_for_temp_map
            temp_map["installed_photos_far_nums"] = temp_installed_photos_far_nums_for_temp_map

            details_list.append(temp_map)


        #for i in result:
        #     if i[0] not in details_map.keys():
        #         details_map[i[0]] = {}
        #         details_map[i[0]]["orders"] = []
        #         details_map[i[0]]["nums"] = 0
        #     # if i[1] not in details_map[i[0]].keys():
        #     #     details_map[i[0]][i[1]] = []
        #     details_map[i[0]]["orders"].append({"order_batch": i[1],
        #                                         "order_id": i[2],
        #                                         "numbers_of_dp": i[3]})
        #     details_map[i[0]]["nums"] += 1
        #
        # for contract_batch, details in details_map.items():
        #     temp_map = {}
        #     temp_map["contract_batch"] = contract_batch
        #     temp_map["orders"] = details["orders"]
        #     temp_map["nums"] = details["nums"]
        #     details_list.append(temp_map)
        #
        ret_map = {"total_dp_nums": total_dp_nums,
                   "total_installed_nums": total_installed_nums,
                   "total_installed_photos_cls_nums": total_installed_photos_cls_nums,
                   "total_installed_photos_far_nums": total_installed_photos_far_nums
                   }

        return result, details_map, details_list, ret_map
    else:

        db_name = CITY.get_db_name(city)
        table_name = "projects"

        select_city_sql = " WHERE `city`=\"" + city + "\" "

        # 精准查询
        accurate_query_key = []
        for key in request.args.keys():
            if key.find('_accurate') > 0:
                accurate_query_key.append(key[0:key.find('accurate') - 1])

        sql_accurate_query = ''
        if len(accurate_query_key) > 0:
            # logger.info(query_key)
            for key in accurate_query_key:
                # if sql_accurate_query == '':
                #     if key == 'index':
                #         sql_accurate_query += ' WHERE ' + 'cast( `' + key + '` as char )' + ' = \'' + request.args.get(
                #             str(key + '_accurate')) + '\''
                #     else:
                #         sql_accurate_query += ' WHERE ' + key + ' = \'' + request.args.get(str(key + '_accurate')) + '\''
                # else:
                if key == 'index':
                    sql_accurate_query += ' AND ' + 'cast( `' + key + '` as char )' + ' = \'' + request.args.get(
                        str(key + '_accurate')) + '\''
                else:
                    sql_accurate_query += ' AND ' + key + ' = \'' + request.args.get(str(key + '_accurate')) + '\''
            # if request.args.get('_page'):
            #     sql = "SELECT * FROM " + table_name + sql_accurate_query + sql_limit
            # else:
            #     sql = "SELECT * FROM " + table_name + sql_accurate_query + sql_limit



        select_sql = "SELECT * FROM " + table_name + select_city_sql + sql_accurate_query


        table_name = "projects"
        #select_sql = "SELECT `contract_batch`, `order_batch`, `order_id`, `index`  FROM {table_name}  "
        #select_sql = "SELECT *  FROM {table_name} WHERE `city`=\"{city}\""
        #select_sql = select_sql.format(table_name=table_name, city=city)
        #result = mysql.select_by_sql_with_long_time_cache(db_name, select_sql)
        result = mysql.select_by_sql_with_long_time_cache(db_name, select_sql, need_col_name=True)
        status_list = result
        #status_list = []
        status_map = {}
        # for i in result:
        #     if i[0] not in status_map.keys():
        #         status_map[i[0]] = {}
        #         status_map[i[0]]["orders"] = []
        #     # if i[1] not in details_map[i[0]].keys():
        #     #     details_map[i[0]][i[1]] = []
        #     status_map[i[0]]["orders"].append({"order_batch": i[1],
        #                                     "order_id": i[2],
        #                                     "index": i[3]})
        # for contract_batch, details in status_map.items():
        #     temp_map = {}
        #     temp_map["contract_batch"] = contract_batch
        #     temp_map["orders"] = details["orders"]
        #     status_list.append(temp_map)

        ret_map = {}

        return result, status_map, status_list, ret_map

# 单纯获取合同批次、订单批次、订单号列
def get_projects_status_list(city):
    db_name = CITY.get_db_name(city)
    table_name = "projects"

    select_city_sql = " WHERE `city`=\"" + city + "\" "

    # 精准查询
    accurate_query_key = []
    for key in request.args.keys():
        if key.find('_accurate') > 0:
            accurate_query_key.append(key[0:key.find('accurate') - 1])

    sql_accurate_query = ''
    if len(accurate_query_key) > 0:
        # logger.info(query_key)
        for key in accurate_query_key:
            if key == 'index':
                sql_accurate_query += ' AND ' + 'cast( `' + key + '` as char )' + ' = \'' + request.args.get(
                    str(key + '_accurate')) + '\''
            else:
                sql_accurate_query += ' AND ' + key + ' = \'' + request.args.get(str(key + '_accurate')) + '\''

    project_name_select_sql = "SELECT DISTINCT(`project_name`) FROM " + table_name + select_city_sql + sql_accurate_query
    contract_batch_select_sql = "SELECT DISTINCT(`contract_batch`) FROM " + table_name + select_city_sql + sql_accurate_query
    order_batch_select_sql = "SELECT DISTINCT(`order_batch`) FROM " + table_name + select_city_sql + sql_accurate_query
    order_id_select_sql = "SELECT DISTINCT(`order_id`) FROM " + table_name + select_city_sql + sql_accurate_query

    project_name_list = mysql.select_by_sql_with_long_time_cache(db_name, project_name_select_sql)
    contract_batch_list = mysql.select_by_sql_with_long_time_cache(db_name, contract_batch_select_sql)
    order_batch_list = mysql.select_by_sql_with_long_time_cache(db_name, order_batch_select_sql)
    order_id_list = mysql.select_by_sql_with_long_time_cache(db_name, order_id_select_sql)

    project_name_list = [i[0] for i in project_name_list]
    contract_batch_list = [i[0] for i in contract_batch_list]
    order_batch_list = [i[0] for i in order_batch_list]
    order_id_list = [i[0] for i in order_id_list]

    return project_name_list, contract_batch_list, order_batch_list, order_id_list

def init_api(app):
    # cache = Cache()  # 缓存 要更改使用的类型，例如redis，在config改
    # cache.init_app(app)

    # 检索数据
    @app.route('/projects', methods=['GET'])
    # @cache.cached(timeout=config.cache_timeout, key_prefix='view')
    def projects_get():
        app.logger.info("projects_get")
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
            return jsonify(result)

        # col_name_map = mysql.get_col_name_map()
        #
        # col_name_list = get_col_name_list(request)

        request_json = request.get_json()

        if request.method == 'GET':


            #long_time_cache.clear()
            if request.args.get('type') == PROJECTS_REQUEST_TYPE.projects_status_detail.name:
                if not request.args.get("city"):
                    city = [i for i in CITY.items()]
                else:
                    city = [request.args.get("city")]

                return_datas = []
                for index, i in enumerate(city):
                    result, status_map, status_list, ret_map = get_projects_status(i)
                    project_name_list, contract_batch_list, order_batch_list, order_id_list = get_projects_status_list(i)
                    return_datas.append({"city": i,
                                         "project_name_list": project_name_list,
                                    "contract_batch_list": contract_batch_list,
                                    "order_batch_list": order_batch_list,
                                    "order_id_list": order_id_list,
                                    "details_list": status_list})


                return jsonify(common.trueReturn(return_datas,
                                                 "orders: [[订单批号，订单号],....], contract_nums: 合同数量 ", addition={"city_list": city}))

            elif request.args.get('type') == PROJECTS_REQUEST_TYPE.projects_status_static.name:
                # 获取项目管理状态信息

                '''
                临时版 2019-09-05
                '''
                if not request.args.get("city"):
                    city = [i for i in CITY.items()]
                else:
                    city = [request.args.get("city")]

                return_datas = []
                for index, i in enumerate(city):
                    result, status_detail_map, status_detail_list, ret_map = get_projects_status(i, detail=True)
                    project_name_list, contract_batch_list, order_batch_list, order_id_list = get_projects_status_list(i)

                    return_datas.append({"city": i,
                                         "project_name_list": project_name_list,
                                         "contract_batch_list": contract_batch_list,
                                         "order_batch_list": order_batch_list,
                                         "order_id_list": order_id_list,
                                    "status_detail_map": status_detail_map,
                                    "status_detail_list": status_detail_list,
                                    "contract_nums": len(status_detail_list),
                                    "order_nums": len(result),
                                    "statics": ret_map}
                                        )


                return jsonify(common.trueReturn(return_datas,
                                                 "orders: [[订单批号，订单号, 门牌数量],....], contract_nums: 合同数量 ", addition={"city_list": city}))

            else:
                return jsonify(common.falseReturn("", "接口参数传递出错，检查type"))

    # 新建、修改数据
    @app.route('/projects', methods=['PUT', 'POST'])
    def projects_PUT_POST():
        app.logger.info("projects_PUT_POST")
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
            return jsonify(result)

        request_json = request.get_json()

        if request.method == 'PUT':

            if request_json.get('type') == PROJECTS_REQUEST_TYPE.projects.name:

                if not request_json.get("update_datas"):
                    return jsonify(common.falseReturn("",
                                                      "没有要修改的数据"))
                else:
                    update_datas_map = request_json.get("update_datas")

                    select_status, select_msg, select_date, result = mysql.select_data("ws_doorplate", "projects",
                                                                                       data_map=update_datas_map,
                                                                                       select_col=["index"])
                    # print("resultresult", result)
                    if not result:
                        pass
                    else:
                        return jsonify(common.falseReturn({"index": result[0][0]},
                                                          "数据已经存在，新建失败，直接使用", addition=common.false_Type.exist))

                if not request_json.get("index"):
                    return jsonify(common.falseReturn("",
                                                      "没有传入要修改数据的index"))
                else:
                    index = request_json.get("index")

                status, msg, date, num = mysql.update_data("ws_doorplate", "projects",
                                                           data_map=update_datas_map,
                                                           data_select_map={"index": index})

                if status:
                    long_time_cache.clear()
                    return jsonify(common.trueReturn("",
                                                     msg))
                else:
                    return jsonify(common.falseReturn("",
                                                     msg))
            else:
                return jsonify(common.falseReturn("",
                                                  "传入的type不正确或者没有传type"))

        elif request.method == 'POST':

            if request_json.get('type') == PROJECTS_REQUEST_TYPE.projects.name:

                if not request_json.get("uploaded_by"):
                    if not result.get('data').get('username'):
                        uploaded_by = "没有填写"
                    else:
                        uploaded_by = result.get('data')["username"]
                else:
                    uploaded_by = request.args.get("uploaded_by")
                if not request_json.get("insert_datas"):
                    return jsonify(common.falseReturn("",
                                                      "没有要新建的数据"))
                else:

                    insert_datas_map = request_json.get("insert_datas")

                    select_status, select_msg, select_date, result = mysql.select_data("ws_doorplate", "projects",
                                                                                       data_map=insert_datas_map,
                                                                                       select_col=["index"])
                    #print("resultresult", result)
                    if not result:
                        pass
                    else:
                        return jsonify(common.falseReturn({"index": result[0][0]},
                                                          "数据已经存在，新建失败，直接使用", addition=common.false_Type.exist))

                    # 如果数据不存在，才增加时间然后往下走插入数据
                    insert_datas_map["uploaded_date"] = common.format_ymdhms_time_now()


                status, msg, date, num = mysql.insert_data("ws_doorplate", "projects", uploaded_by=uploaded_by, data_map=insert_datas_map)

                select_status, select_msg, select_date, result = mysql.select_data("ws_doorplate", "projects", data_map=insert_datas_map, select_col=["index"])

                status = status & select_status

                msg = msg + " \n " + select_msg

                if status:
                    long_time_cache.clear()
                    return jsonify(common.trueReturn({"index": result[0][0]},
                                                     msg))
                else:
                    return jsonify(common.falseReturn("",
                                                     msg))
            else:
                return jsonify(common.falseReturn("",
                                                  "传入的type不正确或者没有传type"))

        else:
            return jsonify(common.falseReturn("",
                                              "后端出错"))


    # 返回不同状态的项目数量
    @app.route('/projectLists/progress', methods=['GET'])
    def projectLists_progress():
        app.logger.info("projects_PUT_POST")
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


        if request.args.get("city"):
            db_name = CITY.get_db_name(request.args.get("city"))
        else:
            return jsonify(common.falseReturn("", "没有传city参数"))


        ret_array = []
        ret_map_values = ["待生产", "生产中", "已完成", "已出货", "已暂停"]

        # wait_for_producing_select_sql = ""

        # result = mysql.select_by_sql_with_long_time_cache(db_name, wait_for_producing_select_sql, need_col_name=True)
        # status_list = result
        # status_list = []
        for i in ret_map_values:
            sum = 1
            status_map = {}
            status_map["progress"] = i
            status_map["sum"] = sum
            ret_array.append(status_map)


        return jsonify(common.trueReturn(ret_array, ""))

        # 返回不同状态的项目数量



    #
    # # 返回所有的负责人和项目编号
    # @app.route('projects/infor', methods=['GET'])
    # def projects_infor():
    #     app.logger.info("projects_PUT_POST")
    #     app.logger.info("request: %s", request)
    #     app.logger.info("当前访问用户：%s", request.remote_addr)
    #     # app.logger.info("Authorization：", request.headers['Authorization'])
    #
    #     result = Auth.identify(Auth, request)
    #     # app.logger.info(result)
    #     app.logger.info("状态: %s 用户: %s ", result.get('status'), result.get('data'))
    #     if (result['status'] and result['data']):
    #         pass
    #     else:
    #         # return json.dumps(result, ensure_ascii=False)
    #         return jsonify(result)
    #
    #     if request.args.get("city"):
    #         db_name = CITY.get_db_name(request.args.get("city"))
    #     else:
    #         return jsonify(common.falseReturn("", "没有传city参数"))
    #
    #     ret_array = []
    #     ret_map_values = ["待生产", "生产中", "已完成", "已出货", "已暂停"]
    #
    #     wait_for_producing_select_sql = ""
    #
    #     result = mysql.select_by_sql_with_long_time_cache(db_name, select_sql, need_col_name=True)
    #     status_list = result
    #     # status_list = []
    #     status_map = {}
    #
    #     return jsonify(common.trueReturn("", ""))
    #
    # # 返回今日，本周，本月，特定项目(从下单日期开始算)
    # @app.route('projects/startTime', methods=['GET'])
    # def projects_startTime():
    #     app.logger.info("projects_PUT_POST")
    #     app.logger.info("request: %s", request)
    #     app.logger.info("当前访问用户：%s", request.remote_addr)
    #     # app.logger.info("Authorization：", request.headers['Authorization'])
    #
    #     result = Auth.identify(Auth, request)
    #     # app.logger.info(result)
    #     app.logger.info("状态: %s 用户: %s ", result.get('status'), result.get('data'))
    #     if (result['status'] and result['data']):
    #         pass
    #     else:
    #         # return json.dumps(result, ensure_ascii=False)
    #         return jsonify(result)
    #
    #     if request.args.get("city"):
    #         db_name = CITY.get_db_name(request.args.get("city"))
    #     else:
    #         return jsonify(common.falseReturn("", "没有传city参数"))
    #
    #     ret_array = []
    #     ret_map_values = ["待生产", "生产中", "已完成", "已出货", "已暂停"]
    #
    #     wait_for_producing_select_sql = ""
    #
    #     result = mysql.select_by_sql_with_long_time_cache(db_name, select_sql, need_col_name=True)
    #     status_list = result
    #     # status_list = []
    #     status_map = {}
    #
    #     return jsonify(common.trueReturn("", ""))
    #
    # # 返回某个客户的所有项目
    # @app.route('projects/customer', methods=['GET'])
    # def projects_customer():
    #     app.logger.info("projects_PUT_POST")
    #     app.logger.info("request: %s", request)
    #     app.logger.info("当前访问用户：%s", request.remote_addr)
    #     # app.logger.info("Authorization：", request.headers['Authorization'])
    #
    #     result = Auth.identify(Auth, request)
    #     # app.logger.info(result)
    #     app.logger.info("状态: %s 用户: %s ", result.get('status'), result.get('data'))
    #     if (result['status'] and result['data']):
    #         pass
    #     else:
    #         # return json.dumps(result, ensure_ascii=False)
    #         return jsonify(result)
    #
    #     if request.args.get("city"):
    #         db_name = CITY.get_db_name(request.args.get("city"))
    #     else:
    #         return jsonify(common.falseReturn("", "没有传city参数"))
    #
    #     ret_array = []
    #     ret_map_values = ["待生产", "生产中", "已完成", "已出货", "已暂停"]
    #
    #     wait_for_producing_select_sql = ""
    #
    #     result = mysql.select_by_sql_with_long_time_cache(db_name, select_sql, need_col_name=True)
    #     status_list = result
    #     # status_list = []
    #     status_map = {}
    #
    #     return jsonify(common.trueReturn("", ""))
    #
    #
    #
    #
    #
