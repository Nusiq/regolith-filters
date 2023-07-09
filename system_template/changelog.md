# Change log
## 2.9.0
Updated the `regolith-json-template` module to version `1.2.0`. This adds `JoinStr` feature and adds `random` module to the default scope. See the `README.md` file of the `json_template` filter for more information.

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