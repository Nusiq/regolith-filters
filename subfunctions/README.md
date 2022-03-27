![](../.resources/subfunctions-title.svg)

# 📝 Description
The Subfunctions filter provide enhanced `mcfunction` syntax, allowing easy
code generation directly from the mcfunction files. Their main feature is the
ability to define multiple functions in a single file, but they can also be
used to generate code in loops, with condintional logic, and using variables
which can be modified during code generation.

Subfunctions are easy to use because their syntax is a superset of the
`mcfunction` syntax. The code of mcfunction files is a valid code for
Subfunctions, which means that they can be added to any project at any stage
of development.

# 💿 Installation
Run the following command in the Regolith project to make this filter
available:
```
regolith install github.com/Nusiq/regolith-filters/subfunctions
```
Add the filter to the `filters` list in the `config.json` file of the Regolith
project to actually enable it (the settings properties are explained in the
next section):
```json
                    {
                        "filter": "subfunctions",
                        "settings": {
                            "scope_path": "subfunctions/scope.json"
                        }
                    },
```

# ✅ Configuration settings
- `scope_path: str` - a path to JSON file that diefines the scope of
  variables provided to the template during its evaluation. The default value
  of this property is `subfunctions/scope.json`. The path is relative to
  data folder in working directory of regolith.
- `edit_lang_files: bool` - a flag that indicates whether the filter should
  edit the language files. The default value of this property is `false`. See
  editing lang files section below for more information.

# ⭐ Features

## Table of contents
- [`function` - subfunctions defined executed instantly](#function---subfunctions-defined-executed-instantly)
- [`definefunction` - definition of subfunction without execution](#definefunction---definition-of-subfunction-without-execution)
- [`functiontree` - a binary tree of functions](#functiontree---a-binary-tree-of-functions)
- [`for` - generating code in a loop](#for---generating-code-in-a-loop)
- [`foreach` - generating code from collections](#foreach---generating-code-from-collections)
- [`if` - generating code based on condition](#if---generating-code-based-on-condition)
- [`var` - defining variables for later use in the same function](#var---defining-variables-for-later-use-in-the-same-function)
- [`>` - evaluating expression without assigning it to a variable](#---evaluating-expression-without-assigning-it-to-a-variable)
- [`eval` - static code generation based on simple expressions](#eval---static-code-generation-based-on-simple-expressions)
- [`UNPACK:HERE` and `UNPACK:SUBFUNCTION`](#unpackhere-and-unpacksubfunction)
- [`##` - subfunction comments](#---subfunction-comments)
- [`assert` - breaking the execution based on the condition](#assert---breaking-the-execution-based-on-the-condition)
- [Indentation limitations](#indentation-limitations)
- [Editing `.lang` files](#editing-lang-files)

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
functiontree <[function_name]><[scoreboard] [start]..[stop] [step]>:
    [function_body]
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
### Example
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

## `foreach` - generating code from collections
### Syntax
```
for <[index] [variable] [expression]>:
    [body]
- variable - the variable used in the for loop added to the scope for `eval`
- index - a name of variable used to keep track of the item index in collection
  (starting from index 0). The value is added to scope and accessible in `eval`
- body - multiline body of the for block. The body ends
  with the line that doesn't have enough indentation (like in Python
  programming language)
```
### Example
Source:
```mcfunction
foreach <i animal ["cat", "dog", "parrot"]>:
    say `eval:i` `eval:animal`
```

Compiled code (added to the same function):
```mcfunction
say 0 cat
say 1 dog
say 2 parrot
```

## `if` - generating code based on condition
### Syntax
```
if <[expression]>:
    [body]
- expression - the expressin with a condition which decides whether the body
  of the if block should be included in the function.
- body - multiline body of the if block. The body ends
  with the line that doesn't have enough indentation (like in Python
  programming language)
```
## `var` - defining variables for later use in the same function
### Syntax
```
var [identifier] = [expression]
- identifier - the name of the variable
- expression - expression whose value is assigned to the variable
```
### Example
```
var pi = 3.14
```
## `>` - evaluating expression without assigning it to a variable
## Description
This is almost the same as `var` but there is no variable to add to the scope.
This is useful for modifiing existing variables (for example expanding lists).
### Syntax
```
> [expression]
- expression - the expression to be evaluated
```
### Example
```
> my_list.append(2)
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

## `UNPACK:HERE` and `UNPACK:SUBFUNCTION`
### Description
`UNPACK:HERE` and `UNPACK:SUBFUNCTION` are special annotations that you can put
at the first line of the mcfunction file. The files with these annotations
are deleted from the pack. They can be used to create multiple function
definitions in one place using `definefunction`. Using `function <>:` and
normal commands in files with these annotations, outside of `definefunction`
code block is not allowed.

`UNPACK:HERE` unpacks the functions defined with definefunction in the same
path as the source file.

`UNPACK:SUBFUNCTION` doesn't modify the default behavior of `definefunction`

## `##` - subfunction comments
Double hash `##` is used to comment out the rest of the line. Comments
that start with `##` are not copied to the compiled file unlike normal
mcfunction commments (single hash `#`).

## `assert` - breaking the execution based on the condition
### Syntax
```
assert [expression]
- expression - the expression which decides whether the execution should
  be broken.
```
### Example
```mcfunction
assert False
```
This code would stop the execution and print an error message.

## Indentation limitations
In normal mcfunction files, indentation don't matter. Subfunctions use the
indentation to group the code in the same way as in Python. As shown in the
examples above, the indentation is used to determine the scope of blocks
like `for`, `definefunction`, `functiontree`, etc.

Apart from all of these situations, where the indentation has a syntactic
meaning, there is one additional case in which the indentation is allowed:
You can create indented blocks of code if they have a comment at the top used
as a header. Here is an example:
```mcfunction
# This is a comment about the block of code
    say first command
    say second command
    say third command
```
Without the comment or the use of the syntax that requires indented blocks,
you can't use arbitrary indentation:
```mcfunction
say This is not allowed!
    say This line will create an error!
    say second command
    say third command
```
This limitation lets Subfunctions detect errors like typos in the lines that
can be used start an indented block (for example `define_function` instead of
`definefunction`).
```mcfunction
define_function <my_function>:
    say Subfunctions would detect an error here!
```

## Editing `.lang` files
Subfunctions ignore the syntax of mcfunction files which means that you could
use it for editing any other type of files. It doesn't make much sense to
edit most of the files in the packs, but in some cases it can be useful to
modify the `.lang` files. By default the `edit_lang_files` option is disabled
but you can enable it and you'll be able to use subfunctions syntax in language
files.

Editing `.lang` files has some restrictions. The features that are designed to
work specificly with `.mcfunction` files are disabled:
- function
- definefunction
- funcitontree
- UNPACK:HERE
- UNPACK:SUBFUNCTION
- subfunction comments (`##`)

## Other notes
The indentation must be created with spaces. Tabs are not supported.
