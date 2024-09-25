# Change log
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
