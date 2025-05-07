import { assertEquals } from "@std/assert";
import {
	deepMergeObjects,
	deepMergeDict,
	deepMergeLists,
	ListMergePolicy,
} from "./json-merge.ts";

// Test basic object merging
Deno.test("deepMergeObjects - primitive values", () => {
	// String values
	assertEquals(deepMergeObjects("a", "b"), "b");

	// Number values
	assertEquals(deepMergeObjects(1, 2), 2);

	// Boolean values
	assertEquals(deepMergeObjects(true, false), false);

	// Undefined and null
	assertEquals(deepMergeObjects(undefined, null), null);
	assertEquals(deepMergeObjects(null, undefined), undefined);

	// Different types
	assertEquals(deepMergeObjects("string", 42), 42);
	assertEquals(deepMergeObjects([], {}), {});
});

// Test object (dictionary) merging
Deno.test("deepMergeDict - basic object merging", () => {
	const objA = { a: 1, b: 2, c: 3 };
	const objB = { b: 5, d: 6 };
	const expected = { a: 1, b: 5, c: 3, d: 6 };

	assertEquals(deepMergeDict(objA, objB), expected);
});

// Test nested object merging
Deno.test("deepMergeDict - nested objects", () => {
	const objA = {
		a: 1,
		b: {
			c: 3,
			d: 4,
		},
	};
	const objB = {
		a: 2,
		b: {
			d: 5,
			e: 6,
		},
	};
	const expected = {
		a: 2,
		b: {
			c: 3,
			d: 5,
			e: 6,
		},
	};

	assertEquals(deepMergeDict(objA, objB), expected);
});

// Test array merging
Deno.test("deepMergeLists - GREATER_LENGTH policy", () => {
	const arrA = [1, 2, 3, 4];
	const arrB = [5, 6, 7];
	const expected = [5, 6, 7, 4];

	assertEquals(
		deepMergeLists(arrA, arrB, ListMergePolicy.GREATER_LENGTH),
		expected
	);
});

Deno.test("deepMergeLists - SMALLER_LENGTH policy", () => {
	const arrA = [1, 2, 3, 4];
	const arrB = [5, 6, 7];
	const expected = [5, 6, 7];

	assertEquals(
		deepMergeLists(arrA, arrB, ListMergePolicy.SMALLER_LENGTH),
		expected
	);
});

Deno.test("deepMergeLists - B_LENGTH policy", () => {
	const arrA = [1, 2, 3, 4];
	const arrB = [5, 6, 7];
	const expected = [5, 6, 7];

	assertEquals(deepMergeLists(arrA, arrB, ListMergePolicy.B_LENGTH), expected);

	// Test where B is longer
	const arrC = [1, 2];
	const arrD = [5, 6, 7, 8];
	const expectedCD = [5, 6, 7, 8];

	assertEquals(
		deepMergeLists(arrC, arrD, ListMergePolicy.B_LENGTH),
		expectedCD
	);
});

Deno.test("deepMergeLists - APPEND policy", () => {
	const arrA = [1, 2, 3];
	const arrB = [4, 5];
	const expected = [1, 2, 3, 4, 5];

	assertEquals(deepMergeLists(arrA, arrB, ListMergePolicy.APPEND), expected);
});

// Test complex nested structures
Deno.test("deepMergeObjects - complex nested structures", () => {
	const objA = {
		name: "ProjectA",
		version: "1.0.0",
		settings: {
			debug: true,
			features: ["a", "b", "c"],
		},
		data: [
			{ id: 1, value: "one" },
			{ id: 2, value: "two" },
		],
	};

	const objB = {
		name: "ProjectB",
		settings: {
			debug: false,
			features: ["c", "d"],
		},
		data: [
			{ id: 1, value: "ONE" },
			{ id: 3, value: "three" },
		],
	};

	const expected = {
		name: "ProjectB",
		version: "1.0.0",
		settings: {
			debug: false,
			features: ["c", "d", "c"],
		},
		data: [
			{ id: 1, value: "ONE" },
			{ id: 3, value: "three" },
		],
	};

	assertEquals(deepMergeObjects(objA, objB), expected);
});

// Test edge cases
Deno.test("deepMergeObjects - edge cases", () => {
	// Empty objects
	assertEquals(deepMergeObjects({}, {}), {});
	assertEquals(deepMergeObjects({ a: 1 }, {}), { a: 1 });
	assertEquals(deepMergeObjects({}, { b: 2 }), { b: 2 });

	// Empty arrays - behavior depends on policy
	// With default GREATER_LENGTH policy, when merging [1, 2] with [], it will keep [1, 2]
	assertEquals(
		deepMergeObjects([1, 2], []),
		[1, 2],
		"Empty array B with GREATER_LENGTH policy should keep A's elements"
	);

	// When merging [] with [3, 4], it will use [3, 4]
	assertEquals(deepMergeObjects([], [3, 4]), [3, 4]);

	// With other policies - add tests as needed
	assertEquals(
		deepMergeObjects([1, 2], [], ListMergePolicy.B_LENGTH),
		[],
		"Empty array B with B_LENGTH policy should result in an empty array"
	);

	// Null values
	assertEquals(deepMergeObjects(null, { a: 1 }), { a: 1 });
	assertEquals(deepMergeObjects({ a: 1 }, null), null);

	// Arrays with objects - using default GREATER_LENGTH policy
	// it will merge the objects at each index
	const arrA = [{ a: 1 }, { b: 2 }];
	const arrB = [{ a: 3 }, { c: 4 }];

	// When merging objects in arrays, objects are merged recursively
	// [{ a: 1 }, { b: 2 }] + [{ a: 3 }, { c: 4 }] = [{ a: 3 }, { b: 2, c: 4 }]
	const expected = [{ a: 3 }, { b: 2, c: 4 }];

	assertEquals(deepMergeObjects(arrA, arrB), expected);
});
