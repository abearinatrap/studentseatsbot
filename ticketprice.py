import requests
import sys
import winsound
from bs4 import BeautifulSoup
from pandas import DataFrame

def stripSpaceArray(arr):
    for input in ['Price','Seller','Section',"Availibility",'Ticket Button']:
        for i in range(len(arr[input])):
            arr[input][i]=''.join(arr[input][i].split())

if __name__ == "__main__":
    pArgs = sys.argv
    if not (len(pArgs) >= 3):
        print(''' 
No arguments, reverting to default settings (lowerbowl, price point 70)

Usage:  uaticketbot.exe (MAX price (integer)) ("upper" for upperbowl, anything else for lower)
Ex. uaticketbot.exe 100 lower
    uaticketbot.exe 60 upper stop_on_find
    
CTRL+C to stop
        
        ''')
        #default stats
        pArgs=["fuck all",str(70),"lower"]
    ''' args should be MAX_PRICE and which bowl ('upper' vs 'lower')'''
    found_valid=False
    print("Finding latest tickets page ...")
    for i in reversed(range(10)):
            rr=requests.get("https://student-seats.com/Forum/Topic/"+str(i))
            if not (rr.url=="https://student-seats.com/"):
                found_valid=True
                break
    if not found_valid:
        print("no student tickets are currently availible to buy/sell")
        exit()
    STUDENT_SEATS_SITE="https://student-seats.com"
    ticket_request_url=rr.url
    maxPrice= pArgs[1]
    bowl= pArgs[2]
    print("Looking for "+bowl+" bowl tickets under $"+maxPrice)
    
    while True:  
        r = requests.get(ticket_request_url)
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

            page_links=[]
            post_links=[]
            for link in soup.find_all('a'):
                page_links.append(link.get('href'))
            for link in page_links:
                #this is weird logic-wise but find returns index value, which when it is a post link is 0, which is not truthy
                if not (link.find("Post/Index/") == -1):
                    post_links.append(link)
                    continue
                
            t_found=False
            #print(post_links)
            lowest_cost={"UpperBowl":[10000,-1],"LowerBowl":[10000,-1]}
            for i in range(len(df['Price'])):
                price= df['Price'][i][1:df['Price'][i].find('.')]
                #print("Price is "+price + " vs. "+maxPrice + " -- "+df['Section'][i])
                lowest_cost[df['Section'][i]][0] = min(lowest_cost[df['Section'][i]][0],int(price))
                if lowest_cost[df['Section'][i]][0]==int(price):
                    lowest_cost[df['Section'][i]][1] = i 

                if df['Section'][i]==("UpperBowl" if bowl=="upper" else "LowerBowl"):
                    if int(price)<=int(maxPrice):
                        t_found=True
                        #break on finding a price lower - removed for data collection
                        #break
            
            print("\n\nNewest data: ")
            print("response time: "+str(r.elapsed.total_seconds()))
            #print(lowest_cost)
            # each link is repeated twice so multiply index by 2
            print("Upper Bowl: $"+str(lowest_cost["UpperBowl"][0]) + " : "+STUDENT_SEATS_SITE+post_links[lowest_cost["UpperBowl"][1]*2])
            print("Lower Bowl: $"+str(lowest_cost["LowerBowl"][0]) + " : "+STUDENT_SEATS_SITE+post_links[lowest_cost["LowerBowl"][1]*2])
        else:
            print("site request error")
        if t_found:
            print('\a\a\a\a\a\a')
            frequency = 2500  
            duration = 500  
            if len(pArgs)>4:
                duration = 3000
            winsound.Beep(frequency, duration)
            print("found")
            if len(pArgs)>4:
                exit()
        else:
            print("not found")