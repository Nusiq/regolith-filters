import { assert, assertEquals } from "@std/assert";
import { dirname, basename, join } from "@std/path";
import {
	applyModules,
	isModulePathIncluded,
	processModules,
} from "./map-ts.ts";

async function withTempProject(
	files: Record<string, string>,
	callback: (tempDir: string) => Promise<void>
): Promise<void> {
	const originalCwd = Deno.cwd();
	const tempDir = await Deno.makeTempDir();
	const projectFiles = {
		"data/modular_mc/auto-map.ts": "export const AUTO_MAP = {};\n",
		...files,
	};

	try {
		for (const [relativePath, content] of Object.entries(projectFiles)) {
			const absolutePath = join(tempDir, relativePath);
			await Deno.mkdir(dirname(absolutePath), { recursive: true });
			await Deno.writeTextFile(absolutePath, content);
		}

		Deno.chdir(tempDir);
		await callback(tempDir);
	} finally {
		Deno.chdir(originalCwd);
		await Deno.remove(tempDir, { recursive: true });
	}
}

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

Deno.test("processModules sorts glob-expanded sources deterministically", async () => {
	await withTempProject(
		{
			"data/modular_mc/example/_map.ts":
				'export const MAP = [{ source: "files/*.txt", target: "BP/" }];\n',
			"data/modular_mc/example/files/b.txt": "b\n",
			"data/modular_mc/example/files/a.txt": "a\n",
			"data/modular_mc/example/files/c.txt": "c\n",
		},
		async () => {
			const modules = await processModules("data/modular_mc");

			assertEquals(modules.length, 1);
			assertEquals(
				modules[0].entries.map((entry) => basename(entry.source)),
				["a.txt", "b.txt", "c.txt"]
			);
		}
	);
});

Deno.test(
	"applyModules preserves same-target append order across modules",
	async () => {
		await withTempProject(
			{
				"data/modular_mc/01_base/_map.ts":
					'export const MAP = [{ source: "base.txt", target: "BP/out.txt" }];\n',
				"data/modular_mc/01_base/base.txt": "BASE\n",
				"data/modular_mc/02_prefix/_map.ts":
					'export const MAP = [{ source: "prefix.txt", target: "BP/out.txt", onConflict: "appendStart" }];\n',
				"data/modular_mc/02_prefix/prefix.txt": "START\n",
				"data/modular_mc/03_suffix/_map.ts":
					'export const MAP = [{ source: "suffix.txt", target: "BP/out.txt", onConflict: "appendEnd" }];\n',
				"data/modular_mc/03_suffix/suffix.txt": "END\n",
			},
			async () => {
				const modules = await processModules("data/modular_mc");
				await applyModules(modules);

				const output = await Deno.readTextFile("BP/out.txt");
				assertEquals(output, "START\nBASE\nEND\n");
			}
		);
	}
);

Deno.test(
	"applyModules preserves same-target merge and skip order across modules",
	async () => {
		await withTempProject(
			{
				"data/modular_mc/01_base/_map.ts":
					'export const MAP = [{ source: "base.json", target: "BP/out.json" }];\n',
				"data/modular_mc/01_base/base.json":
					'{ "name": "base", "values": [1], "nested": { "a": true } }\n',
				"data/modular_mc/02_merge/_map.ts":
					'export const MAP = [{ source: "merge.json", target: "BP/out.json", onConflict: "merge" }];\n',
				"data/modular_mc/02_merge/merge.json":
					'{ "values": [2], "nested": { "b": true } }\n',
				"data/modular_mc/03_skip/_map.ts":
					'export const MAP = [{ source: "skip.json", target: "BP/out.json", onConflict: "skip" }];\n',
				"data/modular_mc/03_skip/skip.json":
					'{ "name": "ignored", "values": [999] }\n',
			},
			async () => {
				const modules = await processModules("data/modular_mc");
				await applyModules(modules);

				const output = JSON.parse(await Deno.readTextFile("BP/out.json"));
				assertEquals(output, {
					name: "base",
					values: [1, 2],
					nested: {
						a: true,
						b: true,
					},
				});
			}
		);
	}
);

Deno.test("applyModules supports sequential execution mode", async () => {
	await withTempProject(
		{
			"data/modular_mc/01_base/_map.ts":
				'export const MAP = [{ source: "base.txt", target: "BP/out.txt" }];\n',
			"data/modular_mc/01_base/base.txt": "BASE\n",
			"data/modular_mc/02_prefix/_map.ts":
				'export const MAP = [{ source: "prefix.txt", target: "BP/out.txt", onConflict: "appendStart" }];\n',
			"data/modular_mc/02_prefix/prefix.txt": "START\n",
			"data/modular_mc/03_suffix/_map.ts":
				'export const MAP = [{ source: "suffix.txt", target: "BP/out.txt", onConflict: "appendEnd" }];\n',
			"data/modular_mc/03_suffix/suffix.txt": "END\n",
		},
		async () => {
			const modules = await processModules("data/modular_mc");
			await applyModules(modules, { mode: "sequential" });

			const output = await Deno.readTextFile("BP/out.txt");
			assertEquals(output, "START\nBASE\nEND\n");
		}
	);
});
