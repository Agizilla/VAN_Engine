import json, sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

d = json.load(open(r'C:\Users\User\Documents\!Claude\ClaudeHipHopperList\ClaudeHipHopperList.pyp', encoding='utf-8'))

for key in ['mdFiles','pyFiles','htmlFiles','txtFiles','prdFiles']:
    for f in d.get(key, []):
        lines = f['content'].count('\n') + 1
        print(f'=== {key}: {f["filename"]} ({lines} lines) ===')
        if lines > 100:
            print(f['content'][:3000])
            print(f'... ({lines} lines total, truncated)')
        else:
            print(f['content'])
        print()
