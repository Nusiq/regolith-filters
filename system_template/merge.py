from typing import Dict, List, TypeVar, Any
from enum import Enum, auto

class ListMergePolicy(Enum):
    GREATER_LENGHT = auto()
    SMALLER_LENGHT = auto()
    B_LENGHT = auto()
    APPEND = auto()

T = TypeVar('T')

def deep_merge_objects(
    a: Any, b: T,
    list_merge_policy: ListMergePolicy=ListMergePolicy.GREATER_LENGHT
) -> T:
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
        return deep_merge_dicts(a, b, list_merge_policy)  # type: ignore
    elif isinstance(a, list):  # Both types are lists
        return deep_merge_lists(a, b, list_merge_policy)  # type: ignore
    # Both types are smoething unknown
    return b

def deep_merge_dicts(
        a: Dict[Any, Any], b: Dict[Any, Any],
        list_merge_policy: ListMergePolicy=ListMergePolicy.GREATER_LENGHT
) -> Dict[Any, Any]:
    '''
    Merges two dictionaries A and B recursively. In case of conflicts (
    situations where merging is not possible) the value from B overwrites value
    from A.
    '''
    result: Dict[Any, Any] = {}
    # a.keys() | b.keys() could be used but it doesn't preserve order
    keys = list(a.keys()) + list(b.keys())
    used_keys: set[Any] = set()
    for k in keys:
        if k in used_keys:
            continue
        used_keys.add(k)
        if k in b:
            if k not in a: # in B not in A
                result[k] = b[k]
                continue
            result[k] = deep_merge_objects(a[k], b[k], list_merge_policy)
        elif k in a:  # in A not in B
            result[k] = a[k]
    return result

def deep_merge_lists(
    a: List[Any], b: List[Any],
    list_merge_policy: ListMergePolicy=ListMergePolicy.GREATER_LENGHT
) -> List[Any]:
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
