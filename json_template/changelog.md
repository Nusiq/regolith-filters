# Changelog
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
