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
uses `_scope.json` file to define the variables that are used for
code generation.

# Installation
Run the following command in the Regolith project to make this filter
available:
```
regolith install system_template
```
Add the filter to the `filters` list in the `config.json` file of the Regolith
project to actually enable it (the settings properties are explained in the
next section):
```
                    {
                        "filter": "system_template",
                        "settings": {
                          "scope_path": "system_template/scope.json"
                        }
                    },
```

# Configuration settings
- `scope_path: str` - a path to JSON file that diefines the scope of variables provided
  to the template during its evaluation. This propery is merged with the scope
  provided directly in the modified JSON file and with the default scope which is:
  `{'true': True, 'false': False, 'math': math, 'uuid': uuid, 'AUTO': AUTO}`
  where math and uuid are standard python modules, and AUTO is a special value
  used to mark that the target file should be mapped automatically based on its
  extension. The default value of this property is `system_template/scope.json`.
  The path is relative to data folder in working directory of regolith.
- `systems: list[str]` - a list of glob patterns to match the system folders
  that should be processed. The default value is `["**/*"]` which means that
  all system folders will be processed.

# Examples
There is an example in the `test` subfolder of this filter.

> Note:
>
> The test uses "script" property to reference local `main.py` file of this
> filter. When you donwload the filter your "filterDefinitions" property will
> look different (it will include an URL).


# Usage
## The structure of the system templates
The templates are stored inside the data folder of the filter - the
"system_template" folder in the filters data path defined in the `config.json`
file of the Regolith project (by default it's `packs/data/system_template`).

Inside that path, every folder that has two files `_scope.json` and `_map.py`
is considered a system template. The folder doesn't have to be a direct
subfolder of the `system_template` folder (you can organize the folder
structure to your preference).

Other files inside
```
📁 system_template
  auto_map.json
  📁 [path/to/system]
    📝 examlpe_python_file.py
    📝 example_json_file.json
    📝 example_file.example_extension
    📝 _scope.json
    📝 _map.py
```
- `auto_map.json` - a file that defines how to automatically map files of the
  systems to the resource and behavior packs using the "AUTO" keyword, based
  on the file extension. The file maps the ending of the file to the folder
  in RP or BP.
- `_scope.json` - defines the scope used for evaluating the `_map.py`
  file. The scope is merged with the default scope and with the scope provided
  in the `scope_path` property.
- `_map.py` - a file that defines relation between the source files and
  the exported files. It decides where the files should be copied and some of
  their properties used during code generation (see the section below).
- Other files are the temlpates. You can put any kind of files here. The
  `_scope.json` and `_map.py` files define what to do with them.

## The `_map.py` file

The `_map.py` is a Python file but it's used as a configuration file. The
Python syntax lets you define complex structures in a very simple way, using
comprehension. The `_scope.json` file is used to define the scope with variables
used for evaluating the `_map.py` file.

The `_map.py` file should contain a single expresion that evaluates to a
list of dictionaries. Every dictionary defines a single relation between the
source file, its destination. It also defines how to handle situations when
the destination file already exists.

Properties of the dictionary inside the `_map.py` list:
- `source` - the path to the source file relative to the folder of the sytem.
  The source is treated as a glob pattern if it contains `*` or `?` characters.
  Using glob patterns is useful in combination with the `AUTO` keyword for the
  target file.
- `target` - the destination of the file. Remember to include `RP` or `BP` in
  the destination path to output it to a resource or behavior pack. Alternatively,
  you can use the `AUTO` keyword to automatically map the file to the resource
  or behavior pack based on the file extension. The rules of mapping are
  defined in the `auto_map.json` file.
- `scope` - The sustem_template filter lets you define the output files using
  the same principles that are used to evaluate the `_map.py` in order to
  generate JSON files.

  If you set your source file to be a Python file, and the target file to be
  a JSON file, the file will be evaluated using the scope defined in the
  `scope` property, and then the result will be saved as a JSON file.

  The scope accessible during the evaluation of the file is created by merging
  multiple sources:
  - The default scope `{'true': True, 'false': False, 'math': math, 'uuid': uuid`, "AUTO": AUTO}`
  - The scope that the "scope_path" property points to.
  - The `_scope.json` file in the system folder.
  - The `scope` property of the dictionary.

  The scopes are merge in this order. If multiple scopes define the same variable,
  the value from the scope that is defined later shadows the value from the
  scope that is defined earlier.

  > WARNING:
  >
  > Use this feature carefully. In most cases, it's better to use the `_scope.json`
  > file, or the scope form "scope_path". Hiding variables in multiple sources may
  > hinder the readability of the code.

- `on_conflict` - defines what to do when the target file already exists.
  Possible values are:
  - `stop` - an error is raised.
    - **Default for JSON and .mcfunction files.**
  - `append_start` - the new file is appended at the start of the old
    - Not available when the target file is a JSON file.
  - `append_end` - the new file is appended at the end of the old one.
    - **Default for .lang files**
    - Not available when the target file is a JSON file.
  - `overwrite` - the new file overwrites the old one.
  - `skip` - the new file is skipped.
  - `merge` - the new file is merged with the old one.
    - Only available when the target file is a JSON file.

  The files with different extensions than .json, .mcfunction and .lang can
  only use the `stop`, `overwrite` and `skip` options.

  > WARNING:
  >
  > It's usually the best to use the default options.
  > Using other options decreases the readability of the code.

- `subfunctions` - a property only available for `.mcfunction` and `.lang` files
  it defines if the file should be executed with its scope using the `subfunctions`
  regolith filter. You can read more about the `subfunctions`
  [here](https://github.com/Nusiq/regolith-filters/tree/master/subfunctions). The
  value of this property is True by default for the `.mcfunction` files and
  False by default for the `.lang` files.

## Shared files
Sometimes you want to share some files between multiple systems. You can do
it using a special `_shared` folder and `SHARED:` prefix in the file `source`
property.


Example:

*some_system/_map.py*
```
[
    {
        // Regular resource
        "source": "my_texture.png",
        "target": AUTO
    },
    {
        // Shared resource
        "source": "SHARED:my_shared_texture.png",
        "target": AUTO
    }
]
```
This configuration means that you can put the `my_shared_texture.png` either in
`some_system/my_shared_texture.png` or in `_shared/my_shared_texture.png`. If
you crate both files, the local file of the system will be used.

The purpose of the shared resources is to avoid duplicating the files.

Since the use of the shared resouces means that you put resources outside of
the system, this means that you can't just copy the system folder to another
project. The `system_template` implements a solution to this problem. It
adds 3 new commands that are intended to be used with the
`regolith apply-filter` command:
- `pack` - packs the `_shared` resources into the system folder.
- `unpack` - unpacks the system folders into the `_shared` folder.
- `undo` - undoes the last operation.

A typical workflow of moving the system from project A to project B would look
like this (the examples of the commands and their syntax are explained in the
next section):

1. In project A run the `pack` command.
2. Copy the system folder to project B.
3. In project B run the `unpack` command.
4. In project A run the `undo` command.

You don't have to unpack the system in project B if you're not going to share
any resources of that system with other systems on the project. In that case,
it is recommended to remove the `SHARED:` prefix from the `source` properties
in the system's `_map.py` file. In general, the cleanest solution is to keep
all of the shared resources in the `_shared` folder and to remove the `SHARED:`
prefix if a resource is not shared.

## The syntax of the `pack`, `unpack` and `undo` commands

The `pack`, `unpack` and `undo` commands are  designed to be used with the
`regolith apply-filter` command. The `apply-filter` command syntax is:
```
regolith apply-filter -- <filter_name> <filter_arguments>
```
In case of the `system_template` filter, the filter name is always
`system_template`:
```
regolith apply-filter -- system_template <filter_arguments>
```

### The `pack` and `unpack` commands
The `pack` and `unpack` commands have their own flags that can be used to
specify their behavior:

- `--systems` - a list of glob patterns that define which systems should be
  packed or unpacked. The default value is `**/*` which means that all systems
  will be packed or unpacked. You can provide multiple patterns by separating
  them with a space.
- `--scope` - a path to a JSON file that defines the scope that will be used
  when evaluating the `_map.py` files. The default value is
  `system_template/scope.json` which means that the default scope will be used.

Example: Unpacking `my_system` using the `scope.json` file as the scope.
```
regolith apply-filter -- system_template unpack --systems my_system --scope scope.json
```

### The `undo` command
The `undo` command has no flags. It undoes the last `pack` or `unpack`
operation.

Example: Undoing the last operation.
```
regolith apply-filter -- system_template undo
```
