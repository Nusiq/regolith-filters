# Change log
## 1.3.0
### `executionOrder`
Added new property to the `MAP` entries - `executionOrder: number`. It is set to 0 by default. Entries with `executionOrder < 0` are generated before the entries executed asynchronously (see notes from update `1.1.1`). Entries with `executionOrder > 0` are generated after the entries executed asynchronously. Entries with `executionOrder == 0` are executed asynchronously (this is the default and it doesn't need to be specfied). The entries with lower values are executed before the entries with higher values.

### map-ts.ts
Updated the mapping in the default `map-ts.ts`. Now some output paths are namespaced by default.

## 1.2.0
### Fixed `imports` resolution for Deno 2.6+
ModularMC still modifies its own `deno.json` (in the `.regolith/cache/filters/modular_mc/deno.json` by default) like in the previous versions, but now it also creates an **empty** `deno.json` file (with just `{}` as its content) in the working directory of Regolith (`.regolith/tmp/deno.json`).

Deno 2.6 changed how `deno.json` files are discovered by scripts. Now Deno recursively searches outwards through the parent paths looking for `deno.json` files. Without the empty file, this search would reach the `deno.json` of the Regolith project and Deno would use it for the files that ModularMC dynamically imports from the working directory. The empty file stops the search, so the properly modified "imports" from the filter's `deno.json` keep being used.

Example:
```
.regolith/
    cache/filters/modular_mc/
        deno.json // (1) Modified by ModularMC (same as in previous versions)
    tmp/
        RP/
        BP/
        data/
        deno.json // (2) Empty file (`{}`) created by ModularMC 1.2.0 - it stops Deno's outward config search
packs
    RP/
    BP/
    data/
deno.json // (3)
```

- On ModularMC pre 1.2.0 deno.json (2) wouldn't be generated. The deno.json (1) would be modified to contain the modules defined in deno.json (3) with relative "import" paths modified to point at files directories inside `.regolith/tmp`
    - Deno 2.5 would use deno.json (1) ✅ (with properly modified relative imports)
    - Deno 2.6+ would use deno.json (3) (Deno searches outwards and finds it) ❌ (relative imports point at files inside `packs/...`)
- ModularMC 1.2.0 modifies deno.json (1) like in the previous versions but it also creates the empty deno.json (2).
    - Deno 2.5 would use deno.json (1) ✅ (with properly modified relative imports)
    - Deno 2.6+ would use deno.json (1) ✅ (deno.json (2) stops the outward search before it reaches deno.json (3), so the config of the entry point keeps being used)

### The filter’s `deno.json` is now properly cleaned up before regeneration
Previously, the `deno.json` file inside the filter directory was not cleared correctly before being regenerated from the project’s root `deno.json`. This issue has now been fixed.

### Fixed leftover files from the Esbuild compilation
When ModularMC compiles multiple script entry points with Esbuild, it creates a temporary entry file (`.temp_esbuild_entry_<timestamp>.ts`) in Regolith's working directory. Previously this file was left behind after every `regolith run` (it piled up in `.regolith/tmp/`). Now the file is removed as soon as the compilation finishes. This also covers failed compilations, since the cleanup happens no matter if the compilation succeeded or not.

## 1.1.1
Optimized performance.
- The _map.ts files are read in parallel.
- Modules are executed in parallel but the changes applied to individual files are still sequential so the order of the changes is consistent.
- ModularMC now avoids reading the same file multiple times when multiple modules modify it (the result of previous module is passed to the next one). The file is written to disk only after all the modules have been applied to it.

## 1.1.0
Added whitelist/blacklist module filtering for modules.

## 1.0.0
*I felt like the project is stable enough so it's not 0.8.0*

Added support for importing modules from `deno.json` in context of the _map.ts files.

## 0.7.2
Fixed `onConflict: 'stop'` not working correctly in some cases by removing concurrent evaluation of MapTs items.

## 0.7.1
`appendStart` and `appendEnd` now add a newline character between the content of the merged files if there is no newline character at the end of the top file or the start of the bottom file.

## 0.7.0
If Regolith project has `deno.json` file in its root directory, the filter will use it to resolve the dependencies.

## 0.6.0
Added support for the `dropLabels` option in the Esbuild settings.

## 0.5.0
Added support for text templates.

## 0.4.1
Improved error messages.

## 0.4.0
The JSON Template expressions previously marked with `` ` `` prefix and `` ` `` suffix are now marked just with `` :: `` prefix.

## 0.3.1
Target paths that end with `/` are now used for folder export. Folder export lets you not specify the name of the file; it copies the file name from the source path.

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