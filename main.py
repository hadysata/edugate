import requests
import re
from bs4 import BeautifulSoup
from time import sleep
import json
from pathlib import Path

target = "https://edugate.ksu.edu.sa/ksu/ui/guest/timetable/index/scheduleTreeCoursesIndex.faces"

cookie = ""

mainPage = ""

univerityCourses = []

formOptions = []
hiddenValues = []


def headers():
    global cookie
    return {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/84.0.4147.135 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
        'Cookie': cookiesToString(cookie) if cookie != "" else "null"}


def cookiesToString(cookie):
    return "; ".join([str(x)+"="+str(y) for x, y in cookie.items()])


def get(targetUrl=target, payload=[], attempt=1):
    requestData = None
    try:
        requestData = requests.post(target, data=payload, headers=headers())
    except:
        print("Error")
        if(attempt < 3):
            sleep(attempt * 5)
            get(targetUrl, payload)
        else:
            return 0
    return requestData


def getCookies(page):
    setCookies(page.cookies)


def setCookies(cookies):
    global cookie
    cookie = cookies


def setUpOptions():
    page = get()

    soup = BeautifulSoup(page.content, 'html.parser')

    options = soup.findAll('select')

    for option in options:
        global formOptions
        optionsListValues = []
        optionId = option.attrs['id']
        optionsList = BeautifulSoup(
            str(option), 'html.parser').find_all('option')
        for o in optionsList:
            optionsListValues.append(o['value'])
        result = {
            "optionId": optionId,
            "list": optionsListValues
        }

        formOptions.append(result)


def removeDuplicate(inputList):
    # Remove all duplicated items
    return [i for n, i in enumerate(inputList) if i not in inputList[n + 1:]]


def setUpHiddenValues(page):
    global hiddenValues
    global mainPage
    
    mainPage = page
    
    soup = BeautifulSoup(page.content, 'html.parser')

    hidden_tags = soup.findAll("input", type="hidden")

    for tag in hidden_tags:
        try:
            hiddenValues.append((tag.attrs['name'], tag.attrs['value']))
        except:
            next



    hiddenValues = removeDuplicate(hiddenValues)



def getMajors(select1, select2):
    global hiddenValues

    params = hiddenValues[:]
    params.remove(('myForm:index', ''))
    params.append(('myForm:select1', select1))
    params.append(('myForm:select2', select2))
    params.append(('myForm:_idcl' , ''))

    page = get(payload=params)

    majorsList = []
    majorsTree = page.text.split("tree.add(")
    for major in majorsTree:
        if "javascript:setIndex" in major:
            majorCode = ''
            majorName = ''
            majorSplitter = major.split("'")
            majorDetailsSplitter = majorSplitter[1].split('-')
            if(len(majorDetailsSplitter) <= 2):
                majorCode = majorDetailsSplitter[0]
                majorName = majorDetailsSplitter[1]
            else:
                majorCode = majorDetailsSplitter[0]
                majorName = majorDetailsSplitter[2]

            majorIndex = major.split("javascript:setIndex(")[1].split(")")[0]

            majorsList.append(
                {"code": majorCode, "name": majorName, "index": majorIndex})

    return removeDuplicate(majorsList)


def getMajorCourses(majorIndex, select1, select2):
    global hiddenValues
    coursesList = []

    params = hiddenValues[:]
    params.remove(('myForm:index', ''))
    params.append(('myForm:select1', select1))
    params.append(('myForm:select2', select2))
    params.append(('myForm:index', majorIndex))

    if("myForm:_idcl" in mainPage.text):
        params.append(('myForm:_idcl', 'myForm:commandLink'))
    else:
        params.append(('myForm:commandLink', 'myForm:commandLink'))

    page = get(payload=params)

    soup = BeautifulSoup(page.content, 'html.parser')

    rows = soup.findAll('tr', {"class": re.compile('^ROW')})

    for row in rows:
        data = row.text.splitlines()
        coursesList.append(
            {'code': data[1], 'name': data[2], 'credits': data[5]})

    return removeDuplicate(coursesList)


def init():
    page = get()
    getCookies(page)
    setUpOptions()
    setUpHiddenValues(page)


def worker():
    global formOptions
    global univerityCourses

    select1List = []
    select2List = []

    for value in formOptions:
        if(value['optionId'] == 'myForm:select1'):
            select1List = value['list']
        elif(value['optionId'] == 'myForm:select2'):
            select2List = value['list']

    for select1 in select1List:
        for select2 in select2List:
            majors = getMajors(select1, select2)
            for major in majors:
                univerityCourses.extend(downloader(major, select1, select2))
                autoSave()

    univerityCourses = removeDuplicate(univerityCourses)
    print('Total of {} courses found in this target'.format(len(univerityCourses)))
    save()


def downloader(major, select1, select2):
    print('downloading {} Courses...'.format(major['code']))
    coursesList = getMajorCourses(major['index'], select1, select2)
    print('{} courses found in {}'.format(len(coursesList), major['code']))
    return coursesList


def save():
    global univerityCourses
    with open('data.json', 'w+', encoding='utf-8') as f:
        json.dump(univerityCourses, f, ensure_ascii=False)


def autoSave():
    global univerityCourses
    with open('data.json', 'a+', encoding='utf-8') as f:
        json.dump(univerityCourses, f, ensure_ascii=False)



init()
worker()
