import os
import traceback
import logging
import pymysql
import argparse
import xlrd
import xlwt
import App.datas.dp_sort as dp_sort
from App.datas import excel as ExcelModel
from App import config
from App import cache

from App.mysql import mysql
import datetime
import types


# 读取excel文件	
def load_Excel(dir_path, **kw):
	print("Loading order excel")

	workbook = xlrd.open_workbook(dir_path)
	sheet_names = workbook.sheet_names()
	if kw.get("city"):
		city = kw.get("city")
	else:
		city = "guangzhou"
	if city == "guangzhou":
		doorplates_id_list = []
		doorplates_name_list = []
		police_name_list = []
		global_id_list = []

		for sheet_name in sheet_names:
			#print(sheet_name)
			sheet = workbook.sheet_by_name(sheet_name)
			doorplates_id_col = -1
			doorplates_name_col = -1
			police_name_col = -1
			global_id_col = -1
			for r in range(sheet.nrows):
				for c in range(sheet.ncols):
					#print(sheet.row_values(r))
					if (sheet.cell(r,c).ctype == 1): # 单元格为string类型 0 empty,1 string, 2 number, 3 date, 4 boolean, 5 error
						if sheet.cell_value(r,c).lower().find("门牌id") >= 0:
							doorplates_id_col = c
						if sheet.cell_value(r,c) == "门牌名称":
							doorplates_name_col = c
						if sheet.cell_value(r,c).find("派出所") >= 0:
							police_name_col = c
						if sheet.cell_value(r,c) == "全球唯一码":
							global_id_col = c

			for r in range(sheet.nrows):
				if r == 0:
					continue
				if doorplates_id_col >=0:
					if (sheet.cell(r,doorplates_id_col).ctype) > 0:
						if (sheet.cell(r,doorplates_id_col).ctype) == 2:
							cell_string = sheet.cell_value(r, doorplates_id_col)
							#doorplates_id_list.append(str(int(cell_string)))
							doorplates_id_list.append(str(int(cell_string)))
						else:
							cell_string = sheet.cell_value(r, doorplates_id_col)
							doorplates_id_list.append(str(cell_string))
				if doorplates_name_col >= 0:
					if (sheet.cell(r,doorplates_name_col).ctype) > 0:
						if (sheet.cell(r,doorplates_name_col).ctype) == 2:
							cell_string = sheet.cell_value(r, doorplates_name_col)
							doorplates_name_list.append(str(int(cell_string)))
						else:
							cell_string = sheet.cell_value(r, doorplates_name_col)
							doorplates_name_list.append(str(cell_string))
				if global_id_col >= 0:
					if (sheet.cell(r,global_id_col).ctype) > 0:
						if (sheet.cell(r,global_id_col).ctype) == 2:
							cell_string = sheet.cell_value(r, global_id_col)
							global_id_list.append(str(int(cell_string)))
						else:
							cell_string = sheet.cell_value(r, global_id_col)
							global_id_list.append(str(cell_string))

				# if (sheet.cell(r,doorplates_name_col).ctype) > 0:
				# 	if (sheet.cell(r,doorplates_name_col).ctype) == 2:
				# 		cell_string = sheet.cell_value(r, doorplates_name_col)
				# 		police_name_list.append(str(int(cell_string)))
				# 	else:
				# 		cell_string = sheet.cell_value(r, doorplates_name_col)
				# 		police_name_list.append(str(cell_string))

		return doorplates_id_list, doorplates_name_list, global_id_list

	else:
		try:
			col_name = kw.get("col_name")
		except:
			col_name = "global_id"
		query_list = query.load_Excel_for_special(dir_path, col_name=col_name)
		return query_list

'''
	query
	*args:
	*kw:
		db_name: str  表示连接的db名字
		db_table_name: str 表示要操作的表名字
		col_name_needed_list: 要生成的列
'''
def query(path, col_name_needed_list = ['pcs', 'community', 'street', 'dp_num', 'dp_num_trans', 'dp_name', 'dp_id',  \
                                        'global_id_with_dp_name', 'dp_type', 'dp_size', 'global_id'], *args, **kw):
	print("Starting")
	#db = pymysql.connect("127.168.1.100", "root", "root", "ws_doorplate")
	if kw.get("city"):
		city = kw.get("city")
	else:
		city = "guangzhou"
	if kw.get("db_name"):
		db_name = kw.get("db_name")
	else:
		db_name = "ws_doorplate"
	if kw.get("db_table_name"):
		db_table_name = kw.get("db_table_name")
	else:
		db_table_name = "gz_orders"

	db = pymysql.connect("localhost", "root", "root", db_name)

	print("citycitycity", city)
	# 使用cursor()方法获取操作游标
	cursor = db.cursor()
	cursor.execute(" SELECT column_name FROM information_schema.columns WHERE table_schema=\'" + db_name + "\' AND table_name=\'" + db_table_name + "\' ")
	results = cursor.fetchall()
	col_name_list = []
	#print(results)
	for i in results:
		col_name_list.append(str(i[0]))

	#if not city == "foshan" and not city == "maoming":
	# 做排序用
	village_col = col_name_list.index('pcs')
	road_col = col_name_list.index('street')
	doorplate_col = col_name_list.index('dp_num_trans')
	#doorplate_col = col_name_list.index('dp_num')
	#print(village_col)
	#print(road_col)
	#print(doorplate_col)

	#print("列名：", col_name_list)
	db.commit()

	col_name_projects_list = ["contract_batch", "order_batch", "order_id"]
	col_name_need_list = []
	col_name_need_pure_list = []
	for i in col_name_list:
		if i not in col_name_projects_list:
			col_name_need_pure_list.append(i)
			col_name_need_list.append(db_table_name + ".`" + i + "`")
		else:
			pass

	col_name_final_list = col_name_projects_list + col_name_need_pure_list

	sql_head = " SELECT  t1.`contract_batch`, t1.`order_batch`, t1.`order_id`, " + ",".join(
		col_name_need_list) + " FROM {table_name} "
	sql_head = sql_head.format(table_name=db_table_name)

	projects_sql = " INNER JOIN " \
				   "(SELECT projects.`index`, projects.`contract_batch`, projects.`order_batch`, projects.`order_id` FROM projects " \
				   ") t1 on t1.`index` = {table_name}.`projects_index` "
	projects_sql = projects_sql.format(table_name=db_table_name)


	if not kw.get("index_list"): # 如果没有index_list 则默认是读取excel
		print("no index_list, loading excel")
		doorplates_id_list, doorplates_name_list, global_id_list = load_Excel(path)
		if not doorplates_name_list and not doorplates_id_list and not global_id_list:
			new_excel = xlwt.Workbook()  # 新建excel
			mySheet = new_excel.add_sheet("sheet1")  # 添加工作表名
			temp_str = '上传文件有问题'
			mySheet.write(0, 0, temp_str)
			# 保存
			new_excel.save(path + "error_query.xls")
			return [], path + "error_query.xls"
		# return [], ""



		# 优先用门牌id进行检索，其次全球唯一码，再其次门牌名称
		#print ("global_id_listglobal_id_listglobal_id_list", global_id_list)
		if len(doorplates_id_list) > 0 and not city == "foshan" and not city == "maoming":
			# print ("总共要检索的：", len(doorplates_id_list))
			# SELECT_sql = "SELECT * FROM " + db_table_name + " WHERE dp_id in (%s) " % (
			# 	','.join(['%s'] * len(doorplates_id_list)))
			SELECT_sql = sql_head + projects_sql + " WHERE {table_name}.`dp_id` in (%s) " % (
				 	','.join(['%s'] * len(doorplates_id_list)))
			SELECT_sql = SELECT_sql.format(table_name=db_table_name)
			query_data_col = col_name_final_list.index('dp_id')  # 要检索的信息所在的列
			if 'dp_id' not in col_name_needed_list:
				col_name_needed_list.append('dp_id')
			if col_name_needed_list:
				query_data_in_needed_col = col_name_needed_list.index('dp_id')  # 要检索的信息所在的列
			query_data = doorplates_id_list
		elif len(global_id_list) > 0:
			# print ("总共要检索的：", len(doorplates_name_list))
			# SELECT_sql = "SELECT * FROM " + db_table_name + " WHERE global_id in (%s) " % (
			# 	','.join(['%s'] * len(global_id_list)))
			SELECT_sql = sql_head + projects_sql + " WHERE {table_name}.`global_id` in (%s) " % (
				','.join(['%s'] * len(global_id_list)))
			SELECT_sql = SELECT_sql.format(table_name=db_table_name)
			#print("SELECT_sqlSELECT_sqlSELECT_sql", SELECT_sql)
			query_data_col = col_name_final_list.index('global_id')  # 要检索的信息所在的列
			if 'global_id' not in col_name_needed_list:
				col_name_needed_list.append('global_id')
			if col_name_needed_list:
				query_data_in_needed_col = col_name_needed_list.index('global_id')  # 要检索的信息所在的列
			query_data = global_id_list
		elif len(doorplates_name_list) > 0:
			# print ("总共要检索的：", len(doorplates_name_list))
			# SELECT_sql = "SELECT * FROM " + db_table_name + " WHERE dp_name in (%s) " % (
			# 	','.join(['%s'] * len(doorplates_name_list)))
			SELECT_sql = sql_head + projects_sql + " WHERE {table_name}.`dp_name` in (%s) " % (
				','.join(['%s'] * len(doorplates_name_list)))
			SELECT_sql = SELECT_sql.format(table_name=db_table_name)
			query_data_col = col_name_final_list.index('dp_name')  # 要检索的信息所在的列
			if 'dp_name' not in col_name_needed_list:
				col_name_needed_list.append('dp_name')
			if col_name_needed_list:
				query_data_in_needed_col = col_name_needed_list.index('dp_name')  # 要检索的信息所在的列
			query_data = doorplates_name_list

		'''
		else:
			doorplate_col = col_name_list.index('DZMC')
			col_name = kw.get("col_name")
			query_list = load_Excel_for_special(path, col_name=col_name)

			# if "dp_id" in col_name_needed_list:
			# 	col_name_needed_list.remove("dp_id")
			# if "dp_name" in col_name_needed_list:
			# 	col_name_needed_list.remove("dp_name")
			# if "dp_type" in col_name_needed_list:
			# 	col_name_needed_list.remove("dp_type")

			if not query_list:
				new_excel = xlwt.Workbook()  # 新建excel
				mySheet = new_excel.add_sheet("sheet1")  # 添加工作表名
				temp_str = '上传文件有问题'
				mySheet.write(0, 0, temp_str)
				# 保存
				new_excel.save(path + "error_query.xls")
				return [], path + "error_query.xls"
			# return [], ""

			# 优先用全球唯一码进行检索
			if len(query_list) > 0:
				# print ("总共要检索的：", len(doorplates_id_list))
				SELECT_sql = "SELECT * FROM " + db_table_name + " WHERE global_id in (%s) " % (
					','.join(['%s'] * len(query_list)))
				query_data_col = col_name_list.index('global_id')  # 要检索的信息所在的列
				if 'global_id' not in col_name_needed_list:
					col_name_needed_list.append('global_id')
				if col_name_needed_list:
					query_data_in_needed_col = col_name_needed_list.index('global_id')  # 要检索的信息所在的列
				query_data = query_list
		'''
	else:
		print("loading index_list")
		doorplates_index_list = kw.get("index_list")
		# print ("总共要检索的：", len(doorplates_index_list))
		# SELECT_sql = "SELECT * FROM " + db_table_name + " WHERE `index` in (%s) " % (
		# 	','.join(['%s'] * len(doorplates_index_list)))
		SELECT_sql = sql_head + projects_sql + " WHERE {table_name}.`index` in (%s) " % (
			','.join(['%s'] * len(doorplates_index_list)))
		SELECT_sql = SELECT_sql.format(table_name=db_table_name)
		query_data_col = col_name_final_list.index('index')  # 要检索的信息所在的列
		if 'index' not in col_name_needed_list:
			col_name_needed_list.append('index')
		if col_name_needed_list:
			query_data_in_needed_col = col_name_needed_list.index('index')  # 要检索的信息所在的列
		query_data = doorplates_index_list



	sql = SELECT_sql

	print("sqlsqlsqlsql", sql)

	if sql:
		try:
			# 执行sql语句
			#print(sql)
			
			cursor.execute(sql, query_data)
			#print (query_data)

			results = cursor.fetchall()
			#print (results)
			print (len(results))

			#results = list(results)

			if city == "guangzhou":
				results = dp_sort.sort(list(results), village_col, road_col, doorplate_col)
			else:
				results = dp_sort.sort_by_dp(list(results), doorplate_col)


			# filepath, filename, fullpath = ExcelModel.datas_to_excel(results, col_name_list=col_name,
			# 														 path=path,
			# 														 excel_name="all_datas_of_query.xls")

			new_excel = xlwt.Workbook() # 新建excel
			mySheet = new_excel.add_sheet("查询结果") # 添加工作表名
			# 写入每一列的列名
			i = 0

			col_name_map = mysql.get_col_name_map()

			if not col_name_needed_list:
				for col_name in col_name_final_list:
					mySheet.write(0, i, col_name_map.get(col_name))
					i += 1
				col_name_needed_list_index = list(range(len(col_name_final_list)))
			else:
				for col_name in col_name_needed_list:
					mySheet.write(0, i, col_name_map.get(col_name))
					i += 1
				col_name_needed_list_index = []
				#print(col_name_needed_list_index)
				for col_name in col_name_needed_list:
					col_name_needed_list_index.append(col_name_final_list.index(col_name))
				#print(col_name_needed_list_index)

			# 从第1行开始写入数据
			# row_num = 1
			# for i in results:
			# 	col_num = 0
			# 	for j in i:
			# 		mySheet.write(row_num, col_num, j)
			# 		col_num += 1
			# 	row_num += 1
			#print(col_name_needed_list_index)
			row_num = 1
			for i in results:
				col_num = 0
				for j in col_name_needed_list_index:
					#print(i[j])
					mySheet.write(row_num, col_num, i[j])
					col_num += 1
				row_num += 1


			query_data_col_from_results = []
			for i in results:
				query_data_col_from_results.append(i[query_data_col])

			empty = 0
			empty_list = []
			for index, i in enumerate(query_data):
				if i not in query_data_col_from_results:
					empty += 1
					#empty_list.append([index,i])
					empty_list.append(i)

			empty_list.sort()
			#empty_list.sort(key= lambda i: i[1])
			temp_str = "上传的数据有" + str(len(query_data)) + "个。" + "一共查到" + str(len(results)) + "个数据。" + "一共有" + str(len(empty_list)) + "个查不到。" + '下面是查询不到的数据（如果为空，则表示全部查到了）'

			mySheet.write(row_num, 0, temp_str)
			row_num += 1


			if not col_name_needed_list:
				#for index, i in empty_list:
				for i in empty_list:
					#mySheet.write(row_num, query_data_col, i)
					mySheet.write(row_num, query_data_col, i)
					mySheet.write(row_num, 0, "查不到")
					#mySheet.write(row_num, query_data_col+1, "查不到的数据应该在查询文件的第"+str(index)+'行左右')
					row_num += 1
			else:
				#for index, i in empty_list:
				for i in empty_list:
					#mySheet.write(row_num, query_data_col, i)
					mySheet.write(row_num, query_data_in_needed_col, i)
					mySheet.write(row_num, 0, "查不到")
					#mySheet.write(row_num, query_data_in_needed_col + 1, "查不到的数据应该在查询文件的第" + str(index) + '行左右')
					row_num += 1



			# 查询结果统计和查不到的结果表
			mySheet = new_excel.add_sheet("查询结果统计以及查不到的数据")  # 添加工作表名
			row_num = 0 # 新表 从0开始

			mySheet.write(row_num, 0, temp_str)
			row_num += 1


			if not col_name_needed_list:
				#for index, i in empty_list:
				for i in empty_list:
					#mySheet.write(row_num, query_data_col, i)
					mySheet.write(row_num, query_data_col, i)
					mySheet.write(row_num, 0, "查不到")
					#mySheet.write(row_num, query_data_col+1, "查不到的数据应该在查询文件的第"+str(index)+'行左右')
					row_num += 1
			else:
				#for index, i in empty_list:
				for i in empty_list:
					#mySheet.write(row_num, query_data_col, i)
					mySheet.write(row_num, query_data_in_needed_col, i)
					mySheet.write(row_num, 0, "查不到")
					#mySheet.write(row_num, query_data_in_needed_col + 1, "查不到的数据应该在查询文件的第" + str(index) + '行左右')
					row_num += 1



			# 保存
			new_excel.save(path + "all_datas_of_query.xls")

			print ("excel的数据有：%d个， 检索出来的有：%d个， 其中是空的有： %d个，" % (len(query_data), len(results), empty))
			print(path + "all_datas_of_query.xls")
			#print("这些数据不在数据库", empty_list)

			# 提交到数据库执行
			db.commit()
		except pymysql.ProgrammingError as error:
			code, message = error.args
			print(">>>>>>>>>>>>>", code, message)
			logging.error('SQL执行失败，执行语句为:%s'%str(sql))

			traceback.print_exc()
			# 如果发生错误则回滚
			db.rollback()
			#db.undo()
			pass

		
	# 关闭数据库连接
	db.close()

	# 把数据转成map字典
	results = [list([list(i) for i in results])]
	results_map_list = []
	for i in results[0]:
		col = 0
		temp_map = {}
		for j in i:

			if isinstance(j, datetime.datetime):
				if not j:
					print(datetime.datetime.strptime('2000-01-01 00:00:00', '%Y-%m-%d %H:%M:%S'))
				else:
					temp_map[col_name_final_list[col]] = j.strftime('%Y-%m-%d %H:%M:%S')
			else:
				temp_map[col_name_final_list[col]] = j
			col += 1
		results_map_list.append(temp_map)

	for i in col_name_final_list:
		col = 0
		temp_map = {}
		for j in col_name_final_list:
			if j == 'index':
				temp_map[j] = '数据库中没有此数据，检查检索的条件'
			else:
				temp_map[j] = ''
			col += 1
		temp_map[col_name_final_list[query_data_col]] = i
		results_map_list.append(temp_map)
	#print(results_map_list)

	# results 为列表，results[0]是检索数据的列表，results[1]是检索不到数据的（查询数据）列表
	return results_map_list, path + "all_datas_of_query.xls"


# 读取excel文件
# 读取指定列
# col_name 为读取的excel指定列
def load_Excel_for_special(dir_path, *args, **kw):
	print("Loading order excel")

	workbook = xlrd.open_workbook(dir_path)
	sheet_names = workbook.sheet_names()
	query_list = []

	#print("kw.get('col_name')", kw.get('col_name'))
	if kw.get('col_name'):
		query = kw.get('col_name')
	else:
		query = "全球唯一码"

	for sheet_name in sheet_names:
		# print(sheet_name)
		sheet = workbook.sheet_by_name(sheet_name)
		query_col = -1
		for r in range(sheet.nrows):
			for c in range(sheet.ncols):
				# print(sheet.row_values(r))
				if (sheet.cell(r, c).ctype == 1):  # 单元格为string类型 0 empty,1 string, 2 number, 3 date, 4 boolean, 5 error
					# print("sheet.cell_value(r, c)", sheet.cell_value(r, c))
					if sheet.cell_value(r, c).lower().find(query) >= 0:
						query_col = c


		for r in range(sheet.nrows):
			if r == 0:
				continue
			if query_col >= 0:
				if (sheet.cell(r, query_col).ctype) > 0:
					if (sheet.cell(r, query_col).ctype) == 2:
						cell_string = sheet.cell_value(r, query_col)
						# doorplates_id_list.append(str(int(cell_string)))
						query_list.append(str(int(cell_string)))
					else:
						cell_string = sheet.cell_value(r, query_col)
						query_list.append(str(cell_string))

	return query_list


'''
	query
	*args:
	*kw:
		db_name: str  表示连接的db名字
		db_table_name: str 表示要操作的表名字
		col_name_needed_list: 要生成的列
		col_name: 为指定的要读取的excel的列名
		col_name_in_db: 为对应数据库的字段名
'''


def query_from_special(path, col_name_needed_list=['pcs', 'street', 'dp_num', 'dp_num_trans', 'dp_name', 'dp_id', \
									  'global_id_with_dp_name', 'dp_type', 'dp_size', 'global_id',
									  'col_name_needed_list'], *args, **kw):
	print("Starting")
	# db = pymysql.connect("127.168.1.100", "root", "root", "ws_doorplate")
	if not kw:
		db_name = "ws_doorplate"
		db_table_name = "gz_orders"
	else:
		try:
			db_name = kw.get("db_name")
			db_table_name = kw.get("db_table_name")
			col_name = kw.get("col_name")
			col_name_in_db = kw.get("col_name_in_db")
		except:
			db_name = "ws_doorplate"
			db_table_name = "gz_orders"
			col_name = "门牌id"
			col_name_in_db = "dp_id"


	db = pymysql.connect("localhost", "root", "root", db_name)
	# 使用cursor()方法获取操作游标
	cursor = db.cursor()
	cursor.execute(
		" SELECT column_name FROM information_schema.columns WHERE table_schema='ws_doorplate' AND table_name='gz_orders' ")
	results = cursor.fetchall()
	col_name_list = []
	# print(results)
	for i in results:
		col_name_list.append(str(i[0]))

	# 做排序用
	village_col = col_name_list.index('pcs')
	road_col = col_name_list.index('street')
	# doorplate_col = col_name_list.index('dp_num')
	try:
		doorplate_col = col_name_list.index('dp_num_trans')
	except:
		doorplate_col = col_name_list.index('dp_num')
	# print(village_col)
	# print(road_col)
	# print(doorplate_col)

	# print("列名：", col_name_list)
	db.commit()

	query_list = load_Excel_for_special(path, col_name=col_name)

	if not query_list:
		new_excel = xlwt.Workbook()  # 新建excel
		mySheet = new_excel.add_sheet("sheet1")  # 添加工作表名
		temp_str = '上传文件有问题，或者参数传入不正确！'
		mySheet.write(0, 0, temp_str)
		# 保存
		new_excel.save(path + "error_query.xls")
		return [], path + "error_query.xls"
	# return [], ""

	# 优先用门牌id进行检索

	# print (doorplates_id_list)

	if len(query_list) > 0:
		# print ("总共要检索的：", len(doorplates_id_list))
		SELECT_sql = "SELECT * FROM " + db_table_name + " WHERE " + col_name_in_db + " in (%s) " % (
			','.join(['%s'] * len(query_list)))
		query_data_col = col_name_list.index(col_name_in_db)  # 要检索的信息所在的列
		if col_name_in_db not in col_name_needed_list:
			col_name_needed_list.append(col_name_in_db)
		if col_name_needed_list:
			query_data_in_needed_col = col_name_needed_list.index(col_name_in_db)  # 要检索的信息所在的列
		query_data = query_list


	sql = SELECT_sql

	if sql:
		try:
			# 执行sql语句
			# print(sql)

			cursor.execute(sql, query_data)
			# print (query_data)

			results = cursor.fetchall()
			# print (results)
			print(len(results))
			# results = list(results)

			results = dp_sort.sort(list(results), village_col, road_col, doorplate_col)

			# filepath, filename, fullpath = ExcelModel.datas_to_excel(results, col_name_list=col_name,
			# 														 path=path,
			# 														 excel_name="all_datas_of_query.xls")

			new_excel = xlwt.Workbook()  # 新建excel
			mySheet = new_excel.add_sheet("查询结果")  # 添加工作表名
			# 写入每一列的列名
			i = 0

			if not col_name_needed_list:
				for col_name in col_name_list:
					mySheet.write(0, i, ExcelModel.col_name_map.get(col_name))
					i += 1
				col_name_needed_list_index = list(range(len(col_name_list)))
			else:
				for col_name in col_name_needed_list:
					mySheet.write(0, i, ExcelModel.col_name_map.get(col_name))
					i += 1
				col_name_needed_list_index = []
				# print(col_name_needed_list_index)
				for col_name in col_name_needed_list:
					col_name_needed_list_index.append(col_name_list.index(col_name))

			row_num = 1
			for i in results:
				col_num = 0
				for j in col_name_needed_list_index:
					# print(i[j])
					mySheet.write(row_num, col_num, i[j])
					col_num += 1
				row_num += 1

			query_data_col_from_results = []
			for i in results:
				query_data_col_from_results.append(i[query_data_col])

			empty = 0
			empty_list = []
			for index, i in enumerate(query_data):
				if i not in query_data_col_from_results:
					empty += 1
					# empty_list.append([index,i])
					empty_list.append(i)

			empty_list.sort()
			# empty_list.sort(key= lambda i: i[1])
			temp_str = "上传的数据有" + str(len(query_data)) + "个。" + "一共查到" + str(len(results)) + "个数据。" + "一共有" + str(
				len(empty_list)) + "个查不到。" + '下面是查询不到的数据（如果为空，则表示全部查到了）'

			mySheet.write(row_num, 0, temp_str)
			row_num += 1

			if not col_name_needed_list:
				# for index, i in empty_list:
				for i in empty_list:
					# mySheet.write(row_num, query_data_col, i)
					mySheet.write(row_num, query_data_col, i)
					mySheet.write(row_num, 0, "查不到")
					# mySheet.write(row_num, query_data_col+1, "查不到的数据应该在查询文件的第"+str(index)+'行左右')
					row_num += 1
			else:
				# for index, i in empty_list:
				for i in empty_list:
					# mySheet.write(row_num, query_data_col, i)
					mySheet.write(row_num, query_data_in_needed_col, i)
					mySheet.write(row_num, 0, "查不到")
					# mySheet.write(row_num, query_data_in_needed_col + 1, "查不到的数据应该在查询文件的第" + str(index) + '行左右')
					row_num += 1

			# 查询结果统计和查不到的结果表
			mySheet = new_excel.add_sheet("查询结果统计以及查不到的数据")  # 添加工作表名
			row_num = 0  # 新表 从0开始

			mySheet.write(row_num, 0, temp_str)
			row_num += 1

			if not col_name_needed_list:
				# for index, i in empty_list:
				for i in empty_list:
					# mySheet.write(row_num, query_data_col, i)
					mySheet.write(row_num, query_data_col, i)
					mySheet.write(row_num, 0, "查不到")
					# mySheet.write(row_num, query_data_col+1, "查不到的数据应该在查询文件的第"+str(index)+'行左右')
					row_num += 1
			else:
				# for index, i in empty_list:
				for i in empty_list:
					# mySheet.write(row_num, query_data_col, i)
					mySheet.write(row_num, query_data_in_needed_col, i)
					mySheet.write(row_num, 0, "查不到")
					# mySheet.write(row_num, query_data_in_needed_col + 1, "查不到的数据应该在查询文件的第" + str(index) + '行左右')
					row_num += 1

			# 保存
			new_excel.save(path + "all_datas_of_query.xls")

			print("excel的数据有：%d个， 检索出来的有：%d个， 其中是空的有： %d个，" % (len(query_data), len(results), empty))
			print(path + "all_datas_of_query.xls")
			# print("这些数据不在数据库", empty_list)

			# 提交到数据库执行
			db.commit()
		except pymysql.ProgrammingError as error:
			code, message = error.args
			print(">>>>>>>>>>>>>", code, message)
			logging.error('SQL执行失败，执行语句为:%s' % str(sql))

			traceback.print_exc()
			# 如果发生错误则回滚
			db.rollback()
			# db.undo()
			pass

	# 关闭数据库连接
	db.close()

	# 把数据转成map字典
	results = [list([list(i) for i in results])]
	results_map_list = []
	for i in results[0]:
		col = 0
		temp_map = {}
		for j in i:

			if isinstance(j, datetime.datetime):
				if not j:
					print(datetime.datetime.strptime('2000-01-01 00:00:00', '%Y-%m-%d %H:%M:%S'))
				else:
					temp_map[col_name_list[col]] = j.strftime('%Y-%m-%d %H:%M:%S')
			else:
				temp_map[col_name_list[col]] = j
			col += 1
		results_map_list.append(temp_map)

	for i in empty_list:
		col = 0
		temp_map = {}
		for j in col_name_list:
			if j == 'index':
				temp_map[j] = '数据库中没有此数据，检查检索的条件'
			else:
				temp_map[j] = ''
			col += 1
		temp_map[col_name_list[query_data_col]] = i
		results_map_list.append(temp_map)
	# print(results_map_list)

	# results 为列表，results[0]是检索数据的列表，results[1]是检索不到数据的（查询数据）列表
	return results_map_list, path + "all_datas_of_query.xls"



if __name__ == '__main__':
	# query(args.excel)
	pass
