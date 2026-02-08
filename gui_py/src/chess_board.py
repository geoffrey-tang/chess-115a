import tkinter as tk
import ttkbootstrap as ttk
import threading
import UCIEngine

# obviously just local to me will change this when our engine uci is working
engine_path = "/mnt/c/Users/eitan/Downloads/stockfish-windows-x86-64-avx2/stockfish/stockfish-windows-x86-64-avx2.exe"

class ChessGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Chess Board")

        self.square_size = 100
        self.menu_size = 400

        # Board orientation: False = white at bottom, True = black at bottom
        self.flipped = False

        # Colors
        # Feel free to mess with this
        self.light_square = "#eeeed2"
        self.dark_square = "#769656"

        self.drag_data = {"x": 0, "y": 0, "item": None}

        self.setup_ui()
        self.draw_board()
        self.menu()

    # initialization of tkinter frame and canvas objects
    def setup_ui(self):
        main_frame = ttk.Frame(self.root, padding=10)
        main_frame.pack()

        # Canvas for chess board
        self.canvas = tk.Canvas(
            main_frame,
            width=self.square_size * 8 + self.menu_size,
            height=self.square_size * 8,
        )
        self.canvas.pack()

        self.canvas.tag_bind("draggable", "<ButtonPress-1>", self.drag_start)
        self.canvas.tag_bind("draggable", "<B1-Motion>", self.drag_motion)
        self.canvas.tag_bind("draggable", "<ButtonRelease-1>", self.drag_release)

    # draw/ redraw the board using create_rectangle and arithmetic
    def draw_board(self):
        self.canvas.delete("square")  # only delete squares, not pieces

        # Draw squares (screen coordinates)
        for screen_row in range(8):
            for screen_col in range(8):
                x1 = screen_col * self.square_size
                y1 = screen_row * self.square_size
                x2 = x1 + self.square_size
                y2 = y1 + self.square_size

                # Convert to board coords to get correct color pattern
                board_row, board_col = self.screen_to_board(x1 + 1, y1 + 1)
                color = self.light_square if (board_row + board_col) % 2 == 1 else self.dark_square

                self.canvas.create_rectangle(x1, y1, x2, y2, fill=color, outline="", tags="square")

        # Keep squares below pieces
        self.canvas.tag_lower("square")
    
    def load_images(self):
        self.images = {}
        for color in ("w", "b"):
            for piece in ("p", "r", "n", "b", "q", "k"):
                key = f"{color}{piece}"
                img = tk.PhotoImage(file=f"pieces/{key}.png")

                scale = img.width() // 80
                if scale > 1:
                    img = img.subsample(scale, scale)

                self.images[key] = img

    def create_piece(self, row, col, piece_code, iswhite):
        x, y = self.board_to_screen(row, col)

        piece = self.canvas.create_image(
                x, y,
                image=self.images[piece_code],
                tags=("piece", "draggable", piece_code)
        )

        self.pieces[piece] = (row, col, piece_code, iswhite)

    def create_all_pieces(self):
        self.pieces = {}
        # Pawns
        for col in range(8):
            self.create_piece(1, col, "wp", iswhite=1)
            self.create_piece(6, col, "bp", iswhite=0)

        # Rooks
        self.create_piece(0, 0, "wr", iswhite=1)
        self.create_piece(0, 7, "wr", iswhite=1)
        self.create_piece(7, 0, "br", iswhite=0)
        self.create_piece(7, 7, "br", iswhite=0)

        # Knights
        self.create_piece(0, 1, "wn", iswhite=1)
        self.create_piece(0, 6, "wn", iswhite=1)
        self.create_piece(7, 1, "bn", iswhite=0)
        self.create_piece(7, 6, "bn", iswhite=0)

        # Bishops
        self.create_piece(0, 2, "wb", iswhite=1)
        self.create_piece(0, 5, "wb", iswhite=1)
        self.create_piece(7, 2, "bb", iswhite=0)
        self.create_piece(7, 5, "bb", iswhite=0)

        # Queens
        self.create_piece(0, 3, "wq", iswhite=1)
        self.create_piece(7, 3, "bq", iswhite=0)

        # Kings
        self.create_piece(0, 4, "wk", iswhite=1)
        self.create_piece(7, 4, "bk", iswhite=0)

    def drag_start(self, event):
        # Prevent moves while engine is thinking
        if self.engine_thinking:
            return
        item = self.canvas.find_closest(event.x, event.y)[0]
        # Checks whose turn it is when allowing drag
        if "piece" not in self.canvas.gettags(item) or self.whites_turn != self.pieces[item][3]:
            return

        self.drag_data["item"] = item
        self.drag_data["x"] = event.x
        self.drag_data["y"] = event.y

    def drag_motion(self, event):
        item = self.drag_data["item"]
        if item is None:
            return

        dx = event.x - self.drag_data["x"]
        dy = event.y - self.drag_data["y"]

        self.canvas.move(item, dx, dy)

        self.drag_data["x"] = event.x
        self.drag_data["y"] = event.y

    # implements post move logic:
    # peice capturing
    # saving move to move history list
    # starting engine searching
    def drag_release(self, event):
        item = self.drag_data["item"]
        if item is None:
            return

        cx, cy = self.canvas.coords(item)

        # convert screen position to board coordinates
        row, col = self.screen_to_board(cx, cy)
        row = max(0, min(7, row))
        col = max(0, min(7, col))

        # Convert back to screen position for snapping
        target_x, target_y = self.board_to_screen(row, col)

        dx = target_x - cx
        dy = target_y - cy

        # capturing logic
        occupant = self.get_piece_at(row, col)
        if occupant is not None and self.whites_turn != self.pieces[occupant][3]:
            # a piece is already there, capture it
            self.canvas.delete(occupant)
            del self.pieces[occupant]

        self.canvas.move(item, dx, dy)

        # save move in UCI format: "e2e4"
        old_row, old_col = self.pieces[item][0], self.pieces[item][1]
        origin_square = self.colToFile(old_col) + str(old_row + 1)
        dest_square = self.colToFile(col) + str(row + 1)
        self.move_history.append(f"{origin_square}{dest_square}")

        self.pieces[item] = (row, col, self.pieces[item][2], self.pieces[item][3])
        self.drag_data["item"] = None

        self.whites_turn = not self.whites_turn

        # engine responds after player's move in a background thread
        if not self.whites_turn:  # engine plays black
            self.engine_thinking = True
            threading.Thread(target=self.engine_think, daemon=True).start()

    # ui/menu drawing 
    def menu(self):
        y_margins = 50

        x1 = self.square_size * 8
        y1 = 0
        x2 = x1 + self.menu_size
        y2 = self.square_size * 8
        self.canvas.create_rectangle(x1, y1, x2, y2, fill="#FFFFFF", outline = "")

        # Play game btn
        play_button = ttk.Button(self.root, text= "Play a game/reset", command=self.game_started)
        self.canvas.create_window(x1 + self.menu_size // 2, y_margins , window=play_button)
        # Flip board btn
        flip_button = ttk.Button(self.root, text= "Do a flip!", command=self.flip_board)
        self.canvas.create_window(x1 + self.menu_size // 2, 2*y_margins , window=flip_button)

    # main game loop
    def game_started(self):
        # engine path, just btw this path format is wsl specific
        self.engine = UCIEngine.UCIEngine(engine_path)
        self.draw_board()
        self.load_images()
        self.create_all_pieces()
        self.menu()
        self.whites_turn = True
        self.move_history = []
        self.engine_thinking = False

    def flip_board(self):
        self.flipped = not self.flipped
        self.draw_board()
        for item, (row, col, piece_code, iswhite) in self.pieces.items():
            x, y = self.board_to_screen(row, col)
            self.canvas.coords(item, x, y)

    # converts row and column board coordinates to screen-pixel coordinates
    def board_to_screen(self, row, col):
        if self.flipped:
            screen_row = row
            screen_col = 7 - col
        else:
            screen_row = 7 - row
            screen_col = col
        x = screen_col * self.square_size + self.square_size // 2
        y = screen_row * self.square_size + self.square_size // 2
        return x, y

    # converts screen-pixel coordinates to row, column board coordinates
    def screen_to_board(self, x, y):
        screen_col = int(x // self.square_size)
        screen_row = int(y // self.square_size)
        if self.flipped:
            row = screen_row
            col = 7 - screen_col
        else:
            row = 7 - screen_row
            col = screen_col
        return row, col

    ## helper functions

    # column number to file letter
    def colToFile(self, col):
        if col < 0 or col > 7:
            raise ValueError(f"Column must be 0-7, got {col}")
        return chr(ord('a') + col)

    # file letter to column number
    def fileToCol(self, file):
        return ord(file) - ord('a')

    def get_piece_at(self, row, col):
        for item, (r, c, piece_code, iswhite) in self.pieces.items():
            if r == row and c == col:
                return item
        return None

    # UCI input functions
    def parseUciMove(self, uci_move):
        from_col = self.fileToCol(uci_move[0])
        from_row = int(uci_move[1]) - 1
        to_col = self.fileToCol(uci_move[2])
        to_row = int(uci_move[3]) - 1
        return (from_row, from_col), (to_row, to_col)

    def make_move(self, uci_move):
        (from_row, from_col), (to_row, to_col) = self.parseUciMove(uci_move)

        item = self.get_piece_at(from_row, from_col)
        if item is None:
            return

        occupant = self.get_piece_at(to_row, to_col)
        if occupant is not None:
            self.canvas.delete(occupant)
            del self.pieces[occupant]

        x, y = self.board_to_screen(to_row, to_col)
        self.canvas.coords(item, x, y)

        self.move_history.append(uci_move)
        self.pieces[item] = (to_row, to_col, self.pieces[item][2], self.pieces[item][3])
        self.whites_turn = not self.whites_turn

    # Thread stuff: 
    # if you don't use threads, calling the engine
    # for moves freezes everything else. Not good
    def engine_think(self):
        self.pending_move = self.engine.get_move(self.move_history)
        # tkinter function to keep things thread-safe
        self.root.after(0, self.finish_engine_move)

    def finish_engine_move(self):
        self.make_move(self.pending_move)
        self.engine_thinking = False

