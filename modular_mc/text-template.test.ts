import { assertEquals } from "@std/assert";
import { evaluate } from "./text-template.ts";

Deno.test("AST-based multiple statement detection", () => {
	// Test single expressions (should add return)
	const scope = { x: 5, y: 10 };
	
	// Single expression
	assertEquals(evaluate("{ts:x + y:}", scope), "15");
	
	// Single expression with semicolon in string literal (should NOT be treated as multiple statements)
	assertEquals(evaluate('{ts:"hello; world":}', scope), "hello; world");
	
	// Multiple statements
	const multiStmtResult = evaluate("{ts:let temp = x + y; return temp * 2:}", scope);
	assertEquals(multiStmtResult, "30");
	
	// Multiple statements with newlines
	const multiStmtNewlineResult = evaluate(`{ts:
		let temp = x + y;
		return temp * 2
	:}`, scope);
	assertEquals(multiStmtNewlineResult, "30");
	
	// Expression with semicolon in comment (should be treated as single expression)
	const commentResult = evaluate("{ts:x + y; // comment:}", scope);
	assertEquals(commentResult, "15");
});
