import os

def write_svg(filename, content):
    filepath = os.path.join("static", "images", "protein-folding", filename)
    with open(filepath, "w", encoding="utf-8") as f:
        f.write("\n".join(content))

def gen_folding_funnel():
    svg = [
        '<svg width="500" height="350" viewBox="0 0 500 350" xmlns="http://www.w3.org/2000/svg">',
        '<defs>',
        '<linearGradient id="bg" x1="0%" y1="0%" x2="0%" y2="100%"><stop offset="0%" stop-color="#ffffff"/><stop offset="100%" stop-color="#f8fafc"/></linearGradient>',
        '<linearGradient id="funnelGrad" x1="0%" y1="0%" x2="0%" y2="100%"><stop offset="0%" stop-color="#93c5fd" stop-opacity="0.6"/><stop offset="100%" stop-color="#1d4ed8" stop-opacity="0.8"/></linearGradient>',
        '</defs>',
        '<rect width="500" height="350" rx="16" fill="url(#bg)" stroke="#e2e8f0" stroke-width="1"/>',
        '<text x="250" y="40" font-family="system-ui" font-size="20" font-weight="700" fill="#0f172a" text-anchor="middle">The Folding Funnel Energy Landscape</text>',
        
        # Axes
        '<line x1="50" y1="300" x2="450" y2="300" stroke="#94a3b8" stroke-width="2" marker-end="url(#arrow)"/>',
        '<line x1="250" y1="310" x2="250" y2="60" stroke="#94a3b8" stroke-width="2" marker-end="url(#arrow)"/>',
        '<text x="250" y="330" font-family="system-ui" font-size="14" fill="#64748b" text-anchor="middle">Conformational Entropy</text>',
        '<text x="30" y="180" font-family="system-ui" font-size="14" fill="#64748b" text-anchor="middle" transform="rotate(-90 30 180)">Free Energy</text>',
        
        # Funnel Shape
        '<path d="M 100 80 Q 150 150 200 180 Q 220 220 250 280 Q 280 220 300 180 Q 350 150 400 80 L 250 80 Z" fill="url(#funnelGrad)" stroke="#2563eb" stroke-width="2" stroke-linejoin="round"/>',
        
        # Labels
        '<text x="150" y="100" font-family="system-ui" font-size="12" font-weight="600" fill="#1e3a8a" text-anchor="middle">Unfolded States</text>',
        '<text x="350" y="100" font-family="system-ui" font-size="12" font-weight="600" fill="#1e3a8a" text-anchor="middle">Unfolded States</text>',
        '<text x="160" y="170" font-family="system-ui" font-size="12" font-weight="600" fill="#1e3a8a" text-anchor="middle">Molten Globule</text>',
        '<circle cx="250" cy="275" r="5" fill="#ef4444" />',
        '<text x="310" y="280" font-family="system-ui" font-size="14" font-weight="700" fill="#dc2626" text-anchor="start">Native State</text>',
        
        '</svg>'
    ]
    write_svg("folding-funnel.svg", svg)

def gen_coevolution():
    svg = [
        '<svg width="500" height="300" viewBox="0 0 500 300" xmlns="http://www.w3.org/2000/svg">',
        '<rect width="500" height="300" rx="16" fill="#f8fafc" stroke="#e2e8f0" stroke-width="1"/>',
        '<text x="250" y="40" font-family="system-ui" font-size="20" font-weight="700" fill="#0f172a" text-anchor="middle">Co-evolution in an MSA</text>',
        
        # MSA Grid
        '<g transform="translate(150, 80)">',
    ]
    
    seqs = [
        ["A", "L", "D", "V", "R"], # D(-), R(+)
        ["A", "L", "E", "V", "K"], # E(-), K(+)
        ["A", "I", "D", "I", "K"], # D(-), K(+)
        ["A", "V", "R", "V", "D"], # R(+), D(-) -> mutation!
        ["A", "L", "K", "V", "E"]  # K(+), E(-) -> mutation!
    ]
    
    cell_w = 40
    cell_h = 30
    
    for i, seq in enumerate(seqs):
        svg.append(f'<text x="-10" y="{i*cell_h + 20}" font-family="system-ui" font-size="12" fill="#64748b" text-anchor="end">Seq {i+1}</text>')
        for j, res in enumerate(seq):
            fill = "#ffffff"
            text_color = "#334155"
            stroke = "#cbd5e1"
            
            # Highlight co-evolving columns
            if j == 2: # Negative/Positive
                if res in ["D", "E"]: fill, text_color = "#fee2e2", "#b91c1c" # Red for negative
                if res in ["R", "K"]: fill, text_color = "#dbeafe", "#1d4ed8" # Blue for positive
                stroke = "#94a3b8"
            elif j == 4:
                if res in ["D", "E"]: fill, text_color = "#fee2e2", "#b91c1c"
                if res in ["R", "K"]: fill, text_color = "#dbeafe", "#1d4ed8"
                stroke = "#94a3b8"
                
            svg.append(f'<rect x="{j*cell_w}" y="{i*cell_h}" width="{cell_w}" height="{cell_h}" fill="{fill}" stroke="{stroke}" stroke-width="1"/>')
            svg.append(f'<text x="{j*cell_w + 20}" y="{i*cell_h + 20}" font-family="system-ui" font-size="14" font-weight="600" fill="{text_color}" text-anchor="middle">{res}</text>')
            
    svg.append('</g>')
    
    # Arrows and explanations
    svg.append('<path d="M 250 240 Q 290 270 330 240" fill="none" stroke="#8b5cf6" stroke-width="2" stroke-dasharray="4"/>')
    svg.append('<text x="290" y="270" font-family="system-ui" font-size="12" font-weight="600" fill="#6d28d9" text-anchor="middle">Charge-reversal mutations correlate</text>')
    
    svg.append('<text x="250" y="65" font-family="system-ui" font-size="12" fill="#64748b" text-anchor="middle">Position i</text>')
    svg.append('<text x="330" y="65" font-family="system-ui" font-size="12" fill="#64748b" text-anchor="middle">Position j</text>')
    
    svg.append('</svg>')
    write_svg("coevolution.svg", svg)

def gen_mlm():
    svg = [
        '<svg width="500" height="250" viewBox="0 0 500 250" xmlns="http://www.w3.org/2000/svg">',
        '<rect width="500" height="250" rx="16" fill="#f8fafc" stroke="#e2e8f0" stroke-width="1"/>',
        '<text x="250" y="40" font-family="system-ui" font-size="20" font-weight="700" fill="#0f172a" text-anchor="middle">Masked Language Modeling (MLM)</text>',
        
        # Input tokens
        '<g transform="translate(40, 80)">',
        '<rect x="0" y="0" width="40" height="40" rx="6" fill="#e2e8f0"/><text x="20" y="25" font-family="system-ui" font-weight="700" text-anchor="middle">M</text>',
        '<rect x="50" y="0" width="40" height="40" rx="6" fill="#e2e8f0"/><text x="70" y="25" font-family="system-ui" font-weight="700" text-anchor="middle">E</text>',
        '<rect x="100" y="0" width="60" height="40" rx="6" fill="#fef08a" stroke="#d97706"/><text x="130" y="25" font-family="system-ui" font-size="12" font-weight="700" fill="#b45309" text-anchor="middle">&lt;MASK&gt;</text>',
        '<rect x="170" y="0" width="40" height="40" rx="6" fill="#e2e8f0"/><text x="190" y="25" font-family="system-ui" font-weight="700" text-anchor="middle">G</text>',
        '<rect x="220" y="0" width="40" height="40" rx="6" fill="#e2e8f0"/><text x="240" y="25" font-family="system-ui" font-weight="700" text-anchor="middle">L</text>',
        '<rect x="270" y="0" width="40" height="40" rx="6" fill="#e2e8f0"/><text x="290" y="25" font-family="system-ui" font-weight="700" text-anchor="middle">Y</text>',
        '<rect x="320" y="0" width="60" height="40" rx="6" fill="#fef08a" stroke="#d97706"/><text x="350" y="25" font-family="system-ui" font-size="12" font-weight="700" fill="#b45309" text-anchor="middle">&lt;MASK&gt;</text>',
        '<rect x="390" y="0" width="40" height="40" rx="6" fill="#e2e8f0"/><text x="410" y="25" font-family="system-ui" font-weight="700" text-anchor="middle">S</text>',
        '</g>',
        
        # Transformer
        '<rect x="150" y="140" width="200" height="30" rx="6" fill="#dbeafe" stroke="#3b82f6" stroke-width="2"/>',
        '<text x="250" y="160" font-family="system-ui" font-size="14" font-weight="700" fill="#1d4ed8" text-anchor="middle">Protein Language Model</text>',
        
        # Arrows
        '<line x1="250" y1="120" x2="250" y2="140" stroke="#94a3b8" stroke-width="2"/>',
        '<line x1="170" y1="170" x2="170" y2="190" stroke="#94a3b8" stroke-width="2"/>',
        '<line x1="390" y1="170" x2="390" y2="190" stroke="#94a3b8" stroke-width="2"/>',
        
        # Output tokens
        '<g transform="translate(150, 190)">',
        '<rect x="0" y="0" width="40" height="40" rx="6" fill="#dcfce7" stroke="#059669"/><text x="20" y="25" font-family="system-ui" font-weight="700" fill="#047857" text-anchor="middle">T</text>',
        '</g>',
        '<g transform="translate(370, 190)">',
        '<rect x="0" y="0" width="40" height="40" rx="6" fill="#dcfce7" stroke="#059669"/><text x="20" y="25" font-family="system-ui" font-weight="700" fill="#047857" text-anchor="middle">A</text>',
        '</g>',
        
        '</svg>'
    ]
    write_svg("mlm.svg", svg)

def gen_plddt():
    svg = [
        '<svg width="500" height="200" viewBox="0 0 500 200" xmlns="http://www.w3.org/2000/svg">',
        '<rect width="500" height="200" rx="16" fill="#f8fafc" stroke="#e2e8f0" stroke-width="1"/>',
        '<text x="250" y="40" font-family="system-ui" font-size="20" font-weight="700" fill="#0f172a" text-anchor="middle">AlphaFold pLDDT Confidence Scale</text>',
        
        # Scale
        '<g transform="translate(50, 80)">',
        '<rect x="0" y="0" width="100" height="40" fill="#ff7d45"/>',
        '<rect x="100" y="0" width="100" height="40" fill="#ffdb13"/>',
        '<rect x="200" y="0" width="100" height="40" fill="#65cbf3"/>',
        '<rect x="300" y="0" width="100" height="40" fill="#0053d6"/>',
        
        # Markers
        '<line x1="100" y1="-5" x2="100" y2="45" stroke="#ffffff" stroke-width="2"/>',
        '<line x1="200" y1="-5" x2="200" y2="45" stroke="#ffffff" stroke-width="2"/>',
        '<line x1="300" y1="-5" x2="300" y2="45" stroke="#ffffff" stroke-width="2"/>',
        
        # Text top
        '<text x="50" y="25" font-family="system-ui" font-size="14" font-weight="700" fill="#ffffff" text-anchor="middle">&lt; 50</text>',
        '<text x="150" y="25" font-family="system-ui" font-size="14" font-weight="700" fill="#1e293b" text-anchor="middle">50 - 70</text>',
        '<text x="250" y="25" font-family="system-ui" font-size="14" font-weight="700" fill="#1e293b" text-anchor="middle">70 - 90</text>',
        '<text x="350" y="25" font-family="system-ui" font-size="14" font-weight="700" fill="#ffffff" text-anchor="middle">&gt; 90</text>',
        
        # Text bottom
        '<text x="50" y="65" font-family="system-ui" font-size="12" font-weight="600" fill="#c2410c" text-anchor="middle">Very Low (IDR)</text>',
        '<text x="150" y="65" font-family="system-ui" font-size="12" font-weight="600" fill="#a16207" text-anchor="middle">Low</text>',
        '<text x="250" y="65" font-family="system-ui" font-size="12" font-weight="600" fill="#0284c7" text-anchor="middle">Confident</text>',
        '<text x="350" y="65" font-family="system-ui" font-size="12" font-weight="600" fill="#1e3a8a" text-anchor="middle">Very High</text>',
        '</g>',
        
        '</svg>'
    ]
    write_svg("plddt.svg", svg)

def gen_inverse_folding():
    svg = [
        '<svg width="500" height="250" viewBox="0 0 500 250" xmlns="http://www.w3.org/2000/svg">',
        '<rect width="500" height="250" rx="16" fill="#f8fafc" stroke="#e2e8f0" stroke-width="1"/>',
        '<text x="250" y="40" font-family="system-ui" font-size="20" font-weight="700" fill="#0f172a" text-anchor="middle">Inverse Folding (ProteinMPNN)</text>',
        
        # Left: Structure
        '<g transform="translate(60, 90)">',
        '<path d="M 0 30 C 20 -20 40 80 60 30 S 80 -10 100 30" fill="none" stroke="#8b5cf6" stroke-width="6" stroke-linecap="round"/>',
        '<text x="50" y="80" font-family="system-ui" font-size="14" font-weight="600" fill="#6d28d9" text-anchor="middle">Fixed 3D Backbone</text>',
        '</g>',
        
        # Middle: Model
        '<rect x="200" y="95" width="100" height="40" rx="8" fill="#10b981" stroke="#047857" stroke-width="2"/>',
        '<text x="250" y="120" font-family="system-ui" font-size="14" font-weight="700" fill="#ffffff" text-anchor="middle">ProteinMPNN</text>',
        
        # Arrows
        '<line x1="170" y1="115" x2="190" y2="115" stroke="#94a3b8" stroke-width="2" marker-end="url(#arrow)"/>',
        '<line x1="310" y1="115" x2="330" y2="115" stroke="#94a3b8" stroke-width="2" marker-end="url(#arrow)"/>',
        
        # Right: Sequence
        '<g transform="translate(340, 95)">',
        '<rect x="0" y="0" width="120" height="40" rx="6" fill="#eff6ff" stroke="#3b82f6" stroke-width="1"/>',
        '<text x="60" y="25" font-family="system-ui" font-size="14" font-weight="700" fill="#1d4ed8" text-anchor="middle" letter-spacing="2">M K A V L</text>',
        '<text x="60" y="75" font-family="system-ui" font-size="14" font-weight="600" fill="#2563eb" text-anchor="middle">Designed Sequence</text>',
        '</g>',
        
        '</svg>'
    ]
    write_svg("inverse-folding.svg", svg)

if __name__ == "__main__":
    gen_folding_funnel()
    gen_coevolution()
    gen_mlm()
    gen_plddt()
    gen_inverse_folding()
    print("New Protein SVGs generated successfully.")
