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