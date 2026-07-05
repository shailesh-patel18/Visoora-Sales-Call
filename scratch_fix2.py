import re
import os

files_to_fix = [
    ('frontend/app/login/page.tsx', 'export default function LoginPage()', 'function LoginContent()', 'LoginPage'),
    ('frontend/app/signup/page.tsx', 'export default function SignupPage()', 'function SignupContent()', 'SignupPage')
]

for filepath, search_str, replace_str, component_name in files_to_fix:
    if not os.path.exists(filepath):
        continue
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    # Change component name
    content = content.replace(search_str, replace_str)
    
    # Add Suspense import if missing
    if 'Suspense' not in content:
        content = content.replace('import React, { useState', 'import React, { useState, Suspense')
        content = content.replace('import React, { FormEvent, useState', 'import React, { FormEvent, useState, Suspense')

    # Append wrapper
    wrapper = f"""
export default function {component_name}() {{
  return (
    <Suspense fallback={{<div className="min-h-screen bg-black flex items-center justify-center text-white">Loading...</div>}}>
      <{replace_str.replace('function ', '').replace('()', '')} />
    </Suspense>
  );
}}
"""
    content += wrapper

    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)
