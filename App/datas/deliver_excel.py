# 送货单生成脚本
import xlrd
import xlwt
# import argparse # gunicorn 不支持 argparse!!!
import os
from xlrd import xldate_as_tuple
import datetime
import time
from App.datas import dp_sort
from App.datas import excel
from App import common
from App.mysql.mysql import CITY
from App.mysql import mysql

# parser = argparse.ArgumentParser()
# parser.add_argument('--excel', help = "excel 完整路径")
# args = parser.parse_args()



# 获取字符串长度，一个中文的长度为2
def len_byte(value):
    length = len(value)
    utf8_length = len(value.encode('utf-8'))
    length = (utf8_length - length) / 2 + length
    return int(length)

def get_worksheet(workbook, sheet="sheet", exist_sheet_name=[]):
    # 工作博名字为sheet
    # cell_overwrite_ok=False 意思是可以重复写入

    temp = sheet
    sum = 1
    while (temp in exist_sheet_name):
        temp = sheet + '_' + str(sum)
        sum += 1

    worksheet = workbook.add_sheet(temp, cell_overwrite_ok=False)

    exist_sheet_name.append(temp)
    return worksheet
# 复合样式
def setZiTiStyle(bold=False,height=280,VERT=0x01,HORZ=0x01, horz_Align=xlwt.Alignment.HORZ_CENTER):
    # 可以设置多种样式
    style = xlwt.XFStyle()
    yanshi = xlwt.Borders()
    ziti = xlwt.Font()
    duiqi = xlwt.Alignment()
    ziti.name =u'宋体' #宋体
    ziti.height = height # 字体14
    ziti.bold = bold
    duiqi.horz = horz_Align
    duiqi.vert =VERT
    # 字体设置
    style.font = ziti
    # 居中方式
    style.alignment = duiqi
    return style
# 内容样式
def setStyle(bold=False,height=220, border=True, horz_Align=xlwt.Alignment.HORZ_CENTER, color=0, background_color=1):
    # 可以设置多种样式
    style = xlwt.XFStyle()
    yanshi = xlwt.Borders()
    ziti = xlwt.Font()
    duiqi = xlwt.Alignment()
    # THIN实线边框
    if border:
        yanshi.left = xlwt.Borders.THIN
        yanshi.right = xlwt.Borders.THIN
        yanshi.bottom = xlwt.Borders.THIN
        yanshi.top = xlwt.Borders.THIN
    else:
        #yanshi.left = xlwt.Borders.NO_LINE
        yanshi.right = xlwt.Borders.NO_LINE
        yanshi.bottom = xlwt.Borders.NO_LINE
        yanshi.top = xlwt.Borders.NO_LINE
    yanshi.left_colour = 0x40
    yanshi.right_colour = 0x40
    yanshi.bottom_colour = 0x40
    yanshi.top_colour = 0x40
    ziti.name =u'宋体' #宋体
    ziti.height = height # 字体14
    ziti.bold = bold
    ziti.colour_index = color # 颜色 常用颜色 黑色0 白色1 红色2 绿色3 蓝色4 黄色5 紫色6 浅蓝色7
    # 背景颜色设置
    # 设置背景颜色的模式
    style.pattern.pattern = xlwt.Pattern.SOLID_PATTERN
    # 背景颜色
    style.pattern.pattern_fore_colour = background_color
    #style.pattern.pattern_back_colour = background_color
    duiqi.horz = horz_Align
    duiqi.vert =xlwt.Alignment.VERT_CENTER
    # 字体设置
    style.font = ziti
    # 边框设置
    style.borders = yanshi
    # 居中方式
    style.alignment = duiqi

    return style

# 内容样式 [0,0,0,0] -> [top,bottom,left,right]
def setStyle2(border_mask=[0,0,0,0]):
    # 可以设置多种样式

    borders = xlwt.Borders()
    borders.top = border_mask[0]
    borders.bottom = border_mask[1]
    borders.left = border_mask[2]
    borders.right = border_mask[3]


    style = xlwt.XFStyle()
    style.borders = borders

    return style

def write_template():
    pass


def load_Excel(path):

    workbook=xlrd.open_workbook(path)
    #sheet = workbook.sheets()[0]

    print("Loading order excel")
    sheet_names = workbook.sheet_names()
    #for sheet_name in sheet_names:
    sheet_name = sheet_names[0]
    #print(sheet_name)
    sheet = workbook.sheet_by_name(sheet_name)

    pcs = -1
    community = -1
    street = -1
    dp_name = -1
    dp_num = -1
    dp_num_trans = -1
    global_id_with_dp_name = -1
    dp_type = -1
    dp_size = -1
    dp_id = -1
    global_id = -1
    exported_produce = -1

    col_name_index_map = {}
    # col_name_index_map['duplicate'] = -1 # 查重index 默认在数据的最后一列
    datas_list = []

    # 加载到标题那一行
    # 默认加载第一行
    col_title_row = -1
    for r in range(sheet.nrows):
        if col_title_row >= 0:
            break
        for c in range(sheet.ncols):
            if sheet.cell_value(r, c) in list(excel.col_name_map.values()):
                #print(sheet.cell_value(r, c))
                col_title_row = r
                #print(col_title_row)
                #r = len(range(sheet.nrows)) - 1
                break

    if col_title_row == -1:
        col_title_row = 0

    col_name_list = mysql.get_col_name_list()

    for c in range(sheet.ncols):
        # print(sheet.cell_value(0,c))
        # print(sheet.cell_value(col_title_row,c))
        if (sheet.cell(col_title_row,
                       c).ctype > 0):  # 单元格为string类型 0 empty,1 string, 2 number, 3 date, 4 boolean, 5 error
            for i in col_name_list:
                if sheet.cell_value(col_title_row, c) == i[1]:
                    col_name_index_map[i[0]] = c
            # if sheet.cell_value(col_title_row,c) == ("派出所"):
            #         pcs = c
            #         col_name_index_map["pcs"] = c
            # elif sheet.cell_value(col_title_row,c) == ("社区"):
            #         community = c
            #         col_name_index_map["community"] = c
            # elif sheet.cell_value(col_title_row,c) == ("街路巷"):
            #         street = c
            #         col_name_index_map["street"] = c
            # elif sheet.cell_value(col_title_row,c) == ("门牌号"):
            #         dp_num = c
            #         col_name_index_map["dp_num"] = c
            # elif sheet.cell_value(col_title_row,c) == ("门牌名称"):
            #         dp_name = c
            #         col_name_index_map["dp_name"] = c
            # elif sheet.cell_value(col_title_row,c) == ("全球唯一码带门牌名称"):
            #         global_id_with_dp_name = c
            #         col_name_index_map["global_id_with_dp_name"] = c
            # elif sheet.cell_value(col_title_row,c) == ("全球唯一码"):
            #         global_id = c
            #         col_name_index_map["global_id"] = c
            # elif sheet.cell_value(col_title_row,c) == ("门牌类型"):
            #         dp_type = c
            #         col_name_index_map["dp_type"] = c
            # elif sheet.cell_value(col_title_row,c) == ("门牌规格"):
            #         dp_size = c
            #         col_name_index_map["dp_size"] = c
            # elif sheet.cell_value(col_title_row,c) == ("门牌id"):
            #         dp_id = c
            #         col_name_index_map["dp_id"] = c
            # elif sheet.cell_value(col_title_row,c) == ("门牌号纯数字"):
            #         dp_num_trans = c
            #         col_name_index_map["dp_num_trans"] = c
            # elif sheet.cell_value(col_title_row,c) == ("是否生成生产单"):
            #         exported_produce = c
            #         col_name_index_map["exported_produce"] = c

    temp_data_len = 0
    for r in range(sheet.nrows):
        #if r == 0:
        if r <= col_title_row:
            continue
        temp_data = []
        for c in range(sheet.ncols):
            if (sheet.cell(r,c).ctype) > 0 and (sheet.cell(r,c).ctype) < 5:
                if (sheet.cell(r,c).ctype) == 3:
                    date = xldate_as_tuple(sheet.cell(r,c).value,0)
                    cell_string = str(datetime.datetime(*date))
                    temp_data.append(cell_string)
                elif (sheet.cell(r,c).ctype) == 2:

                    # 把1.0类型的数字 转成 1
                    if sheet.cell_value(r,c)==int(sheet.cell_value(r,c)): #checking for the integer:
                        cell_string = str(int(sheet.cell_value(r,c)))
                        temp_data.append(cell_string)
                    else:
                        cell_string = str(sheet.cell_value(r,c))
                        temp_data.append(cell_string)
                else:
                    cell_string = str(sheet.cell_value(r,c))
                    temp_data.append(cell_string)
            elif (sheet.cell(r,c).ctype) == 0:
                cell_string = str('')
                temp_data.append(cell_string)
        if not temp_data_len:
            temp_data_len = len(temp_data)
        datas_list.append(temp_data)


    if len(datas_list) > 0:
        if 'dp_num_trans' not in col_name_index_map.keys():
            col_name_index_map['dp_num_trans'] = temp_data_len
            temp_data_len += 1
            for temp in datas_list:
                temp.append(
                    dp_sort.chinese_to_arabic_with_connection(temp[col_name_index_map['dp_num']]))
        # print("len(street_dp_type_dp_size_map[type][size][street][0])",
        #       len(street_dp_type_dp_size_map[type][size][street][0]))
        # 如果没有生成全球唯一码带门牌名称，就生成
        if 'global_id_with_dp_name' not in col_name_index_map.keys():
            col_name_index_map['global_id_with_dp_name'] = temp_data_len
            temp_data_len += 1
            for temp in datas_list:
                temp.append(
                    temp[col_name_index_map['global_id']] + temp[col_name_index_map['dp_name']])
    #print(datas_list)
    return datas_list, col_name_index_map


def export_excel(datas_list, col_name_index_map, path="", filename="", **kw):

    city = kw.get("city")
    need_dp_type = ""
    if not kw:
        pass
    else:
        try:
            need_dp_type = kw.get("need_dp_type")
        except:
            need_dp_type = ""





    print("need_dp_type", need_dp_type)




    #前期设置工作
    # 设置单元格的格式
    # 第一行行高25.5，字体宋体，字体大小20，居中，加粗(内容是正式或者是临时)
    # 第二行行高15,字体宋体，字体大小12，靠右，加粗
    # 第三行行高18.75，字体宋体，字体大小14，靠左，加粗(内容是单位名称：)
    # 第四行行高18.75，字体宋体，字体大小14，居中，加粗(内容是规格：)
    # 第五行行高14.25，字体宋体，字体大小11，居中，四条边框(内容是街路巷，门牌号，数量，门牌名称，门牌id，全球唯一码)
    # 内容主要是第五行的东西，其中数量要求合并单元格，门牌号是文本类型
    # 最后一行加上合计：
    # sheet表名为单位名缩写，比如广州市公安局海珠区分局赤岗派出所，临时门牌应为赤岗-临时,正式门牌应为赤岗-正式
    OneStyle = setZiTiStyle(True,400,0x01,0x02) # 字体20，垂直居中，居中对齐
    TwoStyle = setZiTiStyle(True,240,0x01,0x03, horz_Align=xlwt.Alignment.HORZ_RIGHT) # 字体20，垂直居中，右端对齐
    ThreeStyle = setZiTiStyle(True,280,0x01,0x01, horz_Align=xlwt.Alignment.HORZ_LEFT) # 字体20，垂直居中，靠左对齐
    FourStyle = setZiTiStyle(True,280,0x01,0x02) # 字体20，垂直居中，居中对齐
    content_Style = setStyle(False)
    content_Style_yellow = setStyle(False, color=5)
    content_yellow_background_color_Style = setStyle(False, background_color=5)
    content_title_Style = setStyle(True)
    content_left_Style = setStyle(False, border=False, horz_Align = xlwt.Alignment.HORZ_LEFT)
    content_title_Style_no_border = setStyle(False, border=False)
    content_align_left_red_color_Style = setStyle(bold=False, height=220, border=True,
                                        horz_Align=xlwt.Alignment.HORZ_LEFT,
                                        color=2)
    content_align_left_red_color_yellow_background_Style = setStyle(bold=False, height=220, border=True,
                                                  horz_Align=xlwt.Alignment.HORZ_LEFT,
                                                  color=2, background_color=5)
    content_align_left_yellow_background_Style = setStyle(bold=False, height=220, border=True,
                                                                    horz_Align=xlwt.Alignment.HORZ_LEFT,
                                                                    background_color=5)
    content_align_left_yellow_color_Style = setStyle(bold=False, height=220, border=True,
                                                  horz_Align=xlwt.Alignment.HORZ_LEFT,
                                                  color=5)

    content_align_left_Style = setStyle(bold=False, height=220, border=True,
                                        horz_Align=xlwt.Alignment.HORZ_LEFT)
    content_align_left_no_border_Style = setStyle(False, border=False, horz_Align=xlwt.Alignment.HORZ_LEFT)
    content_no_border_no_bold = setStyle(False, border=False)

    content_right_border = setStyle2([0, 0, 0, 1])
    content_bottom_border = setStyle2([0, 1, 0, 0])
    content_bottom_right_border = setStyle2([0, 1, 0, 1])



    biaoti = ["街路巷","门牌号","数量","门牌名称","门牌id","全球唯一码"]

    if not datas_list:
        workbook = xlwt.Workbook()
        worksheet = workbook.add_sheet("上传excel数据空", cell_overwrite_ok=False)
        worksheet.write_merge(0, 0, 0, 3, "上传excel数据空", content_Style)

        save_path = os.path.dirname(path) + "/produced_" + str(time.time()) + ".xls"
        print("输出文件在：", save_path)
        workbook.save(save_path)
        return save_path

    #col_name_index_map
    if "pcs" not in col_name_index_map.keys():
        workbook = xlwt.Workbook()
        worksheet = workbook.add_sheet("上传excel数据无派出所数据，或者派出所列名格式出错", cell_overwrite_ok=False)
        worksheet.write_merge(0, 0, 0, 3, "上传excel数据无派出所数据，或者派出所列名格式出错", content_Style)
        # 最后保存
        save_path = os.path.dirname(path) + "/produced_" + str(time.time()) + ".xls"
        print("输出文件在：", save_path)
        workbook.save(save_path)
        return save_path

    repeat_datas = []  # 重复数据数组
    repeat_datas_but_not_same = []  # 重复数据但是global_id不同的数组
    #print(col_name_index_map)

    statistics_datas = {} # 数据数量统计map




    # {"xx派出所":[[],[],[]...[]], "xx派出所":[[],[],[]...[]], "xx派出所":[[],[],[]...[]}
    pcs_map = {}
    # 按派出所分数据
    for i in datas_list:
        '''
        广州的门牌生产单按派出所分
        其他的目前按社区
        '''
        if city == 'guangzhou':
            #split_data = i[col_name_index_map["pcs"]]
            if col_name_index_map.get("order_id"):
                split_data = i[col_name_index_map["pcs"]] + "_" + i[col_name_index_map["order_id"]]
            else:
                split_data = i[col_name_index_map["pcs"]] + "_" + ""
        else:
            split_data = i[col_name_index_map["pcs"]]+i[col_name_index_map["community"]]

        if split_data not in pcs_map.keys():
            pcs_map[split_data] = []
            pcs_map[split_data].append(i)
        else:
            pcs_map[split_data].append(i)

    #print(pcs_map)
    workbook = xlwt.Workbook()

    exist_sheet_name = []

    for pcs in pcs_map.keys():
        data = pcs_map.get(pcs)
        if city == 'guangzhou':
            w = pcs.split("_")[0]
        else:
            w = pcs






        '''
        查找相同门牌名称的数据
        '''
        #repeat_datas = [] # 重复数据数组
        dp_name_map = {}
        dp_name_list = [[index, i[col_name_index_map["dp_name"]]] for index, i in enumerate(data)]
        #dp_name_set = set(dp_name_list)
        #print(dp_type_map)
        for index, dp_name in dp_name_list:
            if dp_name == '' or dp_name is None:
                continue
            if dp_name not in dp_name_map.keys():
                dp_name_map[dp_name] = {}
                dp_name_map[dp_name]["index"] = []
                dp_name_map[dp_name]["index_and_dp_type_map"] = {}
                dp_name_map[dp_name]["same"] = 0
                dp_name_map[dp_name]["no_same"] = 0
                dp_name_map[dp_name]["index"].append(index)
                #dp_name_map[dp_name]["index_and_dp_type_map"][index] = data[index][col_name_index_map["dp_type"]]
            else:
                for i in dp_name_map[dp_name]["index"]:
                    #print(data[i][col_name_index_map["global_id"]])
                    #print(data[index][col_name_index_map["global_id"]])
                    #if data[i][col_name_index_map["global_id"]] == data[index][col_name_index_map["global_id"]]:

                    # 新增，如果门牌类型也相同的话才增加
                    if data[i][col_name_index_map["global_id"]] == data[index][col_name_index_map["global_id"]] and data[i][col_name_index_map["dp_type"]] == data[index][col_name_index_map["dp_type"]]:
                        dp_name_map[dp_name]["same"] += 1
                        repeat_datas.append(data[index])
                        #data.remove(data[index])
                        #data[index][col_name_index_map['dp_type']] = '重复数据'

                        # 2019-06-29
                        data[index][col_name_index_map['dp_type']] = None
                        '''
                        if need_dp_type=='temporary':
                           if str(data[index][col_name_index_map['dp_type']]).find('正式') >= 0:
                               data[index][col_name_index_map['dp_type']] = None
                        elif need_dp_type == 'official':
                            if str(data[index][col_name_index_map['dp_type']]).find('临时') >= 0:
                                data[index][col_name_index_map['dp_type']] = None
                        #elif not need_dp_type: # 传空值代表全要
                        else:
                            data[index][col_name_index_map['dp_type']] = None
                        '''
                        break

                    else:
                        dp_name_map[dp_name]["no_same"] += 1
                        dp_name_map[dp_name]["index"].append(index)
                        repeat_datas_but_not_same.append(data[index])
                        # 2019-06-29
                        #data[index][col_name_index_map['dp_type']] = None

                        if data[i][col_name_index_map["dp_type"]] == data[index][col_name_index_map["dp_type"]]:
                            data[index][col_name_index_map['dp_type']] = None

                        '''
                        if need_dp_type == 'temporary':
                            if str(data[index][col_name_index_map['dp_type']]).find('正式') >= 0:
                                data[index][col_name_index_map['dp_type']] = None
                        elif need_dp_type == 'official':
                            if str(data[index][col_name_index_map['dp_type']]).find('临时') >= 0:
                                data[index][col_name_index_map['dp_type']] = None
                        # elif not need_dp_type: # 传空值代表全要
                        else:
                            pass
                        if data[i][col_name_index_map["dp_type"]] == data[index][col_name_index_map["dp_type"]]:
                            data[index][col_name_index_map['dp_type']] = None
                        '''

                        break
        #print(dp_name_map)
        # dp_name_map = {}
        # dp_name_list = [i[col_name_index_map["dp_name"]] for i in data]
        # #dp_name_set = set(dp_name_list)
        # #print(dp_type_map)
        # for dp_name in dp_name_list:
        #     if dp_name not in dp_name_map.keys():
        #         dp_name_map[dp_name] = 1
        #     else:
        #         dp_name_map[dp_name] += 1


        # 按门牌类型划分数据
        '''
        {"正式":[],[],[],"临时":[],[],[]}
        '''
        dp_type_map = {}
        for i in data:
            if "dp_type" not in col_name_index_map.keys():
                if "正式门牌" not in dp_type_map.keys():
                    dp_type_map["正式门牌"] = []
                dp_type_map["正式门牌"].append(i)
            else:
                # if i[col_name_index_map["dp_type"]] == '重复数据':
                if i[col_name_index_map["dp_type"]] is None:
                    continue
                else:
                    if need_dp_type == 'temporary':
                        if str(i[col_name_index_map["dp_type"]]).find('正式') >= 0:
                            continue
                    elif need_dp_type == 'official':
                        if str(i[col_name_index_map["dp_type"]]).find('临时') >= 0:
                            continue
                    else:
                        pass
                    if i[col_name_index_map["dp_type"]] not in dp_type_map.keys():
                        dp_type_map[i[col_name_index_map["dp_type"]]] = []
                        dp_type_map[i[col_name_index_map["dp_type"]]].append(i)
                    else:
                        dp_type_map[i[col_name_index_map["dp_type"]]].append(i)
        #print(dp_type_map['临时门牌'])
        #print("dp_type_map", dp_type_map)
        # 按门牌规格以及门牌类型划分数据
        '''
        {"正式":{"300*200":[],[],[]},"临时":{"300*200":[],[],[]}}
        '''
        dp_type_dp_size_map = {}
        for type in dp_type_map.keys():
            dp_type_dp_size_map[type] = {}
            for i in dp_type_map[type]:
                if i[col_name_index_map["dp_size"]] not in dp_type_dp_size_map[type].keys():
                    dp_type_dp_size_map[type][i[col_name_index_map["dp_size"]]] = []
                    dp_type_dp_size_map[type][i[col_name_index_map["dp_size"]]].append(i)
                else:
                    dp_type_dp_size_map[type][i[col_name_index_map["dp_size"]]].append(i)

        #print(dp_type_dp_size_map)
        #
        # # 按门牌规格划分数据
        # dp_size_map = {}
        # for i in data:
        #     if i[col_name_index_map["dp_size"]] not in dp_size_map.keys():
        #         dp_size_map[i[col_name_index_map["dp_size"]]] = []
        #         dp_size_map[i[col_name_index_map["dp_size"]]].append(i)
        #     else:
        #         dp_size_map[i[col_name_index_map["dp_size"]]].append(i)
        #
        # # print(dp_size_map)

        # 按街划分数据
        '''
        {"正式":{"300*200":{"xx街":[],[],[]}},"临时":{"300*200":{"xx街":[],[],[]}}}
        '''

        street_dp_type_dp_size_map = {}
        for type in dp_type_map.keys():
            street_dp_type_dp_size_map[type] = {}
            for size in dp_type_dp_size_map[type]:
                street_dp_type_dp_size_map[type][size] = {}
                for i in dp_type_dp_size_map[type][size]:
                    if i[col_name_index_map["street"]] not in street_dp_type_dp_size_map[type][size].keys():
                        street_dp_type_dp_size_map[type][size][i[col_name_index_map["street"]]] = []
                        street_dp_type_dp_size_map[type][size][i[col_name_index_map["street"]]].append(i)
                    else:
                        street_dp_type_dp_size_map[type][size][i[col_name_index_map["street"]]].append(i)

        #print(street_dp_type_dp_size_map)

        street_map = {}
        for i in data:
            if i[col_name_index_map["street"]] not in street_map.keys():
                street_map[i[col_name_index_map["street"]]] = []
                street_map[i[col_name_index_map["street"]]].append(i)
            else:
                street_map[i[col_name_index_map["street"]]].append(i)

        #print(street_map)
        #data_available = 0

        #print(data)

        if w.find("派出所") >= 0 or w.find("分局") >= 0:
        #if w.find("派出所") >= 0:
            for type in street_dp_type_dp_size_map.keys():
                wirte_now_row = 0
                type_datas = street_dp_type_dp_size_map[type]

                danwei = "单位名：" + str(w)
                b = "制作单号："
                Tou = ""

                col_width = []

                if w.find("分局") >= 0 and w.find("派") >= w.find("分局"):

                    #data_available = 1
                    #print(w)
                    #if w.find("社区") >= 0:
                    #if len(w) >= 3:
                    if not w[-3:] == "派出所":
                        sheetname = w[w.index("分局")+2:w.index("派出所")+3] + "_" + w[w.index("派出所")+3:]
                    else:
                        sheetname = w[w.index("分局"):w.index("派")]
                        sheetname = sheetname[2:] + "_" + type
                    worksheet = get_worksheet(workbook, sheetname, exist_sheet_name)
                    danwei = "单位名：" + str(w)
                    b = "制作单号："
                    if w.find("广州") >= 0:
                        Tou = "广州市公安局" + type + "生产清单"
                    elif w.find("佛山") >= 0:
                        Tou = "佛山市公安局" + type + "生产清单"
                    else:
                        try:
                            Tou = w[w.index("省") + 1:w.index("市")] + "生产清单"
                        except:
                            Tou = w + "生产清单"
                elif w.find("分局") >= 0 and w.find("分局")==(len(w)-2):
                    #data_available = 1
                    #print(w)

                    sheetname = w[w.index('公安局') + 3: w.index('分局') + 2]
                    sheetname = sheetname + "_" + type
                    worksheet = get_worksheet(workbook, sheetname, exist_sheet_name)
                    danwei = "单位名：" + str(w)
                    b = "制作单号："
                    if w.find("广州") >= 0:
                        Tou = "广州市公安局" + type + "生产清单"
                    elif w.find("佛山") >= 0:
                        Tou = "佛山市公安局" + type + "生产清单"
                    else:
                        try:
                            Tou = w[w.index("省") + 1:w.index("市")] + "生产清单"
                        except:
                            Tou = w + "生产清单"
                else:
                    sheetname = "有错误" + str(w)
                    worksheet = get_worksheet(workbook, "有错误"+str(w), exist_sheet_name)


                # 第一行，标题
                title = "广州市伟圣实业有限公司"
                worksheet.write_merge(wirte_now_row, wirte_now_row, 0, 3, title, OneStyle)
                wirte_now_row += 1
                # 第二行 子标题
                sub_title = "二维码" + type + "门牌送货明细表"
                worksheet.write_merge(wirte_now_row, wirte_now_row, 0, 3, sub_title, OneStyle)
                wirte_now_row += 1
                # 第三行 项目名称，送货单号
                try:
                    projects_name = "项目名称：" + CITY.get_city_name_map()[city] + "门牌制作"
                except:
                    projects_name = "项目名称：门牌制作"
                worksheet.write_merge(wirte_now_row, wirte_now_row, 0, 1, projects_name, ThreeStyle)

                deliver_id = "送货单号"
                worksheet.write(wirte_now_row, 3, deliver_id, ThreeStyle)
                wirte_now_row += 1

                # 第四行，收货单位
                receive_by = "收货单位：" + str(w)
                worksheet.write_merge(wirte_now_row, wirte_now_row, 0, 2, receive_by, ThreeStyle)
                wirte_now_row += 1

                # 第五行，收货单位
                projects_batch = "项目批号："
                produce_id = "生产单号："
                worksheet.write(wirte_now_row, 0, projects_batch, ThreeStyle)
                worksheet.write(wirte_now_row, 3, produce_id, ThreeStyle)
                wirte_now_row += 1

                order_batch = ""
                if kw.get("need_order_batch"):
                    if col_name_index_map.get("order_batch"):
                        try:
                        #order_batch = datas_list[0][col_name_index_map.get("order_batch")]
                            order_batch = list(list(list(street_dp_type_dp_size_map.values())[0].values())[0].values())[0][0][col_name_index_map.get("order_batch")]
                        except:
                            pass
                order_id = ""
                if kw.get("need_order_id"):
                    if col_name_index_map.get("order_id"):
                        #order_id = datas_list[0][col_name_index_map.get("order_id")]
                        try:
                            order_id = list(list(list(street_dp_type_dp_size_map.values())[0].values())[0].values())[0][0][col_name_index_map.get("order_id")]
                        except:
                            pass


                # 第六行，批号，清单号
                batch = "批号：" + order_batch
                list_id = "清单号：" + order_id
                worksheet.write(wirte_now_row, 0, batch, ThreeStyle)
                worksheet.write(wirte_now_row, 3, list_id, ThreeStyle)
                wirte_now_row += 1


                #for size in sorted(street_dp_type_dp_size_map[type].keys()):
                for size in sorted(list(street_dp_type_dp_size_map[type].keys()), reverse=True):


                    GuiGe = "规格：" + size
                    # 规格
                    worksheet.write_merge(wirte_now_row, wirte_now_row,0,3,GuiGe,FourStyle)
                    wirte_now_row += 1

                    #col_width = []
                    # 写标题
                    for i in range(6):
                        if i < 4:
                            worksheet.write(wirte_now_row,i,biaoti[i], content_title_Style)
                        else:
                            if city == "guangzhou":
                                worksheet.write(wirte_now_row, i, biaoti[i], content_title_Style_no_border)
                            elif i == 4:
                                worksheet.write(wirte_now_row, i, "二维码", content_title_Style_no_border)
                            #worksheet.write(wirte_now_row, i, biaoti[i], setStyle(False, border=False))


                    # 写主要内容
                    # 内容是街路巷，门牌号，门牌名称，门牌id，全球唯一码
                    wirte_now_row += 1

                    temp_sum = 0

                    #for street in sorted(street_dp_type_dp_size_map[type][size].keys()):
                    for street in dp_sort.sort_for_1D(list(street_dp_type_dp_size_map[type][size].keys())):

                        # 街路巷
                        worksheet.write_merge(wirte_now_row,
                                              wirte_now_row + len(street_dp_type_dp_size_map[type][size][street]) - 1,
                                              0, 0,
                                              street, content_Style)
                        # 数量
                        worksheet.write_merge(wirte_now_row,
                                              wirte_now_row + len(street_dp_type_dp_size_map[type][size][street]) - 1,
                                              2, 2,
                                              len(street_dp_type_dp_size_map[type][size][street]), content_Style)

                        temp_sum += len(street_dp_type_dp_size_map[type][size][street])
                        #for data_for_street in street_dp_type_dp_size_map[type][size][street]:

                        #print("len(street_dp_type_dp_size_map[type][size][street][0])",len(street_dp_type_dp_size_map[type][size][street][0]))
                        # 如果没有生成门牌纯数字，就生成
                        # if 'dp_num_trans' not in col_name_index_map.keys():
                        #     col_name_index_map['dp_num_trans'] = len(street_dp_type_dp_size_map[type][size][street][0])
                        #     for data_for_street in list(street_dp_type_dp_size_map[type][size][street]):
                        #         data_for_street.append(dp_sort.chinese_to_arabic_with_connection(data_for_street[col_name_index_map['dp_num']]))
                        # # print("len(street_dp_type_dp_size_map[type][size][street][0])",
                        # #       len(street_dp_type_dp_size_map[type][size][street][0]))
                        # # 如果没有生成全球唯一码带门牌名称，就生成
                        # if 'global_id_with_dp_name' not in col_name_index_map.keys():
                        #     col_name_index_map['global_id_with_dp_name'] = len(
                        #         street_dp_type_dp_size_map[type][size][street][0])
                        #     for data_for_street in list(street_dp_type_dp_size_map[type][size][street]):
                        #         data_for_street.append(data_for_street[col_name_index_map['global_id']]+data_for_street[col_name_index_map['dp_name']])
                        #
                        # print("len(street_dp_type_dp_size_map[type][size][street][0])",
                        #       len(street_dp_type_dp_size_map[type][size][street][0]))
                        #for data_for_street in dp_sort.sort_by_dp(list(street_dp_type_dp_size_map[type][size][street]), col_name_index_map['dp_name'], col_name_index_map['dp_num']):

                        if len(list(street_dp_type_dp_size_map[type][size][street])) <= 0:
                            continue
                            #break
                        for data_for_street in dp_sort.sort_by_dp_and_street(list(street_dp_type_dp_size_map[type][size][street]), col_name_index_map['dp_name'],
                                                                  col_name_index_map['dp_num_trans']):

                            # 设置列宽
                            if not col_width:
                                col_width.append(len_byte(data_for_street[col_name_index_map['street']])*1.5)
                                col_width.append(len_byte(data_for_street[col_name_index_map['dp_num']]))
                                col_width.append(10)
                                col_width.append(len_byte(data_for_street[col_name_index_map['dp_name']])*1.5)
                                if city == "guangzhou":
                                    col_width.append(len_byte(data_for_street[col_name_index_map['dp_id']])*1.5)
                                col_width.append(len_byte(data_for_street[col_name_index_map['global_id_with_dp_name']])*1.5)
                            else:
                                if col_width[0] <= len_byte(data_for_street[col_name_index_map['street']])*1.5:
                                    col_width[0] = len_byte(data_for_street[col_name_index_map['street']])*1.5
                                if col_width[1] <= len_byte(data_for_street[col_name_index_map['dp_num']]):
                                    col_width[1] = len_byte(data_for_street[col_name_index_map['dp_num']])
                                # if col_width[2] <= 10:
                                #     col_width[2] = 10
                                if col_width[3] <= len_byte(data_for_street[col_name_index_map['dp_name']])*1.5:
                                    col_width[3] = len_byte(data_for_street[col_name_index_map['dp_name']])*1.5
                                if city == "guangzhou":
                                    if col_width[4] <= len_byte(data_for_street[col_name_index_map['dp_id']])*1.5:
                                        col_width[4] = len_byte(data_for_street[col_name_index_map['dp_id']])*1.5
                                    if col_width[5] <= len_byte(data_for_street[col_name_index_map['global_id_with_dp_name']])*1.5:
                                        col_width[5] = len_byte(data_for_street[col_name_index_map['global_id_with_dp_name']])*1.5
                                else:
                                    if col_width[4] <= len_byte(data_for_street[col_name_index_map['global_id_with_dp_name']])*1.5:
                                        col_width[4] = len_byte(data_for_street[col_name_index_map['global_id_with_dp_name']])*1.5


                            # 门牌号
                            if not data_for_street[col_name_index_map['dp_num_trans']] \
                                or str(data_for_street[col_name_index_map['dp_num_trans']]).lower() == "none" \
                                or str(data_for_street[col_name_index_map['dp_num_trans']]).lower() == "null":
                                worksheet.write(wirte_now_row, 1, dp_sort.chinese_to_arabic_with_connection(data_for_street[col_name_index_map['dp_num']]),
                                                content_Style)
                            else:
                                worksheet.write(wirte_now_row, 1, data_for_street[col_name_index_map['dp_num_trans']],
                                                content_Style)


                            #worksheet.write(wirte_now_row, 1, data_for_street[col_name_index_map['dp_num']], content_Style)
                            # if col_name_index_map.get('exported_produce') :
                            #     # 如果exported_produce >=1 即生成过生产单， 则标黄
                            #     if int(data_for_street[col_name_index_map['exported_produce']]) >= 1:
                            #         worksheet.write(wirte_now_row, 1, data_for_street[col_name_index_map['dp_num_trans']],
                            #                         content_Style_yellow)
                            #     else:
                            #         worksheet.write(wirte_now_row, 1,
                            #                         data_for_street[col_name_index_map['dp_num_trans']],
                            #                         content_Style)
                            # else:
                            #     worksheet.write(wirte_now_row, 1, data_for_street[col_name_index_map['dp_num_trans']],
                            #                     content_Style)
                            #content_align_left_yellow_color_Style

                            # 门牌名称content_left_Style_
                            # worksheet.write(wirte_now_row, 3, data_for_street[col_name_index_map['dp_name']],
                            #                 content_Style)
                            # worksheet.write(wirte_now_row, 3, data_for_street[col_name_index_map['dp_name']],
                            #                 setStyle(False, border=True, horz_Align=xlwt.Alignment.HORZ_LEFT))


                            ''' # 有门牌名称重复的处理 old
                            if dp_name_map[data_for_street[col_name_index_map['dp_name']]] > 1:
                                # 如果有重复，则输出为红色字体
                                worksheet.write(wirte_now_row, 3, data_for_street[col_name_index_map['dp_name']],
                                                content_align_left_red_color_Style)

                                # # 设置为0后只写一次，其余不写
                                # dp_name_map[data_for_street[col_name_index_map['dp_name']]] = 0

                            #elif dp_name_map[data_for_street[col_name_index_map['dp_name']]] == 1:
                            else:
                                worksheet.write(wirte_now_row, 3, data_for_street[col_name_index_map['dp_name']],
                                                content_align_left_Style)
                            '''

                            # 有门牌名称重复的处理
                            #print("data_for_street[col_name_index_map['exported_produce']]",data_for_street[col_name_index_map['exported_produce']])
                            #if len(dp_name_map[data_for_street[col_name_index_map['dp_name']]]["index"]) > 1:
                            #print("dp_name_map",dp_name_map)


                            # 2019-09-11
                            # if not dp_name_map:
                            #     continue
                            if data_for_street[col_name_index_map['dp_name']] == '':
                                worksheet.write(wirte_now_row, 3,
                                                data_for_street[col_name_index_map['dp_name']],
                                                content_align_left_Style)

                            elif dp_name_map[data_for_street[col_name_index_map['dp_name']]]["same"] > 0:
                                # 如果有重复，则输出为红色字体
                                # worksheet.write(wirte_now_row, 3, data_for_street[col_name_index_map['dp_name']],
                                #                 content_align_left_red_color_Style)
                                if col_name_index_map.get('exported_produce') :
                                    # 如果exported_produce >=1 即生成过生产单， 则标黄
                                    if int(data_for_street[col_name_index_map['exported_produce']]) >= 1:
                                        worksheet.write(wirte_now_row, 3, data_for_street[col_name_index_map['dp_name']],
                                                        content_align_left_red_color_yellow_background_Style)
                                    else:
                                        worksheet.write(wirte_now_row, 3,
                                                        data_for_street[col_name_index_map['dp_name']],
                                                        content_align_left_red_color_Style)
                                else:
                                    worksheet.write(wirte_now_row, 3, data_for_street[col_name_index_map['dp_name']],
                                                    content_align_left_red_color_Style)
                                dp_name_map[data_for_street[col_name_index_map['dp_name']]]["same"] = -1

                                # # 设置为0后只写一次，其余不写
                                # dp_name_map[data_for_street[col_name_index_map['dp_name']]] = 0

                            #elif dp_name_map[data_for_street[col_name_index_map['dp_name']]] == 1:
                            #elif dp_name_map[data_for_street[col_name_index_map['dp_name']]]["same"] != -1:
                            else:
                                if dp_name_map[data_for_street[col_name_index_map['dp_name']]]["no_same"] > 0:
                                    # 如果有重复 但是global_id不重复，则输出为红色字体
                                    # worksheet.write(wirte_now_row, 3, data_for_street[col_name_index_map['dp_name']],
                                    #                 content_align_left_red_color_Style)
                                    if col_name_index_map.get('exported_produce'):
                                        # 如果exported_produce >=1 即生成过生产单， 则标黄
                                        if int(data_for_street[col_name_index_map['exported_produce']]) >= 1:
                                            worksheet.write(wirte_now_row, 3,
                                                            data_for_street[col_name_index_map['dp_name']],
                                                            content_align_left_red_color_yellow_background_Style)
                                        else:
                                            worksheet.write(wirte_now_row, 3,
                                                            data_for_street[col_name_index_map['dp_name']],
                                                            content_align_left_red_color_Style)
                                    else:
                                        worksheet.write(wirte_now_row, 3,
                                                        data_for_street[col_name_index_map['dp_name']],
                                                        content_align_left_red_color_Style)


                                    # 2019-06-29
                                    #dp_name_map[data_for_street[col_name_index_map['dp_name']]]["no_same"] = -1
                                elif dp_name_map[data_for_street[col_name_index_map['dp_name']]]["no_same"] != -1:
                                    # worksheet.write(wirte_now_row, 3, data_for_street[col_name_index_map['dp_name']],
                                    #             content_align_left_Style)
                                    if col_name_index_map.get('exported_produce'):
                                        # 如果exported_produce >=1 即生成过生产单， 则标黄
                                        if int(data_for_street[col_name_index_map['exported_produce']]) >= 1:
                                            worksheet.write(wirte_now_row, 3,
                                                            data_for_street[col_name_index_map['dp_name']],
                                                            content_align_left_yellow_background_Style)
                                        else:
                                            worksheet.write(wirte_now_row, 3,
                                                            data_for_street[col_name_index_map['dp_name']],
                                                            content_align_left_Style)
                                    else:
                                        worksheet.write(wirte_now_row, 3,
                                                        data_for_street[col_name_index_map['dp_name']],
                                                        content_align_left_Style)

                            col_index_now = 4
                            if city == "guangzhou":
                                # 门牌ID
                                worksheet.write(wirte_now_row, col_index_now,
                                                data_for_street[col_name_index_map['dp_id']], content_no_border_no_bold)
                                col_index_now += 1
                            else:
                                pass

                            # 全球唯一码
                            #worksheet.write(wirte_now_row, 5, data_for_street[col_name_index_map['global_id_with_dp_name']], content_Style)
                            # worksheet.write(wirte_now_row, 5, data_for_street[col_name_index_map['global_id']],
                            #                 setStyle(False, border=False, horz_Align=xlwt.Alignment.HORZ_LEFT))
                            # worksheet.write(wirte_now_row, col_index_now, data_for_street[col_name_index_map['global_id_with_dp_name']],
                            #                 content_align_left_no_border_Style)
                            if city == "guangzhou":
                                worksheet.write(wirte_now_row, col_index_now,
                                                data_for_street[col_name_index_map['global_id_with_dp_name']],
                                                content_align_left_no_border_Style)
                            elif city == "shaoguan":
                                worksheet.write(wirte_now_row, col_index_now,
                                                data_for_street[
                                                    col_name_index_map['global_id_with_dp_name']][36:]
                                                + "/" + data_for_street[col_name_index_map['global_id_with_dp_name']][:36],
                                                content_align_left_no_border_Style)
                            else:
                                try:
                                    worksheet.write(wirte_now_row, col_index_now,
                                                    data_for_street[col_name_index_map['global_id_with_dp_name']][:36]+"|"+data_for_street[col_name_index_map['global_id_with_dp_name']][36:],
                                                    content_align_left_no_border_Style)
                                except:
                                    worksheet.write(wirte_now_row, col_index_now,
                                                    data_for_street[col_name_index_map['global_id_with_dp_name']],
                                                    content_align_left_no_border_Style)


                            wirte_now_row += 1


                    worksheet.write_merge(wirte_now_row, wirte_now_row, 0, 1, "合计",  content_title_Style)
                    worksheet.write(wirte_now_row, 2, int(temp_sum), content_title_Style)
                    worksheet.write(wirte_now_row, 3, "", content_Style)
                    wirte_now_row += 1

                    worksheet.write(wirte_now_row, 3, "", content_right_border)
                    wirte_now_row += 1

                    worksheet.write(wirte_now_row, 0, "货物接收情况：", ThreeStyle)
                    worksheet.write(wirte_now_row, 3, "", content_right_border)
                    wirte_now_row += 1
                    worksheet.write(wirte_now_row, 3, "", content_right_border)
                    wirte_now_row += 1
                    worksheet.write(wirte_now_row, 3, "", content_right_border)
                    wirte_now_row += 1

                    worksheet.write_merge(wirte_now_row, wirte_now_row, 1, 2, "接收单位签字盖章：", TwoStyle)
                    worksheet.write(wirte_now_row, 3, "", content_right_border)
                    wirte_now_row += 1
                    worksheet.write_merge(wirte_now_row, wirte_now_row, 1, 2, "日期：", TwoStyle)
                    worksheet.write(wirte_now_row, 3, "", content_right_border)
                    wirte_now_row += 1
                    worksheet.write(wirte_now_row, 3, "", content_right_border)
                    wirte_now_row += 1

                    for v in range(3):
                        worksheet.write(wirte_now_row, v, "", content_bottom_border)
                    worksheet.write(wirte_now_row, 3, "", content_bottom_right_border)
                    wirte_now_row += 1


                    if not statistics_datas.get(sheetname):
                        statistics_datas[sheetname] = {}
                    statistics_datas[sheetname][size] = temp_sum

                    #print("statistics_datasstatistics_datasstatistics_datas", statistics_datas)

                    #
                    # for j in range(len(data)):
                    #
                    #     # # 街路巷
                    #     # worksheet.write(5+j, 0, data[j][col_name_index_map['street']], content_Style)
                    #     # 门牌号
                    #     worksheet.write(wirte_now_row, 1, data[j][col_name_index_map['dp_num']], content_Style)
                    #     # # 数量
                    #     # worksheet.write(5+j, 2, len(street_map[data[j][col_name_index_map['street']]]), content_Style)
                    #     # 门牌名称
                    #     worksheet.write(wirte_now_row, 3, data[j][col_name_index_map['dp_name']], content_Style)
                    #     # 门牌ID
                    #     worksheet.write(wirte_now_row, 4, data[j][col_name_index_map['dp_id']], content_Style)
                    #     # 全球唯一码
                    #     worksheet.write(wirte_now_row, 5, data[j][col_name_index_map['global_id_with_dp_name']], content_Style)
                    #
                    #
                    #
                    #     if j == 0:
                    #         col_width.append(len_byte(data[j][col_name_index_map['street']])*2)
                    #         col_width.append(len_byte(data[j][col_name_index_map['dp_num']]))
                    #         col_width.append(10)
                    #         col_width.append(len_byte(data[j][col_name_index_map['dp_name']])*2)
                    #         col_width.append(len_byte(data[j][col_name_index_map['dp_id']]))
                    #         col_width.append(len_byte(data[j][col_name_index_map['global_id_with_dp_name']]))
                    #
                    #         merge_start_index = wirte_now_row
                    #         merge_end_index = wirte_now_row + len(street_map[data[j][col_name_index_map['street']]]) - 1
                    #
                    #         # 街路巷
                    #         worksheet.write_merge(merge_start_index, merge_end_index, 0, 0, data[j][col_name_index_map['street']], content_Style)
                    #         # 数量
                    #         worksheet.write_merge(merge_start_index, merge_end_index, 2, 2, len(street_map[data[j][col_name_index_map['street']]]), content_Style)
                    #
                    #
                    #
                    #     elif merge_end_index + 1 == wirte_now_row:
                    #
                    #
                    #         merge_start_index = wirte_now_row
                    #         merge_end_index = wirte_now_row + len(street_map[data[j][col_name_index_map['street']]]) - 1
                    #
                    #         # 街路巷
                    #         worksheet.write_merge(merge_start_index, merge_end_index, 0, 0, data[j][col_name_index_map['street']], content_Style)
                    #         # 数量
                    #         worksheet.write_merge(merge_start_index, merge_end_index, 2, 2, len(street_map[data[j][col_name_index_map['street']]]), content_Style)
                    #
                    #     wirte_now_row += 1
                    #
                    #     if j == len(data)-1:
                    #         worksheet.write_merge(wirte_now_row, wirte_now_row, 0, 1, "合计", content_Style)
                    #         worksheet.write(wirte_now_row, 2, len(data), content_Style)
                    #         wirte_now_row += 1






                #设置栏位宽度，栏位宽度小于10时候采用默认宽度title_for_repeat_datas
                temp_col_index = 0
                if  col_width[3] < len_byte(danwei):
                    col_width[3] = len_byte(danwei) - (col_width[0] + col_width[1])
                for i in range(len(col_width)):
                    if col_width[i] > 10:
                            worksheet.col(i).width = int(256 * (col_width[i] + 3))

                # tall_style =xlwt.easyxf('font:height 300')
                # worksheet.row(1).set_style(tall_style)

        elif w == '查不到' or w.find('查不到') > 0:
            if "检索不到的数据" in exist_sheet_name:
                worksheet = workbook.get_sheet("检索不到的数据")
            else:
                worksheet = get_worksheet(workbook, "检索不到的数据", exist_sheet_name)
            if w == '查不到':

                # 写标题
                for i in range(6):
                        worksheet.write(1,i,biaoti[i],content_Style)
                for j in range(len(data)):
                    # 门牌名称
                    worksheet.write(2+j, 3, data[j][col_name_index_map['dp_name']], content_Style)
                    if city == "guangzhou":
                        # 门牌ID
                        worksheet.write(2+j, 4, data[j][col_name_index_map['dp_id']], content_Style)
            if w.find('查不到') > 0:
                worksheet.write(0, 0, w, content_Style)


        else:
            worksheet = get_worksheet(workbook, "派出所名称有问题", exist_sheet_name)
            worksheet.write(0, 0, '有问题的派出所名称: '+ str(w), content_Style)
            # 写标题
            for i in range(6):
                worksheet.write(1, i, biaoti[i], content_Style)
            for j in range(len(data)):
                # 门牌名称
                worksheet.write(2 + j, 3, data[j][col_name_index_map['dp_name']], content_Style)
                if city == "guangzhou":
                    # 门牌ID
                    worksheet.write(2 + j, 4, data[j][col_name_index_map['dp_id']], content_Style)
                # 全球唯一码
                worksheet.write(2 + j, 5, data[j][col_name_index_map['global_id']], content_Style)

            #设置栏位宽度，栏位宽度小于10时候采用默认宽度
            # temp_col_index = 0
            # for i in range(len(col_width)):
            #     if col_width[i] > 10:
            #         worksheet.col(i).width = 256 * (col_width[i] + 1)


    # 如果有重复数据，输出
    # print("repeat_datas", repeat_datas)
    # print("len(repeat_datas)",len(repeat_datas))

    temp_col_weight_map = {} # 用来设置列宽

    if len(repeat_datas) > 0 or len(repeat_datas_but_not_same) > 0:
    #if len(repeat_datas) > 0:
        worksheet = get_worksheet(workbook, "重复的数据", exist_sheet_name)
        worksheet.write(0, 0, "下面是重复的数据，如果是空，则是没有", content_Style)
        # 写标题
        title_for_repeat_datas = ["派出所", "社区", "街路巷", "门牌号", "门牌名称", "门牌id", "全球唯一码"]
        for i in range(len(title_for_repeat_datas)):
            worksheet.write(1, i, title_for_repeat_datas[i], content_Style)

        row_sum = 2

        for j in range(len(title_for_repeat_datas)):
            temp_col_weight_map[j] = 15

        for j in range(len(repeat_datas)):
            # 街路巷
            worksheet.write(2 + j, title_for_repeat_datas.index("街路巷"), repeat_datas[j][col_name_index_map['street']], content_Style)
            # 门牌号
            worksheet.write(2 + j, title_for_repeat_datas.index("门牌号"), repeat_datas[j][col_name_index_map['dp_num']], content_Style)
            # 门牌名称
            worksheet.write(2 + j, title_for_repeat_datas.index("门牌名称"), repeat_datas[j][col_name_index_map['dp_name']], content_Style)
            if city=="guangzhou":
                # 门牌ID
                worksheet.write(2 + j, title_for_repeat_datas.index("门牌id"), repeat_datas[j][col_name_index_map['dp_id']], content_Style)
            # 全球唯一码
            worksheet.write(2 + j, title_for_repeat_datas.index("全球唯一码"), repeat_datas[j][col_name_index_map['global_id']], content_Style)

            try:
                # 派出所
                worksheet.write(2 + j, title_for_repeat_datas.index("派出所"), repeat_datas[j][col_name_index_map['pcs']], content_Style)

                # 社区
                worksheet.write(2 + j, title_for_repeat_datas.index("社区"), repeat_datas[j][col_name_index_map['community']], content_Style)
            except:
                print("没有派出所或者社区")

            if len_byte(repeat_datas[j][col_name_index_map['street']]) > temp_col_weight_map[title_for_repeat_datas.index("街路巷")]:
                temp_col_weight_map[title_for_repeat_datas.index("街路巷")] = len_byte(repeat_datas[j][col_name_index_map['street']])

            if len_byte(repeat_datas[j][col_name_index_map['dp_num']]) > temp_col_weight_map[title_for_repeat_datas.index("门牌号")]:
                temp_col_weight_map[title_for_repeat_datas.index("门牌号")] = len_byte(repeat_datas[j][col_name_index_map['dp_num']])

            if len_byte(repeat_datas[j][col_name_index_map['dp_name']]) > temp_col_weight_map[title_for_repeat_datas.index("门牌名称")]:
                temp_col_weight_map[title_for_repeat_datas.index("门牌名称")] = len_byte(repeat_datas[j][col_name_index_map['dp_name']])

            if city == "guangzhou":
                if len_byte(repeat_datas[j][col_name_index_map['dp_id']]) > temp_col_weight_map[title_for_repeat_datas.index("门牌id")]:
                    temp_col_weight_map[title_for_repeat_datas.index("门牌id")] = len_byte(repeat_datas[j][col_name_index_map['dp_id']])

            if len_byte(repeat_datas[j][col_name_index_map['global_id']]) > temp_col_weight_map[title_for_repeat_datas.index("全球唯一码")]:
                temp_col_weight_map[title_for_repeat_datas.index("全球唯一码")] = len_byte(repeat_datas[j][col_name_index_map['global_id']])

            if len_byte(repeat_datas[j][col_name_index_map['pcs']]) > temp_col_weight_map[title_for_repeat_datas.index("派出所")]:
                temp_col_weight_map[title_for_repeat_datas.index("派出所")] = len_byte(repeat_datas[j][col_name_index_map['pcs']])

            if len_byte(repeat_datas[j][col_name_index_map['community']]) > temp_col_weight_map[title_for_repeat_datas.index("社区")]:
                temp_col_weight_map[title_for_repeat_datas.index("社区")] = len_byte(repeat_datas[j][col_name_index_map['community']])


            row_sum = 2+j

        row_sum += 1
        worksheet.write(row_sum, 0, "下面是重复的数据,但全球唯一码不同，如果是空，则是没有", content_Style)
        row_sum += 1
        for j in range(len(repeat_datas_but_not_same)):
            # 街路巷
            worksheet.write(row_sum + j, title_for_repeat_datas.index("街路巷"), repeat_datas_but_not_same[j][col_name_index_map['street']], content_Style)
            # 门牌号
            worksheet.write(row_sum + j, title_for_repeat_datas.index("门牌号"), repeat_datas_but_not_same[j][col_name_index_map['dp_num']], content_Style)
            # 门牌名称
            worksheet.write(row_sum + j, title_for_repeat_datas.index("门牌名称"), repeat_datas_but_not_same[j][col_name_index_map['dp_name']], content_Style)
            if city == "guangzhou":
                # 门牌ID
                worksheet.write(row_sum + j, title_for_repeat_datas.index("门牌id"), repeat_datas_but_not_same[j][col_name_index_map['dp_id']], content_Style)
            # 全球唯一码
            worksheet.write(row_sum + j, title_for_repeat_datas.index("全球唯一码"), repeat_datas_but_not_same[j][col_name_index_map['global_id']], content_Style)

            try:
                # 派出所
                worksheet.write(row_sum + j, title_for_repeat_datas.index("派出所"), repeat_datas_but_not_same[j][col_name_index_map['pcs']], content_Style)

                # 社区
                worksheet.write(row_sum + j, title_for_repeat_datas.index("社区"), repeat_datas_but_not_same[j][col_name_index_map['community']],
                                content_Style)
            except:
                print("没有派出所或者社区")

            #print("temp_col_weight_map", temp_col_weight_map)
            if len_byte(repeat_datas_but_not_same[j][col_name_index_map['street']]) > temp_col_weight_map[title_for_repeat_datas.index("街路巷")]:
                temp_col_weight_map[title_for_repeat_datas.index("街路巷")] = len_byte(repeat_datas_but_not_same[j][col_name_index_map['street']])

            if len_byte(repeat_datas_but_not_same[j][col_name_index_map['dp_num']]) > temp_col_weight_map[title_for_repeat_datas.index("门牌号")]:
                temp_col_weight_map[title_for_repeat_datas.index("门牌号")] = len_byte(repeat_datas_but_not_same[j][col_name_index_map['dp_num']])

            if len_byte(repeat_datas_but_not_same[j][col_name_index_map['dp_name']]) > temp_col_weight_map[title_for_repeat_datas.index("门牌名称")]:
                temp_col_weight_map[title_for_repeat_datas.index("门牌名称")] = len_byte(repeat_datas_but_not_same[j][col_name_index_map['dp_name']])

            if city == "guangzhou":
                if len_byte(repeat_datas_but_not_same[j][col_name_index_map['dp_id']]) > temp_col_weight_map[title_for_repeat_datas.index("门牌id")]:
                    temp_col_weight_map[title_for_repeat_datas.index("门牌id")] = len_byte(repeat_datas_but_not_same[j][col_name_index_map['dp_id']])

            if len_byte(repeat_datas_but_not_same[j][col_name_index_map['global_id']]) > temp_col_weight_map[title_for_repeat_datas.index("全球唯一码")]:
                temp_col_weight_map[title_for_repeat_datas.index("全球唯一码")] = len_byte(repeat_datas_but_not_same[j][col_name_index_map['global_id']])

            if len_byte(repeat_datas_but_not_same[j][col_name_index_map['pcs']]) > temp_col_weight_map[title_for_repeat_datas.index("派出所")]:
                temp_col_weight_map[title_for_repeat_datas.index("派出所")] = len_byte(repeat_datas_but_not_same[j][col_name_index_map['pcs']])

            if len_byte(repeat_datas_but_not_same[j][col_name_index_map['community']]) > temp_col_weight_map[title_for_repeat_datas.index("社区")]:
                temp_col_weight_map[title_for_repeat_datas.index("社区")] = len_byte(repeat_datas_but_not_same[j][col_name_index_map['community']])

        # 设置栏位宽度，栏位宽度小于10时候采用默认宽度
        for i in range(len(title_for_repeat_datas)):

            if i in temp_col_weight_map.keys():
                worksheet.col(i).width = int(256 * (temp_col_weight_map[i]+5))
            else:
                worksheet.col(i).width = int(256 * (20))




    # 统计页
    worksheet = get_worksheet(workbook, "数据统计", exist_sheet_name)

    size_num = 5

    size_list = []
    size_index_map = {}
    size_num_map = {}
    for tilte_name, value in statistics_datas.items():
        if len(value) > size_num:
            size_num = len(value)
        for size, num in value.items():
            if size not in size_list:
                size_list.append(size)

    size_list = sorted(size_list)
    for size in size_list:
        if size not in size_index_map.keys():
            size_index_map[size] = len(size_index_map.keys()) * 2 + len(["工作表序号", "工作表名称"])

    # 写标题
    #title_for_statistics_datas = ["工作表序号", "工作表名称", "规格", "数量", "规格", "数量", "规格", "数量", "规格", "数量", "规格", "数量", "规格", "数量", "规格", "数量", "规格", "数量", "合计"]
    title_for_statistics_datas = ["工作表序号", "工作表名称"] + ["规格", "数量"] * (size_num + 1) + ["合计"]
    # 规格: 600mm*400mm 400mm*300mm 300mm*200mm 180mm*120mm
    row_sum = 0
    for i in range(len(title_for_statistics_datas)):
        worksheet.write(row_sum, i, title_for_statistics_datas[i], content_title_Style)
    row_sum += 1



    temp_sum_sum = 0
    for tilte_name, value in statistics_datas.items():
        # 工作表序号
        worksheet.write(row_sum, title_for_statistics_datas.index("工作表序号"), row_sum, content_Style)
        worksheet.write(row_sum, title_for_statistics_datas.index("工作表名称"), tilte_name, content_Style)
        j = 2
        temp_sum = 0
        # for size, num in value.items():
        temp_size_index = []
        for size in sorted(value):
            num = value[size]
            temp_sum += num
            if size not in size_num_map.keys():
                size_num_map[size] = num
            else:
                size_num_map[size] += num
            temp_size_index.append(size_index_map[size])
            worksheet.write(row_sum, size_index_map[size], size, content_Style)
            j += 1
            worksheet.write(row_sum, size_index_map[size]+1, num, content_Style)
            j += 1
        print("temp_size_indextemp_size_indextemp_size_indextemp_size_index",temp_size_index)
        try:
            j = 2
            while j < title_for_statistics_datas.index("合计"):
                if j not in temp_size_index:
                    worksheet.write(row_sum, j, "", content_Style)
                    j += 1
                    worksheet.write(row_sum, j, "", content_Style)
                    j += 1
                else:
                    j += 2
        except:
            pass

        worksheet.write(row_sum, title_for_statistics_datas.index("合计"), temp_sum, content_Style)
        temp_sum_sum += temp_sum
        row_sum += 1


    for size, index in size_index_map.items():
        worksheet.write(row_sum, index, "规格小计", content_Style)
        worksheet.write(row_sum, index+1, size_num_map[size], content_Style)
    row_sum += 1
    worksheet.write(row_sum, title_for_statistics_datas.index("合计")-1, "所有总数", content_Style)
    worksheet.write(row_sum, title_for_statistics_datas.index("合计"), temp_sum_sum, content_Style)


    # 设置栏位宽度，栏位宽度小于10时候采用默认宽度
    for i in range(len(title_for_statistics_datas)):

        if i == 1:
            worksheet.col(i).width = int(256 * (40))
        else:
            worksheet.col(i).width = int(256 * (15))



    filename_pre, filename_suffix = os.path.splitext(filename)
    # 最后保存
    save_path = os.path.dirname(path) + "/delivered_" + str(filename_pre) + '_' + common.format_ymdhms_time_now_for_filename() +  ".xls"
    #save_path = os.path.dirname(path) + "/produced_" + str(filename_pre) ++ ".xls"

    workbook.save(save_path)
    print("输出文件在：", save_path)

    return save_path

def export(path, filename="", **kw):
    datas_list, col_name_index_map = load_Excel(path)
    #print(datas_list)
    print(col_name_index_map)

    # print(pcs_map)


    save_path = export_excel(datas_list, col_name_index_map, path, filename=filename, **kw)
    return save_path, datas_list, col_name_index_map

if __name__=='__main__':
    #datas_list, col_name_index_map = load_Excel(args.excel)
    #print(datas_list) 
    #print(col_name_index_map)
    pass
    # test

    #print(pcs_map)
    #export_excel(datas_list, col_name_index_map, args.excel)
