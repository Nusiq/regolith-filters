import { ModularMcError } from "./error.ts";
import dedent from "npm:dedent";
import * as ts from "npm:typescript";

const TS_EXPRESSION_REGEX = /{ts:(.+?):}/gs;

/**
 * Analyzes a TypeScript expression to determine if it contains multiple statements
 * @param expr The expression to analyze
 * @returns true if the expression contains multiple statements, false otherwise
 */
function isMultiStatementTS(expr: string): boolean {
	try {
		// Parse the expression as TypeScript
		return (
			ts.createSourceFile("temp.ts", expr, ts.ScriptTarget.Latest)
				.statements.length > 1
		);
	} catch {
		return false;
	}
}

function evaluateExpression(expr: string, scope: Record<string, any>): any {
	// Create parameter names and values arrays for the function
	const paramNames = Object.keys(scope);
	const paramValues = Object.values(scope);

	// Check if the expression has multiple statements using AST analysis
	const trimmedExpr = expr.trim();
	let functionBody: string;
	if (isMultiStatementTS(trimmedExpr)) {
		// For multiple statements, use the expression as-is
		functionBody = trimmedExpr;
	} else {
		// For single expression, check if it already starts with 'return'
		if (trimmedExpr.startsWith("return ")) {
			functionBody = trimmedExpr;
		} else {
			// For single expression, add return
			functionBody = `return ${trimmedExpr};`;
		}
	}

	// Create a function with our parameters
	const fn = new Function(...paramNames, functionBody);

	try {
		// Execute the function with our context values
		return fn(...paramValues);
	} catch (error) {
		throw new ModularMcError(
			dedent`
			Error evaluating TypeScript expression:
			${expr}
			
			Error: ${error}`
		);
	}
}

export function evaluate(
	content: string,
	scope: Record<string, any> = {}
): string {
	return content.replace(TS_EXPRESSION_REGEX, (_, expression) => {
		const result = evaluateExpression(expression.trim(), scope);
		return String(result);
	});
}
