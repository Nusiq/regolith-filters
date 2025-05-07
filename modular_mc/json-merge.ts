/**
 * Defines policies for merging lists in deep merge operations.
 */
export enum ListMergePolicy {
	/**
	 * Use the greater length of two lists when merging
	 */
	GREATER_LENGTH,

	/**
	 * Use the smaller length of two lists when merging
	 */
	SMALLER_LENGTH,

	/**
	 * Always use the length of the second list (B)
	 */
	B_LENGTH,

	/**
	 * Append items from list B to list A
	 */
	APPEND,
}

/**
 * Merges two JSON objects A and B recursively. In case of conflicts
 * (situations where merging is not possible) the value from B overwrites value from A.
 * The function doesn't always create a copy of parts of A and B.
 * Sometimes uses references to objects that already exist in A or B which
 * means that editing returned structure may edit some values in A or B.
 *
 * @param a First object to merge
 * @param b Second object to merge (takes precedence in conflicts)
 * @param listMergePolicy Policy for merging arrays
 * @returns Merged object
 */
export function deepMergeObjects(
	a: any,
	b: any,
	listMergePolicy: ListMergePolicy = ListMergePolicy.GREATER_LENGTH
): any {
	// If types are different, unable to merge
	if (typeof a !== typeof b) {
		return b;
	}

	// Both types are the same
	if (a !== null && b !== null) {
		if (typeof a === "object") {
			if (Array.isArray(a) && Array.isArray(b)) {
				// Both are arrays
				return deepMergeLists(a, b, listMergePolicy);
			} else if (!Array.isArray(a) && !Array.isArray(b)) {
				// Both are objects (but not arrays)
				return deepMergeDict(a, b, listMergePolicy);
			}
		}
	}

	// For primitive types or when one is null/array and the other is object
	return b;
}

/**
 * Merges two dictionaries A and B recursively. In case of conflicts
 * (situations where merging is not possible) the value from B overwrites value from A.
 *
 * @param a First dictionary to merge
 * @param b Second dictionary to merge (takes precedence in conflicts)
 * @param listMergePolicy Policy for merging arrays
 * @returns Merged dictionary
 */
export function deepMergeDict(
	a: Record<string, any>,
	b: Record<string, any>,
	listMergePolicy: ListMergePolicy = ListMergePolicy.GREATER_LENGTH
): Record<string, any> {
	const result: Record<string, any> = {};
	// Combine keys from both objects (preserving order similar to Python implementation)
	const keys = [...Object.keys(a), ...Object.keys(b)];
	const usedKeys = new Set<string>();

	for (const k of keys) {
		if (usedKeys.has(k)) {
			continue;
		}
		usedKeys.add(k);

		if (k in b) {
			if (!(k in a)) {
				// In B not in A
				result[k] = b[k];
				continue;
			}
			// In both A and B
			result[k] = deepMergeObjects(a[k], b[k], listMergePolicy);
		} else if (k in a) {
			// In A not in B
			result[k] = a[k];
		}
	}

	return result;
}

/**
 * Merges two lists A and B recursively. In case of conflicts
 * (situations where merging is not possible) the value from B overwrites value from A.
 *
 * @param a First list to merge
 * @param b Second list to merge (takes precedence in conflicts)
 * @param listMergePolicy Policy for merging arrays
 * @returns Merged list
 */
export function deepMergeLists(
	a: any[],
	b: any[],
	listMergePolicy: ListMergePolicy = ListMergePolicy.GREATER_LENGTH
): any[] {
	let listLen: number;

	// Determine the length of the result list based on policy
	switch (listMergePolicy) {
		case ListMergePolicy.GREATER_LENGTH:
			listLen = Math.max(a.length, b.length);
			break;
		case ListMergePolicy.SMALLER_LENGTH:
			listLen = Math.min(a.length, b.length);
			break;
		case ListMergePolicy.B_LENGTH:
			listLen = b.length;
			break;
		case ListMergePolicy.APPEND:
			// Special case: append B to A
			return [...a, ...b];
	}

	// Create result array with determined length
	const result: any[] = new Array(listLen).fill(null);

	for (let i = 0; i < listLen; i++) {
		if (i < b.length) {
			if (i >= a.length) {
				// In B not in A
				result[i] = b[i];
				continue;
			}
			// In both A and B
			result[i] = deepMergeObjects(a[i], b[i], listMergePolicy);
		} else if (i < a.length) {
			// In A not in B
			result[i] = a[i];
		}
	}

	return result;
}
