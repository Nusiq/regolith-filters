# Description
This filter introduces a concept of a system in behavior and resource packs.
The systems are groups of files that are used to serve certain purposes.

A system can have various forms. It's up to you to decide how to group your
code. Below there are some examples of things that can be implemented as
systems.
- single Minecraft entity
- a minigame
- multiple Minecraft entities that cannot exist without each other

System templates and easy to reuse between multiple project, because every
template has its dedicated folder. They are also configurable. Every system
uses `system_scope.json` file to define the variables that are used for
code generation.

# Installation
Run the following command in the Regolith project to make this filter
available:
```
regolith install github.com/Nusiq/regolith-filters/system_template
```
Add the filter to the `filters` list in the `config.json` file of the Regolith
project to actually enable it (the settings properties are explained in the
next section):
```
                    {
                        "url": "system_template",
                        "settings": {
                          "scope_path": "system_template/scope.json"
                        }
                    },
```

# Configuration settings
- `scope_path: str` - a path to JSON file that diefines the scope of variables provided
  to the template during its evaluation. This propery is merged with the scope
  provided directly in the modified JSON file and with the default scope which is:
  `{'true': True, 'false': False, 'math': math, 'uuid': uuid}` where math and
  uuid are standard python modules. The default value of this property is
  `system_template/scope.json`. The path is relative to
  data folder in working directory of regolith.

# Examples
There is an example in the `test` subfolder of this filter. Note that it uses
local reference to the `main.py` file of this filter. Normally you would use
an URL (just like in the "How to use it" section).

# The structure of the system templates
The templates are stored inside the filter data folder. Every direct or
indirect subfolder from this folder that has `system_scope.json` and
`system_template.py` files is considered a system template by the filter.
The path to the folder is the name of the system displayed in the Regolith
logs.
```
📁 system_template
  📁 [path/to/system]
    📁 data
      📝 examlpe_python_file.py
      📝 example_json_file.json
      📝 example_file.example_extension
    📝 system_scope.json
    📝 system_template.py
```
- `system_scope.json` - defines the scope used for evaluating the `system_template.py`
  file. The scope is merged with the default scope and with the scope provided
  in the `scope_path` property.
- `system_template.py` - python file with single expression that evaluates to
  a list of dictionaries. Each dictionary has the following keys:
    - `source` - the path to the source file relative to the `[system name]/data`
      folder.
    - `target` - the destination of the file (can be either in `RP` or `BP`
        folders of the Regolith project).
    - `scope` - this property is used only when the source file is a python
        file and the target is a JSON file. It defines the scope used for
        evaluating the source file (then it's dumped as JSON to the target).
    - `use_global_scope` - this property is used only when the source file is
        a python file and the target is a JSON file. It defines whether the
        scope defined in the `system_scope.json` and in the `scope_path` file
        should be used while evaluating the source file.
     - `on_conflict` - defines what to do when the target file already exists.
        Possible values are:
        - `overwrite` - the new file overwrites the old one.
        - `skip` - the new file is skipped.
        - `stop` - an error is raised.
        - `append_start` - the new file is appended at the start of the old
           one. This option is not available for JSON files.
        - `append_end` - the new file is appended at the end of the old one.
           This option is not available for JSON files.
        - `merge` - the new file is merged with the old one. This option is
           available only if the target file is a JSON file and a source file
           is either a JSON file or a python file.
- `data/*` - a folder with files that are used as source files for the system.
  The files can be any type of files.
