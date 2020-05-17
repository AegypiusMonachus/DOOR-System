# 门牌名称排序

import enum
import re
import copy

CN_NUM = {
	'〇': 0, '一': 1, '二': 2, '三': 3, '四': 4, '五': 5, '六': 6, '七': 7, '八': 8, '九': 9, '零': 0,
	'壹': 1, '贰': 2, '叁': 3, '肆': 4, '伍': 5, '陆': 6, '柒': 7, '捌': 8, '玖': 9, '貮': 2, '两': 2,
}

CN_UNIT = {
	'十': 10,
	'拾': 10,
	'百': 100,
	'佰': 100,
	'千': 1000,
	'仟': 1000,
	'万': 10000,
	'萬': 10000,
	'亿': 100000000,
	'億': 100000000,
	'兆': 1000000000000,
}


class CN(enum.IntEnum):
	〇,一,二,三,四,五,六,七,八,九,十 = range(11)

	@classmethod
	def has_value(cls, value):
		return any(value == item.value for item in cls)
	@classmethod
	def has_key(cls, key):
		return any(key == item.name for item in cls)
	@classmethod
	def key_index(cls, s):
		temp_s = str(s)
		# for item in cls:
		# 	temp_index = temp_s.find(item.name)
		# 	if temp_index >= 0:
		# 		return temp_index
		temp_index = 0
		for item in temp_s:
			if CN.has_key(item):
				return temp_index
			temp_index += 1
		return -1
	@classmethod
	def str_to_value(cls, s):
		temp_s = str(s)
		temp_str = ''
		index = 0
		for i in temp_s:
			if CN.has_key(i):
				if i == '十' and len(temp_str) > 0:
					if index == len(temp_s) -1:
						temp_str = temp_str[0:-1] + str(int(temp_str) * 10) + '0'
					elif CN.has_key(temp_s[index + 1]) == False:
						temp_str = temp_str[0:-1] + str(int(temp_str) * 10) + '0'
					else:
						temp_str = temp_str[0:-1] + str(int(temp_str) * 10)
				else:
					temp_str += str(cls[i].value)
			index += 1

		if temp_str.isdigit():
			temp_str = int(temp_str)
		else:
			temp_str = 0
		return temp_str

# 返回str中的数字, 无则为0
def str_to_num(s):

	temp_str = ''
	digit_index_list = []
	digit_index_start = -1
	digit_index_end = -1
	index = 0
	alphabet_list = [] # 字母列表，如果s中有字母就添加进来

	length = 6 # 每段数字 转化后的默认长度 例如length为6时， 1 -> 000001

	# 将 默认每段数字 转成 长度为length的数字
	if s.isdigit():
		digit_index_list.append((0, len(s)))
	else:
		for i in s:
			if i.islower() or i.isupper():
				alphabet_list.append(i)
			if i.isdigit() and digit_index_start == -1:
				digit_index_start = index
				if index == len(s) - 1:
					digit_index_end = index + 1
					digit_index_list.append((digit_index_start, digit_index_end))
					digit_index_start = -1
					digit_index_end = -1
			elif i.isdigit() == False and digit_index_start >= 0:
				digit_index_end = index
				digit_index_list.append((digit_index_start, digit_index_end))
				digit_index_start = -1
				digit_index_end = -1
			index += 1
	for i in digit_index_list:
		for j in range(length - (i[1] - i[0])):
			temp_str += '0'
		temp_str += s[i[0]:i[1]]


	# 将中文数字转成数字，长度默认为len
	for i in range(length - len(str(CN.str_to_value(s)))):
			temp_str += '0'
	temp_str += str(CN.str_to_value(s))

	# 添加上 英文字母
	for i in alphabet_list:
		temp_str += i

	return temp_str

# 返回str中的数字, 无则为0
def str_to_num_new(s):

	temp_str = ''
	digit_index_list = []
	index = 0
	alphabet_list = [] # 字母列表，如果s中有字母就添加进来

	length = 6 # 每段数字 转化后的默认长度 例如length为6时， 1 -> 000001

	# 将 默认每段数字 转成 长度为length的数字
	#print(s)
	if not s:
		temp_str += '0'
	else:
		if s.isdigit():
			digit_index_list.append(s)
		else:
			for i in s.split('-'):

				if i.islower() or i.isupper():
					alphabet_list.append(i)
				if i.isdigit():
					digit_index_list.append(i)
				elif i.isdigit() == False:
					digit_index_list.append(i)

		for i in digit_index_list:
			for j in range(length - len(i)):
				temp_str += '0'
			temp_str += str(i)
		# 添加上 英文字母
		for i in alphabet_list:
			temp_str += i
		#print(temp_str)
	return temp_str


# 返回值是 纯数字
def chinese_to_arabic(cn: str) -> int:
	unit = 0  # current
	ldig = []  # digest
	begin_index = -1
	end_index = -1
	index = 0
	for cndig in list(cn):
		if cndig in CN_UNIT or cndig in CN_NUM:
			if begin_index == -1:
				begin_index = index
			end_index = index + 1
		index += 1
	# print ("begin_index", begin_index)
	# print ("end_index", end_index)

	for cndig in reversed(cn):
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
	return val

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
			if index == len(list(cn)) - 1:
				index_map[begin_index] = len(list(cn))
		elif begin_index != end_index:
			end_index = index
			index_map[begin_index] = end_index
			begin_index = end_index
		index += 1

	#print(cn)
	# print ("begin_index", begin_index)
	# print ("end_index", end_index)
	# print (index_map)

	need_cut = 0
	for key, value in index_map.items():
		# print(key, value)
		key = key - need_cut
		value = value - need_cut
		# print(key, value)
		unit = 0  # current
		ldig = []  # digest
		#temp_cn = copy.deepcopy(cn[key:value])
		temp_cn = temp_cn = cn[key:value]

		# print(temp_cn)

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
		# return val, begin_index, end_index

		# print(val)
		# print(cn[key:value])

		if key >= 0:
			# i[1] = i[1].replace(i[1][begin:end], str(num))
			cn = cn.replace(cn[key:value], str(val), 1)
		# print (cn)

		if (value - key) != len(str(val)):
			need_cut += (value - key) - len(str(val))

	# i[1] = '-'.join(re.findall(r"\d+\.?\d*",i[1]))

	return ('-'.join(re.findall(r"\d+\.?\d*", cn)))
'''

# "102号之5" -> 102-5
# "102号之五" -> 102-5
# version 2.0  "102号之一零一" -> 102-101
def chinese_to_arabic_with_connection(cn: str) -> str:
	has_CN_UNIT_sign = 0
	temp_cn = copy.deepcopy(cn)

	# print ("cn", cn)

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
			if index == len(list(cn)) - 1:
				index_map[begin_index] = len(list(cn))
		elif begin_index != end_index:
			end_index = index
			index_map[begin_index] = end_index
			begin_index = end_index
		index += 1

	# print (cn)
	# print ("begin_index", begin_index)
	# print ("end_index", end_index)
	# print (index_map)

	need_cut = 0
	for key, value in index_map.items():
		# print(key, value)
		key = key - need_cut
		value = value - need_cut

		# print(key, value)
		unit = 0  # current
		ldig = []  # digest
		# temp_cn = copy.deepcopy(cn[key:value])

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
				temp_list_cn[key + temp_index] = i
				temp_index += 1
			cn = "".join(temp_list_cn)
		# print ("cn_step_temp", cn)

		else:
			# print(temp_cn)

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
			# return val, begin_index, end_index

			# print(val)
			# print(cn[key:value])

			if key >= 0:
				# i[1] = i[1].replace(i[1][begin:end], str(num))
				cn = cn.replace(cn[key:value], str(val), 1)
			# print (cn)

			if (value - key) != len(str(val)):
				need_cut += (value - key) - len(str(val))

	# i[1] = '-'.join(re.findall(r"\d+\.?\d*",i[1]))

	return ('-'.join(re.findall(r"\d+\.?\d*", cn)))

# # 注意！传进去的datas是二维list，
# # village_col、road_col、doorplate_col表示派出所名称或社区名称、路名、门牌号码所在的列下标index
# def sort(datas, village_col, road_col, doorplate_col):
# 	#print(datas)
# 	if datas:
# 		# datas.sort(key=lambda i: (
# 		# 	i[village_col], i[road_col][0:CN.key_index(i[road_col])] if CN.key_index(i[road_col]) >= 0 else str(i[road_col]),
# 		# 	CN.str_to_value(i[road_col]), str_to_num(i[doorplate_col])))
# 		datas.sort(key=lambda i: (
# 			i[village_col], i[road_col][0:CN.key_index(i[road_col])] if CN.key_index(i[road_col]) >= 0 else str(i[road_col]),
# 			chinese_to_arabic(i[road_col]), str_to_num(i[doorplate_col])))
# 		return datas
# 	else:
# 		return []

# 注意！传进去的datas是二维list，
# village_col、road_col、doorplate_col表示派出所名称或社区名称、路名、门牌号码所在的列下标index
def sort(datas, village_col, road_col, doorplate_col):
	#print(datas)
	if datas:
		# datas.sort(key=lambda i: (
		# 	i[village_col], i[road_col][0:CN.key_index(i[road_col])] if CN.key_index(i[road_col]) >= 0 else str(i[road_col]),
		# 	CN.str_to_value(i[road_col]), str_to_num(i[doorplate_col])))


		# datas.sort(key=lambda i: (
		# 	str(i[village_col]), i[road_col][0:CN.key_index(i[road_col])] if CN.key_index(i[road_col]) >= 0 else str(i[road_col]),
		# 	chinese_to_arabic(str(i[road_col])), str_to_num_new(i[doorplate_col])))


		# 用chinese_to_arabic_with_connection,如果有bug 用回chinese_to_arabic
		datas.sort(key=lambda i: (
			str(i[village_col]),
			i[road_col][0:CN.key_index(i[road_col])] if CN.key_index(i[road_col]) >= 0 else str(i[road_col]),
			chinese_to_arabic_with_connection(str(i[road_col])), str_to_num_new(i[doorplate_col])))

		return datas
	else:
		return []

# 一维排序
def sort_for_1D(datas):
	#print(datas)
	if datas:
		# datas.sort(key=lambda i: (
		# 	i[village_col], i[road_col][0:CN.key_index(i[road_col])] if CN.key_index(i[road_col]) >= 0 else str(i[road_col]),
		# 	CN.str_to_value(i[road_col]), str_to_num(i[doorplate_col])))

		# datas.sort(key=lambda i: (i[0:CN.key_index(i)] if CN.key_index(i) >= 0 else str(i),
		# 						  chinese_to_arabic(i), str_to_num(i)))


		# 用chinese_to_arabic_with_connection,如果有bug 用回chinese_to_arabic
		datas.sort(key=lambda i: (i[0:CN.key_index(i)] if CN.key_index(i) >= 0 else str(i),
								  str_to_num_new(chinese_to_arabic_with_connection(i))))
		# datas.sort(key=lambda i: (i[0:CN.key_index(i)] if CN.key_index(i) >= 0 else str(i),
		# 						  chinese_to_arabic_with_connection(str(i))))
		#datas.sort(key=lambda i: (chinese_to_arabic_with_connection(str(i))))
		return datas
	else:
		return []

# 注意！传进去的datas是二维list，
# village_col、road_col、doorplate_col表示派出所名称或社区名称、路名、门牌号码所在的列下标index
def sort_by_dp(datas, doorplate_col):
	# print(datas)
	if datas:
		# datas.sort(key=lambda i: (
		# 	i[village_col], i[road_col][0:CN.key_index(i[road_col])] if CN.key_index(i[road_col]) >= 0 else str(i[road_col]),
		# 	CN.str_to_value(i[road_col]), str_to_num(i[doorplate_col])))
		datas.sort(key=lambda i: (chinese_to_arabic(i[doorplate_col]), str_to_num(i[doorplate_col])))
		return datas
	else:
		return []


# 注意！传进去的datas是二维list，
# village_col、road_col、doorplate_col表示派出所名称或社区名称、路名、门牌号码所在的列下标index
def sort_by_dp_and_street(datas, road_col, doorplate_col):
	# print(datas)
	if datas:
		# datas.sort(key=lambda i: (
		# 	i[village_col], i[road_col][0:CN.key_index(i[road_col])] if CN.key_index(i[road_col]) >= 0 else str(i[road_col]),
		# 	CN.str_to_value(i[road_col]), str_to_num(i[doorplate_col])))
		#datas.sort(key=lambda i: (str_to_num(i[doorplate_col]),  i[road_col][0:CN.key_index(i[road_col])] if CN.key_index(i[road_col]) >= 0 else str_to_num(i[road_col])))
		# datas.sort(key=lambda i: (
		# 	i[road_col][0:CN.key_index(i[road_col])] if CN.key_index(i[road_col]) >= 0 else "", str_to_num_new(i[doorplate_col])))
		datas.sort(key=lambda i: (str_to_num_new(i[doorplate_col])))
		return datas
	else:
		return []


