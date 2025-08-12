from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, Set, List, Optional
import argparse, os, math

EPS = "ε"

# ----------------------- tokenización / parsing -----------------------
def remove_spaces(s: str) -> str:
    return "".join(ch for ch in s if not ch.isspace())

def is_symbol(ch: str) -> bool:
    return ch not in {"|", "*", "+", "?", "(", ")", "."}

def add_concat(exp: str) -> str:
    """Inserta el operador de concatenación explícito '.' donde corresponda."""
    res = []
    for i, ch in enumerate(exp):
        res.append(ch)
        if i == len(exp) - 1:
            continue
        a, b = ch, exp[i + 1]
        if (is_symbol(a) or a in {")", "*", "+", "?"}) and (is_symbol(b) or b in {"(", EPS}):
            res.append(".")
    return "".join(res)

PRECEDENCE = {"|": 1, ".": 2, "*": 3, "+": 3, "?": 3}
RIGHT_ASSOC = {"*", "+", "?"}

def to_postfix(regex: str) -> List[str]:
    out, stack = [], []
    i = 0
    while i < len(regex):
        ch = regex[i]
        if ch == EPS:
            out.append(EPS)
        elif is_symbol(ch):
            out.append(ch)
        elif ch == "(":
            stack.append(ch)
        elif ch == ")":
            while stack and stack[-1] != "(":
                out.append(stack.pop())
            if not stack: raise ValueError("Paréntesis desbalanceados")
            stack.pop()
        elif ch in PRECEDENCE:
            while stack and stack[-1] != "(":
                top = stack[-1]
                if (top in PRECEDENCE and
                   (PRECEDENCE[top] > PRECEDENCE[ch] or
                   (PRECEDENCE[top] == PRECEDENCE[ch] and ch not in RIGHT_ASSOC))):
                    out.append(stack.pop())
                else:
                    break
            stack.append(ch)
        else:
            raise ValueError(f"Símbolo no soportado: {repr(ch)}")
        i += 1
    while stack:
        op = stack.pop()
        if op in {"(", ")"}: raise ValueError("Paréntesis desbalanceados al final")
        out.append(op)
    return out

# ----------------------- Thompson NFA -----------------------
_id = 0
def new_id() -> int:
    global _id
    _id += 1
    return _id

@dataclass(eq=False)
class State:
    id: int = field(default_factory=new_id)
    edges: Dict[str, Set["State"]] = field(default_factory=dict)
    def add_edge(self, sym: str, to_state: "State"):
        self.edges.setdefault(sym, set()).add(to_state)

@dataclass
class Fragment:  # para Thompson
    start: State
    accept: State

@dataclass
class NFA:
    start: State
    accept: State
    states: Set[State]

def thompson_from_postfix(post: List[str]) -> NFA:
    stack: List[Fragment] = []

    def sym_frag(s: str) -> Fragment:
        a, b = State(), State()
        a.add_edge(EPS if s == EPS else s, b)
        return Fragment(a, b)

    for tok in post:
        if tok == "|":
            b, a = stack.pop(), stack.pop()
            s, t = State(), State()
            s.add_edge(EPS, a.start); s.add_edge(EPS, b.start)
            a.accept.add_edge(EPS, t); b.accept.add_edge(EPS, t)
            stack.append(Fragment(s, t))
        elif tok == ".":
            b, a = stack.pop(), stack.pop()
            a.accept.add_edge(EPS, b.start)
            stack.append(Fragment(a.start, b.accept))
        elif tok == "*":
            a = stack.pop()
            s, t = State(), State()
            s.add_edge(EPS, a.start); s.add_edge(EPS, t)
            a.accept.add_edge(EPS, a.start); a.accept.add_edge(EPS, t)
            stack.append(Fragment(s, t))
        elif tok == "+":
            a = stack.pop()
            s, t = State(), State()
            s.add_edge(EPS, a.start)
            a.accept.add_edge(EPS, a.start); a.accept.add_edge(EPS, t)
            stack.append(Fragment(s, t))
        elif tok == "?":
            a = stack.pop()
            s, t = State(), State()
            s.add_edge(EPS, a.start); s.add_edge(EPS, t)
            a.accept.add_edge(EPS, t)
            stack.append(Fragment(s, t))
        else:
            stack.append(sym_frag(tok))

    if len(stack) != 1:
        raise RuntimeError("ER inválida (stack final != 1).")
    frag = stack.pop()

    # recolectar estados alcanzables
    visited: Set[State] = set()
    def dfs(u: State):
        if u in visited: return
        visited.add(u)
        for succs in u.edges.values():
            for v in succs: dfs(v)
    dfs(frag.start)
    return NFA(frag.start, frag.accept, visited)

# ----------------------- simulación (ε-cierre) -----------------------
def epsilon_closure(states: Set[State]) -> Set[State]:
    stack = list(states); closure = set(states)
    while stack:
        s = stack.pop()
        for v in s.edges.get(EPS, set()):
            if v not in closure:
                closure.add(v); stack.append(v)
    return closure

def move(states: Set[State], sym: str) -> Set[State]:
    out: Set[State] = set()
    for s in states:
        for v in s.edges.get(sym, set()):
            out.add(v)
    return out

def nfa_accepts(nfa: NFA, w: str) -> bool:
    current = epsilon_closure({nfa.start})
    for ch in w:
        current = epsilon_closure(move(current, ch))
        if not current: break
    return nfa.accept in current


def layout_positions(nfa: NFA):
    """Posiciones (x,y) por BFS desde el inicial (layout simple y estable)."""
    from collections import deque
    adj = {s: set() for s in nfa.states}
    for s in nfa.states:
        for dests in s.edges.values():
            adj[s] |= dests

    dist = {nfa.start: 0}
    q = deque([nfa.start])
    while q:
        u = q.popleft()
        for v in adj[u]:
            if v not in dist:
                dist[v] = dist[u] + 1
                q.append(v)

    maxd = max(dist.values()) if dist else 0
    for s in nfa.states:
        dist.setdefault(s, maxd)

    # agrupar por nivel
    levels = {}
    for s, d in dist.items():
        levels.setdefault(d, []).append(s)

    # asignar coordenadas
    pos = {}
    sep_x, sep_y = 2.4, 1.6
    for d in sorted(levels):
        ys = levels[d]
        n = len(ys)
        for i, s in enumerate(sorted(ys, key=lambda z: z.id)):
            # centrar en torno a 0 con separación vertical
            y = (i - (n - 1) / 2.0) * sep_y
            x = d * sep_x
            pos[s] = (x, y)
    return pos

def draw_nfa_matplotlib(nfa: NFA, filename_png: str):
    import matplotlib.pyplot as plt
    from matplotlib.patches import Circle, FancyArrowPatch, Arc

    pos = layout_positions(nfa)
    xs = [p[0] for p in pos.values()] + [-2]
    ys = [p[1] for p in pos.values()] + [0]
    x_min, x_max = min(xs) - 1.2, max(xs) + 1.2
    y_min, y_max = min(ys) - 1.2, max(ys) + 1.2

    fig, ax = plt.subplots(figsize=(max(6, (x_max - x_min) * 1.2),
                                    max(4, (y_max - y_min) * 1.2)))
    ax.set_xlim(x_min, x_max); ax.set_ylim(y_min, y_max)
    ax.axis('off')

    R = 0.28

    # nodos
    for s, (x, y) in pos.items():
        circ = Circle((x, y), R, fill=False, lw=2)
        ax.add_patch(circ)
        if s is nfa.accept:
            circ2 = Circle((x, y), R - 0.06, fill=False, lw=2)
            ax.add_patch(circ2)
        ax.text(x, y, str(s.id), ha='center', va='center', fontsize=10)

    # flecha de inicio
    x0, y0 = pos[nfa.start]
    arr = FancyArrowPatch((-2, y0), (x0 - R, y0), arrowstyle='->', lw=1.6,
                          mutation_scale=14)
    ax.add_patch(arr)

    # aristas
    for s, (x1, y1) in pos.items():
        for sym, dests in s.edges.items():
            for t in dests:
                x2, y2 = pos[t]
                if s is t:
                    # self-loop
                    arc = Arc((x1, y1 + R + 0.20), 0.8, 0.6, angle=0,
                              theta1=220, theta2=-40, lw=1.5)
                    ax.add_patch(arc)
                    ax.text(x1 + 0.05, y1 + R + 0.7, sym, fontsize=9)
                    continue
                # curva ligera si están en el mismo nivel para evitar solapado
                same_level = abs(y1 - y2) < 1e-9
                if same_level and x2 < x1:
                    # arco hacia atrás
                    ctrl = ((x1 + x2)/2.0, y1 + 0.6)
                else:
                    ctrl = None

                if ctrl:
                    # aproximación simple: dos segmentos
                    m1 = ((x1 + ctrl[0]) / 2, (y1 + ctrl[1]) / 2)
                    arr1 = FancyArrowPatch((x1 + (R if x2>x1 else -R), y1),
                                           m1, arrowstyle='-', lw=1.5,
                                           mutation_scale=12)
                    arr2 = FancyArrowPatch(m1, (x2 - (R if x2>x1 else -R), y2),
                                           arrowstyle='->', lw=1.5,
                                           mutation_scale=12)
                    ax.add_patch(arr1); ax.add_patch(arr2)
                    xm, ym = (x1 + x2)/2.0, (y1 + y2)/2.0 + 0.25
                    ax.text(xm, ym, sym, fontsize=9)
                else:
                    arr = FancyArrowPatch((x1, y1), (x2, y2),
                                          arrowstyle='->', lw=1.5,
                                          mutation_scale=12,
                                          shrinkA=12, shrinkB=12)
                    ax.add_patch(arr)
                    xm, ym = (x1 + x2)/2.0, (y1 + y2)/2.0 + 0.15
                    ax.text(xm, ym, sym, fontsize=9)

    fig.tight_layout()
    if not filename_png.lower().endswith(".png"):
        filename_png += ".png"
    fig.savefig(filename_png, dpi=150)
    plt.close(fig)
    print(f"Imagen guardada en: {filename_png}")

# ----------------------- front-end CLI -----------------------
def compile_regex_to_nfa(regex: str) -> NFA:
    global _id
    _id = 0
    s = add_concat(remove_spaces(regex))
    post = to_postfix(s)
    return thompson_from_postfix(post)

def main():
    parser = argparse.ArgumentParser(description="Thompson NFA + simulador + matplotlib")
    parser.add_argument("--input", required=True, help="Archivo con ER (una por línea)")
    parser.add_argument("--outdir", default="out_nfas", help="Carpeta de salida PNG")
    parser.add_argument("--word", default=None, help="Cadena única w para todas las ER")
    parser.add_argument("--words", default=None, help="Archivo con w por línea (paralelo a las ER)")
    args = parser.parse_args()

    os.makedirs(args.outdir, exist_ok=True)
    with open(args.input, "r", encoding="utf-8") as f:
        regexes = [ln.strip() for ln in f if ln.strip()]

    # preparar palabras
    words: List[Optional[str]] = []
    if args.word is not None:
        words = [args.word] * len(regexes)
    elif args.words is not None:
        with open(args.words, "r", encoding="utf-8") as f:
            words = [ln.rstrip("\n") for ln in f]
        if len(words) < len(regexes):
            words += [""] * (len(regexes) - len(words))
    else:
        for reg in regexes:
            w = input(f"Cadena w para `{reg}` (ENTER = ε): ")
            words.append(w)

    for i, (reg, w) in enumerate(zip(regexes, words), 1):
        print("\n" + "=" * 70)
        print(f"[{i}] ER: {reg}")
        nfa = compile_regex_to_nfa(reg)
        png = os.path.join(args.outdir, f"nfa_{i}.png")
        draw_nfa_matplotlib(nfa, png)
        w = "" if w is None else w
        print(f"w = {repr(w)}  ->  {'sí' if nfa_accepts(nfa, w) else 'no'}")

if __name__ == "__main__":
    main()
