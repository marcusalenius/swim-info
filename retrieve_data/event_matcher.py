'''
The file contains the function is_correct_event, which is used to determine if
a row text is the correct event.
'''

STROKE_TRANSLATIONS = {
    'butterfly': 'fjärilsim',
    'backstroke': 'ryggsim',
    'breaststroke': 'bröstsim',
    'freestyle': 'frisim'
}

def is_correct_event(row_text: str, event_name: str) -> bool:
    '''
    Returns True if the row text is the correct event, False otherwise.
    '''
    row_tokens = row_text.lower().split(' ')
    row_event_tokens = row_tokens[2:4]
    name_event_tokens = event_name.lower().split(' ')
    if row_event_tokens == name_event_tokens:
        return True
    row_event_tokens = [STROKE_TRANSLATIONS.get(token, token) 
                        for token in row_event_tokens]
    name_event_tokens = [STROKE_TRANSLATIONS.get(token, token) 
                         for token in name_event_tokens]
    return row_event_tokens == name_event_tokens
