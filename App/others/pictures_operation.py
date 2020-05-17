'''
created: 2019-07-18
author: Cong

remark:
    以后会陆续把一些关于图片处理的接口移动到这里
'''
import os
import pymysql
from werkzeug.utils import secure_filename
from App.others import files_operation
from App.datas.api import CITY
from App import logger
from App import common
from App import cache
from App import config
from flask import jsonify
from App.others import get_MD5 as get_MD5_class
import tempfile
import math

dydatas_basepath = config.DY_DATAS_PATH # 永久数据 默认路径

# 扫描指定文件夹的照片，并且返回所有照片的MD5 文件名 MD5 字典
def get_MD5_map(**kw):
    if kw.get("path"):
        files_list = files_operation.get_files_list(kw.get("path"))
    else:
        files_list = kw.get("files_list")
    MD5_map = {}

    for file in files_list:
        MD5_map[os.path.basename(file)] = files_operation.GetFileMd5(file)

    #MD5_list = list(set(MD5_list))

    return MD5_map

# 更新照片MD5数据库
# 如果MD5在数据库没有，就插入到数据库
# db_name 数据库名字
# table_name 表名字
# pictures_dir_path 照片文件目录
# picture_city 为空的话 更新所有城市
# files_list 为空的话，扫描照片文件夹目录pictures_dir_path，不为空则为要添加的照片MD5路径
# pictures_dir_path 和 files_list二者不能全为空
def update_MD5_db(db_name, table_name, pictures_dir_path="", picture_city="", files_list="", only_insert=False):

    total_update_list = []
    db = pymysql.connect("localhost", "root", "root", db_name)
    cursor = db.cursor()
    if not files_list and not pictures_dir_path:
        print("检查参数！pictures_dir_path和files_list不能同时为空！")
        return False, []
    if not picture_city:
        city_name_list = os.listdir(pictures_dir_path)
    else:
        city_name_list = [picture_city]
    for city in city_name_list:
        if not CITY.has_key(city):
            logger.info("该城市 %s 名字有误！", city)
            continue
        else:
            logger.info("城市 %s 开始更新照片MD5数据", city)

            if files_list:
                files_list = files_list
            else:
                files_list = files_operation.get_files_list(os.path.join(pictures_dir_path, city))
            city_table = CITY.get_table_name(city)
            if only_insert:
                # 直接插入，不需要检测file是否存在与数据库
                files_need_update_list = files_list
            else:
                select_sql = " SELECT `index`, `city`, `file_name`, `iden_id`, `MD5` FROM {table_name} WHERE `city`=\"{city}\" "
                select_sql = select_sql.format(table_name=table_name, city=city)

                logger.info("[%s] city: %s, db: %s, table: %s, sql: %s", common.format_ymdhms_time_now(), city, db_name,
                            table_name,
                            select_sql)

                cursor.execute(select_sql)
                col = cursor.description
                result = cursor.fetchall()
                col_name_list = [i[0] for i in col]

                files_need_update_list = [] # 需要更新的数组

                file_name_in_table_list = [] # 在数据库的照片名list
                iden_id_list = [] # 在数据库的iden_id list
                for i in result:
                    iden_id_list.append(i[col_name_list.index("iden_id")])
                    file_name_in_table_list.append(i[col_name_list.index("file_name")])

                for file in files_list:
                    file_name = os.path.basename(file)
                    if file_name not in file_name_in_table_list:
                        files_need_update_list.append(file)
                    # file_iden_id = file_name.split("_")[0]
                    # if file_iden_id not in iden_id_list:
                    #     files_need_update_list.append(file)
                total_update_list.extend(files_need_update_list)

            logger.info("[%s] city: %s, db: %s, table: %s, total update MD5 files: %s", common.format_ymdhms_time_now(), city,
                        db_name, table_name, str(len(files_need_update_list)))

            step = 10000  # 每次更新step个
            step_num = math.ceil(len(files_need_update_list) / step)

            try:
                for i in range(step_num):
                    head = i * step
                    if i == (step_num - 1):
                        tail = len(files_need_update_list)
                    else:
                        tail = (i + 1) * step
                    MD5_map = get_MD5_map(files_list=files_need_update_list[head:tail])  # 这是需要更新到数据的MD5 list
                    insert_sql = ""
                    insert_sql_head = " INSERT INTO `{table_name}`(`city`, `file_name`, `iden_id`, `MD5`) "
                    insert_sql_head = insert_sql_head.format(table_name=table_name)
                    insert_sql_body = " (\"{city}\", \"{file_name}\", \"{iden_id}\", \"{MD5}\") "
                    temp_index = 0
                    for file, MD5 in MD5_map.items():
                        if temp_index == 0:
                            insert_sql += insert_sql_head
                            insert_sql += " VALUES "
                        else:
                            insert_sql += ", "
                        iden_id = file.split("_")[0]
                        insert_sql += insert_sql_body.format(city=city, file_name=file, iden_id=iden_id, MD5=MD5)
                        temp_index += 1

                    # logger.info("[%s] city: %s, db: %s, table: %s, sql: %s", common.format_ymdhms_time_now(), city,
                    #             db_name, table_name, insert_sql)

                    cursor.execute(insert_sql)

            except:
                print("更新到数据库失败")
                return False, []

            db.commit()

            files_list = [] # 清一下 files

    db.close()
    return True, total_update_list

# 获取指定城市照片MD5
# db_name 数据库名字
# table_name 表名字
def get_MD5(db_name, table_name, city="", picture_batch_list=[], picture_MD5_batch_list=[]):

    db = pymysql.connect("localhost", "root", "root", db_name)
    cursor = db.cursor()

    if not city:
        select_sql = " SELECT `index`, `city`, `file_name`, `iden_id`, `MD5` FROM {table_name}  "
        select_sql = select_sql.format(table_name=table_name)
        city = "所有城市"
    else:
        select_sql = " SELECT `index`, `city`, `file_name`, `iden_id`, `MD5` FROM {table_name} WHERE `city`=\"{city}\" "
        select_sql = select_sql.format(table_name=table_name, city=city)

    batch_sql = " (\"{picture_batch_list}\") "
    if not picture_batch_list:
        pass
    else:
        batch_sql = batch_sql.format(picture_batch_list="\",\"".join(picture_batch_list))
        if select_sql.find("WHERE") >= 0:
            select_sql = select_sql + " AND `iden_id` in " + batch_sql
        else:
            select_sql = select_sql + " WHERE `iden_id` in " + batch_sql

    MD5_batch_sql = " (\"{picture_MD5_batch_list}\") "
    if not picture_MD5_batch_list:
        pass
    else:
        MD5_batch_sql = MD5_batch_sql.format(picture_MD5_batch_list="\",\"".join(picture_MD5_batch_list))
        if select_sql.find("WHERE") >= 0:
            select_sql = select_sql + " AND `MD5` in " + MD5_batch_sql
        else:
            select_sql = select_sql + " WHERE `MD5` in " + MD5_batch_sql


    logger.info("[%s] city: %s, db: %s, table: %s, sql: %s", common.format_ymdhms_time_now(), city, db_name, table_name,
                select_sql)

    cursor.execute(select_sql)
    col = cursor.description
    result = cursor.fetchall()
    col_name_list = [i[0] for i in col]
    file_MD5_map = {}
    for i in result:
        if not file_MD5_map.get(i[col_name_list.index("MD5")]):
            file_MD5_map[i[col_name_list.index("MD5")]] = [i[col_name_list.index("file_name")]]
        else:
            file_MD5_map[i[col_name_list.index("MD5")]].append(i[col_name_list.index("file_name")])
        #file_MD5_map[i[col_name_list.index("file_name")]] = i[col_name_list.index("MD5")]

    db.close()
    return True, file_MD5_map

# save_dir: "/xxx/xxx/xx/" 保存路径
# f: request.files['file']
# filename: 文件名
def upload_picture(save_dir, f, filename):
    logger.info("有照片要上传")
    # if city == "foshan":
    # 注意：没有的文件夹一定要先创建，不然会提示没有该路径
    filename = secure_filename(filename)
    filename_pre = filename.split('.')[0]
    select_col_data = filename.split('.')[0].split('_')[0]
    pictures_type = filename.split('.')[0].split('_')[1]
    filesuffix = filename.split('.')[1]

    sum = 0

    '''
    for root, dirs, files in os.walk(dydatas_basepath + '/gd_dp_photos/' + city):
        # app.logger.info('root_dir: %s', root)  # 当前目录路径
        # app.logger.info('sub_dirs: %s', dirs)  # 当前路径下所有子目录
        # app.logger.info('files: %s', files)  # 当前路径下所有非目录子文件
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
    # app.logger.info(tempfile)

    f.save(temp_file)

    temp_file.seek(0)
    upload_file_MD5 = get_MD5_class.GetFileMd5_from_file(temp_file)
    logger.info("upload_file_MD5 %s", upload_file_MD5)
    # 文件夹不存在时创建文件夹
    if not os.path.isdir(save_dir):
        os.makedirs(save_dir)

    filename = filename_pre + '.' + filesuffix
    while (os.path.isfile(os.path.join(save_dir, filename))):  # 入参需要是绝对路径
        # temp_MD5 = get_MD5.GetFileMd5(dydatas_basepath + '/gd_dp_photos/' + city + "/" + filename)
        temp_MD5 = get_MD5_class.GetFileMd5(os.path.join(save_dir, filename))
        logger.info("temp_MD5 %s", temp_MD5)
        if upload_file_MD5 != temp_MD5:
            sum += 1
            filename = filename_pre + "_" + str(sum) + '.' + filesuffix
        else:
            # fasle_type = existed 表示已经有该照片存在
            return False, os.path.join(save_dir, filename)

    # excel_name += '.xls'
    upload_path = os.path.join(save_dir, filename)
    f.stream.seek(0)
    f.save(upload_path)
    logger.info("文件保存在：%s", upload_path)


    return True, upload_path