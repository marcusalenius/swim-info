'''
This file contains the main call chain for retrieving data from LiveTiming and
Tempus. The main function is retrieve_data, which takes a session url and the
number of heats to consider, and returns a dictionary with the meet name, 
session number, and the best swims for the session. 

The main call chain is as follows:

get_meet_and_session_data
 |  called:    1 time
 |  cached:    no
 |  request:   GET to LiveTiming
 |  iterates:  no
 V
get_best_swims_for_session
 |  called:    1 time
 |  cached:    no
 |  request:   no
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

# external libraries
from bs4 import BeautifulSoup
from urllib.parse import quote

# helper functions
from retrieve_data.utilities import (GET,
                                     get_element_text,
                                     fastest_swim,
                                     get_fifty_results,
                                     final_time,
                                     avg50,
                                     time_function)
from retrieve_data.meet_matcher import meet_names_match
from retrieve_data.event_matcher import is_correct_event
from retrieve_data.event_ids import TEMPUS_EVENT_IDs
from retrieve_data.progress_bar import ProgressBar

# cache functions
from cache.swimmer_id_cache import (load_stored_swimmer_id_cache, 
                                    save_swimmer_id_cache, 
                                    get_cached_swimmer_id, 
                                    add_swimmer_id_to_cache)
from cache.meet_id_cache import (load_stored_meet_id_and_location_cache,
                                 save_meet_id_and_location_cache,
                                 get_cached_meet_id_and_location, 
                                 add_meet_id_and_location_to_cache)
from cache.meet_results_cache import (load_stored_meet_results_cache,
                                      save_meet_results_cache,
                                      get_cached_meet_results,
                                      add_meet_results_to_cache)


###############################################################################
### Debugging

# Set DEBUG to True to print debug messages
DEBUG = False

def debug_print(*args): 
    if DEBUG: print(*args)

###############################################################################


###############################################################################
### Initialize progress bar
progress_bar = ProgressBar(bar_length=50, debug=DEBUG)
###############################################################################


###############################################################################
# Helper functions for get_best_swim_for_swimmer
###############################################################################

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
        return cached_id
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
    response = GET(form_url, debug=DEBUG)
    if response is None:
        debug_print(f'Error getting Tempus swimmer search page: {form_url}.')
        return None
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
        debug_print(f'Error: Event name not found in TEMPUS_EVENT_IDs: '
                    f'{event_name_with_pool}.')
        return None
    return TEMPUS_EVENT_IDs[event_name_with_pool]

def get_meet_name_and_date(swimmer_id: str, event_id: str
                           ) -> tuple[str, str, str] | None:
    '''
    Gets the name and date of the meet where the swimmer swam their personal 
    best. This function makes a GET request to Tempus. It also return the time
    of the swim as a backup time in case the LiveTiming results are not found.
    '''
    tempus_url = (f'https://www.tempusopen.se/index.php?r=swimmer/'
                  f'distance&id={swimmer_id}&event={event_id}')
    tempus_page = GET(tempus_url, debug=DEBUG)
    if tempus_page is None:
        debug_print(f'Error getting Tempus personal best page {tempus_url}.')
        return None
    tempus_soup = BeautifulSoup(tempus_page.content, 'html.parser')
    tempus_trs = tempus_soup.find_all('tr')
    # empty page (swimmer has no times for the event)
    if tempus_trs == []:
        return None
    first_row_tds = tempus_trs[1].find_all('td')
    name = get_element_text(first_row_tds[-1])
    date = get_element_text(first_row_tds[-2])
    backup_time = get_element_text(first_row_tds[0])
    backup_time = backup_time.removeprefix('00:').removeprefix('0')
    return name, date, backup_time

def get_meet_id_and_location(name: str, 
                             date:str) -> tuple[str, str] | None:
    '''
    Returns the LiveTiming id and location of a meet by its name. 

    If the meet is in the cache, its id and location are returned immediately.
    Otherwise, a GET request is made to LiveTiming to search for the meet. If
    the meet is found, its id and location are added to the cache and returned.
    If the meet is not found, None, None is returned.
    '''
    cached_id_and_location = get_cached_meet_id_and_location(name)
    if cached_id_and_location is not None:
        return cached_id_and_location
    # note: 6444 is an arbitrary id and just used to get the page
    livetiming_url = 'https://www.livetiming.se/archive.php?cid=6644'
    livetiming_page = GET(livetiming_url, debug=DEBUG)
    if livetiming_page is None:
        debug_print(f'Error getting LiveTiming all meets page: '
                    f'{livetiming_url}.')
        return None
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
    return None

###############################################################################
# Helper function for get_splits_from_meet
###############################################################################

def get_meet_results(meet_id: str) -> list[str] | None:
    '''
    Returns the table row texts of the results of a meet. If the meet is in the
    cache, its results are returned immediately. Otherwise, a GET request is
    made to LiveTiming to get the meet results. The results are then added to
    the cache.
    '''
    cached_results = get_cached_meet_results(meet_id)
    if cached_results is not None:
        return cached_results
    meet_results_url = (f'https://www.livetiming.se/results.php?'
                        f'cid={meet_id}&session=0&all=1')
    meet_results_page = GET(meet_results_url, debug=DEBUG)
    if meet_results_page is None:
        debug_print(f'Error getting LiveTiming meet results page: '
                    f'{meet_results_url}.')
        return None
    meet_results_soup = BeautifulSoup(meet_results_page.content, 'html.parser')
    meet_results_trs = meet_results_soup.find_all('tr')
    meet_results_row_texts = [get_element_text(row) 
                              for row in meet_results_trs
                              if get_element_text(row) != '']
    add_meet_results_to_cache(meet_id, meet_results_row_texts)
    return meet_results_row_texts

###############################################################################
# Main call chain (reverse order)
###############################################################################

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
            if row_tokens[i] == '50m:' and row_tokens[i+1][0].isdigit():
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
        if (
            # two names
            (len(row_tokens) >= 3 and
             f'{row_tokens[1]} {row_tokens[2]}' == swimmer_data['name'] and
             row_tokens[3].isdigit() and 
             (row_tokens[3] == swimmer_data['born'] or 
              meet_year - int(row_tokens[3]) == int(swimmer_data['born']))) or

            # three names
            (len(row_tokens) >= 4 and
             (f'{row_tokens[1]} {row_tokens[2]} {row_tokens[3]}' == 
                                                    swimmer_data['name']) and
             row_tokens[4].isdigit() and 
             (row_tokens[4] == swimmer_data['born'] or 
              meet_year - int(row_tokens[4]) == int(swimmer_data['born'])))
        ):
            if is_fifty_event:
                fifty_result = get_fifty_results(row_text)
                if fifty_result is None:
                    return None
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
    fastest swim are returned. Returns None if the event is not found or if 
    there are no 50 splits.
    
    Called once by get_best_swim_for_swimmer.
    '''
    meet_results_row_texts = get_meet_results(meet_id)
    if meet_results_row_texts is None:
        return None
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

    fastest_swim_splits = fastest_swim(all_splits)
    if '50m' not in fastest_swim_splits:
        return None
    return fastest_swim_splits

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
            'final_time': 'time',
            'avg50': 'time',
            'splits': { '50': 'time', '100': 'time (last 50 time)', ... },
            'all_times_url': 'url',
            'all_events_url': 'url'
        }
    Called for each swimmer in a heat by get_best_swims_for_heat.

    In case of an error, the returned dictionary looks like this:
        {
            'Error': 'error message',
            [as many of the standard keys as possible]
        }
    '''
    debug_print(f'      Getting best swim for swimmer '
                f'{swimmer_data["name"]} ...')
    # get the swimmer id (needed for the Tempus request)
    swimmer_id = get_swimmer_id(swimmer_data)
    if swimmer_id is None:
        return {'Error' : 'Error getting Tempus swimmer id. '
                          f'Swimmer name: {swimmer_data["name"]}.'}
    
    # get the event id (needed for the Tempus request)
    event_name = ' '.join(event_name.split(' ')[:2]) # ensure format is correct
    event_id = get_event_id(event_name, pool)
    if event_id is None:
        return {'Error' : 'Error getting Tempus event id. '
                          f'Event name: {event_name}, Pool: {pool}.'}
    
    best_swim = dict()

    # add the all times url and all events url
    all_times_url = (f'https://www.tempusopen.se/index.php?r=swimmer/'
                     f'distance&id={swimmer_id}&event={event_id}')
    best_swim['all_times_url'] = all_times_url
    all_events_url = (f'https://www.tempusopen.se/index.php?r=swimmer/'
                      f'view&id={swimmer_id}')
    best_swim['all_events_url'] = all_events_url

    # get the meet name and date
    return_val = get_meet_name_and_date(swimmer_id, event_id)
    if return_val is None:
        best_swim['Error'] = 'First time swimming the event.'
        return best_swim
    meet_name, meet_date, backup_time = return_val
        
    best_swim['meet_name'] = meet_name
    best_swim['meet_date'] = meet_date
    
    # get the meet id and location
    return_val = get_meet_id_and_location(meet_name, meet_date)
    if return_val is None:
        best_swim['Error'] = 'Error getting LiveTiming meet id and location.'
        best_swim['final_time'] = backup_time
        return best_swim
    meet_id, meet_location = return_val

    result_url = (
        f'https://www.livetiming.se/results.php?cid={meet_id}&session=0&all=1')
    best_swim['result_url'] = result_url
    best_swim['meet_location'] = meet_location

    # get the splits
    meet_year = int(meet_date[:4])
    splits = get_splits_from_meet(meet_id, meet_year, swimmer_data, event_name)
    if splits is None:
        best_swim['Error'] = ('Error getting splits from LiveTiming. '
                              f'Meet id: {meet_id}.')
        best_swim['final_time'] = backup_time
        return best_swim
    
    best_swim['splits'] = splits
    best_swim['final_time'] = final_time(splits)
    best_swim['avg50'] = avg50(splits)
    if 'medley' in event_name.lower():
        best_swim['avg50'] = None

    return best_swim

def get_best_swims_for_heat(heat_rows: list, event_name: str, pool: str
                            ) -> dict:
    '''
    Iterates through the swimmers in a heat and gets the best swim for each
    swimmer. Called for each heat in an event by get_best_swims_for_event.
    '''
    debug_print('    Getting best swims for heat...')
    heat_best_swims = dict()
    for row in heat_rows:
        row_text = get_element_text(row)
        if (len(row_text) <= 2) or (not row_text[0].isdigit()): continue
        tds = row.find_all('td')
        element_texts = [get_element_text(td) for td in tds]
        element_texts = [text for text in element_texts if text != '']
        if len(element_texts) <= 3: continue # safety
        element_texts = (element_texts[1:] if element_texts[2][0].isalpha() 
                         else element_texts)
        lane = element_texts[0]
        swimmer_data = dict()
        swimmer_data['name'] = element_texts[1]
        swimmer_data['born'] = element_texts[2]
        club = element_texts[3]
        club = ' '.join([word.title() if len(word) > 2 else word 
                        for word in club.split(' ')])
        swimmer_data['club'] = club
        heat_best_swims[f'({lane}, {swimmer_data["name"]})'] = (
            get_best_swim_for_swimmer(swimmer_data, event_name, pool))
    return heat_best_swims

def get_best_swims_for_event(event_heat_list_url: str, num_heats: int
                             ) -> tuple[str, dict] | None:
    '''
    Iterates through the heats in an event and gets the best swims for each 
    heat. Makes a GET request to LiveTiming. Called for each event in a session
    by get_best_swims_for_session. Returns None if the event is a relay.
    '''
    debug_print('  Getting best swims for event...')
    event_heat_list_page = GET(event_heat_list_url, debug=DEBUG)
    if event_heat_list_page is None:
        debug_print(f'Error getting event heat list page: '
                    f'{event_heat_list_url}')
        return None
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
            if row_tokens[-1][1].isdigit():
                heat = row_tokens[-2]
            else:
                heat = 1
            if event_name is None:
                event_name = ' '.join(row_tokens[2:5])
                # skip relays and extralopp
                if (('x' in event_name.lower() and 
                    'mixed' not in event_name.lower()) or 
                    'extralopp' in event_name.lower()):
                    return None
            if total_heats is None:
                if row_tokens[-1][1].isdigit():
                    total_heats = int(row_tokens[-1].replace('(', '')
                                                    .replace(')', ''))
                else:
                    total_heats = 1
                progress_bar.set_num_heats(min(total_heats, num_heats))
            if (curr_heat is not None and 
                int(curr_heat) > total_heats - num_heats):
                # get best swims for the previous heat
                heat_best_swims = get_best_swims_for_heat(curr_heat_rows, 
                                                          event_name, pool)
                event_best_swims[curr_heat] = heat_best_swims
                progress_bar.update_heat(
                    int(curr_heat) if num_heats >= total_heats
                    else int(curr_heat) - (total_heats - num_heats))
            if curr_heat is not None:
                curr_heat_rows = []
            curr_heat = heat
            debug_print(f'    Heat: {curr_heat} of {total_heats}')
            continue
        if curr_heat is not None:
            curr_heat_rows.append(row)
    # get best swims for the last heat
    heat_best_swims = get_best_swims_for_heat(curr_heat_rows, event_name, 
                                              pool)
    event_best_swims[curr_heat] = heat_best_swims
    progress_bar.update_heat(int(curr_heat) if num_heats >= total_heats
                             else int(curr_heat) - (total_heats - num_heats))
    return event_name, event_best_swims
        
def get_best_swims_for_session(session_soup, num_heats: int) -> dict:
    '''
    Iterates through the events in a session and gets the best swims for each
    event. Returns a dictionary where the keys are event names and the values
    are dictionaries where the keys are lane numbers and swimmer names, and the
    values are dictionaries with their best swims. Called once by 
    get_meet_and_session_data.
    '''
    debug_print('Getting best swims for session...')
    session_trs = session_soup.find_all('tr')
    session_best_swims = dict()
    for row in session_trs[1:]:
        tds = row.find_all('td')
        event_number = get_element_text(tds[0])
        debug_print(f'  Event number: {event_number} of '
                    f'{progress_bar.num_events}')
        for td in tds:
            if get_element_text(td) == 'Heatlista':
                link = td.find('a')['href']
                event_heat_list_url = f'https://www.livetiming.se/{link}'
                return_val = get_best_swims_for_event(event_heat_list_url,
                                                      num_heats)
                if return_val is None: 
                    continue
                event_name, event_best_swims = return_val
                session_best_swims[f'({event_number}, {event_name})'] = (
                    event_best_swims)
        progress_bar.update_event(int(event_number))
        
    return session_best_swims

def get_meet_and_session_data(session_url: str, num_heats: int) -> dict:
    '''
    Returns a dictionary with the meet name, session number, and the best swims
    for the session. Called once by retrieve_data. Makes a GET request to 
    LiveTiming.
    '''
    session_page = GET(session_url, debug=DEBUG)
    if session_page is None:
        debug_print(f'Error getting session page: {session_url}')
        return {'Error' : 'Error getting session page.'}
    session_soup = BeautifulSoup(session_page.content, 'html.parser')
    tbody = session_soup.find('tbody')
    num_events = len(tbody.find_all('tr')) - 1
    progress_bar.set_num_events(num_events)
    meet_name = ' '.join(get_element_text(session_soup.find('h1'))
                         .split(' ')[2:])
    session_number = session_url.split('=')[-1]
    session_best_swims = get_best_swims_for_session(session_soup, num_heats)
    session_data = dict()
    session_data['meet_name'] = meet_name
    session_data['session_number'] = session_number
    session_data['events'] = session_best_swims
    return session_data

def retrieve_data(session_url: str, num_heats: int) -> dict:
    '''
    The function called by main.py to retrieve session data. Returns a
    dictionary with the meet name, session number, and the best swims for the
    session. 

    A progress bar is displayed while the data is being retrieved. The progress
    bar is updated for each event and heat. 
    
    The time taken to retrieve the data is measured and printed.
    '''
    # load caches from files
    load_stored_swimmer_id_cache()
    load_stored_meet_id_and_location_cache()
    load_stored_meet_results_cache()
    session_data = time_function(get_meet_and_session_data,
                                 session_url, num_heats)
    # save caches to files
    save_swimmer_id_cache()
    save_meet_id_and_location_cache()
    save_meet_results_cache()

    return session_data
