import pymysql
import math
from App import common
from App import config
import datetime
#from App import app
#logger = app.logger
from App import logger
from App import long_time_cache
import collections
from flask import jsonify
#logger = common.global_obj["logger"]

#format_time_now = common.format_ymdhms_time_now()

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

def db_connect(db_name):
    db = pymysql.connect(config.DB_HOST, config.DB_USER, config.DB_PASSWORD, db_name)
    return db

# {"pinyin":"拼音"}
def get_col_name_map():
    col_name_map = {}
    db = db_connect("ws_doorplate")
    # 使用cursor()方法获取操作游标
    cursor = db.cursor()
    # 获取列名
    cursor.execute(
        " SELECT col_name, col_name_chinese FROM col_name_map ")
    results = cursor.fetchall()
    for i in results:
        col_name_map[i[0]] = i[1]
    return col_name_map

# ["pinyin", "拼音"]
def get_col_name_list():
    col_name_list = []
    db = db_connect("ws_doorplate")
    # 使用cursor()方法获取操作游标
    cursor = db.cursor()
    # 获取列名
    cursor.execute(
        " SELECT col_name, col_name_chinese FROM col_name_map ")
    results = cursor.fetchall()
    for i in results:
        col_name_list.append([i[0], i[1]])
    return col_name_list


def select_by_sql(db_name, sql, args=[], **kw):
    '''

    db: 数据库名
    table_name: 表名
    sql: 自己写好的sql

    kw: 可选
        need_transform: 把数据库传回的None值转成 空字符串""， 默认True 代表开启

    '''
    # db = pymysql.connect("localhost", "root", "root", "ws_doorplate")
    # db = pymysql.connect(config.DB_HOST, config.DB_USER, config.DB_PASSWORD, config.DB_NAME)

    # 使用cursor()方法获取操作游标
    db = db_connect(db_name)
    cursor = db.cursor()
    try:
        if args:
            cursor.execute(sql, args)
        else:
            cursor.execute(sql)
        results = cursor.fetchall()
    except:
        print(sql)
        print("select_by_sql查询出错，sql 语句有错误！")
        return [[]]
    db.close()
    print("select_by_sql 查询成功")
    if kw.get("need_transform") == False:
        if not results:
            return (())
        return [list(i) for i in results]
    else:
        #return [["" if not j and j != 0 else j for j in i] for i in results]
        if not results:
            return (())
        return [["" if j is None else j for j in i] for i in results]

@long_time_cache.memoize(timeout=config.cache_timeout)
def select_by_sql_with_long_time_cache(db_name, sql, args=[], **kw):
    '''
    select数据并长时间缓存
    db: 数据库名
    table_name: 表名
    sql: 自己写好的sql

    kw: 可选
        need_transform: 把数据库传回的None值转成 空字符串""， 默认True 代表开启
        need_col_name: 返回带列名的key的map的集合数组，即列名：值， 默认False, need_col_name与need_transform二选一的

    '''
    # db = pymysql.connect("localhost", "root", "root", "ws_doorplate")
    # db = pymysql.connect(config.DB_HOST, config.DB_USER, config.DB_PASSWORD, config.DB_NAME)

    # 使用cursor()方法获取操作游标
    db = db_connect(db_name)
    cursor = db.cursor()
    #print("sqlsqlsqlsql", sql)
    try:
        if args:
            cursor.execute(sql, args)
        else:
            cursor.execute(sql)
        col = cursor.description
        results = cursor.fetchall()
    except:
        print(sql)
        print("select_by_sql查询出错，sql 语句有错误！")
        return [[]]
    db.close()
    print("select_by_sql 查询成功")

    if kw.get("need_col_name") == True:
        temp_map = {}
        temp_list = []
        for i in results:
            for index, j in enumerate(i):
                temp_map[col[index][0]] = j
            temp_list.append(temp_map)
        ret = temp_list
    else:
        if kw.get("need_transform") == False:
            if not results:
                ret =  (())
            ret = [list(i) for i in results]
        else:
            #return [["" if not j and j != 0 else j for j in i] for i in results]
            if not results:
                ret = (())
            ret = [["" if j is None else j for j in i] for i in results]

    return ret


def select(db_name, sql, args=[], **kw):
    '''
    select数据
    db: 数据库名
    table_name: 表名
    sql: 自己写好的sql

    kw: 可选
        need_transform: 把数据库传回的None值转成 空字符串""， 默认True 代表开启
        need_col_name: 返回带列名的key的map的集合数组，即列名：值， 默认False, need_col_name与need_transform二选一的

    '''
    # db = pymysql.connect("localhost", "root", "root", "ws_doorplate")
    # db = pymysql.connect(config.DB_HOST, config.DB_USER, config.DB_PASSWORD, config.DB_NAME)

    # 使用cursor()方法获取操作游标
    db = db_connect(db_name)
    cursor = db.cursor()
    #print("sqlsqlsqlsql", sql)
    try:
        if args:
            cursor.execute(sql, args)
        else:
            cursor.execute(sql)
        col = cursor.description
        results = cursor.fetchall()
    except:
        print(sql)
        print("select_by_sql查询出错，sql 语句有错误！")
        return [[]]
    db.close()
    print("select_by_sql 查询成功")

    if kw.get("need_col_name") == True:
        temp_map = {}
        temp_list = []
        for i in results:
            for index, j in enumerate(i):
                temp_map[col[index][0]] = j
            temp_list.append(temp_map)
        ret = temp_list
    else:
        if kw.get("need_transform") == False:
            if not results:
                ret =  (())
            ret = [list(i) for i in results]
        else:
            #return [["" if not j and j != 0 else j for j in i] for i in results]
            if not results:
                ret = (())
            ret = [["" if j is None else j for j in i] for i in results]

    return ret


# 更新已经生成生产单的数据
def update_exported_produce(dbname, table_name, by_who="unknown", dp_id_list=[], global_id_list=[], need_connect=0, custom_addition=""):
    print('开始更新已经生成生产单的数据', ' 用户: ', by_who)
    print('表名', table_name)
    '''

    dbname: need_connect=0 为数据库连接后返回的对象 need_connect=1 时需要传dbname
    table_name: 表名
    cols: 列名
    dp_id_list: dp_id_list数组
    global_id_list: global_id_list数组
    注意： dp_id_list和global_id_list数组只能二选一
    
    custom_addition: 自定义附加在后面的条件

    '''
    # db = pymysql.connect("localhost", "root", "root", "ws_doorplate")
    # db = pymysql.connect(config.DB_HOST, config.DB_USER, config.DB_PASSWORD, config.DB_NAME)
    db = db_connect(dbname)
    # 使用cursor()方法获取操作游标
    cursor = db.cursor()



    sql_head = "UPDATE "+ table_name
    sql_cols = " SET `exported_produce`=`exported_produce`+1 " + \
                              ", `exported_produce_by` = " + "\'" + by_who + "\'" + \
                              ", `exported_produce_date` = " + "\'" + common.format_ymdhms_time_now() + "\'"

   # sql_where = " WHERE `global_id` IN (\'%s\') " % ('\',\''.join(list(global_id_and_date_map.keys())[head:tail]))
    where_name = 'dp_id'
    datas = dp_id_list
    if len(dp_id_list) > 0:
        where_name = 'dp_id'
        datas = dp_id_list
    elif len(global_id_list) > 0:
        where_name = 'global_id'
        datas = global_id_list
    step = 1000
    step_num = math.ceil(len(datas) / step)
    # done_count = 0
    for i in range(step_num):
        temp_data_list = []
        head = i * step
        if i == (step_num - 1):
            tail = len(datas)
        else:
            tail = (i + 1) * step
        sql_where = " WHERE `" + where_name + "` IN (\'%s\') " % ('\',\''.join(datas[head:tail]))
        sql = sql_head+sql_cols+sql_where
        #print(sql)
        try:
            cursor.execute(sql)
        except:
            print('Error! At %d/%d ' % (tail, len(datas)))
            return False
        print('%d/%d done' % (tail, len(datas)))
    db.commit()
    print('All done!')
    # 关闭数据库连接
    db.close()
    return True


# 更新安装照片相关
# 要是按global_id更新就传 global_id_far_list global_id_cls_list
# 按dp_id更新就传  dp_id_cls_list dp_id_far_list
def update_photos(db_name, table_name, **kw):
    print("Starting")
    db = pymysql.connect("192.168.1.100", "root", "root", db_name)
    # 使用cursor()方法获取操作游标
    cursor = db.cursor()
    # cursor.execute(
    #     " SELECT column_name FROM information_schema.columns WHERE table_schema=\'"+ db_name +"\' AND table_name=\'"+ table_name +"\'")
    # results = cursor.fetchall()
    # col_name_list = []
    # print(results)
    # for i in results:
    #     col_name_list.append(str(i[0]))
    #
    # print("列名：", col_name_list)
    # db.commit()

    # 更新的条件
    update_condition = ""
    update_photos_type = ""
    update_condition_list = []
    if not kw.get("picture_type"):
        print("mysql.py update_photos()  kw 没有 picture_type")
        return False
    else:
        picture_type = kw.get("picture_type")
    picture_type_by = ""
    if kw.get("picture_type_by"):
        picture_type_by = kw.get("picture_type_by")
    else:
        picture_type_by = ""
    mark_picture_type = 0
    if kw.get("mark_picture_type") == 1:
        mark_picture_type = kw.get("mark_picture_type")
    else:
        mark_picture_type = 0
    if kw.get("picture_type_date"):
        picture_type_date = kw.get("picture_type_date")
    else:
        picture_type_date = ""

    if kw.get('picture_type_photos_upload_by'):
        picture_type_photos_upload_by = kw.get('picture_type_photos_upload_by')
    else:
        picture_type_photos_upload_by = "未知"

    if kw.get("picture_type_photos_upload_date"):
        picture_type_photos_upload_date = kw.get("picture_type_photos_upload_date")
    else:
        picture_type_photos_upload_date = common.format_ymdhms_time_now()
    if kw.get("file_from"):
        file_from = kw.get("file_from")
    else:
        file_from = "没有填写"


    for k, v in kw.items():
        if k.find('list') >= 0:
            update_condition = k.split("_")[0] + "_" + k.split("_")[1]
            update_condition_list = v
        if k.find('cls') >= 0:
            # global_id_cls_list
            update_photos_type = 'installed_photos_cls'
            photos_type = "cls"
        elif k.find('far') >= 0:
            # dp_id_far_list
            # global_id_far_list
            update_photos_type = 'installed_photos_far'
            photos_type = "far"


    if picture_type == "collected":
        update_photos_type = "collected_photos"



    if not update_photos_type or not update_condition or not update_condition_list:
        print("更新到数据库失败")
        print("update_photos_type: ", update_photos_type)
        print("update_condition: ", update_condition)
        print("update_condition_list len: ", len(update_condition_list))
        return False

    print("总共要进行更新的数据：", len(update_condition_list))

    condition_sql = ""
    if picture_type_by:
        condition_sql += ", `{picture_type}_by`=\"" + picture_type_by + "\" "
        condition_sql = condition_sql.format(picture_type=picture_type)
    if mark_picture_type == 1:
        condition_sql += ", `{picture_type}`=`{picture_type}`+1 "
        condition_sql = condition_sql.format(picture_type=picture_type)
    if picture_type_date:
        try:
            picture_type_date = datetime.datetime.strptime(picture_type_date, "%Y-%m-%d")
            picture_type_date += +datetime.timedelta(hours=14)
            picture_type_date = picture_type_date.strftime("%Y-%m-%d %H:%M:%S")
        except:
            picture_type_date = datetime.datetime.strptime(picture_type_date, "%Y-%m-%d %H:%M:%S")

            picture_type_date = picture_type_date.strftime("%Y-%m-%d %H:%M:%S")
        condition_sql += ", `{picture_type}_date`=\"" + picture_type_date + "\" "
        condition_sql = condition_sql.format(picture_type=picture_type)
    else:
        picture_type_date = ""

    if picture_type == "collected":
        condition_sql += ", `{picture_type}_photos_upload_by`=\"{picture_type_photos_upload_by}\" " + \
                         ", `{picture_type}_photos_upload_date`=\"{picture_type_photos_upload_date}\" "

        condition_sql += ", `{picture_type}_photos_from`=\"{file_from}\" "

        condition_sql = condition_sql.format(picture_type=picture_type,
                                             picture_type_photos_upload_by=picture_type_photos_upload_by,
                                             picture_type_photos_upload_date=picture_type_photos_upload_date,
                                             file_from=file_from)

    else:


        condition_sql += ", `{picture_type}_photos_{photos_type}_upload_by`=\"{picture_type_photos_upload_by}\" " + \
                         ", `{picture_type}_photos_{photos_type}_upload_date`=\"{picture_type_photos_upload_date}\" "

        condition_sql += ", `{picture_type}_photos_{photos_type}_from`=\"{file_from}\" "



        condition_sql = condition_sql.format(picture_type=picture_type,
                                             photos_type=photos_type,
                                             picture_type_photos_upload_by=picture_type_photos_upload_by,
                                             picture_type_photos_upload_date=picture_type_photos_upload_date,
                                             file_from=file_from)

    print("picture_type_date", picture_type_date)

    #query_data_col = col_name_list.index(update_condition)  # 要检索的信息所在的列

    step = 10000  # 每次更新step个
    step_num = math.ceil(len(update_condition_list) / step)

    try:
        for i in range(step_num):
            head = i * step
            if i == (step_num - 1):
                tail = len(update_condition_list)
            else:
                tail = (i + 1) * step


            UPDATE_sql_head = "UPDATE " + table_name + " SET `"+ update_photos_type + "`=`"+ update_photos_type + "`+1 " + condition_sql + " WHERE `"+ update_condition + "` in (%s) " % (
                ','.join(['%s'] * len(update_condition_list[head:tail])))
            sql = UPDATE_sql_head
            print(sql)
            cursor.execute(sql, update_condition_list[head:tail])
            print('%d/%d done' % (tail, len(update_condition_list)))

    except:
        print("更新到数据库失败")
        return False


    db.commit()
    # 关闭数据库连接
    db.close()
    print("更新照片包成功")
    return True

# 更新照片MD5 待完善，目前未启用，
# 查看pictures_operation.py 的update_MD5_db() 方法，更好用
'''
    传 data_list
    依次为city、file_name、iden_id、MD5
'''
def insert_photos_MD5(db_name, table_name, **kw):
    print("Starting")
    db = pymysql.connect("192.168.1.100", "root", "root", db_name)
    # 使用cursor()方法获取操作游标
    cursor = db.cursor()
    if kw.get('data_list'):
        data_list = kw.get('data_list')
    else:
        data_list = []
    if kw.get('city'):
        city = kw.get('city')
    else:
        city = "未传城市参数city"
    data_need_update_list = data_list  # 需要更新的数组

    logger.info("[%s] city: %s, db: %s, table: %s, total update MD5 files: %s", common.format_ymdhms_time_now(), city,
                db_name, table_name, str(len(data_need_update_list)))

    step = 10000  # 每次更新step个
    step_num = math.ceil(len(data_need_update_list) / step)

    try:
        for i in range(step_num):
            head = i * step
            if i == (step_num - 1):
                tail = len(data_need_update_list)
            else:
                tail = (i + 1) * step
            insert_sql = ""
            insert_sql_head = " INSERT INTO `{table_name}`(`city`, `file_name`, `iden_id`, `MD5`) "
            insert_sql_head = insert_sql_head.format(table_name=table_name)
            insert_sql_body = " (\"{city}\", \"{file_name}\", \"{iden_id}\", \"{MD5}\") "
            temp_index = 0
            for city, file_name, iden_id, MD5 in data_need_update_list[head:tail]:
                if temp_index == 0:
                    insert_sql += insert_sql_head
                    insert_sql += " VALUES "
                else:
                    insert_sql += ", "
                insert_sql += insert_sql_body.format(city=city, file_name=file_name, iden_id=iden_id, MD5=MD5)
                temp_index += 1

            # logger.info("[%s] city: %s, db: %s, table: %s, sql: %s", common.format_ymdhms_time_now(), city,
            #             db_name, table_name, insert_sql)

            cursor.execute(insert_sql)

    except:
        print("更新到数据库失败")
        return False

    db.commit()
    db.close()
    return True

# # 更新生产数据，暂未启用
# def update_produced(db, table_name, cols, where_map={}, custom_addition=""):
#     '''
#
#     db: 数据库连接后返回的对象
#     table_name: 表名
#     cols: 列名
#     where_map: where条件
#     custom_addition: 自定义附加在后面的条件
#
#     '''
#     # db = pymysql.connect("localhost", "root", "root", "ws_doorplate")
#     # db = pymysql.connect(config.DB_HOST, config.DB_USER, config.DB_PASSWORD, config.DB_NAME)
#
#     # 使用cursor()方法获取操作游标
#     cursor = db.cursor()
#
#     sql_head = "UPDATE " + table_name
#     sql_cols = " SET `installed`=`installed`+1 " + \
#                ", `installed_by` = " + "\'" + i["sync_installed_by"] + "\'" + \
#                ", `installed_coordinate` = " + "\'" + i["sync_installed_coordinate"] + "\'"
#
# # 更新安装状态，暂未启用
# def update_installed(db, table_name, cols, where_map={}, custom_addition=""):
#     '''
#
#     db: 数据库连接后返回的对象
#     table_name: 表名
#     cols: 列名
#     where_map: where条件
#     custom_addition: 自定义附加在后面的条件
#
#     '''
#     # db = pymysql.connect("localhost", "root", "root", "ws_doorplate")
#     # db = pymysql.connect(config.DB_HOST, config.DB_USER, config.DB_PASSWORD, config.DB_NAME)
#
#     # 使用cursor()方法获取操作游标
#     cursor = db.cursor()
#
#
#
#     sql_head = "UPDATE "+ table_name
#     sql_cols = " SET `installed`=`installed`+1 " + \
#                               ", `installed_by` = " + "\'" + i["sync_installed_by"] + "\'" + \
#                               ", `installed_coordinate` = " + "\'" + i["sync_installed_coordinate"] + "\'"


# 城市模块
def get_city_name():
    city_name_list = []
    city_name_map = {}
    city_name_db_map = {}
    city_name_table_map = {}

    db = db_connect("ws_doorplate")
    # 使用cursor()方法获取操作游标
    cursor = db.cursor()

    # 获取列名
    cursor.execute(
        " SELECT `city`,`city_name_chinese`,`city_db`,`city_table` FROM cities ")
    results = cursor.fetchall()
    #logger.info(results)
    for i in results:
        city_name_list.append([str(i[0]), str(i[1])])
        city_name_map[str(i[0])] = str(i[1])
        city_name_db_map[str(i[0])] = str(i[2])
        city_name_table_map[str(i[0])] = str(i[3])
    db.close()
    return city_name_list, city_name_map, city_name_db_map, city_name_table_map

def insert_city(**kw):
    if kw.get("city"):
        city = kw.get("city")
    else:
        return False, [], {}
    if kw.get("city_name_chinese"):
        city_name_chinese = kw.get("city_name_chinese")
    else:
        return False, [], {}
    city_name_list = []
    city_name_map = {}

    table_name = city+"_dp"
    history_table_name = city+"_dp_history"

    db = db_connect("ws_doorplate")
    # 使用cursor()方法获取操作游标
    cursor = db.cursor()
    create_sql = " CREATE  TABLE IF NOT EXISTS {table_name} (LIKE dp_template) ".format(table_name=table_name)
    logger.info(create_sql)
    try:
        cursor.execute(create_sql)
        db.commit()
    except:
        logger.info("创建城市数据表失败")
    create_history_sql = " CREATE  TABLE IF NOT EXISTS {history_table_name} (LIKE dp_history_template) ".format(history_table_name=history_table_name)
    logger.info(create_history_sql)
    try:
        cursor.execute(create_history_sql)
        db.commit()
    except:
        logger.info("创建城市历史表失败")
    insert_sql = "INSERT INTO `ws_doorplate`.`cities`(`city`, `city_name_chinese`, `city_db`, `city_table`) VALUES ('{city}', '{city_name_chinese}', 'ws_doorplate', '{table_name}');"
    insert_sql = insert_sql.format(city=city, city_name_chinese=city_name_chinese, table_name=table_name)
    logger.info(insert_sql)
    try:
        cursor.execute(insert_sql)
        db.commit()
    except:
        logger.info("插入城市名称失败")
    city_name_list, city_name_map, city_name_db_map, city_name_table_map = get_city_name()
    db.close()
    return True, city_name_list, city_name_map




# 单条插入新数据
# data_map为插入字段名以及值例如{"global_id":"462EA0BB-8309-4E18-9D0A-666666666666"}
def insert_data(db_name, db_table_name, uploaded_by="没有填写", data_map={}):

    print("Starting insert data")

    if not db_name or not db_table_name or not data_map:
        return False, '插入失败，检查参数', common.format_ymdhms_time_now(), "1"


    print("插入的数据库", db_name)
    print("插入的表", db_table_name)


    db = pymysql.connect("192.168.1.100", "root", "root", db_name)
    # 使用cursor()方法获取操作游标
    cursor = db.cursor()
    select_col_sql = "SELECT column_name FROM information_schema.columns WHERE table_schema=" + "\"" + db_name + "\"" + " AND table_name=" + "\"" + db_table_name + "\""
    # print(select_col_sql)
    cursor.execute(select_col_sql)
    results = cursor.fetchall()
    col_name_list = []
    # print(results)
    for i in results:
        col_name_list.append(str(i[0]))

    # print("列名：", col_name_list)
    db.commit()

    cursor = db.cursor()

    data_map = collections.OrderedDict(data_map)

    print("要进行插入的数据：", data_map)

    try:

        sql = "INSERT INTO " + db_table_name + "(" + ",".join(list(data_map.keys())) + ")" + "VALUES" + "(\"" + "\",\"".join(
            [str(i) for i in list(data_map.values())]) + "\")"
        print("sqlsqlsql", sql)
        cursor.execute(sql)

    except:
        # 关闭数据库连接
        db.close()
        return False, '插入失败', '0', '0'


    db.commit()
    # 关闭数据库连接
    db.close()

    return True, '插入成功', common.format_ymdhms_time_now(), "1"


# 单条查询数据
# data_map为查询字段名以及值例如{"global_id":"462EA0BB-8309-4E18-9D0A-666666666666"}
def select_data(db_name, db_table_name, data_map={}, select_col=[]):

    print("Starting  select data")

    if not db_name or not db_table_name or not data_map:
        return False, '查询失败，检查参数', common.format_ymdhms_time_now(), "1"


    print("查询的数据库", db_name)
    print("查询的表", db_table_name)


    db = pymysql.connect("192.168.1.100", "root", "root", db_name)
    # 使用cursor()方法获取操作游标
    cursor = db.cursor()
    select_col_sql = "SELECT column_name FROM information_schema.columns WHERE table_schema=" + "\"" + db_name + "\"" + " AND table_name=" + "\"" + db_table_name + "\""
    # print(select_col_sql)
    cursor.execute(select_col_sql)
    results = cursor.fetchall()
    col_name_list = []
    # print(results)
    for i in results:
        col_name_list.append(str(i[0]))

    # print("列名：", col_name_list)
    db.commit()

    cursor = db.cursor()

    if not select_col:
        select_col_sql = " * "
    else:
        select_col_sql = "`" + "`,`".join(select_col) + "`"

    data_map = collections.OrderedDict(data_map)

    condition_sql = ""

    print("要进行查询的数据条件：", data_map)

    for key, value in data_map.items():
        if not condition_sql:
            condition_sql += " `" + key + "`=\"" + str(value) + "\""
        else:
            condition_sql += " AND `" + key + "`=\"" + str(value) + "\""



    try:

        sql = "SELECT " + select_col_sql + " FROM " + db_table_name + " WHERE " + condition_sql
        print("sqlsqlsql", sql)
        cursor.execute(sql)
        result = cursor.fetchall()

    except:
        # 关闭数据库连接
        db.close()
        return False, '查询失败', '0', (())


    # 关闭数据库连接
    db.close()

    return True, '查询成功', common.format_ymdhms_time_now(), result



# 单更新新数据
# data_map为更新字段名以及值例如{"global_id":"462EA0BB-8309-4E18-9D0A-666666666666"}
# data_select_map为要进行更新的选择条件，一般为{"index": xxx}
def update_data(db_name, db_table_name, updated_by="没有填写", data_map={}, data_select_map={}):

    print("Starting update data")

    if not db_name or not db_table_name or not data_map:
        return False, '更新失败，检查参数', common.format_ymdhms_time_now(), "1"


    print("更新的数据库", db_name)
    print("更新的表", db_table_name)


    db = pymysql.connect("192.168.1.100", "root", "root", db_name)
    # 使用cursor()方法获取操作游标
    cursor = db.cursor()
    select_col_sql = "SELECT column_name FROM information_schema.columns WHERE table_schema=" + "\"" + db_name + "\"" + " AND table_name=" + "\"" + db_table_name + "\""
    # print(select_col_sql)
    cursor.execute(select_col_sql)
    results = cursor.fetchall()
    col_name_list = []
    # print(results)
    for i in results:
        col_name_list.append(str(i[0]))

    # print("列名：", col_name_list)
    db.commit()

    cursor = db.cursor()

    data_map = collections.OrderedDict(data_map)

    print("要进行更新的数据：", data_map)
    print("要进行更新的数据是：", data_select_map)


    try:

        sql_head = "UPDATE " + db_table_name + " "
        sql_tail = ""
        for name, value in data_map.items():
            if not sql_tail:
                sql_tail = " SET " + "`" + name + "`=" + "\"" + str(value) + "\""
            else:
                sql_tail += ", " + "`" + name + "`=" + "\"" + str(value) + "\""

        condition_sql = ""
        for name, value in data_select_map.items():
            if not condition_sql:
                condition_sql = " WHERE " + "`" + name + "`=" + "\"" + str(value) + "\""
            else:
                condition_sql += " AND " + "`" + name + "`=" + "\"" + str(value) + "\""

        sql = sql_head + sql_tail + condition_sql
        print("sqlsqlsql", sql)

        cursor.execute(sql)

    except:
        # 关闭数据库连接
        db.close()
        return False, '更新失败', '0', '0'


    db.commit()
    # 关闭数据库连接
    db.close()

    return True, '更新成功', common.format_ymdhms_time_now(), "1"



# 插入api调用日志
'''
    传 data_list
    依次为city、file_name、iden_id、MD5
'''
def insert_photos_MD5(db_name, table_name, **kw):
    print("Starting")
    db = pymysql.connect("192.168.1.100", "root", "root", db_name)
    # 使用cursor()方法获取操作游标
    cursor = db.cursor()
    if kw.get('data_list'):
        data_list = kw.get('data_list')
    else:
        data_list = []
    if kw.get('city'):
        city = kw.get('city')
    else:
        city = "未传城市参数city"
    data_need_update_list = data_list  # 需要更新的数组

    logger.info("[%s] city: %s, db: %s, table: %s, total update MD5 files: %s", common.format_ymdhms_time_now(), city,
                db_name, table_name, str(len(data_need_update_list)))

    step = 10000  # 每次更新step个
    step_num = math.ceil(len(data_need_update_list) / step)

    try:
        for i in range(step_num):
            head = i * step
            if i == (step_num - 1):
                tail = len(data_need_update_list)
            else:
                tail = (i + 1) * step
            insert_sql = ""
            insert_sql_head = " INSERT INTO `{table_name}`(`city`, `file_name`, `iden_id`, `MD5`) "
            insert_sql_head = insert_sql_head.format(table_name=table_name)
            insert_sql_body = " (\"{city}\", \"{file_name}\", \"{iden_id}\", \"{MD5}\") "
            temp_index = 0
            for city, file_name, iden_id, MD5 in data_need_update_list[head:tail]:
                if temp_index == 0:
                    insert_sql += insert_sql_head
                    insert_sql += " VALUES "
                else:
                    insert_sql += ", "
                insert_sql += insert_sql_body.format(city=city, file_name=file_name, iden_id=iden_id, MD5=MD5)
                temp_index += 1

            # logger.info("[%s] city: %s, db: %s, table: %s, sql: %s", common.format_ymdhms_time_now(), city,
            #             db_name, table_name, insert_sql)

            cursor.execute(insert_sql)

    except:
        print("更新到数据库失败")
        return False

    db.commit()
    db.close()
    return True