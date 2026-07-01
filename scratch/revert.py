import os
import glob
import re
import json

workspace = r'c:\Users\hp\Documents\Ydays_2026'
fr_json_path = os.path.join(workspace, 'src', 'i18n', 'fr.json')

with open(fr_json_path, 'r', encoding='utf-8') as f:
    fr_data = json.load(f)
    
auto_dict = fr_data.get('auto', {})

def restore_file(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
        
    original = content
        
    def repl_jsx_text(m):
        key = m.group(1)
        if key in auto_dict:
            return f'>{auto_dict[key]}</Text>'
        return m.group(0)
        
    content = re.sub(r'>\{t\(\"auto\.([^\"]+)\"\)\}</Text>', repl_jsx_text, content)
    content = re.sub(r'>\{\s*t\(\"auto\.([^\"]+)\"\)\s*\}</Text>', repl_jsx_text, content)
    
    def repl_jsx_prop(m):
        prop = m.group(1)
        key = m.group(2)
        if key in auto_dict:
            return f'{prop}=\"{auto_dict[key]}\"'
        return m.group(0)
        
    content = re.sub(r'([a-zA-Z0-9_]+)=\{\s*t\(\"auto\.([^\"]+)\"\)\s*\}', repl_jsx_prop, content)
    
    content = re.sub(r'\s*const\s*\{\s*t\s*\}\s*=\s*useLanguage\(\)\s*;', '', content)
    
    if content != original:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        return True
    return False

modified = 0
for filepath in glob.glob(os.path.join(workspace, 'src', '**', '*.tsx'), recursive=True):
    if restore_file(filepath):
        modified += 1

print(f'Restored {modified} files.')
