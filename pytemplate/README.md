![](../.resources/pytemplate-title.svg)

# 📝 Description
The Pytemplate filter lets you insert code into JSON files based on Python
based templates. The templates are Python files with a single expression that
evaluates to a structure that can be encoded in JSON (usually a dictionary).
Python has powerful comprehension feature which is perfect for generating
data structures like that.

The filter looks for JSON files using glob pattern to see if they contain
references to templates. If they do, the filter evalates the template and
merges the result with the content of the JSON file.

# 💿 Installation
Run the following command in the Regolith project to make this filter
available:
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

# ⭐ Example
`data/pytemplate/variants.py` - the path relative to `data/pytemplate`
is the identifier of the template (`variants` in this case).
```Py
{
    f"nusiq:{base_name}_{i}": {
        f"minecraft:{int_component}": {
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
                            "trigger_phrase": "TEMPLATE"
                        }
                    },
```

A fragment of a behavior of an entity that matched provided BP glob pattern
The value after colon is an identifier of the template, `{"num_variants": 10}`
is a scope of variables which are used by the template to generate the code.
```
...
    "component_groups": {
      "TEMPLATE:variants": {
          "num_variants": 10,
          "base_name": "component_a",
          "int_component": "variant"
      },
      "TEMPLATE1:variants": {
          "num_variants": 10,
          "base_name": "component_b",
          "int_component": "mark_variant"
      },
...
```
This template creates and add 10 component groups for the entity with
variant values from 0 to 9 (named `component_a_{number}`) and
10 component groups with mark variant values from 0 to 9 (named
`component_b_{number}`).

Note that the trigger phrase is "TEMPLATE" but "TEMPLATE1" is also a valid
because "TEMPLATE" is a prefix of "TEMPLATE1". Everything *after the trigger
phrase* and before the colon is ignored so you can use the same template
multiple times in the same part of the JSON file. The part after colon is
the identifier of the template.


# 🔧 Technical details
## Configuration settings
- `bp_patterns: str` - glob patterns for matching JSON files in behavior pack
  (`**/*.json` by default)
- `rp_patterns: List[str]` - glob patterns for matching JSON files in resource
  pack (`**/*.json` by default)
- `trigger_phrase: str` - a string used to trigger the template replacement.
  The default value is `"TEMPLATE"`. Any key in the JSON file that starts with
  this string, is split into two parts using `:` as a separator. The first part
  is the trigger phrase (+ optional suffix) and the second part is the
  identifier of the template (the path to the teplate file relative to the
  filter data path).
- `sort_keys: bool` - optional value which decides whether the keys of the
  JSON file should be sorted. `True` by default. This property only affects
  the files that are modified by the filter. Sorting keys is not the purpose
  of this filter so for performance reasons it doesn't write the files if
  they're not modified.
- `compact: bool` - optional value which decides whether the JSON
  should be compact (with white spaces removed). `False` by default. This
  property only affects the files that use are modified by the filter.
- `scope_path: str` - a path to JSON file that diefines the scope of variables
  provided to the template during its evaluation. This propery is merged with
  the scope provided directly inside the JSON file and with the default
  scope which is: `{'true': True, 'false': False, 'math': math, 'uuid': uuid}`
  (`math` and `uuid` are standard Python modules). The default value of this
  property is `pytemplate/scope.json`.

## Providing data to the templates
There are 3 ways to provide the scope of variables to the template:
- Some of the values are provided by default (for example `true` value is equal
  to `True` so you can use exactly the same syntax as in JSON files)
- You can put the data into the JSON file indicated by the `scope_path`
  property.
- You can provide the data directly to the template when it's referenced in the
  JSON file. A template reference always contains two parts: the key which
  triggers the use of the template and an object which is merged with the
  scope provided by the other two ways.
