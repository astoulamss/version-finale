import os

workspace = r'c:\Users\hp\Documents\Ydays_2026'

# 1. BackButton.tsx
file = os.path.join(workspace, 'src/components/ui/BackButton.tsx')
with open(file, 'r', encoding='utf-8') as f: content = f.read()
content = content.replace('accessibilitylabel=', 'accessibilityLabel=')
with open(file, 'w', encoding='utf-8') as f: f.write(content)

# 2. AuthFlow.tsx
file = os.path.join(workspace, 'src/screens/AuthFlow.tsx')
with open(file, 'r', encoding='utf-8') as f: content = f.read()
content = content.replace('t(\'auth.create_account\')', '"Créer mon compte"')
with open(file, 'w', encoding='utf-8') as f: f.write(content)

# 3. HomeScreen.tsx
file = os.path.join(workspace, 'src/screens/HomeScreen.tsx')
with open(file, 'r', encoding='utf-8') as f: content = f.read()
content = content.replace('tone = theme.yellow;', 'tone = "#EAB308";')
content = content.replace('tone = theme.blue;', 'tone = "#3B82F6";')
with open(file, 'w', encoding='utf-8') as f: f.write(content)

# 4. ManagerScreens.tsx
file = os.path.join(workspace, 'src/screens/ManagerScreens.tsx')
with open(file, 'r', encoding='utf-8') as f: content = f.read()
content = content.replace('setShowStatusFilterDropdown(!showStatusFilterDropdown)', 'console.log("clicked")')
with open(file, 'w', encoding='utf-8') as f: f.write(content)

# 5. ProfileScreen.tsx
file = os.path.join(workspace, 'src/screens/ProfileScreen.tsx')
with open(file, 'r', encoding='utf-8') as f: content = f.read()
content = content.replace('selectedLanguage === \'fr\' ? t(\'settings.language_fr\') : t(\'settings.language_en\')', '"Français"')
content = content.replace('selectedLanguage === \'fr\' ? t("settings.language_fr") : t("settings.language_en")', '"Français"')
content = content.replace('selectedLanguage === "fr" ? "Français" : "Anglais"', '"Français"')
with open(file, 'w', encoding='utf-8') as f: f.write(content)
