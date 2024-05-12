from bs4 import BeautifulSoup
import requests


'https://www.tempusopen.se/index.php?r=swimmer%2Findex&Swimmer%5Bfirst_name%5D=Viktor&Swimmer%5Blast_name%5D=Tjernstr%C3%B6m&Swimmer%5Bswimmer_club%5D=&Swimmer%5BsearchChoice%5D=&ajax=swimmer-grid'
'https://www.tempusopen.se/index.php?r=swimmer%2Findex&Swimmer%5Bfirst_name%5D=Viktor&Swimmer%5Blast_name%5D=Tjernstr%C3%B6m&Swimmer%5Bswimmer_club%5D=Sundsvall&Swimmer%5BsearchChoice%5D=&ajax=swimmer-grid'



def get_meet_name_from_page(swimmer_id: str, event_id: str) -> str:
    '''
    Gets the name of the meet where the swimmer swam their personal best.
    '''
    tempus_url = (f'https://www.tempusopen.se/index.php?r=swimmer/'
                  f'distance&id={swimmer_id}&event={event_id}')
    tempus_page = requests.get(tempus_url)
    tempus_soup = BeautifulSoup(tempus_page.content, 'html.parser')
    tempus_trs = tempus_soup.find_all('tr')
    return tempus_trs[1].find_all('td')[-1].get_text()

print(get_meet_name_from_page('330221', '54'))

def get_meet_id_from_name(name: str) -> str:
    '''
    Gets the ID of a meet by its name.
    '''
    livetiming_url = 'https://www.livetiming.se/archive.php?cid=6644'
    livetiming_page = requests.get(livetiming_url)
    livetiming_soup = BeautifulSoup(livetiming_page.content, 'html.parser')
    livetiming_trs = livetiming_soup.find_all('tr')
    for row in livetiming_trs[1:]:
        name_td = row.find_all('td')[0]
        meet_name = name_td.get_text()
        if meet_name != name:
            continue
        link = name_td.find('a')['href']
        id = link.split('=')[-1]
        return id

print(get_meet_id_from_name('Järfälla Nationella 2024'))