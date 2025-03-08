# Change log
## 3.0.0
New configuration structure to make Minecraft debugger setup easier to achieve.

This version removes the `entryPoint` property and adds new `working_dir` property.

The `entryPoint` is now hardcoded to be `data/system_template_esbuild/main.ts. This guarantees that the code is compiled inside the data folder of this filter.

The `working_dir` property lets you move all of the files from `data/system_template_esbuild` to a different location before the build process. The location is relative to the root of the project. This combined with the `sourcemap` option allows you to set up the Minecraft debugger with ease. The files are always compiled into `main.js` that is located in the same directory as the `main.ts` file, and then the `main.js` is copied to the `outfile` location.


## 2.1.0
Added the `sourcemap` option (boolean) for the filter, that maps directly to the `sourcemap` option in the esbuild configuration.

## 2.0.3
Internal change - updated the script from the CommonJS module to ES module.

## 2.0.2
Undo the previous change. Minecraft doesn't seem to support ES2023 yet.

## 2.0.1
Update to ES2023.

Thanks to @Fabrimat for the contribution.

## 2.0.0
The `scope` property in the config of the filter is now relative to `data/` directory to make the behavior of the filter consistent with `system_template`

## 1.0.1
Changed default 'entryPoint' from 'data/main.ts' to 'data/system_template_esbuild/main.ts' to avoid potential file collisions during the build process.

## 1.0.0
Initial release.
