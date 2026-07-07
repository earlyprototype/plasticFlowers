#!/usr/bin/env node

import fs from "node:fs/promises";
import path from "node:path";

const DEFAULT_BASE_URL = process.env.API_BASE_URL ?? "http://localhost:8000";
const sleep = (ms) => new Promise((resolve) => setTimeout(resolve, ms));

async function main() {
  const args = parseArgs(process.argv.slice(2));
  if (!args.session || !args.file) {
    printUsage();
    process.exit(1);
  }

  const filePath = path.resolve(args.file);
  const contents = await fs.readFile(filePath, "utf-8");
  const chunks = JSON.parse(contents);
  if (!Array.isArray(chunks)) {
    throw new Error("Replay file must contain an array of chunks");
  }

  const delay = Number.isFinite(args.delay) ? args.delay : 1000;
  const baseUrl = DEFAULT_BASE_URL.replace(/\/$/, "");
  const endpoint = `${baseUrl}/api/sessions/${encodeURIComponent(args.session)}/chunks`;

  console.log(`Replaying ${chunks.length} chunks to ${endpoint}`);
  for (let i = 0; i < chunks.length; i += 1) {
    const chunk = chunks[i];
    if (!chunk?.text) {
      console.warn(`Skipping chunk ${i} (missing text)`);
      continue;
    }
    const payload = {
      text: chunk.text,
      start_time: chunk.start_time ?? chunk.start ?? 0,
      end_time: chunk.end_time ?? chunk.end ?? chunk.start_time ?? 0,
    };
    const response = await fetch(endpoint, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    if (!response.ok) {
      const detail = await response.text();
      console.error(`Chunk ${i + 1}/${chunks.length} failed: ${response.status} ${detail}`);
    } else {
      console.log(`Chunk ${i + 1}/${chunks.length} dispatched`);
    }
    if (i < chunks.length - 1) {
      await sleep(delay);
    }
  }
}

function parseArgs(argv) {
  const args = {};
  for (let i = 0; i < argv.length; i += 1) {
    const arg = argv[i];
    if (arg === "--session" || arg === "-s") {
      args.session = argv[++i];
    } else if (arg === "--file" || arg === "-f") {
      args.file = argv[++i];
    } else if (arg === "--delay" || arg === "-d") {
      args.delay = Number(argv[++i]);
    }
  }
  return args;
}

function printUsage() {
  console.log(`
Usage: npm run replay -- --session SESSION_ID --file chunks.json [--delay 750]

File format:
[
  { "text": "Chunk text", "start_time": 0.0, "end_time": 4.2 },
  { "text": "Next chunk", "start_time": 4.2, "end_time": 8.5 }
]
`);
}

main().catch((error) => {
  console.error(error);
  process.exit(1);
});

