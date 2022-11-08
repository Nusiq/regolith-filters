# 📝 Description
This filter creates a text file which counts the number of uses of the filter.
The text file is created in the filter data in `/run_counter/counter.txt`. The
file should be added to `.gitignore` if you're working in a team to avoid
merge conflicts.

# 💿 Installation
Run the following command in the Regolith project to make this filter
available:
```
regolith install run_counter
```

Alternatively, you can use the direct URL to the filter:
```
regolith install github.com/Nusiq/regolith-filters/run_counter
```


Add the filter to the `filters` list in the `config.json` file of the Regolith
project to actually enable it (the settings properties are explained in the
next section):
```json
                    {
                        "filter": "run_counter"
                    },
```
