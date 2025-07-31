from view import WordUp
import ttkbootstrap as ttk


def set_and_center_window_geometry(window):
    screen_width = window.winfo_screenwidth()
    screen_height = window.winfo_screenheight()

    geometry = WordUp.app_geometry  # avoiding winfo_width winfo_height in case of rendering delay
    width, height = geometry.split('+')[0].split('x')
    width = int(width)
    height = int(height)
    x = (screen_width // 2) - (width // 2)
    y = (screen_height // 2) - (height // 2) - 30

    window.geometry(f'{width}x{height}+{x}+{y}')


if __name__ == '__main__':
    window = ttk.Window(themename=WordUp.app_theme)
    window.title(WordUp.app_name)
    window.resizable(False, False)
    set_and_center_window_geometry(window)

    app = WordUp(window)

    window.mainloop()

