import tkinter as tk
import ttkbootstrap as ttk


class ChessGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Chess Board")

        self.square_size = 100

        # Colors
        # Feel free to mess with this
        self.light_square = "#FFFFFF"
        self.dark_square = "#000000"

        self.drag_data = {"x": 0, "y": 0, "item": None}

        self.setup_ui()
        self.draw_board()

        self.pieces = {}
        self.create_all_pieces()

    def setup_ui(self):
        main_frame = ttk.Frame(self.root, padding=10)
        main_frame.pack()

        # Canvas for chess board
        self.canvas = tk.Canvas(
            main_frame,
            width=self.square_size * 8,
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

    def create_piece(self, row, col, color):
        size = 80
        pad = (self.square_size - size) // 2
        
        x1 = col * self.square_size + pad
        y1 = row * self.square_size + pad
        x2 = x1 + size
        y2 = y1 + size

        piece = self.canvas.create_oval(
                x1, y1, x2, y2,
                fill = color,
                tags=("piece", "draggable")
        )

        self.pieces[piece] = (row, col)

    def create_all_pieces(self):
        for col in range(8):
            self.create_piece(1, col, "white")
            self.create_piece(6, col, "black")

        self.create_piece(0, 0, "white")
        self.create_piece(0, 7, "white")
        self.create_piece(7, 0, "black")
        self.create_piece(7, 7, "black")

    def drag_start(self, event):
        item = self.canvas.find_closest(event.x, event.y)[0]

        if "piece" not in self.canvas.gettags(item):
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
        
        x1, y1, x2, y2 = self.canvas.coords(item)
        cx = (x1 + x2) // 2
        cy = (y1 + y2) // 2

        col = max(0, min(7, cx // self.square_size))
        row = max(0, min(7, cy // self.square_size))

        target_x = col * self.square_size + self.square_size // 2
        target_y = row * self.square_size + self.square_size // 2

        dx = target_x - cx
        dy = target_y - cy

        self.canvas.move(item, dx, dy)

        self.pieces[item] = (row, col)
        self.drag_data["item"] = None
