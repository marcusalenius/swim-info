'''
This file contains utility and helper functions that are used in 
populate_html.py.
'''

###############################################################################
# Utility function for date formatting
###############################################################################

MONTH_NAMES = {
    '01': 'januari',
    '02': 'februari',
    '03': 'mars',
    '04': 'april',
    '05': 'maj',
    '06': 'juni',
    '07': 'juli',
    '08': 'augusti',
    '09': 'september',
    '10': 'oktober',
    '11': 'november',
    '12': 'december'
}

def format_date(date: str) -> str:
    '''
    Converts the date format from 'YYYY-MM-DD' to 'day month year'.
    '''
    year, month, day = date.split('-')
    return f'{str(int(day))} {MONTH_NAMES[month]} {year}'
