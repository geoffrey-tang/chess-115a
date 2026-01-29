import ttkbootstrap as ttk

def main():
    app = ttk.Window(themename="flatly")
    app.title("Python GUI Environment OK")
    ttk.Label(app, text="ttkbootstrap + tkinter is working ✅", padding=20).pack()
    app.mainloop()

if __name__ == "__main__":
    main()
