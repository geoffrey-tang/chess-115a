import os
import tkinter as tk
import ttkbootstrap as ttk
import threading
import chess
import UCIEngine

from tkinter import filedialog, messagebox, Tk

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
        self.last_move = None
        self.selected_square = None
        self.move_san_history = []
        self.history_view_index = None
        self.history_widget = None
        self.engine_thinking = False
        self.premove_queue = []  # list of (from_sq, to_sq, promotion)
        self.resigned = False

        self.analysis_mode = False
        self.analysis_engine = None
        self.analysis_running = False
        self.analysis_eval_text = None
        
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
        self.canvas.bind("<ButtonRelease-3>", lambda e: self.cancel_premove())

    # draw/ redraw the board using create_rectangle and arithmetic
    def draw_board(self):
        self.canvas.delete("square")  # only delete squares, not pieces

        # Squares involved in the last move
        last_move_squares = set()
        if self.last_move:
            last_move_squares.add((
                chess.square_rank(self.last_move.from_square),
                chess.square_file(self.last_move.from_square),
            ))
            last_move_squares.add((
                chess.square_rank(self.last_move.to_square),
                chess.square_file(self.last_move.to_square),
            ))

        # Squares involved in queued premoves (only shown in live position)
        # Earlier premoves = light red; most-recently queued = darker red
        premove_squares = set()
        premove_latest_squares = set()
        if self.premove_queue and self.history_view_index is None:
            for pm in self.premove_queue[:-1]:
                premove_squares.add((chess.square_rank(pm[0]), chess.square_file(pm[0])))
                premove_squares.add((chess.square_rank(pm[1]), chess.square_file(pm[1])))
            last = self.premove_queue[-1]
            premove_latest_squares.add((chess.square_rank(last[0]), chess.square_file(last[0])))
            premove_latest_squares.add((chess.square_rank(last[1]), chess.square_file(last[1])))

        # Draw squares (screen coordinates)
        for screen_row in range(8):
            for screen_col in range(8):
                x1 = screen_col * self.square_size
                y1 = screen_row * self.square_size
                x2 = x1 + self.square_size
                y2 = y1 + self.square_size

                # Convert to board coords to get correct color pattern
                board_row, board_col = self.screen_to_board(x1 + 1, y1 + 1)
                is_light = (board_row + board_col) % 2 == 1

                if self.selected_square == (board_row, board_col):
                    color = "#f6f669" if is_light else "#baca2b"
                elif (board_row, board_col) in last_move_squares:
                    color = "#cdd26e" if is_light else "#aaa23a"
                elif (board_row, board_col) in premove_latest_squares:
                    color = "#e87070" if is_light else "#b83030"
                elif (board_row, board_col) in premove_squares:
                    color = "#f0b8b8" if is_light else "#d06060"
                else:
                    color = self.light_square if is_light else self.dark_square

                self.canvas.create_rectangle(x1, y1, x2, y2, fill=color, outline="", tags="square")

        # Rank labels (1–8) along the left edge of the board
        for screen_row in range(8):
            board_row, board_col = self.screen_to_board(1, screen_row * self.square_size + 1)
            is_light = (board_row + board_col) % 2 == 1
            text_color = self.dark_square if is_light else self.light_square
            self.canvas.create_text(
                3, screen_row * self.square_size + 3,
                text=str(board_row + 1), anchor="nw",
                fill=text_color, font=("Arial", 10, "bold"), tags="square",
            )

        # File labels (a–h) along the bottom edge of the board
        for screen_col in range(8):
            board_row, board_col = self.screen_to_board(
                screen_col * self.square_size + 1,
                7 * self.square_size + 1,
            )
            is_light = (board_row + board_col) % 2 == 1
            text_color = self.dark_square if is_light else self.light_square
            self.canvas.create_text(
                screen_col * self.square_size + self.square_size - 3,
                7 * self.square_size + self.square_size - 3,
                text=chr(ord('a') + board_col), anchor="se",
                fill=text_color, font=("Arial", 10, "bold"), tags="square",
            )

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

        # Block dragging while browsing move history
        if self.history_view_index is not None:
            return

        # During engine thinking: allow queuing a premove
        if self.engine_thinking:
            if "piece" not in self.canvas.gettags(item):
                return
            if item not in self.pieces:
                return
            tags = self.canvas.gettags(item)
            piece_code = next((t for t in tags if len(t) == 2 and t[0] in "wb" and t[1] in "prnbqk"), None)
            player_color_char = "w" if self.player_is_white else "b"
            if piece_code is None or piece_code[0] != player_color_char:
                return
            self.drag_data["item"] = item
            self.drag_data["x"] = event.x
            self.drag_data["y"] = event.y
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

        self.selected_square = (row, col)
        self.draw_board()
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

        cx, cy = self.canvas.coords(item)

        # During engine thinking: capture move as a premove instead of executing it
        if self.engine_thinking and not self.editing:
            row, col = self.screen_to_board(cx, cy)
            row = max(0, min(7, row))
            col = max(0, min(7, col))
            old_row, old_col = self.pieces[item][0], self.pieces[item][1]
            from_sq = self.board_to_chess_square(old_row, old_col)
            to_sq = self.board_to_chess_square(row, col)
            tags = self.canvas.gettags(item)
            piece_code = next((t for t in tags if len(t) == 2 and t[0] in "wb" and t[1] in "prnbqk"), None)
            player_color_char = "w" if self.player_is_white else "b"
            if piece_code and piece_code[0] == player_color_char and from_sq != to_sq:
                promotion = None
                # Determine what piece will occupy from_sq (may be a chained premove)
                moving_piece = self.board.piece_at(from_sq)
                if moving_piece is None:
                    for pm in self.premove_queue:
                        if pm[1] == from_sq:
                            moving_piece = self.board.piece_at(pm[0])
                            break
                if moving_piece and moving_piece.piece_type == chess.PAWN and row in (0, 7):
                    promotion = self.ask_promotion(player_color_char == "w")
                self.premove_queue.append((from_sq, to_sq, promotion))
                # Snap piece visually to the premove destination
                tx, ty = self.board_to_screen(row, col)
                self.canvas.coords(item, tx, ty)
            else:
                # Invalid premove target = snap piece back
                x, y = self.board_to_screen(old_row, old_col)
                self.canvas.coords(item, x, y)
            self.drag_data["item"] = None
            self.selected_square = None
            self.draw_board()
            return

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
            promo = self.ask_promotion(piece.color == chess.WHITE)
            move = chess.Move(from_sq, to_sq, promotion=promo)

        if move not in self.board.legal_moves:
            x, y = self.board_to_screen(old_row, old_col)
            self.canvas.coords(item, x, y)
            self.drag_data["item"] = None
            self.selected_square = None
            self.draw_board()
            return

        self.record_move(move)
        self.last_move = move
        self.selected_square = None
        self.board.push(move)
        self.draw_board()
        self.create_all_pieces()
        self.restart_analysis()

        self.drag_data["item"] = None

        self.update_status()

        if self.is_over():
            self.check_game_over()
            return

        # engine responds after player's move in a background thread
        player_color = chess.WHITE if self.player_is_white else chess.BLACK
        if self.board.turn != player_color:
            self.engine_thinking = True
            threading.Thread(target=self.engine_think, daemon=True).start()

    def clear_menu(self):
        self.canvas.delete("menu_item")
        self.canvas.delete("status")

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
        self.canvas.create_rectangle(x1, y1, x2, y2, fill="#f8f8f8", outline="", tags="menu_item")

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

            # Check if a game is currently active
            game_active = (hasattr(self, "engine") and hasattr(self, "board") and 
                          not self.is_over() if hasattr(self, "board") else False)

            btn_frame = ttk.Frame(self.root)
            if not game_active:
                # Show "Play a game" when no game is active or game is over
                ttk.Button(btn_frame, text="Play a game", command=self.game_started).pack(side="left", padx=(0, 4))
            if game_active:
                # Show "Resign" only when game is active
                ttk.Button(btn_frame, text="Resign", command=self.forfeit_game).pack(side="left")
            self.canvas.create_window(center, row * y_margins, window=btn_frame, tags="menu_item")
            row += 1

        # Common buttons
        flip_button = ttk.Button(self.root, text="Do a flip!", command=self.flip_board)
        self.canvas.create_window(center, row * y_margins, window=flip_button, tags="menu_item")
        row += 1

        # Board Editor button (RESTORED)
        if not self.bot_vs_bot_active:
            editor_button = ttk.Button(self.root, text="Board Editor", command=self.board_editor)
            self.canvas.create_window(center, row * y_margins, window=editor_button, tags="menu_item")
            row += 1

        # Analysis Board button
        analysis_button = ttk.Button(self.root, text="Analysis Board", command=self.start_analysis_mode)
        self.canvas.create_window(center, row * y_margins, window=analysis_button, tags="menu_item")
        row += 1

        # Analysis display (if active)
        if self.analysis_mode and hasattr(self, "board") and not self.editing:
            self.create_analysis_display(center, row)
            row += 3  # Reserve space for analysis (takes ~3 rows)

        if hasattr(self, "board") and not self.editing:
            self.draw_history_panel(row)

        self.update_status()

    def update_status(self):
        self.canvas.delete("status")
        if not hasattr(self, "board") or self.editing:
            return

        x = self.square_size * 8 + self.menu_size // 2
        y = self.square_size * 8 - 25  # near the bottom of the sidebar

        if self.board.is_checkmate():
            winner = "Black" if self.board.turn == chess.WHITE else "White"
            text, color = f"Checkmate — {winner} wins!", "#c0392b"
        elif self.board.is_stalemate():
            text, color = "Stalemate — Draw", "#555555"
        elif self.board.is_insufficient_material():
            text, color = "Draw — insufficient material", "#555555"
        elif self.board.is_repetition(3):
            text, color = "Draw — threefold repetition", "#555555"
        elif self.board.is_check():
            turn = "White" if self.board.turn == chess.WHITE else "Black"
            text, color = f"{turn} to move  •  CHECK!", "#c0392b"
        else:
            turn = "White" if self.board.turn == chess.WHITE else "Black"
            text, color = f"{turn} to move", "#222222"

        self.canvas.create_text(x, y, text=text, fill=color,
                                font=("Arial", 12, "bold"), tags="status")

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
        self.canvas.create_rectangle(x1, y1, x2, y2, fill="#f8f8f8", outline="", tags="menu_item")

        # Back button
        back_button = ttk.Button(self.root, text="Back", command=self.menu)
        self.canvas.create_window(x1 + self.menu_size // 2, y_margins, window=back_button, tags="menu_item")

        # Side to play dropdown
        self.selected_side = tk.StringVar(value="White to play")
        options = ["White to play", "Black to play"]
        option_menu = tk.OptionMenu(self.root, self.selected_side, *options)
        self.canvas.create_window(x1 + self.menu_size // 2, 2 * y_margins, window=option_menu, tags="menu_item")

        # Castling rights label
        castling_label = tk.Label(self.root, text="Castling Rights", bg="#f8f8f8")
        self.canvas.create_window(x1 + self.menu_size // 2, 3 * y_margins, window=castling_label, tags="menu_item")

        # Castling rights checkboxes
        self.white_kingside = tk.BooleanVar(value=True)
        self.white_queenside = tk.BooleanVar(value=True)
        self.black_kingside = tk.BooleanVar(value=True)
        self.black_queenside = tk.BooleanVar(value=True)

        center = x1 + self.menu_size // 2

        # White row
        white_label = tk.Label(self.root, text="White", bg="#f8f8f8")
        self.canvas.create_window(center - 80, 3.5 * y_margins, window=white_label, tags="menu_item")
        white_oo = ttk.Checkbutton(self.root, text="O-O", variable=self.white_kingside)
        self.canvas.create_window(center + 10, 3.5 * y_margins, window=white_oo, tags="menu_item")
        white_ooo = ttk.Checkbutton(self.root, text="O-O-O", variable=self.white_queenside)
        self.canvas.create_window(center + 90, 3.5 * y_margins, window=white_ooo, tags="menu_item")

        # Black row
        black_label = tk.Label(self.root, text="Black", bg="#f8f8f8")
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
        self.move_san_history = []
        self.history_view_index = None
        self.history_widget = None
        self.resigned = False
        self.premove_queue = []
        self.draw_board()
        self.create_all_pieces()
        self.engine_thinking = False
        self.menu()

        # If it's the engine's turn, let it move
        player_color = chess.WHITE if self.player_is_white else chess.BLACK
        if self.board.turn != player_color:
            self.engine_thinking = True
            threading.Thread(target=self.engine_think, daemon=True).start()
	
        self.restart_analysis()

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
        self.last_move = None
        self.selected_square = None
        self.resigned = False
        self.premove_queue = []
        self.move_san_history = []
        self.history_view_index = None
        self.history_widget = None
        self.draw_board()
        self.load_images()
        self.create_all_pieces()
        self.menu()
        self.engine_thinking = False

        # If player is black, engine moves first
        if not self.player_is_white:
            self.engine_thinking = True
            threading.Thread(target=self.engine_think, daemon=True).start()

    def forfeit_game(self):
        if not hasattr(self, "board") or self.is_over():
            return
        winner = "Black" if self.player_is_white else "White"
        self.resigned = True
        messagebox.showinfo("Game Over", f"You forfeited. {winner} wins.")
        self.engine_thinking = True  # block further moves
        self.menu()  # Refresh menu to update button display

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
        self.resigned = False
        self.premove_queue = []
        self.last_move = None
        self.selected_square = None
        self.move_san_history = []
        self.history_view_index = None
        self.history_widget = None
        self.draw_board()
        self.load_images()
        self.create_all_pieces()
        self.menu()
        delay = self.move_delay.get() if hasattr(self, 'move_delay') else 500
        self.root.after(delay, self.bot_vs_bot_loop)

    def bot_vs_bot_loop(self):
        if not self.bot_vs_bot_active or self.bot_vs_bot_paused:
            return
        if self.is_over():
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
            self.record_move(move)
            self.board.push(move)
            self.last_move = move
        if self.history_view_index is None:
            self.draw_board()
            self.create_all_pieces()
        self.update_status()
        if self.is_over():
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
        if not hasattr(self, "pieces"):
            return
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
            self.record_move(move)
            self.board.push(move)
            self.last_move = move
        self.engine_thinking = False
        if self.history_view_index is None:
            self.draw_board()
            self.create_all_pieces()
        self.update_status()
        if self.is_over():
            self.check_game_over()
            return

        # Execute the next premove in the queue if one exists
        if self.premove_queue and self.history_view_index is None:
            from_sq, to_sq, promotion = self.premove_queue.pop(0)
            pm = chess.Move(from_sq, to_sq, promotion=promotion) if promotion else chess.Move(from_sq, to_sq)
            if pm in self.board.legal_moves:
                self.record_move(pm)
                self.last_move = pm
                self.board.push(pm)
                self.draw_board()
                self.create_all_pieces()
                self.restart_analysis()
                self.update_status()
                if self.is_over():
                    self.check_game_over()
                    return
                # Engine responds to the premove
                self.engine_thinking = True
                threading.Thread(target=self.engine_think, daemon=True).start()
            else:
                # Premove was illegal = discard the rest of the queue
                self.premove_queue.clear()
                self.draw_board()
                self.create_all_pieces()

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

    def cancel_premove(self):
        if not self.premove_queue:
            return
        self.premove_queue.clear()
        self.draw_board()
        if hasattr(self, 'pieces'):
            self.create_all_pieces()


    def record_move(self, move):
        # Record the SAN for move. Must be called before board.push(move)
        self.move_san_history.append(self.board.san(move))
        self.refresh_history_widget()

    def draw_history_panel(self, row):
        # Create a  move-history Text widget in the sidebar.
        y_margins = 50
        sidebar_x = self.square_size * 8
        sidebar_w = self.menu_size
        board_h = self.square_size * 8

        top_y = row * y_margins + 30
        bot_y = board_h - 55           # leave room for status label
        panel_h = bot_y - top_y
        panel_w = sidebar_w - 20

        if panel_h < 60:
            self.history_widget = None
            return

        if self.history_widget is not None and self.history_widget.winfo_exists():
            self.history_widget.destroy()
        self.history_widget = None

        frame = tk.Frame(self.root, bg="#f8f8f8")

        txt = tk.Text(
            frame,
            font=("Courier", 10),
            wrap="none",
            state="disabled",
            cursor="arrow",
            relief="flat",
            bg="#f8f8f8",
            padx=4, pady=2,
            exportselection=False,
        )
        scrollbar = ttk.Scrollbar(frame, orient="vertical", command=txt.yview)
        txt.config(yscrollcommand=scrollbar.set)
        scrollbar.pack(side="right", fill="y")
        txt.pack(side="left", fill="both", expand=True)

        self.history_widget = txt
        center_x = sidebar_x + sidebar_w // 2
        mid_y = (top_y + bot_y) // 2
        self.canvas.create_window(
            center_x, mid_y,
            window=frame,
            width=panel_w,
            height=panel_h,
            tags="menu_item",
        )
        self.refresh_history_widget()

    def refresh_history_widget(self):
        # Rewrite the Text widget contents from move_san_history.
        txt = self.history_widget
        if txt is None or not txt.winfo_exists():
            return

        txt.config(state="normal")
        txt.delete("1.0", "end")

        for i, san in enumerate(self.move_san_history):
            is_white = (i % 2 == 0)
            if is_white:
                txt.insert("end", f"{i // 2 + 1:>3}. ")
            tag = f"move_{i}"
            txt.insert("end", san, tag)
            if is_white:
                # pad so black's move aligns; SAN rarely exceeds 7 chars
                txt.insert("end", " " * max(1, 8 - len(san)))
            else:
                txt.insert("end", "\n")

        # If the last move was white's, close the line
        if self.move_san_history and len(self.move_san_history) % 2 == 1:
            txt.insert("end", "\n")

        for i in range(len(self.move_san_history)):
            tag = f"move_{i}"
            if i == self.history_view_index:
                txt.tag_config(tag, background="#2962ff", foreground="white")
            else:
                txt.tag_config(tag, background="", foreground="black")
            txt.tag_bind(tag, "<Button-1>",
                         lambda _, idx=i: self.on_history_click(idx))
            txt.tag_bind(tag, "<Enter>",
                         lambda _, t=tag: txt.tag_config(t, underline=True))
            txt.tag_bind(tag, "<Leave>",
                         lambda _, t=tag: txt.tag_config(t, underline=False))

        txt.config(state="disabled")

        # Scroll to the viewed move, or to the end if live
        if self.history_view_index is not None:
            ranges = txt.tag_ranges(f"move_{self.history_view_index}")
            if ranges:
                txt.see(ranges[0])
        else:
            txt.see("end")

    def on_history_click(self, index):
        # Click on a move entry in the history widget
        # Clicking the last move exits history view (returns to live)
        if index >= len(self.move_san_history) - 1:
            self.exit_history_view()
            return
        self.history_view_index = index
        self._render_history_position(index)
        self.refresh_history_widget()

    def _render_history_position(self, index):
        # Show the board after `index` half-moves without touching self.board
        start_fen = getattr(self, "start_fen", None)
        temp = chess.Board(start_fen) if start_fen else chess.Board()
        moves = list(self.board.move_stack)
        for move in moves[:index + 1]:
            temp.push(move)

        # Use the move that arrived at this position for the highlight
        saved = self.last_move
        self.last_move = moves[index] if moves else None
        self.draw_board()
        self.last_move = saved

        self.canvas.delete("piece")
        self.pieces = {}
        for square, piece in temp.piece_map().items():
            row, col = chess.square_rank(square), chess.square_file(square)
            code = ("w" if piece.color == chess.WHITE else "b") + piece.symbol().lower()
            self.create_piece(row, col, code, piece.color)

    def exit_history_view(self):
        # Go to the live board position
        self.history_view_index = None
        self.draw_board()
        self.create_all_pieces()
        self.refresh_history_widget()

    def ask_promotion(self, is_white):
        # Show a modal with piece images; returns the chosen chess piece type.
        color = "w" if is_white else "b"
        choices = [
            (chess.QUEEN,  f"{color}q"),
            (chess.ROOK,   f"{color}r"),
            (chess.BISHOP, f"{color}b"),
            (chess.KNIGHT, f"{color}n"),
        ]

        chosen = tk.IntVar(value=chess.QUEEN)

        dialog = tk.Toplevel(self.root)
        dialog.title("Promote to")
        dialog.resizable(False, False)
        dialog.grab_set()  # modal

        frame = ttk.Frame(dialog, padding=10)
        frame.pack()

        for piece_type, code in choices:
            btn = tk.Button(
                frame,
                image=self.images[code],
                relief="raised", bd=2,
                command=lambda p=piece_type: (chosen.set(p), dialog.destroy()),
            )
            btn.pack(side="left", padx=4, pady=4)

        self.root.wait_window(dialog)
        return chosen.get()

    def is_over(self):
        # True if the game is over, i.e. threefold repetition
        return self.resigned or self.board.is_game_over() or self.board.is_repetition(3)

    def check_game_over(self):
        if self.board.is_checkmate():
            winner = "Black" if self.board.turn == chess.WHITE else "White"
            messagebox.showinfo("Game Over", f"Checkmate! {winner} wins.")
        elif self.board.is_stalemate():
            messagebox.showinfo("Game Over", "Stalemate!")
        elif self.board.is_insufficient_material():
            messagebox.showinfo("Game Over", "Draw (insufficient material)")
        elif self.board.is_repetition(3):
            messagebox.showinfo("Game Over", "Draw by threefold repetition!")
        self.engine_thinking = True  # block further moves
        self.menu()  # Refresh menu to update button display

    def start_analysis_mode(self):
        self.analysis_mode = True
        self.analysis_running = True

        # If no board exists yet → start from default
        if not hasattr(self, "board"):
            self.board = chess.Board()

        # If editor is active → build board from editor pieces
        if self.editing:
            white_to_play = True
            if hasattr(self, "selected_side"):
                white_to_play = self.selected_side.get() == "White to play"
            self.board = chess.Board(self.board_to_fen(white_to_play))

        self.analysis_engine = UCIEngine.UCIEngine(engine_path)

        # Refresh menu to show analysis display in proper position
        self.menu()

        threading.Thread(target=self.analysis_loop, daemon=True).start()

    def create_analysis_display(self, center_x=None, row=None):
        if self.analysis_eval_text:
            self.canvas.delete(self.analysis_eval_text)

        # If called from menu with positioning, use that; otherwise use default
        if center_x is not None and row is not None:
            x = center_x
            y = row * 50  # y_margins = 50
        else:
            x = self.square_size * 8 + self.menu_size // 2
            y = 50  # Top of sidebar

        self.analysis_eval_text = self.canvas.create_text(
            x, y, text="Evaluating...", 
            font=("Arial", 11), fill="black",
            width=self.menu_size - 40,  # Wrap text to fit sidebar
            tags="menu_item"
        )

    def analysis_loop(self):
        while self.analysis_running:
            try:
                fen = self.board.fen()

                self.analysis_engine.send(f"position fen {fen}")

                info = self.analysis_engine.analyze(movetime_ms=300)

                self.root.after(0, self.update_analysis_display, info)

            except Exception as e:
                print("Analysis error:", e)
                break

    def update_analysis_display(self, info):
        if not self.analysis_eval_text:
            return

        score = info.get("score", "?")
        pv = info.get("pv", [])
        best_move = info.get("best_move")

        text = f"Eval: {score}"

        if pv:
            text += "\nBest line:\n" + " ".join(pv)
        elif best_move:
            text += f"\nBest move: {best_move}"
        else:
            text += "\nBest move: (searching...)"

        self.canvas.itemconfig(self.analysis_eval_text, text=text)

    def restart_analysis(self):
        if not self.analysis_mode:
            return

        self.analysis_running = False
        self.analysis_running = True
        threading.Thread(target=self.analysis_loop, daemon=True).start()
