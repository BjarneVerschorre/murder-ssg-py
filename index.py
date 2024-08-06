const fs = require('fs-extra');
const path = require('path');
const showdown = require('showdown');
const ejs = require('ejs');

require('dotenv').config();

const buildDir = path.join(__dirname, 'build');
const sourceDir = path.join(__dirname, 'src');
const templateDir = path.join(__dirname, 'templates');
const staticDir = path.join(__dirname, 'static');

const converter = new showdown.Converter({ metadata: true });

const walk = async (dir, test) => {
	return new Promise((resolve, reject) => {
		fs.readdir(dir, async function(err, list) {
			if (err) reject(err);

			let pending = list.length;

			if (!pending) return reject(err);

			for (const file of list) {
				filePath = path.resolve(dir, file);

				const stat = await fs.stat(filePath);

				if (stat && stat.isDirectory()) {
					//Its a directory
					console.log("Directory:", filePath);

					//Ensure directory
					await fs.ensureDir(path.resolve(buildDir, file));

					//Walk subdirectory
					await walk(filePath);
				}
				else {
					//Its a file
					console.log("File:", filePath);

					let fileData = path.parse(filePath);

					//Only parse markdown files
					if (fileData.ext === ".md") {
						let fileContents = await fs.readFile(filePath, 'utf-8');
						let fileHTML = converter.makeHtml(fileContents);
						let fileMetadata = converter.getMetadata();

						//Get parent directory
						let relative = path.relative(sourceDir, fileData.dir);
						let joined = path.join(buildDir, relative);

						//Generate relative static path (ensure POSIX)
						let static = path.relative(fileData.dir, staticDir);
						//Ensure POSIX
						static = static.replace(/\\/g, "/");
						//Account for directory level
						static = static.replace('../', '');

						//Render file

						//Get a specific template, or render with a default
						let fileTemplate = fileData.template || "base";
						let fileTemplatePath = path.join(templateDir, fileTemplate + ".ejs");

						const renderedFile = await ejs.renderFile(fileTemplatePath, {
							content: fileHTML,
							static: static,
							slug: fileData.name,
							...fileMetadata
						}, { async: true });

						//Place in new directory
						let fileOutput = path.resolve(joined, fileData.name + ".html");

						await fs.outputFile(fileOutput, renderedFile);
					}
				}
			}

			resolve();
		});
	});
}

async function main (directory) {
	try {
		console.time('Execution time');
		//Ensure directories
		await fs.ensureDir(buildDir);
		await fs.ensureDir(sourceDir);
		await fs.ensureDir(templateDir);
		await fs.ensureDir(staticDir);

		if (!process.env.ERASE_BUILD !== "false") await fs.emptyDir(buildDir);

		console.log("Building...");

		//Build markdown files
		await walk(sourceDir);

		//Copy static files
		await fs.copy(staticDir, path.join(buildDir, "static"));

		console.log("Built.");
		console.timeEnd('Execution time');
	}
	catch (err) {
		console.error(err);
	}
}

main();
