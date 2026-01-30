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

        self.setup_ui()
        self.draw_board()

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

    def draw_board(self):
        self.canvas.delete("all")

        # Draw squares
        for rank in range(8):
            for file in range(8):
                x1 = file * self.square_size
                y1 = rank * self.square_size
                x2 = x1 + self.square_size
                y2 = y1 + self.square_size

                color = self.light_square if (rank + file) % 2 == 0 else self.dark_square

                self.canvas.create_rectangle(x1, y1, x2, y2, fill=color)
