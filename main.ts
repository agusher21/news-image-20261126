// news-image-20261126 — entry point (Node 22, standard library only).
// The front page is the entry.png beside this file, drawn by tools/generate.py.
// This file just hands that exact image to the grader: it copies entry.png
// into the output directory (MAKEFUN_OUTPUT_DIR outside the grader,
// /output inside it). Nothing is redrawn or resized here.
import { copyFileSync } from 'node:fs';
import { join } from 'node:path';

const root = new URL('.', import.meta.url).pathname;
const outDir = process.env.MAKEFUN_OUTPUT_DIR ?? '/output';
copyFileSync(join(root, 'entry.png'), join(outDir, 'entry.png'));
