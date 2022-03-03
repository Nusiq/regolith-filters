WARNING! THIS FILTER USES THE PYTHON `eval()` FUNCTION TO GENERATE CODE. IF
YOU ARE NOT SURE WHAT THIS MEANS, DO NOT USE THIS FILTER. NEVER USE THIS FILTER
ON ANY CODE THAT YOU DO NOT TRUST.

# Description
This filter inserts code into JSON files based on Python based templates.

The filter loops through the JSON files from RP and BP that match provided
glob patterns (`*/**.json` by default), when it finds a JSON key that
matches the name specified in settings, it replaces it with a value generated
based on template file. The template files are Python files with single
expression that evaluates to a value which can be encoded in JSON.

# Installation
Run this command in the Regolith project to make this filter available:
```
regolith install github.com/Nusiq/regolith-filters/pytemplate
```
When you have done that, you can use the filter in your Regolith project by
adding it to the `filters` section of a profile in the `config.json` file of
the Project:
```json
                    {
                        "filter": "pytemplate"
                    },
```


# Example
`data/pytemplate/variants.py` - the path relative to `data/pytemplate`
is the identifier of the template (`variants` in this case).
```Py
{
    f"nusiq:variant{i}": {
        "minecraft:variant": {
            "value": i
        }
    } for i in range(num_variants)
}
```

Filter config in `config.json` of Regolith project (all of the possible
settings properties are explained in the next section):
```json
                    {
                        "filter": "pytemplate",
                        "settings": {
                            "trigger_phrases": ["TEMPLATE", "TEMPLATE_1"]
                        }
                    },
```

A fragment of a behavior of an entity that matched provided BP glob pattern
The value after colon is an identifier of the template, `{"num_variants": 10}`
is a scope of variables which are used by the template to generate the code.
```
...
    "component_groups": {
      "TEMPLATE:variants": {"num_variants": 10},
...
```
This template creates and add 10 component groups for the entity with
variant values from 0 to 9 inclusive.

# Configuration settings
- `bp_patterns: str` - optional glob patterns for matching JSON files in
  behavior pack (`**/*.json` by default)
- `rp_patterns: List[str]` - optional glob patterns for matching JSON files in
  resource pack (`**/*.json` by default)
- `trigger_phrases: List[str]` - optional list of strings used to trigger the
  template replacement. The default value is `["TEMPLATE"]`.
  defining multiple trigger phrases can be useful when you want to use the
  same template multiple times in the same place with different parameters. 
- `sort_keys: bool` - optional value which decides whether the keys of the
  modified JSON file should be sorted. True by default.
- `compact: bool` - optional value which decides whether the modified JSON
  should be compact (with white spaces removed). False by default.
- `scope_path: str` - a path to JSON file that diefines the scope of variables
  provided to the template during its evaluation. This propery is merged with
  the scope provided directly in the modified JSON file and with the default
  scope which is: `{'true': True, 'false': False, 'math': math, 'uuid': uuid}`
  where math and uuid are standard python modules. The default value of this
  property is `pytemplate/scope.json`. The path is relative to
  data folder in working directory of regolith.
