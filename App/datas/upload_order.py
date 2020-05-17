'''
广州门牌上传订单，更新数据库数据
insert_datas(path, filename='未填写_未填写_未填写', contract_batch="没有填写", order_batch="没有填写", db_name='ws_doorplate', db_table_name='gz_orders_test')

'''
import os
import traceback
import logging
import pymysql
#import argparse
import xlrd
import xlwt
import math
import time
import copy
import re
import collections
import datetime
import App.common as  common
from App.datas import dp_sort
from App.mysql import mysql


# parser = argparse.ArgumentParser()
# parser.add_argument('--excel', help = "要检索的 excel 完整路径")
# parser.add_argument('--excels_folder', help = "要检索的 excels所在的目录 完整路径")
# args = parser.parse_args()
col_name_map = mysql.get_col_name_map()
# col_name_map = {
# 	'contract_batch': '合同批次',
# 	'order_batch': '订单批次',
# 	'from_filename': '来源文件',
# 	'distirct_id': '行政区号',
# 	'order_id': '订单号',
# 	'dp_id': '门牌id',
# 	'district': '行政区',
# 	'pcs': '派出所',
# 	'street': '街路巷',
# 	'dp_name': '门牌名称',
# 	'dp_num': '门牌号',
# 	'dp_num_trans': '门牌号纯数字',
# 	'dp_size': '门牌规格',
# 	'dp_nail_style': '钉挂方式',
# 	'producer': '烧制厂家',
# 	'produce_date': '烧制日期(格式YYYY-MM-DD)',
# 	'installer': '安装厂家',
# 	'factory_batch': '厂家批号',
# 	'factory_index': '厂家序号',
# 	'applicant': '申请人',
# 	'contact_number': '联系电话',
# 	'jump': '跳号说明',
# 	'fix': '补漏制作',
# 	'dp_type': '门牌类型',
# 	'global_id': '全球唯一码',
# 	'index': 'id',
# 	'global_id_with_dp_name': '全球唯一码带门牌名称'
# }

# col_name_map的key value反倒
col_name_map_reverse = {}
for key, value in col_name_map.items():
	col_name_map_reverse[value] = key
#print(col_name_map_reverse)

CN_NUM = {
    '〇' : 0, '一' : 1, '二' : 2, '三' : 3, '四' : 4, '五' : 5, '六' : 6, '七' : 7, '八' : 8, '九' : 9, '零' : 0,
    '壹' : 1, '贰' : 2, '叁' : 3, '肆' : 4, '伍' : 5, '陆' : 6, '柒' : 7, '捌' : 8, '玖' : 9, '貮' : 2, '两' : 2,
}
 
CN_UNIT = {
    '十' : 10,
    '拾' : 10,
    '百' : 100,
    '佰' : 100,
    '千' : 1000,
    '仟' : 1000,
    '万' : 10000,
    '萬' : 10000,
    '亿' : 100000000,
    '億' : 100000000,
    '兆' : 1000000000000,
}

'''
# "102号之5" -> 102-5
# "102号之五" -> 102-5
def chinese_to_arabic_with_connection(cn: str) -> str:
	unit = 0  # current
	ldig = []  # digest
	begin_index = -1
	end_index = -1
	index = 0
	index_map = {}
	for cndig in list(cn):
		if cndig in CN_UNIT or cndig in CN_NUM:
			if begin_index == end_index:
				begin_index = index
			end_index = index + 1
			if index==len(list(cn))-1:
				index_map[begin_index] = len(list(cn))
		elif begin_index!=end_index:
			end_index = index
			index_map[begin_index] = end_index
			begin_index = end_index
		index += 1


	need_cut = 0
	for key,value in index_map.items():
		#print(key, value)
		key = key - need_cut
		value = value - need_cut
		#print(key, value)
		unit = 0  # current
		ldig = []  # digest
		#temp_cn = copy.deepcopy(cn[key:value])
		temp_cn = cn[key:value]

		#print(temp_cn)

		for cndig in reversed(temp_cn):
			if cndig in CN_UNIT:
				unit = CN_UNIT.get(cndig)
				if unit == 10000 or unit == 100000000:
					ldig.append(unit)
					unit = 1
			elif cndig in CN_NUM:
				dig = CN_NUM.get(cndig)
				if unit:
					dig *= unit
					unit = 0
				ldig.append(dig)
		# else:
		# 	ldig.append(int(cndig))
		if unit == 10:
			ldig.append(10)
		val, tmp = 0, 0
		for x in reversed(ldig):
			if x == 10000 or x == 100000000:
				val += tmp * x
				tmp = 0
			else:
				tmp += x
		val += tmp
		#return val, begin_index, end_index

		#print(val)
		#print(cn[key:value])

		if key >=0:
			#i[1] = i[1].replace(i[1][begin:end], str(num))
			cn = cn.replace(cn[key:value], str(val), 1)
		#print (cn)
		
		if (value-key)!=len(str(val)):
			need_cut += (value-key) - len(str(val))

	#i[1] = '-'.join(re.findall(r"\d+\.?\d*",i[1]))
	
	return ('-'.join(re.findall(r"\d+\.?\d*", cn)))
'''
# "102号之5" -> 102-5
# "102号之五" -> 102-5
# version 2.0  "102号之一零一" -> 102-101
def chinese_to_arabic_with_connection(cn: str) -> str:

	has_CN_UNIT_sign = 0
	temp_cn = copy.deepcopy(cn)

	#print ("cn", cn)
	if not cn:
		return ""

	unit = 0  # current
	ldig = []  # digest
	begin_index = -1
	end_index = -1
	index = 0
	index_map = {}
	for cndig in list(cn):
		if cndig in CN_UNIT or cndig in CN_NUM:
			if begin_index == end_index:
				begin_index = index
			end_index = index + 1
			if index==len(list(cn))-1:
				index_map[begin_index] = len(list(cn))
		elif begin_index!=end_index:
			end_index = index
			index_map[begin_index] = end_index
			begin_index = end_index
		index += 1

	#print (cn)
	# print ("begin_index", begin_index)
	# print ("end_index", end_index)
	# print (index_map)

	need_cut = 0
	for key,value in index_map.items():
		#print(key, value)
		key = key - need_cut
		value = value - need_cut
		#print(key, value)
		unit = 0  # current
		ldig = []  # digest
		#temp_cn = copy.deepcopy(cn[key:value])
		temp_cn = cn[key:value]
		temp_cn_digit = ""
		for i, items in enumerate(list(temp_cn)):
			if items in CN_UNIT:
				temp_cn_digit
				temp_cn_digit = ""
				break
			if items in CN_NUM:
				temp_cn_digit += str(CN_NUM[items])
		if temp_cn_digit:
			temp_list_cn = list(cn)
			temp_index = 0
			for i in temp_cn_digit:
				temp_list_cn[key+temp_index] = i
				temp_index += 1
			cn = "".join(temp_list_cn)
			#print ("cn_step_temp", cn)

		else:
		#print(temp_cn)

			for cndig in reversed(temp_cn):
				if cndig in CN_UNIT:
					unit = CN_UNIT.get(cndig)
					if unit == 10000 or unit == 100000000:
						ldig.append(unit)
						unit = 1
				elif cndig in CN_NUM:
					dig = CN_NUM.get(cndig)
					if unit:
						dig *= unit
						unit = 0
					ldig.append(dig)
			# else:
			# 	ldig.append(int(cndig))
			if unit == 10:
				ldig.append(10)
			val, tmp = 0, 0
			for x in reversed(ldig):
				if x == 10000 or x == 100000000:
					val += tmp * x
					tmp = 0
				else:
					tmp += x
			val += tmp
			#return val, begin_index, end_index

			#print(val)
			#print(cn[key:value])

			if key >=0:
				#i[1] = i[1].replace(i[1][begin:end], str(num))
				cn = cn.replace(cn[key:value], str(val), 1)
			#print (cn)
			if (value-key)!=len(str(val)):
				need_cut += (value-key) - len(str(val))
	#i[1] = '-'.join(re.findall(r"\d+\.?\d*",i[1]))
	return ('-'.join(re.findall(r"\d+\.?\d*", cn)))

def test():
	for i in range(3, 0, -1):
		print("test will start in %d second"%(i))
		time.sleep(1)
	db = pymysql.connect("192.168.1.100", "root", "root", "ws_doorplate")
	# 使用cursor()方法获取操作游标
	cursor = db.cursor()
	#sql = "INSERT INTO fs_dp(produced) VALUES ('1')"
	sql = "UPDATE fs_dp SET produced=produced+1 WHERE global_id=\"462EA0BB-8309-4E18-9D0A-666666666666\""
	print(sql)
	cursor.execute(sql)
	# results = cursor.fetchall()

	db.commit() # commit之后，sql语句才真正执行
	db.close()
	print("test done")

# 从文件夹中读取所有excel文件路径
def load_excels_from_folder(dir):
    result = []#所有的文件
    for maindir, subdir, file_name_list in os.walk(dir):

        #print("1:",maindir) #当前主目录
        #print("2:",subdir) #当前主目录下的所有目录
        #print("3:",file_name_list)  #当前主目录下的所有文件

        for filename in file_name_list:
            apath = os.path.join(maindir, filename)#合并成一个完整路径
            result.append(apath)
    return result

# 判断全球唯一码有没有空
def global_id_has_NULL(dir_path):
	workbook = xlrd.open_workbook(dir_path)
	sheet_names = workbook.sheet_names()

	status = True # True代表没有为空的

	for sheet_name in sheet_names:
		# print(sheet_name)
		sheet = workbook.sheet_by_name(sheet_name)
		global_id_col_map = {}
		# global_id_col = -1
		# title_col_map = {}
		title_col_map = collections.OrderedDict()  # 这样的话 字典的keys会按添加的顺序排序

		# 读取标题
		for c in range(sheet.ncols):
			# print(sheet.row_values(r))
			if (sheet.cell(1, c).ctype) > 0 and (sheet.cell(1, c).ctype) < 5:
				# 单元格为string类型 0 empty,1 string, 2 number, 3 date, 4 boolean, 5 error
				title_col_map[col_name_map_reverse.get(sheet.cell_value(1, c))] = c

		if "global_id" not in title_col_map.keys():
			status = False
			return status
		else:
			if sheet.nrows <= 2:
				status = False
				return status
			c = title_col_map.get("global_id")
			for r in range(2, sheet.nrows):
				if (sheet.cell(r, c).ctype) <= 0 or (sheet.cell(r, c).ctype) >= 5:
					status = False
					return status
				if (sheet.cell(1, c).ctype) == 1:
					if sheet.cell_value(1, c) == "":
						status = False
						return status

	return status


# 读取excel文件	
def load_Excel(dir_path):
	#print("Loading excel")
	#print (dir_path)


	workbook = xlrd.open_workbook(dir_path)
	sheet_names = workbook.sheet_names()
	datas = []



	for sheet_name in sheet_names:
		#print(sheet_name)
		sheet = workbook.sheet_by_name(sheet_name)
		global_id_col_map = {}
		#global_id_col = -1
		#title_col_map = {}
		title_col_map = collections.OrderedDict() # 这样的话 字典的keys会按添加的顺序排序

		# 读取标题
		for c in range(sheet.ncols):
			#print(sheet.row_values(r))
			if (sheet.cell(1,c).ctype) > 0 and (sheet.cell(1,c).ctype) < 5:
			# 单元格为string类型 0 empty,1 string, 2 number, 3 date, 4 boolean, 5 error
				title_col_map[col_name_map_reverse.get(sheet.cell_value(1,c))] = c

		#print(title_col_map)

		for r in range(2, sheet.nrows):
			temp_datas = []
			for c in range(sheet.ncols):
				if "global_id_with_dp_name" in title_col_map.keys() and c == title_col_map.get("global_id_with_dp_name"):
					if (sheet.cell(r,c).ctype) > 0 and (sheet.cell(r,c).ctype) < 5:
						temp_datas.append(str(sheet.cell_value(r,c)))
					else:
						if "global_id" in title_col_map.keys() and "dp_name" in title_col_map.keys():
							temp_datas.append(str(sheet.cell_value(r, title_col_map.get("global_id"))) + str(sheet.cell_value(r, title_col_map.get("dp_name"))))
						else:
							temp_datas.append("")

				else:
					if (sheet.cell(r,c).ctype) > 0 and (sheet.cell(r,c).ctype) < 5:
						temp_datas.append(str(sheet.cell_value(r,c)))
					else:
						temp_datas.append("")
			datas.append(temp_datas)
			#print (len(temp_datas))

	#print (datas)
	print ("数据一共", len(datas))

	#print("("+ ",".join(["%s"] * len(title_col_map.keys())) +")")
	return datas, title_col_map

		

# 从路径中读取所有excels的所有数据
def load_all_datas_from_folders(dir):
	all_files = load_excels_from_folder(dir)
	all_global_id_list = []
	count = 0
	xls_num_count = 0
	xls_now = 1
	for path in all_files:
		#print (path)
		if path.find('.xls') >= 0:
			xls_num_count += 1
	print ('Loading excels: ')
	test_sum = 0
	for path in all_files:
		#print (path)

		if path.find('.xls') >= 0:
			#print(path)
			global_id = load_Excel(path)
			# for i in global_id:
			# 	if i=='C0DD57F9-0DFB-4CA9-868C-A5A4894D91DB':
			# 		print(path)
			# 	if i=='C187922A-9209-411B-808F-3DE9D76A34FD':
			# 		print(path)
			# 	if i=='D98D547A-B29B-4230-954A-521CF37992CE':
			# 		print(path)
			# 	if i=='B8411FCA-A5EE-4AA7-8751-C4F78358AEC8':
			# 		print(path)
			# 	if i=='6E29F59A-2600-47D8-9645-0C4F06995FCB':
			# 		print(path)
			# 	if i=='全球唯一码':
			# 		#print(path)
			# 		test_sum += 1
			# 	if i=='二维码':
			# 		#print(path)
			# 		test_sum += 1
			# 	if i>='规格':
			# 		#print(i)
			# 		test_sum += 1
			all_global_id_list.extend(global_id)
			count += len(all_global_id_list)
		print ('已完成', xls_now, '/', xls_num_count)
		xls_now += 1
	print ('All excels loaded!')	
			# print (len(dp_id))
			# print (len(global_id))
			# print (count)
			# print (len(all_dp_id_list))
			# print (len(all_global_id_list))
			#print(all_dp_id_list)
	print ('全球唯一码总数：' , len(all_global_id_list))
	#print ('test_sum：' , test_sum)
	return all_global_id_list

def move():
	print("Starting")
	db = pymysql.connect("192.168.1.100", "root", "root", "ws_doorplate")
	# 使用cursor()方法获取操作游标
	cursor = db.cursor()
	#cursor.execute(" SELECT column_name FROM information_schema.columns WHERE table_schema='ws_doorplate' AND table_name='gz_orders' ")
	cursor.execute(" SELECT dp_id, order_id, global_id FROM gz_orders ")
	datas = cursor.fetchall()
	db.commit()

	sql_head = "INSERT INTO dp_status(dp_id, order_id, global_id) VALUES "


	step = 10000
	step_num = math.ceil(len(datas) / step)
	#done_count = 0
	for i in range(step_num):
		temp_data_list = []
		head = i * step
		if i == (step_num - 1):
			tail = len(datas)
		else:
			tail = (i + 1) * step
		for j in datas[head:tail]:
			temp = ''
			temp = '(' + ','.join(["\'%s\'", "\'%s\'", "\'%s\'"]) + ')'
			pass_this = 0
			temp_j = list(j)
			#print (temp_j[2])
			if temp_j[2] is None:
				pass_this = 1
			#print (temp)
			if pass_this == 0:
				temp = (temp % tuple(temp_j))
				temp_data_list.append(temp)

		sql = sql_head + ','.join(temp_data_list)
		cursor.execute(sql)
		print ('%d/%d done' % ((int(i)+1)*step, len(datas)))
		db.commit()

	db.close()


# 单条插入新数据
# data_map为插入字段名以及值例如{"global_id":"462EA0BB-8309-4E18-9D0A-666666666666"}
# def insert_data(filename='未填写_未填写_未填写', contract_batch="没有填写", order_batch="没有填写", db_name='ws_doorplate',
# 				 db_table_name='gz_orders_test', uploaded_by="没有填写", data_map={}):
def insert_data(filename='未填写_未填写_未填写', projects_index=-1, db_name='ws_doorplate',
				 				 db_table_name='gz_orders_test', uploaded_by="没有填写", data_map={}):
	# def update_datas(path):
	print("Starting insert data")

	# if not contract_batch:
	# 	contract_batch = "没有填写"
	# if not order_batch:
	# 	order_batch = "没有填写"
	if not filename:
		filename = '未填写_未填写_未填写'

	if projects_index == -1:
		return False, '插入失败, 没有传入projects_index', '0', '0'

	print("文件名", filename)
	print("插入的数据库", db_name)
	print("插入的表", db_table_name)
	print("项目id", projects_index)
	# print("合同批号", contract_batch)
	# print("订单批号", order_batch)

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
	select_col_name_sql = " SELECT col_name, col_name_chinese FROM col_name_map "

	cursor.execute(select_col_name_sql)
	col_name_tuple = cursor.fetchall()

	global col_name_map, col_name_map_reverse
	# 从数据库拉取最新col name 字典表 然后更新到col_name_map，col_name_map_reverse

	for i, j in col_name_tuple:
		col_name_map[i] = j
		col_name_map_reverse[j] = i

	from_filename = filename

	distirct_id = filename.split("_")[0]
	order_id = filename.split("_")[1]

	#如果有门牌号，则生成门牌号纯数字
	if data_map.get("dp_num") and not data_map.get("dp_num_trans"):
		data_map["dp_num_trans"] = dp_sort.chinese_to_arabic_with_connection(data_map.get("dp_num"))

	data_map = collections.OrderedDict(data_map)



	#print("要进行插入的数据：", data_map)
	print("要进行插入的数据数量：", len(data_map))
	uploaded_date = common.format_ymdhms_time_now()
	# other_datas = [contract_batch, order_batch, from_filename, distirct_id, order_id, uploaded_by, uploaded_date]
	#
	# other_col = ["contract_batch", "order_batch", "from_filename", "distirct_id", "order_id", "uploaded_by",
	# 			 "uploaded_date"]

	if "projects_index" in data_map.keys():
		other_datas = [from_filename, distirct_id, order_id, uploaded_by, uploaded_date]
		other_col = ["from_filename", "distirct_id", "order_id", "uploaded_by",
					 "uploaded_date"]
	else:
		other_datas = [projects_index, from_filename, distirct_id, order_id, uploaded_by, uploaded_date]
		other_col = ["projects_index", "from_filename", "distirct_id", "order_id", "uploaded_by",
					 "uploaded_date"]


	sql = "INSERT INTO " + db_table_name + "(" + ",".join(list(data_map.keys())) + "," + ",".join(
		other_col) + ")" + "VALUES" + "(\"" + "\",\"".join(
		[str(i) for i in list(data_map.values())] + [str(i) for i in other_datas]) + "\")"
	cursor.execute(sql)
	'''
	try:

		sql = "INSERT INTO " + db_table_name + "(" + ",".join(list(data_map.keys())) + "," + ",".join(
			other_col) + ")" + "VALUES" + "(\"" + "\",\"".join([str(i) for i in list(data_map.values())]+other_datas) + "\")"
		cursor.execute(sql)

	except:
		# 关闭数据库连接
		db.close()
		return False, '更新失败', '0', '0'
	'''

	db.commit()
	# 关闭数据库连接
	db.close()

	return True, '更新成功', common.format_ymdhms_time_now(), "1"

# 批量插入新数据
def insert_datas(path, filename='未填写_未填写_未填写', projects_index=-1, db_name='ws_doorplate', db_table_name='gz_orders_test', uploaded_by="没有填写"):
	#def update_datas(path):
	print("Starting insert datas")


	if projects_index==-1:
		return False, '插入失败, 没有传入projects_index', '0', '0'
	if not filename:
		filename = '未填写_未填写_未填写'

	print("文件名", filename)
	print("插入的数据库", db_name)
	print("插入的表", db_table_name)
	print("项目id", projects_index)



	db = pymysql.connect("192.168.1.100", "root", "root", db_name)
	# 使用cursor()方法获取操作游标
	cursor = db.cursor()
	select_col_sql = "SELECT column_name FROM information_schema.columns WHERE table_schema=" + "\"" + db_name + "\"" + " AND table_name=" + "\"" + db_table_name + "\""
	#print(select_col_sql)
	cursor.execute(select_col_sql)
	results = cursor.fetchall()
	col_name_list = []
	#print(results)
	for i in results:
		col_name_list.append(str(i[0]))

	#print("列名：", col_name_list)
	db.commit()

	cursor = db.cursor()
	select_col_name_sql = " SELECT col_name, col_name_chinese FROM col_name_map "

	cursor.execute(select_col_name_sql)
	col_name_tuple = cursor.fetchall()


	global col_name_map, col_name_map_reverse
	# 从数据库拉取最新col name 字典表 然后更新到col_name_map，col_name_map_reverse

	for i,j in col_name_tuple:
		col_name_map[i] = j
		col_name_map_reverse[j] = i


	from_filename = filename

	try:

		distirct_id = filename.split("_")[0]

	except:
		distirct_id = "未能从文件名提取"
	try:
		order_id = filename.split("_")[1]
	except:
		order_id = "未能从文件名提取"

	# 读取数据
	datas, title_col_map = load_Excel(path)

	print ("总共要进行插入的数据：", len(datas))
	uploaded_date = common.format_ymdhms_time_now()

	if "projects_index" in title_col_map.keys():
		other_datas = [from_filename, distirct_id, order_id, uploaded_by, uploaded_date]
		# other_col = ["from_filename", "distirct_id", "order_id", "uploaded_by",
		# 			 "uploaded_date", "dp_num_trans", "global_id_with_dp_name"]
		other_col = ["from_filename", "distirct_id", "order_id", "uploaded_by",
					 "uploaded_date"]
	else:
		other_datas = [projects_index, from_filename, distirct_id, order_id, uploaded_by, uploaded_date]
		# other_col = ["projects_index", "from_filename", "distirct_id", "order_id", "uploaded_by",
		# 			 "uploaded_date", "dp_num_trans", "global_id_with_dp_name"]
		other_col = ["projects_index", "from_filename", "distirct_id", "order_id", "uploaded_by",
					 "uploaded_date"]


	if db_table_name == "gz_orders": # 为广州单独加的
		if "producer" not in title_col_map.keys():
			other_col.append("producer")
			other_datas.append("广州市伟圣实业有限公司")

		if "produce_date" not in title_col_map.keys():
			other_col.append("produce_date")
			other_datas.append((datetime.datetime.now() + datetime.timedelta(days=10)).strftime('%Y-%m-%d')) # 在当前时间上+10天

		if "installer" not in title_col_map.keys():
			other_col.append("installer")
			other_datas.append("广州市伟圣实业有限公司")

		if "factory_index" not in title_col_map.keys():
			other_col.append("factory_index")
			# other_datas.append("广州市伟圣实业有限公司")
			select_order_batch_sql = "SELECT order_batch FROM projects WHERE `index`={projects_index}"
			select_order_batch_sql = select_order_batch_sql.format(projects_index=projects_index)

			cursor.execute(select_order_batch_sql)
			order_batch = cursor.fetchall()
			if not order_batch:
				order_batch = "未知"
			else:
				order_batch = order_batch[0][0]
			other_datas.append(order_batch)

		if "factory_batch" not in title_col_map.keys():
			other_col.append("factory_batch")
			#other_datas.append("广州市伟圣实业有限公司")
			select_max_factory_batch_sql = "SELECT max(cast(SUBSTRING_INDEX(t1.s1,\"-\",-1) as SIGNED INTEGER)) from (SELECT DISTINCT(factory_batch) as s1 FROM gz_orders  WHERE factory_batch LIKE \"%{doorplates_type}%\") t1;"
			if not order_batch:
				doorplates_type = "NONE"
			else:
				if order_batch[0] == "L":
					doorplates_type = "LSMP"
				else:
					doorplates_type = "ZSMP"
			select_max_factory_batch_sql = select_max_factory_batch_sql.format(doorplates_type=doorplates_type)

			cursor.execute(select_max_factory_batch_sql)
			factory_batch_num_max = cursor.fetchall()
			if not factory_batch_num_max:
				factory_batch_num_max = str(1)
			else:
				factory_batch_num_max = int(factory_batch_num_max[0][0])
				factory_batch_num_max = str(factory_batch_num_max + 1)
			other_datas.append("WS-GZ-" + doorplates_type + "-" + factory_batch_num_max)

	if "dp_num_trans" not in title_col_map.keys():
		other_col.append("dp_num_trans")

	if "global_id_with_dp_name" not in title_col_map.keys():
		other_col.append("global_id_with_dp_name")



	# other_datas = [projects_index, from_filename, distirct_id, order_id, uploaded_by, uploaded_date]
	other_datas = [str(i) for i in other_datas]
	# other_col = ["projects_index", "from_filename", "distirct_id", "order_id", "uploaded_by", "uploaded_date", "dp_num_trans", "global_id_with_dp_name", ]

	#datas = ["(\""+ "\",\"".join(i) +"\")" for i in datas]



	step = 1000 # 每次更新step个
	step_num = math.ceil(len(datas) / step)




	try:

		for i in range(step_num):
			head = i * step
			if i == (step_num - 1):
				tail = len(datas)
			else:
				tail = (i + 1) * step


			if "global_id_with_dp_name" not in title_col_map.keys():
				temp_datas = ["(\""+ "\",\"".join(i + other_datas + [chinese_to_arabic_with_connection(i[title_col_map["dp_num"]])] + [i[title_col_map["global_id"]]+i[title_col_map["dp_name"]]]) +"\")" for i in datas[head:tail]]
			else:
				if "dp_num_trans" not in title_col_map.keys():
					temp_datas = ["(\"" + "\",\"".join(
						i + other_datas + [chinese_to_arabic_with_connection(i[title_col_map["dp_num"]])]) + "\")" for i in datas[head:tail]]
				else:
					temp_datas = ["(\"" + "\",\"".join(
						i + other_datas) + "\")" for i
								  in datas[head:tail]]
			#print(temp_datas)
			sql = "INSERT INTO "+ db_table_name + "(" + ",".join(list(title_col_map.keys())) + "," + ",".join(other_col) +")" + " VALUES " + ",".join(temp_datas)
			#print (sql)
			#UPDATE_sql_head = "UPDATE fs_dp SET produced=produced+1 WHERE global_id in (%s) " % (','.join(['%s'] * len(global_id_list[head:tail])))
			#sql = UPDATE_sql_head
			#cursor.execute(sql, global_id_list[head:tail])
			cursor.execute(sql)
			print ('%d/%d done' % (tail, len(datas)))

	except:
		# 关闭数据库连接
		db.close()
		print("INSERT INTO "+ db_table_name + "(" + ",".join(list(title_col_map.keys())) + "," + ",".join(other_col) +")" + " VALUES " + temp_datas[0])
		return False, '插入失败', '0', '0'

	# for i in range(step_num):
	# 	head = i * step
	# 	if i == (step_num - 1):
	# 		tail = len(datas)
	# 	else:
	# 		tail = (i + 1) * step
	#
	# 	temp_datas = ["(\""+ "\",\"".join(i + other_datas + [chinese_to_arabic_with_connection(i[title_col_map["dp_num"]])] + [i[title_col_map["global_id"]]+i[title_col_map["dp_name"]]]) +"\")" for i in datas[head:tail]]
	# 	#print(temp_datas)
	# 	sql = "INSERT INTO "+ db_table_name + "(" + ",".join(list(title_col_map.keys())) + "," + ",".join(other_col) +")" + "VALUES" + ",".join(temp_datas)
	# 	#print (sql)
	# 	#UPDATE_sql_head = "UPDATE fs_dp SET produced=produced+1 WHERE global_id in (%s) " % (','.join(['%s'] * len(global_id_list[head:tail])))
	# 	#sql = UPDATE_sql_head
	# 	#cursor.execute(sql, global_id_list[head:tail])
	# 	cursor.execute(sql)
	# 	print ('%d/%d done' % (tail, len(datas)))


	# if sql:
	# 	try:
	# 		# 执行sql语句
	# 		#print(sql)
			
	# 		cursor.execute(sql, query_data)
	# 		#print (query_data)
	# 		print ("excel的数据有：%d个， 检索出来的有：%d个， 其中是空的有： %d个，" % (len(query_data), len(results), empty))
	# 		print("这些数据不在数据库", empty_list)

	# 		results = cursor.fetchall()
			
	# 		# 提交到数据库执行
	# 		db.commit()
	# 	except pymysql.ProgrammingError as error:
	# 		code, message = error.args
	# 		print(">>>>>>>>>>>>>", code, message)
	# 		logging.error('SQL执行失败，执行语句为:%s'%str(sql))

	# 		traceback.print_exc()
	# 		# 如果发生错误则回滚
	# 		db.rollback()
	# 		#db.undo()
	# 		pass

	db.commit()
	
	# 获取更新时间
	select_date_sql = "SELECT MAX(last_update_date) FROM " + db_table_name + " WHERE global_id=" + "\'" + datas[0][title_col_map["global_id"]] + "\'"
	#print(select_date_sql)
	#print(select_col_sql)
	cursor.execute(select_date_sql)
	update_date = cursor.fetchall()[0][0]

	# 关闭数据库连接
	db.close()



	return True, '更新成功', update_date.strftime('%Y-%m-%d %H:%M:%S'), str(len(datas))



if __name__ == '__main__':
	pass
	#query(args.excel)
	#all_files = load_excels_from_folder(args.excels_folder)
	#print(all_files)
	#global_id_list = load_all_datas_from_folders(args.excels_folder)
	# print (len(global_id_list))
	#print(global_id_list)
	# global_id_set = set(global_id_list)
	# print ('去除重复后', len(global_id_set))

	#load_Excel(args.excel)

	#update_datas(args.excels_folder)
	#move()
	#insert_datas(args.excel)

	#test()
