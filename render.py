#!/usr/bin/env python3
"""Anima DFS Timestamps. Toda la lógica (tin/tout/ancestros) viene de la traza
que imprime dfs_timestamps.cpp; este script solo la dibuja.

Uso:  python3 render.py [--preview] [--out video.mp4]
Requiere: python3, pycairo, ffmpeg, g++
"""
import argparse, math, subprocess, sys, os
import cairo

HERE = os.path.dirname(os.path.abspath(__file__))

# ====== EDITAR: integrantes ======
TITULO = "DFS Timestamps"
INTEGRANTES = ["Rola", "Integrante 2", "Integrante 3"]
CURSO = "CS2023 · Algoritmos y Estructuras de Datos · Proyecto 2 · 2026-2"
# =================================

W, H, FPS = 1920, 1080, 30
BG = (0.058, 0.070, 0.125)
FG = (0.91, 0.92, 0.96)
DIM = (0.55, 0.58, 0.70)
GRAY = (0.23, 0.26, 0.38)
BLUE = (0.31, 0.63, 1.0)
GREEN = (0.27, 0.83, 0.60)
YELLOW = (1.0, 0.82, 0.40)
ORANGE = (1.0, 0.62, 0.35)
PINK = (1.0, 0.42, 0.62)
RED = (1.0, 0.38, 0.38)
SANS, MONO = "DejaVu Sans", "DejaVu Sans Mono"


# ---------------------------------------------------------------- C++ / traza
def build_cpp():
    exe = os.path.join(HERE, "dfs_timestamps")
    src = exe + ".cpp"
    if not os.path.exists(exe) or os.path.getmtime(exe) < os.path.getmtime(src):
        subprocess.check_call(["g++", "-O2", "-std=c++17", src, "-o", exe])
    return exe


def run_cpp(exe, n, root, edges, queries):
    inp = f"{n} {root} {len(queries)}\n"
    inp += "".join(f"{a} {b}\n" for a, b in edges)
    inp += "".join(f"{u} {v}\n" for u, v in queries)
    out = subprocess.run([exe], input=inp, capture_output=True, text=True, check=True).stdout
    events, queries_out = [], []
    for ln in out.splitlines():
        p = ln.split()
        if p[0] == "ENTER":
            events.append(("ENTER", int(p[1]), int(p[2]), int(p[3])))
        elif p[0] == "EXIT":
            events.append(("EXIT", int(p[1]), int(p[2])))
        else:
            queries_out.append((int(p[1]), int(p[2]), p[3] == "1"))
    return Trace(n, events, queries_out)


class Trace:
    def __init__(self, n, events, queries):
        self.n, self.events, self.queries = n, events, queries
        self.parent, self.children, self.tin, self.tout = {}, {}, {}, {}
        for e in events:
            if e[0] == "ENTER":
                _, v, p, t = e
                self.parent[v] = p
                self.tin[v] = t
                self.children.setdefault(v, [])
                if p >= 0:
                    self.children.setdefault(p, []).append(v)
            else:
                self.tout[e[1]] = e[2]
        self.root = events[0][1]

    def layout(self, rect, maxdx=230, maxdy=135):
        """Posiciones (x,y) de cada nodo dentro de rect=(x,y,w,h)."""
        x0, y0, w, h = rect
        leaves = [0]
        slot, depth = {}, {}

        def go(v, d):
            depth[v] = d
            ch = self.children[v]
            if not ch:
                slot[v] = leaves[0]
                leaves[0] += 1
            else:
                for c in ch:
                    go(c, d + 1)
                slot[v] = sum(slot[c] for c in ch) / len(ch)

        go(self.root, 0)
        L, D = leaves[0], max(depth.values()) + 1
        dx = min(maxdx, w / L)
        dy = min(maxdy, h / D)
        cx, cy = x0 + w / 2, y0 + h / 2
        mid = (L - 1) / 2
        pos = {}
        for v in slot:
            pos[v] = (cx + (slot[v] - mid) * dx, cy + (depth[v] - (D - 1) / 2) * dy)
        return pos


def name(v):
    return chr(ord("A") + v)


# ------------------------------------------------------------------- helpers
def ease(p):
    p = max(0.0, min(1.0, p))
    return p * p * (3 - 2 * p)


def seg(p, a, b):
    return ease((p - a) / (b - a))


def col(c, a=1.0):
    return (c[0], c[1], c[2], a)


class Video:
    def __init__(self, out, scale):
        self.scale = scale
        self.w, self.h = int(W * scale), int(H * scale)
        self.surf = cairo.ImageSurface(cairo.FORMAT_ARGB32, self.w, self.h)
        self.c = cairo.Context(self.surf)
        self.c.scale(scale, scale)
        self.ff = subprocess.Popen(
            ["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "bgra",
             "-s", f"{self.w}x{self.h}", "-r", str(FPS), "-i", "-",
             "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "17", "-preset", "medium", out],
            stdin=subprocess.PIPE)
        self.frames = 0

    def play(self, seconds, draw):
        n = max(2, int(round(seconds * FPS)))
        for i in range(n):
            c = self.c
            c.set_source_rgb(*BG)
            c.paint()
            draw(c, i / (n - 1))
            self.ff.stdin.write(self.surf.get_data())
            self.frames += 1

    def close(self):
        self.ff.stdin.close()
        self.ff.wait()


def font(c, size, face=SANS, bold=False):
    c.select_font_face(face, cairo.FONT_SLANT_NORMAL,
                       cairo.FONT_WEIGHT_BOLD if bold else cairo.FONT_WEIGHT_NORMAL)
    c.set_font_size(size)


def text(c, s, x, y, size=36, color=FG, a=1.0, face=SANS, bold=False, align="l"):
    font(c, size, face, bold)
    ext = c.text_extents(s)
    if align == "c":
        x -= ext.x_advance / 2
    elif align == "r":
        x -= ext.x_advance
    c.set_source_rgba(*col(color, a))
    c.move_to(x, y)
    c.show_text(s)


def wrap(c, s, maxw, size, face=SANS, bold=False):
    font(c, size, face, bold)
    lines, cur = [], ""
    for w in s.split(" "):
        t = (cur + " " + w).strip()
        if c.text_extents(t).x_advance > maxw and cur:
            lines.append(cur)
            cur = w
        else:
            cur = t
    lines.append(cur)
    return lines


def para(c, s, x, y, maxw, size=34, color=FG, a=1.0, lh=1.4, bold=False, align="l"):
    for ln in wrap(c, s, maxw, size, bold=bold):
        text(c, ln, x, y, size, color, a, bold=bold, align=align)
        y += size * lh
    return y


def rrect(c, x, y, w, h, r=14):
    c.new_sub_path()
    c.arc(x + w - r, y + r, r, -math.pi / 2, 0)
    c.arc(x + w - r, y + h - r, r, 0, math.pi / 2)
    c.arc(x + r, y + h - r, r, math.pi / 2, math.pi)
    c.arc(x + r, y + r, r, math.pi, 1.5 * math.pi)
    c.close_path()


def panel(c, x, y, w, h, color=GRAY, a=0.35, edge=None):
    rrect(c, x, y, w, h)
    c.set_source_rgba(*col(color, a))
    c.fill_preserve()
    if edge:
        c.set_source_rgba(*col(edge, 0.9))
        c.set_line_width(2)
    else:
        c.set_source_rgba(0, 0, 0, 0)
    c.stroke()


def caption(c, s, a=1.0):
    panel(c, 120, 905, W - 240, 120, GRAY, 0.55 * a)
    lines = wrap(c, s, W - 320, 36)
    y = 905 + 60 - (len(lines) - 1) * 24 + 12
    for ln in lines:
        text(c, ln, W / 2, y, 36, FG, a, align="c")
        y += 50


def header(c, s, sub=None):
    text(c, s, 70, 90, 54, FG, bold=True)
    if sub:
        text(c, sub, 70, 135, 28, DIM)


# ---------------------------------------------------------------- dibujo árbol
class State:
    """Estado visible del DFS en un instante (se arma solo desde la traza)."""
    def __init__(self):
        self.tin, self.tout, self.stack, self.timer = {}, {}, [], 0
        self.cur = None
        self.hl = {}      # nodo -> color (consultas)


def draw_tree(c, T, pos, st, R=34, anim=None, show_pairs=True):
    """anim = (tipo, v, p) para el evento que se está animando."""
    # aristas
    for v, par in T.parent.items():
        if par < 0:
            continue
        (x1, y1), (x2, y2) = pos[par], pos[v]
        seen = v in st.tin or (anim and anim[0] == "ENTER" and anim[1] == v)
        c.set_source_rgba(*col(GRAY if not seen else DIM, 1))
        c.set_line_width(4)
        c.move_to(x1, y1)
        c.line_to(x2, y2)
        c.stroke()
        if anim and anim[0] == "ENTER" and anim[1] == v:        # arista que crece
            q = seg(anim[2], 0, 0.6)
            c.set_source_rgba(*col(YELLOW))
            c.set_line_width(6)
            c.move_to(x1, y1)
            c.line_to(x1 + (x2 - x1) * q, y1 + (y2 - y1) * q)
            c.stroke()
        if anim and anim[0] == "EXIT" and anim[1] == v:         # vuelta al padre
            q = seg(anim[2], 0.3, 1.0)
            c.set_source_rgba(*col(GREEN))
            c.set_line_width(6)
            c.move_to(x2, y2)
            c.line_to(x2 + (x1 - x2) * q, y2 + (y1 - y2) * q)
            c.stroke()
    # nodos
    for v, (x, y) in pos.items():
        discovered = v in st.tin
        done = v in st.tout
        r = R
        if anim and anim[0] == "ENTER" and anim[1] == v:
            q = seg(anim[2], 0.4, 1.0)
            r = R * (0.2 + 0.8 * q) + 8 * math.sin(q * math.pi)
            discovered = q > 0
        fill = GRAY
        if v in st.hl:
            fill = st.hl[v]
        elif done:
            fill = GREEN
        elif discovered:
            fill = BLUE
        c.arc(x, y, r, 0, 2 * math.pi)
        c.set_source_rgba(*col(fill, 1 if (discovered or v in st.hl) else 0.6))
        c.fill()
        if v == st.cur:
            c.arc(x, y, r + 8, 0, 2 * math.pi)
            c.set_source_rgba(*col(YELLOW, 0.6 + 0.4 * math.sin((anim[2] if anim else 0) * 6)))
            c.set_line_width(5)
            c.stroke()
        text(c, name(v), x, y + 11, 32, BG if (discovered or v in st.hl) else DIM, bold=True, align="c")
        if show_pairs:
            ti = st.tin.get(v)
            to = st.tout.get(v)
            if anim and anim[0] == "EXIT" and anim[1] == v:
                to = T.tout[v] if anim[2] > 0.5 else None
            if ti is not None and not (anim and anim[0] == "ENTER" and anim[1] == v and anim[2] < 0.5):
                s_in = str(ti)
                s_out = "?" if to is None else str(to)
                pw = 150
                panel(c, x - pw / 2, y + r + 8, pw, 40, BG, 0.9, GRAY)
                text(c, f"[ {s_in} , {s_out} ]", x, y + r + 37, 26,
                     ORANGE if to is None else FG, face=MONO, bold=True, align="c")


CODE = [
    "dfs(v):",
    "    tin[v] = t++",
    "    para cada hijo u de v:",
    "        dfs(u)",
    "    tout[v] = t - 1",
]


def draw_side(c, st, line=None):
    panel(c, 1230, 175, 640, 300, GRAY, 0.3)
    text(c, "Algoritmo", 1255, 215, 26, DIM)
    for i, ln in enumerate(CODE):
        y = 265 + i * 46
        if i == line:
            panel(c, 1245, y - 33, 610, 44, YELLOW, 0.22)
        text(c, ln, 1265, y, 28, FG, face=MONO)
    # contador
    panel(c, 1230, 495, 300, 110, GRAY, 0.3)
    text(c, "t (reloj)", 1255, 535, 24, DIM)
    text(c, str(st.timer), 1255, 590, 52, ORANGE, bold=True, face=MONO)
    # pila
    panel(c, 1550, 495, 320, 330, GRAY, 0.3)
    text(c, "pila de llamadas", 1570, 535, 24, DIM)
    for i, v in enumerate(reversed(st.stack[-6:])):
        y = 560 + i * 42
        panel(c, 1570, y, 280, 36, BLUE, 0.35 if i else 0.7)
        text(c, f"dfs({name(v)})", 1590, y + 27, 24, FG, face=MONO)
    panel(c, 1230, 625, 300, 200, GRAY, 0.3)
    text(c, "regla", 1255, 665, 24, DIM)
    para(c, "tin: al entrar", 1255, 710, 270, 26, ORANGE)
    para(c, "tout: al salir", 1255, 752, 270, 26, GREEN)


# ------------------------------------------------------------------- escenas
def title_scene(V):
    def d(c, p):
        a = seg(p, 0, 0.2) * (1 - seg(p, 0.85, 1))
        text(c, TITULO, W / 2, 440, 130, FG, a, bold=True, align="c")
        text(c, "Tiempos de descubrimiento (tin) y finalización (tout) en un DFS", W / 2, 520, 38, BLUE, a, align="c")
        text(c, CURSO, W / 2, 640, 28, DIM, a, align="c")
        text(c, " · ".join(INTEGRANTES), W / 2, 700, 34, FG, a * seg(p, 0.2, 0.4), align="c")
    V.play(4.5, d)


def intro_scene(V):
    cards = [
        ("¿Qué es?", BLUE,
         "Durante un DFS le damos a cada nodo dos números: tin[v] cuando lo descubrimos y tout[v] cuando terminamos todo su subárbol."),
        ("¿Para qué sirve?", GREEN,
         "El subárbol de v pasa a ser el intervalo [tin, tout]. Así saber si u es ancestro de v cuesta O(1). Base de LCA, virtual tree, Euler tour..."),
        ("¿Cómo funciona?", ORANGE,
         "Un reloj t que sube SOLO al descubrir. Al entrar: tin[v] = t++. Al salir: tout[v] = t - 1. Un solo recorrido DFS."),
    ]

    def d(c, p):
        header(c, "Introducción", "Es un algoritmo (no una estructura): preprocesa un árbol en O(n)")
        for i, (t, colr, body) in enumerate(cards):
            a = seg(p, 0.05 + i * 0.25, 0.15 + i * 0.25)
            x = 70 + i * 610
            panel(c, x, 220, 580, 420, colr, 0.14 * a, colr)
            text(c, t, x + 35, 295, 46, colr, a, bold=True)
            para(c, body, x + 35, 365, 510, 33, FG, a, 1.45)
    V.play(17, d)


def make_state():
    return State()


def apply(st, ev):
    if ev[0] == "ENTER":
        _, v, par, t = ev
        st.tin[v] = t
        st.stack.append(v)
        st.timer = t + 1
        st.cur = v
    else:
        _, v, to = ev
        st.tout[v] = to
        st.stack.pop()
        st.cur = st.stack[-1] if st.stack else None


def play_dfs(V, T, rect, title, sub, caps, per_event=0.85, R=34, maxdx=230, maxdy=135):
    """Reproduce todos los eventos del DFS. caps: dict indice_evento -> texto."""
    pos = T.layout(rect, maxdx, maxdy)
    st = make_state()
    cap = {"t": ""}
    V.play(0.8, lambda c, p: (header(c, title, sub), draw_tree(c, T, pos, st, R),
                              draw_side(c, st)))
    for i, ev in enumerate(T.events):
        if i in caps:
            cap["t"] = caps[i]
        before_tin = dict(st.tin)
        line = 1 if ev[0] == "ENTER" else 4

        def d(c, p, ev=ev, line=line):
            # durante la animación el estado "anterior" no incluye todavía este evento
            header(c, title, sub)
            anim = (ev[0], ev[1], p)
            draw_tree(c, T, pos, st, R, anim)
            draw_side(c, st, line)
            if cap["t"]:
                caption(c, cap["t"])
        # el estado se aplica al inicio para que pila/reloj reaccionen enseguida,
        # pero tin/tout del nodo se ocultan hasta mitad de la animación (ver draw_tree)
        apply(st, ev)
        if ev[0] == "EXIT":
            tout_val = st.tout.pop(ev[1])
            st.tout_pending = (ev[1], tout_val)
            half = per_event * 0.5

            def d1(c, p, ev=ev, line=line):
                header(c, title, sub)
                draw_tree(c, T, pos, st, R, ("EXIT", ev[1], p * 0.5))
                draw_side(c, st, line)
                if cap["t"]:
                    caption(c, cap["t"])
            V.play(half, d1)
            st.tout[ev[1]] = tout_val

            def d2(c, p, ev=ev, line=line):
                header(c, title, sub)
                draw_tree(c, T, pos, st, R, ("EXIT", ev[1], 0.5 + p * 0.5))
                draw_side(c, st, line)
                if cap["t"]:
                    caption(c, cap["t"])
            V.play(half, d2)
        else:
            V.play(per_event, d)
    st.cur = None
    V.play(1.2, lambda c, p: (header(c, title, sub), draw_tree(c, T, pos, st, R), draw_side(c, st),
                              caption(c, cap["t"]) if cap["t"] else None))
    return pos, st


def demo_scene(V, T):
    caps = {
        0: "Empezamos en la raíz A. Descubrirla: tin[A] = 0 y el reloj pasa a 1.",
        1: "Bajamos a B, luego a E y a H. Cada nodo nuevo recibe el siguiente tin.",
        4: "H es hoja: no tiene hijos, así que sale enseguida y tout[H] = 3 (último tin usado).",
        6: "Al salir de E volvemos a B y descubrimos F (tin = 4). El reloj NO sube al salir.",
        8: "B termina con tout[B] = 4: su subárbol {B, E, F, H} ocupa justo los tiempos 1..4.",
        10: "Seguimos con C, D, G, I y J. Cuando A termine, todos los nodos tienen su par [tin, tout].",
    }
    play_dfs(V, T, (60, 170, 1130, 700), "DFS paso a paso", "Cada nodo termina con un intervalo [tin, tout]", caps, 0.85)


def queries_scene(V, T):
    rect = (60, 150, 1130, 580)
    pos = T.layout(rect)
    st = State()
    st.tin, st.tout = dict(T.tin), dict(T.tout)
    order = sorted(T.tin, key=lambda v: T.tin[v])
    n_t = max(T.tout.values()) + 1
    cx0, cw = 1360, 480

    def draw_chart(c, qu, a_hl, hl):
        panel(c, 1230, 175, 640, 640, GRAY, 0.3)
        text(c, "intervalos [tin, tout]", 1255, 215, 26, DIM)
        u = cw / n_t
        for t in range(n_t + 1):
            x = cx0 + t * u
            c.set_source_rgba(*col(GRAY, 0.8))
            c.set_line_width(1.5)
            c.move_to(x, 245)
            c.line_to(x, 245 + len(order) * 46 + 6)
            c.stroke()
        for t in range(n_t):
            text(c, str(t), cx0 + (t + 0.5) * u, 240, 20, DIM, align="c")
        for i, v in enumerate(order):
            y = 255 + i * 46
            colr = hl.get(v, BLUE if True else GREEN)
            base = colr if v in hl else GRAY
            text(c, name(v), 1262, y + 28, 26, FG, face=MONO, bold=True)
            rrect(c, cx0 + T.tin[v] * u + 3, y + 3, (T.tout[v] - T.tin[v] + 1) * u - 6, 32, 8)
            c.set_source_rgba(*col(base, 1.0 if v in hl else 0.75))
            c.fill()

    def one(qi, q):
        a, b, ans = q

        def d(c, p):
            hl = {}
            if p > 0.08:
                hl[a] = YELLOW
                hl[b] = BLUE
            st.hl = {}
            if p > 0.08:
                st.hl = dict(hl)
            if p > 0.75:
                st.hl[b] = GREEN if ans else RED
            header(c, "Consultas de ancestro en O(1)", "¿u es ancestro de v?  tin[u] ≤ tin[v]  y  tout[v] ≤ tout[u]")
            draw_tree(c, T, pos, st, 34)
            draw_chart(c, q, 1, hl)
            # fórmula con los números reales
            ta, tb, oa, ob = T.tin[a], T.tin[b], T.tout[a], T.tout[b]
            s1 = f"¿{name(a)} es ancestro de {name(b)}?"
            text(c, s1, 70, 800, 40, YELLOW, seg(p, 0, 0.1), bold=True)
            if p > 0.35:
                k1, k2 = ta <= tb, ob <= oa
                text(c, f"tin[{name(a)}] ≤ tin[{name(b)}]  →  {ta} ≤ {tb}  →  {'sí' if k1 else 'no'}", 70, 845, 30,
                     GREEN if k1 else RED, seg(p, 0.35, 0.5), face=MONO)
            if p > 0.5:
                k2 = ob <= oa
                text(c, f"tout[{name(b)}] ≤ tout[{name(a)}]  →  {ob} ≤ {oa}  →  {'sí' if k2 else 'no'}", 70, 885, 30,
                     GREEN if k2 else RED, seg(p, 0.5, 0.65), face=MONO)
            if p > 0.75:
                res = f"Respuesta del programa en C++: {'SÍ es ancestro' if ans else 'NO es ancestro'}"
                text(c, res, 70, 940, 40, GREEN if ans else RED, seg(p, 0.75, 0.9), bold=True)
        V.play(5.5, d)

    for qi, q in enumerate(T.queries):
        one(qi, q)
    # nota sobre caso u == v
    st.hl = {}


def edge_scene(V, T1, T2):
    caps1 = {0: "Caso borde 1 — árbol con un solo nodo: tin = tout = 0. El intervalo [0, 0] es válido y A es ancestro de sí mismo."}
    play_dfs(V, T1, (60, 170, 1130, 700), "Caso borde: un solo nodo", "n = 1", caps1, 1.2)
    caps2 = {0: "Caso borde 2 — peor caso de profundidad: una cadena. Los tin crecen 0,1,2,3,4 y todos los tout valen 4.",
             5: "Los intervalos quedan anidados [0,4] ⊃ [1,4] ⊃ [2,4]...: cada nodo es ancestro de los de abajo, aun con n grande."}
    play_dfs(V, T2, (60, 170, 1130, 700), "Caso borde: cadena (profundidad n)", "n = 5, un solo hijo por nodo", caps2, 0.7, R=34, maxdy=150)


def complexity_scene(V):
    rows = [
        ("Precomputar tin / tout", "O(n)", "un solo DFS: cada nodo y cada arista una vez", BLUE),
        ("¿u es ancestro de v?", "O(1)", "dos comparaciones de enteros", GREEN),
        ("Tamaño del subárbol de v", "O(1)", "tout[v] − tin[v] + 1", GREEN),
        ("Memoria extra", "O(n)", "dos arreglos (tin, tout) + pila del DFS", ORANGE),
    ]

    def d(c, p):
        header(c, "Complejidad", "Con n nodos (en un árbol hay n − 1 aristas)")
        for i, (a, o, why, colr) in enumerate(rows):
            al = seg(p, 0.05 + i * 0.15, 0.15 + i * 0.15)
            y = 215 + i * 150
            panel(c, 70, y, 1780, 125, colr, 0.13 * al, colr)
            text(c, a, 110, y + 55, 40, FG, al, bold=True)
            text(c, why, 110, y + 100, 28, DIM, al)
            text(c, o, 1800, y + 80, 64, colr, al, bold=True, face=MONO, align="r")
        t = seg(p, 0.7, 0.85)
        para(c, "Se paga O(n) una vez y después cada consulta de ancestros cuesta O(1) (frente a O(h) subiendo por los padres).",
             70, 850, 1780, 34, YELLOW, t)
    V.play(14, d)


def credits_scene(V):
    def d(c, p):
        a = seg(p, 0, 0.2) * (1 - seg(p, 0.85, 1))
        text(c, "Gracias", W / 2, 400, 110, FG, a, bold=True, align="c")
        text(c, TITULO + " · " + CURSO, W / 2, 490, 30, BLUE, a, align="c")
        y = 580
        for n in INTEGRANTES:
            text(c, n, W / 2, y, 40, FG, a, align="c")
            y += 60
        text(c, "Inspiración visual: 3Blue1Brown / Manim. Código propio en C++ y Python (pycairo + ffmpeg).",
             W / 2, y + 60, 26, DIM, a, align="c")
    V.play(6, d)


# ----------------------------------------------------------------------- main
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--preview", action="store_true", help="960x540 rápido")
    ap.add_argument("--out", default=os.path.join(HERE, "dfs_timestamps.mp4"))
    ap.add_argument("--scene", default="all")
    a = ap.parse_args()

    exe = build_cpp()
    edges = [(0, 1), (0, 2), (0, 3), (1, 4), (1, 5), (3, 6), (4, 7), (6, 8), (6, 9)]
    T = run_cpp(exe, 10, 0, edges, [(0, 7), (1, 9), (6, 9), (2, 2)])
    T1 = run_cpp(exe, 1, 0, [], [(0, 0)])
    T2 = run_cpp(exe, 5, 0, [(0, 1), (1, 2), (2, 3), (3, 4)], [(0, 4), (4, 0)])

    V = Video(a.out, 0.5 if a.preview else 1.0)
    scenes = {
        "title": lambda: title_scene(V),
        "intro": lambda: intro_scene(V),
        "demo": lambda: demo_scene(V, T),
        "queries": lambda: queries_scene(V, T),
        "edge": lambda: edge_scene(V, T1, T2),
        "complexity": lambda: complexity_scene(V),
        "credits": lambda: credits_scene(V),
    }
    for k, f in scenes.items():
        if a.scene in ("all", k):
            f()
    V.close()
    print(f"listo: {a.out}  ({V.frames / FPS:.1f} s)")


if __name__ == "__main__":
    main()
