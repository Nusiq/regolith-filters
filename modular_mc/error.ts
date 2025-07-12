export class ModularMcError extends Error {
	constructor(message: string) {
		// Add '>' after every new line.
		const formattedMessage = message.trim().replace(/\n/g, "\n>   ");
		super(formattedMessage);
	}

	moreInfo(info: Error | any) {
		const errorMessage = info instanceof Error ? info.message : String(info);
		this.message += `\n[+] ${errorMessage}`;
		return this;
	}
}
