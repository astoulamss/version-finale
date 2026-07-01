import os
import re

workspace = r'c:\Users\hp\Documents\Ydays_2026'

# AuthFlow.tsx
file = os.path.join(workspace, 'src/screens/AuthFlow.tsx')
with open(file, 'r', encoding='utf-8') as f: content = f.read()
content = re.sub(r't\([^)]*\)', '"Connexion"', content)
with open(file, 'w', encoding='utf-8') as f: f.write(content)

# ProfileScreen.tsx
file = os.path.join(workspace, 'src/screens/ProfileScreen.tsx')
with open(file, 'r', encoding='utf-8') as f: content = f.read()
content = content.replace('selectedLanguage === "fr" ? "Français" : "Anglais"', '"Français"')
content = content.replace('"Français" ? "Français" : "Français"', '"Français"')
# If there are any Truthy expressions like `"Français" ? ...` fix them
content = re.sub(r'\"Français\"\s*\?\s*\"Français\"\s*:\s*\"[^\"]*\"', '"Français"', content)
with open(file, 'w', encoding='utf-8') as f: f.write(content)
