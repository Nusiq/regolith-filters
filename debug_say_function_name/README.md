# What does this filter do?
Adds say command to the functions from specified paths to print the names
of the functions when they're executed.

# How to use it
Copy this code to your list of the filters and edit the "patterns" property
so the list contains only the patterns of the functions that you want to print
to the chat.
```
                    {
                        "url": "github.com/Nusiq/regolith-filters/debug_say_function_name",
                        "settings": {
                            "patterns": ["**/*.mcfunction"]
                        }
                    },
```