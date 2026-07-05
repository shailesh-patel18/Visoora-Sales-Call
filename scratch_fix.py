import re
f = open('frontend/app/activation/page.tsx', 'r', encoding='utf-8')
content = f.read()
f.close()

content = content.replace('export default function ActivationPage()', 'function ActivationContent()')
content = content.replace('import React, { useEffect, useState } from "react";', 'import React, { useEffect, useState, Suspense } from "react";')
content += '\nexport default function ActivationPage() {\n  return (\n    <Suspense fallback={<div className="min-h-screen bg-[hsl(var(--surface-0))] flex items-center justify-center text-white">Loading...</div>}>\n      <ActivationContent />\n    </Suspense>\n  );\n}\n'

f = open('frontend/app/activation/page.tsx', 'w', encoding='utf-8')
f.write(content)
f.close()
