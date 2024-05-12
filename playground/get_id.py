import requests
from bs4 import BeautifulSoup
from urllib.parse import unquote, quote



form_url = 'https://www.tempusopen.se/index.php?r=swimmer%2Findex&Swimmer%5Bfirst_name%5D=Viktor&Swimmer%5Blast_name%5D=Tjernstr%C3%B6m&Swimmer%5Bswimmer_club%5D=&Swimmer%5BsearchChoice%5D=&Swimmer%5Bclass%5D=99&Swimmer%5Bis_active%5D=99&ajax=swimmer-grid'
response = requests.get(form_url)
soup = BeautifulSoup(response.content, 'html.parser')
# print(soup.find('table').prettify())
print(soup.find_all('td', {'class': 'name-column'})[0].find('a')['href'])

print(unquote('%C3%B6'))
print(quote('ö'))
