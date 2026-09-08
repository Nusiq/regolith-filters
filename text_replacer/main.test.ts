import { assertEquals } from "@std/assert";
import { collectFiles, parseSettings, replaceInFile, runReplacement } from "./main.ts";

export async function parseSettings_parses_valid_settings_and_normalizes_paths() {
	const settings = parseSettings([
		JSON.stringify({
			replace_from: "a",
			replace_to: "b",
			paths: ["RP\\sub\\", "BP/"],
		}),
	]);
	assertEquals(settings, {
		replace_from: "a",
		replace_to: "b",
		paths: ["RP/sub", "BP"],
	});
}

export async function parseSettings_falls_back_to_default_paths() {
	const settings = parseSettings([
		JSON.stringify({ replace_from: "a", replace_to: "b" }),
	]);
	assertEquals(settings, {
		replace_from: "a",
		replace_to: "b",
		paths: ["RP", "BP"],
	});
}

export async function collectFiles_collects_files_from_nested_folders() {
	const root = await Deno.makeTempDir();
	try {
		await Deno.mkdir(`${root}/a/b`, { recursive: true });
		await Deno.mkdir(`${root}/c`);
		await Deno.writeTextFile(`${root}/a/1.txt`, "1");
		await Deno.writeTextFile(`${root}/a/b/2.txt`, "2");
		await Deno.writeTextFile(`${root}/c/3.txt`, "3");
		const files: string[] = [];
		await collectFiles(root, files);
		assertEquals(
			files.map((path) => path.slice(root.length + 1)).sort(),
			["a/1.txt", "a/b/2.txt", "c/3.txt"]
		);
	} finally {
		await Deno.remove(root, { recursive: true });
	}
}

export async function replaceInFile_replaces_all_occurrences_of_the_text() {
	const root = await Deno.makeTempDir();
	try {
		const path = `${root}/file.txt`;
		await Deno.writeTextFile(path, "foo bar foo");
		assertEquals(await replaceInFile(path, "foo", "baz"), true);
		assertEquals(await Deno.readTextFile(path), "baz bar baz");
	} finally {
		await Deno.remove(root, { recursive: true });
	}
}

export async function replaceInFile_reports_unmodified_files() {
	const root = await Deno.makeTempDir();
	try {
		const path = `${root}/file.txt`;
		await Deno.writeTextFile(path, "foo bar");
		assertEquals(await replaceInFile(path, "missing", "baz"), false);
		assertEquals(await Deno.readTextFile(path), "foo bar");
	} finally {
		await Deno.remove(root, { recursive: true });
	}
}

export async function replaceInFile_skips_files_that_are_not_valid_utf8() {
	const root = await Deno.makeTempDir();
	try {
		const path = `${root}/file.bin`;
		const bytes = [0xff, 0xfe, 0x00, 0x01];
		await Deno.writeFile(path, new Uint8Array(bytes));
		assertEquals(await replaceInFile(path, "a", "b"), false);
		assertEquals(Array.from(await Deno.readFile(path)), bytes);
	} finally {
		await Deno.remove(root, { recursive: true });
	}
}

export async function runReplacement_replaces_text_in_the_pack_folders() {
	const root = await Deno.makeTempDir();
	try {
		await Deno.mkdir(`${root}/RP/textures`, { recursive: true });
		await Deno.mkdir(`${root}/BP/functions`, { recursive: true });
		await Deno.mkdir(`${root}/ignored`, { recursive: true });
		await Deno.writeTextFile(`${root}/RP/a.json`, '{"id": "@namespace"}');
		await Deno.writeTextFile(`${root}/RP/textures/b.json`, "@namespace @namespace");
		await Deno.writeTextFile(`${root}/BP/functions/c.mcfunction`, "say @namespace");
		await Deno.writeTextFile(`${root}/BP/d.txt`, "no match here");
		await Deno.writeFile(
			`${root}/BP/functions/e.png`,
			new Uint8Array([0x89, 0x50, 0xff, 0xfe])
		);
		await Deno.writeTextFile(`${root}/ignored/f.json`, "@namespace");

		const { scanned, modified } = await runReplacement({
			replace_from: "@namespace",
			replace_to: "demo_ns",
			paths: [`${root}/RP`, `${root}/BP`],
		});
		// Scanned: a.json, b.json, c.mcfunction, d.txt, e.png (ignored/ is not
		// in the scanned paths).
		assertEquals(scanned, 5);
		// Modified: a.json, b.json and c.mcfunction.
		assertEquals(modified, 3);
		assertEquals(await Deno.readTextFile(`${root}/RP/a.json`), '{"id": "demo_ns"}');
		assertEquals(
			await Deno.readTextFile(`${root}/RP/textures/b.json`),
			"demo_ns demo_ns"
		);
		assertEquals(
			await Deno.readTextFile(`${root}/BP/functions/c.mcfunction`),
			"say demo_ns"
		);
		assertEquals(await Deno.readTextFile(`${root}/BP/d.txt`), "no match here");
		// The binary file must stay untouched.
		assertEquals(
			Array.from(await Deno.readFile(`${root}/BP/functions/e.png`)),
			[0x89, 0x50, 0xff, 0xfe]
		);
		// Files outside of the scanned paths must stay untouched.
		assertEquals(await Deno.readTextFile(`${root}/ignored/f.json`), "@namespace");
	} finally {
		await Deno.remove(root, { recursive: true });
	}
}

export async function runReplacement_preserves_the_BOM_of_utf8_files() {
	const root = await Deno.makeTempDir();
	try {
		await Deno.mkdir(`${root}/RP`, { recursive: true });
		const path = `${root}/RP/bom.json`;
		const content = new TextEncoder().encode('{"a": "@namespace"}');
		const bytes = new Uint8Array(3 + content.length);
		bytes.set([0xef, 0xbb, 0xbf]);
		bytes.set(content, 3);
		await Deno.writeFile(path, bytes);

		await runReplacement({
			replace_from: "@namespace",
			replace_to: "x",
			paths: [`${root}/RP`],
		});
		const result = await Deno.readFile(path);
		assertEquals(Array.from(result.slice(0, 3)), [0xef, 0xbb, 0xbf]);
		assertEquals(new TextDecoder().decode(result.subarray(3)), '{"a": "x"}');
	} finally {
		await Deno.remove(root, { recursive: true });
	}
}

Deno.test(
	"parseSettings parses valid settings and normalizes paths",
	parseSettings_parses_valid_settings_and_normalizes_paths
);
Deno.test(
	"parseSettings falls back to default paths",
	parseSettings_falls_back_to_default_paths
);
Deno.test(
	"collectFiles collects files from nested folders",
	collectFiles_collects_files_from_nested_folders
);
Deno.test(
	"replaceInFile replaces all occurrences of the text",
	replaceInFile_replaces_all_occurrences_of_the_text
);
Deno.test(
	"replaceInFile reports unmodified files",
	replaceInFile_reports_unmodified_files
);
Deno.test(
	"replaceInFile skips files that are not valid UTF-8",
	replaceInFile_skips_files_that_are_not_valid_utf8
);
Deno.test(
	"runReplacement replaces text in the pack folders",
	runReplacement_replaces_text_in_the_pack_folders
);
Deno.test(
	"runReplacement preserves the BOM of UTF-8 files",
	runReplacement_preserves_the_BOM_of_utf8_files
);
