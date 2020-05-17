'''
计算MD5
'''
# coding=gbk

import hashlib
import os
import datetime

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
def GetFileMd5_from_file(f):

	myhash = hashlib.md5()

	while True:
		b = f.read(8096)
		if not b:
			break
		myhash.update(b)
	return myhash.hexdigest()

#filepath = input('请输入文件路径：')

# 输出文件的md5值以及记录运行时间
starttime = datetime.datetime.now()
#print (GetFileMd5(filepath))
endtime = datetime.datetime.now()
#print ('运行时间：%ds'%((endtime-starttime).seconds))