# 📝 Description

The `json_template` filter is a tool that extends the capabilities of JSON. It introduces a new syntax that allows you to easily replace JSON keys and string values surrounded with backticks (`` ` ``) with the result of evaluating a Python expression. This is achieved using Python's `eval` function.

Features:

- Use variables defined in a separate "scope.json" file.
- The keys that evaluate to a list generate multiple JSON objects which enables
  you to define repetitive structures in a more concise way.
- The files that you work with are still valid JSON files which means that you
  can stil use their schema validation features.

*If you like this filter you might also like the [`pytemplate`](/pytemplate) filter, which uses Python files that evaluate to JSON serializable objects instead of JSON files.*

# 💿 Installation
Run the following command in the Regolith project to make this filter
available:
```
regolith install github.com/Nusiq/regolith-filters/json_template
```
When you have done that, you can use the filter in your Regolith project by
adding it to the `filters` section of a profile in the `config.json` file of
the Project:
```json
                    {
                        "filter": "json_template",
                        "settings": {
                            "scope_path": "json_template/scope.json",
                            "'patterns": ["BP/**/*.json", "RP/**/*.json"]
                        }
                    },
```
# ⚙️ Configuration settings
- `scope_path: str` - a path to JSON file that diefines the scope of variables provided to the template during its evaluation. The default value of this property is `json_template/scope.json`. The path is relative to data folder in working directory of regolith.
- `patterns: List[str]` - a list of glob patterns that define the files that will be processed by the filter. The default value of this property is `["BP/**/*.json", "RP/**/*.json"]`.

Providing the settings is optional. The example above is equivalent to not providing any settings at all as it uses the default values.

# 🔤 Syntax

If you're familiar with Python and JSON, the syntax used by this filter should be easy to understand.

## Backticks 
If a key or a string value is surrounded with backticks, the filter will try to evaluate the expression inside the backticks and replace the key or the value.

*Input*
```json
{
    "foo": "`2 + 2`",
    "`str(5+5)`": "baz"
}
```
*Output*
```json
{
    "foo": 4,
    "10": "baz"
}
```
Note that the `5+5` expression must be converted to a string. Passing a number as a key would result in an error.

## Defining objects in loops

If a key evaluates to a list, the filter will generate multiple JSON objects with the keys based on each element of the list.

*Input*
```json
{ 
    "`[f'bar{i}' for i in range(2)]`": "baz"
}
```
*Output*
```json
{
    "bar0": "baz",
    "bar1": "baz"
}
```

## Using variables and the scope.json file
You can use variables defined in the `scope.json` file.

*scope.json*
```json
{
    "foo": 12345
}
```
*Input*
```json
{
    "bar": "`foo`"
}
```
*Output*
```json
{
    "bar": 12345
}
```
## The `Ext` object
There is a special `Ext` object that lets you extend the scope by providing it with new variables. The `Ext` object is especially useful when you define your keys in a loop. It can be used to pass the variables from the loop into the generated JSON objects.

*Input*
```json
{
    "`[Ext(f'foo{i}', number=i) for i in range(2)]`": {
        "bar": "`number`"
    }
}
```
*Output*
```json
{
    "foo0": {
        "bar": 0
    },
    "foo1": {
        "bar": 1
    }
}
```
The first value of `Ext` is the key to the generated JSON object,
the rest of the arguments must be keyword arguments. The keyword arguments are passed to the scope of the object.
