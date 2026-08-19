#!/usr/bin/env python3
"""
generate_snake.py
=================
Generador de Snake auténtico con mecánica de cuadrícula celda a celda:
- Cabeza con ojos direccionales que rotan hacia la dirección de avance (arriba, abajo, izq, der).
- Cuerpo de 6 bloques cuadrados idénticos a las celdas de commits que siguen la estela real sin invertirse.
- Recorrido orgánico por todo el mapa de contribuciones.
- Detección y devorado de nuevo commit verde neón, transformándolo en cyan.
"""

import math

def generate_perfect_snake():
    COLS = 53
    ROWS = 7
    CELL_SIZE = 11
    GAP = 3
    PAD = 14
    WIDTH = PAD * 2 + COLS * (CELL_SIZE + GAP) - GAP
    HEIGHT = PAD * 2 + ROWS * (CELL_SIZE + GAP) - GAP

    # Matriz base de commits del historial real
    LEVEL_COLORS = {
        0: "#161b22",
        1: "#003d52",
        2: "#007799",
        3: "#00b4d8",
        4: "#00d8ff",
    }

    import random
    random.seed(2026)
    grid = [[0 for _ in range(COLS)] for _ in range(ROWS)]
    for c in range(COLS):
        for r in range(ROWS):
            if c > 25 and random.random() > 0.45:
                grid[r][c] = random.choices([1, 2, 3, 4], weights=[40, 30, 20, 10])[0]
            elif random.random() > 0.7:
                grid[r][c] = random.choices([1, 2], weights=[65, 35])[0]

    # Coordenada del nuevo commit verde
    TARGET_C = 36
    TARGET_R = 2
    grid[TARGET_R][TARGET_C] = 0

    # 1. Simulación paso a paso en la cuadrícula discreta (Grid-based path)
    # Generamos una secuencia continua de celdas (c, r) donde cada paso es adyacente (distancia Manhattan = 1)
    
    steps = []
    
    def add_line(c1, r1, c2, r2):
        nonlocal steps
        cur_c, cur_r = c1, r1
        if not steps or steps[-1] != (cur_c, cur_r):
            steps.append((cur_c, cur_r))
        while cur_c != c2 or cur_r != r2:
            if cur_c < c2: cur_c += 1
            elif cur_c > c2: cur_c -= 1
            elif cur_r < r2: cur_r += 1
            elif cur_r > r2: cur_r -= 1
            steps.append((cur_c, cur_r))

    # Ruta de patrullaje de la cabeza por todo el tablero, pasando por (TARGET_C, TARGET_R)
    # y recorriendo esquinas de punta a punta:
    waypoints = [
        (0, 0),
        (12, 0),
        (12, 4),
        (22, 4),
        (22, 1),
        (30, 1),
        (30, TARGET_R),
        (TARGET_C, TARGET_R),   # <--- MOMENTO DEL COMIDO
        (44, TARGET_R),
        (44, 0),
        (52, 0),
        (52, 6),
        (40, 6),
        (40, 5),
        (20, 5),
        (20, 6),
        (4, 6),
        (4, 2),
        (0, 2),
        (0, 0),
    ]

    for i in range(len(waypoints) - 1):
        add_line(waypoints[i][0], waypoints[i][1], waypoints[i+1][0], waypoints[i+1][1])

    # Encontrar el índice de paso en que come el commit
    eat_step_idx = steps.index((TARGET_C, TARGET_R))
    total_steps = len(steps)
    eat_pct = (eat_step_idx / float(total_steps)) * 100.0

    TOTAL_DURATION = 22.0  # segundos por vuelta completa

    # 2. Keyframes de la cabeza y rotación de ojos
    SNAKE_LENGTH = 6
    segments_keyframes = [[] for _ in range(SNAKE_LENGTH)]
    head_rotations = []

    for step_i in range(total_steps):
        pct = (step_i / float(total_steps)) * 100.0
        
        # Posición de la cabeza
        hc, hr = steps[step_i]
        
        # Dirección de la cabeza (para rotar los ojos hacia adelante)
        next_step = steps[(step_i + 1) % total_steps]
        dx = next_step[0] - hc
        dy = next_step[1] - hr
        
        rot = 0
        if dx > 0: rot = 0       # Derecha
        elif dx < 0: rot = 180   # Izquierda
        elif dy > 0: rot = 90    # Abajo
        elif dy < 0: rot = -90   # Arriba
        
        head_rotations.append((pct, rot))

        # Para cada segmento del cuerpo, toma la celda de (step_i - seg_idx)
        for seg_idx in range(SNAKE_LENGTH):
            hist_idx = (step_i - seg_idx) % total_steps
            sc, sr = steps[hist_idx]
            x = PAD + sc * (CELL_SIZE + GAP)
            y = PAD + sr * (CELL_SIZE + GAP)
            segments_keyframes[seg_idx].append((pct, x, y))

    # Construir CSS para cada segmento
    segments_css = ""
    for seg_idx in range(SNAKE_LENGTH):
        kf_str = ""
        for pct, x, y in segments_keyframes[seg_idx]:
            kf_str += f"{pct:.1f}% {{ transform: translate({x}px, {y}px); }}\n        "
        
        segments_css += f"""
      .snake-seg-{seg_idx} {{
        animation: moveSeg_{seg_idx} {TOTAL_DURATION}s linear infinite;
      }}
      @keyframes moveSeg_{seg_idx} {{
        {kf_str}
      }}"""

    # CSS de rotación de la cabeza
    head_rot_kf = ""
    for pct, rot in head_rotations:
        head_rot_kf += f"{pct:.1f}% {{ transform: rotate({rot}deg); }}\n        "

    head_rot_css = f"""
      .snake-head-orient {{
        transform-origin: {CELL_SIZE/2}px {CELL_SIZE/2}px;
        animation: orientHead {TOTAL_DURATION}s steps(1) infinite;
      }}
      @keyframes orientHead {{
        {head_rot_kf}
      }}
    """

    # CSS del commit verde que aparece y cambia de color al comerlo
    target_x = PAD + TARGET_C * (CELL_SIZE + GAP)
    target_y = PAD + TARGET_R * (CELL_SIZE + GAP)

    commit_css = f"""
      #target_commit {{
        animation: commitPulseAndEat {TOTAL_DURATION}s ease-in-out infinite;
        transform-origin: {target_x + CELL_SIZE/2}px {target_y + CELL_SIZE/2}px;
      }}
      @keyframes commitPulseAndEat {{
        0%, {eat_pct - 15.0:.1f}% {{
          opacity: 0;
          transform: scale(0);
          fill: #00e676;
        }}
        {eat_pct - 12.0:.1f}% {{
          opacity: 1;
          transform: scale(1.3);
          fill: #00e676;
          filter: drop-shadow(0 0 10px #00e676);
        }}
        {eat_pct - 8.0:.1f}%, {eat_pct - 1.0:.1f}% {{
          opacity: 1;
          transform: scale(1.05);
          fill: #00e676;
          filter: drop-shadow(0 0 6px #00e676);
        }}
        /* MOMENTO DEL DEVORADO */
        {eat_pct:.1f}% {{
          opacity: 1;
          transform: scale(1.6);
          fill: #ffffff;
          filter: drop-shadow(0 0 16px #ffffff);
        }}
        /* DESPUÉS DE COMIDO: Pasa a Cyan y se queda en el tablero */
        {eat_pct + 1.0:.1f}%, 95% {{
          opacity: 1;
          transform: scale(1);
          fill: #00d8ff;
          filter: drop-shadow(0 0 4px #00d8ff);
        }}
        100% {{
          opacity: 0;
          transform: scale(0);
        }}
      }}
    """

    # 3. Construir SVG de la cuadrícula de commits
    grid_cells_svg = ""
    for r in range(ROWS):
        for c in range(COLS):
            x = PAD + c * (CELL_SIZE + GAP)
            y = PAD + r * (CELL_SIZE + GAP)
            lvl = grid[r][c]
            fill = LEVEL_COLORS[lvl]
            grid_cells_svg += f'<rect x="{x}" y="{y}" width="{CELL_SIZE}" height="{CELL_SIZE}" rx="2" fill="{fill}" />\n    '

    # Commit verde objetivo
    target_commit_svg = f'<rect id="target_commit" x="{target_x}" y="{target_y}" width="{CELL_SIZE}" height="{CELL_SIZE}" rx="2" fill="#00e676" />'

    # Segmentos de la serpiente (cuerpo + cabeza direccional)
    # Cola a cuerpo
    snake_body_svg = ""
    for seg_idx in range(SNAKE_LENGTH - 1, 0, -1):
        opacity = 0.95 - (seg_idx * 0.08)
        snake_body_svg += f"""
    <g class="snake-seg-{seg_idx}">
      <rect x="0" y="0" width="{CELL_SIZE}" height="{CELL_SIZE}" rx="2.5" fill="#00d8ff" opacity="{opacity:.2f}" style="filter: drop-shadow(0 0 3px #00b4d8);" />
    </g>"""

    # Cabeza (seg_0) con rotación direccional de ojos
    snake_head_svg = f"""
    <g class="snake-seg-0">
      <g class="snake-head-orient">
        <!-- Cabeza con esquinas redondeadas tipo arcade -->
        <rect x="0" y="0" width="{CELL_SIZE}" height="{CELL_SIZE}" rx="3" fill="#ffffff" style="filter: drop-shadow(0 0 7px #00d8ff);" />
        <!-- Ojos en el frente (mirando a la derecha en rot 0) -->
        <circle cx="8" cy="3" r="1.4" fill="#0d1117" />
        <circle cx="8" cy="8" r="1.4" fill="#0d1117" />
        <circle cx="8.5" cy="3" r="0.6" fill="#00d8ff" />
        <circle cx="8.5" cy="8" r="0.6" fill="#00d8ff" />
      </g>
    </g>"""

    final_svg = f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {WIDTH} {HEIGHT}" width="100%" height="{HEIGHT}" fill="none">
  <defs>
    <style>
      {commit_css}
      {segments_css}
      {head_rot_css}
    </style>
  </defs>

  <!-- Fondo Limpio -->
  <rect width="100%" height="100%" rx="12" fill="#0d1117" />

  <!-- Historial de Commits Completo -->
  <g>
    {grid_cells_svg}
  </g>

  <!-- Nuevo Commit Verde que Aparece y Muta a Cyan al Ser Comido -->
  <g>
    {target_commit_svg}
  </g>

  <!-- Serpiente Auténtica con Ojos Direccionales y Estela Exacta -->
  <g>
    {snake_body_svg}
    {snake_head_svg}
  </g>
</svg>"""

    with open("assets/snake.svg", "w", encoding="utf-8") as f:
        f.write(final_svg)
    print("Snake SVG con física exacta y ojos direccionales generado con éxito.")

if __name__ == "__main__":
    generate_perfect_snake()
