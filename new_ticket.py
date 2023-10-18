import requests
import sys
from bs4 import BeautifulSoup
from pandas import DataFrame
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure

from re import sub
from decimal import Decimal
from datetime import datetime, timezone
import json
import time
import signal
import sys


STUDENT_SEATS_SITE="https://studentseats.com"
DELIM="/"
MONGO_URL="add_HERE"
MONGO_DATABASE="ticket"

mongo_client=None
mongo_db=None 
mongo_col=None 

def connectDb():
    global mongo_client
    if mongo_client is None:
        mongo_client=MongoClient(MONGO_URL)
    try:
        mongo_client.admin.command('ping')
    except ConnectionFailure:
        print("Database not availible")
        mongo_client=None
        return
    mongo_db=mongo_client[MONGO_DATABASE]
    return mongo_db

def getSite(school="Alabama", sport="Football"):
    #os.system('cls' if os.name == 'nt' else 'clear')
    #return "https://studentseats.com/OhioState/OhioState-PennState-tickets?id=894"
    #print("Finding latest tickets page ...")
    rr=requests.get(STUDENT_SEATS_SITE+DELIM+school)
    soup = BeautifulSoup(rr.content, "html.parser")
    table=soup.find('div',{'id':sport})
    links = table.findAll('a',{'class':"upcomingGameCard"})
    url = links[0]["href"]
    if url.startswith("http"):
        return url
    
    return STUDENT_SEATS_SITE  + url

def stripSpaceArray(arr):
    for input in ['Price','Seller','Section',"Availibility",'Ticket Button']:
        for i in range(len(arr[input])):
            arr[input][i]=''.join(arr[input][i].split())

def requestSite(url):
    print("requesting "+url)
    r = requests.get(url)
    #os.system('cls' if os.name == 'nt' else 'clear')
    
    if r.status_code == 200:
        soup = BeautifulSoup(r.content, "html.parser")
        table=soup.find('div',{'id':'ticketsForSale'})
        if table is None:
            return False
        #print(table)
        #print("########################################")
        new_table = []
        
        for row in table.find_all('div',{'class':'card-element'}):
            info = row.find_all('div', {'class': 'ticket-info-group'})
            if info is None:
                continue
            # username
            username = info[0].find('span',{'class':'ticket-username'})
            #print('username', username.text.strip())

            # section info
            section_data = info[1].find_all('span')
            section_info = ' '.join(i.text for i in section_data)
            #print("section info: ", section_info)

            # price
            money = info[2].find('span')
            #print('money', money.text.strip())

            #print("################")
            #Decimal(sub(r'[^\d.]', '', money.text.strip()))
            new_table.append({  "Seller":username.text.strip(),
                                "Price":float(sub(r'[^\d.]', '', money.text.strip())),
                                'section_info':section_info})
        #print(new_table)
        df = DataFrame(new_table, columns=['Seller','Price','section_info'])
        #print(df)
        #stripSpaceArray(df)
    else:
        return False
    return df

def getStats(frame, time):
    data = {
            'date': int(time),
            'mean': frame.loc[:, 'Price'].mean(),
            'median': frame.loc[:, 'Price'].median(),
            'stddev': frame.loc[:, 'Price'].std(),
            'min': float(frame.loc[:, 'Price'].min()),
            'max': float(frame.loc[:, 'Price'].max()),
            'size': frame.loc[:, 'Price'].size
            }
    
    if frame.size > 0 :
        #section = 0
        section =  0 if "Lower" in frame.iloc[0]['section_info'] else 1
        data['section'] = section
    return data

def writeData(data):
    filename = str(time_now)+".json"
    with open("/mnt/drive/ssoutput/"+filename, "w") as f:
        f.write(json.dumps(data))

if __name__ == "__main__":
    pArgs = sys.argv

    data = []
    count = 0

    def signal_handler(sig, frame):
        print('You pressed Ctrl+C!')
        writeData(data)
        sys.exit(0)

    signal.signal(signal.SIGINT, signal_handler)

    game = getSite()
    print(game)
    # last frame, compare
    p_sections = []
    while True:
        try:
            frame = requestSite(game)
            if frame is False:
                time.sleep(2)
                continue
            time_now = int(datetime.now(timezone.utc).timestamp())
            sections = [x for _, x in frame.groupby(['section_info'])]
            for s in sections:
                sa = getStats(s,time_now)
                # print(sa)
                if len(p_sections) < sa['section']+1:
                    p_sections.append(sa)
                else:
                    diffkeys = [k for k in sa if p_sections[sa['section']][k] != sa[k]]
                    if len(diffkeys)>1:
                        data.append(sa)
                        p_sections[sa['section']] = sa
                        print("diff append") 
                    else:
                        print(str(time_now), "have not changed", end=". ")
            
            if len(data)>500:
                writeData(data)
                data.clear()
            
            time.sleep(2)
        except Exception as e:
            import traceback
            traceback.print_exc()
            print(str(e))
            writeData(data)
            sys.exit(1)