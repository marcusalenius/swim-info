'''

'''

###############################################################################

### Edit the following constants:

# The URL of the live timing session to retrieve data from.
LIVETIMING_SESSION_URL = (
    'https://www.livetiming.se/program.php?cid=8051&session=1')

# Number of heats per event to get the best swim splits for. Set to 1 or above.
NUM_HEATS = 2

###############################################################################

from retrieve_data.retrieve_data import retrieve_data
from populate_html.populate_html import populate_html

def main():
    session_data = retrieve_data(LIVETIMING_SESSION_URL, NUM_HEATS)
    populate_html(session_data)

if __name__ == '__main__':
    main()
