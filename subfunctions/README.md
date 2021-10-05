# What does this filter do?
It extends the syntax of Mcfunctions and lets you implement function files
inside other function files.

# How to use it
Copy this code to your list of the filters.
```
                    {
                        "url": "github.com/Nusiq/regolith-filters/subfunctions",
                    },
```

The filter lets you define subfunctions in two ways. One of them creates a
function and instantly executes it and the second one is used just for the
definition.

## Creating functions to be executed instantly

You can use `function` keyword combined with subfunction name between less than
and greater than symbols. It will create a subfolder with the same name as
the root function, and with the subfunction in it named after the name you
provided.

Inside the root function the code of the subfunction will be replaced with
subfunction call. The filter accepts any code which isn't a comment and
which ends with `function <subfunction name>:`. The subfunction must use the
symbols valid for the function name.

*BP/functions/xxx/yyy/zzz.mcfunction*
```mcfunction
# Some code
function <aaa>:
    # The code of the subfunction
    execute @a ~ ~ ~ function <bbb>:
        # The code of the nested subfunction
# Some other code
```

File above would resolve into:
*BP/functions/xxx/yyy/zzz.mcfunction*
```mcfunction
# Some code
function xxx/yyy/zzz/aaa
# Some other code
```

*BP/functions/xxx/yyy/zzz/aaa.mcfunction*
```mcfunction
execute @a ~ ~ ~ function xxx/yyy/zzz/aaa/bbb
```

*BP/functions/xxx/yyy/zzz/aaa/bbb.mcfunction*
```mcfunction
# The code of the nested subfunction
```


## Creating functions to be reused later

Subfunction definitions can be created by using
`definefunction <subfunction name>:` pattern. You can't combine
`definefunction` with any other commands (like `execute`). The `definefunction`
line must start with `definefunction` keyword or with indentation.

## Calling subfunctions
Since the pattern of creating the subfunction names is known you can call them
like any other function.

## Important
The indentation must be created with spaces. Tabs are not supported.