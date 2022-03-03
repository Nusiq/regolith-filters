# What does this filter do?
Adds tellraw command to the functions from specified paths to print `@s`and
their names when they're executed. The messages are generated based on the
pattern:
```
tellraw @a {"rawtext":[{"text": PREFIX},{"selector": "@s"},{"text": ": "},{"text": FUNC_NAME}]}

PREFIX - optional text prefix
FUNC_NAME - the name of the function (optionally colored)
```

# How to use it
Install the filter by running the following command:
```
regolith install github.com/Nusiq/regolith-filters/debug_say_function_name
```

Add the filter to the `filters` list in the `config.json` file of the Regolith
project to actually enable it:
```
                    {
                        "filter": "debug_say_function_name",
                        "settings": {
                            "patterns": ["**/*.mcfunction"],
                            "random_colors": true,
                            "prefix": ""
                        }
                    },
```

### Settings
All settings are optional. The example above shows the default values. Not
providing any settings will result in the filter working in the same way as
with the settings above.

The "patterns" is a list of glob patterns to match against the subpaths of
`BP/functions` to determine if the filter should be applied. By default it
matches all mcfunction files (`**/*.mcfunction`).

The "random_colors" setting determines if the function names should be printed
in random colors. By default it's set to `true`. The colors are picked
semi-randomly from the pool of color codes (§2, §3, §4, §5, §6, §9, §a, §b,
§c, §d, §e, §g) based on the names of the functions. Some of the color codes
available in Minecraft like §0 are not in the pool because they're hard to
read.

Prefix is a string that will be prepended to the message. By default it's set
to an empty string (no prefix).
