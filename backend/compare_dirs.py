import os

dir1 = r"c:\Users\hp\Documents\Ydays_2026\temp_ydays\ydays"
dir2 = r"c:\Users\hp\Documents\Ydays_2026\backend"

def get_clean_content(filepath):
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return [line.rstrip().replace('\r', '') for line in f]
    except Exception:
        # Binary file or encoding issue, fall back to binary
        with open(filepath, 'rb') as f:
            return f.read()

def compare_folders(d1, d2):
    diff_files = []
    only_d1 = []
    only_d2 = []
    
    ignore_dirs = {".git", "venv", "__pycache__"}
    ignore_files = {".env", "ydays.db", "rh_app.db", "compare_dirs.py"}
    
    for root, dirs, files in os.walk(d1):
        dirs[:] = [d for d in dirs if d not in ignore_dirs]
        rel_path = os.path.relpath(root, d1)
        if rel_path == ".":
            rel_path = ""
            
        target_dir = os.path.join(d2, rel_path)
        
        # Check files
        for f in files:
            if f in ignore_files:
                continue
            rel_f = os.path.join(rel_path, f) if rel_path else f
            
            f1 = os.path.join(root, f)
            f2 = os.path.join(target_dir, f)
            
            if not os.path.exists(f2):
                only_d1.append(rel_f)
            else:
                c1 = get_clean_content(f1)
                c2 = get_clean_content(f2)
                if c1 != c2:
                    diff_files.append(rel_f)
                    
    for root, dirs, files in os.walk(d2):
        dirs[:] = [d for d in dirs if d not in ignore_dirs]
        rel_path = os.path.relpath(root, d2)
        if rel_path == ".":
            rel_path = ""
            
        source_dir = os.path.join(d1, rel_path)
        
        # Check files
        for f in files:
            if f in ignore_files:
                continue
            rel_f = os.path.join(rel_path, f) if rel_path else f
            f1 = os.path.join(source_dir, f)
            if not os.path.exists(f1):
                only_d2.append(rel_f)
                
    return sorted(only_d1), sorted(only_d2), sorted(diff_files)

only_d1, only_d2, diff_files = compare_folders(dir1, dir2)

print("=== Files only in remote ===")
for f in only_d1:
    print(f)
    
print("\n=== Files only in local ===")
for f in only_d2:
    print(f)
    
print("\n=== Files that differ ===")
for f in diff_files:
    print(f)
