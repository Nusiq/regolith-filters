# Changelog
## 1.1.1
Enabled usual ZIP compression method.

## 1.1.0
The `output` parameter can be treated as Python expression if it starts and ends with backtick (`` ` ``). The expression is evaluated in the context that has `git_describe` variable, which is created by running `git describe --tags --always --abbrev=0` command.

This feature can be used to dynamically generate output paths for releases containing the version number from the latest tag. For example:
```json
{
    "output": "`f'{git_describe}-release.mctemplate'`"
}
```
Adding this setting to the configuration would create an mctemplate file named like `1.0.0-release.mctemplate` if the latest tag is `1.0.0`.

## 1.0.1
Fixed crashes when the output directory does not exist.

## 1.0.0
Initial release.
