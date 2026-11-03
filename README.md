# DFS Timestamps — Anima tu Algoritmo (CS2023, Proyecto 2)

Video educativo (~96 s) que explica y demuestra **DFS Timestamps** (`tin` / `tout`).

## Cómo funciona (la animación es real)
- `dfs_timestamps.cpp`: implementación propia en C++ (DFS iterativo con pila explícita, sin librerías de grafos). Imprime una *traza* (`ENTER`, `EXIT`, `QUERY`) con los valores que calcula de verdad.
- `render.py`: lee esa traza y la dibuja con pycairo; ffmpeg codifica el MP4. Ningún tin/tout/respuesta está escrito a mano.

## Requisitos
`g++` (C++17), `python3`, `pycairo`, `ffmpeg`, fuente DejaVu Sans.

## Ejecutar
```bash
python3 render.py            # 1920x1080 -> dfs_timestamps.mp4
python3 render.py --preview  # 960x540, rápido
python3 render.py --scene demo   # una sola escena (title, intro, demo, queries, edge, complexity, credits)
```
Los integrantes se editan al inicio de `render.py` (`INTEGRANTES`).

## Probar el C++ solo
```bash
g++ -O2 -std=c++17 dfs_timestamps.cpp -o dfs_timestamps
printf '3 0 1\n0 1\n1 2\n0 2\n' | ./dfs_timestamps   # n root q / aristas / consultas
```

## Complejidad
Precómputo O(n) · ¿u ancestro de v? O(1) · tamaño de subárbol O(1) · memoria O(n).
