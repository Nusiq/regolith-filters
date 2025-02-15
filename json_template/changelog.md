# Changelog
## 2.3.2
More strict `requirements.txt` file. No changes in the code.

## 2.3.1
Updated the `regolith-json-template` library to version 1.3.1.

Enables using the `Ellipsis` (`...`) in the lists.

## 2.3.0
Updated the `regolith-json-template` library to version 1.3.0.

When a value in a dictionary evaluates to `Ellipsis` (`...`), the key-value pair is removed from the dictionary. This can be used to conditionally remove keys from the dictionary.

## 2.2.0
Updated the `regolith-json-template` library to version 1.2.0.

This update allows using `JoinStr()` function for joining lists of strings that start with this object into a single string.

This update also adds `random` module to the default scope.

## 2.1.0
Updated the `regolith-json-template` library to version 1.1.0.

This update allows using special `__unpack__` keys in the dictionaries, which are children of a list. The value of the `__unpack__` key is a list of dictionaries to be used as the scope for the dictionary that contains the `__unpack__` key. This creates multiple objects which are unpacked into the parent list in place of the original dictionary. If the unpacked object shouldn't be a dictionary, but a string, number, etc., then the special `__value__` key can be used in conjunction with `__unpack__`. The evaluated value of `__value__` will be used instead of the dictionary.
## 2.0.1
Moved some of the code to an external library called `regolith-json-template`.
## 2.0.0
Renamed the `Ext` class to `K` inside the template files and to
`JsonTemplateK` internally in the code of the filter.

## 1.0.0
Initial release.

Features:
- Evaluate Python expressions in JSON files in keys/strings surrounded by backticks.
- Keys that evaluate to lists can generate multiple objects
- Use variables defined in the `scope.json` file
- The `Ext` that can temporarlily modify the scope
