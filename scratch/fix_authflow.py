import os

workspace = r'c:\Users\hp\Documents\Ydays_2026'
file = os.path.join(workspace, 'src/screens/AuthFlow.tsx')
with open(file, 'r', encoding='utf-8') as f: content = f.read()

content = content.replace('useEffec"Connexion"', 'useEffect(')
content = content.replace('Easing.ou"Connexion"', 'Easing.out(')
content = content.replace('loop.star"Connexion"', 'loop.start(')
content = content.replace('Objec"Connexion"', 'Object(')
content = content.replace('preventDefaul"Connexion"', 'preventDefault(')
content = content.replace('se"Connexion"', 'set(')
content = content.replace('aler"Connexion"', 'alert(')
content = content.replace('tes"Connexion"', 'test(')
content = content.replace('Reac"Connexion"', 'React(')
content = content.replace('ge"Connexion"', 'get(')
content = content.replace('wai"Connexion"', 'wait(')
content = content.replace('tex"Connexion"', 'text(')
content = content.replace('nex"Connexion"', 'next(')
content = content.replace('lis"Connexion"', 'list(')
content = content.replace('ini"Connexion"', 'init(')
content = content.replace('pos"Connexion"', 'post(')
content = content.replace('defaul"Connexion"', 'default(')

with open(file, 'w', encoding='utf-8') as f: f.write(content)
