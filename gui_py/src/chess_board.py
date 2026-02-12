import tkinter as tk
import ttkbootstrap as ttk
import threading
import UCIEngine
import chess

# obviously just local to me will change this when our engine uci is working
engine_path = "/usr/games/stockfish"

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
        # remove all pieces from canvas
        self.canvas.delete("piece")
        self.pieces = {}

        for square, piece in self.board.piece_map().items():
            row, col = chess.square_rank(square), chess.square_file(square)
            piece_code = ("w" if piece.color == chess.WHITE else "b") + piece.symbol().lower()
            self.create_piece(row, col, piece_code, piece.color)

    def drag_start(self, event):
        # Prevent moves while engine is thinking
        if self.engine_thinking:
            return
        
        item = self.canvas.find_closest(event.x, event.y)[0]
        # Checks whose turn it is when allowing drag
        if "piece" not in self.canvas.gettags(item):
            return

        row, col = self.pieces[item][0], self.pieces[item][1]
        square = self.board_to_chess_square(row, col)

        piece = self.board.piece_at(square)

        if piece is None or piece.color != self.board.turn:
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
        if item is None or self.engine_thinking:
            return

        cx, cy = self.canvas.coords(item)

        # convert screen position to board coordinates
        row, col = self.screen_to_board(cx, cy)
        row = max(0, min(7, row))
        col = max(0, min(7, col))

        old_row, old_col = self.pieces[item][0], self.pieces[item][1]

        from_sq = self.board_to_chess_square(old_row, old_col)
        to_sq = self.board_to_chess_square(row, col)

        move = chess.Move(from_sq, to_sq)

        piece = self.board.piece_at(from_sq)

        if piece and piece.piece_type == chess.PAWN and row in (0, 7):
            move = chess.Move(from_sq, to_sq, promotion=chess.QUEEN)

        if move not in self.board.legal_moves:

            x, y = self.board_to_screen(old_row, old_col)
            self.canvas.coords(item, x, y)
            self.drag_data["item"] = None
            return

        self.board.push(move)
        self.create_all_pieces()

        self.drag_data["item"] = None

        if self.board.turn == chess.BLACK:
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
        self.board = chess.Board()
        self.draw_board()
        self.load_images()
        self.create_all_pieces()
        self.menu()
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

        self.pieces[item] = (to_row, to_col, self.pieces[item][2], self.pieces[item][3])

    # Thread stuff: 
    # if you don't use threads, calling the engine
    # for moves freezes everything else. Not good
    def engine_think(self):
        uci_moves = [m.uci() for m in self.board.move_stack]
        self.pending_move = self.engine.get_move(uci_moves)
        # tkinter function to keep things thread-safe
        self.root.after(0, self.finish_engine_move)

    def finish_engine_move(self):
        self.make_move(self.pending_move)

        if move in self.board.legal_moves:
            self.board.push(move)
            self.sync_gui_with_board()

        self.engine_thinking = False

    def board_to_chess_square(self, row, col):
        return chess.square(col, row)

    def chess_square_to_board(self, square):
        return chess.square_rank(square), chess.square_file(square)


