import tkinter as tk
import ttkbootstrap as ttk


class ChessGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Chess Board")

        self.square_size = 100

        self.menu_size = 400

        # Colors
        # Feel free to mess with this
        self.light_square = "#eeeed2"
        self.dark_square = "#769656"

        self.drag_data = {"x": 0, "y": 0, "item": None}

        self.setup_ui()
        self.draw_board()
        
        #draw menu
        self.menu()

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

    def draw_board(self):
        self.canvas.delete("all")

        # Draw squares
        for row in range(8):
            for col in range(8):
                x1 = col * self.square_size
                y1 = row * self.square_size
                x2 = x1 + self.square_size
                y2 = y1 + self.square_size

                color = self.light_square if (row + col) % 2 == 0 else self.dark_square

                self.canvas.create_rectangle(x1, y1, x2, y2, fill=color, outline = "")
    
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
        
        x = col * self.square_size + self.square_size // 2
        y = row * self.square_size + self.square_size // 2

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

    def drag_release(self, event):
        item = self.drag_data["item"]
        if item is None:
            return
        
        cx, cy = self.canvas.coords(item)

        col = max(0, min(7, cx // self.square_size))
        row = max(0, min(7, cy // self.square_size))

        target_x = col * self.square_size + self.square_size // 2
        target_y = row * self.square_size + self.square_size // 2

        dx = target_x - cx
        dy = target_y - cy

        # capturing logic
        occupant = self.get_piece_at(row, col)
        if occupant is not None and self.whites_turn != self.pieces[occupant][3]:
            # a piece is already there, capture it
            self.canvas.delete(occupant)
            del self.pieces[occupant]  

        self.canvas.move(item, dx, dy)

        self.pieces[item] = (row, col, self.pieces[item][2], self.pieces[item][3])
        self.drag_data["item"] = None

        self.whites_turn = not self.whites_turn

    def get_piece_at(self, row, col):
        for item, (r, c, piece_code, iswhite) in self.pieces.items():
            if r == row and c == col:
                return item
        return None
    
    def menu(self):
        y_margins = 50

        x1 = self.square_size * 8
        y1 = 0
        x2 = x1 + self.menu_size
        y2 = self.square_size * 8
        self.canvas.create_rectangle(x1, y1, x2, y2, fill="#FFFFFF", outline = "")

        button = ttk.Button(self.root, text= "Play a game/reset", command=self.game_started)
        self.canvas.create_window(x1 + self.menu_size // 2, y_margins , window=button)

    def game_started(self):
        self.load_images()
        self.create_all_pieces()

        self.whites_turn = True


        #print("HI!")
