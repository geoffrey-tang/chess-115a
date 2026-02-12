import os
import tkinter as tk
import ttkbootstrap as ttk
import threading
import chess
import UCIEngine

engine_path = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "build", "chess_cli"))

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
        self.editing = False
        self.palette_height = 2 * self.square_size + 40

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
        item = self.canvas.find_closest(event.x, event.y)[0]

        if self.editing:
            # In editor mode, allow dragging any piece freely
            if "piece" not in self.canvas.gettags(item):
                return
            self.drag_data["item"] = item
            self.drag_data["x"] = event.x
            self.drag_data["y"] = event.y
            return

        # Prevent moves while engine is thinking
        if self.engine_thinking:
            return
        # Only allow dragging the player's pieces on their turn
        piece_is_white = self.pieces.get(item, (0, 0, "", 0))[3]
        if "piece" not in self.canvas.gettags(item):
            return
        if piece_is_white != self.player_is_white or self.whites_turn != piece_is_white:
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

        if self.editing:
            board_width = self.square_size * 8
            board_height = self.square_size * 8

            # If dropped on the board, snap to grid
            if 0 <= cx < board_width and 0 <= cy < board_height:
                row, col = self.screen_to_board(cx, cy)
                row = max(0, min(7, row))
                col = max(0, min(7, col))

                # Remove any existing piece at that square
                occupant = self.get_piece_at(row, col)
                if occupant is not None and occupant != item:
                    self.canvas.delete(occupant)
                    del self.pieces[occupant]

                target_x, target_y = self.board_to_screen(row, col)
                self.canvas.coords(item, target_x, target_y)
                self.pieces[item] = (row, col, self.pieces[item][2], self.pieces[item][3])
            else:
                # Dragged off the board — remove the piece
                self.canvas.delete(item)
                del self.pieces[item]

            self.drag_data["item"] = None
            return

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
        if self.whites_turn != self.player_is_white:
            self.engine_thinking = True
            threading.Thread(target=self.engine_think, daemon=True).start()

    def clear_menu(self):
        self.canvas.delete("menu_item")

    # ui/menu drawing
    def menu(self):
        self.editing = False
        self.canvas.delete("palette")
        self.canvas.config(height=self.square_size * 8)
        self.clear_menu()
        y_margins = 50

        x1 = self.square_size * 8
        y1 = 0
        x2 = x1 + self.menu_size
        y2 = self.square_size * 8
        self.canvas.create_rectangle(x1, y1, x2, y2, fill="#FFFFFF", outline="", tags="menu_item")

        # Play color dropdown
        if not hasattr(self, "play_color"):
            self.play_color = tk.StringVar(value="Play as White")
        color_options = ["Play as White", "Play as Black"]
        color_menu = tk.OptionMenu(self.root, self.play_color, *color_options)
        self.canvas.create_window(x1 + self.menu_size // 2, y_margins, window=color_menu, tags="menu_item")

        # Play game btn
        play_button = ttk.Button(self.root, text="Play a game/reset", command=self.game_started)
        self.canvas.create_window(x1 + self.menu_size // 2, 2 * y_margins, window=play_button, tags="menu_item")
        # Flip board btn
        flip_button = ttk.Button(self.root, text="Do a flip!", command=self.flip_board)
        self.canvas.create_window(x1 + self.menu_size // 2, 3 * y_margins, window=flip_button, tags="menu_item")
        # Board Editor btn
        editor_button = ttk.Button(self.root, text="Board Editor", command=self.board_editor)
        self.canvas.create_window(x1 + self.menu_size // 2, 4 * y_margins, window=editor_button, tags="menu_item")

    def board_editor(self, _value=None):
        self.editing = True
        self.clear_menu()
        self.canvas.delete("piece")
        self.canvas.delete("palette")

        # Expand canvas to fit palette below the board
        board_height = self.square_size * 8
        self.canvas.config(height=board_height + self.palette_height)

        self.draw_board()
        self.load_images()
        self.create_all_pieces()
        self.draw_palette()

        y_margins = 50

        x1 = self.square_size * 8
        y1 = 0
        x2 = x1 + self.menu_size
        y2 = board_height + self.palette_height
        self.canvas.create_rectangle(x1, y1, x2, y2, fill="#FFFFFF", outline="", tags="menu_item")

        # Back button
        back_button = ttk.Button(self.root, text="Back", command=self.menu)
        self.canvas.create_window(x1 + self.menu_size // 2, y_margins, window=back_button, tags="menu_item")

        # Side to play dropdown
        self.selected_side = tk.StringVar(value="White to play")
        options = ["White to play", "Black to play"]
        option_menu = tk.OptionMenu(self.root, self.selected_side, *options)
        self.canvas.create_window(x1 + self.menu_size // 2, 2 * y_margins, window=option_menu, tags="menu_item")

        # Castling rights label
        castling_label = tk.Label(self.root, text="Castling Rights", bg="#FFFFFF")
        self.canvas.create_window(x1 + self.menu_size // 2, 3 * y_margins, window=castling_label, tags="menu_item")

        # Castling rights checkboxes
        self.white_kingside = tk.BooleanVar(value=True)
        self.white_queenside = tk.BooleanVar(value=True)
        self.black_kingside = tk.BooleanVar(value=True)
        self.black_queenside = tk.BooleanVar(value=True)

        center = x1 + self.menu_size // 2

        # White row
        white_label = tk.Label(self.root, text="White", bg="#FFFFFF")
        self.canvas.create_window(center - 80, 3.5 * y_margins, window=white_label, tags="menu_item")
        white_oo = ttk.Checkbutton(self.root, text="O-O", variable=self.white_kingside)
        self.canvas.create_window(center + 10, 3.5 * y_margins, window=white_oo, tags="menu_item")
        white_ooo = ttk.Checkbutton(self.root, text="O-O-O", variable=self.white_queenside)
        self.canvas.create_window(center + 90, 3.5 * y_margins, window=white_ooo, tags="menu_item")

        # Black row
        black_label = tk.Label(self.root, text="Black", bg="#FFFFFF")
        self.canvas.create_window(center - 80, 4 * y_margins, window=black_label, tags="menu_item")
        black_oo = ttk.Checkbutton(self.root, text="O-O", variable=self.black_kingside)
        self.canvas.create_window(center + 10, 4 * y_margins, window=black_oo, tags="menu_item")
        black_ooo = ttk.Checkbutton(self.root, text="O-O-O", variable=self.black_queenside)
        self.canvas.create_window(center + 90, 4 * y_margins, window=black_ooo, tags="menu_item")

        # Action buttons
        reset_button = ttk.Button(self.root, text="Reset to start", command=self.reset_editor)
        self.canvas.create_window(center, 5.5 * y_margins, window=reset_button, tags="menu_item")

        clear_button = ttk.Button(self.root, text="Clear board", command=self.clear_board)
        self.canvas.create_window(center, 6.5 * y_margins, window=clear_button, tags="menu_item")

        flip_button = ttk.Button(self.root, text="Flip board", command=self.flip_board)
        self.canvas.create_window(center, 7.5 * y_margins, window=flip_button, tags="menu_item")

        continue_button = ttk.Button(self.root, text="Continue from here", command=self.continue_from_editor)
        self.canvas.create_window(center, 8.5 * y_margins, window=continue_button, tags="menu_item")

    def reset_editor(self):
        self.canvas.delete("piece")
        self.pieces = {}
        self.create_all_pieces()

    def clear_board(self):
        self.canvas.delete("piece")
        self.pieces = {}

    def continue_from_editor(self):
        self.whites_turn = self.selected_side.get() == "White to play"
        self.start_fen = self.board_to_fen()

        self.editing = False
        self.canvas.delete("palette")
        self.canvas.config(height=self.square_size * 8)
        self.clear_menu()

        self.engine = UCIEngine.UCIEngine(engine_path)
        self.player_is_white = self.whites_turn
        self.flipped = not self.player_is_white
        self.draw_board()
        # Reposition existing pieces for the (possibly flipped) board
        for item, (row, col, piece_code, iswhite) in self.pieces.items():
            x, y = self.board_to_screen(row, col)
            self.canvas.coords(item, x, y)
        self.move_history = []
        self.engine_thinking = False
        self.menu()

        # If it's the engine's turn, let it move
        if self.whites_turn != self.player_is_white:
            self.engine_thinking = True
            threading.Thread(target=self.engine_think, daemon=True).start()

    def draw_palette(self):
        board_height = self.square_size * 8
        palette_y = board_height + 20
        piece_types = ["k", "q", "r", "b", "n", "p"]
        spacing = self.square_size

        # Background for palette area
        self.canvas.create_rectangle(
            0, board_height, self.square_size * 8, board_height + self.palette_height,
            fill="#d4d4d4", outline="", tags="palette"
        )

        # White pieces row
        for i, piece in enumerate(piece_types):
            code = f"w{piece}"
            x = (i + 1) * spacing + spacing // 2
            y = palette_y + self.square_size // 2
            item = self.canvas.create_image(x, y, image=self.images[code], tags=("palette", "palette_piece", code))

        # Black pieces row
        for i, piece in enumerate(piece_types):
            code = f"b{piece}"
            x = (i + 1) * spacing + spacing // 2
            y = palette_y + self.square_size + self.square_size // 2
            item = self.canvas.create_image(x, y, image=self.images[code], tags=("palette", "palette_piece", code))

        # Bind palette drag events
        self.canvas.tag_bind("palette_piece", "<ButtonPress-1>", self.palette_drag_start)
        self.canvas.tag_bind("palette_piece", "<B1-Motion>", self.drag_motion)
        self.canvas.tag_bind("palette_piece", "<ButtonRelease-1>", self.palette_drag_release)

    def palette_drag_start(self, event):
        item = self.canvas.find_closest(event.x, event.y)[0]
        tags = self.canvas.gettags(item)
        # Find the piece code from the tags (e.g. "wp", "bq")
        piece_code = None
        for tag in tags:
            if len(tag) == 2 and tag[0] in "wb" and tag[1] in "prnbqk":
                piece_code = tag
                break
        if piece_code is None:
            return

        # Create a clone to drag
        x, y = event.x, event.y
        clone = self.canvas.create_image(
            x, y, image=self.images[piece_code],
            tags=("piece", "draggable", piece_code)
        )
        self.drag_data["item"] = clone
        self.drag_data["x"] = event.x
        self.drag_data["y"] = event.y
        self.drag_data["from_palette"] = True

    def palette_drag_release(self, event):
        item = self.drag_data["item"]
        if item is None:
            return

        cx, cy = self.canvas.coords(item)
        board_height = self.square_size * 8
        board_width = self.square_size * 8

        # If dropped on the board, snap to grid
        if 0 <= cx < board_width and 0 <= cy < board_height:
            row, col = self.screen_to_board(cx, cy)
            row = max(0, min(7, row))
            col = max(0, min(7, col))

            # Remove any existing piece at that square
            occupant = self.get_piece_at(row, col)
            if occupant is not None:
                self.canvas.delete(occupant)
                del self.pieces[occupant]

            target_x, target_y = self.board_to_screen(row, col)
            self.canvas.coords(item, target_x, target_y)

            tags = self.canvas.gettags(item)
            piece_code = None
            for tag in tags:
                if len(tag) == 2 and tag[0] in "wb" and tag[1] in "prnbqk":
                    piece_code = tag
                    break
            iswhite = 1 if piece_code[0] == "w" else 0
            self.pieces[item] = (row, col, piece_code, iswhite)
        else:
            # Dropped off the board, discard it
            self.canvas.delete(item)

        self.drag_data["item"] = None
        self.drag_data["from_palette"] = False



    # main game loop
    def game_started(self):
        self.engine = UCIEngine.UCIEngine(engine_path)
        self.player_is_white = self.play_color.get() == "Play as White"
        self.flipped = not self.player_is_white
        self.draw_board()
        self.load_images()
        self.create_all_pieces()
        self.menu()
        self.whites_turn = True
        self.move_history = []
        self.start_fen = None
        self.engine_thinking = False

        # If player is black, engine moves first
        if not self.player_is_white:
            self.engine_thinking = True
            threading.Thread(target=self.engine_think, daemon=True).start()

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

    def board_to_fen(self):
        piece_map = {
            "wp": chess.Piece(chess.PAWN, chess.WHITE),
            "wr": chess.Piece(chess.ROOK, chess.WHITE),
            "wn": chess.Piece(chess.KNIGHT, chess.WHITE),
            "wb": chess.Piece(chess.BISHOP, chess.WHITE),
            "wq": chess.Piece(chess.QUEEN, chess.WHITE),
            "wk": chess.Piece(chess.KING, chess.WHITE),
            "bp": chess.Piece(chess.PAWN, chess.BLACK),
            "br": chess.Piece(chess.ROOK, chess.BLACK),
            "bn": chess.Piece(chess.KNIGHT, chess.BLACK),
            "bb": chess.Piece(chess.BISHOP, chess.BLACK),
            "bq": chess.Piece(chess.QUEEN, chess.BLACK),
            "bk": chess.Piece(chess.KING, chess.BLACK),
        }
        board = chess.Board(fen=None)  # empty board
        board.turn = self.whites_turn

        for item, (row, col, piece_code, iswhite) in self.pieces.items():
            square = chess.square(col, row)
            board.set_piece_at(square, piece_map[piece_code])

        # Castling rights from checkboxes
        castling = ""
        if hasattr(self, "white_kingside") and self.white_kingside.get():
            castling += "K"
        if hasattr(self, "white_queenside") and self.white_queenside.get():
            castling += "Q"
        if hasattr(self, "black_kingside") and self.black_kingside.get():
            castling += "k"
        if hasattr(self, "black_queenside") and self.black_queenside.get():
            castling += "q"
        board.set_castling_fen(castling if castling else "-")

        return board.fen()

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
        if self.start_fen:
            # Custom position: send FEN + any subsequent moves
            fen_cmd = f"position fen {self.start_fen}"
            if self.move_history:
                fen_cmd += " moves " + " ".join(self.move_history)
            self.engine.send(fen_cmd)
            self.pending_move = self.engine.search()
        else:
            self.pending_move = self.engine.get_move(self.move_history)
        # tkinter function to keep things thread-safe
        self.root.after(0, self.finish_engine_move)

    def finish_engine_move(self):
        self.make_move(self.pending_move)
        self.engine_thinking = False

