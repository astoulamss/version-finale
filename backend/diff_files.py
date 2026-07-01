import difflib

file1 = r"c:\Users\hp\Documents\Ydays_2026\temp_ydays\ydays\api\team_risks.py"
file2 = r"c:\Users\hp\Documents\Ydays_2026\backend\api\team_risks.py"

with open(file1, 'r', encoding='utf-8') as f:
    lines1 = [line.rstrip().replace('\r', '') for line in f]
    
with open(file2, 'r', encoding='utf-8') as f:
    lines2 = [line.rstrip().replace('\r', '') for line in f]
    
diff = difflib.unified_diff(lines1, lines2, fromfile='remote', tofile='local')
print('\n'.join(diff))
