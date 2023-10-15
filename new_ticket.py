import requests
import sys
from bs4 import BeautifulSoup
from pandas import DataFrame
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure

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
    return "https://studentseats.com/OhioState/OhioState-PennState-tickets?id=894"
    print("Finding latest tickets page ...")
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
        print("########################################")
        new_table = []
        
        for row in table.find_all('div',{'class':'card-element'}):
            info = row.find_all('div', {'class': 'ticket-info-group'})
            # username
            username = info[0].find('span',{'class':'ticket-username'})
            print('username', username.text.strip())

            # section info
            section_data = info[1].find_all('span')
            section_info = ' '.join(i.text for i in section_data)
            print("section info: ", section_info)

            # price
            money = info[2].find('span')
            print('money', money.text.strip())

            print("################")
        #print(new_table)
        df = DataFrame(new_table, columns=['Seller','Price','Section','Availibility','Ticket Button'])
        #stripSpaceArray(df)
    else:
        return False
    return df

if __name__ == "__main__":
    pArgs = sys.argv
    
    game = getSite()
    print(game)
    requestSite(game)
        