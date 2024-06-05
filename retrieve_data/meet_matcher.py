''''
This file contains the function meet_names_match, which is used to match a meet
name from Tempus to a meet name from LiveTiming, and its helper functions.
'''
import re
from retrieve_data.utilities import collapse_whitespace

MEET_NAME_ABBREVIATIONS = {
    ('ungdoms', 'gp') : 'ugp',
    ('ungdoms', 'grand', 'prix') : 'ugp',
    ('långbana',) : '50',
    ('kortbana',) : '25',
    ('bockstendsdoppet',) : 'bockstensdoppet', # misspelled in Tempus
    ('eriksdal',) : 'eriksdalsbadet'
}

MEET_NAME_REMOVABLE_TOKENS = {
    'med', 'och', 'i', 'på', 'hos', 'vid', 'till', 'för', 'av', 'en',
    'ett', 'två', 'tre', 'fyra', 'bassäng', 'bassängen', 'simhall', 
    'simhallen', 'sim', 'simning', 'simningen', 'simtävling', 'simtävlingen',
    'arena', 'arenan', 'pool', 'poolen', 'bad', 'badet', 'badhus', 'badhuset',
    'simarena', 'simarenan', 'simbassäng', 'simbassängen', '&'
}

# copy-paste the key from the UI and add year to it and copy-paste the value 
# from LiveTiming
HARDCODED_NAMES = {
    'JSM/Sum-Sim äldre & Sum-Sim 16 år 2021' : 
        'JSM/Sum-Sim äldre & Sum-Sim 16 år (50m)',
    'Eskilstuna Sprint (25m) 2023' : 
        'UGP 2 2023 (50m), Eskilstuna & Eskilstuna-Sprint',
    'Zoggs Zwim Stockholm - Summer Cup 2023' : 
        'Zoggs Zwim - Summer Cup',
    'HEAD Summer Cup 2021' :
        'Polisen Head Summer Cup',
    'Eskilstuna Sprint 2022' :
        'UGP 2 2022 med Eskilstuna Sprint',
    'DM-JDM (50m) 2022 Eskilstuna' :
        'DM-JDM (50m) 2022 Mellansvenska'
}

def hardcoded_name(name: str) -> str:
    '''
    Returns the hardcoded name for the given name if it exists, otherwise
    returns the name unchanged.
    '''
    return HARDCODED_NAMES.get(name, name)

def clean_meet_name(name: str) -> str:
    '''
    Cleans a meet name by removing unnecessary characters and adding spaces
    between words and numbers.
    '''
    name = name.replace('(', '').replace(')', '')
    name = name.replace(',', ' ').replace('-', ' ').replace('.', ' ')
    name = name.replace('50m', '50').replace('25m', '25')
    # add space between words and numbers
    name = ' '.join(re.compile(r'(\d+|\D+)').findall(name))
    return collapse_whitespace(name)

def make_abbreviations(tokens: set[str]) -> None:
    '''
    Replaces any tokens that are a key of MEET_NAME_ABBREVIATIONS with the
    corresponding value.
    '''
    for key, value in MEET_NAME_ABBREVIATIONS.items():
        key = set(key)
        if key.issubset(tokens):
            tokens -= key
            tokens.add(value)

def meet_names_match(name1: str, date1: str, name2: str, date2: str) -> bool:
    '''
    Returns True if the two meet names are similar enough to be considered the 
    same meet. This function is used to match a meet name from Tempus to a meet 
    name from LiveTiming.
    '''
    name1, name2 = hardcoded_name(name1), hardcoded_name(name2)
    name1, name2 = name1.lower(), name2.lower()
    if name1 == name2: return True
    name1, name2 = clean_meet_name(name1), clean_meet_name(name2)
    if name1 == name2: return True
    year1, year2 = date1[:4], date2[:4]
    if year1 != year2: return False
    name1_tokens = set(name1.split(' '))
    name2_tokens = set(name2.split(' '))
    # delete arbitrary tokens
    name1_tokens -= MEET_NAME_REMOVABLE_TOKENS
    name2_tokens -= MEET_NAME_REMOVABLE_TOKENS
    make_abbreviations(name1_tokens)
    make_abbreviations(name2_tokens)
    # make sure both sets contain the year
    name1_tokens |= {year1}
    name2_tokens |= {year2}
    return name1_tokens == name2_tokens 
