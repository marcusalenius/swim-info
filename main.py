'''

'''

###############################################################################

### Edit the following constants:

# The URL of the live timing session to retrieve data from.
LIVETIMING_SESSION_URL = (
    'https://www.livetiming.se/program.php?cid=8051&session=1')

# Number of heats per event to get the best swim splits for. Set to 1 or above.
NUM_HEATS = 100

# Whether to retrieve new data or just populate the html with the existing data.
RETRIEVE_NEW_DATA = True

###############################################################################

import json
from retrieve_data.retrieve_data import retrieve_data
from populate_html.populate_html import populate_html

def main():
    '''
    Main function. If RETRIEVE_NEW_DATA is set to True, retrieves the session
    data from LIVETIMING_SESSION_URL with NUM_HEATS heats of each event, saves 
    it to session_data.json, and populates the html. If set to False just
    populates the html with the existing data in session_data.json.
    '''
    if RETRIEVE_NEW_DATA:
        session_data = retrieve_data(LIVETIMING_SESSION_URL, NUM_HEATS)
        with open('session_data.json', 'w', encoding='utf-8') as file:
            json.dump(session_data, file, indent=4, sort_keys=True)
    else:
        with open('session_data.json', 'r', encoding='utf-8') as file:
            session_data = json.load(file)

    populate_html(session_data)

if __name__ == '__main__':
    main()
