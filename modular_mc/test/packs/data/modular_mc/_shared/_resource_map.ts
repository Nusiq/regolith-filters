import { fromFileUrl } from "jsr:@std/path";

export default {
	sharedBehavior: fromFileUrl(new URL("./shared.behavior.json", import.meta.url)),
};
