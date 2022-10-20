def dict_merge(source, destination):
    """ Merge two dictionaries. Only keys which are not present in destination
    will be copied from source, anything else will be kept untouched. Function
    will return a new dict which has the merged key/value pairs. """
    from copy import deepcopy
    tmp = deepcopy(destination)

    for key, value in source.items():
        if key not in tmp:
            tmp[key] = value
        elif isinstance(source[key], dict):
            tmp[key] = dict_merge(source[key], tmp[key])

    return tmp
