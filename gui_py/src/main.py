import ttkbootstrap as ttk
from chess_board import ChessGUI


def main():
    # Can check out the different themes at 
    # https://ttkbootstrap.readthedocs.io/en/latest/themes/
    app = ttk.Window(themename="cosmo")
    ChessGUI(app)
    app.mainloop()


if __name__ == "__main__":

    main()
