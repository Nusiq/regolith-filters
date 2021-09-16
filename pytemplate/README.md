# What does this filter do?
This filter loops through the JSON files from RP and BP that match provided
glob patterns (`*/**.json` by default), when it finds a JSON key that
matches the name specified in settings, it replaces it with a value generated
based on template file.

The template files are files with Python expression that evaluates to a value
which can be encoded in JSON.

# Configuration settings
- `templates_path: str` - a path to a directory with template files (relative to regolith working directory)
- `bp_patterns: str` - optional glob patterns for matching JSON files in behavior pack (`**/*.json` by default)
- `rp_patterns: List[str]` - optional glob patterns for matching JSON files in resource pack (`**/*.json` by default)
- `trigger_phrase: str` - optional string used to trigger the template replacement. The default value is "TEMPLATE".
- `sort_keys: bool` - optional value which decides whether the keys of the modified JSON file should be sorted. True by default.
- `compact: bool` - optional value which decides whether the modified JSON should be compact (with white spaces removed). False by default.
- `scope` - a scope of variables provided for the template during the evaluation. This property is merged with the scope provided directly in the modified JSON file and with the default value: `{'true': True, 'false': False, 'math': math, 'uuid': uuid}` where math and uuid are standard python modules.

# Example
`../../nusiq-pytemplates/variants.py` - the path relative to the
"template_path" from config is the identifier of the template.
```Py
{
    f"nusiq:variant{i}": {
        "minecraft:variant": {
            "value": i
        }
    } for i in range(num_variants)
}
```

Filter config in config.json of Regolith project:
```
...
                    {
                        "url": "github.com/Nusiq/regolith-filters/pytemplate",
                        "settings": {
                            "templates_path": "../../nusiq-pytemplates"
                        }
                    },
...
```

A fragment of a behavior of an entity that matched provided BP glob pattern
The value after colon is an identifier of the template, `{"num_variants": 10}`
is a scope used to evaluate the temlpate.
```
...
    "component_groups": {
      "TEMPLATE:variants": {"num_variants": 10},
...
```
This template will create and add 10 component groups for the entity with
variant values from 0 to 9 inclusive.
