import os
import tkinter as tk
import ttkbootstrap as ttk
import threading
import chess
import UCIEngine

from tkinter import filedialog, Tk

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
        self.bot_vs_bot_active = False
        self.bot_vs_bot_paused = False
        self.palette_height = 2 * self.square_size + 40

        self.move_hints = set()
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
        item = self.canvas.find_closest(event.x, event.y)[0]

        if self.editing:
            # In editor mode, allow dragging any piece freely
            if "piece" not in self.canvas.gettags(item):
                return
            self.drag_data["item"] = item
            self.drag_data["x"] = event.x
            self.drag_data["y"] = event.y
            return

        # Prevent interaction during bot vs bot
        if self.bot_vs_bot_active:
            return

        # Prevent moves while engine is thinking
        if self.engine_thinking:
            return
        if "piece" not in self.canvas.gettags(item):
            self.clear_move_hints()
            return

        # Use chess.Board to check turn and piece ownership
        row, col = self.pieces[item][0], self.pieces[item][1]
        square = self.board_to_chess_square(row, col)
        piece = self.board.piece_at(square)
        if piece is None or piece.color != self.board.turn:
            self.clear_move_hints()
            return
        # Only allow dragging the player's own color
        player_color = chess.WHITE if self.player_is_white else chess.BLACK
        if piece.color != player_color:
            self.clear_move_hints()
            return

        self.show_move_hints(square)

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

        self.clear_move_hints()

        if self.engine_thinking:
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

        # engine responds after player's move in a background thread
        player_color = chess.WHITE if self.player_is_white else chess.BLACK
        if self.board.turn != player_color:
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

        center = x1 + self.menu_size // 2
        row = 1

        # Game Mode dropdown
        if not hasattr(self, "game_mode"):
            self.game_mode = tk.StringVar(value="Player vs Engine")
        mode_options = ["Player vs Engine", "Bot vs Bot"]
        mode_menu = tk.OptionMenu(self.root, self.game_mode, *mode_options,
                                  command=self.on_mode_change)
        self.canvas.create_window(center, row * y_margins, window=mode_menu, tags="menu_item")
        row += 1

        is_bot_vs_bot = self.game_mode.get() == "Bot vs Bot"

        if is_bot_vs_bot and self.bot_vs_bot_active:
            # During active bot vs bot game: show pause/stop controls
            pause_text = "Resume" if self.bot_vs_bot_paused else "Pause"
            pause_button = ttk.Button(self.root, text=pause_text, command=self.toggle_pause)
            self.canvas.create_window(center, row * y_margins, window=pause_button, tags="menu_item")
            row += 1

            stop_button = ttk.Button(self.root, text="Stop", command=self.stop_bot_game)
            self.canvas.create_window(center, row * y_margins, window=stop_button, tags="menu_item")
            row += 1

        elif is_bot_vs_bot:
            # Bot vs Bot setup controls
            if not hasattr(self, "think_time"):
                self.think_time = tk.IntVar(value=1000)
            if not hasattr(self, "move_delay"):
                self.move_delay = tk.IntVar(value=500)
            if not hasattr(self, "white_engine_path"):
                self.white_engine_path = engine_path
            if not hasattr(self, "black_engine_path"):
                self.black_engine_path = engine_path

            # Think time slider
            think_frame = ttk.Frame(self.root)
            ttk.Label(think_frame, text="Think time:").pack(side="left", padx=(0, 5))
            think_val = ttk.Label(think_frame, text=f"{self.think_time.get()}ms", width=7)
            def update_think(val, lbl=think_val):
                self.think_time.set(int(float(val)))
                lbl.config(text=f"{self.think_time.get()}ms")
            ttk.Scale(think_frame, from_=100, to=5000, variable=self.think_time,
                      length=150, command=update_think).pack(side="left")
            think_val.pack(side="left", padx=(5, 0))
            self.canvas.create_window(center, row * y_margins, window=think_frame, tags="menu_item")
            row += 1

            # Move delay slider
            delay_frame = ttk.Frame(self.root)
            ttk.Label(delay_frame, text="Move delay:").pack(side="left", padx=(0, 5))
            delay_val = ttk.Label(delay_frame, text=f"{self.move_delay.get()}ms", width=7)
            def update_delay(val, lbl=delay_val):
                self.move_delay.set(int(float(val)))
                lbl.config(text=f"{self.move_delay.get()}ms")
            ttk.Scale(delay_frame, from_=0, to=3000, variable=self.move_delay,
                      length=150, command=update_delay).pack(side="left")
            delay_val.pack(side="left", padx=(5, 0))
            self.canvas.create_window(center, row * y_margins, window=delay_frame, tags="menu_item")
            row += 1

            # White engine selector
            w_name = os.path.basename(self.white_engine_path)
            w_frame = ttk.Frame(self.root)
            ttk.Label(w_frame, text=f"W: {w_name}").pack(side="left", padx=(0, 5))
            ttk.Button(w_frame, text="Browse",
                       command=lambda: self.browse_engine("white")).pack(side="left")
            self.canvas.create_window(center, row * y_margins, window=w_frame, tags="menu_item")
            row += 1

            # Black engine selector
            b_name = os.path.basename(self.black_engine_path)
            b_frame = ttk.Frame(self.root)
            ttk.Label(b_frame, text=f"B: {b_name}").pack(side="left", padx=(0, 5))
            ttk.Button(b_frame, text="Browse",
                       command=lambda: self.browse_engine("black")).pack(side="left")
            self.canvas.create_window(center, row * y_margins, window=b_frame, tags="menu_item")
            row += 1

            # Start match button
            play_button = ttk.Button(self.root, text="Start match", command=self.game_started)
            self.canvas.create_window(center, row * y_margins, window=play_button, tags="menu_item")
            row += 1

        else:
            # Player vs Engine
            if not hasattr(self, "play_color"):
                self.play_color = tk.StringVar(value="Play as White")
            color_options = ["Play as White", "Play as Black"]
            color_menu = tk.OptionMenu(self.root, self.play_color, *color_options)
            self.canvas.create_window(center, row * y_margins, window=color_menu, tags="menu_item")
            row += 1

            play_button = ttk.Button(self.root, text="Play a game/reset", command=self.game_started)
            self.canvas.create_window(center, row * y_margins, window=play_button, tags="menu_item")
            row += 1

        # Common buttons
        flip_button = ttk.Button(self.root, text="Do a flip!", command=self.flip_board)
        self.canvas.create_window(center, row * y_margins, window=flip_button, tags="menu_item")
        row += 1

        if not self.bot_vs_bot_active:
            editor_button = ttk.Button(self.root, text="Board Editor", command=self.board_editor)
            self.canvas.create_window(center, row * y_margins, window=editor_button, tags="menu_item")

    def board_editor(self, _value=None):
        self.editing = True
        self.clear_menu()
        self.canvas.delete("piece")
        self.canvas.delete("palette")

        # Expand canvas to fit palette below the board
        board_height = self.square_size * 8
        self.canvas.config(height=board_height + self.palette_height)

        self.board = chess.Board()
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
        self.board = chess.Board()
        self.canvas.delete("piece")
        self.pieces = {}
        self.create_all_pieces()

    def clear_board(self):
        self.canvas.delete("piece")
        self.pieces = {}

    def continue_from_editor(self):
        white_to_play = self.selected_side.get() == "White to play"
        self.start_fen = self.board_to_fen(white_to_play)

        # Build a chess.Board from the editor FEN
        self.board = chess.Board(self.start_fen)

        self.editing = False
        self.canvas.delete("palette")
        self.canvas.config(height=self.square_size * 8)
        self.clear_menu()

        if self.game_mode.get() == "Bot vs Bot":
            self.start_bot_vs_bot(fen=self.start_fen)
            return

        self.engine = UCIEngine.UCIEngine(engine_path)
        self.player_is_white = white_to_play
        self.flipped = not self.player_is_white
        self.draw_board()
        self.create_all_pieces()
        self.engine_thinking = False
        self.menu()

        # If it's the engine's turn, let it move
        player_color = chess.WHITE if self.player_is_white else chess.BLACK
        if self.board.turn != player_color:
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
        if self.game_mode.get() == "Bot vs Bot":
            self.start_bot_vs_bot()
            return
        self.engine = UCIEngine.UCIEngine(engine_path)
        self.board = chess.Board()
        self.player_is_white = self.play_color.get() == "Play as White"
        self.flipped = not self.player_is_white
        self.start_fen = None
        self.draw_board()
        self.load_images()
        self.create_all_pieces()
        self.menu()
        self.engine_thinking = False

        # If player is black, engine moves first
        if not self.player_is_white:
            self.engine_thinking = True
            threading.Thread(target=self.engine_think, daemon=True).start()

    def on_mode_change(self, _value=None):
        self.cleanup_bot_engines()
        self.menu()

    def browse_engine(self, color):
        path = filedialog.askopenfilename(
            title=f"Select {color.title()} Engine",
            filetypes=[("Executable files", "*.exe"), ("All files", "*.*")]
        )
        if path:
            if color == "white":
                self.white_engine_path = path
            else:
                self.black_engine_path = path
            self.menu()

    def cleanup_bot_engines(self):
        self.bot_vs_bot_active = False
        self.bot_vs_bot_paused = False
        if hasattr(self, 'white_engine') and self.white_engine:
            self.white_engine.quit()
            self.white_engine = None
        if hasattr(self, 'black_engine') and self.black_engine:
            self.black_engine.quit()
            self.black_engine = None

    def start_bot_vs_bot(self, fen=None):
        self.cleanup_bot_engines()
        if fen:
            self.board = chess.Board(fen)
            self.start_fen = fen
        else:
            self.board = chess.Board()
            self.start_fen = None
        w_path = self.white_engine_path if hasattr(self, 'white_engine_path') else engine_path
        b_path = self.black_engine_path if hasattr(self, 'black_engine_path') else engine_path
        self.white_engine = UCIEngine.UCIEngine(w_path)
        self.black_engine = UCIEngine.UCIEngine(b_path)
        self.bot_vs_bot_active = True
        self.bot_vs_bot_paused = False
        self.flipped = False
        self.engine_thinking = False
        self.draw_board()
        self.load_images()
        self.create_all_pieces()
        self.menu()
        delay = self.move_delay.get() if hasattr(self, 'move_delay') else 500
        self.root.after(delay, self.bot_vs_bot_loop)

    def bot_vs_bot_loop(self):
        if not self.bot_vs_bot_active or self.bot_vs_bot_paused:
            return
        if self.board.is_game_over():
            self.bot_vs_bot_active = False
            self.menu()
            return
        engine = self.white_engine if self.board.turn == chess.WHITE else self.black_engine
        threading.Thread(target=self.bot_think, args=(engine,), daemon=True).start()

    def bot_think(self, engine):
        try:
            movetime = self.think_time.get() if hasattr(self, 'think_time') else 1000
            uci_moves = [m.uci() for m in self.board.move_stack]
            if self.start_fen:
                fen_cmd = f"position fen {self.start_fen}"
                if uci_moves:
                    fen_cmd += " moves " + " ".join(uci_moves)
                engine.send(fen_cmd)
                best_move = engine.search(movetime_ms=movetime)
            else:
                best_move = engine.get_move(uci_moves, movetime_ms=movetime)
            self.root.after(0, self.finish_bot_move, best_move)
        except Exception as e:
            print(f"Engine error: {e}")
            self.root.after(0, self.stop_bot_game)

    def finish_bot_move(self, move_uci):
        if not self.bot_vs_bot_active:
            return
        move = chess.Move.from_uci(move_uci)
        if move in self.board.legal_moves:
            self.board.push(move)
        self.create_all_pieces()
        if self.board.is_game_over():
            self.bot_vs_bot_active = False
            self.menu()
            return
        delay = self.move_delay.get() if hasattr(self, 'move_delay') else 500
        self.root.after(delay, self.bot_vs_bot_loop)

    def toggle_pause(self):
        self.bot_vs_bot_paused = not self.bot_vs_bot_paused
        if not self.bot_vs_bot_paused:
            self.bot_vs_bot_loop()
        self.menu()

    def stop_bot_game(self):
        self.cleanup_bot_engines()
        self.menu()

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

    def board_to_fen(self, white_to_play=True):
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
        board.turn = chess.WHITE if white_to_play else chess.BLACK

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

    # Thread stuff:
    # if you don't use threads, calling the engine
    # for moves freezes everything else. Not good
    def engine_think(self):
        uci_moves = [m.uci() for m in self.board.move_stack]
        if self.start_fen:
            # Custom position: send FEN + any subsequent moves
            fen_cmd = f"position fen {self.start_fen}"
            if uci_moves:
                fen_cmd += " moves " + " ".join(uci_moves)
            self.engine.send(fen_cmd)
            self.pending_move = self.engine.search()
        else:
            self.pending_move = self.engine.get_move(uci_moves)
        # tkinter function to keep things thread-safe
        self.root.after(0, self.finish_engine_move)

    def finish_engine_move(self):
        # Parse the UCI move and push to chess.Board
        move = chess.Move.from_uci(self.pending_move)
        if move in self.board.legal_moves:
            self.board.push(move)
        self.create_all_pieces()
        self.engine_thinking = False

    def board_to_chess_square(self, row, col):
        return chess.square(col, row)

    def chess_square_to_board(self, square):
        return chess.square_rank(square), chess.square_file(square)

    def show_move_hints(self, square):
        self.clear_move_hints()

        legal_moves = [m for m in self.board.legal_moves if m.from_square == square]

        for move in legal_moves:
            r, c = self.chess_square_to_board(move.to_square)
            x, y = self.board_to_screen(r, c)

            radius = self.square_size // 6
            hint = self.canvas.create_oval(
                x - radius, y - radius,
                x + radius, y + radius,
                fill="#888888",
                outline="",
                tags="move_hint"
            )
            self.move_hints.add(hint)

        self.canvas.tag_raise("move_hint")

    def clear_move_hints(self):
        for hint in self.move_hints:
            self.canvas.delete(hint)
        self.move_hints.clear()


    def check_game_over(self):
        if self.board.is_checkmate():
            winner = "Black" if self.board.turn else "White"
            msg.showinfo("Game Over", f"Checkmate! {winner} wins.")
        elif self.board.is_stalemate():
            msg.showinfo("Game Over", "Stalemate!")
        elif self.board.is_insufficient_material():
            msg.showinfo("Game Over", "Draw (insufficient material)")
