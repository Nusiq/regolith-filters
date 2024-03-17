# 📝 Description
A simple script compiler that uses Esbuild designed to be used with the System Template Regolith Filter.

# 💿 Installation
Run the following command in the Regolith project to make this filter
available:
```
regolith install system_template_esbuild
```

Alternatively, you can use the direct URL to the filter:
```
regolith install github.com/Nusiq/regolith-filters/system_template_esbuild
```


Add the filter to the `filters` list in the `config.json` file of the Regolith project to enable it:
```json
{
    "filter": "system_template_esbuild"
    // "settings": { you can optionally define settings here } 
}
```

# ⚙️ Settings
The filter supports the following settings:
- `minify: boolean` (optional, default `false`) - Whether to minify the output.
- `entryPoint: string` (optional, default `'data/main.ts'`) - The entry point for the build.
- `outfile: string` (optional default `'BP/scripts/main.js'`) - The output file for the build.
- `external: string[]` (optional, default `["@minecraft/server]`) - A list of external modules to exclude from the bundle in addition to '@minecraft/server' which is included by default.
- `scope_path: string` (optional, default `null`) - The path to the JSON file containing the scope used for evaluating entryPoint and outfile.

The evaluation of the `entryPoint` and `outfile` is based on simple substitution of variables. If `entryPoint` or `outfile` are strings that start and end with a backtick ('`` ` ``'), then the string is evaluated as a template string. This is not the same as a JavaScript template string. The variables need to be surrounded by `{}` instead of `${}`. The templating also doesn't supprot any expressions, only simple variable substitution with variables defined in the scope file.
