const fs = require('fs');
const path = require('path');

function deploy() {
  console.log('Deploying Conversation-IDE...');

  const releaseDir = path.join(__dirname, '..', 'release');
  const vanEngineDir = path.join(__dirname, '..', '..', '..', 'VAN_Engine');

  if (!fs.existsSync(releaseDir)) {
    console.error('No release directory found. Run build first.');
    process.exit(1);
  }

  const winDir = path.join(releaseDir, 'win');
  if (fs.existsSync(winDir)) {
    const dest = path.join(vanEngineDir, 'bin');
    if (!fs.existsSync(dest)) {
      fs.mkdirSync(dest, { recursive: true });
    }
    fs.cpSync(winDir, dest, { recursive: true });
    console.log('Deployed Windows build to VAN_Engine/bin');
  }

  console.log('Deploy complete!');
}

deploy();
