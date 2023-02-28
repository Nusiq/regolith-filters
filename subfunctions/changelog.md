# Changelog
## 2.0.2
Update the `regolith-subfunctions` dependency to ~=1.1. This allowes using comments
in the scope.json file.
## 2.0.1
Move the code of the filter out of the project to an external repository:
[https://github.com/Nusiq/regolith-subfunctions](https://github.com/Nusiq/regolith-subfunctions)
## 2.0.0
Changed how the `functiontree` works. Now it support new execute command syntax. The `step` property
of the `functiontree` has been removed as it didn't serve any purpose the way it was implemented.
## 1.0.7
Simplified the regex patterin for python expression to: [^\n\r]+
## 1.0.6
Removed the safe eval function and replaced it with the regular `eval()` function from
standard library. This solution is less safe but has better performance. Regolith is
not safe by design, so it's not a big deal.
## 1.0.5
- Added `~` to the characters accepted by "eval:".
## 1.0.4
- Improved error handling
## 1.0.3
- Fixed nested functiontrees
## 1.0.2
- Added changelog
- Rewrote entire codebase
- Added support for `print()` function in `>` block
- The Subfunctions filter is now more strict about the indentation but is
  better at detecting errors
