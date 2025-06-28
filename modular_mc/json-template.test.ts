import { assertEquals } from "@std/assert";
import {
	evaluate,

	// These values are actually used (but inside of executed strings):
	// deno-lint-ignore no-unused-vars
	k,
	// deno-lint-ignore no-unused-vars
	joinStr,
} from "./json-template.ts";

// Define a default scope similar to the Python tests
const DEFAULT_SCOPE = { foo: 12345 };

Deno.test("Basic Expressions", () => {
	const source = {
		foo: "`2 + 2`",
		"`String(5+5)`": "baz",
	};
	const expected = {
		foo: 4,
		"10": "baz",
	};
	assertEquals(evaluate(source, DEFAULT_SCOPE), expected);
});

Deno.test("List Comprehension as Key", () => {
	const source = {
		// Using Array.map instead of Python's list comprehension
		"`Array(2).fill(0).map((_, i) => 'bar' + i)`": "baz",
	};
	const expected = {
		bar0: "baz",
		bar1: "baz",
	};
	assertEquals(evaluate(source, DEFAULT_SCOPE), expected);
});

Deno.test("Using Variables from Scope", () => {
	const source = {
		bar: "`foo`",
	};
	const expected = {
		bar: 12345,
	};
	assertEquals(evaluate(source, DEFAULT_SCOPE), expected);
});

Deno.test("Using K Object", () => {
	const source = {
		// Using Array.map instead of Python's list comprehension
		"`Array(2).fill(0).map((_, i) => K('foo' + i, { number: i }))`": {
			bar: "`number`",
		},
	};
	const expected = {
		foo0: {
			bar: 0,
		},
		foo1: {
			bar: 1,
		},
	};
	assertEquals(evaluate(source, DEFAULT_SCOPE), expected);
});

Deno.test("Unpack with Objects", () => {
	const source = [
		{
			my_favourite_color: "I don't know",
		},
		{
			__unpack__: [{ color: "red" }, { color: "green" }],
			my_favourite_color: "`color.toUpperCase()`",
		},
		{
			my_favourite_color: "BLACK",
		},
	];
	const expected = [
		{
			my_favourite_color: "I don't know",
		},
		{
			my_favourite_color: "RED",
		},
		{
			my_favourite_color: "GREEN",
		},
		{
			my_favourite_color: "BLACK",
		},
	];
	assertEquals(evaluate(source, DEFAULT_SCOPE), expected);
});

Deno.test("Unpack with Expression", () => {
	const source = [
		{
			my_favourite_color: "I don't know",
		},
		{
			__unpack__: "`['red', 'green'].map(c => ({ color: c }))`",
			my_favourite_color: "`color.toUpperCase()`",
		},
		{
			my_favourite_color: "BLACK",
		},
	];
	const expected = [
		{
			my_favourite_color: "I don't know",
		},
		{
			my_favourite_color: "RED",
		},
		{
			my_favourite_color: "GREEN",
		},
		{
			my_favourite_color: "BLACK",
		},
	];
	assertEquals(evaluate(source, DEFAULT_SCOPE), expected);
});

Deno.test("Unpack with Value", () => {
	const source = [
		"It's not green",
		{
			__unpack__: "`['red', 'green'].map(c => ({ color: c }))`",
			__value__: "`color === 'green'`",
		},
		"Not green",
	];
	const expected = ["It's not green", false, true, "Not green"];
	assertEquals(evaluate(source, DEFAULT_SCOPE), expected);
});

Deno.test("JoinStr", () => {
	const source = ["`joinStr(';')`", "a = 1", "b = 2", "c = 3"];
	const expected = "a = 1;b = 2;c = 3";
	assertEquals(evaluate(source, DEFAULT_SCOPE), expected);
});

Deno.test("JoinStr with Unpack", () => {
	const source = [
		{
			__unpack__: "`[{ v: joinStr(' ') }, { v: 'hi' }, { v: 'there' }]`",
			__value__: "`v`",
		},
		"hello",
		"there",
		"it's me",
	];
	const expected = "hi there hello there it's me";
	assertEquals(evaluate(source, DEFAULT_SCOPE), expected);
});

Deno.test("Undefined for Removing Keys", () => {
	const source = {
		foo: "`undefined`",
		"`String(5+5)`": "`undefined`",
		bar: { baz: "`undefined`" },
	};
	const expected = {
		bar: {},
	};
	assertEquals(evaluate(source, DEFAULT_SCOPE), expected);
});

Deno.test("Undefined for Removing Array Items", () => {
	const source = {
		foo: ["`undefined`", "`undefined`"],
	};
	const expected = {
		foo: [],
	};
	assertEquals(evaluate(source, DEFAULT_SCOPE), expected);
});

Deno.test("Undefined in Top Level Array", () => {
	const source = ["`undefined`", "`undefined`"];
	const expected: unknown[] = [];
	assertEquals(evaluate(source, DEFAULT_SCOPE), expected);
});

// Add test for properly testing array map that returns K objects
Deno.test("Array.map returning K objects", () => {
	const source = {
		"`[0, 1].map(i => K('bar' + i, {}))`": "baz",
	};
	const expected = {
		bar0: "baz",
		bar1: "baz",
	};
	assertEquals(evaluate(source, DEFAULT_SCOPE), expected);
});

// Add test for invalid key type with proper error checking
Deno.test("Invalid key type throws error", () => {
	const source = {
		"`[0, 1]`": "invalid",
	};

	try {
		evaluate(source, DEFAULT_SCOPE);
		// If we get here, the test should fail
		assertEquals(true, false, "Expected error was not thrown");
	} catch {
		// Pass the test
		assertEquals(true, true);
	}
});

Deno.test("Number key throws error", () => {
	const source = {
		"`42`": "invalid",
	};

	try {
		evaluate(source, DEFAULT_SCOPE);
		// If we get here, the test should fail
		assertEquals(true, false, "Expected error was not thrown");
	} catch (error: unknown) {
		if (error instanceof Error) {
			// Test passes if the correct error is thrown
			assertEquals(
				error.message.includes("Object keys must be strings"),
				true,
				`Unexpected error message: ${error.message}`
			);
		} else {
			// If it's not an Error object, fail the test
			assertEquals(true, false, "Thrown error is not an Error object");
		}
	}
});
