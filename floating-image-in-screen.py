import sys
import tkinter as tk
from tkinter import filedialog, messagebox
from PIL import Image, ImageTk
import tkinter.font as tkfont

try:
    RESAMPLE_FILTER = Image.Resampling.LANCZOS
except AttributeError:
    RESAMPLE_FILTER = Image.ANTIALIAS

# TEST

# REQUIRED_VERSION = (3, 13, 12)
# if tuple(sys.version_info[:3]) != REQUIRED_VERSION:
#     root_tmp = tk.Tk()
#     root_tmp.withdraw()
#     messagebox.showerror(
#         "Versión de Python incorrecta",
#         f"Se requiere Python {REQUIRED_VERSION[0]}.{REQUIRED_VERSION[1]}.{REQUIRED_VERSION[2]}.\nLa Versión actual: {sys.version.split()[0]} NO ES COMPATIBLE."
#     )
#     sys.exit(1)


class FloatingImageApp:
    def __init__(self, root):
        self.root = root
        self.root.overrideredirect(True)
        self.root.attributes("-topmost", True)
        self.root.configure(bg="#333333")

        self.top_frame = tk.Frame(self.root, bg="#222222")
        self.top_frame.pack(side=tk.TOP, fill=tk.X)

        self.move_button = tk.Label(self.top_frame, text="≡", fg="white", bg="#222222", cursor="fleur")
        self.move_button.pack(side=tk.LEFT, padx=6, pady=4)
        self.move_button.bind("<ButtonPress-1>", self.start_move)
        self.move_button.bind("<B1-Motion>", self.do_move)

        self.close_button = tk.Button(self.top_frame, text="✕", command=self.root.destroy, bg="#444444", fg="white", bd=0)
        self.close_button.pack(side=tk.RIGHT, padx=6, pady=2)

        self.image_label = tk.Label(self.root, bg="#333333")
        self.image_label.pack()

        self.controls = tk.Frame(self.root, bg="#333333")
        self.controls.pack(side=tk.BOTTOM, fill=tk.X, padx=10, pady=6)

        load_button = tk.Button(self.controls, text="Seleccionar imagen", command=self.select_image)
        load_button.pack(side=tk.LEFT, padx=5)

        opacity_label = tk.Label(self.controls, text="Opacidad:", fg="white", bg="#333333")
        opacity_label.pack(side=tk.LEFT, padx=(15, 5))

        self.opacity_scale = tk.Scale(self.controls, from_=20, to=100, orient=tk.HORIZONTAL,
                                       command=self.change_opacity, bg="#333333", fg="white", highlightthickness=0)
        self.opacity_scale.set(100)
        self.opacity_scale.pack(side=tk.LEFT, fill=tk.X, expand=True)

        small_font = tkfont.Font(size=8)
        self.credits_label = tk.Label(self.root, text="Créditos: WnDetonao. Ver: TSC-28426TF6 Comp T-114-02", fg="white", bg="#333333", font=small_font)
        self.credits_label.pack(side=tk.BOTTOM, pady=(0,4))

        self.current_image = None
        self.photo_image = None

        self.original_image = None

        self._offset_x = 0
        self._offset_y = 0

        self.resize_grip = tk.Label(self.root, bg="#222222", cursor="size_nw_se")
        self.resize_grip.place(relx=1.0, rely=1.0, anchor="se", x=-6, y=-6)
        self.resize_grip.bind("<ButtonPress-1>", self.start_resize)
        self.resize_grip.bind("<B1-Motion>", self.do_resize)

    def select_image(self):
        file_path = filedialog.askopenfilename(
            title="Seleccionar imagen",
            filetypes=[("Archivos de imagen", "*.png *.jpg *.jpeg *.bmp *.gif"), ("Todos los archivos", "*")]
        )
        if file_path:
            self.load_image(file_path)

    def load_image(self, path):
        try:
            image = Image.open(path)
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo cargar la imagen:\n{e}")
            return

        image = image.convert("RGBA")
        self.original_image = image
        image = self.resize_image(image)
        self.current_image = image
        self.photo_image = ImageTk.PhotoImage(image)
        self.image_label.config(image=self.photo_image)

        self.root.update_idletasks()
        img_w, img_h = self.current_image.size
        extra_w = 8
        extra_h = self.top_frame.winfo_reqheight() + self.controls.winfo_reqheight() + self.credits_label.winfo_reqheight() + 20
        total_w = img_w + extra_w
        total_h = img_h + extra_h
        screen_w = self.root.winfo_screenwidth()
        screen_h = self.root.winfo_screenheight()
        if total_w > screen_w:
            total_w = screen_w - 40
        if total_h > screen_h:
            total_h = screen_h - 40

        self.root.geometry(f"{total_w}x{total_h}")
        self.image_label.config(width=img_w, height=img_h)
        self.change_opacity(self.opacity_scale.get())

    def resize_image(self, image):
        self.root.update_idletasks()
        if isinstance(image, tuple):
            return image
        max_size = getattr(self, '_resize_max_size', None)
        if max_size is None:
            screen_w = self.root.winfo_screenwidth() - 80
            screen_h = self.root.winfo_screenheight() - 120
            max_size = (screen_w, screen_h)
        w, h = image.size
        if w <= max_size[0] and h <= max_size[1]:
            return image
        return image.copy().resize(self.fit_size(image.size, max_size), RESAMPLE_FILTER)

    def _get_image_for_area(self, area_size):
        if self.original_image is None:
            return None
        self._resize_max_size = area_size
        img = self.resize_image(self.original_image)
        delattr(self, '_resize_max_size')
        return img

    def fit_size(self, size, max_size):
        w, h = size
        max_w, max_h = max_size
        ratio = min(max_w / w, max_h / h)
        return int(w * ratio), int(h * ratio)

    def change_opacity(self, value):
        alpha = float(value) / 100
        self.root.attributes("-alpha", alpha)

    def start_move(self, event):
        self._offset_x = event.x_root - self.root.winfo_x()
        self._offset_y = event.y_root - self.root.winfo_y()

    def do_move(self, event):
        x = event.x_root - self._offset_x
        y = event.y_root - self._offset_y
        self.root.geometry(f"+{x}+{y}")

    def start_resize(self, event):
        self._resize_start_x = event.x_root
        self._resize_start_y = event.y_root
        self._resize_start_w = self.root.winfo_width()
        self._resize_start_h = self.root.winfo_height()

    def do_resize(self, event):
        dx = event.x_root - getattr(self, '_resize_start_x', event.x_root)
        dy = event.y_root - getattr(self, '_resize_start_y', event.y_root)
        new_w = max(100, self._resize_start_w + dx)
        new_h = max(80, self._resize_start_h + dy)
        # Aplicar nuevo tamaño de ventana
        self.root.geometry(f"{new_w}x{new_h}")

        extra_w = 8
        extra_h = self.top_frame.winfo_reqheight() + self.controls.winfo_reqheight() + self.credits_label.winfo_reqheight() + 20
        img_w = max(1, new_w - extra_w)
        img_h = max(1, new_h - extra_h)
        img = self._get_image_for_area((img_w, img_h))
        if img is not None:
            self.current_image = img
            self.photo_image = ImageTk.PhotoImage(img)
            self.image_label.config(image=self.photo_image)
            self.image_label.config(width=img_w, height=img_h)

if __name__ == "__main__":
    root = tk.Tk()
    app = FloatingImageApp(root)
    root.mainloop()

# Dont ask me how i made it work, i have no fucking idea and i dont think i will know it soon or later... maybe later