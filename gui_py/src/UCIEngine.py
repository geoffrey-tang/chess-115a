import subprocess

# subprocess library: https://docs.python.org/3/library/subprocess.html
# UCI reference: https://backscattering.de/chess/uci/

class UCIEngine:
    def __init__(self, engine_path):
        self.engine = subprocess.Popen(
            engine_path,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            text=True
        )
        self.send("uci")
        self.receive("uciok")
        self.send("isready")
        self.receive("readyok")

    def send(self, command):
        self.engine.stdin.write(command + "\n")
        self.engine.stdin.flush()
    
    def receive(self, string):
        while 1:
            line_read = self.engine.stdout.readline()
            if string in line_read:
                return line_read
            
    def search(self, movetime_ms=3000):
        self.send("isready")
        self.receive("readyok")
        self.send(f"go movetime {movetime_ms}")
        return self.receive("bestmove").split()[1]
    
    def get_pos(self, fen_str, movetime_ms=3000):
        self.send(f"position fen {fen_str}")
        return self.search(movetime_ms)
    
    def get_move(self, moves, movetime_ms=3000):
        if moves:
            moves_str = " ".join(moves)
            self.send(f"position startpos moves {moves_str}")
        else:
            self.send("position startpos")
        return self.search(movetime_ms)

    def quit(self):
        try:
            self.send("quit")
            self.engine.wait(timeout=2)
        except Exception:
            self.engine.kill()

    def analyze(self, movetime_ms = 300):
        """
        Ask engine for evaluation + principal variation.
        Returns dict: { score: str, pv: [moves] }
        """

        self.send("isready")
        self.wait_ready()

        self.send(f"go movetime {movetime_ms}")

        score = None
        best_pv = []
        best_move = None

        while True:
            line = self.engine.stdout.readline().strip()

            if not line:
                continue

            if line.startswith("info"):
                parts = line.split()

                if "score" in parts:
                    try:
                        idx = parts.index("score")
                        if parts[idx + 1] == "cp":
                            score = int(parts[idx + 2]) / 100
                        elif parts[idx + 1] == "mate":
                            score = f"Mate in {parts[idx + 2]}"
                    except:
                        pass

                if "pv" in parts: 
                    best_pv = parts[parts.index("pv") + 1:]
            
            if line.startswith("bestmove"):
                best_move = line.split()[1]
                break
            
        return {"score": score, "pv": best_pv, "best_move": best_move}

    def wait_ready(self):
        while True:
            line = self.engine.stdout.readline().strip()
            if line == "readyok":
                break
