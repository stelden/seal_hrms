// Copyright (c) 2026, Stelden EA Ltd and contributors
// For license information, please see license.txt

// jsdom lacks matchMedia, which the library's colour mode and phone layouts read.
if (!window.matchMedia) {
	window.matchMedia = (query: string) =>
		({
			matches: false,
			media: query,
			onchange: null,
			addListener: () => {},
			removeListener: () => {},
			addEventListener: () => {},
			removeEventListener: () => {},
			dispatchEvent: () => false,
		}) as MediaQueryList;
}

// jsdom has no PointerEvent; Base UI's controls (Switch, Checkbox, Radio) dispatch one on click.
if (!window.PointerEvent) window.PointerEvent = MouseEvent as unknown as typeof PointerEvent;

// jsdom's CSS has no supports() or registerProperty(); without them SealProvider shows its
// "please update your browser" page instead of the screen.
Object.assign(globalThis, { CSS: { ...globalThis.CSS, supports: () => true, registerProperty: () => {} } });

// jsdom's AbortSignal is not the one Node's Request accepts, so a data router's navigation dies in
// tests ("Expected signal to be an instance of AbortSignal"). The router needs only these fields.
class RouterRequest {
	url: string;
	method: string;
	signal?: AbortSignal;
	headers = new Headers();
	constructor(input: string | URL, init: { method?: string; signal?: AbortSignal } = {}) {
		this.url = String(input);
		this.method = init.method ?? "GET";
		this.signal = init.signal;
	}
}
Object.assign(globalThis, { Request: RouterRequest });
