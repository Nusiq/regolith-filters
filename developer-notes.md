# Filters Implemented as PyPI Packages



Some of the filters in this repository (json_tempalte, subfunctions) are implemented as PyPI packages, and the code of the filter iteself basically just calls their main function. The system_tempalte also heavily relies on these packages. This may be a bit confusing and can be a barrier to some developers who want to modify the code of the filters, unless you know a simple trick.

You can simply `git clone` the repository of the module (for example [subfunctions](https://github.com/Nusiq/regolith-subfunctions)) and then during the development modify the content of the `requirements.txt` of the filter in such a way that it points to the local directory of the module instead of the PyPI package.

For example, if you downloaded the module to `C:/Documents/Projects/Regolith/regolith-subfunctions`, you can modify the `requirements.txt` of the filter to look like this:
```pip-requirements
# Comment original content:
# regolith-subfunctions~=1.2
# And add the local path:
-e "C:/Documents/Projects/Regolith/regolith-subfunctions"
better-json-tools~=1.0,>=1.0.3
```
The `-e` installs the package in "editable" mode, which means that you can modify the code of the module and the changes will be immediately reflected in the filter.

When you finish your update you can just make a pull request to the module repository and mention that the filter dependency should also be updated.