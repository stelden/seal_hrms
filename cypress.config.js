const { defineConfig } = require("cypress");
const fs = require("fs");

module.exports = defineConfig({
	projectId: "seal-hrms",
	adminPassword: "21954124",
	testUser: "Administrator",
	defaultCommandTimeout: 20000,
	pageLoadTimeout: 15000,
	video: true,
	viewportHeight: 960,
	viewportWidth: 1400,
	retries: {
		runMode: 1,
		openMode: 1,
	},
	e2e: {
		setupNodeEvents(on, config) {
			on("after:spec", (spec, results) => {
				if (results && results.video) {
					const failures = results.tests.some((test) =>
						test.attempts.some((attempt) => attempt.state === "failed")
					);
					if (!failures) {
						try { fs.unlinkSync(results.video); } catch (_) {}
					}
				}
			});
			return config;
		},
		testIsolation: false,
		baseUrl: "http://localhost",
		specPattern: ["./cypress/integration/*.js"],
		supportFile: "./cypress/support/e2e.js",
	},
	env: {
		adminPassword: "21954124",
	},
});
