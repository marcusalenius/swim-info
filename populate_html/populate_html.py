'''
This file contains the functions that populate index.html with the session
data.
'''

# external libraries
from bs4 import BeautifulSoup
import json

# templates
from populate_html.html_snippet_templates import (EVENT_ITEM_TEMPLATE,
                                                  RIGHT_COLUMN_TEMPLATE,
                                                  HEAT_CONTAINER_TEMPLATE,
                                                  HEAT_ITEM_TEMPLATE,
                                                  HEAT_CONTENT_TEMPLATE,
                                                  SWIMMER_CONTAINER_TEMPLATE,
                                                  SWIMMER_ITEM_TEMPLATE,
                                                  SWIMMER_CONTENT_TEMPLATE,
                                                  SPLIT_ROW_TEMPLATE)

# helper functions
from populate_html.utilities import format_date                                  


###############################################################################
# Helper functions for add_right_columns (reverse order)
###############################################################################

def add_splits(swimmer_content_soup, splits: dict) -> None:
    '''
    Adds 'split-row's to 'swimmer-content-splits'.
    '''
    splits_list = list(splits.items())
    splits_list = [(int(key[:-1]), value) for key, value in splits_list]
    splits_list.sort(key=lambda key_value: key_value[0])
    for split_index in range(0, len(splits_list), 2):
        split_row_soup = BeautifulSoup(SPLIT_ROW_TEMPLATE, 'html.parser')
        for col_index in range(2):
            splits = splits_list[split_index + col_index]
            distance = f'{str(splits[0])}m:'
            time = splits[1]
            time_tokens = time.split(' ')
            if len(time_tokens) == 1:
                distance_time = time
                last_fifty = None
            else:
                distance_time = time_tokens[0]
                last_fifty = time_tokens[1]
            col = split_row_soup.find(
                'div', class_=f'split-row-col{col_index+1}')
            col.find('p', class_='split-row-distance').string = distance
            col.find('p', class_='split-row-time').string = distance_time + ' '
            if last_fifty is not None:
                span_soup = BeautifulSoup(
                    f'<span class="last-50 pt14-gray3">{last_fifty}</span>', 
                    'html.parser')
                col.find('p', class_='split-row-time').append(span_soup)
        
        # add to swimmer content
        swimmer_content_soup.find('div', 
                                  class_='swimmer-content-splits').append(
                                        split_row_soup)

def add_swimmers(heat_content_soup, swimmers: dict) -> None:
    '''
    Adds 'swimmer-list' to 'heat-content'.
    '''
    swimmers = list(swimmers.items())
    # key has format '(lane, name)'
    swimmers.sort(key=lambda swimmer: int(swimmer[0][1:-1].split(', ')[0]))
    for swimmer_string, best_swim_info in swimmers:
        swimmer_string = swimmer_string[1:-1]
        swimmer_tokens = swimmer_string.split(', ')
        lane_number = swimmer_tokens[0]
        swimmer_name = swimmer_tokens[1]

        swimmer_container_soup = BeautifulSoup(SWIMMER_CONTAINER_TEMPLATE, 
                                               'html.parser')
        # add swimmer item
        swimmer_item_soup = BeautifulSoup(SWIMMER_ITEM_TEMPLATE, 'html.parser')
        swimmer_item_soup.find('p', class_='swimmer-item-lane').string = (
            lane_number)
        swimmer_item_soup.find('p', class_='swimmer-item-name').string = (
            swimmer_name)
        if 'Error' in best_swim_info:
            swimmer_container_soup.find('div', 
                                        class_='swimmer-container').append(
                                            swimmer_item_soup)
            swimmer_content_soup = BeautifulSoup(SWIMMER_CONTENT_TEMPLATE, 
                                            'html.parser')
            swimmer_container_soup.find('div', 
                                        class_='swimmer-container').append(
                                            swimmer_content_soup)
            heat_content_soup.find('div', class_='swimmer-list').append(
                swimmer_container_soup)
            continue
        swimmer_item_soup.find('p', class_='swimmer-item-best').string = (
            best_swim_info['final_time'])
        swimmer_container_soup.find('div', class_='swimmer-container').append(
                swimmer_item_soup)

        # add swimmer content
        swimmer_content_soup = BeautifulSoup(SWIMMER_CONTENT_TEMPLATE, 
                                            'html.parser')
        swimmer_content_soup.a['href'] = best_swim_info['result_url']
        swimmer_content_soup.a.string = best_swim_info['meet_name']
        date = format_date(best_swim_info['meet_date'])
        swimmer_content_soup.find(
            'div', class_='swimmer-content-text').p.string = (
                f'{best_swim_info["meet_location"]}, {date}')
        if best_swim_info['avg50'] is not None:
            # add avg50 if it exists
            swimmer_content_soup.find('p', class_='avg50-time').string = (
                best_swim_info['avg50'])
        else:
            # otherwise remove the avg50 div
            swimmer_content_soup.find('div', class_='swimmer-content-avg50'
                                      ).decompose()
        add_splits(swimmer_content_soup, best_swim_info['splits'])
        swimmer_container_soup.find('div', class_='swimmer-container').append(
                swimmer_content_soup)

        # add to heat content
        heat_content_soup.find('div', class_='swimmer-list').append(
            swimmer_container_soup)

def add_heats(right_column_soup, heats: dict) -> None:
    '''
    Adds 'heat-list' to 'right-column'.
    '''
    heats = list(heats.items())
    heats.sort(key=lambda heat: int(heat[0]))
    number_of_heats = heats[-1][0]
    for number, swimmers in heats:
        heat_container_soup = BeautifulSoup(HEAT_CONTAINER_TEMPLATE, 
                                            'html.parser')
        heat_container_div = heat_container_soup.find(
            'div', class_='heat-container')
        # add heat item
        heat_item_soup = BeautifulSoup(HEAT_ITEM_TEMPLATE, 'html.parser')
        heat_item_soup.p.string = f'Heat {number} ({number_of_heats})'
        heat_container_div.append(heat_item_soup)
        # add heat content
        heat_content_soup = BeautifulSoup(HEAT_CONTENT_TEMPLATE, 'html.parser')
        add_swimmers(heat_content_soup, swimmers)
        heat_container_div.append(heat_content_soup)

        # add to right column
        right_column_soup.find('div', class_='heat-list').append(
            heat_container_soup)

###############################################################################
# Functions directly called by populate_html
###############################################################################

def populate_page_title(page_soup, meet_name: str, session_number: str) -> None:
    '''
    Populates the h1 tag with the meet name and the h2 tag with the session 
    number.
    '''
    page_soup.h1.string = meet_name
    page_soup.h2.string = f'Pass {session_number}'

def populate_event_menu(page_soup, events: dict) -> None:
    '''
    Populates the event menu with the events.
    '''
    for event_string in events.keys():
        event_string = event_string[1:-1]
        event_tokens = event_string.split(', ')
        event_number = event_tokens[0]
        event_name = event_tokens[1]

        event_soup = BeautifulSoup(EVENT_ITEM_TEMPLATE, 'html.parser')
        event_soup.find('div', class_='event-item')['id'] = (
            f'event-item-{event_number}')
        event_soup.find('p', class_='event-item-number').string = event_number
        event_soup.find('p', class_='event-item-name').string = event_name

        # add to page
        page_soup.find('div', class_='event-menu').append(event_soup)

def add_right_columns(page_soup, events: dict) -> None:
    '''
    Adds right columns to the page, one for each event.
    '''
    for event_string, heats in events.items():
        event_string = event_string[1:-1]
        event_tokens = event_string.split(', ')
        event_number = event_tokens[0]
        event_name = event_tokens[1]

        right_column_soup = BeautifulSoup(RIGHT_COLUMN_TEMPLATE, 'html.parser')
        right_column_soup.find('div', class_='right-column')['id'] = (
            f'right-column-{event_number}')
        right_column_soup.h3.string = f'Gren {event_number}, {event_name}'

        add_heats(right_column_soup, heats)

        # add to page
        page_soup.find('div', class_='two-columns').append(right_column_soup)

###############################################################################

def populate_html(session_data: dict) -> None:
    '''
    The function called by main.py to populate index.html. Given the session 
    data, populates index.html with the data.
    '''
    # get template from index_template.html
    with open('ui/index_template.html', 'r', encoding='utf-8') as file:
        page_soup = BeautifulSoup(file, 'html.parser')
    populate_page_title(page_soup, session_data['meet_name'], 
                        session_data['session_number'])
    populate_event_menu(page_soup, session_data['events'])
    add_right_columns(page_soup, session_data['events'])
    # write to index.html
    with open('ui/index.html', 'w', encoding='utf-8') as file:
        file.write(str(page_soup))
    
    print('Application ready. Open ui/index.html with Live Server to view.')
