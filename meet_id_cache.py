'''
This file contains a cache for meet IDs and locations. The keys are the names
of the meets, and the values are tuples containing the IDs and locations of 
the meets.
'''
import json

# { 'meet_name' : ('id', 'location') }
meet_id_and_location_cache: dict[str, tuple[str, str]] = dict()

def load_stored_meet_id_and_location_cache() -> None:
    '''
    Loads the stored cache from a file.
    '''
    global meet_id_and_location_cache
    try:
        with open('meet_id_cache.json', 'r') as file:
            meet_id_and_location_cache = json.load(file)
    except json.decoder.JSONDecodeError: 
        pass

def save_meet_id_and_location_cache() -> None:
    '''
    Saves the cache to a file.
    '''
    with open('meet_id_cache.json', 'w') as file:
        json.dump(meet_id_and_location_cache, file, indent=4)

def get_cached_meet_id_and_location(meet_name: str) -> str | None:
    '''
    Gets the ID and location of a meet from the cache. Returns None if the meet 
    is not in the cache.
    '''
    return meet_id_and_location_cache.get(meet_name)

def add_meet_id_and_location_to_cache(meet_name: str, id: str, 
                                      location: str) -> None:
    '''
    Adds a meet's ID and location to the cache.
    '''
    meet_id_and_location_cache[meet_name] = (id, location)
