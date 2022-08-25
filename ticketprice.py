import requests
import sys
import os
from bs4 import BeautifulSoup
from pandas import DataFrame
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure
from datetime import datetime

STUDENT_SEATS_SITE="https://studentseats.com"
MONGO_URL="mongodb://localhost:27017"
MONGO_DATABASE="ticket"

mongo_client=None
mongo_db=None 
mongo_col=None 

def connectDb():
    if mongo_client == None:
        mongo_client=MongoClient(MONGO_URL)
    try:
        mongo_client.admin.command('ping')
    except ConnectionFailure:
        print("Database not availible")
        mongo_client=None
        return
    mongo_db=mongo_client[MONGO_DATABASE]

def getSite():
    os.system('cls' if os.name == 'nt' else 'clear')
    found_valid=False
    print("Finding latest tickets page ...")
    #not sure what happens when goes past range of (home) games 
    for i in reversed(range(12)):
            rr=requests.get(STUDENT_SEATS_SITE+"/Forum/Topic/"+str(i))
            if not (rr.url==STUDENT_SEATS_SITE):
                found_valid=True
                break
    if not found_valid:
        print("No student tickets are currently availible to buy/sell")
        exit()
    
    return rr.url

def stripSpaceArray(arr):
    for input in ['Price','Seller','Section',"Availibility",'Ticket Button']:
        for i in range(len(arr[input])):
            arr[input][i]=''.join(arr[input][i].split())

def requestSite(url):
    r = requests.get(url)
    os.system('cls' if os.name == 'nt' else 'clear')
    
    if r.status_code == 200:
        soup = BeautifulSoup(r.content, "html.parser")
        table=soup.find('table',{'id':'forumIndexTable'})

        new_table = []
        for row in table.find_all('tr')[1:]:
            column_marker = 0
            columns = row.find_all('td')
            new_table.append([column.get_text() for column in columns])
        df = DataFrame(new_table, columns=['Seller','Price','Section','Availibility','Ticket Button'])
        stripSpaceArray(df)
    else:
        return False
    return df

if __name__ == "__main__":
    pArgs = sys.argv
    standard_out=""
    if not (len(pArgs) >= 3):
        inst_out='\nNo arguments, reverting to default settings (lowerbowl, price point 70)\n\nUsage:  uaticketbot.exe (MAX price (integer)) ("upper" for upperbowl, anything else for lower)\nEx. uaticketbot.exe 100 lower\n\tuaticketbot.exe 60 upper stop_on_find\n\nCTRL+C to stop\n\n'
        standard_out+=inst_out
        #default stats
        pArgs=[":",str(70),"lower"]
    
    ticket_request_url = getSite()
    maxPrice= pArgs[1]
    bowl= pArgs[2]
    standard_out+="Looking for "+bowl+" bowl tickets under $"+maxPrice
    
    connectDb()
    if not mongo_client==None:
        #current collection name is the url of the ticket page
        mongo_col=mongo_db[ticket_request_url]

    while True:  
        df=requestSite(ticket_request_url)
        print(standard_out)
        if not df==False:
            page_links=[]
            #links of ticket postings
            post_links=[]
            for link in soup.find_all('a'):
                page_links.append(link.get('href'))
            for link in page_links:
                #this is weird logic-wise but find returns index value, which when it is a post link is 0, which is not truthy
                if not (link.find("Post/Index/") == -1):
                    post_links.append(link)
                    continue
                
            ticket_found=False
            lowest_cost={"UpperBowl":[10000,-1],"LowerBowl":[10000,-1]}

            m_requests=[]
            now_time=datetime.now()
            ticket_price_sum=0

            for i in range(len(df['Price'])):
                price= df['Price'][i][1:df['Price'][i].find('.')]
                ticket_price_sum += float(price)
                lowest_cost[df['Section'][i]][0] = min(lowest_cost[df['Section'][i]][0],float(price))
                m_requests.insert({"name":"NAME_HERE","price":float(price),"time":now_time})
                if lowest_cost[df['Section'][i]][0]==int(price):
                    lowest_cost[df['Section'][i]][1] = i 

                if df['Section'][i]==("UpperBowl" if bowl=="upper" else "LowerBowl"):
                    if int(price)<=int(maxPrice):
                        ticket_found=True

            ticket_price_avg = ticket_price_sum / len(df['Price'])

            
            #insert each ticket into that game's collection
            mongo_db[ticket_request_url].insert_many(m_requests)

            print("\n\nNewest data: ")
            print("response time: "+str(r.elapsed.total_seconds()))
            print("Upper Bowl: $"+str(lowest_cost["UpperBowl"][0]) + " : "+STUDENT_SEATS_SITE+post_links[lowest_cost["UpperBowl"][1]*2])
            print("Lower Bowl: $"+str(lowest_cost["LowerBowl"][0]) + " : "+STUDENT_SEATS_SITE+post_links[lowest_cost["LowerBowl"][1]*2])
        else:
            print("site request error")

        if ticket_found:
            print('\a\a\a\a\a\a')
            print("found")
            if len(pArgs)>4:
                exit()
        else:
            print("not found")
