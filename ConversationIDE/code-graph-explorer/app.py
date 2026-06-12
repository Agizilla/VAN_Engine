#!/usr/bin/env python3
import ast
import json
import sys
import os
import tempfile
import subprocess
import shutil
import importlib.util
from pathlib import Path
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import traceback

app = Flask(__name__, static_folder='.')
CORS(app)

# ----------------------------------------------------------------------
# 1. AST Parsing
# ----------------------------------------------------------------------
class FunctionCollector(ast.NodeVisitor):
    def __init__(self):
        self.functions = {}
        self.imports = set()
        self._current_func = None

    def visit_FunctionDef(self, node):
        params = [arg.arg for arg in node.args.args]
        old = self._current_func
        self._current_func = node.name
        self.functions[node.name] = {
            'params': params,
            'line': node.lineno,
            'calls': set(),
            'docstring': ast.get_docstring(node) or ''
        }
        self.generic_visit(node)
        self._current_func = old

    def visit_Call(self, node):
        if isinstance(node.func, ast.Name) and self._current_func:
            self.functions[self._current_func]['calls'].add(node.func.id)
        self.generic_visit(node)

    def visit_Import(self, node):
        for alias in node.names:
            self.imports.add(alias.name.split('.')[0])

    def visit_ImportFrom(self, node):
        module = node.module or ''
        self.imports.add(module.split('.')[0])

def parse_python_file(content):
    try:
        tree = ast.parse(content)
        collector = FunctionCollector()
        collector.visit(tree)
        for name, info in collector.functions.items():
            info['calls'] = list(info['calls'])
        return {'functions': collector.functions, 'imports': list(collector.imports)}, None
    except SyntaxError as e:
        return None, str(e)

# ----------------------------------------------------------------------
# 2. Sandboxed execution with tracing
# ----------------------------------------------------------------------
TRACE_TEMPLATE = r'''
import sys, json, importlib.util
trace_events = []
def trace_calls(frame, event, arg):
    trace_events.append({"type": event, "name": frame.f_code.co_name, "line": frame.f_lineno})
    return trace_calls
sys.settrace(trace_calls)
module_name = "user_module"
spec = importlib.util.spec_from_file_location(module_name, SCRIPT_PATH)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
args = json.loads(ARGS_JSON)
result = getattr(module, FUNC_NAME)(*args)
try:
    result_str = json.dumps(result)
except:
    result_str = repr(result)
output = {"result": result_str, "trace": trace_events}
print(json.dumps(output))
'''

def run_with_trace(script_path, function_name, args, timeout_sec=5):
    script = TRACE_TEMPLATE.replace('SCRIPT_PATH', json.dumps(script_path))
    script = script.replace('FUNC_NAME', json.dumps(function_name))
    script = script.replace('ARGS_JSON', json.dumps(json.dumps(args)))

    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False, encoding='utf-8') as f:
        f.write(script)
        wrapper_path = f.name

    try:
        env = os.environ.copy()
        env['PYTHONPATH'] = os.path.dirname(script_path)
        proc = subprocess.run(
            [sys.executable, wrapper_path],
            capture_output=True, text=True, timeout=timeout_sec, env=env
        )
        if proc.returncode != 0:
            return None, f"Execution error: {proc.stderr or proc.stdout}"
        lines = proc.stdout.strip().split('\n')
        output = json.loads(lines[-1])
        return output, None
    except subprocess.TimeoutExpired:
        return None, f"Timeout ({timeout_sec}s)"
    except Exception as e:
        return None, str(e)
    finally:
        os.unlink(wrapper_path)

# ----------------------------------------------------------------------
# 3. Routes
# ----------------------------------------------------------------------
UPLOADS = {}

@app.route('/')
def index():
    return send_from_directory('.', 'explorer.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400
    if not file.filename.endswith('.py'):
        return jsonify({'error': 'Only .py files allowed'}), 400
    content = file.read().decode('utf-8')
    graph, error = parse_python_file(content)
    if error:
        return jsonify({'error': f'Parse error: {error}'}), 400
    temp_dir = tempfile.mkdtemp()
    temp_path = os.path.join(temp_dir, file.filename)
    with open(temp_path, 'w', encoding='utf-8') as f:
        f.write(content)
    session_id = str(hash(content + str(os.urandom(8))))
    UPLOADS[session_id] = temp_path
    return jsonify({'graph': graph, 'session_id': session_id})

@app.route('/execute', methods=['POST'])
def execute():
    data = request.json
    session_id = data.get('session_id')
    function_name = data.get('function_name')
    args = data.get('args', [])
    if not session_id or not function_name:
        return jsonify({'error': 'Missing session_id or function_name'}), 400
    temp_path = UPLOADS.get(session_id)
    if not temp_path or not os.path.exists(temp_path):
        return jsonify({'error': 'Session expired or file not found'}), 400
    result, error = run_with_trace(temp_path, function_name, args)
    if error:
        return jsonify({'error': error}), 500
    return jsonify(result)

@app.route('/cleanup', methods=['POST'])
def cleanup():
    data = request.json
    session_id = data.get('session_id')
    temp_path = UPLOADS.pop(session_id, None)
    if temp_path and os.path.exists(temp_path):
        shutil.rmtree(os.path.dirname(temp_path))
    return jsonify({'status': 'ok'})

if __name__ == '__main__':
    app.run(debug=True, port=5001)
