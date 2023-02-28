# Changelog
# 1.1.2
Update the `better-json-tools` dependency to 1.0.3 or better. 1.0.3 implements an
important bug fix that ensures that the with quotes inside are exported correctly.
# 1.1.1
Update the `better-json-tools` dependency to be less specific (not matching the patch version)
# 1.1.0
- The filter uses `better-json-tools` dependency. It's now able to load JSON with comments.
- Added in-place tmeplates
- Changed the default settings of `bp_patterns` and `rp_patterns` to `[]` from `["**/*.json"]`.
  The recommended way to use the filter is now to use the in-place templates.
# 1.0.0
- Added changelog
- Replaced the "trigger_phrases" property with "trigger_phrase"
