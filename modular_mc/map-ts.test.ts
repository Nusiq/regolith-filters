import { assert } from "@std/assert";
import { isModulePathIncluded } from "./map-ts.ts";

// isModulePathIncluded TESTS:

Deno.test("isModulePathIncluded - empty whitelist allows all", () => {
	assert(isModulePathIncluded("", [""], []) === true);
	assert(isModulePathIncluded("sub", [""], []) === true);
	assert(isModulePathIncluded("sub/dir", [""], []) === true);
});

Deno.test("isModulePathIncluded - exact match whitelist", () => {
	assert(isModulePathIncluded("sub", ["sub"], []) === true);
	assert(isModulePathIncluded("other", ["sub"], []) === false);
});

Deno.test("isModulePathIncluded - subdirectory match whitelist", () => {
	assert(isModulePathIncluded("sub/dir", ["sub"], []) === true);
	assert(isModulePathIncluded("sub/dir/deep", ["sub"], []) === true);
	assert(isModulePathIncluded("other/dir", ["sub"], []) === false);
});

Deno.test("isModulePathIncluded - multiple whitelist entries", () => {
	assert(isModulePathIncluded("sub1", ["sub1", "sub2"], []) === true);
	assert(isModulePathIncluded("sub2/dir", ["sub1", "sub2"], []) === true);
	assert(isModulePathIncluded("other", ["sub1", "sub2"], []) === false);
});

Deno.test("isModulePathIncluded - blacklist excludes", () => {
	assert(isModulePathIncluded("sub", [""], ["sub"]) === false);
	assert(isModulePathIncluded("sub/dir", [""], ["sub"]) === false);
	assert(isModulePathIncluded("other", [""], ["sub"]) === true);
});

Deno.test("isModulePathIncluded - blacklist subdirectory", () => {
	assert(isModulePathIncluded("sub/bad", [""], ["sub/bad"]) === false);
	assert(isModulePathIncluded("sub/good", [""], ["sub/bad"]) === true);
});

Deno.test("isModulePathIncluded - whitelist and blacklist combination", () => {
	assert(isModulePathIncluded("sub/good", ["sub"], ["sub/bad"]) === true);
	assert(isModulePathIncluded("sub/bad", ["sub"], ["sub/bad"]) === false);
	assert(isModulePathIncluded("other", ["sub"], []) === false);
});

Deno.test(
	"isModulePathIncluded - normalize trailing slashes in whitelist",
	() => {
		assert(isModulePathIncluded("sub", ["sub/"], []) === true);
		assert(isModulePathIncluded("sub/dir", ["sub/"], []) === true);
	}
);

Deno.test(
	"isModulePathIncluded - normalize trailing slashes in blacklist",
	() => {
		assert(isModulePathIncluded("sub", [""], ["sub/"]) === false);
		assert(isModulePathIncluded("sub/dir", [""], ["sub/"]) === false);
	}
);

Deno.test("isModulePathIncluded - empty modulePath (root)", () => {
	assert(isModulePathIncluded("", [""], []) === true);
	assert(isModulePathIncluded("", ["sub"], []) === false);
});

Deno.test("isModulePathIncluded - complex paths", () => {
	assert(isModulePathIncluded("a/b/c", ["a"], ["a/b/d"]) === true);
	assert(isModulePathIncluded("a/b/d", ["a"], ["a/b/d"]) === false);
	assert(isModulePathIncluded("x/y", ["a"], []) === false);
});

Deno.test("isModulePathIncluded - potentially matching substrings", () => {
	// a/bb shouldn't blacklist a/bbb
	assert(isModulePathIncluded("a/bbb", [""], ["a/bb"]) === true);

	// a/bb shouldn't whitelist a/bbb
	assert(isModulePathIncluded("a/bbb", ["a/bb"], []) === false);
});

Deno.test("isModulePathIncluded - match nothing", () => {
	assert(isModulePathIncluded("a/bb", [""], [""]) === false);
});
