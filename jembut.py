import time
from collections import deque
import heapq
from itertools import count
import matplotlib.pyplot as plt

EASY = [
    "000002890280060314000000000130650907008197023500238001705080600824000000060905740",
    "000000580010320960002900340703080609098031700150609800046053000087090406001840005",
    "037659002409830050060000000390725468004060300506000009008090004642087003903206500",
    "201097503780605009050134708000243006000061850060708100027000095590370680000500040",
    "018002047905000000734918200591080700072001038006047591100009065060130002203400010",
    "534018296078000135106325800702003400903450028001200350000000080080036000319500047",
    "500310067300549008000086054050090400010465039069230501931008042607123000005074010",
    "100004708287510649049278510000907000305482190070100000096725430002001065504009002",
    "890120000020800693053796002704209506500461270200007084940000328002040951385012000",
    "100340792792150004030972650653290010080530946470060200000029578907605100500703000"
]

MEDIUM = [
    "006000000090031700400050006984000602600102400000008950060340129050010804000007500",
    "510000603007001000400000108750012000084090020903080016000050302045008700001200905",
    "045000060007049230000050000000502390300001002001090000089020150500968724720010006",
    "025043000093010060000000953014630708000005001007000530748102006102090870000000015",
    "800091540100060098974030216000749005008006004000000602735002001000003020089014000",
    "003098025005160079000000000000001908090400713371000000060250097002600034000847200",
    "709065000002000000000800500230600000076450009095000086640003758807006300003007024",
    "027050030090070608060040721000004000300500260685032410000027000070690340030410000",
    "980040600703051080000000000500807200040000000320190050809005761274000000056000320",
    "080920070060178094000000210700260800090700421500809003900087540000600007007540080"
]

HARD = [
    "900050107703000480000094006017000300000100000004029001079000000601003000000081970",
    "104600357000070000090001006035000060019403500020000943000004002040009000068005000",
    "085090300960003150002000600039007001000004000010805700701000800004001005050080207",
    "000104002500000900000030400010009008000043000800500006300018005085306710000070600",
    "800070002000054090014300075040000008300800000000000920000908703403700000060230500",
    "001520690204006000000001007000700001000130050038000000000803902080000000302450718",
    "302070010005090007400001800006000000000050208000900040050007093080500100090200700",
    "009300200700095000040000000000078001600010900907500003003000804106000750004850000",
    "050010000430000708600003100020638007003100000500794200090080032005002000800007009",
    "060008040300040007200003005000400570900060480006000000400127903000059100000000708"
]

EXTRA_HARD = [
    "000000800000217000310080000043026000090000047500009080000040098000071200005900010",
    "502400060030080000000500000060000807003006010009100032004021500300670000000300020",
    "000300806000000090008600230020100600000960000000002078637000500840000000500809300",
    "200100500060000009051000026180007400090000370000050000800000000400098000902070001",
    "090000080000530100710002000020950000600100000001000007000780036000060450030010009",
    "800001000000080070000034906000020000160000740480100003020000400300600507600005039",
    "000603008050710000000800004004300500008900000091000800045130072000020910070000000",
    "502000074003700108009020000000600000205010030000070010007160009900000050008000201",
    "030800000402009000000070000070600350500400280000002600000048730900000006080003905",
    "090200010000000308100040000201000900000080530000000700403908000008050090010030070"
]

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


def compare():
    problems = {}

    for i in range (0,10):
        problems[f"sudoku EZ {i}"] = (lambda: build_sudoku(EASY[i]), is_valid_sudoku)

    for i in range(0,10):
        problems[f"sudoku MED {i}"] = (lambda: build_sudoku(MEDIUM[i]), is_valid_sudoku)

    for i in range(0,10):
        problems[f"sudoku HRD {i}"] = (lambda: build_sudoku(HARD[i]), is_valid_sudoku)

    for i in range(0,10):
        problems[f"sudoku EHRD {i}"] = (lambda: build_sudoku(EXTRA_HARD[i]), is_valid_sudoku)

    result_easy_3 = []
    result_easy_new = []
    result_medium_3 = []
    result_medium_new = []
    result_hard_3 = []
    result_hard_new = []
    result_extra_hard_3 = []
    result_extra_hard_new = []

    print(f"{'masalah':14s}{'algoritma':10s}{'arcs':>10s}{'checks':>10s}{'backtracks':>12s}{'ms':>10s}  valid")
    for name, (build_fn, check_fn) in problems.items():
        for algo_name, ac_fn in [("AC-3", ac3), ("AC-New", ac_new)]:
            result, counter, seconds = solve(build_fn, ac_fn)
            ok = check_fn(result)
            ms = seconds * 1000
            print(f"{name:14s}{algo_name:10s}{counter['arcs']:10d}{counter['checks']:10d}{counter['backtracks']:12d}{ms:10.2f}  {ok}")

            if name.startswith("sudoku EZ"):
                if algo_name == "AC-3":
                    result_easy_3.append(ms)
                elif algo_name == "AC-New":
                    result_easy_new.append(ms)

            elif name.startswith("sudoku MED"):
                if algo_name == "AC-3":
                    result_medium_3.append(ms)
                elif algo_name == "AC-New":
                    result_medium_new.append(ms)

            elif name.startswith("sudoku HRD"):
                if algo_name == "AC-3":
                    result_hard_3.append(ms)
                elif algo_name == "AC-New":
                    result_hard_new.append(ms)

            elif name.startswith("sudoku EHRD"):
                if algo_name == "AC-3":
                    result_extra_hard_3.append(ms)
                elif algo_name == "AC-New":
                    result_extra_hard_new.append(ms)

    result = {
        "EASY": sum(result_easy_3)/10,
        "MEDIUM": sum(result_medium_3)/10,
        "HARD": sum(result_hard_3)/10,
        "EXTRA_HARD": sum(result_extra_hard_3)/10,
    }

    result_new = {
        "EASY": sum(result_easy_new) / len(result_easy_new),
        "MEDIUM": sum(result_medium_new) / len(result_medium_new),
        "HARD": sum(result_hard_new) / len(result_hard_new),
        "EXTRA_HARD": sum(result_extra_hard_new) / len(result_extra_hard_new)
    }

    plt.plot(
        list(result.keys()),
        list(result.values()),
        marker="o",
        label="AC-3"
    )

    plt.plot(
        list(result_new.keys()),
        list(result_new.values()),
        marker="s",
        label="AC-New"
    )

    plt.xlabel("Sudoku Difficulty")
    plt.ylabel("Average Execution Time (ms)")
    plt.title("AC-3 vs AC-New")
    plt.legend()
    plt.grid(True)
    plt.show()

if __name__ == "__main__":
    compare()
