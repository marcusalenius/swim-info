'''

'''

from bs4 import BeautifulSoup

import json








def populate_html() -> None:
    '''
    
    '''
    with open('ui/index_template.html', 'r', encoding='utf-8') as file:
        soup = BeautifulSoup(file, 'html.parser')
    populate_page_title(soup)
    populate_event_menu(soup)
    add_right_columns(soup)
    with open('ui/index.html', 'w', encoding='utf-8') as file:
        file.write(str(soup))

with open('output.json', 'r', encoding='utf-8') as file:
    data = json.load(file)



