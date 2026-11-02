import time
from collections import deque
import heapq
from itertools import count
import tkinter as tk
from tkinter import ttk
import matplotlib.pyplot as plt
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import csv

PUZZLES = {"EASY": [], "MEDIUM": [], "HARD": [], "EXTRA_HARD": []}
with open("data/sudoku_data.csv", newline="") as f:
    for row in csv.DictReader(f):
        PUZZLES[row["difficulty"]].append(row["puzzle"])

EASY = PUZZLES["EASY"]
MEDIUM = PUZZLES["MEDIUM"]
HARD = PUZZLES["HARD"]
EXTRA_HARD = PUZZLES["EXTRA_HARD"]

def build_sudoku(puzzle):
    domains = {}
    neighbors = {}
    for r in range(9):
        for c in range(9):
            ch = puzzle[r * 9 + c]
            domains[(r, c)] = set(range(1, 10)) if ch == "0" else {int(ch)}
            row = {(r, k) for k in range(9)}
            col = {(k, c) for k in range(9)}

            br, bc = 3 * (r // 3), 3 * (c // 3)

            box = {(br + i, bc + j) for i in range(3) for j in range(3)}
            neighbors[(r, c)] = (row | col | box) - {(r, c)}

    return domains, neighbors

def revise(domains, xi, xj, counter):
    counter["checks"] += len(domains[xi])
    removed = False

    for x in list(domains[xi]):
        if not any(x != y for y in domains[xj]):
            domains[xi].discard(x)
            removed = True
    return removed


def ac3(domains, neighbors, assigned, counter):
    queue = deque((xi, xj) for xi in neighbors for xj in neighbors[xi])
    in_queue = set(queue)
    while queue:
        xi, xj = queue.popleft()
        in_queue.discard((xi, xj))
        counter["arcs"] += 1

        if revise(domains, xi, xj, counter):
            if len(domains[xi]) == 0:
                return False
            for xk in neighbors[xi]:
                if xk != xj and (xk, xi) not in in_queue:
                    queue.append((xk, xi))
                    in_queue.add((xk, xi))
    return True

def arc_priority(domains, neighbors, xi, xj):
    di = len(domains[xi])
    s_factor = len(domains[xj]) / di
    crisis = len(neighbors[xi]) / di
    return (s_factor, -crisis)

def ac_new(domains, neighbors, assigned, counter):
    tie = count()

    heap = [(*arc_priority(domains, neighbors, xi, xj), next(tie), xi, xj) for xi in neighbors if xi not in assigned for xj in neighbors[xi]]
    heapq.heapify(heap)
    in_queue = {(xi, xj) for _, _, _, xi, xj in heap}

    while heap:
        _, _, _, xi, xj = heapq.heappop(heap)
        in_queue.discard((xi, xj))
        counter["arcs"] += 1

        if revise(domains, xi, xj, counter):
            if not domains[xi]:
                return False
            for xk in neighbors[xi]:
                if xk != xj and xk not in assigned and (xk, xi) not in in_queue:
                    heapq.heappush(
                        heap,
                        (*arc_priority(domains, neighbors, xk, xi), next(tie), xk, xi),
                    )
                    in_queue.add((xk, xi))
    return True

def backtrack(domains, neighbors, assigned, ac_fn, counter):
    if len(assigned) == len(domains) :
        return dict(assigned)

    var = next(v for v in domains if v not in assigned)

    for value in sorted(domains[var]):
        new_domains = {v: set(d) for v, d in domains.items()}
        new_domains[var] = {value}
        new_assigned = {**assigned, var: value}

        if ac_fn(new_domains,  neighbors, new_assigned, counter):
            result = backtrack(new_domains, neighbors, new_assigned, ac_fn, counter)
            if result is not None:
                return result
        counter["backtracks"] += 1
    return None


def solve(build_fn, ac_fn):
    domains, neighbors = build_fn()
    counter = {"arcs": 0, "checks": 0, "backtracks": 0}
    start = time.perf_counter()
    if not ac_fn(domains, neighbors, {}, counter):
        return None, counter, time.perf_counter() - start
    result = backtrack(domains, neighbors, {}, ac_fn, counter)
    return result, counter, time.perf_counter() - start

def is_valid_sudoku(assignment):
    if assignment is None:
        return False
    full = set(range(1, 10))
    grid = [[assignment[(r,c)] for c in range(9)] for r in range(9)]
    rows_ok = all(set(grid[r]) == full for r in range(9))
    cols_ok = all(set(grid[r][c] for r in range(9)) == full for c in range(9))
    boxes_ok = all(set(grid[br * 3 + i][bc * 3 + j] for i in range(3) for j in range(3)) == full for br in range(3) for bc in range(3))
    return rows_ok and cols_ok and boxes_ok


def is_valid_map(neighbors, assignment):
    if assignment is None or len(assignment) != len(neighbors) or any(assignment[x] is None for x in neighbors):
        return False
    return all(assignment[x] != assignment[y] for x in neighbors for y in neighbors[x])

LARGEFONT =("Verdana", 35)

class tkinterApp(tk.Tk):
    
    def __init__(self, *args, **kwargs): 
        tk.Tk.__init__(self, *args, **kwargs)
        container = tk.Frame(self)  
        container.pack(side = "top", fill = "both", expand = True) 
        container.grid_rowconfigure(0, weight = 1)
        container.grid_columnconfigure(0, weight = 1)
        self.frames = {}  

        for F in (StartPage, LoadingPage, PlotPage, Page2):
            frame = F(container, self)
            self.frames[F] = frame 
            frame.grid(row = 0, column = 0, sticky ="nsew")

        self.show_frame(StartPage)

    def show_frame(self, cont):
        for F, f in self.frames.items():
            if F is not cont:
                f.grid_remove()

        frame = self.frames[cont]
        frame.grid()
        frame.tkraise()
        self.update_idletasks()          
        frame.event_generate("<<ShowFrame>>")


class StartPage(tk.Frame):    
    def __init__(self, parent, controller): 
        tk.Frame.__init__(self, parent)
        v = tk.IntVar()

        header = tk.Label(self, text = "Sudoku Solver", font=("Arial", 12, "bold"))

        label = tk.Label(self, text="Comparing the original AC-3 with AC-3 Modification with Sudoku")
        header.pack(side="top")
        label.pack(side="top")
        tk.Radiobutton(self, text="Compare AC-3 with AC-3 modification with ready to use data", variable=v, value=1, command=lambda : controller.show_frame(LoadingPage)).pack(anchor=tk.W)
        tk.Radiobutton(self, text="Input your own data", variable=v, value=2, command=lambda : controller.show_frame(Page2)).pack(anchor=tk.W)

class LoadingPage(tk.Frame):
    def __init__(self, parent, controller):
        tk.Frame.__init__(self, parent)
        self.controller = controller
        tk.Label(self, text="Menjalankan perbandingan...").pack(pady=(120, 10))
        self.progress = ttk.Progressbar(self, orient="horizontal", length=300, mode="determinate")
        self.progress.pack()
        self.bind("<<ShowFrame>>", self.on_show)

    def on_show(self, event):
        self.progress['value'] = 0
        self.after(100, self.compare)

    def compare(self):
        sets = {"EASY": EASY, "MEDIUM": MEDIUM, "HARD": HARD, "EXTRA_HARD": EXTRA_HARD}
        algos = [("AC-3", ac3), ("AC-New", ac_new)]
        times = {name: {lvl: [] for lvl in sets} for name, _ in algos}
        total = len(sets) * 10 * len(algos)

        for level, puzzles in sets.items():
            for p in puzzles:
                for algo_name, ac_fn in algos:
                    result, counter, seconds = solve(lambda: build_sudoku(p), ac_fn)
                    times[algo_name][level].append(seconds * 1000)
                    self.progress['value'] += 100 / total
                    self.update_idletasks()

        self.controller.results = {
            algo: {lvl: sum(v) / len(v) for lvl, v in d.items()}
            for algo, d in times.items()
        }
        self.controller.show_frame(PlotPage)


class PlotPage(tk.Frame):
    def __init__(self, parent, controller):
        tk.Frame.__init__(self, parent)
        self.controller = controller

        self.fig = Figure(figsize=(6, 4), dpi=100)
        self.ax = self.fig.add_subplot(111)
        self.canvas = FigureCanvasTkAgg(self.fig, master=self)
        self.canvas.get_tk_widget().pack(fill="both", expand=True)

        ttk.Button(self, text="Back", command=lambda: controller.show_frame(StartPage)).pack(pady=5)
        self.bind("<<ShowFrame>>", self.on_show)

    def on_show(self, event):
        results = self.controller.results
        self.ax.clear()
        markers = {"AC-3": "o", "AC-New": "s"}
        for algo, data in results.items():
            self.ax.plot(list(data.keys()), list(data.values()), marker=markers[algo], label=algo)
        self.ax.set_xlabel("Sudoku Difficulty")
        self.ax.set_ylabel("Average Execution Time (ms)")
        self.ax.set_title("AC-3 vs AC-New")
        self.ax.legend()
        self.ax.grid(True)
        self.canvas.draw()

class Page2(tk.Frame): 
    def __init__(self, parent, controller):
        tk.Frame.__init__(self, parent)
        label = ttk.Label(self, text ="Page 2", font = LARGEFONT)
        label.grid(row = 0, column = 4, padx = 10, pady = 10)
        button1 = ttk.Button(self, text ="Page 1",
                            command = lambda : controller.show_frame(Page1))

        button1.grid(row = 1, column = 1, padx = 10, pady = 10)
        button2 = ttk.Button(self, text ="Startpage",
                            command = lambda : controller.show_frame(StartPage))

        button2.grid(row = 2, column = 1, padx = 10, pady = 10)

app = tkinterApp()
app.title("Sudoku Solver")
app.mainloop()