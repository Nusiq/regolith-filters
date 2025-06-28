/**
 * Represents a dynamic key in a JSON template. When evaluated, it creates a key-value pair
 * where the key is the identifier and the value is evaluated in the provided scope.
 */
export class K {
	constructor(
		public identifier: string,
		public scope: Record<string, any> = {}
	) {
		// Validate that the identifier is a string
		if (typeof identifier !== "string") {
			throw new Error(
				`K class identifier must be a string, got ${typeof identifier}: ${JSON.stringify(
					identifier
				)}`
			);
		}
	}
}

/**
 * Shorthand function for creating K instances without using 'new'
 */
export function k(identifier: string, scope: Record<string, any> = {}): K {
	return new K(identifier, scope);
}

/**
 * Represents a string joining operation in a JSON template. When used as the first element
 * in an array, it causes the remaining elements to be joined with the specified separator.
 */
export class JoinStr {
	constructor(public separator: string) {}
}

/**
 * Shorthand function for creating JoinStr instances without using 'new'
 */
export function joinStr(separator: string): JoinStr {
	return new JoinStr(separator);
}

/**
 * Type guard to check if a value is a backtick-enclosed expression.
 * These expressions are evaluated at runtime to produce dynamic values.
 */
function isBacktickExpression(value: unknown): value is string {
	return (
		typeof value === "string" && value.startsWith("`") && value.endsWith("`")
	);
}

/**
 * Evaluates a JavaScript expression in the context of the provided scope.
 * The expression can access all scope variables and the template helper functions (K, JoinStr, k, joinStr).
 */
function evaluateExpression(expr: string, scope: Record<string, any>): any {
	// Create parameter names and values arrays for the function
	// "k" is imported as "K" to let users use variables named "k"
	const paramNames = ["K", "joinStr", ...Object.keys(scope)];
	const paramValues = [k, joinStr, ...Object.values(scope)];

	// Create a function with our parameters
	const fn = new Function(...paramNames, `return ${expr};`);

	// Execute the function with our context values
	return fn(...paramValues);
}

/**
 * Evaluates an __unpack__ expression, which can be either a backtick expression
 * that evaluates to an array or a direct array value.
 */
function evaluateUnpackExpression(
	item: any,
	scope: Record<string, any>
): any[] {
	if (isBacktickExpression(item.__unpack__)) {
		const expr = item.__unpack__.slice(1, -1);
		const evaluatedUnpack = evaluateExpression(expr, scope);

		if (!Array.isArray(evaluatedUnpack)) {
			throw new Error(
				`__unpack__ expression must evaluate to an array, got ${typeof evaluatedUnpack}: ${JSON.stringify(
					evaluatedUnpack
				)}`
			);
		}

		return evaluatedUnpack;
	}

	if (Array.isArray(item.__unpack__)) {
		return item.__unpack__;
	}

	throw new Error(
		`__unpack__ must be an array or a backtick expression that evaluates to an array, got ${typeof item.__unpack__}: ${JSON.stringify(
			item.__unpack__
		)}`
	);
}

/**
 * Validates that an unpack scope is a valid object that can be used for evaluation.
 */
function validateUnpackScope(unpackScope: any): void {
	if (typeof unpackScope !== "object" || unpackScope === null) {
		throw new Error(
			`Each item in __unpack__ must be an object to use as scope, got ${typeof unpackScope}: ${JSON.stringify(
				unpackScope
			)}`
		);
	}
}

/**
 * Evaluates a JSON template, replacing dynamic expressions with their computed values.
 *
 * The template can contain:
 * - Backtick-enclosed expressions (`2 + 2`)
 * - K objects for dynamic keys
 * - JoinStr objects for string joining
 * - __unpack__ for array expansion
 * - __value__ for conditional inclusion
 *
 * Undefined values are skipped, allowing for conditional inclusion of properties.
 */
export function evaluate(template: any, scope: Record<string, any> = {}): any {
	if (template === null || template === undefined) {
		return template;
	}

	// Handle arrays
	if (Array.isArray(template)) {
		const result: any[] = [];

		for (const item of template) {
			if (typeof item === "object" && item !== null && "__unpack__" in item) {
				const unpackScopes = evaluateUnpackExpression(item, scope);

				if ("__value__" in item) {
					// If __value__ is present, evaluate it for each scope and add to results
					for (const unpackScope of unpackScopes) {
						validateUnpackScope(unpackScope);
						const mergedScope = { ...scope, ...unpackScope };

						const value = isBacktickExpression(item.__value__)
							? evaluateExpression(item.__value__.slice(1, -1), mergedScope)
							: evaluate(item.__value__, mergedScope);

						if (value !== undefined) {
							result.push(value);
						}
					}
				} else {
					// Otherwise evaluate the rest of the object for each scope
					for (const unpackScope of unpackScopes) {
						validateUnpackScope(unpackScope);
						const mergedScope = { ...scope, ...unpackScope };
						const { __unpack__, ...rest } = item;
						const evaluatedItem = evaluate(rest, mergedScope);
						if (evaluatedItem !== undefined) {
							result.push(evaluatedItem);
						}
					}
				}
			} else {
				const evaluatedItem = evaluate(item, scope);
				if (evaluatedItem !== undefined) {
					result.push(evaluatedItem);
				}
			}
		}

		// After expanding all elements, check if this is a JoinStr operation
		if (result.length > 0 && result[0] instanceof JoinStr) {
			const separator = result[0].separator;
			const items = result.slice(1).map((item) => String(item));
			return items.join(separator);
		}

		return result;
	}

	// Handle objects
	if (typeof template === "object" && template !== null) {
		const result: Record<string, any> = {};

		for (const [key, value] of Object.entries(template)) {
			// Check if key is an expression
			if (isBacktickExpression(key)) {
				const expr = key.slice(1, -1);
				const evaluatedKey = evaluateExpression(expr, scope);

				if (evaluatedKey === undefined) {
					continue; // Skip this key
				}

				if (evaluatedKey instanceof K) {
					// Single K instance
					const evaluatedValue = evaluate(value, {
						...scope,
						...evaluatedKey.scope,
					});
					if (evaluatedValue !== undefined) {
						result[evaluatedKey.identifier] = evaluatedValue;
					}
				} else if (Array.isArray(evaluatedKey)) {
					// Check the content of the array
					if (evaluatedKey.every((item) => item instanceof K)) {
						// Array of K instances
						for (const k of evaluatedKey) {
							const evaluatedValue = evaluate(value, { ...scope, ...k.scope });
							if (evaluatedValue !== undefined) {
								result[k.identifier] = evaluatedValue;
							}
						}
					} else if (evaluatedKey.every((item) => typeof item === "string")) {
						// Array of strings - shortcut for array of K objects with empty scopes
						for (const key of evaluatedKey) {
							const evaluatedValue = evaluate(value, scope);
							if (evaluatedValue !== undefined) {
								result[key] = evaluatedValue;
							}
						}
					} else {
						throw new Error(
							`Array keys must contain only K instances or strings, got mixed types: ${JSON.stringify(
								evaluatedKey
							)}`
						);
					}
				} else {
					// For any other type, we require a string
					if (typeof evaluatedKey !== "string") {
						throw new Error(
							`Object keys must be strings, got ${typeof evaluatedKey}: ${JSON.stringify(
								evaluatedKey
							)}`
						);
					}

					// Regular string key
					const evaluatedValue = evaluate(value, scope);
					if (evaluatedValue !== undefined) {
						result[evaluatedKey] = evaluatedValue;
					}
				}
			} else {
				// Regular key
				const evaluatedValue = evaluate(value, scope);
				if (evaluatedValue !== undefined) {
					result[key] = evaluatedValue;
				}
			}
		}

		return result;
	}

	// Handle string values that may be expressions
	if (isBacktickExpression(template)) {
		const expr = template.slice(1, -1);
		return evaluateExpression(expr, scope);
	}

	// Return other primitive values as is
	return template;
}
