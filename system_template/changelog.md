# Change log
## 3.3.0
Updated the subfunctions module to 1.2.0. The same version that is used by the subfunctions filter version 2.1.0. This allows creating subfunctions from the 'schedule' command (you can check the 'subfunctions' filter's README for more information).

## 3.2.1
Added `.material` to the default `auto_map.json` file.

## 3.2.0
## Groups
The systems can now be groupped together in directories called groups.
- Any directory that contains a `_group_scope.json` file is considered a group.
- The `_group_scope.json` file can define variables that are visible to all systems in the group. During the evaluation of the system it is merged with the global and the system scope. It overrides the global scope and is overriden by the system scope.
- When using `AUTO_SUBFOLDER` or `AUTO_FLAT_SUBFOLDER` keywords, the name of the systems of the group is based on the path from the root of the group instead of the root of the project.
- Groups have their own `_shared` resources folders but the can also access the files in the global `_shared` folder.
- The `unpack` command for `reoglith apply-filter` unpacks the files to the `_shared` folder of the group instead of the global `_shared` folder.
- The `pack` command for `reoglith apply-filter` can pack the files from both of the `_shared` folders (global and group) into the system's data folder but the files from the group's `_shared` folder have priority over the files from the global `_shared` folder.
- Currently nested groups are not supported.

## File scanning improvements and changes
Fixed the bug that caused the filter to scan entire filter data folder looking for systems instead of scanning just the system template folder. This fix should also improve the performance on projects that are big enough to make walking files significant part of the execution time. Additionally, the function that scans the files won't go into the folders of the systems anymore. This means that the nested systems aren't supported anymore but in most cases it's a performance gain at the cost of supporting a rarely used feature that decreases readability of the project.

## 3.1.0
The "append_start" and "append_end" values of the "on_conflict" are not limited to the `.mcfunction` and `.lang` files anymore.

## 3.0.1
Fixed plugin functions not being able to call other plugin functions from their scope.

## 3.0.0

## Added plugins
The plugins are Python files stored in `_plugins` foler. There are two types of plugins:
- global plugins - stored in `<filters-data>/system_template/_plugins` folder. These are shared between all systems.
- local plugins - stored in `<filters-data>/system_tempalte/<system>/_plugins` folder. These are specific to the system.

Plugins are executed using `exec` function, and then their local scope is merged with the scope of the system. The order of execution of the plugins in the same folder is not defined (current implementation uses `pathlib.Path.glob`).

The priority of the data defined by plugins, and local and global scopes is as follows (things higher on the list are overriden by things lower on the list):
- global plugins
- global scope
- local plugins
- local scope

## Removed some of the default variables from the scope
The following variables are no longer defined in the default scope:
- `Path`
- `uuid`
- `math`
- `random`

They are added using a `_default_plugin.py` file from the `_plugins` folder available in the new default `data` folder.

> **WARNING:** If you're upgrading from a previous version, you need to add the `_default_plugin.py` file to your `_plugins` folder to get the same functionality as before.

## JSON files are only parsed when needed
Some of the JSON files of the systems are not parsed anymore and are treated as regular text files. This is done to improve the performance of the filter. The files are only evaluated when it's needed, that is:
- when they use the `"on_conflict": "merge"` option (so that their content can be merged with an existing file)
- when they use `"json_template": true` so that their content can be generated using the `regolith-json-template` library

## Updated the default `auto_map.json` file
The feature and feature rule now strip the `.feature` and `.feature_rule` suffixes from the file names when exported. This is done because the feature and feature rule files are required to have matching file names and identifiers.

## 2.9.1
Added missing `regolith-json-template` variables to the default scope.

## 2.9.0
Updated the `regolith-json-template` module to version `1.2.0`. This adds `JoinStr` feature and adds `random` module to the default scope. See the `README.md` file of the `json_template` filter for more information.

> **WARNING:** This version is missing the `JoinStr` feature. Use `2.9.1` instead.

## 2.8.0
Updated the `regolith-json-template` library to version `1.1.0` to unlock the `__unpack__` and `__value__` keys. See the `json_template` filter's `README.md` for more information.

## 2.7.0
- The auto_map.json file supports new mapping format. The values of the mapping can be a string (old format) or an object with the following properties:
  - `target` - the target path of the file (used for the same purpose as the string value in the old format)
  - `replace_extension` - the value to be used to replace the extension being mapped (optional)
- Updated the default `auto_map.json` file.
  - Added mapping for the `.<some suffix>.py` files into their coressponding json files (e.g. `.bp_ac.py` -> `.bp_ac.json`)
  - Added new mapping for the texture files using the new mapping format. The newly added texture mapping uses similar prefixes to the old mapping, but starting with a dot instead of an underscore. The old mapping is still present for backwards compatibility. Example:
    - Old: `_block.png` -> `_block.png` (still works)
    - New: `.block.png` -> `.png`
## 2.6.1
Fixed filter crashing on invalid JSON files instead of printing an error message with useful information.
## 2.6.0
Added `AUTO_FLAT` and `AUTO_FLAT_SUBFOLDER` keywords for new auto mapping.
## 2.5.0
Added `AUTO_SUBFOLDER` keyword that can be used with the "target" property of a system in `_map.py`. To automatically map the file to a path in RP or BP folder with the addition of a subfolder named after the path of the system.
## 2.4.1
- Fixed the issue of crashing when using `subfunctions` to create nested file structures.
- Fixed crashing when the `config.json` file is not defining the `log_path` property.
## 2.4.0
Added option to evaluate JSON files (`.json` or `.material`) with the
`json_template` regolith filter if explicitly specified in the `_map.py` file.
## 2.3.0
Added `pathlib.Path` to the default scope. The files are evaluated with the
working directory set to the system folder, which means that the `Path(".")`
points at the system folder to let you access the information about the files
in the system.
## 2.2.0
Added logging feature
## 2.1.0
- Added support for the shared resources stored in the `shared` folder. The
  shared resources can be annotated by adding `SHARED:` prefix in their source
  path.
- Updated `auto_map.json` in the data folder.
- Added `pack`, `unpack` and `undo` commands for
  `regolith apply-filter -- system_template`. To make working with shared
  resources easier.
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