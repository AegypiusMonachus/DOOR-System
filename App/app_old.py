'''
此文件暂时报废
'''
# #导入数据库模块
# import pymysql
# #导入Flask框架，这个框架可以快捷地实现了一个WSGI应用
# from flask import Flask
# # abort 异常
# from flask import abort
# # 发送文件的
# from flask import send_file
# #默认情况下，flask在程序文件夹中的templates子文件夹中寻找模块
# from flask import render_template
# # # session
# # from flask import session
# #导入前台请求的request模块
# import traceback
# from flask import request
# #导入json
# import json
# #导入flask_cors包，允许跨域访问
# from flask_cors import CORS
# from flask import Response
# import os
# from werkzeug.utils import secure_filename
# from App.datas import excel as ExcelModel
# from App.datas import query
# import datetime
# import App.config as config
#
# # 全局变量
# datas = [] # 当前页面显示的数据
# data_col_name = [] # 数据库列表名
# #basepath = "/home/dy_server/doorplates_server/temp_datas" # 默认路径
# basepath = config.TEMP_DATAS_PATH # 默认路径
# sql_str = '' # 当前的查询sql
#
# from flask_sqlalchemy import SQLAlchemy
# #db = SQLAlchemy()
# #传递根目录
# app = Flask(__name__)
# app.config.from_object('config')
#
# from App.users.model import db
# db.init_app(app)
# import App.users.api as users_api
# users_api.init_api(app)
# import App.datas.api as datas_api
# datas_api.init_api(app)
#
# CORS(app, supports_credentials=True) # 支持跨域访问
#
# # # session
# # app.config["SECRET_KEY"] = os.urandom(24)
#
# # #添加header_reesponse
# # def add_headers_to_fontawesome_static_files(response):
# #     """
# #     Fix for font-awesome files: after Flask static send_file() does its
# #     thing, but before the response is sent, add an
# #     Access-Control-Allow-Origin: *
# #     HTTP header to the response (otherwise browsers complain).
# #     """
# #
# #     if (request.path and
# #         re.search(r'\.(ttf|woff|svg|eot)$', request.path)):
# #         response.headers.add('Access-Control-Allow-Origin', '*')
# #
# #     return response
#
# # #默认路径访问登录页面
# # @app.route('/')
# # def login():
# #     return render_template('login.html')
#
# # #默认路径访问注册页面
# # @app.route('/regist')
# # def regist():
# #     return render_template('regist.html')
# #
# # #获取注册请求及处理
# # @app.route('/registuser')
# # def getRigistRequest():
# # #把用户名和密码注册到数据库中
# #
# #     #连接数据库,此前在数据库中创建数据库test1
# #     db = pymysql.connect("localhost","root","123456","test1" )
# #     # 使用cursor()方法获取操作游标
# #     cursor = db.cursor()
# #     # SQL 插入语句
# #     sql = "INSERT INTO usersTable(name, password) VALUES ('%s', '%s')" % \
# #     (request.args.get('user'), request.args.get('password'))
# #     try:
# #         # 执行sql语句
# #         cursor.execute(sql)
# #         # 提交到数据库执行
# #         db.commit()
# #          #注册成功之后跳转到登录页面
# #         return render_template('login.html')
# #     except:
# #         #抛出错误信息
# #         traceback.print_exc()
# #         # 如果发生错误则回滚
# #         db.rollback()
# #         return '注册失败'
# #     # 关闭数据库连接
# #     db.close()
# #
# #
# # # 获取登录参数及处理
# # @app.route('/login', methods=['POST','GET'])
# # def getLoginRequest():
# #     # 查询用户名及密码是否匹配及存在
# #     # 连接数据库,此前在数据库中创建数据库TESTDB
# #     db = pymysql.connect("localhost", "root", "123456", "test1")
# #     # 使用cursor()方法获取操作游标
# #     cursor = db.cursor()
# #     if request.method == 'POST':
# #         # SQL 查询语句
# #         print(str(request.get_data(as_text=True)))
# #
# #         data = json.loads(request.get_data(as_text=True))
# #         print(data)
# #         sql = "SELECT * FROM usersTable WHERE name='%s' AND password='%s' " % (data['user'], \
# #                                                                               data['password'])
# #         #sql = "SELECT * FROM usersTable WHERE name='%s' AND password='%s' " % (request.form['user'], \
# #          #                                                                      request.form['password'])
# #
# #     else:
# #         # SQL 查询语句
# #         print(str(request.args))
# #         sql = "SELECT * FROM usersTable WHERE name='%s' AND password='%s' " % (request.args.get('user'), \
# #                                                                           request.args.get('password'))
# #     try:
# #         # 执行sql语句
# #         cursor.execute(sql)
# #         results = cursor.fetchall()
# #         print(len(results))
# #         if len(results) == 1:
# #             returnData = {}
# #             returnData['success'] = True
# #             returnData['redirect'] = 'pages/dashboard'
# #             jsonStr = json.dumps(returnData, ensure_ascii=False)
# #
# #
# #             print("登陆成功")
# #             #return '登录成功'
# #             return jsonStr
# #         else:
# #             print("登陆失败")
# #             return '用户名或密码不正确'
# #         # 提交到数据库执行
# #         db.commit()
# #     except:
# #         # 如果发生错误则回滚
# #         traceback.print_exc()
# #         db.rollback()
# #     # 关闭数据库连接
# #     db.close()
#
#
#
# # 检索数据
# @app.route('/doorplates', methods=['GET'])
# def getDataRequest():
#
#     print("当前访问用户：", request.remote_addr)
#     # 查询数据是否存在
#     # 连接数据库,此前在数据库中创建数据库dayi_doorplate
#     #db = pymysql.connect("localhost", "root", "123456", "dayi_doorplate")
#     #db = pymysql.connect("localhost", "root", "root", "ws_doorplate")
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
#     #print(request.args)
#     #print(type(request.args))
#     query_key = []
#     for key in request.args.keys():
#         if key.find('like') > 0:
#             query_key.append(key[0:key.find('like')-1])
#
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
#     #if len(str(request.args.get('doorID')))
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
#
#     if len(query_key) > 0:
#         #print(query_key)
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
#         #print(sql)
#         #print("SELECT COUNT(*) FROM gz_orders " + sql_like_query)
#         cursor.execute("SELECT COUNT(*) FROM gz_orders " + sql_like_query)
#         count = cursor.fetchall()
#         #print(int(count[0][0]))
#         count = int(count[0][0])
#     # if request.args.get('pcs_like'):
#     #     sql = "SELECT * FROM gz_orders WHERE pcs like '%%%s%%' " % (request.args.get('pcs_like'))
#     #     sql = sql + sql_limit
#     #     cursor.execute("SELECT COUNT(*) FROM gz_orders WHERE pcs like '%%%s%%'" % (request.args.get('pcs_like')))
#     #     count = cursor.fetchall()
#     #     print(int(count[0][0]))
#     #     count = int(count[0][0])
#     elif page > 0:
#         #sql = "SELECT * FROM gz_orders ORDER BY dp_id LIMIT '%d' " % (request.args.get('order_id'))
#
#         sql = "SELECT * FROM gz_orders" + sql_limit
#         sql_str = "SELECT * FROM gz_orders "
#         cursor.execute("SELECT COUNT(*) FROM gz_orders")
#         count = cursor.fetchall()
#         #print(int(count[0][0]))
#         count = int(count[0][0])
#
#     #sql = "SELECT * FROM usersTable WHERE name='%s' AND password='%s' " % (request.args.get('doorID'), \
#      #                                                                     request.args.get('password'))
#     #print(sql)
#     # count = 0
#     #resp = Response("Foo bar baz")
#
#
#
#
#     doorplatesList = []
#     if sql:
#         try:
#             # 执行sql语句
#             print(sql)
#             cursor.execute(sql)
#             results = cursor.fetchall()
#             #print(len(results))
#             #print(results)
#
#
#             #doorplatesList.append({'x-total-count': len(results)})
#
#             if len(results) >= 1:
#                 print("查到相关数据")
#
#                 #doorplatesList = []
#                 global datas
#                 for r in results:
#                     #print(r[23], end=' ')
#                     #print(r[4], end=' ')
#                     #print(r[2], end=' ')
#                     #print("---")
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
#                 #data['x-total-count'] = len(doorplatesList)
#                 jsonStr = json.dumps(datas, ensure_ascii=False)
#
#                 #print(jsonStr)
#                 #decode_json = json.loads(jsonStr)
#                 #print(decode_json)
#
#                 #return jsonStr
#                 resp = Response(jsonStr)
#                 resp.mimetype = 'application/json'
#                 #resp.headers['x-total-count'] = len(results)
#                 resp.headers['x-total-count'] = count
#                 resp.headers['access-control-expose-headers'] = 'X-Total-Count'
#                 #return Response(jsonStr, mimetype='application/json')
#                 # 关闭数据库连接
#                 db.close()
#                 return resp
#             else:
#                 print("没有相关数据")
#                 #return jsonStr
#                 resp = Response(str([]))
#                 resp.mimetype = 'application/json'
#                 #resp.headers['x-total-count'] = len(results)
#                 resp.headers['x-total-count'] = count
#                 resp.headers['access-control-expose-headers'] = 'X-Total-Count'
#                 #return Response(jsonStr, mimetype='application/json')
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
#
#
# @app.route('/excel', methods=['GET', 'POST'])
# def excel():
#     print("有文件要上传")
#     if request.method == 'POST':
#         #f = request.files['file']
#         #f = request.files.get('file')
#         print(request.files)
#         if 'file' not in request.files:
#             resp = Response(str([{'index': '未上传文件'}]))
#             resp.mimetype = 'application/json'
#             resp.headers['x-total-count'] = 1
#             resp.headers['access-control-expose-headers'] = 'X-Total-Count'
#             return resp
#         f = request.files['file']
#         #basepath = os.path.dirname(__file__)  # 当前文件所在路径
#         #print(basepath)
#         #basepath = "/home/dy_server/doorplates_server/temp_datas"
#         #print(basepath)
#         # 注意：没有的文件夹一定要先创建，不然会提示没有该路径
#         upload_path = os.path.join(basepath + '/uploads', secure_filename(f.filename))
#         print("文件保存在：", upload_path)
#         f.save(upload_path)
#
#         # 上传成功后 查询excel
#         results, query_excel_path = query.query(upload_path)
#         results.append({'query_excel_url': query_excel_path})
#
#         jsonStr = json.dumps(results, ensure_ascii=False)
#         #print(jsonStr)
#         resp = Response(jsonStr)
#         resp.mimetype = 'application/json'
#         resp.headers['x-total-count'] = len(results) - 1 # 减去query_excel_path占用的一个
#         resp.headers['access-control-expose-headers'] = 'X-Total-Count'
#
#         #return '成功上传'
#         return resp
#
#
#     resp = Response(str([{'index': '未上传文件，可能是请求有问题'}]))
#     resp.mimetype = 'application/json'
#     resp.headers['x-total-count'] = 1
#     resp.headers['access-control-expose-headers'] = 'X-Total-Count'
#     return resp
#
#
# @app.route('/files', methods=['GET', 'POST'])
# def files():
#     print("有文件要下载")
#     if request.method == 'GET':
#         try:
#             path = request.args.get('path')
#             #print(path)
#             if path == 'need_make_excel':
#                 file_sended_path = os.path.join(basepath, 'downloads')
#                 db = pymysql.connect("localhost", "root", "root", "ws_doorplate")
#                 # 使用cursor()方法获取操作游标
#                 cursor = db.cursor()
#                 cursor.execute(sql_str)
#                 results = cursor.fetchall()
#                 db.commit()
#                 #excel_name = 'total_of_' + len(datas) + "_" + datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S') + '.xls'
#                 excel_name = str(len(results)) + "_" + datetime.datetime.now().strftime('%Y%m%d') + '.xls'
#                 #excel_name = datetime.datetime.now().strftime('%Y%m%d')
#                 sum = 0
#                 #(excel_name, extension) = os.path.splitext(excel_name)
#                 if os.path.isfile(os.path.join(file_sended_path, excel_name)):
#                     for root, dirs, files in os.walk(file_sended_path):
#                         #print('root_dir:', root)  # 当前目录路径
#                         #print('sub_dirs:', dirs)  # 当前路径下所有子目录
#                         #print('files:', files)  # 当前路径下所有非目录子文件
#                         for file in files:
#                             if file.find(excel_name) == 0:
#                                 sum += 1
#
#                     excel_name = excel_name + "(" + str(sum) + ")"
#
#                 excel_name += '.xls'
#
#                 #filepath, filename, fullpath = ExcelModel.datas_to_excel(datas, col_name_list=data_col_name, path=basepath, excel_name=excel_name)
#                 filepath, filename, fullpath = ExcelModel.datas_to_excel(results, col_name_list=data_col_name,
#                                                                          path=file_sended_path, excel_name=excel_name)
#                 print("要下载的文件是：", filename, "\n路径：", filepath)
#                 #print(fullpath)
#                 db.close()
#                 if os.path.isfile(fullpath):
#                     result = send_file(fullpath, as_attachment=True, attachment_filename=filename)
#                     #result.headers["x-suggested-filename"] = filename
#                     #result.headers["x-filename"] = filename
#                     #result.headers["Access-Control-Expose-Headers"] = 'x-filename'
#                     return result
#                     #return send_from_directory(filepath, filename, as_attachment=True)
#                     #return send_file(path, as_attachment=True, attachment_filename=filename)
#                 print("下载文件有错误，可能是文件路径不存在")
#                 abort(404)
#
#             else:
#                 #if os.path.isfile(os.path.join('upload', path)):
#                 (filepath, filename) = os.path.split(path)
#                 print("要下载的文件是：", filename, "\n路径：", filepath)
#                 if os.path.isfile(path):
#                     result = send_file(path, as_attachment=True, attachment_filename=filename)
#                     #result.headers["x-suggested-filename"] = filename
#                     #result.headers["x-filename"] = filename
#                     #result.headers["Access-Control-Expose-Headers"] = 'x-filename'
#                     return result
#                     #return send_from_directory(filepath, filename, as_attachment=True)
#                     #return send_file(path, as_attachment=True, attachment_filename=filename)
#                 print("下载文件有错误，可能是文件路径不存在")
#                 abort(404)
#
#         except:
#             print("下载文件有错误，可能是GET协议参数不匹配")
#             abort(404)
#
#
#
# @app.route('/test')
# def test():
#     return '家乐你是傻逼!!!'
#
# # 使用__name__ == '__main__'是 Python 的惯用法，确保直接执行此脚本时才
# # python xx.py __name__ == __main__， 如果是import xx.py __name__!=__main__
# if __name__ == '__main__':
#     #app.run(debug=False, host='0.0.0.0', port=2333)
#     #app.run(debug=config.DEBUG, host=config.HOST, port=config.PORT)
#     #app.run(debug=False, host='127.0.0.1', port=2333)
#     # additional options: --host=0.0.0.0 --port=2333
#     pass