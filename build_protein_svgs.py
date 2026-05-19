import os

def generate_amino_acid_svg():
    width = 400
    height = 300
    svg = []
    svg.append(f'<svg width="{width}" height="{height}" viewBox="0 0 {width} {height}" xmlns="http://www.w3.org/2000/svg">')
    svg.append('<defs>')
    svg.append('<linearGradient id="bg" x1="0%" y1="0%" x2="0%" y2="100%"><stop offset="0%" stop-color="#ffffff"/><stop offset="100%" stop-color="#f8fafc"/></linearGradient>')
    svg.append('<filter id="shadow" x="-20%" y="-20%" width="140%" height="140%"><feDropShadow dx="0" dy="4" stdDeviation="4" flood-color="#000" flood-opacity="0.1"/></filter>')
    svg.append('</defs>')
    
    svg.append(f'<rect width="{width}" height="{height}" rx="16" fill="url(#bg)" stroke="#e2e8f0" stroke-width="1"/>')
    svg.append('<text x="200" y="40" font-family="system-ui, sans-serif" font-size="20" font-weight="700" fill="#0f172a" text-anchor="middle">General Amino Acid Structure</text>')

    # Bonds
    svg.append('<line x1="200" y1="150" x2="100" y2="150" stroke="#94a3b8" stroke-width="4"/>') # to Amino
    svg.append('<line x1="200" y1="150" x2="300" y2="150" stroke="#94a3b8" stroke-width="4"/>') # to Carboxyl
    svg.append('<line x1="200" y1="150" x2="200" y2="70" stroke="#94a3b8" stroke-width="4"/>') # to Hydrogen
    svg.append('<line x1="200" y1="150" x2="200" y2="230" stroke="#94a3b8" stroke-width="4"/>') # to R-group

    # Atoms / Groups
    # Alpha Carbon
    svg.append('<circle cx="200" cy="150" r="24" fill="#475569" filter="url(#shadow)"/>')
    svg.append('<text x="200" y="156" font-family="system-ui, sans-serif" font-size="16" font-weight="700" fill="#ffffff" text-anchor="middle">Cα</text>')

    # Amino Group
    svg.append('<circle cx="100" cy="150" r="30" fill="#3b82f6" filter="url(#shadow)"/>')
    svg.append('<text x="100" y="156" font-family="system-ui, sans-serif" font-size="16" font-weight="700" fill="#ffffff" text-anchor="middle">NH3+</text>')
    svg.append('<text x="100" y="195" font-family="system-ui, sans-serif" font-size="12" font-weight="600" fill="#3b82f6" text-anchor="middle">Amino Group</text>')

    # Carboxyl Group
    svg.append('<circle cx="300" cy="150" r="30" fill="#ef4444" filter="url(#shadow)"/>')
    svg.append('<text x="300" y="156" font-family="system-ui, sans-serif" font-size="16" font-weight="700" fill="#ffffff" text-anchor="middle">COO-</text>')
    svg.append('<text x="300" y="195" font-family="system-ui, sans-serif" font-size="12" font-weight="600" fill="#ef4444" text-anchor="middle">Carboxyl Group</text>')

    # Hydrogen
    svg.append('<circle cx="200" cy="70" r="20" fill="#94a3b8" filter="url(#shadow)"/>')
    svg.append('<text x="200" y="76" font-family="system-ui, sans-serif" font-size="16" font-weight="700" fill="#ffffff" text-anchor="middle">H</text>')

    # R-group
    svg.append('<rect x="170" y="230" width="60" height="40" rx="8" fill="#10b981" filter="url(#shadow)"/>')
    svg.append('<text x="200" y="256" font-family="system-ui, sans-serif" font-size="18" font-weight="700" fill="#ffffff" text-anchor="middle">R</text>')
    svg.append('<text x="200" y="285" font-family="system-ui, sans-serif" font-size="12" font-weight="600" fill="#10b981" text-anchor="middle">Side Chain</text>')

    svg.append('</svg>')
    
    with open("static/images/protein-folding/amino-acid.svg", "w", encoding="utf-8") as f:
        f.write("\n".join(svg))

def generate_folding_levels_svg():
    width = 600
    height = 200
    svg = []
    svg.append(f'<svg width="{width}" height="{height}" viewBox="0 0 {width} {height}" xmlns="http://www.w3.org/2000/svg">')
    svg.append('<defs>')
    svg.append('<linearGradient id="bg" x1="0%" y1="0%" x2="0%" y2="100%"><stop offset="0%" stop-color="#ffffff"/><stop offset="100%" stop-color="#f8fafc"/></linearGradient>')
    svg.append('</defs>')
    svg.append(f'<rect width="{width}" height="{height}" rx="16" fill="url(#bg)" stroke="#e2e8f0" stroke-width="1"/>')

    # Primary
    svg.append('<g transform="translate(30, 80)">')
    for i in range(5):
        svg.append(f'<circle cx="{i*25 + 15}" cy="0" r="10" fill="#3b82f6" />')
        if i < 4:
            svg.append(f'<line x1="{i*25 + 25}" y1="0" x2="{i*25 + 40}" y2="0" stroke="#94a3b8" stroke-width="2"/>')
    svg.append('<text x="65" y="40" font-family="system-ui" font-size="14" font-weight="700" fill="#0f172a" text-anchor="middle">Primary</text>')
    svg.append('<text x="65" y="60" font-family="system-ui" font-size="12" fill="#64748b" text-anchor="middle">Sequence</text>')
    svg.append('</g>')

    svg.append('<line x1="180" y1="80" x2="200" y2="80" stroke="#cbd5e1" stroke-width="2" marker-end="url(#arrow)"/>')

    # Secondary
    svg.append('<g transform="translate(220, 80)">')
    svg.append('<path d="M0,0 Q15,-20 30,0 T60,0 T90,0 T120,0" fill="none" stroke="#10b981" stroke-width="6" stroke-linecap="round"/>')
    svg.append('<text x="60" y="40" font-family="system-ui" font-size="14" font-weight="700" fill="#0f172a" text-anchor="middle">Secondary</text>')
    svg.append('<text x="60" y="60" font-family="system-ui" font-size="12" fill="#64748b" text-anchor="middle">Helices / Sheets</text>')
    svg.append('</g>')

    svg.append('<line x1="360" y1="80" x2="380" y2="80" stroke="#cbd5e1" stroke-width="2" />')

    # Tertiary
    svg.append('<g transform="translate(420, 80)">')
    svg.append('<path d="M0,-10 C20,20 40,-30 60,0 S80,30 100,-10 S120,10 100,20 S80,-10 60,10 S30,20 10,0 Z" fill="none" stroke="#8b5cf6" stroke-width="6" stroke-linejoin="round"/>')
    svg.append('<text x="60" y="40" font-family="system-ui" font-size="14" font-weight="700" fill="#0f172a" text-anchor="middle">Tertiary</text>')
    svg.append('<text x="60" y="60" font-family="system-ui" font-size="12" fill="#64748b" text-anchor="middle">3D Fold</text>')
    svg.append('</g>')

    svg.append('</svg>')
    with open("static/images/protein-folding/folding-levels.svg", "w", encoding="utf-8") as f:
        f.write("\n".join(svg))

def generate_evoformer_svg():
    width = 500
    height = 350
    svg = []
    svg.append(f'<svg width="{width}" height="{height}" viewBox="0 0 {width} {height}" xmlns="http://www.w3.org/2000/svg">')
    svg.append('<defs>')
    svg.append('<linearGradient id="bg" x1="0%" y1="0%" x2="0%" y2="100%"><stop offset="0%" stop-color="#ffffff"/><stop offset="100%" stop-color="#f8fafc"/></linearGradient>')
    svg.append('</defs>')
    svg.append(f'<rect width="{width}" height="{height}" rx="16" fill="url(#bg)" stroke="#e2e8f0" stroke-width="1"/>')
    svg.append('<text x="250" y="40" font-family="system-ui" font-size="20" font-weight="700" fill="#0f172a" text-anchor="middle">Evoformer Block Architecture</text>')

    # MSA Track
    svg.append('<g transform="translate(50, 80)">')
    svg.append('<rect width="160" height="180" rx="8" fill="#eff6ff" stroke="#3b82f6" stroke-width="2"/>')
    svg.append('<text x="80" y="30" font-family="system-ui" font-size="16" font-weight="700" fill="#1d4ed8" text-anchor="middle">MSA Representation</text>')
    
    # Internal nodes for MSA
    svg.append('<rect x="20" y="50" width="120" height="30" rx="4" fill="#ffffff" stroke="#93c5fd" stroke-width="1"/>')
    svg.append('<text x="80" y="70" font-family="system-ui" font-size="12" fill="#1e3a8a" text-anchor="middle">Row Attention</text>')
    
    svg.append('<rect x="20" y="90" width="120" height="30" rx="4" fill="#ffffff" stroke="#93c5fd" stroke-width="1"/>')
    svg.append('<text x="80" y="110" font-family="system-ui" font-size="12" fill="#1e3a8a" text-anchor="middle">Column Attention</text>')
    
    svg.append('<rect x="20" y="130" width="120" height="30" rx="4" fill="#ffffff" stroke="#93c5fd" stroke-width="1"/>')
    svg.append('<text x="80" y="150" font-family="system-ui" font-size="12" fill="#1e3a8a" text-anchor="middle">Transition (FFN)</text>')
    svg.append('</g>')

    # Pair Track
    svg.append('<g transform="translate(290, 80)">')
    svg.append('<rect width="160" height="180" rx="8" fill="#ecfdf5" stroke="#10b981" stroke-width="2"/>')
    svg.append('<text x="80" y="30" font-family="system-ui" font-size="16" font-weight="700" fill="#047857" text-anchor="middle">Pair Representation</text>')

    svg.append('<rect x="20" y="50" width="120" height="30" rx="4" fill="#ffffff" stroke="#6ee7b7" stroke-width="1"/>')
    svg.append('<text x="80" y="70" font-family="system-ui" font-size="12" fill="#064e3b" text-anchor="middle">Triangle Update</text>')
    
    svg.append('<rect x="20" y="90" width="120" height="30" rx="4" fill="#ffffff" stroke="#6ee7b7" stroke-width="1"/>')
    svg.append('<text x="80" y="110" font-family="system-ui" font-size="12" fill="#064e3b" text-anchor="middle">Triangle Attention</text>')
    
    svg.append('<rect x="20" y="130" width="120" height="30" rx="4" fill="#ffffff" stroke="#6ee7b7" stroke-width="1"/>')
    svg.append('<text x="80" y="150" font-family="system-ui" font-size="12" fill="#064e3b" text-anchor="middle">Transition (FFN)</text>')
    svg.append('</g>')

    # Interaction Arrows
    svg.append('<path d="M 130 260 L 130 280 L 370 280 L 370 260" fill="none" stroke="#94a3b8" stroke-width="2" stroke-dasharray="4"/>')
    svg.append('<text x="250" y="300" font-family="system-ui" font-size="12" fill="#64748b" text-anchor="middle">Information Exchange (Outer Product / Bias)</text>')
    
    svg.append('<path d="M 210 130 Q 250 110 290 130" fill="none" stroke="#8b5cf6" stroke-width="2" marker-end="url(#arrow)"/>')
    svg.append('<path d="M 290 170 Q 250 190 210 170" fill="none" stroke="#8b5cf6" stroke-width="2" marker-end="url(#arrow)"/>')

    svg.append('</svg>')
    with open("static/images/protein-folding/evoformer.svg", "w", encoding="utf-8") as f:
        f.write("\n".join(svg))

if __name__ == "__main__":
    generate_amino_acid_svg()
    generate_folding_levels_svg()
    generate_evoformer_svg()
    print("Protein SVGs generated successfully.")
