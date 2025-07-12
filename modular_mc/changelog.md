# Change log
## 0.4.0
- The JSON Template expressions previously marked with `` ` `` prefix and `` ` `` suffix are now marked just with `` :: `` prefix.

## 0.3.1
- Target paths that end with `/` are now used for folder export. Folder export lets you not specify the name of the file; it copies the file name from the source path.

## 0.3.0
- Source paths in _map.ts entries now can be absolute paths, as long as the target path is not using `:auto` and the source path is inside the data directory of ModularMC.
- Removed the `scope` and `scopePath` properties from the settings. Using imports in _map.ts file sufficiently covers the same use case.

## 0.2.1
Fixed a bug where the filter could incorrectly change working directory while resolving the list of files to process from glob patterns.

## 0.2.0
Renamed the `k` function used in JSON Template to `K` to let users use variable name `k` (a common name for a key in a JSON object). This name also matches the JSON Template from System Template Regolith filter.

## 0.1.2
Added support for glob patterns in the map file.

## 0.1.1
Fixed a bug where having multiple script entry points for Esbuild would crash the filter.

## 0.1.0
Initial release.