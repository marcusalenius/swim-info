'''
This file contains a cache for swimmer IDs. The keys are the names, birth 
years, and clubs of the swimmers, and the values are the IDs of the swimmers 
in Tempus.
'''
import json

# { 'name, born, club' : 'id' }
swimmer_id_cache: dict[tuple[str, str, str], str] = dict()

# Local helper function
def get_swimmer_id_cache_key(swimmer_data: dict[str, str]) -> str:
    '''
    Gets the key for the swimmer id cache from swimmer data.
    '''
    return (f'{swimmer_data["name"]}, {swimmer_data["born"]}, ' 
            f'{swimmer_data["club"]}')


def load_stored_swimmer_id_cache() -> None:
    '''
    Loads the stored cache from a file.
    '''
    global swimmer_id_cache
    try:
        with open('cache/swimmer_id_cache.json', 'r') as file:
            swimmer_id_cache = json.load(file)
    except json.decoder.JSONDecodeError: 
        pass

def save_swimmer_id_cache() -> None:
    '''
    Saves the cache to a file.
    '''
    with open('cache/swimmer_id_cache.json', 'w') as file:
        json.dump(swimmer_id_cache, file, indent=4)

def get_cached_swimmer_id(swimmer_data: dict[str, str]) -> str | None:
    '''
    Gets the ID of a swimmer from the cache. Returns None if the swimmer is not
    in the cache.
    '''
    key = get_swimmer_id_cache_key(swimmer_data)
    return swimmer_id_cache.get(key)

def add_swimmer_id_to_cache(swimmer_data: dict[str, str], id: str) -> None:
    '''
    Adds a swimmer's ID to the cache.
    '''
    key = get_swimmer_id_cache_key(swimmer_data)
    swimmer_id_cache[key] = id
   