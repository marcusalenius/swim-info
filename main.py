'''
Main call chain:

get_best_swims_for_session
 |  called:    1 time
 |  cached:    no
 |  request:   GET to LiveTiming
 |  iterates:  through the events in the session
 V
get_best_swims_for_event
 |  called:    num. events_in_session times
 |  cached:    no
 |  request:   GET to LiveTiming    
 |  iterates:  through the heats in the event
 V
get_best_swims_for_heat
 |  called:    num. heats_in_event times
 |  cached:    no
 |  request:   none
 |  iterates:  through the swimmers in the heat
 V
get_best_swim_for_swimmer
 |  |  called:    num. swimmers_in_heat times
 |  |  cached:    no
 |  |  request:   none
 |  |  iterates:  no
 |  |
 |  +--> get_swimmer_id 
 |  |      called:    1 time
 |  |      cached:    yes
 |  |      request:   GET to Tempus
 |  |      iterates:  no
 |  |
 |  +--> get_event_id
 |  |      called:    1 time
 |  |      cached:    no
 |  |      request:   none
 |  |      iterates:  no
 |  |
 |  +--> get_meet_name_and_date
 |  |      called:    1 time
 |  |      cached:    no
 |  |      request:   GET to Tempus
 |  |      iterates:  no
 |  |
 |  +--> get_meet_id_and_location
 |         called:    1 time
 |         cached:    yes
 |         request:   GET to LiveTiming
 |         iterates:  through all meets in LiveTiming
 V
get_splits_from_meet
 |  |  called:    1 time
 |  |  cached:    no
 |  |  request:   none
 |  |  iterates:  through all results of the meet
 |  |
 |  +--> get_meet_results
 |         called:    1 time
 |         cached:    yes
 |         request:   GET to LiveTiming
 |         iterates:  no
 V
get_splits_from_event_edition
 |  called:    num. matching_event_editions_in_meet times
 |  cached:    no
 |  request:   none
 |  iterates:  through all swims in the event edition
 V
get_splits_from_swim
    called:    num. matching_swims_in_event_edition times
    cached:    no
    request:   none
    iterates:  through the row texts of a swim and the splits on that row
'''




import requests
from bs4 import BeautifulSoup
from urllib.parse import quote

from pprint import pprint 
import json

from utilities import get_element_text
from meet_matcher import meet_names_match
from event_matcher import is_correct_event
from event_ids import TEMPUS_EVENT_IDs
from swimmer_id_cache import (load_stored_swimmer_id_cache, 
                              save_swimmer_id_cache, 
                              get_cached_swimmer_id, 
                              add_swimmer_id_to_cache)
from meet_id_cache import (load_stored_meet_id_and_location_cache,
                           save_meet_id_and_location_cache,
                           get_cached_meet_id_and_location, 
                           add_meet_id_and_location_to_cache)
from meet_results_cache import (load_stored_meet_results_cache,
                                save_meet_results_cache,
                                get_cached_meet_results,
                                add_meet_results_to_cache)
from main_helpers import (fastest_swim,
                          get_fifty_results)

LIVETIMING_SESSION_URL = (
    'https://www.livetiming.se/program.php?cid=8051&session=1')

'''
Number of heats per event to get the best swim splits for. Set to 1 or above.
'''
NUM_HEATS = 2



DEBUG = True
def debug_print(*args):
    if DEBUG:
        print(*args)

import time
def time_function(func, *args):
    start = time.time()
    return_val = func(*args)
    end = time.time()
    print(f'Time taken: {end-start} seconds')
    return return_val


######################################################################
# Helper functions for get_best_swim_for_swimmer
######################################################################

def get_swimmer_id(swimmer_data: dict[str, str]) -> str | None:
    '''
    Returns the Tempus id of a swimmer. The swimmer data should be a dictionary
    with the keys 'name', 'born', and 'club'. The name should be in the format
    'First Last' and born should be in the format 'YYYY'.

    If the swimmer is in the cache, their id is returned immediately. Otherwise,
    a GET request is made to Tempus to search for the swimmer. If the swimmer is
    found, their id is added to the cache and returned. If the swimmer is not
    found, None is returned.
    '''
    cached_id = get_cached_swimmer_id(swimmer_data)
    if cached_id is not None:
        debug_print('Used cached swimmer id.')
        return cached_id
    debug_print('Making GET request to Tempus for swimmer id.')
    first_name = quote(swimmer_data['name'].split(' ')[0])
    last_name = quote(' '.join(swimmer_data['name'].split(' ')[1:]))
    club = quote(swimmer_data['club'])
    form_url = (f'https://www.tempusopen.se/index.php?r=swimmer%2Findex'
                f'&Swimmer%5Bfirst_name%5D={first_name}'
                f'&Swimmer%5Blast_name%5D={last_name}'
                f'&Swimmer%5Bswimmer_club%5D={club}'
                f'&Swimmer%5BsearchChoice%5D=1'
                f'&Swimmer%5Bclass%5D=99'
                f'&Swimmer%5Bis_active%5D=1'
                f'&ajax=swimmer-grid')
    response = requests.get(form_url)
    response_soup = BeautifulSoup(response.content, 'html.parser')
    first_row = response_soup.find_all('tr')[1]
    first_row_text = get_element_text(first_row)
    if first_row_text == 'Inget hittades':
        return None
    link = first_row.find('a')['href']
    id = link.split('id=')[-1]
    add_swimmer_id_to_cache(swimmer_data, id)
    return id
    
def get_event_id(event_name: str, pool: str) -> str | None:
    '''
    Returns the Tempus event id for a given event name and pool ('25m' or 
    '50m'). Returns None if the event name is not associated with an id. This 
    function simply uses the TEMPUS_EVENT_IDs dictionary.
    '''
    event_name_with_pool = f'{event_name} ({pool})'.lower()
    if event_name_with_pool not in TEMPUS_EVENT_IDs:
        return None
    return TEMPUS_EVENT_IDs[event_name_with_pool]

def get_meet_name_and_date(swimmer_id: str, event_id: str) -> tuple[str, str]:
    '''
    Gets the name and date of the meet where the swimmer swam their personal 
    best. This function makes a GET request to Tempus.
    '''
    tempus_url = (f'https://www.tempusopen.se/index.php?r=swimmer/'
                  f'distance&id={swimmer_id}&event={event_id}')
    tempus_page = requests.get(tempus_url)
    tempus_soup = BeautifulSoup(tempus_page.content, 'html.parser')
    tempus_trs = tempus_soup.find_all('tr')
    first_row_tds = tempus_trs[1].find_all('td')
    name = get_element_text(first_row_tds[-1])
    date = get_element_text(first_row_tds[-2])
    return name, date

def get_meet_id_and_location(name: str, 
                             date:str) -> tuple[str, str] | tuple[None, None]:
    '''
    Returns the LiveTiming id and location of a meet by its name. 

    If the meet is in the cache, its id and location are returned immediately.
    Otherwise, a GET request is made to LiveTiming to search for the meet. If
    the meet is found, its id and location are added to the cache and returned.
    If the meet is not found, None, None is returned.
    '''
    cached_id_and_location = get_cached_meet_id_and_location(name)
    if cached_id_and_location is not None:
        debug_print('Used cached meet id and location.')
        return cached_id_and_location
    debug_print('Making GET request to LiveTiming for meet id and location.')
    # note: 6444 is an arbitrary id and just used to get the page
    livetiming_url = 'https://www.livetiming.se/archive.php?cid=6644'
    livetiming_page = requests.get(livetiming_url)
    livetiming_soup = BeautifulSoup(livetiming_page.content, 'html.parser')
    livetiming_trs = livetiming_soup.find_all('tr')
    for row in livetiming_trs[1:]:
        row_tds = row.find_all('td')
        name_td = row_tds[0]
        meet_name = get_element_text(name_td)
        date_td = row_tds[3]
        meet_date = get_element_text(date_td)
        if meet_names_match(name, date, meet_name, meet_date):
            link = name_td.find('a')['href']
            id = link.split('=')[-1]
            location_td = row_tds[1]
            location = get_element_text(location_td)
            add_meet_id_and_location_to_cache(name, id, location)
            return id, location
    return None, None

######################################################################
# Helper function for get_splits_from_meet
######################################################################

def get_meet_results(meet_id: str) -> list[str]:
    '''
    Returns the table row texts of the results of a meet. If the meet is in the
    cache, its results are returned immediately. Otherwise, a GET request is
    made to LiveTiming to get the meet results. The results are then added to
    the cache.
    '''
    cached_results = get_cached_meet_results(meet_id)
    if cached_results is not None:
        debug_print('Used cached meet results.')
        return cached_results
    debug_print('Making GET request to LiveTiming for meet results.')
    meet_results_url = (f'https://www.livetiming.se/results.php?'
                        f'cid={meet_id}&session=0&all=1')
    meet_results_page = requests.get(meet_results_url)
    meet_results_soup = BeautifulSoup(meet_results_page.content, 'html.parser')
    meet_results_trs = meet_results_soup.find_all('tr')
    meet_results_row_texts = [get_element_text(row) 
                              for row in meet_results_trs
                              if get_element_text(row) != '']
    add_meet_results_to_cache(meet_id, meet_results_row_texts)
    return meet_results_row_texts

######################################################################
# Main call chain (reversed)
######################################################################

def get_splits_from_swim(swim_row_texts: list[str]) -> dict[str, str]:
    '''
    Iterates through the row texts of a swim and the splits on that row. 
    Returns the splits for the given swim in a dictionary which looks like:
        {
            '50m': 'time',
            '100m': 'time (last 50 time)',
            '150m': 'time (last 50 time)',
            '200m': 'time (last 50 time)',
            ...
        }
    Called for each matching swim by get_splits_from_event_edition.
    '''
    splits = dict()
    for row_text in swim_row_texts:
        row_tokens = row_text.split(' ')
        i = 0
        while i < len(row_tokens)-1:
            if row_tokens[i] == '50m:':
                splits['50m'] = row_tokens[i+1]
                i += 2
            if (row_tokens[i][-1] == ':' and row_tokens[i][0].isdigit() and 
                i+2 < len(row_tokens)):
                # [:-1] to remove the colon
                splits[row_tokens[i][:-1]] = ' '.join(row_tokens[i+1:i+3])
                i += 3
            else:
                i += 1
    return splits

def get_splits_from_event_edition(event_name: str,
                                  meet_year: int,
                                  event_edition_row_texts: list[str], 
                                  swimmer_data: dict[str, str]
                                  ) -> dict[str, str] | None:
    '''
    Iterates through the swimmers in an event edition and gets the splits for
    the swimmer. Returns None if the swimmer is not found in the event edition.
    Called for each matching event edition by get_splits_from_meet.
    '''
    is_fifty_event = '50m ' in event_name
    swim_row_texts = []
    in_correct_swim = False
    for row_text in event_edition_row_texts:
        if row_text == '': continue
        row_tokens = row_text.split(' ')
        if (f'{row_tokens[1]} {row_tokens[2]}' == swimmer_data['name']
            and row_tokens[3].isdigit() and 
            (row_tokens[3] == swimmer_data['born'] or 
             meet_year - int(row_tokens[3]) == int(swimmer_data['born']))):
            if is_fifty_event:
                return {'50m': get_fifty_results(row_text)}
            in_correct_swim = True
            continue
        if (in_correct_swim and 
            (row_tokens[0].isdigit() or row_tokens[0][0] == '=')):
            in_correct_swim = False
            if swim_row_texts != []:
                return get_splits_from_swim(swim_row_texts)
            continue
        if in_correct_swim:
            swim_row_texts.append(row_text)
    return None

def get_splits_from_meet(meet_id: str, 
                         meet_year: int,
                         swimmer_data: dict[str, str], 
                         event_name: str) -> dict[str, str] | None:
    '''
    Returns the splits for the swimmer in the given event at the given meet.
    If the meet is in the cache, no GET request is made. Otherwise, a GET
    request is made to LiveTiming to get the meet results.

    If the swimmer swam the event multiple times, only the splits of the 
    fastest swim are returned. Returns None if the event is not found. 
    
    Called once by get_best_swim_for_swimmer.
    '''
    meet_results_row_texts = get_meet_results(meet_id)
    all_splits = []
    curr_event_edition_row_texts = []
    in_correct_event = False
    in_swimmer_rows = False
    for row_text in meet_results_row_texts:
        if row_text == '': continue
        if ((row_text[:5] == 'Gren ' or row_text[:6] == 'Event ') and 
            (is_correct_event(row_text, event_name))):
            in_correct_event = True
            continue
        if ((in_correct_event) and 
            (row_text[:10] == 'Plac Namn ' or row_text[:10] == 'Rank Name ')):
            in_swimmer_rows = True
            continue
        if (in_correct_event and in_swimmer_rows and 
            (row_text[:16] == 'Grenen officiell' or 
             row_text[:14] == 'Event official')):
            in_correct_event = False
            in_swimmer_rows = False
            if curr_event_edition_row_texts != []:
                splits = get_splits_from_event_edition(event_name, meet_year,
                                                curr_event_edition_row_texts, 
                                                swimmer_data)
                if splits is not None:
                    all_splits.append(splits)
                curr_event_edition_row_texts = []
            continue
        if in_correct_event and in_swimmer_rows:
            curr_event_edition_row_texts.append(row_text)
    if all_splits == []:
        return None
    return fastest_swim(all_splits)

def get_best_swim_for_swimmer(swimmer_data: dict[str, str], event_name: str,
                              pool: str) -> dict:
    '''
    Gets the best swim for a swimmer in a given event. The return value is a
    dictionary which looks like this:
        {
            'meet_name': 'meet name',
            'meet_date': 'date',
            'meet_location': 'location',
            'result_url': 'url',
            'splits': { '50': 'time', '100': 'time (last 50 time)', ... }
        }
    Called for each swimmer in a heat by get_best_swims_for_heat.
    '''
    swimmer_id = get_swimmer_id(swimmer_data)
    if swimmer_id is None:
        return {'Error' : 'Error getting Tempus swimmer id. '
                          f'Swimmer name: {swimmer_data["name"]}.'}
    # ensure that the event name is in the correct format
    event_name = ' '.join(event_name.split(' ')[:2])
    event_id = get_event_id(event_name, pool)
    if event_id is None:
        return {'Error' : 'Error getting Tempus event id. '
                          f'Event name: {event_name}, Pool: {pool}.'}
    meet_name, meet_date = get_meet_name_and_date(swimmer_id, event_id)
    meet_id, meet_location = get_meet_id_and_location(meet_name, meet_date)
    if meet_id is None or meet_location is None:
        return {'Error' : 'Error getting LiveTiming meet id and location. '
                          f'Meet name: {meet_name}.'}
    meet_year = int(meet_date[:4])
    splits = get_splits_from_meet(meet_id, meet_year, swimmer_data, event_name)
    if splits is None:
        return {'Error' : 'Error getting splits from LiveTiming. '
                          f'Meet name: {meet_name}. Meet id: {meet_id}.'}
    result_url = (
        f'https://www.livetiming.se/results.php?cid={meet_id}&session=0&all=1')
    # assemble the best swim dictionary
    best_swim = dict()
    best_swim['meet_name'] = meet_name
    best_swim['meet_date'] = meet_date
    best_swim['meet_location'] = meet_location
    best_swim['result_url'] = result_url
    best_swim['splits'] = splits
    return best_swim

def get_best_swims_for_heat(heat_rows: list, event_name: str,
                            pool: str) -> dict:
    '''
    Iterates through the swimmers in a heat and gets the best swim for each
    swimmer. Called for each heat in an event by get_best_swims_for_event.
    '''
    heat_best_swims = dict()
    for row in heat_rows:
        row_text = get_element_text(row)
        if ((len(row_text) <= 2) or (not row_text[0].isdigit()) or 
            (not row_text[1].isspace())): continue
        lane = row_text[0]
        tds = row.find_all('td')
        swimmer_data = dict()
        swimmer_data['name'] = get_element_text(tds[3])
        swimmer_data['born'] = get_element_text(tds[4])
        swimmer_data['club'] = get_element_text(tds[5])
        heat_best_swims[f'({lane}, {swimmer_data["name"]})'] = (
            get_best_swim_for_swimmer(swimmer_data, event_name, pool))
    return heat_best_swims

def get_best_swims_for_event(event_heat_list_url: str) -> tuple[str, dict]:
    '''
    Iterates through the heats in an event and gets the best swims for each 
    heat. Makes a GET request to LiveTiming. Called for each event in a session
    by get_best_swims_for_session.
    '''
    event_heat_list_page = requests.get(event_heat_list_url)
    event_soup = BeautifulSoup(event_heat_list_page.content, 'html.parser')
    event_trs = event_soup.find_all('tr')
    event_name = None
    pool = None
    total_heats = None
    curr_heat = None
    curr_heat_rows = []
    event_best_swims = dict()
    for row in event_trs[1:]:
        row_text = get_element_text(row)
        if row_text == '': continue
        if row_text[:9] == 'Bassäng: ':
            pool = row_text[9:12]
        if row_text[:5] == 'Gren ':
            # new heat
            row_tokens = row_text.split(' ')
            heat = row_tokens[-2]
            if event_name is None:
                event_name = ' '.join(row_tokens[2:5])
            if total_heats is None:
                total_heats = int(row_tokens[-1].replace('(', '')
                                                .replace(')', ''))
            if (curr_heat is not None and 
                int(curr_heat) > total_heats - NUM_HEATS):
                # get best swims for the previous heat
                heat_best_swims = get_best_swims_for_heat(curr_heat_rows, 
                                                          event_name, pool)
                event_best_swims[curr_heat] = heat_best_swims
            if curr_heat is not None:
                curr_heat_rows = []
            curr_heat = heat
            continue
        if curr_heat is not None:
            curr_heat_rows.append(row)
    # get best swims for the last heat
    heat_best_swims = get_best_swims_for_heat(curr_heat_rows, event_name, 
                                              pool)
    event_best_swims[curr_heat] = heat_best_swims
    return event_name, event_best_swims
        

# load_stored_swimmer_id_cache()
# load_stored_meet_id_and_location_cache()
# load_stored_meet_results_cache()

# return_val = time_function(get_best_swims_for_event, 
#                            'https://www.livetiming.se/program.php?cid=8051&session=1&type=HL&event=1&tpid=1')

# with open('output.json', 'w') as file:
#     json.dump(return_val[1], file, indent=4, sort_keys=True)

# # pprint(return_val)
# # pprint(get_best_swims_for_event('https://www.livetiming.se/program.php?cid=8051&session=1&type=HL&event=1&tpid=1'))

# save_swimmer_id_cache()
# save_meet_id_and_location_cache()
# save_meet_results_cache()

def get_best_swims_for_session(session_url: str) -> dict:
    '''
    Iterates through the events in a session and gets the best swims for each
    event. Returns a dictionary where the keys are event names and the values
    are dictionaries where the keys are lane numbers and swimmer names, and the
    values are dictionaries with their best swims. Makes a GET request to
    LiveTiming. Called once by the main function.
    '''
    session_page = requests.get(session_url)
    session_soup = BeautifulSoup(session_page.content, 'html.parser')
    session_trs = session_soup.find_all('tr')
    session_best_swims = dict()
    for row in session_trs[1:]:
        tds = row.find_all('td')
        for td in tds:
            if get_element_text(td) == 'Heatlista':
                link = td.find('a')['href']
                event_heat_list_url = f'https://www.livetiming.se/{link}'
                event_name, event_best_swims = get_best_swims_for_event(
                    event_heat_list_url)
                session_best_swims[event_name] = event_best_swims
    return session_best_swims

def main():
    load_stored_swimmer_id_cache()
    load_stored_meet_id_and_location_cache()
    load_stored_meet_results_cache()
    # session_best_swims = get_best_swims_for_session(LIVETIMING_SESSION_URL)
    session_best_swims = time_function(get_best_swims_for_session,
                                       LIVETIMING_SESSION_URL)
    save_swimmer_id_cache()
    save_meet_id_and_location_cache()
    save_meet_results_cache()

    with open('output.json', 'w') as file:
        json.dump(session_best_swims, file, indent=4, sort_keys=True)


if __name__ == '__main__':
    main()

