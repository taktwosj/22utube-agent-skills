import { copyFileSync, mkdirSync } from "node:fs";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const projectRoot = resolve(dirname(fileURLToPath(import.meta.url)), "..");
const source = resolve(projectRoot, "node_modules", "gsap", "dist", "gsap.min.js");
const target = resolve(projectRoot, "assets", "vendor", "gsap.min.js");
mkdirSync(dirname(target), { recursive: true });
copyFileSync(source, target);
console.log(`VENDORED_GSAP:${target}`);
