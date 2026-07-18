import { readFileSync } from "node:fs";
import { verifyBundle, formatReport, type Anchors, type Bundle } from "./verify.js";

// Usage: h2a-verify <bundle.json> <anchors.json>
// Exit 0 if the record is an honest reflection of the evidence; 1 otherwise.
// Runs anywhere Node runs — outside the implementer's infrastructure, by design.
function main() {
  const [bundlePath, anchorsPath] = process.argv.slice(2);
  if (!bundlePath || !anchorsPath) {
    console.error("usage: h2a-verify <bundle.json> <anchors.json>");
    process.exit(2);
  }
  const bundle = JSON.parse(readFileSync(bundlePath, "utf8")) as Bundle;
  const anchors = JSON.parse(readFileSync(anchorsPath, "utf8")) as Anchors;
  const report = verifyBundle(bundle, anchors);
  console.log(formatReport(report));
  process.exit(report.ok ? 0 : 1);
}

main();
