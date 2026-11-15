with open('scripts/validate_m5_final_pair.py', 'rb') as f:
    content = f.read().decode('utf-8')

replacements = {
    'λ': 'lam',
    'Δ': 'd',
    'µ': 'u',
    '°': ' deg',
    '≤': '<=',
    '≥': '>=',
    '—': '-',
    '–': '-',
    '’': "'",
    '“': '"',
    '”': '"',
}
for k, v in replacements.items():
    content = content.replace(k, v)

content_ascii = content.encode('ascii', errors='ignore').decode('ascii')
with open('scripts/validate_m5_final_pair.py', 'w', encoding='ascii') as f:
    f.write(content_ascii)
print('Successfully cleaned validate_m5_final_pair.py to ASCII')
