'''
此py文件包含文件操作的一些封装函数
目前有：
1. 计算MD5
2. 将文件打包成zip函数
3. zip路径 -> 解压到指定路径
5. 用MD5判断文件名是否存在
6. 上传文件保存在指定目录
7. 判断文件路径是否存在，并返回可以保存的路径
8. 判断路径是否存在，并返回可以保存的路径
9. 创建指定路径的所有文件夹
10. 给出指定路径的所有文件列表
'''
import zipfile
import App.config as config
from App import common
import os
import hashlib
import os
import datetime
import tempfile
from App.common import global_obj




'''
1. 计算MD5
filename 为路径
'''
# coding=gbk
def GetFileMd5(filename):
    #print(filename)
    if not os.path.isfile(filename):
        #print("文件不存在")
        return
    myhash = hashlib.md5()
    f = open(filename, 'rb')
    #print(f)
    #print(type(f))
    while True:
        b = f.read(8096)
        if not b :
            break
        myhash.update(b)
    f.close()
    return myhash.hexdigest()

# f is an _io.Buffered* object
# f为一个object
def GetFileMd5_from_file(f):

    myhash = hashlib.md5()

    while True:
        b = f.read(8096)
        if not b:
            break
        myhash.update(b)
    return myhash.hexdigest()


'''
2. 文件路径数组 -> zip
'''
def files_to_zip(filepath_list):
    #print(filepath_list)
    #print("len(filepath_list)",len(filepath_list))

    try:
        sum = 0
        zip_path = os.path.join(config.TEMP_DOWNLOAD_DATAS_PATH, "打包照片_" + common.format_ymdhms_time_now_for_filename() + ".zip")
        while(os.path.isfile(zip_path)):
            sum += 1
            zip_path = os.path.join(config.TEMP_DOWNLOAD_DATAS_PATH, "打包照片_" + common.format_ymdhms_time_now_for_filename() + "_" + str(sum) + ".zip")

        zipf = zipfile.ZipFile(zip_path, 'w')

        for file in filepath_list:
            #print(file)
            zipf.write(file)
        zipf.close()

        return zip_path

    except:
        return ""


'''
3. zip路径 -> 解压到指定路径
zip_path -> des_path
kw:
    namelist = 1 # 只需要 文件名列表
    members = [] # 要解压的文件名列表
return:
    files_name_list # 压缩包文件列表
    saved_files_name_list  # 有保存到本地的文件名
    not_saved_files_name_list # 没有保存到本地的文件名
    need_check_files_name_list # 待检查的文件名
'''
def zip_to_files(zip_path, des_path, *args, **kw):
    logger = global_obj.get("logger")


    if not zip_path or not des_path:
        print("zip_path 或 des_path为空")
        return False, []

    if not os.path.isdir(des_path):
        print("没有此路径", des_path)
        return False, []

    files_name_list = []
    if kw.get('namelist') == 1:
        zipf = zipfile.ZipFile(zip_path)
        files_name_list = zipf.namelist()
        return True, files_name_list

    if kw.get("picture_type"):
        picture_type = kw.get("picture_type")
    else:
        picture_type = "installed"
        print("files_operation.py zip_to_files() 没有传入picture_type 默认照片类型 ", picture_type)
    print("解压包照片类型: ", picture_type)

    save = 1

    if kw.get('need_save') == 0:
        save = kw.get('need_save')

    members = []
    if kw.get("members"):
        members = kw.get("members")
    print("members", members)
    #try:
    zipf = zipfile.ZipFile(zip_path)
    files_name_list = zipf.namelist()
    print("要解压的文件是: ", zip_path, "共有: ", len(files_name_list), "文件(包括文件夹等所有文件数量)")
    print("解压到的路径是: ", des_path)
    sum = 0
    saved_files_name_list = [] # 有保存到本地的文件名
    not_saved_files_name_list = []  # 没有保存到本地的文件名
    #zipf.extractall(des_path)  # 将所有文件解压到 test_unzip_path 目录下
    if kw.get('city'):
        city = kw.get('city')
    else:
        city = ""
    for name in members:
        (dir_temp, file_name) = os.path.split(name)
        raw_file_name = file_name
        if not file_name:
            continue
        if city == "guangzhou":
            if file_name.find("_cj01") >= 0:
                pass
            else:
                file_name_prefix, file_name_postfix = os.path.splitext(file_name)
                file_name = file_name_prefix + "_cj01" + file_name_postfix
        temp_f = zipf.read(name)
        need_save, full_path = is_file_with_MD5(temp_f, os.path.join(des_path, file_name))
        if not need_save:
            not_saved_files_name_list.append(raw_file_name)
            continue
        if save == 1:
            f_handle = open(full_path, "wb")
            f_handle.write(temp_f)
            f_handle.close()
        else:
            pass
        saved_files_name_list.append(raw_file_name)
        sum += 1
    zipf.close()
    print("共有: ", str(sum), "个文件成功保存在", des_path)
    logger.info("saved_files_name_list: %s \n not_saved_files_name_list: %s", saved_files_name_list, not_saved_files_name_list)
    logger.info("saved_files_name_list_len: %s \n not_saved_files_name_list_len: %s", str(len(saved_files_name_list)), str(len(not_saved_files_name_list)))

    return True, files_name_list, saved_files_name_list, not_saved_files_name_list
    # except:
    #     print("解压出错！")
    #     return False, []

'''
 荒废的函数
:param str:
:return: 1/0
目前是每天一个log文件
'''
def write_str_to_log(str):

    try:
        log_file_path = os.path.join(config.DY_DATAS_LOG_PATH, "all_running_log" + "_" + common.format_ymd_time_now_for_filename() + ".txt")
        with open(log_file_path, 'a+') as f:
            f.write('----------\n')
            temp_str = common.format_ymdhms_time_now_for_filename() + ": " + str
            f.write(temp_str)
            # f.write('\n----------')
            f.write('\n')
            # f.write(update_date)
        return 1
    except:
        return 0


'''
5. 用MD5判断文件名是否存在

return:
    need_save: 1为需要保存，0为不需要
    save_path: 保存的路径
'''
def is_file_with_MD5(f, path):
    need_save = 1

    # 如果path路径的文件不存在，直接保存即可
    if not os.path.isfile(path):
        if type(f) == bytes:
            # 如果f是字节流的处理方式
            return need_save, path
        else:
            #f.stream.seek(0)
            return need_save, path

    temp_file = tempfile.TemporaryFile()
    if type(f) == bytes:
        # 如果f是字节流的处理方式
        temp_file.write(f)
        temp_file.seek(0)
    else:
        # 如果f是file类
        #print("type", type(f))
        f.save(temp_file)
        temp_file.seek(0)

    #f = open(path, 'rb')
    upload_file_MD5 = GetFileMd5_from_file(temp_file)
    #print("file_MD5", upload_file_MD5)
    (temp_dir, temp_file_name) = os.path.split(path)
    filename_pre, filesuffix = os.path.splitext(temp_file_name)
    filesuffix = filesuffix[1:]
    filename = filename_pre + '.' + filesuffix
    sum = 0
    while (os.path.isfile(os.path.join(temp_dir, filename))):  # 入参需要是绝对路径
        # temp_MD5 = get_MD5.GetFileMd5(dydatas_basepath + '/gd_dp_photos/' + city + "/" + filename)
        temp_MD5 = GetFileMd5(os.path.join(temp_dir, filename))
        #print("temp_MD5", temp_MD5)
        if upload_file_MD5 != temp_MD5:
            sum += 1
            filename = filename_pre + "_" + str(sum) + '.' + filesuffix
        else:
            print("文件没有保存，本地已经有MD5相同的文件：", filename)
            need_save = 0
            return need_save, os.path.join(temp_dir, filename)

    # excel_name += '.xls'
    save_path = os.path.join(temp_dir, filename)

    print("文件需要保存在：", save_path)
    # f.stream.seek(0)
    # f.save(upload_path)

    if type(f)==bytes:
        pass
    else:
        f.stream.seek(0)
    return need_save, save_path


'''
6. 上传文件，保存在本地
f = request.files['file']
'''
def upload_file(f, des_path, file_name):

    temp_path = os.path.join(des_path, file_name)
    need_save, upload_path = is_file_with_MD5(f, temp_path)

    if need_save:
        f.save(upload_path)
        print("文件保存在：", upload_path)
        return upload_path
    else:
        return upload_path

'''
7. 判断文件路径是否存在，并返回可以保存的路径
    input:
        args:
            path = 文件路径
    return:
        是否存在，以及可以保存的路径
'''
def is_file(path):
    if not os.path.isfile(path):
        return True, path
    folder_path, file_name = os.path.split(path)
    file_name_prefix, file_name_postfix = os.path.splitext(file_name)
    sum = 0

    while(os.path.isfile(os.path.join(folder_path, file_name))):
        sum += 1
        file_name_prefix, file_name_postfix = os.path.splitext(file_name)
        file_name = file_name_prefix + "_" + str(sum) + file_name_postfix
    if sum > 1:
        #return os.path.join(folder_path, file_name)
        return True, os.path.join(folder_path, file_name)
    else:
        #return os.path.join(folder_path, file_name)
        return False, os.path.join(folder_path, file_name)

'''
8. 判断路径是否存在，并返回可以保存的路径
    input:
        args:
            path = 路径，也可以带文件名
    return:
        是否存在
'''
def is_dir(path):
    path = os.path.dirname(path) # 先去掉文件名, 得到文件名可以用 os.path.basename(path)
    return os.path.isdir(path)

'''
9. 创建指定路径的所有文件夹
    input:
        args:
            path = 路径
    return:
        创建完的路径
'''
def make_dirs(path):
    path = os.path.dirname(path)  # 先去掉文件名
    if not os.path.isdir(path):
        os.makedirs(path)
    return path

'''
10. 给出指定路径的所有文件列表
'''

def get_files_list(path):
    files_list = []
    for root, dirs, files in os.walk(path):
        #print('root_dir:', root)  # 当前目录路径
        #print('sub_dirs:', dirs)  # 当前路径下所有子目录
        #print('files:', files)  # 当前路径下所有非目录子文件
        for file in files:
            files_list.append(os.path.join(root, file))
    return files_list

