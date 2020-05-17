import os
import xlwt
from App.others import files_operation
from App.mysql import mysql

col_name_map = {
    'contract_batch': '合同批次',
    'order_batch': '订单批次',
    'from_filename': '来源文件',
    'distirct_id': '行政区号',
    'order_id': '订单号',
    'dp_id': '门牌id',
    'district': '行政区',
    'pcs': '派出所',
    'street': '街路巷',
    'dp_name': '门牌名称',
    'dp_num': '门牌号',
    'dp_num_trans': '门牌号纯数字',
    'dp_size': '门牌规格',
    'dp_nail_style': '钉挂方式',
    #'dp_nail_style': '门牌安装方式',
    'producer': '烧制厂家',
    'produce_date': '烧制日期',
    'installer': '安装厂家',
    'factory_batch': '厂家批号',
    'factory_index': '厂家序号',
    'applicant': '申请人',
    'contact_number': '联系电话',
    'jump': '跳号说明',
    'fix': '补漏制作',
    'dp_type': '门牌类型',
    'global_id': '全球唯一码',
    'global_id_with_dp_name': '全球唯一码带门牌名称',
    'exported_produce': '是否生成生产单',
    "exported_produce_by": '生成生产单操作员',
    "exported_produce_date": '生成生产单日期',
    "produced": '是否生产',
    "delivered": '是否送货',
    "recevied": '接收确认',
    "installed": '是否安装',
    "installed_by": '安装人员',
    "installed_date": '安装日期',
    "installed_coordinate": '安装坐标',
    "installed_photos": '安装照片',
    "installed_photos_cls": '安装近照片',
    "installed_photos_far": '安装远照片',
    "photos": '照片',
    "uploaded_by": '上传人员',
    "uploaded_date": '上传日期',
    "index": '数据id',
    "update_by": '修改人',
    "update_date": '修改日期',
    "enter_repository_date": "入库日期",
    "exit_repository_date": "出库日期",
    "last_update_date": '最后修改日期'
}



# 将数据保存成excel，
# 参数：数据、列名数组、excel保存路径、excel保存文件名
# 数据参数是数组类型，
def datas_to_excel(datas_list, col_name_list=['pcs', 'street', 'dp_num', 'dp_num_trans', 'dp_name', 'global_id', \
                                        'global_id_with_dp_name', 'dp_type', 'dp_size', 'exported_produce'], path='./', excel_name='new.xls'):

    save_path = os.path.join(path, excel_name)
    print("生成的excel在", save_path)
    new_excel = xlwt.Workbook()  # 新建excel
    mySheet = new_excel.add_sheet("sheet1")  # 添加工作表名

    col_name_map = mysql.get_col_name_map()

    # 写入每一列的列名
    i = 0
    for col_name in col_name_list:
        if not col_name_map.get(col_name):
            mySheet.write(0, i, col_name)
        else:
            mySheet.write(0, i, col_name_map.get(col_name))
        i += 1
    # 从第1行开始写入数据
    row_num = 1
    if isinstance(datas_list, tuple):
        for data in datas_list:
            col_num = 0
            for j in data:
                mySheet.write(row_num, col_num, j)
                col_num += 1
            row_num += 1
    else:
        for data in datas_list:
            col_num = 0
            for col_name in col_name_list:
                mySheet.write(row_num, col_num, data[col_name])
                col_num += 1
            row_num += 1

    # query_data_col_from_results = []
    # for i in results:
    #     query_data_col_from_results.append(i[query_data_col])

    # empty = 0
    # empty_list = []
    # for i in query_data:
    #     if i not in query_data_col_from_results:
    #         empty += 1
    #         empty_list.append(i)

    # mySheet.write(row_num, 0, '查询不到的数据')
    # row_num += 1
    # for i in empty_list:
    #     mySheet.write(row_num, query_data_col, i)
    #     row_num += 1


    # 保存
    new_excel.save(save_path)
    return path, excel_name, save_path

'''
    将数据保存成excel，
    input:
        args: 数据、excel保存路径、excel保存文件名
            数据是字典类型，字典key是列名，value是对应的列数据
        可选:
            title_sequence_list: 传入列名的顺序list, 如要生成的为["派出所","安装人"]这样的顺序
            title_info: 这个是表头的信息，传二维list
    return:
        文件保存的路径    
'''
def data_map_to_excel(data_map, path='./', excel_name='new.xls', **kw):

    if path != './':
        files_operation.make_dirs(path)
    exist, full_path = files_operation.is_file(os.path.join(path, excel_name))


    new_excel = xlwt.Workbook()  # 新建excel
    mySheet = new_excel.add_sheet("sheet1")  # 添加工作表名

    print(data_map)

    row_index_now = 0
    # 按行写表头信息
    if kw.get("title_info"):
        title_info = kw.get("title_info")
        for row_data in title_info:
            for col_index, col_data in enumerate(row_data):
                mySheet.write(row_index_now, col_index, col_data)
            row_index_now += 1

    col_index = 0
    # 按列写数据
    for col_name, col_data_list in data_map.items():
        mySheet.write(row_index_now, col_index, col_name)
        for row_index, row_data in enumerate(col_data_list):
            # 写col_index列的数据, row_index+1是因为第一行已经被写了
            mySheet.write(row_index+row_index_now+1, col_index, row_data)
        col_index += 1

    # 保存
    new_excel.save(full_path)
    print("生成的excel在", full_path)
    return full_path