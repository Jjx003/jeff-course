import math

def generate_equity_chart():
    out_data = [
        {"outs": 4, "rule": 16, "exact": 16.5},
        {"outs": 8, "rule": 32, "exact": 31.5},
        {"outs": 9, "rule": 36, "exact": 35.0},
        {"outs": 12, "rule": 48, "exact": 45.0},
        {"outs": 15, "rule": 60, "exact": 54.1},
    ]

    width = 700
    height = 400
    padding_x = 80
    padding_top = 80
    padding_bottom = 60

    svg = []
    svg.append(f'<svg width="{width}" height="{height}" viewBox="0 0 {width} {height}" xmlns="http://www.w3.org/2000/svg">')
    svg.append('<defs>')
    svg.append('<linearGradient id="bg" x1="0%" y1="0%" x2="0%" y2="100%"><stop offset="0%" stop-color="#ffffff"/><stop offset="100%" stop-color="#f8fafc"/></linearGradient>')
    svg.append('<linearGradient id="ruleLine" x1="0%" y1="0%" x2="100%" y2="0%"><stop offset="0%" stop-color="#94a3b8"/><stop offset="100%" stop-color="#64748b"/></linearGradient>')
    svg.append('<linearGradient id="exactLine" x1="0%" y1="0%" x2="100%" y2="0%"><stop offset="0%" stop-color="#3b82f6"/><stop offset="100%" stop-color="#1d4ed8"/></linearGradient>')
    svg.append('<filter id="shadow" x="-10%" y="-10%" width="120%" height="120%"><feDropShadow dx="0" dy="4" stdDeviation="4" flood-color="#2563eb" flood-opacity="0.2"/></filter>')
    svg.append('</defs>')

    svg.append(f'<rect width="{width}" height="{height}" rx="16" fill="url(#bg)" stroke="#e2e8f0" stroke-width="1"/>')

    # Title
    svg.append('<text x="40" y="45" font-family="system-ui, -apple-system, sans-serif" font-size="22" font-weight="700" fill="#0f172a">Rule of 4 vs. Exact Equity</text>')
    svg.append('<text x="40" y="65" font-family="system-ui, -apple-system, sans-serif" font-size="14" fill="#64748b">Comparing the approximation rule to true mathematical equity on the flop</text>')

    g_width = width - padding_x * 2
    g_height = height - padding_top - padding_bottom
    x_start = padding_x
    y_end = height - padding_bottom

    # Y-axis (0 to 70%)
    y_max = 70
    for i in range(0, 80, 10):
        y = y_end - (i / y_max) * g_height
        svg.append(f'<line x1="{x_start}" y1="{y}" x2="{x_start + g_width}" y2="{y}" stroke="#e2e8f0" stroke-width="1" stroke-dasharray="4 4"/>')
        svg.append(f'<text x="{x_start - 15}" y="{y + 4}" font-family="system-ui, sans-serif" font-size="12" font-weight="500" fill="#94a3b8" text-anchor="end">{i}%</text>')

    x_step = g_width / (len(out_data) - 1)
    rule_points = []
    exact_points = []

    for idx, d in enumerate(out_data):
        x = x_start + idx * x_step
        y_rule = y_end - (d["rule"] / y_max) * g_height
        y_exact = y_end - (d["exact"] / y_max) * g_height
        
        rule_points.append(f"{x},{y_rule}")
        exact_points.append(f"{x},{y_exact}")

        svg.append(f'<line x1="{x}" y1="{y_end}" x2="{x}" y2="{y_end + 8}" stroke="#cbd5e1" stroke-width="2"/>')
        svg.append(f'<text x="{x}" y="{y_end + 24}" font-family="system-ui, sans-serif" font-size="13" font-weight="600" fill="#475569" text-anchor="middle">{d["outs"]} outs</text>')

    svg.append(f'<polyline points="{" ".join(rule_points)}" fill="none" stroke="url(#ruleLine)" stroke-width="4" stroke-dasharray="8 6" stroke-linecap="round" stroke-linejoin="round"/>')
    svg.append(f'<polyline points="{" ".join(exact_points)}" fill="none" stroke="url(#exactLine)" stroke-width="5" stroke-linecap="round" stroke-linejoin="round" filter="url(#shadow)"/>')

    for idx, d in enumerate(out_data):
        x = x_start + idx * x_step
        y_rule = y_end - (d["rule"] / y_max) * g_height
        y_exact = y_end - (d["exact"] / y_max) * g_height
        
        # Rule points & Tooltips
        svg.append(f'<circle cx="{x}" cy="{y_rule}" r="5" fill="#ffffff" stroke="#64748b" stroke-width="2"/>')
        svg.append(f'<rect x="{x - 22}" y="{y_rule - 32}" width="44" height="22" rx="4" fill="#f1f5f9" stroke="#cbd5e1" stroke-width="1"/>')
        svg.append(f'<text x="{x}" y="{y_rule - 17}" font-family="system-ui, sans-serif" font-size="12" font-weight="700" fill="#64748b" text-anchor="middle">{d["rule"]}%</text>')

        # Exact points & Tooltips
        svg.append(f'<circle cx="{x}" cy="{y_exact}" r="7" fill="#ffffff" stroke="#2563eb" stroke-width="3"/>')
        svg.append(f'<rect x="{x - 22}" y="{y_exact + 12}" width="44" height="22" rx="4" fill="#eff6ff" stroke="#bfdbfe" stroke-width="1"/>')
        svg.append(f'<text x="{x}" y="{y_exact + 27}" font-family="system-ui, sans-serif" font-size="12" font-weight="700" fill="#1d4ed8" text-anchor="middle">{d["exact"]}%</text>')

    # Legend
    leg_y = height - 25
    svg.append('<rect x="40" y="{}" width="16" height="4" rx="2" fill="#2563eb" transform="translate(0, -6)"/>'.format(leg_y))
    svg.append(f'<text x="65" y="{leg_y}" font-family="system-ui, sans-serif" font-size="13" font-weight="600" fill="#1e293b">Exact Mathematical Equity</text>')
    
    svg.append('<line x1="260" y1="{}" x2="280" y2="{}" stroke="#64748b" stroke-width="4" stroke-dasharray="6 4" transform="translate(0, -4)"/>'.format(leg_y, leg_y))
    svg.append(f'<text x="290" y="{leg_y}" font-family="system-ui, sans-serif" font-size="13" font-weight="600" fill="#1e293b">Rule of 4 Approximation</text>')

    svg.append('</svg>')
    
    with open("static/images/poker-theory/equity-chart.svg", "w", encoding="utf-8") as f:
        f.write("\n".join(svg))

def generate_hand_matrix():
    ranks = ["A", "K", "Q", "J", "T", "9", "8", "7", "6", "5", "4", "3", "2"]
    cell_size = 46
    padding_x = 60
    padding_y = 80
    width = cell_size * 13 + padding_x * 2
    height = cell_size * 13 + padding_y + 80 # legend space

    svg = []
    svg.append(f'<svg width="{width}" height="{height}" viewBox="0 0 {width} {height}" xmlns="http://www.w3.org/2000/svg">')
    svg.append('<defs>')
    svg.append('<style>')
    svg.append('.cell { stroke: #ffffff; stroke-width: 3px; transition: all 0.2s; }')
    svg.append('.cell:hover { opacity: 0.9; }')
    svg.append('.text { font-family: system-ui, -apple-system, sans-serif; font-size: 15px; font-weight: 700; text-anchor: middle; dominant-baseline: central; pointer-events: none; }')
    svg.append('.title { font-family: system-ui, -apple-system, sans-serif; font-size: 28px; font-weight: 800; fill: #0f172a; }')
    svg.append('.subtitle { font-family: system-ui, -apple-system, sans-serif; font-size: 15px; fill: #64748b; }')
    svg.append('.legend-text { font-family: system-ui, -apple-system, sans-serif; font-size: 15px; font-weight: 600; fill: #334155; dominant-baseline: central; }')
    svg.append('</style>')
    svg.append('</defs>')

    svg.append(f'<rect width="{width}" height="{height}" rx="24" fill="#f8fafc" />')
    
    svg.append('<text x="60" y="45" class="title">Complete Starting Hand Matrix</text>')
    svg.append('<text x="60" y="70" class="subtitle">169 distinct hand categories representing all 1,326 combos</text>')

    start_x = padding_x
    start_y = 100

    for i, r1 in enumerate(ranks):
        for j, r2 in enumerate(ranks):
            x = start_x + j * cell_size
            y = start_y + i * cell_size
            
            if i == j:
                hand = f"{r1}{r2}"
                fill = "#8b5cf6" # Violet for pairs
                text_color = "#ffffff"
            elif j > i:
                hand = f"{r1}{r2}s"
                fill = "#34d399" # Emerald for suited
                text_color = "#022c22"
            else:
                hand = f"{r2}{r1}o"
                fill = "#cbd5e1" # Slate for offsuit
                text_color = "#1e293b"
            
            svg.append(f'<rect x="{x}" y="{y}" width="{cell_size}" height="{cell_size}" rx="8" class="cell" fill="{fill}"/>')
            svg.append(f'<text x="{x + cell_size/2}" y="{y + cell_size/2 + 1}" class="text" fill="{text_color}">{hand}</text>')

    # Legend
    leg_y = start_y + 13 * cell_size + 40
    
    # Legend - Pairs
    svg.append(f'<rect x="{start_x}" y="{leg_y}" width="24" height="24" rx="6" fill="#8b5cf6"/>')
    svg.append(f'<text x="{start_x + 36}" y="{leg_y + 13}" class="legend-text">Pocket Pairs (6 combos)</text>')

    # Legend - Suited
    svg.append(f'<rect x="{start_x + 240}" y="{leg_y}" width="24" height="24" rx="6" fill="#34d399"/>')
    svg.append(f'<text x="{start_x + 276}" y="{leg_y + 13}" class="legend-text">Suited (4 combos)</text>')

    # Legend - Offsuit
    svg.append(f'<rect x="{start_x + 460}" y="{leg_y}" width="24" height="24" rx="6" fill="#cbd5e1"/>')
    svg.append(f'<text x="{start_x + 496}" y="{leg_y + 13}" class="legend-text">Offsuit (12 combos)</text>')

    svg.append('</svg>')

    with open("static/images/poker-theory/hand-matrix.svg", "w", encoding="utf-8") as f:
        f.write("\n".join(svg))

if __name__ == "__main__":
    generate_equity_chart()
    generate_hand_matrix()
    print("SVGs generated successfully.")
