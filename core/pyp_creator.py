#!/usr/bin/env python3
"""
.pyp Creator -- bundles a project folder into a self-contained .pyp skill container.

Usage:
    python pyp_creator.py <folder_path> [--name PROJECT_NAME]

What it does:
  1. Scans <folder_path> for all files recursively
  2. Inlines .md, .html, .txt, .py files into the .pyp JSON (text content)
  3. Moves ALL other files (images, configs, binaries, etc.) into ARTIFACTS/
  4. Creates empty INPUTS/ and OTHER/ directories for manual use
  5. Writes <ProjectName>.pyp alongside ARTIFACTS/, INPUTS/, OTHER/
  6. The original folder now contains only: ProjectName.pyp + ARTIFACTS/ + INPUTS/ + OTHER/
"""

import os
import sys
import json
import shutil
import argparse
from datetime import datetime


TEXT_EXTENSIONS = {'.md', '.html', '.htm', '.txt', '.py', '.pyp'}
BINARY_EXTENSIONS = {
    '.mp3', '.wav', '.ogg', '.flac', '.aac', '.wma', '.m4a',
    '.mp4', '.webm', '.avi', '.mkv', '.mov', '.wmv',
    '.png', '.jpg', '.jpeg', '.gif', '.svg', '.webp', '.ico', '.bmp',
    '.pdf', '.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx',
    '.zip', '.tar', '.gz', '.bz2', '.7z', '.rar',
    '.exe', '.dll', '.so', '.dylib', '.bin',
    '.pkl', '.pickle', '.h5', '.hdf5', '.npy', '.npz',
    '.pt', '.pth', '.ckpt', '.safetensors',
    '.db', '.sqlite', '.sqlite3',
    '.DS_Store', '.gitkeep',
}


def classify_files(root_path):
    """Scan folder and classify files into categories."""
    md_files = []
    html_files = []
    txt_files = []
    py_files = []
    prd_files = []
    artifacts = []
    inputs = []
    other = []

    for dirpath, dirnames, filenames in os.walk(root_path):
        dirnames[:] = [d for d in dirnames if not d.startswith('.') and d not in ('ARTIFACTS', 'INPUTS', 'OTHER', '__pycache__', 'node_modules', '.git', '.venv')]

        for fname in sorted(filenames):
            fpath = os.path.join(dirpath, fname)
            if os.path.islink(fpath):
                continue

            rel_path = os.path.relpath(fpath, root_path)
            ext = os.path.splitext(fname)[1].lower()
            is_prd = fname.upper().startswith('PRD') or fname.startswith('PRD_')

            if ext in TEXT_EXTENSIONS or ext == '.prd':
                try:
                    with open(fpath, 'r', encoding='utf-8', errors='replace') as f:
                        content = f.read()
                except Exception as e:
                    content = '[Error reading file: ' + str(e) + ']'

                entry = {'filename': rel_path, 'content': content}

                if is_prd or ext == '.prd' or fname.upper().startswith('PRD'):
                    prd_files.append(entry)
                elif ext == '.py':
                    py_files.append(entry)
                elif ext in ('.html', '.htm'):
                    html_files.append(entry)
                elif ext == '.md':
                    md_files.append(entry)
                elif ext == '.txt':
                    if len(content) > 50000:
                        inputs.append(rel_path)
                    else:
                        txt_files.append(entry)
                else:
                    txt_files.append(entry)
            else:
                artifacts.append(rel_path)

    # Detect setup script
    setup_script = None
    for fname in ('setup.sh', 'run.sh', 'start.sh', 'launch.sh'):
        fpath = os.path.join(root_path, fname)
        if os.path.isfile(fpath):
            try:
                with open(fpath, 'r', encoding='utf-8', errors='replace') as f:
                    setup_script = f.read()
                print('  Found setup script: ' + fname)
                break
            except:
                pass

    return {
        'setupScript': setup_script,
        'mdFiles': md_files,
        'htmlFiles': html_files,
        'txtFiles': txt_files,
        'pyFiles': py_files,
        'prdFiles': prd_files,
        'artifacts': sorted(artifacts),
        'inputs': sorted(inputs),
        'other': sorted(other),
    }


def determine_main_entry(py_files, html_files):
    for f in py_files:
        name = f['filename']
        base = os.path.basename(name)
        if base in ('main.py', 'app.py', 'run.py', 'cli.py', 'start.py'):
            return name
    for f in html_files:
        name = f['filename']
        base = os.path.basename(name)
        if base in ('index.html', 'index.htm', 'main.html'):
            return name
    if py_files:
        return py_files[0]['filename']
    if html_files:
        return html_files[0]['filename']
    return None


def get_required_args(py_files, main_entry):
    if not main_entry or not py_files:
        return []
    main_file = None
    for f in py_files:
        if f['filename'] == main_entry:
            main_file = f['content']
            break
    if not main_file:
        return []
    args = []
    lines = main_file.split('\n')
    for line in lines:
        line = line.strip()
        if 'add_argument' in line:
            import re
            matches = re.findall(r"'--?([a-zA-Z_][a-zA-Z0-9_]*)'", line)
            args.extend(matches)
        if 'dest=' in line:
            import re
            matches = re.findall(r"dest='([a-zA-Z_][a-zA-Z0-9_]*)'", line)
            args.extend(matches)
    seen = set()
    unique_args = []
    for a in args:
        if a not in seen:
            seen.add(a)
            unique_args.append(a)
    return unique_args


def create_pyp(folder_path, project_name=None):
    folder_path = os.path.abspath(folder_path)
    if not os.path.isdir(folder_path):
        print("Error: '" + folder_path + "' is not a valid directory")
        return False
    if not project_name:
        project_name = os.path.basename(folder_path)
    if project_name.endswith('.pyp'):
        project_name = project_name[:-4]

    print()
    print('[.] Creating .pyp for: ' + project_name)
    print('SRC: ' + folder_path)

    classified = classify_files(folder_path)
    main_entry = determine_main_entry(classified['pyFiles'], classified['htmlFiles'])
    required_args = get_required_args(classified['pyFiles'], main_entry)

    is_web = False
    if not classified['pyFiles'] and classified['htmlFiles']:
        is_web = True
    elif main_entry and main_entry.endswith('.html'):
        is_web = True

    pyp_data = {
        'pypVersion': '1.0.0',
        'projectName': project_name,
        'description': 'Project: ' + project_name,
        'createdAt': datetime.now().isoformat(),
        'mainEntry': main_entry,
        'requiredArgs': required_args,
        'isWebProject': is_web,
        'setupScript': classified['setupScript'],
        'mdFiles': classified['mdFiles'],
        'pyFiles': classified['pyFiles'],
        'htmlFiles': classified['htmlFiles'],
        'txtFiles': classified['txtFiles'],
        'prdFiles': classified['prdFiles'],
        'artifacts': classified['artifacts'],
        'inputs': classified['inputs'],
        'other': classified['other'],
    }

    if classified['setupScript']:
        print('  Setup script inlined (' + str(len(classified['setupScript'])) + ' chars)')

    pyp_path = os.path.join(folder_path, project_name + '.pyp')
    with open(pyp_path, 'w', encoding='utf-8') as f:
        json.dump(pyp_data, f, indent=2, ensure_ascii=False)
    pyp_size_kb = os.path.getsize(pyp_path) / 1024
    print('Created: ' + os.path.basename(pyp_path) + ' (' + str(round(pyp_size_kb, 1)) + ' KB)')

    text_count = (len(classified['mdFiles']) + len(classified['htmlFiles']) +
                  len(classified['txtFiles']) + len(classified['pyFiles']) +
                  len(classified['prdFiles']))
    print('Text files inlined: ' + str(text_count))
    print('Artifacts to move: ' + str(len(classified['artifacts'])))

    artifacts_dir = os.path.join(folder_path, 'ARTIFACTS')
    if classified['artifacts']:
        os.makedirs(artifacts_dir, exist_ok=True)
        moved = 0
        for rel_path in classified['artifacts']:
            src = os.path.join(folder_path, rel_path)
            dst = os.path.join(artifacts_dir, rel_path)
            os.makedirs(os.path.dirname(dst), exist_ok=True)
            if os.path.exists(src):
                shutil.move(src, dst)
                moved += 1
        print('Moved ' + str(moved) + ' files to ARTIFACTS/')
        for rel_path in sorted(classified['artifacts'], reverse=True):
            src_dir = os.path.dirname(os.path.join(folder_path, rel_path))
            while src_dir != folder_path:
                try:
                    if os.path.isdir(src_dir) and not os.listdir(src_dir):
                        os.rmdir(src_dir)
                except:
                    pass
                src_dir = os.path.dirname(src_dir)

    if classified['inputs']:
        inputs_dir = os.path.join(folder_path, 'INPUTS')
        os.makedirs(inputs_dir, exist_ok=True)
        for rel_path in classified['inputs']:
            src = os.path.join(folder_path, rel_path)
            dst = os.path.join(inputs_dir, rel_path)
            os.makedirs(os.path.dirname(dst), exist_ok=True)
            if os.path.exists(src):
                shutil.move(src, dst)

    os.makedirs(os.path.join(folder_path, 'INPUTS'), exist_ok=True)
    os.makedirs(os.path.join(folder_path, 'OTHER'), exist_ok=True)

    # Remove original text files that are now inlined in the .pyp
    all_inlined = (classified['mdFiles'] + classified['htmlFiles'] +
                   classified['txtFiles'] + classified['pyFiles'] +
                   classified['prdFiles'])
    removed = 0
    for entry in all_inlined:
        src = os.path.join(folder_path, entry['filename'])
        if os.path.exists(src):
            os.remove(src)
            removed += 1
    if removed:
        print('Removed ' + str(removed) + ' original text files (now in .pyp)')

    # Clean up empty dirs
    for dirpath, dirnames, filenames in os.walk(folder_path, topdown=False):
        if dirpath == folder_path:
            continue
        if dirpath.startswith(os.path.join(folder_path, 'ARTIFACTS')):
            continue
        if dirpath.startswith(os.path.join(folder_path, 'INPUTS')):
            continue
        if dirpath.startswith(os.path.join(folder_path, 'OTHER')):
            continue
        try:
            if not os.listdir(dirpath):
                os.rmdir(dirpath)
        except:
            pass

    print()
    print('.pyp created successfully!')
    print('----------------------------')
    print('  1. ' + project_name + '.pyp')
    print('  2. ARTIFACTS/ (' + str(len(classified['artifacts'])) + ' files)')
    print('  3. INPUTS/ (' + str(len(classified['inputs'])) + ' files)')
    print('  4. OTHER/ (0 files)')
    print('----------------------------')
    return True


def main():
    parser = argparse.ArgumentParser(description='Create a .pyp skill container from a folder')
    parser.add_argument('folder', help='Path to the project folder')
    parser.add_argument('--name', '-n', help='Project name (default: folder name)')
    args = parser.parse_args()
    success = create_pyp(args.folder, args.name)
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()
