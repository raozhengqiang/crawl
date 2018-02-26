import chaorendamaUtils
from selenium import webdriver
from PIL import Image
import time
import utils
import random
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
#import chaorendamaUtils
import logger
import datetime
import sys

import redis
reCli = redis.StrictRedis(host='54.223.113.29', password='redis2017', port=16379, db=0)

gStartTime = time.time()

baseData ='C:/Users/raozhengqiang/Desktop/爬虫/img/'

dcap = dict(DesiredCapabilities.PHANTOMJS)
dcap["phantomjs.page.settings.userAgent"] =random.choice(utils.user_agent_list)
dcap['Accept'] = 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'
dcap['Accept-Language']='en-US,en;q=0.5'
dcap['Accept-Encoding']='deflate'
dcap['executable_path']='/usr/local/bin/phantomjs'

driver = webdriver.PhantomJS(executable_path=r'C:\Users\raozhengqiang\python\phantomjs-2.1.1-windows\bin\phantomjs.exe', desired_capabilities=dcap)
# driver = webdriver.Firefox()

driver.set_page_load_timeout(20)
driver.set_script_timeout(20)

serverIp = 'http://shixin.court.gov.cn' #202.102.85.92
imgurl = 'http://shixin.court.gov.cn/index_new.html'


def Crawler():
    driver.get(imgurl)

    frame = driver.find_element_by_name("myYanzmNew")

    pos1 = frame.location
    #print(driver.page_source)
    driver.switch_to_frame('myYanzmNew')
    #print(pos1)
    str1 = driver.page_source
    #print(str1)
    #with open(baseData + 'webpages/' + str(random.randint(1000, 9999)), 'a+') as f:
        #f.write(str1)
    #print(str1)

    #captchaNew.do?captchaId=e19442c25e1046e880d1fd56e1921574&amp
    startStr = 'src=\'captchaNew.do?captchaId='
    startIndex = str1.index(startStr)
    #print(startIndex)
    endIndex = str1.index('&amp', startIndex)

    captchId = str1[startIndex + len(startStr) : endIndex]

    imgcacph = driver.find_element_by_id('captchaImg')
    size = imgcacph.size
    #print(size)
    xpos = pos1['x'] + imgcacph.location['x']
    ypos = pos1['y'] + imgcacph.location['y']
    driver.save_screenshot("screenshot.png")
    im = Image.open('screenshot.png')
    left = xpos
    top = ypos
    right = left + size['width']
    bottom = top + size['height']
    im = im.crop((left, top, right, bottom))  # defines crop points
    #im.save('img.png')  # saves new cropped image
    #im.show()


    #这个为utils中的函数
    dateStr = datetime.datetime.now().strftime("%Y%m%d%H%M-")
    randomStr1 = str(random.randint(1000,9999))
    randomStr=randomStr1+dateStr+'_'
    #print(randomStr)
    imgFilename = baseData+'unLabeledimages/'+randomStr +'.png'
    im.save(imgFilename)

    #这个来自chaorendamaUtils函数
    captcha, imgId = chaorendamaUtils.getCodeAndId(imgFilename)#处理得到的图
    #print(captcha)
    #print(imgId)
    logger.info('captcha code: %s, imgId: %s' % (captcha, imgId))
        

    imgLabeledPath =baseData +'LabelImages/'+randomStr+captcha+'.png'

    timecost=10

    if len(captcha)!=4:
        checkBool=False
        chaorendamaUtils.reportError(imgId)
        logger.warn("report captcha error: %s, %s, %s" % (imgFilename, imgId, captcha))

    else:
        startTime = time.time()
        checkBool = checkCaptcha(driver, captcha, captchId)
        timecost = time.time() - startTime
        print(timecost)

    if checkBool == False:
        logger.warn(" check failed, imgId: %s, fileName:%s" % (imgId, imgFilename))

    else:
        im.save(imgLabeledPath)
        logger.info("Check passs: fileName: %s, code: %s" % (imgFilename, captcha))

    

    return driver, captcha, captchId, checkBool



def checkCaptcha(driver,captcha,captchId):
    if 'quit' in captcha:
        return False
    detailUrl = serverIp + '/disDetailNew?id=10246055&pCode=' + captcha + '&captchaId=' + captchId
    driver.get(detailUrl)
    print(driver.page_source)

    if 'caseCode' in driver.page_source:
        print('------------------------------check pass----------------------')
        print(driver.page_source)
        return  True
    print('--------4-----------------check captcha failed -------------------')
    return False
totalnum=0
totalcnt = 0#计算的id总数
totalerr=0#总的错误数

totalImg = 0#总的图片数

totalSucc = 0#总的成功数
conseqErr=0#结果错误数
nodatacnt=0#id没有记录的总数
def getDetail(driver, captcha, captchId, id):
    global  totalcnt
    global  totalerr
    global  nodatacnt
    global  totalnum
    totalcnt+=1
    detailUrl = serverIp + '/disDetailNew?id=' + str(id) + '&pCode=' + captcha + '&captchaId=' + captchId
    print(detailUrl)
    driver.get(detailUrl)
    logger.info("url: %s"%detailUrl)

    if len(driver.page_source) < 2000:
        logger.info("content: %s"%driver.page_source)
    else:
        logger.info("get main page")

    if 'caseCode' in driver.page_source and '点击重新获取验证码' not in driver.page_source:
        nodatacnt = 0
        with open(baseData + utils.getResultFileName()+'_shixin.txt', 'a+') as f:
            f.write(driver.page_source + '\n')
        with open(baseData+'_id.txt','a+') as f:
            f.write(str(id)+'\n')
        totalnum+=1

    else:
        totalerr += 1
        nodatacnt += 1

    if '网站当前访问量较大，请输入验证码后继续访问' in driver.page_source:
        return False

    else:
        return True
    

#以下为显示数目函数
def printstat():
    logger.info("Total cnt: %d" % totalcnt)
    logger.info("total error：%d" % totalerr)
    logger.info("Total image: %d" % totalImg)
    logger.info("total success：%d" % totalSucc)



oldValue = [0,0,0,0,0,0]
#以下为跟新数组函数
def updateMetrics():
    global oldValue
    shixinMetrics = ['statshixintotalcnt', 'statshixintotalimg', 'statshixintotalsuccimg', 'statshixintotalerror','statshixinTotalTimeCost', 'statshixinDownloadCnt']
    #valueStr=[计算的总id数,总的图片数,id有效的数目，总的错误数,
    valueStr = [totalcnt, totalImg, totalSucc, totalerr, time.time() - gStartTime, totalcnt - totalerr]

    for i in range(len(shixinMetrics)):
        keyStr = shixinMetrics[i]
        #取出原先存储在keyStr中的值存入oldStr
        oldStr = reCli.get(keyStr)
        
        #计算新的value值
        newValue = valueStr[i] - oldValue[i]
        #将老的数值存入
        oldValue[i] = valueStr[i]

        if oldStr is not None:
            newValue += float(oldStr)
        reCli.set(keyStr, newValue)

maxruntime = 200000000000000#最多运行15分钟sleep
shixinIndexTag = 'shixinIndex'

def process():
    global totalcnt
    global totalImg
    global totalSucc
    global conseqErr
    global nodatacnt

    maxcnt=100000#设置最大的计数值

    startId=700596450#(reCli.get(shixinIndexTag))#id号从200万开始
    #print(reCli.get(shixinIndexTag))

    logger.info("begin new session.....")
    logger.info("start indes: %s"%startId)
    
    while True:
        printstat()

        if time.time() - gStartTime > maxruntime:#达到了最大运行时间
            logger.warn('run over %d seconds, so stop program now'%maxruntime)
            break

        if totalcnt > maxcnt:
            logger.info("over %d record, stop programm....."%maxcnt)
            break

        if conseqErr > 5 :
            logger.error("too many consequence error, stop now: %d"%conseqErr)
            break

        if totalSucc > 1 and totalcnt < 50:
            logger.error("server too slow, stop programm now.......")
            break

        totalImg += 1

        try:
            driver, captcha, captchId, checkBool = Crawler()#获取驱动，验证码，验证码的id，以及检测是否有用
        except:
            logger.error(sys.exc_info())
            checkBool = False
            captcha = 'wrong'

        startTime = time.time()

        if captcha.find('quit') != -1:
            print('quit...')
            break

        if checkBool == False:#检测代码是否出错
            logger.warn("code is incorrect:%s"%captcha)
            conseqErr+=1

            if conseqErr > 3:
                sleepTime = conseqErr * 10#如果代码测试的错误数量超过3，则进行睡眠
                logger.info('conseq erro：%d, sleep(s): %d'%(conseqErr,sleepTime))
                time.sleep(sleepTime)

            time.sleep(3)
            continue

        #经过以上步骤全部完成后，则说明代码可以进行下一步的工作
        totalSucc += 1
        conseqErr = 0
        
        #以上的代码是为了检测是否可以获取验证码，并成功搜索
        while True:
            endTime = time.time()

            if endTime - startTime > 180:
                print('refresh image')
                break

            if time.time() - gStartTime > maxruntime:
                logger.warn('run over %d seconds, so stop program now' % maxruntime)
                break

            logger.info("get detail info: %s"%startId)

            retbo = False

            try:
                retbo = getDetail(driver, captcha, captchId, startId)

            except:
                logger.error(sys.exc_info())

            if retbo == False:
                break

            startId+=1#reCli.incr(shixinIndexTag)
            
            if nodatacnt > 50:
                nodatacnt = 0
                startId += 500

            time.sleep(0.3)

    logger.info(chaorendamaUtils.getLeftPoint())
    printstat()

process()

print('total: ', totalcnt)
print('error: ', totalerr)
print('done')
#print(reCli.get(shixinIndexTag))

driver.close()
driver.quit()

            
                            


        














    
