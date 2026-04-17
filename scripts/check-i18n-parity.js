#!/usr/bin/env node
/**
 * Verifies that messages/en.json and messages/de.json have identical key structures.
 * Run: node scripts/check-i18n-parity.js
 * Exit code 0 = parity OK, 1 = mismatch found.
 */
import fs from "fs";
import path from "path";
import { fileURLToPath } from "url";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const messagesDir = path.join(__dirname, "..", "frontend", "messages");
const en = JSON.parse(fs.readFileSync(path.join(messagesDir, "en.json"), "utf8"));
const de = JSON.parse(fs.readFileSync(path.join(messagesDir, "de.json"), "utf8"));

function collectKeys(obj, prefix = "") {
  const keys = [];
  for (const [k, v] of Object.entries(obj)) {
    const full = prefix ? `${prefix}.${k}` : k;
    if (typeof v === "object" && v !== null && !Array.isArray(v)) {
      keys.push(...collectKeys(v, full));
    } else {
      keys.push(full);
    }
  }
  return keys;
}

const enKeys = new Set(collectKeys(en));
const deKeys = new Set(collectKeys(de));

const missingInDe = [...enKeys].filter((k) => !deKeys.has(k));
const missingInEn = [...deKeys].filter((k) => !enKeys.has(k));

if (missingInDe.length > 0) {
  console.error("❌ Keys present in en.json but missing in de.json:");
  missingInDe.forEach((k) => console.error(`  - ${k}`));
}
if (missingInEn.length > 0) {
  console.error("❌ Keys present in de.json but missing in en.json:");
  missingInEn.forEach((k) => console.error(`  - ${k}`));
}

if (missingInDe.length === 0 && missingInEn.length === 0) {
  console.log("✅ i18n parity OK — en.json and de.json have identical key structures.");
  process.exit(0);
} else {
  process.exit(1);
}
