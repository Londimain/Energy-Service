from tkinter import ttk


def setup_style(screen_width):
    style = ttk.Style()
    style.theme_use('clam')

    bg = '#2b2b2b'
    fg = '#ffffff'
    select_bg = '#1e6b9e'
    select_fg = '#ffffff'
    heading_bg = "#5c3377"
    heading_fg = '#ffffff'

    font_size = 9 if screen_width < 1024 else 10
    heading_font_size = 8 if screen_width < 1024 else 10

    style.configure('TFrame', background=bg)
    style.configure('TLabel', background=bg, foreground=fg, font=('Segoe UI', font_size))

    nav_padding = (5, 3) if screen_width < 1024 else (10, 5)

    nav_pressed_bg = '#4a5a6a'
    active_nav_pressed_bg = '#5a6a7a'
    action_pressed_bg = '#4d6a7a'

    style.configure('Nav.TButton',
                    background='#2c3e50',
                    foreground='#ffffff',
                    borderwidth=1,
                    focusthickness=3,
                    focuscolor='none',
                    padding=nav_padding)
    style.map('Nav.TButton',
              background=[('active', '#3a5a6a'), ('pressed', nav_pressed_bg)],
              foreground=[('active', '#ffffff'), ('pressed', '#ffffff')])

    style.configure('ActiveNav.TButton',
                    background='#3a4a5a',
                    foreground='#ffffff',
                    borderwidth=1,
                    focusthickness=3,
                    focuscolor='none',
                    padding=nav_padding)
    style.map('ActiveNav.TButton',
              background=[('active', '#4a5a6a'), ('pressed', active_nav_pressed_bg)],
              foreground=[('active', '#ffffff'), ('pressed', '#ffffff')])

    style.configure('Action.TButton',
                    background='#2d4a5a',
                    foreground='#ffffff',
                    borderwidth=1,
                    focusthickness=3,
                    focuscolor='none',
                    padding=nav_padding)
    style.map('Action.TButton',
              background=[('active', '#3d5a6a'), ('pressed', action_pressed_bg)],
              foreground=[('active', '#ffffff'), ('pressed', '#ffffff')])

    PRESSED_COLOR = '#4a5a6a'
    style.configure('NavPressed.TButton',
                    background=PRESSED_COLOR,
                    foreground='#ffffff',
                    borderwidth=1,
                    focusthickness=3,
                    focuscolor='none',
                    padding=nav_padding)
    style.configure('ActiveNavPressed.TButton',
                    background=PRESSED_COLOR,
                    foreground='#ffffff',
                    borderwidth=1,
                    focusthickness=3,
                    focuscolor='none',
                    padding=nav_padding)
    style.configure('ActionPressed.TButton',
                    background=PRESSED_COLOR,
                    foreground='#ffffff',
                    borderwidth=1,
                    focusthickness=3,
                    focuscolor='none',
                    padding=nav_padding)

    style.configure('TEntry', fieldbackground='#3c3c3c', foreground=fg, insertcolor=fg,
                    borderwidth=1, relief='solid')

    row_height = 26 if screen_width < 1024 else 28

    style.configure('Treeview',
                    background='#3c3c3c',
                    foreground=fg,
                    fieldbackground='#3c3c3c',
                    rowheight=row_height,
                    bordercolor='#888888',
                    borderwidth=2)
    style.map('Treeview',
              background=[('selected', select_bg)],
              foreground=[('selected', select_fg)],
              fieldbackground=[('selected', select_bg)])

    style.configure('Treeview.Heading',
                    background=heading_bg,
                    foreground=heading_fg,
                    relief='raised',
                    borderwidth=3,
                    font=('Segoe UI', heading_font_size, 'bold'))
    style.map('Treeview.Heading',
              background=[('active', "#713a9e")],
              foreground=[('active', '#ffffff')])

    style.configure('TLabelframe', background=bg, foreground=fg, borderwidth=2,
                    relief='groove')
    style.configure('TLabelframe.Label', background=bg, foreground=fg, font=('Segoe UI', heading_font_size, 'bold'))
    style.configure('TScrollbar', background='#3c3c3c', troughcolor='#2b2b2b',
                    arrowcolor=fg, borderwidth=0)