/**
 * Executes a function in a specific working directory and restores the original working directory afterward.
 * This is useful for operations that need to be performed in a specific directory context.
 *
 * WARNING: Since this function changes the working directory temporarily it's important not to call
 * multiple functions that do that and rely on the working directory asynchronously.
 *
 * @param dir - The directory to change to before executing the function
 * @param fn - The function to execute in the specified directory
 * @returns The result of the executed function
 * @throws If the directory change fails or if the function throws an error
 */
export async function withWd<T>(
	dir: string,
	fn: () => Promise<T> | T
): Promise<T> {
	const originalDir = Deno.cwd();
	try {
		// Change to the specified directory
		Deno.chdir(dir);
		// Execute the function
		return await fn();
	} finally {
		// Always restore the original directory, even if an error occurred
		Deno.chdir(originalDir);
	}
}
