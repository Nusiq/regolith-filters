# Change log
## 2.0.2
Updated the `better-json-tools` dependency to `~=1.0.3`. It fixes epxorting the
JSON files with quotes inside the strings.
## 2.0.1
Updated `regolith-subfunctions` dependency to `~=1.1`. This allows using
comments in the `scope.json` file. For `mcfunction` and `lang` files
evaluation.
## 2.0.0
The `.lang` and `.mcfunction` files can be evaluated using the subfunctions
filter with the scope defined in the `_map.py` file.
## 1.2.0
- Added support for using glob patterns in the `_map.py` file for the source
files.
- The `.material` files are treated the same as the JSON files.
- Better error messages.
- Merging dictionaries (JSON files) preserves the order of the keys.
## 1.1.1
The filter uses the `CompactEncoder` from the `better_json_tools` package for
exporting the JSON files.
## 1.1.0
The scope files can use comments.
## 1.0.0
- renamed `system_scope.json` to `_scope.json`
- removed the `data` folder from the systems (everything is in the root)
- added `AUTO` keyword that can be used with the "target" property of a system in `_map.py`
- renamed `system_template.py` to `_map.py`
- removed `use_global_scope` property from the system configuration (enabled by default)
- improved README file
## Older versions
Older versions are not documented here. You can check the hisotry of the commit
messages.