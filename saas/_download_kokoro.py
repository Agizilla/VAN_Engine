import urllib.request
import tarfile
import os
import sys

model_dir = os.path.join(os.path.dirname(__file__), 'tts_models')
os.makedirs(model_dir, exist_ok=True)

# Try smaller int8 model first (~100MB vs 312MB)
url = 'https://github.com/k2-fsa/sherpa-onnx/releases/download/tts-models/kokoro-int8-en-v0_19.tar.bz2'
tarball = os.path.join(model_dir, 'kokoro-int8-en-v0_19.tar.bz2')

def report(block, blocksize, totalsize):
    downloaded = block * blocksize / (1024*1024)
    if totalsize > 0:
        total_mb = totalsize / (1024*1024)
        pct = min(100, downloaded / total_mb * 100)
        sys.stdout.write('\r  Downloading: %.1f / %.1f MB (%.0f%%)' % (downloaded, total_mb, pct))
    else:
        sys.stdout.write('\r  Downloaded: %.1f MB' % downloaded)
    sys.stdout.flush()

print('Downloading kokoro-int8-en-v0_19 (~100MB)...')
urllib.request.urlretrieve(url, tarball, report)
print('\nDownload complete. Extracting...')
with tarfile.open(tarball, 'r:bz2') as tar:
    tar.extractall(path=model_dir)
os.remove(tarball)
print('Extraction complete.')
model_path = os.path.join(model_dir, 'kokoro-int8-en-v0_19')
for f in sorted(os.listdir(model_path)):
    fp = os.path.join(model_path, f)
    print('  %s  (%d bytes)' % (f, os.path.getsize(fp)))
