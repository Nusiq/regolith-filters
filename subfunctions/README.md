# What does this filter do?
The filter provides additional syntax for `mcfunction` files and lets you
define functions inside other functions.

# How to use it
Copy this code to your list of the filters.
```
                    {
                        "url": "github.com/Nusiq/regolith-filters/subfunctions"
                    },
```
# Configuration settings
- `scope_path: str` - a path to JSON file that diefines the scope of
  variables provided to the template during its evaluation. The default value
  of this property is `subfunctions/scope.json`. The path is relative to
  data folder in working directory of regolith.

# Features

## `function` - subfunctions defined executed instantly

### Syntax
```
[any_code] function <[function_name]>:
    [function_body]
- any_code - usually an execute command or chain of execute commands, but
  since subfunctions don't parse mcfunction files, you can put there any
  string.
- function_name - a name of the new function to create [A-Za-z0-9]+, the file
  is created inside a folder with the same name as the root function
- function_body - multiline body of the function. The body ends
  with the line that doesn't have enough indentation (like in Python
  programming language)
```
### Description
The `function` command has extended syntax. You can use `function` keyword
combined with subfunction name between `<` and `>` symbols.
It creates subfolder with the same name as the root function, and with
the subfunction in it named after provided name.

Inside the root function the code of the subfunction is replaced with
subfunction call. The filter accepts any code which isn't a comment and
which ends with `function <subfunction name>:`. The subfunction must use the
symbols valid for the function name.

### Example

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


## `definefunction` - definition of subfunction without execution
### Syntax
```
definefunction <[function_name]>:
    [function_body]
- function_name - a name of the new function to create [A-Za-z0-9]+, the file
  is created inside a folder with the same name as the root function
- function_body - multiline body of the function. The body ends
  with the line that doesn't have enough indentation (like in Python
  programming language)
```
### Description
Subfunction definitions can be created by using
`definefunction <subfunction name>:` pattern. You can't combine
`definefunction` with any other commands (like `execute`). The `definefunction`
line must start with `definefunction` keyword or with indentation.

## Calling subfunctions from `definefunction` and `function`
Since the pattern of creating the subfunction names is known you can call them
like any other function.

## `functiontree` - a binary tree of functions
### Syntax
```
[any_code] functiontree <[function_name]><[scoreboard] [start]..[stop] [step]>:
    [function_body]
- any_code - usually an execute command or chain of execute commands, but
  since subfunctions don't parse mcfunction files, you can put there any
  string.
- function_name - a base name of the new functions to create ([A-Za-z0-9]+),
  the files are created inside a folder with the same name as the root function
  and are named after function_name with addition of sufix which represents
  the scoreboard range they search.
- scoreboard - the name of the scoreboard used for function tree
- start - starting value of range
- stop - end value of range
- step - the incrementation step (optional)
- function_body - multiline body of the function. The body ends
  with the line that doesn't have enough indentation (like in Python
  programming language)
```
### Description
`functiontree` lets you quickly search values of scoreboard of `@s` using
binary tree made out of function files calling each other. It also  adds
a variable to the scope with the value of the scoreboard which can be accessed
using `eval` (see documentation below)

### Example
This is an example of simple implentation of getting elements from table
created from 100 scoreboards, that uses `tab_index` scoreboard to point at
index of the table to be accessed and `table_io` to copy the value from the
table.

Source: *BP/functions/table.mcfunction*
```mcfunction
functiontree <table_get><tab_index 0..100>:
    scoreboard players operation @s table_io = @s t_`eval:tab_index`
```

Complied code: *BP/functions/table.mcfunction*
```
execute @s[scores={tab_index=0..49}] ~ ~ ~ function table/get_0_49
execute @s[scores={tab_index=50..99}] ~ ~ ~ function table/get_50_99
```

Example branch: *BP/functions/table/get_0_49.mcfunction*
```mcfunction
execute @s[scores={tab_index=0..24}] ~ ~ ~ function table/get_0_24
execute @s[scores={tab_index=25..49}] ~ ~ ~ function table/get_25_49
```

Example leaf: *BP/functions/table/get_1_2.mcfunction*
```mcfunction
execute @s[scores={tab_index=1..1}] ~ ~ ~ scoreboard players operation @s table_io = @s t_1
execute @s[scores={tab_index=2..2}] ~ ~ ~ scoreboard players operation @s table_io = @s t_2
```

## `for` - generating code in a loop
### Syntax
```
for <[variable] [start]..[stop] [step]>:
    [body]
- variable - the variable used in the for loop added to the scope for `eval`
- start - starting value of range
- stop - end value of range
- step - the incrementation step (optional)
- body - multiline body of the for block. The body ends
  with the line that doesn't have enough indentation (like in Python
  programming language)
```
### Example:
Source:
```mcfunction
for <i 0..25 5>:
    say hello `eval:i`*100=`eval:i*100`
```

Compiled code (added to the same function):
```mcfunction
say hello 0*100=0
say hello 5*100=500
say hello 10*100=1000
say hello 15*100=1500
say hello 20*100=2000
```

## `if` - generating code based on condition
### Syntax
```
if <[condition]>:
    [body]
- variable - the expressin with a condition which decides whether the body
  of the if block should be included in the function.
- body - multiline body of the if block. The body ends
  with the line that doesn't have enough indentation (like in Python
  programming language)
```
## `eval` - static code generation based on simple expressions
### Syntax
```
`eval:[math_expression]`

- math_expression - the expression to be evaluated and inserted instead to
  the function of eval. 
```
### Description
Eval is to generate code based on basic math expressions. It can also access
the variables from `for` and `functiontree`.

## Important
The indentation must be created with spaces. Tabs are not supported.
