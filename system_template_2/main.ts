import { evaluate } from "./json-template.ts";

// Example usage
const template = {
	"`'greeting'`": "`message + '!'`",
};

const result = evaluate(template, { message: "Hello world" });
console.log(result);
