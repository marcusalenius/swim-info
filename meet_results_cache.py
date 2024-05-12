'''
This file contains a cache for meet results. The keys are the IDs of the meets,
and the values are lists of the table row text of the meet results.
'''
import json

# { 'id' : ['row_text', 'row_text', ...] }
meet_results_cache: dict[str, list[str]] = dict()

def load_stored_meet_results_cache() -> None:
    '''
    Loads the stored cache from a file.
    '''
    global meet_results_cache
    try:
        with open('meet_results_cache.json', 'r') as file:
            meet_results_cache = json.load(file)
    except json.decoder.JSONDecodeError: 
        pass

def save_meet_results_cache() -> None:
    '''
    Saves the cache to a file.
    '''
    with open('meet_results_cache.json', 'w') as file:
        json.dump(meet_results_cache, file, indent=4)

def get_cached_meet_results(meet_id: str) -> list[str] | None:
    '''
    Gets the results of a meet from the cache. Returns None if the meet is not
    in the cache.
    '''
    return meet_results_cache.get(meet_id)

def add_meet_results_to_cache(meet_id: str, trs: list[str]) -> None:
    '''
    Adds the results of a meet to the cache.
    '''
    meet_results_cache[meet_id] = trs
