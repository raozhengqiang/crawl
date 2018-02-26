import sys
from selenium import webdriver
from PIL import Image
import time
import utils
import random
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
import  chaorendamaUtils
# from logger import logger
import datetime

import logging
logger = logging.getLogger('root')
FORMAT = "[%(filename)s: %(lineno)s - %(funcName)20s()] %(message)s"
logging.basicConfig(format=FORMAT)
logger.setLevel(logging.DEBUG)

gStartTime = time.time()

#settings:
baseData = 'C:/Users/raozhengqiang/Desktop/爬虫/img/'
#baseData='/root/python/data_zhixing/'
#baseData='/crawler/data_zhixing/'



zhixingIndexTag = 'zhixingIndexNew' #'zhixingIndex'

import redis
reCli = redis.StrictRedis(host='54.223.113.29', password='redis2017', port=46379, db=0)

dcap = dict(DesiredCapabilities.PHANTOMJS)
dcap["phantomjs.page.settings.userAgent"] = random.choice(utils.user_agent_list)

dcap['Accept'] = 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'
dcap['Accept-Language']='zh-CN,zh;q=0.8,en;q=0.6,zh-TW;q=0.4,fr;q=0.2' #'en-US,en;q=0.5'
dcap['Accept-Encoding']='deflate'
dcap['X-Requested-With'] = 'XMLHttpRequest'

driver = webdriver.PhantomJS(executable_path=r'C:\Users\raozhengqiang\python\phantomjs-2.1.1-windows\bin\phantomjs.exe', desired_capabilities=dcap)
driver.set_page_load_timeout(10)
driver.set_script_timeout(10)

serverIp = 'http://zhixing.court.gov.cn' #202.102.85.92
imgurl = 'http://zhixing.court.gov.cn/search/'



def Crawler():
    driver.get(imgurl)
    #print(driver.page_source)

    if '网站当前访问量较大，请输入验证码后继续访问' in driver.page_source:
        return  False

    frame = driver.find_element_by_name("myYanzm")

    pos1 = frame.location
    driver.switch_to_frame('myYanzm')

    str1 = driver.page_source
    #print(str1)
    startStr = 'src=\'captcha.do?captchaId='
    startIndex = str1.index(startStr)
    endIndex = str1.index('&amp', startIndex)
    captchId = str1[startIndex + len(startStr) : endIndex]
    #print(cpatchId)

    imgcacph = driver.find_element_by_id('captchaImg')
    size = imgcacph.size

    xpos = pos1['x'] + imgcacph.location['x']
    ypos = pos1['y'] + imgcacph.location['y']
    #print(size)
    #print(xpos)
    #print(ypos)

    driver.save_screenshot("screenshot_zhixing.png")
    im = Image.open('screenshot_zhixing.png')
    
    
    left = xpos
    top = ypos
    right = left + size['width']
    bottom = top + size['height']
    #left = 807 
    #right = left + 64
    im = im.crop((left, top, right, bottom))
    
    im.save('img_zhixing.png') # saves new cropped image
    

    randomStr = utils.getImageRandomName() +'_'

    imgFilename = baseData + 'unLabeledimages1/' +  randomStr  + '.png'
    im.save(imgFilename)

    captcha, imgId = chaorendamaUtils.getCodeAndId(imgFilename)
    logger.info('captcha code: %s, imgId: %s' % (captcha,imgId))
    imgLabeledPath = baseData + 'LabelImages1/' +  randomStr + captcha + '.png'
    timecost = 10
    
    if len(captcha) != 4:
        checkBool = False
        chaorendamaUtils.reportError(imgId)
        logger.warn("report captcha error: %s, %s, %s" % (imgFilename, imgId, captcha))
    
    else:
        startTime = time.time()
        checkBool = checkCaptcha(driver, captcha,captchId)
        timecost = time.time() - startTime
    if checkBool == False:
        logger.warn(" check failed, imgId: %s, fileName:%s" % (imgId, imgFilename))
    else:
        im.save(imgLabeledPath)
        logger.info("Check passs: fileName: %s, code: %s" % (imgFilename, captcha))
    return driver, captcha, captchId, checkBool


#检查验证码
def checkCaptcha(driver, captcha, captchId):
    if 'quit' in captcha:
        return  False

    detailUrl = serverIp + '/search/newdetail?id=327271&j_captcha=' + captcha + '&captchaId=' + captchId
    print('detail url: ', detailUrl)

    driver.get(detailUrl)
    print(driver.page_source)

    if 'caseCode' in driver.page_source:
        print('------------------------------check pass----------------------')
        #print driver.page_source
        return  True

    print('-------------------------check captcha failed -------------------')
    return False

totalcnt = 0
totalerr = 0
totalImg = 0
totalSucc = 0
conseqErr = 0
nodatacnt=0

def getDetail(driver, captcha, captchId, id):
    global  totalcnt
    global  totalerr
    global  nodatacnt

    totalcnt += 1

    detailUrl = serverIp + '/search/newdetail?id=' + str(id) + '&j_captcha=' + captcha + '&captchaId=' + captchId
    print(detailUrl)

    try:
        driver.get(detailUrl)
    except:
        logger.error("get excpetion ")

    #print(driver.page_source)
    logger.info("url: %s"%detailUrl)
    if len(driver.page_source) < 2000:
        logger.info("content: %s"%driver.page_source)
    else:
        logger.info("get main page")

    if 'caseCode' in driver.page_source:
        # mqHelper.produce(driver.page_source)
        nodatacnt=0
        f=open(baseData + '执行文件/'+utils.getResultFileName()+'_zhixing.txt', 'a+',encoding="utf-8")
        f.write(driver.page_source + '\n')
    else:
        totalerr += 1
        nodatacnt+=1

    if '网站当前访问量较大，请输入验证码后继续访问' in driver.page_source:
        logger.info("'网站当前访问量较大，请输入验证码后继续访问'")
        return  False
    else:
        return  True


def printstat():
    logger.info("Total cnt: %d" % totalcnt)
    logger.info("total error：%d" % totalerr)
    logger.info("Total image: %d" % totalImg)
    logger.info("total success：%d" % totalSucc)

oldValue = [0,0,0,0,0,0]
'''
def updateMetrics():
    zhixingMetrics = ['statzhixingtotalcnt', 'statzhixingtotalimg', 'statzhixingtotalsuccimg', 'statzhixingtotalerror',
                      'statzhixingTotalTimeCost', 'statzhixingDownloadCnt']

    valueStr = [totalcnt, totalImg, totalSucc, totalerr, time.time() - gStartTime, totalcnt - totalerr]

    for i in range(len(zhixingMetrics)):
        keyStr = zhixingMetrics[i]
        oldStr = reCli.get(keyStr)

        newValue = valueStr[i] - oldValue[i]
        oldValue[i] = valueStr[i] #save old value here

        if oldStr is not None:
            newValue += float(oldStr)
        reCli.set(keyStr, newValue)
'''

stopFlag = False
maxruntime = 8000 #最多运行15分钟后sleep，启动新进程
def process():
    global  totalcnt
    global  totalImg
    global  totalSucc
    global  conseqErr
    global  stopFlag
    global  nodatacnt

    maxcnt = 10000

    startId = reCli.get("zhixingIndexTag")

    logger.info("begin new session.....")
    logger.info("start indes: %s"%startId)

    logger.info(chaorendamaUtils.getLeftPoint())

    while True:
        printstat()
        #updateMetrics()

        if totalcnt > maxcnt:
            logger.info("over %d record, stop programm....."%maxcnt)
            break

        if stopFlag:
            logger.error("stop flag is true, stop now....")
            break

        if time.time() - gStartTime > maxruntime:
            logger.warn('run over %d seconds, so stop program now'%maxruntime)
            break

        

        if conseqErr > 10:
            logger.error("too many consequence error, stop now, error times: %d"%conseqErr)
            break

        if totalSucc > 3 and totalcnt/totalSucc < 50:
            logger.error("server too slow, stop programm now.......")
            break

        totalImg += 1

        try:
            driver, captcha, captchId, checkBool = Crawler()
        except:
            logger.error(sys.exc_info())

            checkBool = False #can't get webpage, mark it as check captcha false, sleep some time
            captcha = 'wrong'

        startTime = time.time()

        if captcha.find('quit') != -1:
            print('quit...')
            break

        if checkBool == False:
            logger.warn("code is incorrect:%s"%captcha)
            conseqErr += 1

            time.sleep(3)
            continue

        totalSucc += 1
        conseqErr = 0
        while True:
            endTime = time.time()

            if endTime - startTime > 180:
                print('refresh image')
                break
            logger.info("get detail info: %s"%startId)

            retBo = getDetail(driver, captcha, captchId, startId)
            if retBo is False:
                stopFlag = True
                break

            #startId+=1
            startId = reCli.incr("zhixingIndexTag")
            print(startId)

            
            if nodatacnt > 50:
                nodatacnt = 0
                startId += 500
                reCli.set("zhixingIndexTag",startId)

            time.sleep(0.6)

            #if int(startId) % (maxcnt / 20) == 0:
                #updateMetrics()

            

    logger.info(chaorendamaUtils.getLeftPoint())
    printstat()

process()

print('total: ', totalcnt)
print('error: ', totalerr)
print('done')
#print(reCli.get(shixinIndexTag))

driver.close()
driver.quit()















