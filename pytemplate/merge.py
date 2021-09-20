from typing import Dict, List
from enum import Enum, auto

class ListMergePolicy(Enum):
    GREATER_LENGHT = auto()
    SMALLER_LENGHT = auto()
    B_LENGHT = auto()
    APPEND = auto()

def deep_merge_objects(a, b, list_merge_policy=ListMergePolicy.GREATER_LENGHT):
    '''
    Merges two JSON objeccts A and B recursively.  In case of conflicts (
    situations where merging is not possible) the value from B overwrites value
    from A. The function doesn't always create a copy of parts of A and B.
    Sometimes uses references to objects that already exist to A or B which
    means that editing returned structure may edit some valeus in A or B.
    '''
    # in A and in B
    if type(a) != type(b):  # different types unable to merge
        return b
    # Both types are the same
    if isinstance(a, dict):  # Both types are dicts
        return deep_merge_dicts(a, b, list_merge_policy)
    elif isinstance(a, list):  # Both types are lists
        return deep_merge_lists(a, b, list_merge_policy)
    # Both types are smoething unknown
    return b

def deep_merge_dicts(
        a: Dict, b: Dict, list_merge_policy=ListMergePolicy.GREATER_LENGHT):
    '''
    Merges two dictionaries A and B recursively. In case of conflicts (
    situations where merging is not possible) the value from B overwrites value
    from A.
    '''
    result = {}
    for k in (a.keys() | b.keys()):
        if k in b:
            if k not in a: # in B not in A
                result[k] = b[k]
                continue
            result[k] = deep_merge_objects(a[k], b[k], list_merge_policy)
        elif k in a:  # in A not in B
            result[k] = a[k]
    return result

def deep_merge_lists(
        a: List, b: List, list_merge_policy=ListMergePolicy.GREATER_LENGHT):
    '''
    Merges two lists A and B recursively. In case of conflicts (
    situations where merging is not possible) the value from B overwrites value
    from A.
    '''
    # GREATER_LENGHT is the default
    # if list_merge_policy is ListMergePolicy.GREATER_LENGHT:
    list_len = max(len(a), len(b))
    if list_merge_policy is ListMergePolicy.SMALLER_LENGHT:
        list_len = min(len(a), len(b))
    elif list_merge_policy is ListMergePolicy.B_LENGHT:
        list_len = len(b)
    elif list_merge_policy is ListMergePolicy.APPEND:
        for b_item in b:
            a.append(b_item)
        return a
    result = [None]*list_len
    for i in range(list_len):
        if i < len(b):
            if i >= len(a): # in B not in A
                result[i] = b[i]
                continue
            # in B and in A
            result[i] = deep_merge_objects(a[i], b[i], list_merge_policy)
        elif i < len(a):  # in A not in B
            result[i] = a[i]
    return result

def test():
    '''Prints some test results of the deep_merge_objects() function.'''
    print(
        'MERGE RESULTS FOR:\n'
        '{"A": [1, {"X": 11, "Y": 22}, {"Z": 333}], "B": [1, 2, 3]}\n'
        '{"A": [1, {"Z": 33},{"X": 111, "Y": 222}, {"ZZ": 123}], "B": [4, 5]}')
    print("::Default mode (GREATER_LENGHT)::")
    result = deep_merge_objects(
        {"A": [1, {"X": 11, "Y": 22}, {"Z": 333}], "B": [1, 2, 3]},
        {"A": [1, {"Z": 33},{"X": 111, "Y": 222}, {"ZZ": 123}], "B": [4, 5]},)
    print(result)

    print("::SMALLER_LENGHT mode::")
    result = deep_merge_objects(
        {"A": [1, {"X": 11, "Y": 22}, {"Z": 333}], "B": [1, 2, 3]},
        {"A": [1, {"Z": 33},{"X": 111, "Y": 222}, {"ZZ": 123}], "B": [4, 5]},
        ListMergePolicy.SMALLER_LENGHT)
    print(result)

    print("::B_LENGHT mode::")
    result = deep_merge_objects(
        {"A": [1, {"X": 11, "Y": 22}, {"Z": 333}], "B": [1, 2, 3]},
        {"A": [1, {"Z": 33},{"X": 111, "Y": 222}, {"ZZ": 123}], "B": [4, 5]},
        ListMergePolicy.B_LENGHT)
    print(result)

# if __name__ == '__main__':
#     test()