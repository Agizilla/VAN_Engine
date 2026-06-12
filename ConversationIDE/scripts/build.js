const { execSync } = require('child_process');
const fs = require('fs');
const path = require('path');

async function build() {
  console.log('Building Conversation-IDE...');

  const distDir = path.join(__dirname, '..', 'dist');
  const releaseDir = path.join(__dirname, '..', 'release');

  if (fs.existsSync(distDir)) {
    fs.rmSync(distDir, { recursive: true });
  }
  if (fs.existsSync(releaseDir)) {
    fs.rmSync(releaseDir, { recursive: true });
  }

  execSync('npx tsc -p tsconfig.json', { stdio: 'inherit', cwd: path.join(__dirname, '..') });
  execSync('npx vite build', { stdio: 'inherit', cwd: path.join(__dirname, '..') });
  execSync('npx electron-builder', { stdio: 'inherit', cwd: path.join(__dirname, '..') });

  console.log('Build complete!');
}

build().catch(err => {
  console.error('Build failed:', err);
  process.exit(1);
});
