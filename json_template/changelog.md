# Changelog
## 2.0.0
Renamed the `Ext` class to `K` inside the template files and to
`JsonTemplateK` internally in the code of the filter.

## 1.0.0
Initial release.

Features:
- Evaluate Python expressions in JSON files in keys/strings surrounded by backticks.
- Keys that evaluate to lists can generate multiple objects
- Use variables defined in the `scope.json` file
- The `Ext` that can temporarlily modify the scope
