import os
import time
import tkinter as tk
import ttkbootstrap as ttk
import threading
import chess
import chess.pgn
import logging
import io
import UCIEngine

from tkinter import filedialog, messagebox

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

        self.board = chess.Board()
        self.analysis_mode = False
        self.analysis_engine = None
        self.analysis_running = False
        self.analysis_eval_text = None
        self.arrow_var = tk.BooleanVar(value = True)

        self.suggestion_arrow = None
        self.suggested_move = None
        self.show_arrows = True

        # Sidebar layout constants
        self.SB = self.square_size * 8      # sidebar x start
        self.SW = self.menu_size             # sidebar width
        self.PAD = 20                        # left margin
        self.BTN_W = self.SW - self.PAD * 2  # button pixel width
        self.ROW_H = 44                      # pixels between rows
        self.SIDEBAR_BG = "#f0f0f0"
        self.SEP_COLOR = "#d0d0d0"

        self.setup_ui()
        self.draw_board()
        self.load_images()
        self.create_all_pieces()
        self.menu()

    # initialization of tkinter frame and canvas objects
    def setup_ui(self):
        main_frame = ttk.Frame(self.root, padding = 10)
        main_frame.pack()

        # Canvas for chess board
        self.canvas = tk.Canvas(
            main_frame,
            width = self.square_size * 8 + self.menu_size,
            height = self.square_size * 8,
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
            last_move_squares.add((chess.square_rank(self.last_move.from_square), chess.square_file(self.last_move.from_square),))
            last_move_squares.add((chess.square_rank(self.last_move.to_square), chess.square_file(self.last_move.to_square),))

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

        self.canvas.tag_lower("square")
        self.canvas.tag_raise("piece")
        self.canvas.tag_raise("suggestion_arrow")
        self.canvas.tag_raise("move_hint")
        self.canvas.tag_raise("menu_item")
        self.canvas.tag_raise("status")
        self.canvas.tag_raise("analysis")
    
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

    def create_piece(self, row, col, piece_code, color):
    
        x, y = self.board_to_screen(row, col)

        image = self.images[piece_code]   # or whatever your image dictionary is called

        item = self.canvas.create_image(
            x,
            y,
            image=image,
            tags=("piece",)
        )

        self.pieces[item] = (row, col, piece_code, color)

        self.canvas.tag_bind(item, "<ButtonPress-1>", self.drag_start)
        self.canvas.tag_bind(item, "<B1-Motion>", self.drag_motion)
        self.canvas.tag_bind(item, "<ButtonRelease-1>", self.drag_release)

    def create_all_pieces(self):
        # remove all pieces from canvas
        self.canvas.delete("piece")
        self.pieces = {}

        for square, piece in self.board.piece_map().items():
            
            col = chess.square_file(square)
            row = chess.square_rank(square)

            piece_code = ("w" if piece.color == chess.WHITE else "b") + piece.symbol().lower()

            self.create_piece(row, col, piece_code, piece.color)

        self.canvas.tag_raise("suggestion_arrow")

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

        # No game started yet, block all piece interaction
        if not hasattr(self, "player_is_white"):
            return

        # Block dragging while browsing move history
        if self.history_view_index is not None:
            return

        # During engine thinking: allow queuing a premove (only during an active game)
        game_active = hasattr(self, "engine") and not self.is_over()
        if self.engine_thinking and game_active:
            if "piece" not in self.canvas.gettags(item):
                return
            if item not in self.pieces:
                return
            piece_code = self.pieces[item][2]
            player_color_char = "w" if self.player_is_white else "b"
            if piece_code[0] != player_color_char:
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
            piece_code = self.pieces[item][2]
            player_color_char = "w" if self.player_is_white else "b"
            if piece_code[0] == player_color_char and from_sq != to_sq:
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

            if 0 <= cx < board_width and 0 <= cy < board_height:
                row, col = self.screen_to_board(cx, cy)
                row = max(0, min(7, row))
                col = max(0, min(7, col))

                occupant = self.get_piece_at(row, col)
                if occupant is not None and occupant != item:
                    self.canvas.delete(occupant)
                    del self.pieces[occupant]

                target_x, target_y = self.board_to_screen(row, col)
                self.canvas.coords(item, target_x, target_y)
                self.pieces[item] = (row, col, self.pieces[item][2], self.pieces[item][3])
            else:
                self.canvas.delete(item)
                del self.pieces[item]

            self.drag_data["item"] = None
            return

        # --- Normal gameplay ---
        row, col = self.screen_to_board(cx, cy)
        row = max(0, min(7, row))
        col = max(0, min(7, col))

        old_row, old_col = self.pieces[item][0], self.pieces[item][1]
        
        from_sq = self.board_to_chess_square(old_row, old_col)
        to_sq = self.board_to_chess_square(row, col)

        piece = self.board.piece_at(from_sq)

        # Fix castling when king is dropped on rook
        if piece and piece.piece_type == chess.KING:
            target_piece = self.board.piece_at(to_sq)

            if target_piece and target_piece.piece_type == chess.ROOK and target_piece.color == piece.color:

                if to_sq > from_sq:  # kingside
                    to_sq = chess.square(chess.FILE_G, chess.square_rank(from_sq))
                else:  # queenside
                    to_sq = chess.square(chess.FILE_C, chess.square_rank(from_sq))

        piece = self.board.piece_at(from_sq)

        # Handle pawn promotion
        move = chess.Move(from_sq, to_sq)
        if piece and piece.piece_type == chess.PAWN and row in (0, 7):
            promo = self.ask_promotion(piece.color == chess.WHITE)
            move = chess.Move(from_sq, to_sq, promotion=promo)

        # Check legality
        if move not in self.board.legal_moves:
            # Illegal move, reset piece to old square
            x, y = self.board_to_screen(old_row, old_col)
            self.canvas.coords(item, x, y)
            self.drag_data["item"] = None
            self.selected_square = None
            self.draw_board()
            return

        self.record_move(move)
        self.board.push(move)

        self.last_move = move
        self.selected_square = None

        self.canvas.delete("piece")
        self.pieces.clear()
        self.draw_board()
        self.create_all_pieces()

        self.drag_data["item"] = None
        self.update_status()

        # Check for game over
        if self.is_over():
            self.check_game_over()
            return

        # Engine move if it's AI's turn
        player_color = chess.WHITE if self.player_is_white else chess.BLACK
        if self.board.turn != player_color:
            self.engine_thinking = True
            threading.Thread(target=self.engine_think, daemon=True).start()

    def menu(self):

        self.editing = False
        self.canvas.delete("palette")
        self.canvas.config(height=self.square_size * 8)
        self.clear_menu()

        self.canvas.create_rectangle(self.SB, 0, self.SB + self.SW, self.square_size * 8,
                                     fill=self.SIDEBAR_BG, outline="", tags="menu_item")
        self.menu_y = 20

        btn = self.sidebar_btn
        dropdown = self.sidebar_dropdown
        sep = self.sidebar_sep
        label = self.sidebar_label

        if not hasattr(self, "game_mode"):
            self.game_mode = tk.StringVar(value="Player vs Engine")
        is_bot_vs_bot = self.game_mode.get() == "Engine vs Engine"
        pve_game_active = (not is_bot_vs_bot and hasattr(self, "engine") and
                           hasattr(self, "board") and not self.is_over())

        # ACTIVE BOT VS BOT
        if is_bot_vs_bot and self.bot_vs_bot_active:
            label("ENGINE VS ENGINE")
            pause_text = "Pause" if not self.bot_vs_bot_paused else "Resume"
            btn(pause_text, self.toggle_pause)
            btn("Stop game", self.stop_bot_game, style="danger-outline")

        # ACTIVE PLAYER VS ENGINE GAME
        elif pve_game_active:
            label("IN GAME")
            btn("Resign", self.forfeit_game, style="danger-outline")

        # IDLE / SETUP (no active game)
        else:
            label("GAME MODE")
            dropdown(self.game_mode, "Player vs Engine", "Engine vs Engine",
                     command=self.on_mode_change)

            if is_bot_vs_bot:
                label("WHITE ENGINE")
                white_path = getattr(self, "white_engine_path", engine_path)
                btn(f"W: {os.path.basename(white_path)}", lambda: self.browse_engine("white"))
                label("BLACK ENGINE")
                black_path = getattr(self, "black_engine_path", engine_path)
                btn(f"B: {os.path.basename(black_path)}", lambda: self.browse_engine("black"))
                sep()
                btn("Start Engine Game", self.start_bot_vs_bot, style="success")
                sep()
                label("BOARD")
                btn("Board Editor", self.board_editor)
            else:
                if not hasattr(self, "play_color"):
                    self.play_color = tk.StringVar(value="Play as White")
                dropdown(self.play_color, "Play as White", "Play as Black")
                btn("Play a game", self.game_started, style="success")
                sep()
                label("BOARD")
                btn("Board Editor", self.board_editor)

        # BOARD
        sep()
        label("BOARD")
        btn("Flip board", self.flip_board)

        sep()
        label("ANALYSIS")
        analysis_label = "Stop analysis" if self.analysis_mode else "Analysis Board"
        btn(analysis_label, self.start_analysis_mode)

        if self.analysis_mode and hasattr(self, "board") and not self.editing:
            center = self.SB + self.SW // 2
            self.create_analysis_display(center, self.menu_y)
            self.menu_y += 110

        # POSITION
        sep()
        label("POSITION")
        if not pve_game_active and not self.bot_vs_bot_active:
            btn("Load FEN / PGN", self.load_fen_pgn_dialog)

        if hasattr(self, "board") and not self.editing:
            half = (self.BTN_W - 4) // 2
            b1 = ttk.Button(self.root, text="Copy FEN", command=self.copy_fen, bootstyle="outline")
            b2 = ttk.Button(self.root, text="Copy PGN", command=self.copy_pgn, bootstyle="outline")
            self.canvas.create_window(self.SB + self.PAD, self.menu_y, window=b1, anchor="nw", tags="menu_item", width=half)
            self.canvas.create_window(self.SB + self.PAD + half + 4, self.menu_y, window=b2, anchor="nw", tags="menu_item", width=self.BTN_W - half - 4)
            self.menu_y += self.ROW_H

        # MOVE HISTORY
        sep()
        if hasattr(self, "board") and not self.editing:
            history_row = int(self.menu_y / 50) + 1
            self.draw_history_panel(history_row)

        self.update_status()

    def load_fen_pgn_dialog(self):
        dialog = tk.Toplevel(self.root)
        dialog.title("Load FEN or PGN")
        dialog.resizable(False, False)
        dialog.grab_set()

        frame = ttk.Frame(dialog, padding=12)
        frame.pack(fill="both", expand=True)

        tk.Label(frame, text="Paste a FEN string or PGN game:").pack(anchor="w")
        text = tk.Text(frame, width=60, height=10, wrap="word")
        text.pack(pady=(4, 8))
        text.focus_set()

        status_var = tk.StringVar()
        status_lbl = tk.Label(frame, textvariable=status_var, fg="#c0392b")
        status_lbl.pack(anchor="w")

        def do_load():
            raw = text.get("1.0", "end").strip()
            if not raw:
                return
            board, start_fen, move_history = None, None, []

            tokens = raw.split()
            looks_like_fen = tokens[0].count("/") == 7 if tokens else False

            if looks_like_fen:
                try:
                    board = chess.Board(raw)
                    start_fen = raw if raw != chess.Board().fen() else None
                except Exception as e:
                    status_var.set(f"Invalid FEN: {e}")
                    return
            else:
                try:
                    # keep terminal output clean
                    logging.getLogger("chess.pgn").setLevel(logging.ERROR)
                    game = chess.pgn.read_game(io.StringIO(raw))
                    if game is not None:
                        root = game.board()
                        moves = list(game.mainline_moves())
                        board = root.copy()
                        for move in moves:
                            move_history.append(board.san(move))
                            board.push(move)
                        start_fen = root.fen() if root.fen() != chess.Board().fen() else None
                except Exception as e:
                    status_var.set(f"Invalid PGN: {e}")
                    return
                if board is None:
                    status_var.set("Invalid FEN or PGN, please check and try again.")
                    return

            dialog.destroy()
            self.resume_from_board(board, start_fen, move_history)

        ttk.Button(frame, text="Load", command=do_load).pack(side="right")
        ttk.Button(frame, text="Cancel", command=dialog.destroy).pack(side="right", padx=(0, 6))

    def resume_from_board(self, board, start_fen, move_san_history):
        if self.bot_vs_bot_active:
            self.cleanup_bot_engines()
        if hasattr(self, "engine"):
            try:
                self.engine.quit()
            except Exception:
                pass
        self.engine = UCIEngine.UCIEngine(engine_path)
        self.board = board
        self.start_fen = start_fen
        self.player_is_white = self.play_color.get() == "Play as White" if hasattr(self, "play_color") else True
        self.flipped = not self.player_is_white
        self.last_move = list(board.move_stack)[-1] if board.move_stack else None
        self.selected_square = None
        self.resigned = False
        self.premove_queue = []
        self.move_san_history = move_san_history
        self.history_view_index = None
        self.history_widget = None
        self.engine_thinking = False
        if not hasattr(self, "game_mode"):
            self.game_mode = tk.StringVar(value="Player vs Engine")
        self.game_mode.set("Player vs Engine")
        self.draw_board()
        self.load_images()
        self.create_all_pieces()
        self.menu()
        # If it's the engine's turn, let it move
        player_color = chess.WHITE if self.player_is_white else chess.BLACK
        if not self.is_over() and self.board.turn != player_color:
            self.engine_thinking = True
            threading.Thread(target=self.engine_think, daemon=True).start()

    def copy_fen(self):
        if not hasattr(self, "board"):
            return
        fen = self.board.fen()
        self.root.clipboard_clear()
        self.root.clipboard_append(fen)
        messagebox.showinfo("Copied", "FEN copied to clipboard.")

    def copy_pgn(self):
        if not hasattr(self, "board"):
            return
        game = chess.pgn.Game.from_board(self.board)
        exporter = chess.pgn.StringExporter(headers=True, variations=False, comments=False)
        pgn_str = game.accept(exporter)
        self.root.clipboard_clear()
        self.root.clipboard_append(pgn_str)
        messagebox.showinfo("Copied", "PGN copied to clipboard.")

    def get_material_info(self):
        # Returns (white_captured, black_captured, net) where net > 0 means white is ahead.
        PIECE_VALUES = {chess.PAWN: 1, chess.KNIGHT: 3, chess.BISHOP: 3, chess.ROOK: 5, chess.QUEEN: 9}
        piece_types = [chess.PAWN, chess.KNIGHT, chess.BISHOP, chess.ROOK, chess.QUEEN]

        start_fen = getattr(self, 'start_fen', None)
        start_board = chess.Board(start_fen) if start_fen else chess.Board()

        white_captured = {}  # black pieces captured by white
        black_captured = {}  # white pieces captured by black

        for pt in piece_types:
            black_lost = len(start_board.pieces(pt, chess.BLACK)) - len(self.board.pieces(pt, chess.BLACK))
            white_lost = len(start_board.pieces(pt, chess.WHITE)) - len(self.board.pieces(pt, chess.WHITE))
            if black_lost > 0:
                white_captured[pt] = black_lost
            if white_lost > 0:
                black_captured[pt] = white_lost

        white_score = sum(PIECE_VALUES[pt] * cnt for pt, cnt in white_captured.items())
        black_score = sum(PIECE_VALUES[pt] * cnt for pt, cnt in black_captured.items())
        return white_captured, black_captured, white_score - black_score

    # Shared sidebar helpers
    def sidebar_btn(self, text, command, style="outline", width=None):
        if width is None:
            width = self.BTN_W
        b = ttk.Button(self.root, text=text, command=command, bootstyle=style)
        self.canvas.create_window(self.SB + self.PAD, self.menu_y, window=b,
                                  anchor="nw", tags="menu_item", width=width)
        self.menu_y += self.ROW_H

    def sidebar_dropdown(self, var, *options, command=None):
        om = tk.OptionMenu(self.root, var, *options, command=command)
        om.config(bg=self.SIDEBAR_BG, fg="#222222", activebackground="#e0e0e0",
                  activeforeground="#222222", relief="flat",
                  font=("Arial", 10),
                  highlightthickness=0, bd=0, cursor="hand2")
        om["menu"].config(bg="white", fg="#222222", relief="flat", font=("Arial", 10))
        self.canvas.create_window(self.SB + self.PAD, self.menu_y, window=om,
                                  anchor="nw", tags="menu_item", width=self.BTN_W)
        self.menu_y += self.ROW_H

    def sidebar_sep(self):
        self.menu_y += 4
        self.canvas.create_line(self.SB + self.PAD, self.menu_y,
                                self.SB + self.SW - self.PAD, self.menu_y,
                                fill=self.SEP_COLOR, tags="menu_item")
        self.menu_y += 10

    def sidebar_label(self, text):
        lbl = tk.Label(self.root, text=text, bg=self.SIDEBAR_BG, fg="#888888",
                       font=("Arial", 8))
        self.canvas.create_window(self.SB + self.PAD, self.menu_y, window=lbl,
                                  anchor="nw", tags="menu_item")
        self.menu_y += 18

    def clear_menu(self):
        self.canvas.delete("menu_item")
        self.canvas.delete("status")

    def update_status(self):
        self.canvas.delete("status")
        if not hasattr(self, "board") or self.editing:
            return

        x = self.square_size * 8 + self.menu_size // 2

        # Material counter
        PIECE_ORDER = [chess.QUEEN, chess.ROOK, chess.BISHOP, chess.KNIGHT, chess.PAWN]
        BLACK_SYM = {chess.PAWN: '♟', chess.KNIGHT: '♞', chess.BISHOP: '♝', chess.ROOK: '♜', chess.QUEEN: '♛'}
        WHITE_SYM = {chess.PAWN: '♙', chess.KNIGHT: '♘', chess.BISHOP: '♗', chess.ROOK: '♖', chess.QUEEN: '♕'}

        white_cap, black_cap, net = self.get_material_info()

        white_pieces = ''.join(BLACK_SYM[pt] * white_cap[pt] for pt in PIECE_ORDER if pt in white_cap)
        black_pieces = ''.join(WHITE_SYM[pt] * black_cap[pt] for pt in PIECE_ORDER if pt in black_cap)

        white_adv = f"  +{net}" if net > 0 else ""
        black_adv = f"  +{-net}" if net < 0 else ""
        self.canvas.create_text(x, self.square_size * 8 - 85,
            text=f"White: {white_pieces}{white_adv}",
            fill="#222222", font=("Arial", 11), tags="status")
        self.canvas.create_text(x, self.square_size * 8 - 65,
            text=f"Black: {black_pieces}{black_adv}",
            fill="#222222", font=("Arial", 11), tags="status")

        # Turn / game state
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
                                font=("Arial", 11, "bold"), tags="status")

    def board_editor(self):
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

        self.canvas.create_rectangle(self.SB, 0, self.SB + self.SW, board_height + self.palette_height,
                                     fill=self.SIDEBAR_BG, outline="", tags="menu_item")
        self.menu_y = 20

        btn = self.sidebar_btn
        dropdown = self.sidebar_dropdown
        sep = self.sidebar_sep
        label = self.sidebar_label

        btn("Back", self.menu)

        sep()
        label("SIDE TO MOVE")
        self.selected_side = tk.StringVar(value="White to play")
        dropdown(self.selected_side, "White to play", "Black to play")

        sep()
        label("CASTLING RIGHTS")
        self.white_kingside = tk.BooleanVar(value=True)
        self.white_queenside = tk.BooleanVar(value=True)
        self.black_kingside = tk.BooleanVar(value=True)
        self.black_queenside = tk.BooleanVar(value=True)

        white_frame = ttk.Frame(self.root)
        tk.Label(white_frame, text="White", bg=self.SIDEBAR_BG, width=5, anchor="w").pack(side="left")
        ttk.Checkbutton(white_frame, text="O-O", variable=self.white_kingside).pack(side="left", padx=(4, 0))
        ttk.Checkbutton(white_frame, text="O-O-O", variable=self.white_queenside).pack(side="left", padx=(4, 0))
        self.canvas.create_window(self.SB + self.PAD + self.BTN_W // 2, self.menu_y, window=white_frame, anchor="center", tags="menu_item")
        self.menu_y += self.ROW_H - 8

        black_frame = ttk.Frame(self.root)
        tk.Label(black_frame, text="Black", bg=self.SIDEBAR_BG, width=5, anchor="w").pack(side="left")
        ttk.Checkbutton(black_frame, text="O-O", variable=self.black_kingside).pack(side="left", padx=(4, 0))
        ttk.Checkbutton(black_frame, text="O-O-O", variable=self.black_queenside).pack(side="left", padx=(4, 0))
        self.canvas.create_window(self.SB + self.PAD + self.BTN_W // 2, self.menu_y, window=black_frame, anchor="center", tags="menu_item")
        self.menu_y += self.ROW_H

        sep()
        label("BOARD")
        btn("Reset to start", self.reset_editor)
        btn("Clear board", self.clear_board)
        btn("Flip board", self.flip_board)

        sep()
        label("GAME MODE")
        if not hasattr(self, "game_mode"):
            self.game_mode = tk.StringVar(value="Player vs Engine")
        dropdown(self.game_mode, "Player vs Engine", "Engine vs Engine")

        sep()
        btn("Continue from here", self.continue_from_editor, style="success")

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

        if self.game_mode.get() == "Engine vs Engine":
            # Go to idle engine vs engine menu so user can pick engines first
            self.flipped = False
            self.draw_board()
            self.create_all_pieces()
            self.menu()
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
            self.canvas.create_image(x, y, image=self.images[code], tags=("palette", "palette_piece", code))

        # Black pieces row
        for i, piece in enumerate(piece_types):
            code = f"b{piece}"
            x = (i + 1) * spacing + spacing // 2
            y = palette_y + self.square_size + self.square_size // 2
            self.canvas.create_image(x, y, image=self.images[code], tags=("palette", "palette_piece", code))

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
        if self.game_mode.get() == "Engine vs Engine":
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
        elif self.start_fen:
            self.board = chess.Board(self.start_fen)
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

    def get_piece_at(self, row, col):
        for item, (r, c, _, _) in self.pieces.items():
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
        self.append_move_to_widget(len(self.move_san_history) - 1)

    def draw_history_panel(self, row):
        # Create a  move-history Text widget in the sidebar.
        y_margins = 50
        sidebar_x = self.square_size * 8
        sidebar_w = self.menu_size
        board_h = self.square_size * 8

        top_y = row * y_margins + 30
        bot_y = board_h - 95           # leave room for material + status labels
        panel_h = bot_y - top_y
        panel_w = sidebar_w - 20

        if panel_h < 60:
            self.history_widget = None
            return

        if self.history_widget is not None and self.history_widget.winfo_exists():
            self.history_widget.destroy()
        self.history_widget = None

        frame = tk.Frame(self.root, bg="#f0f0f0")

        txt = tk.Text(
            frame,
            font=("Courier", 10),
            wrap="none",
            state="disabled",
            cursor="arrow",
            relief="flat",
            bg="#f0f0f0",
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

    def bind_move_tag(self, txt, i):
        tag = f"move_{i}"
        txt.tag_bind(tag, "<Button-1>", lambda _, idx=i: self.on_history_click(idx))
        txt.tag_bind(tag, "<Enter>",    lambda _, t=tag: txt.tag_config(t, underline=True))
        txt.tag_bind(tag, "<Leave>",    lambda _, t=tag: txt.tag_config(t, underline=False))

    def append_move_to_widget(self, i):
        # Add a single newly-recorded move to the history widget
        txt = self.history_widget
        if txt is None or not txt.winfo_exists():
            return
        san = self.move_san_history[i]
        is_white = (i % 2 == 0)
        tag = f"move_{i}"

        txt.config(state="normal")
        # If white's move, delete the newline
        # added after the previous black move, then write the move number
        if is_white:
            txt.insert("end", f"{i // 2 + 1:>3}. ")
        txt.insert("end", san, tag)
        if is_white:
            txt.insert("end", " " * max(1, 8 - len(san)))
        else:
            txt.insert("end", "\n")
        txt.config(state="disabled")

        txt.tag_config(tag, background="", foreground="black")
        self.bind_move_tag(txt, i)
        txt.see("end")

    def update_history_highlight(self, old_index, new_index):
        # Only chhange the two tags whose highlight state changed
        txt = self.history_widget
        if txt is None or not txt.winfo_exists():
            return
        if old_index is not None:
            txt.tag_config(f"move_{old_index}", background="", foreground="black")
        if new_index is not None:
            txt.tag_config(f"move_{new_index}", background="#2962ff", foreground="white")
            ranges = txt.tag_ranges(f"move_{new_index}")
            if ranges:
                txt.see(ranges[0])
        else:
            txt.see("end")

    def refresh_history_widget(self):
        # Full rewrite, use only when the widget is first built or reset
        # since relatively costly to rewrite
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
                txt.insert("end", " " * max(1, 8 - len(san)))
            else:
                txt.insert("end", "\n")
            if i == self.history_view_index:
                txt.tag_config(tag, background="#2962ff", foreground="white")
            else:
                txt.tag_config(tag, background="", foreground="black")
            self.bind_move_tag(txt, i)

        if self.move_san_history and len(self.move_san_history) % 2 == 1:
            txt.insert("end", "\n")

        txt.config(state="disabled")

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
        old_index = self.history_view_index
        self.history_view_index = index
        self.render_history_position(index)
        self.update_history_highlight(old_index, index)

    def render_history_position(self, index):
        # Show the board after index half-moves without touching self.board
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
        old_index = self.history_view_index
        self.history_view_index = None
        self.draw_board()
        self.create_all_pieces()
        self.update_history_highlight(old_index, None)

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

        if self.analysis_mode:
            # Turn OFF
            self.analysis_mode = False
            self.analysis_running = False
            self.canvas.delete("analysis")
            self.canvas.delete("suggestion_arrow")
            self.suggested_move = None
            if self.analysis_engine:
                self.analysis_engine.quit()
                self.analysis_engine = None
        else:
            # Turn ON
            if not hasattr(self, "board"):
                return

            self.analysis_mode = True
            
            if self.analysis_engine is None:
                self.analysis_engine = UCIEngine.UCIEngine(engine_path)

            if not self.analysis_running:
                self.analysis_running = True
                threading.Thread(target = self.analysis_loop, daemon = True).start()

        self.menu()

    def create_analysis_display(self, center, y):
        self.canvas.delete("analysis")

        # Eval box background
        self.canvas.create_rectangle(
            self.SB + self.PAD, y, self.SB + self.SW - self.PAD, y + 56,
            fill="#e8e8e8", outline="#d0d0d0",
            width=1, tags="analysis"
        )

        initial_text = "Eval: --     Best move: --"
        self.analysis_eval_text = self.canvas.create_text(
            center, y + 28,
            text=initial_text,
            font=("Courier", 10, "bold"),
            fill="#222222",
            tags="analysis"
        )

        arrow_toggle = ttk.Checkbutton(
            self.root, text="Show arrows",
            variable=self.arrow_var,
            command=self.toggle_arrows,
            bootstyle="round-toggle"
        )
        self.canvas.create_window(self.SB + self.PAD, y + 70, window=arrow_toggle, anchor="nw", tags="analysis")

    def analysis_loop(self):

        last_fen = None

        while self.analysis_running:
            try:
                fen = self.board.fen()

                if fen == last_fen:
                    time.sleep(0.1)
                    continue

                last_fen = fen
                self.analysis_engine.send(f"position fen {fen}") # Send position to engine
                
                def send_update(info):
                    self.root.after(0, self.update_analysis_display, info)

                self.analysis_engine.analyze(movetime_ms = 150, callback = send_update)

                time.sleep(0.1)

            except Exception as e:
                print("Analysis error:", e)
                break

    def draw_suggestion_arrow(self, move_uci):

        if not self.show_arrows:
            return

        self.canvas.delete("suggestion_arrow")

        move = chess.Move.from_uci(move_uci)
        
        r1, c1 = self.chess_square_to_board(move.from_square)
        r2, c2 = self.chess_square_to_board(move.to_square)

        x1, y1 = self.board_to_screen(r1, c1)
        x2, y2 = self.board_to_screen(r2, c2)

        self.suggestion_arrow = self.canvas.create_line(x1, y1, x2, y2, width=8, fill="#1f77ff", arrow=tk.LAST, arrowshape=(20, 25, 10), smooth=True, tags="suggestion_arrow")

        self.canvas.tag_raise("suggestion_arrow", "piece")

    def toggle_arrows(self):
        self.show_arrows = self.arrow_var.get()

        if not self.show_arrows:
            self.canvas.delete("suggestion_arrow")
        else:
            if self.suggested_move:
                try:
                    self.draw_suggestion_arrow(str(self.suggested_move))
                except Exception as e:
                    print("Error drawing arrow:", e)
                    self.clear_suggestion_arrow()

    def clear_suggestion_arrow(self):
        if self.suggestion_arrow:
            self.canvas.delete(self.suggestion_arrow)
            self.suggestion_arrow = None

    def update_analysis_display(self, info):
        if self.analysis_eval_text is None:
            return

        score = info.get("score", "?")
        pv = info.get("pv", [])
        best_move = info.get("best_move")

        move_to_show = pv[0] if pv else best_move
        score_str = str(score) if score is not None else "?"
        move_str = move_to_show if move_to_show else "..."
        text = f"Eval: {score_str:<8} Best: {move_str}"

        self.canvas.itemconfig(self.analysis_eval_text, text = text)

        if move_to_show == self.suggested_move:
            return

        self.suggested_move = move_to_show

        if self.suggested_move and self.show_arrows:
            try:
                self.draw_suggestion_arrow(str(self.suggested_move))
            except Exception as e:
                print("Error drawing arrow:", e)
                self.clear_suggestion_arrow()
        else:
            self.clear_suggestion_arrow()


