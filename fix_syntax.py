import os
import re
path = r'C:\Users\91999\Desktop\final project\templates\bands\explore.html'
with open(path, 'r', encoding='utf-8') as f:
    text = f.read()

# Fix unspaced operators
text = re.sub(r'request\.GET\.event_type==\'([^\']+)\'', r"request.GET.event_type == '\1'", text)
text = re.sub(r'request\.GET\.genre==\'([^\']+)\'', r"request.GET.genre == '\1'", text)

with open(path, 'w', encoding='utf-8') as f:
    f.write(text)
print("Django template space syntax fixes applied to explore.html")
