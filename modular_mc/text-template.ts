import { ModularMcError } from "./error.ts";
import dedent from "npm:dedent";

const TS_EXPRESSION_REGEX = /{ts:(.+?):}/gs;

function evaluateExpression(expr: string, scope: Record<string, any>): any {
	// Create parameter names and values arrays for the function
	const paramNames = Object.keys(scope);
	const paramValues = Object.values(scope);

	// Check if the expression has multiple statements (contains semicolon or newlines with actual statements)
	const trimmedExpr = expr.trim();
	const lines = trimmedExpr.split('\n').map(line => line.trim()).filter(line => line.length > 0);
	const hasMultipleStatements = lines.length > 1 || trimmedExpr.includes(';');

	let functionBody: string;
	if (hasMultipleStatements) {
		// For multiple statements, use the expression as-is
		functionBody = trimmedExpr;
	} else {
		// For single expression, check if it already starts with 'return'
		if (trimmedExpr.startsWith('return ')) {
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