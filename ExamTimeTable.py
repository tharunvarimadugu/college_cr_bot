from bs4 import BeautifulSoup
from urllib.parse import quote, urljoin
import requests
from email.mime import text
from bs4 import BeautifulSoup
import requests
from urllib.parse import urljoin
def safe_url(u):
    if " " not in u:
        return u
    parts=u.split('/',3)
    if len(parts) < 4:
        return u
    prefix ='/'.join(parts[:3])
    path =  quote(parts[3])
    return f"{prefix}/{path}"
def exam_timetable(regulation):
    html_text = requests.get("https://mits.ac.in/ugc-autonomous-exam-portal#ugc-pro3").text
    soup = BeautifulSoup(html_text, 'lxml')
    n=0
    b=[]
    table=soup.find('div', id='ugc-pro3')
    exam=table.find('div',class_='container')
    exam_data=exam.find("div",class_="publication-list mb-4")
    exam1=exam.find_all("li")
    for index,exam2 in enumerate(exam1):
        if n==5:
            break
        a=exam2.text.strip()
        downlink=exam2.find("a")['href']
        downloadlink=safe_url(downlink)
        if regulation in a:
            b.append(a)
            b.append(downloadlink)
            n=n+1
    return b
def results_checking():
    html_text="http://125.16.54.154/mitsresults/resultug"
    soup=BeautifulSoup(requests.get(html_text).text,'lxml')
    table=soup.find('div',class_='wrapper')
    table1=table.find_all('a')
    data=[]
    results_link=[]
    new_text=[]
    data1=[]
    ROMAN = {
        "I": 1,
        "II": 2,
        "III": 3,
        "IV": 4,
    }
    regulation="R20"
    year="3"
    sem="2"
    for index,x in enumerate(table1):
        link=x["href"]
        name=x.get_text(strip=True)      
        full_link = urljoin(html_text, link)
        data.append(name)
        parts = name.split("-")        # ['B.Tech', 'IV', 'II', 'R20', 'Regular', 'May', '2024']
        parts[1] = str(ROMAN[parts[1].upper()])   # IV  -> 4
        parts[2] = str(ROMAN[parts[2].upper()])   # II  -> 2
        text = "-".join(parts)
        if regulation in text and year in text[7] and sem in text[9]:
            new_text.append(text)
            results_link.append(full_link)
    for index,x in enumerate(new_text):
        data1.append((f"{index}: {x}"))
    print("\n".join(data1))
    idx = int(input("Enter number: "))
    choice = new_text[idx]
    result_link = results_link[idx]
    return result_link

        
if __name__=="__main__":
    print(results_checking())
