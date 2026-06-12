#!/usr/bin/env python3
"""
.pyp Packager -- compiles .pyp projects into standalone executables.

Usage:
    python pyp_packager.py <project.pyp> [options]
    python pyp_packager.py --all <folder-with-pyp-files>

Requires: PyInstaller (pip install PyInstaller)

Output:
    ./dist/<ProjectName>/
      +-- <ProjectName>.exe          # Windows executable
      +-- <ProjectName>-setup.exe    # Inno Setup installer (Windows only)
      +-- build.sh                   # macOS/Linux build command
      +-- <ProjectName>.spec         # PyInstaller spec file
"""

import os
import sys
import json
import shutil
import subprocess
import argparse
import tempfile
from datetime import datetime


def find_pyinstaller():
    """Locate the PyInstaller executable."""
    candidates = [
        'pyinstaller',
        'pyinstaller.exe',
        os.path.join(os.path.dirname(sys.executable), 'Scripts', 'pyinstaller'),
        os.path.join(os.path.dirname(sys.executable), 'Scripts', 'pyinstaller.exe'),
    ]
    for c in candidates:
        try:
            result = subprocess.run([c, '--version'], capture_output=True, text=True, timeout=10)
            if result.returncode == 0:
                return c
        except:
            pass
    return None


def load_pyp(pyp_path):
    """Load and validate a .pyp file."""
    with open(pyp_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    required = ['projectName', 'mainEntry', 'pyFiles']
    for key in required:
        if key not in data:
            raise ValueError(f"Missing required field '{key}' in .pyp file")
    return data


def extract_to_temp(pyp_data, temp_dir):
    """Extract all files from .pyp to a temporary directory."""
    categories = {
        'pyFiles': '.py',
        'htmlFiles': '.html',
        'mdFiles': '.md',
        'txtFiles': '.txt',
        'prdFiles': '.prd',
    }

    extracted = []
    for cat, ext in categories.items():
        for entry in pyp_data.get(cat, []):
            filepath = entry['filename']
            content = entry['content']
            full_path = os.path.join(temp_dir, filepath)
            os.makedirs(os.path.dirname(full_path), exist_ok=True)
            with open(full_path, 'w', encoding='utf-8') as f:
                f.write(content)
            extracted.append(filepath)

    # Create ARTIFACTS directory placeholder
    artifacts_dir = os.path.join(temp_dir, 'ARTIFACTS')
    os.makedirs(artifacts_dir, exist_ok=True)
    for artifact in pyp_data.get('artifacts', []):
        full_path = os.path.join(temp_dir, 'ARTIFACTS', artifact)
        os.makedirs(os.path.dirname(full_path), exist_ok=True)
        open(full_path, 'w').close()  # placeholder

    return extracted


def create_web_launcher(temp_dir, pyp_data):
    """Create a Python launcher script for web projects."""
    main_entry = pyp_data['mainEntry']
    project_name = pyp_data['projectName']

    launcher_code = '''\"\"\"
{project_name} -- .pyp Self-Contained Launcher
Starts a local HTTP server and opens the browser.
\"\"\"
import http.server
import socketserver
import webbrowser
import threading
import os
import sys
import inspect

def get_data_dir():
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))

DIR = get_data_dir()
PORT = 8657

class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=DIR, **kwargs)

def start_server():
    with socketserver.TCPServer(("", PORT), Handler) as httpd:
        sys.stderr.write("Server at http://localhost:" + str(PORT) + "\\n")
        httpd.serve_forever()

def main():
    t = threading.Thread(target=start_server, daemon=True)
    t.start()
    webbrowser.open("http://localhost:" + str(PORT) + "/{main_entry}")
    try:
        t.join()
    except KeyboardInterrupt:
        pass

if __name__ == '__main__':
    main()
'''.replace('{project_name}', project_name).replace('{main_entry}', main_entry)

    launcher_path = os.path.join(temp_dir, '_pyp_launcher.py')
    with open(launcher_path, 'w', encoding='utf-8') as f:
        f.write(launcher_code)
    return launcher_path


def create_cli_launcher(temp_dir, pyp_data):
    """Create a CLI launcher that passes args to the main entry."""
    main_entry = pyp_data['mainEntry']
    project_name = pyp_data['projectName']
    required_args = pyp_data.get('requiredArgs', [])

    launcher_code = '''"""
{project_name} CLI -- .pyp Self-Contained Executable
"""
import sys
import os
import json

DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(DIR, 'python_files'))

def main():
    # Add the extracted directory to path
    sys.path.insert(0, DIR)
    
    # Import and run the main entry
    main_module = __import__('{main_entry_module}')
    
    if hasattr(main_module, 'main'):
        sys.exit(main_module.main())
    elif hasattr(main_module, 'cli'):
        sys.exit(main_module.cli())
    else:
        import runpy
        runpy.run_path(os.path.join(DIR, '{main_entry}'))

if __name__ == '__main__':
    main()
'''.replace('{project_name}', project_name).replace('{main_entry_module}', main_entry.replace('.py', ''))

    launcher_path = os.path.join(temp_dir, '_pyp_launcher.py')
    with open(launcher_path, 'w', encoding='utf-8') as f:
        f.write(launcher_code)
    return launcher_path


def build_with_pyinstaller(pyp_data, temp_dir, output_dir, pyinstaller_path):
    """Run PyInstaller to build the executable."""
    project_name = pyp_data['projectName']
    is_web = pyp_data.get('isWebProject', False)

    STD_LIBS = {
        'os', 'sys', 'json', 'time', 're', 'math', 'io', 'pathlib',
        'shutil', 'subprocess', 'tempfile', 'threading', 'datetime',
        'collections', 'functools', 'itertools', 'typing', 'abc',
        'copy', 'random', 'hashlib', 'base64', 'textwrap', 'pprint',
        'logging', 'warnings', 'inspect', 'glob', 'argparse', 'csv',
        'configparser', 'sqlite3', 'xml', 'socket', 'http', 'urllib',
        'email', 'string', 'struct', 'enum', 'dataclasses', 'statistics',
        'decimal', 'fractions', 'numbers', 'operator', 'sched', 'signal',
        'socketserver', 'webbrowser', '__future__',
    }

    if is_web:
        launcher = create_web_launcher(temp_dir, pyp_data)
    else:
        launcher = create_cli_launcher(temp_dir, pyp_data)

    # Collect all data files (HTML, MD, etc.)
    data_files = []
    categories_files = {
        'htmlFiles': '.html',
        'mdFiles': '.md',
        'txtFiles': '.txt',
        'prdFiles': '.prd',
    }

    for cat, ext in categories_files.items():
        for entry in pyp_data.get(cat, []):
            data_files.append(entry['filename'])

    # Build hidden imports from the Python files (only for CLI, not web)
    hidden_imports = set()
    if not is_web:
        for entry in pyp_data.get('pyFiles', []):
            content = entry['content']
            for line in content.split('\n'):
                line = line.strip()
                if line.startswith('import ') and '#' not in line:
                    parts = line.split()
                    if len(parts) > 1:
                        mod = parts[1].split('.')[0]
                        if mod not in STD_LIBS:
                            hidden_imports.add(mod)
                elif line.startswith('from ') and 'import' in line:
                    mod = line.split()[1].split('.')[0]
                    if mod not in STD_LIBS:
                        hidden_imports.add(mod)

    if hidden_imports:
        print('Hidden imports: ' + str(sorted(hidden_imports)))

    # Build the PyInstaller command
    build_dir = os.path.join(temp_dir, 'build_' + project_name)
    dist_dir = os.path.join(temp_dir, 'dist_' + project_name)

    cmd = [
        pyinstaller_path,
        '--onefile',
        '--name', project_name,
        '--distpath', dist_dir,
        '--workpath', build_dir,
        '--specpath', temp_dir,
        '--add-data', launcher + ';.',
    ]

    # Write setup script if present
    setup_script = pyp_data.get('setupScript')
    if setup_script:
        setup_path = os.path.join(temp_dir, 'setup.sh')
        with open(setup_path, 'w', encoding='utf-8') as f:
            f.write(setup_script)
        cmd.extend(['--add-data', setup_path + ';.'])
        print('  Included setup.sh (' + str(len(setup_script)) + ' chars)')

    # Add data files
    for df in data_files:
        src = os.path.join(temp_dir, df)
        if os.path.exists(src):
            cmd.extend(['--add-data', src + ';.'])

    # Add all Python files to the bundle
    for entry in pyp_data.get('pyFiles', []):
        src = os.path.join(temp_dir, entry['filename'])
        if os.path.exists(src):
            cmd.extend(['--add-data', src + ';.'])

    # Add hidden imports
    for imp in sorted(hidden_imports):
        cmd.extend(['--hidden-import', imp])

    # PyInstaller options
    cmd.extend([
        '--clean',
        '--noconfirm',
        '--log-level', 'WARN',
    ])

    if is_web:
        cmd.append('--noconsole')  # no console for web apps
        cmd.append(launcher)
    else:
        # Find the actual main Python file
        main_path = os.path.join(temp_dir, pyp_data['mainEntry'])
        if os.path.exists(main_path):
            cmd.append(main_path)
        else:
            cmd.append(launcher)

    print()
    print('Running PyInstaller...')
    print('  Command: pyinstaller ' + ' '.join(cmd[1:6]) + ' ...')
    print()

    result = subprocess.run(cmd, capture_output=True, text=True, timeout=900)
    
    if result.returncode != 0:
        print('PyInstaller build failed:')
        print(result.stdout[-2000:] if len(result.stdout) > 2000 else result.stdout)
        print(result.stderr[-2000:] if len(result.stderr) > 2000 else result.stderr)
        return None

    # Find the built executable
    built_exe = None
    for root, dirs, files in os.walk(dist_dir):
        for f in files:
            if f.endswith('.exe'):
                built_exe = os.path.join(root, f)
                break
    return built_exe


def create_inno_setup_script(pyp_data, output_dir, exe_path):
    """Create an Inno Setup .iss script for Windows installer."""
    project_name = pyp_data['projectName']
    main_entry = pyp_data['mainEntry']
    is_web = pyp_data.get('isWebProject', False)

    script = '''; Inno Setup Script for {project_name}
; Generated by .pyp Packager on {date}

[Setup]
AppName={project_name}
AppVersion=1.0.0
DefaultDirName={{autopf}}\\{project_name}
DefaultGroupName={project_name}
UninstallDisplayIcon={{app}}\\{project_name}.exe
Compression=lzma2
SolidCompression=yes
OutputDir={output_dir}
OutputBaseFilename={project_name}-setup

[Files]
Source: "{exe_path}"; DestDir: "{{app}}"; Flags: ignoreversion

[Icons]
Name: "{{groupprogram}}\\{project_name}"; Filename: "{{app}}\\{project_name}.exe"
'''.format(
        project_name=project_name,
        date=datetime.now().strftime('%Y-%m-%d'),
        output_dir=output_dir,
        exe_path=exe_path.replace('\\', '\\\\'),
        main_entry=main_entry,
    )

    if is_web:
        script += '''
[Run]
Filename: "{app}\\"' + project_name + '.exe"; Description: "Launch {project_name}"; Flags: nowait postinstall skipifsilent
'''

    iss_path = os.path.join(output_dir, project_name + '.iss')
    with open(iss_path, 'w', encoding='utf-8') as f:
        f.write(script)
    return iss_path


def create_cross_platform_scripts(pyp_data, output_dir):
    """Create build scripts for macOS and Linux."""
    project_name = pyp_data['projectName']

    # macOS build script
    mac_script = '''#!/bin/bash
# Build script for macOS -- {project_name}
# Run this on a Mac with Python 3 + PyInstaller installed

DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$DIR"

# Extract and build
python3 -c "
import json, os, sys
sys.path.insert(0, '.')
from pyp_packager import load_pyp, extract_to_temp, build_with_pyinstaller, create_inno_setup_script
import tempfile

pyp_path = '{project_name}.pyp'
data = load_pyp(pyp_path)
tmp = tempfile.mkdtemp()
extract_to_temp(data, tmp)

# macOS build
import subprocess
result = subprocess.run(['pyinstaller', '--onefile', '--name', '{project_name}',
    '--add-data', '...', '.', '{project_name}.py'], capture_output=True, text=True)
print(result.stdout)
"
'''.format(project_name=project_name)

    mac_path = os.path.join(output_dir, 'build_macos.sh')
    with open(mac_path, 'w', encoding='utf-8') as f:
        f.write(mac_script)
    os.chmod(mac_path, 0o755)

    # Linux build script
    linux_script = '''#!/bin/bash
# Build script for Linux -- {project_name}
# Run this on a Linux machine with Python 3 + PyInstaller installed

DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$DIR"

python3 -c "
import json, os, sys
sys.path.insert(0, '.')
from pyp_packager import load_pyp, extract_to_temp, build_with_pyinstaller
import tempfile

pyp_path = '{project_name}.pyp'
data = load_pyp(pyp_path)
tmp = tempfile.mkdtemp()
extract_to_temp(data, tmp)

import subprocess
result = subprocess.run(['pyinstaller', '--onefile', '--name', '{project_name}',
    '--add-data', '...', '.', '{project_name}.py'], capture_output=True, text=True)
print(result.stdout)
"
'''.format(project_name=project_name)

    linux_path = os.path.join(output_dir, 'build_linux.sh')
    with open(linux_path, 'w', encoding='utf-8') as f:
        f.write(linux_script)
    os.chmod(linux_path, 0o755)

    return [mac_path, linux_path]


def package_pyp(pyp_path, output_dir=None, no_build=False):
    """Main packaging function."""
    pyp_path = os.path.abspath(pyp_path)
    if not os.path.exists(pyp_path):
        print("Error: .pyp file not found: " + pyp_path)
        return False

    print()
    print('[.] Loading .pyp: ' + os.path.basename(pyp_path))

    pyp_data = load_pyp(pyp_path)
    project_name = pyp_data['projectName']
    is_web = pyp_data.get('isWebProject', False)

    print('  Project: ' + project_name)
    print('  Type: ' + ('Web' if is_web else 'CLI'))
    print('  Files: ' + str(len(pyp_data.get('pyFiles', []))) + ' py, ' +
          str(len(pyp_data.get('htmlFiles', []))) + ' html, ' +
          str(len(pyp_data.get('mdFiles', []))) + ' md')

    if not output_dir:
        output_dir = os.path.join(os.path.dirname(pyp_path), 'dist_' + project_name)

    os.makedirs(output_dir, exist_ok=True)

    # Create temp extraction
    temp_dir = tempfile.mkdtemp(prefix='pyp_build_')
    try:
        extracted = extract_to_temp(pyp_data, temp_dir)
        print('  Extracted ' + str(len(extracted)) + ' files to temp')

        if no_build:
            print()
            print('  --no-build specified, skipping PyInstaller')
            print('  Extracted files at: ' + temp_dir)
            print('  Output directory: ' + output_dir)
            return True

        # Find PyInstaller
        pyinstaller_path = find_pyinstaller()
        if not pyinstaller_path:
            print()
            print('Error: PyInstaller not found. Install with:')
            print('  pip install PyInstaller')
            print()
            print('Extracted files at: ' + temp_dir)
            return False

        print('  PyInstaller: ' + pyinstaller_path)

        # Build
        exe_path = build_with_pyinstaller(pyp_data, temp_dir, output_dir, pyinstaller_path)

        if exe_path:
            exe_size = os.path.getsize(exe_path) / (1024 * 1024)
            print('  Built: ' + os.path.basename(exe_path) + ' (' + str(round(exe_size, 1)) + ' MB)')
            shutil.copy2(exe_path, output_dir)
        else:
            print('  Build failed, check output above')
            return False

        # Copy .pyp to output
        shutil.copy2(pyp_path, output_dir)

        # Create Inno Setup script
        if exe_path:
            iss_path = create_inno_setup_script(pyp_data, output_dir, exe_path)
            print('  Installer script: ' + os.path.basename(iss_path))

        # Create cross-platform scripts
        scripts = create_cross_platform_scripts(pyp_data, output_dir)
        print('  Cross-platform scripts created')

        # Write build summary
        summary_path = os.path.join(output_dir, 'BUILD_INFO.txt')
        with open(summary_path, 'w', encoding='utf-8') as f:
            f.write('Build Summary for ' + project_name + '\n')
            f.write('Generated: ' + datetime.now().isoformat() + '\n')
            f.write('Source: ' + os.path.basename(pyp_path) + '\n')
            f.write('Type: ' + ('Web' if is_web else 'CLI') + '\n')
            f.write('Platform: Windows (PyInstaller ' + pyinstaller_path + ')\n')
            f.write('\nTo build for macOS/Linux, run the respective build_*.sh script on that platform.\n')
            f.write('To create Windows installer, compile ' + project_name + '.iss with Inno Setup.\n')

        print()
        print('Output: ' + output_dir)
        print('  +-- ' + project_name + '.exe (' + str(round(exe_size, 1)) + ' MB)')
        print('  +-- ' + project_name + '.iss (Inno Setup)')
        print('  +-- ' + project_name + '.pyp')
        print('  +-- build_macos.sh / build_linux.sh')
        print('  +-- BUILD_INFO.txt')
        print()
        print('.pyp packaged successfully!')
        print()

        return True

    finally:
        # Clean up temp dir
        try:
            shutil.rmtree(temp_dir)
        except:
            pass


def main():
    parser = argparse.ArgumentParser(description='Package .pyp projects as standalone executables')
    parser.add_argument('pyp_file', help='Path to .pyp file')
    parser.add_argument('--output', '-o', help='Output directory (default: ./dist_<ProjectName>)')
    parser.add_argument('--no-build', action='store_true', help='Extract only, skip PyInstaller build')
    args = parser.parse_args()

    success = package_pyp(args.pyp_file, args.output, args.no_build)
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()
