from bs4 import BeautifulSoup
import requests



event = '100m Fjärilsim'
born = '2007'
age = '17' # meet year - birth year
name = 'Eric Söderlund'

livetiming_url = (
    'https://www.livetiming.se/results.php?cid=7913&session=0&all=1')

livetiming_page = requests.get(livetiming_url)

livetiming_soup = BeautifulSoup(livetiming_page.content, 'html.parser')

livetiming_trs = livetiming_soup.find_all('tr')


def is_correct_event(row_text: str) -> bool:
    event_tokens = row_text.split(' ')
    return f'{event_tokens[2]} {event_tokens[3]}' == event

def collapse_whitespace(s: str) -> str:
    '''
    Collapses all whitespace characters in a string to a single space.
    '''
    result = ''
    for i in range(len(s)):
        if not s[i].isspace():
            result += s[i]
        # we already have a space as the last char in result
        elif (result == '') or (not result[-1].isspace()):
            result += ' '
    return result

def get_row_text(row) -> str:
    '''
    Gets the text of a row, in a nice format.
    '''
    return collapse_whitespace(row.get_text().replace('\xa0', ' ').strip())

def get_splits_from_event(livetiming_trs, start_index: int) -> dict[str, str]:
    splits = dict()
    looking_for_name = False
    looking_for_splits = False
    for row in livetiming_trs[start_index + 1:]:
        row_text = get_row_text(row)
        if row_text == '': continue

        # no more swimmers in the event
        if row_text[:17] == 'Grenen officiell:': break

        # starting to list the swimmers
        if row_text[:10] == 'Plac Namn ': 
            looking_for_name = True
            continue
        
        # can continue if we aren't looking for swimmer or splits at this point
        if not looking_for_name and not looking_for_splits: continue

        row_tokens = row_text.split(' ')
        # found the swimmer
        if f'{row_tokens[1]} {row_tokens[2]}' == name:
            looking_for_splits = True
            continue
        # ...extract the splits
        if looking_for_splits:
            splits[row_tokens[0]] = row_tokens[1]
            splits[row_tokens[2]] = f'{row_tokens[3]} {row_tokens[4]}'
            break
    return splits
        




for row_index, row in enumerate(livetiming_trs):
    row_text = get_row_text(row)
    if row_text[:5] == 'Gren ' and is_correct_event(row_text):
        splits = get_splits_from_event(livetiming_trs, row_index)
        print(splits)
        break # temp




    