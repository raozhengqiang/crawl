# coding:utf-8
from ctypes import *
import requests
import json
import random
import binascii
import os
import logger

class Chaoren():
    def __init__(self):
        self.s = requests.Session()
        self.s.encoding = 'utf-8'
        self.data = {
            'username': '',
            'password': '',
            'softid': '56856',  # 修改为自己的软件id
            'imgid': '',
            'imgdata': ''
        }

    def get_left_point(self):
        try:
            r = self.s.post('http://api2.sz789.net:88/GetUserInfo.ashx', self.data)
            return r.json()
        except requests.ConnectionError:
            return self.get_left_point()
        except:
            return False

    def recv_byte(self, imgdata):
        self.data['imgdata'] = binascii.b2a_hex(imgdata).upper()
        try:
            r = self.s.post('http://api2.sz789.net:88/RecvByte.ashx', self.data)
            res = r.json()
            if res[u'info'] == -1:
                return False
            return r.json()
        except requests.ConnectionError:
            return self.recv_byte(imgdata)
        except:
            return False

    def report_err(self, imgid):
        self.data['imgid'] = imgid
        if self.data['imgdata']:
            del self.data['imgdata']
        try:
            r = self.s.post('http://api2.sz789.net:88/ReportError.ashx', self.data)
            return r.json()
        except requests.ConnectionError:
            return self.report_err(imgid)
        except:
            return False

def getLeftPoint():
    client = Chaoren()
    client.data['username'] = 'jackma123'  # 修改为打码账号
    client.data['password'] = '2001nine'  # 修改为打码密码

    return client.get_left_point()

def getCodeAndId(fileName):
    client = Chaoren()
    client.data['username'] = 'jackma123'  # 修改为打码账号
    client.data['password'] = '2001nine'  # 修改为打码密码
    print(client.data)
    # 查剩余验证码点数
    #print client.get_left_point()

    # 提交识别
    imgpath = fileName # os.path.join(os.path.dirname(__file__), 'captchaNew.png')
    imgdata = open(imgpath, 'rb').read()
    res = client.recv_byte(imgdata)
    print(res[u'result'])  # 识别结果

    # 当验证码识别错误时,报告错误
    print(res[u'imgId'])
    return res[u'result'], res[u'imgId']

def reportError(imgId):
    client = Chaoren()
    client.data['username'] = 'jackma123'  # 修改为打码账号
    client.data['password'] = '2001nine'  # 修改为打码密码

    client.report_err(imgId)


# test
if __name__ == '__main__':
    client = Chaoren()
    client.data['username'] = 'jackma123'  # 修改为打码账号
    client.data['password'] = '2001nine'  # 修改为打码密码
    print (client.data)
    # 查剩余验证码点数
    print (client.get_left_point())

    # 提交识别
    imgpath = os.path.join(os.path.dirname(__file__), 'captchaNew.png')
    imgdata = open(imgpath, 'rb').read()
    res = client.recv_byte(imgdata)
    print(res[u'result'])  # 识别结果

    # 当验证码识别错误时,报告错误
    print (res[u'imgId'])
    # report_err(reuslt[u'imgId'])
