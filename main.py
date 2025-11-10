from bs4 import BeautifulSoup
from urllib.parse import quote
import requests
regulation='(R20)'
html_text = requests.get("https://mits.ac.in/ugc-autonomous-exam-portal#ugc-pro3").text
soup = BeautifulSoup(html_text, 'lxml')
def safe_url(u):
    if " " not in u:
        return u
    parts=u.split('/',3)
    if len(parts) < 4:
        return u
    prefix ='/'.join(parts[:3])
    path =  quote(parts[3])
    return f"{prefix}/{path}"
def exam_timetable():
    n=0
    b=[]
    table=soup.find('div', id='ugc-pro3')
    exam=table.find('div',class_='container')
    exam_data=exam.find("div",class_="publication-list mb-4")
    exam1=exam.find_all("li")
    for index,exam2 in enumerate(exam1):
        if n==1:
            break
        a=exam2.text.strip()
        downlink=exam2.find("a")['href']
        downloadlink=safe_url(downlink)
        if regulation in a:
            b.append(a)
            b.append(downloadlink)
            n=n+1
    return b
