import json
import os

with open('../Portable_Cognitive_Graph.ipynb', 'r', encoding='utf-8') as f:
    nb = json.load(f)

for cell in nb['cells']:
    if cell['cell_type'] == 'code':
        source = cell['source']
        if not source:
            continue
        first_line = source[0]
        if first_line.startswith('%%writefile'):
            parts = first_line.strip().split()
            append = False
            filename = None
            if len(parts) >= 3 and parts[1] == '-a':
                filename = parts[2]
                append = True
            elif len(parts) >= 2:
                filename = parts[1]
            
            if filename:
                # remove any leading slashes or . if it's there? The cells use 'pcg/__init__.py' or 'requirements.txt'
                os.makedirs(os.path.dirname(filename) or '.', exist_ok=True)
                mode = 'a' if append else 'w'
                with open(filename, mode, encoding='utf-8') as f_out:
                    f_out.write("".join(source[1:]))

print("Extraction complete.")
