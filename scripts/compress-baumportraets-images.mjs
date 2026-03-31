/**
 * compress-baumportraets-images.mjs
 * Compresses and copies all Baumarten­porträts images to public/baumportraets/images/
 *
 * Large images (borke, knospe, sommerzweig, bluetenstand) → 1200px wide, quality 82
 * Small images (blatt, frucht, oekogramm, verbreitung)    → 900px wide,  quality 85
 *
 * Run with: node scripts/compress-baumportraets-images.mjs
 */

import sharp from 'sharp';
import { readdir, mkdir } from 'fs/promises';
import { join, basename } from 'path';
import { fileURLToPath } from 'url';

const SRC = 'C:/Users/julim/OneDrive - Bildungszentrum Wald Lyss/Muhmenthaler/3_Projekte/99_privat/3_Claude_Code_Projects/6_Baumartenporträts_Website/images';
const DEST = './public/baumportraets/images';

// Large-detail images: resize to 1200px wide
const LARGE_TYPES = ['borke', 'knospe', 'sommerzweig', 'bluetenstand'];
// Small/map images: resize to 900px wide
const SMALL_TYPES = ['blatt', 'frucht', 'oekogramm', 'verbreitung'];

await mkdir(DEST, { recursive: true });

const files = (await readdir(SRC)).filter(f => f.endsWith('.jpg') || f.endsWith('.png'));
console.log(`Found ${files.length} images to process...`);

let done = 0;
let totalOriginal = 0;
let totalCompressed = 0;

for (const file of files) {
  const srcPath = join(SRC, file);
  const destPath = join(DEST, file);
  const name = basename(file, '.jpg');

  const isLarge = LARGE_TYPES.some(t => name.endsWith(`_${t}`));
  const width  = isLarge ? 1200 : 900;
  const quality = isLarge ? 82 : 85;

  try {
    const img = sharp(srcPath);
    const meta = await img.metadata();
    const originalSize = meta.size ?? 0;

    await img
      .resize({ width, withoutEnlargement: true })
      .jpeg({ quality, mozjpeg: true })
      .toFile(destPath);

    const { size: newSize } = await import('fs').then(m =>
      m.promises.stat(destPath)
    );

    totalOriginal   += originalSize;
    totalCompressed += newSize;
    done++;

    const ratio = originalSize > 0
      ? Math.round((1 - newSize / originalSize) * 100)
      : 0;
    process.stdout.write(`[${done}/${files.length}] ${file} — ${ratio}% smaller\n`);
  } catch (err) {
    console.error(`ERROR on ${file}:`, err.message);
  }
}

const savedMB = ((totalOriginal - totalCompressed) / 1024 / 1024).toFixed(1);
const totalMB  = (totalCompressed / 1024 / 1024).toFixed(1);
console.log(`\nDone! ${done} images processed.`);
console.log(`Total size: ${totalMB} MB (saved ~${savedMB} MB)`);
