

def convert_times_from_splits(non_none_splits: list[dict[str, str]]
                              ) -> list[tuple[int]]:
    '''
    Grabs the final time from each split and converts it to a tuple of minutes,
    seconds, and hundredths of a second. Returns a list of these tuples.
    '''
    times_in_mins_secs_hundredths = []
    for splits in non_none_splits:
        values = list(splits.values())
        remove_last_fifty_time = lambda item: item.split(' ')[0]
        times = list(map(remove_last_fifty_time, values))
        get_mins_secs_hundredths = (
            lambda time: time.replace(':', '.').split('.'))
        separated_times = list(map(get_mins_secs_hundredths, times))
        convert_to_ints = lambda separated_time: list(map(int, separated_time))
        separated_times_int = list(map(convert_to_ints, separated_times))
        add_minutes = lambda separated_time: (tuple([0] + separated_time )
                                              if len(separated_time) == 2 
                                              else tuple(separated_time))
        three_item_times = list(map(add_minutes, separated_times_int))
        three_item_times.sort(key=lambda x: x[0]*60 + x[1] + x[2]/100,
                              reverse=True)
        times_in_mins_secs_hundredths.append(three_item_times[0])
    return times_in_mins_secs_hundredths

def get_fastest_swim_index(times: list[tuple[int]]) -> int:
    '''
    Returns the index of the fastest swim from a list of times. The times
    should be in the format (minutes, seconds, hundredths).
    '''
    sorted_times = sorted(times, key=lambda x: x[0]*60 + x[1] + x[2]/100)
    return times.index(sorted_times[0])

def fastest_swim(all_splits: list[dict[str, str]]) -> dict[str, str] | None:
    '''
    Returns the splits of the fastest swim from a list of splits. If all the
    splits are None, returns None. If there is only one non-None split, returns
    that split. If there are multiple non-None splits, returns the split of the
    fastest swim.
    '''
    non_none_splits = [splits for splits in all_splits if splits is not None]
    if len(non_none_splits) == 0:
        return None
    elif len(non_none_splits) == 1:
        return non_none_splits[0]
    times_in_mins_secs_hundredths = convert_times_from_splits(non_none_splits)
    fastest_swim_index = get_fastest_swim_index(times_in_mins_secs_hundredths)
    return all_splits[fastest_swim_index]

def get_fifty_results(row_text: str) -> str:
    '''
    Returns the time of a 50m swim from the row text of a swim.
    '''
    row_tokens = row_text.split(' ')
    if row_tokens[-1][0] == '+':
        return row_tokens[-2]
    return row_tokens[-1]

def final_time(splits: dict[str, str]) -> str:
    '''
    Returns the final time of a swim from the splits.
    '''
    assert(splits is not None)
    splits_list = list(splits.items())
    # make keys integers
    splits_list = [(int(key[:-1]), value) for key, value in splits_list]
    # remove the last 50m time from splits_list
    splits_list = [(key, value.split(' ')[0]) for key, value in splits_list]
    splits_list.sort(key=lambda key_value: key_value[0])
    return splits_list[-1][1]

def avg50(splits: dict[str, str]) -> str | None:
    '''
    Returns the average 50m time of a swim from the splits. The first and
    last 50m splits are ignored. If the swim is 100m or less, returns None.
    '''
    assert(splits is not None)
    if len(splits) <= 2:
        return None
    splits = list(splits.items())
    # make keys integers
    splits = [(int(key[:-1]), value) for key, value in splits]
    # keep the last 50m time from splits
    fifty_times = []
    for key, value in splits:
        time_tokens = value.split(' ')
        # 50m
        if len(time_tokens) == 1:
            fifty_times.append((key, time_tokens[0]))
        else:
            fifty_times.append((key, time_tokens[1][1:-1]))
    fifty_times.sort(key=lambda key_value: key_value[0])
    # exclude the first and last 50m times
    fifty_times = fifty_times[1:-1]
    fifty_times = [float(value) for _, value in fifty_times]
    avg_fifty = sum(fifty_times)/len(fifty_times)
    avg_fifty = round(avg_fifty, 2)
    return str(avg_fifty)
