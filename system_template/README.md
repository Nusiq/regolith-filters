WARNING! THIS FILTER USES THE PYTHON `eval()` FUNCTION TO GENERATE CODE. IF
YOU ARE NOT SURE WHAT THIS MEANS, DO NOT USE THIS FILTER. NEVER USE THIS FILTER
ON ANY CODE THAT YOU DO NOT TRUST.

# What does this filter do?
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

# How to use it
Copy this code to your list of the filters.
```
                    {
                        "url": "github.com/Nusiq/regolith-filters/system_template"
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
The templates are stored inside the filter data folder. Every direct subfolder
from this folder is a system template. The name of the folder is the name of
the system displayed in the Regolith logs. Every system template has 2 config
files (`system_scope.json` and `system_template.py`) and a data folder
(`data`).

```
📁 system_template
  📁 [system name]
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
  - `scope` - this property is required only when the source file is a python
    file and the target is a JSON file. It defines the scope used for
    evaluating the source file (then it's dumped as JSON to the target).
- `data/*` - a folder with files that are used as source files for the system.
  The files can be any type of files.
