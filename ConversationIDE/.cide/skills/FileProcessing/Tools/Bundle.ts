#!/usr/bin/env node
/**
 * Bundle CLI — Multi-format archiving tool
 * Usage: npx ts-node Bundle.ts <source> [--format zip|tar|gzip|rar|pyp] [--output path] [--name name] [--password pw]
 */
import { execSync } from 'child_process';
import { existsSync, statSync, readFileSync, writeFileSync, mkdirSync, cpSync, rmSync } from 'fs';
import { join, dirname, basename, resolve, extname } from 'path';

const FORMATS = ['zip', 'tar', 'gzip', 'rar', 'pyp'] as const;
type Format = typeof FORMATS[number];

interface BundleOpts {
  source: string;
  format: Format;
  output?: string;
  name?: string;
  password?: string;
}

function parseArgs(): BundleOpts {
  const args = process.argv.slice(2);
  if (!args.length) {
    console.error('Usage: Bundle.ts <source> [--format zip|tar|gzip|rar|pyp] [--output path] [--name name] [--password pw]');
    process.exit(1);
  }
  const opts: BundleOpts = { source: resolve(args[0]), format: 'zip' };
  for (let i = 1; i < args.length; i++) {
    switch (args[i]) {
      case '--format': opts.format = args[++i] as Format; break;
      case '--output': opts.output = resolve(args[++i]); break;
      case '--name': opts.name = args[++i]; break;
      case '--password': opts.password = args[++i]; break;
    }
  }
  if (!FORMATS.includes(opts.format)) {
    console.error(`Unsupported format: ${opts.format}. Use: ${FORMATS.join(', ')}`);
    process.exit(1);
  }
  return opts;
}

function run(cmd: string): string {
  try { return execSync(cmd, { stdio: 'pipe', windowsHide: true }).toString(); }
  catch (e: any) { throw new Error(`Command failed: ${cmd}\n${e.stderr?.toString() || e.message}`); }
}

function bundleTar(opts: BundleOpts): string {
  const out = opts.output || join(dirname(opts.source), (opts.name || basename(opts.source)) + '.tar');
  const parent = dirname(opts.source);
  const name = basename(opts.source);
  run(`tar -cf "${out}" -C "${parent}" "${name}"`);
  return out;
}

function bundleGzip(opts: BundleOpts): string {
  const out = opts.output || join(dirname(opts.source), (opts.name || basename(opts.source)) + '.tar.gz');
  const parent = dirname(opts.source);
  const name = basename(opts.source);
  run(`tar -czf "${out}" -C "${parent}" "${name}"`);
  return out;
}

function bundleZip(opts: BundleOpts): string {
  const out = opts.output || join(dirname(opts.source), (opts.name || basename(opts.source)) + '.zip');
  const isDir = existsSync(opts.source) && statSync(opts.source).isDirectory();
  if (isDir) {
    // Use PowerShell Compress-Archive for folders
    run(`powershell -NoProfile -Command "Compress-Archive -Path '${opts.source}\\*' -DestinationPath '${out}' -Force"`);
  } else {
    // Use Python zipfile module for single file
    run(`python -m zipfile -c "${out}" "${opts.source}"`);
  }
  if (opts.password) {
    // Re-pack with password via Python
    const tmp = out.replace('.zip', '_tmp.zip');
    run(`move "${out}" "${tmp}"`);
    const script = `
import zipfile, sys
src = zipfile.ZipFile("${tmp}", "r")
dst = zipfile.ZipFile("${out}", "w", zipfile.ZIP_DEFLATED)
for info in src.infolist():
    data = src.read(info.filename)
    dst.writestr(info, data)
dst.setpassword("${opts.password}".encode())
dst.close()
src.close()
`;
    writeFileSync(join(dirname(out), '_rezip.py'), script);
    run(`python "${join(dirname(out), '_rezip.py')}"`);
    rmSync(join(dirname(out), '_rezip.py'));
    rmSync(tmp);
  }
  return out;
}

function bundleRar(opts: BundleOpts): string {
  const out = opts.output || join(dirname(opts.source), (opts.name || basename(opts.source)) + '.rar');
  run(`rar a -ep1 "${out}" "${opts.source}"`);
  return out;
}

function bundlePyp(opts: BundleOpts): string {
  const cwd = process.cwd();
  const engineRoot = findEngineRoot(cwd);
  const pypScript = join(engineRoot, 'core', 'pyp_creator.py');
  if (!existsSync(pypScript)) throw new Error(`pyp_creator.py not found at ${pypScript}`);

  const name = opts.name || basename(opts.source);
  run(`python "${pypScript}" "${opts.source}" --name "${name}"`);

  // pyp_creator.py creates {name}.pyp + ARTIFACTS/ + INPUTS/ + OTHER/ alongside the source
  const parent = dirname(opts.source);
  const pypFile = join(parent, name + '.pyp');
  if (!existsSync(pypFile)) throw new Error(`pyp_creator.py did not produce ${pypFile}`);

  // If password requested, bundle everything into encrypted zip
  if (opts.password) {
    const zipOut = join(parent, name + '.pyp.zip');
    run(`powershell -NoProfile -Command "Compress-Archive -Path '${parent}\\*.pyp','${parent}\\ARTIFACTS\\*','${parent}\\INPUTS\\*','${parent}\\OTHER\\*' -DestinationPath '${join(parent, '_pyp_raw.zip')}' -Force"`);
    const script = `
import zipfile
src = zipfile.ZipFile("${join(parent, '_pyp_raw.zip')}", "r")
dst = zipfile.ZipFile("${zipOut}", "w", zipfile.ZIP_DEFLATED)
for info in src.infolist():
    data = src.read(info.filename)
    dst.writestr(info, data)
dst.setpassword("${opts.password}".encode())
dst.close()
src.close()
`;
    writeFileSync(join(parent, '_pypzip.py'), script);
    run(`python "${join(parent, '_pypzip.py')}"`);
    rmSync(join(parent, '_pypzip.py'));
    rmSync(join(parent, '_pyp_raw.zip'));
    return zipOut;
  }

  return pypFile;
}

function findEngineRoot(start: string): string {
  let dir = start;
  while (dir.length > 3) {
    if (existsSync(join(dir, 'core', 'pyp_creator.py'))) return dir;
    dir = dirname(dir);
  }
  return start;
}

function main() {
  const opts = parseArgs();
  console.log(`📦 Bundling: ${opts.source}`);
  console.log(`   Format:   ${opts.format}`);
  if (opts.name) console.log(`   Name:     ${opts.name}`);
  if (opts.password) console.log(`   Password: yes`);

  const handlers: Record<Format, (o: BundleOpts) => string> = {
    tar: bundleTar,
    gzip: bundleGzip,
    zip: bundleZip,
    rar: bundleRar,
    pyp: bundlePyp,
  };

  const out = handlers[opts.format](opts);
  const size = existsSync(out) ? (statSync(out).size / 1024).toFixed(1) : '?';
  console.log(`✅ Created: ${out} (${size} KB)`);
}

main();
