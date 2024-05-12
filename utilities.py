'''
This file contains utility functions that are used in the main script and other
supporting files.
'''

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

def get_element_text(row) -> str:
    '''
    Gets the text of an element, in a nice format.
    '''
    return collapse_whitespace(row.get_text().replace('\xa0', ' ').strip())
