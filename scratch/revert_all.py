import os
import glob
import re
import json

workspace = r'c:\Users\hp\Documents\Ydays_2026'
fr_json_path = os.path.join(workspace, 'src', 'i18n', 'fr.json')

with open(fr_json_path, 'r', encoding='utf-8') as f:
    fr_data = json.load(f)
    
def get_translation(key_path):
    keys = key_path.split('.')
    val = fr_data
    for k in keys:
        if isinstance(val, dict) and k in val:
            val = val[k]
        else:
            return None
    return val if isinstance(val, str) else None

def restore_file(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
        
    original = content
        
    def repl_jsx_text(m):
        key = m.group(1)
        val = get_translation(key)
        if val is not None:
            return f'>{val}</Text>'
        return m.group(0)
        
    # Replace >{t("xyz.abc")}</Text>
    content = re.sub(r'>\{\s*t\(\"([^\"]+)\"\)\s*\}</Text>', repl_jsx_text, content)
    
    def repl_jsx_prop(m):
        prop = m.group(1)
        key = m.group(2)
        val = get_translation(key)
        if val is not None:
            return f'{prop}=\"{val}\"'
        return m.group(0)
        
    # Replace prop={t("xyz.abc")}
    content = re.sub(r'([a-zA-Z0-9_]+)=\{\s*t\(\"([^\"]+)\"\)\s*\}', repl_jsx_prop, content)
    
    # Also handle standalone t("xyz") that are not in <Text> or props (e.g. inside a map or logic)
    def repl_standalone(m):
        key = m.group(1)
        val = get_translation(key)
        if val is not None:
            return f'\"{val}\"'
        return m.group(0)
        
    content = re.sub(r't\(\"([^\"]+)\"\)', repl_standalone, content)
    
    # Remove const { t } = useLanguage();
    content = re.sub(r'\s*const\s*\{\s*t\s*\}\s*=\s*useLanguage\(\)\s*;', '', content)
    content = re.sub(r'import\s*\{\s*useLanguage\s*\}\s*from\s*[\'"][^\'"]+LanguageContext[\'"]\s*;?', '', content)
    
    if content != original:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        return True
    return False

modified = 0
for filepath in glob.glob(os.path.join(workspace, 'src', '**', '*.tsx'), recursive=True):
    if restore_file(filepath):
        modified += 1

print(f'Fully Restored {modified} files.')
