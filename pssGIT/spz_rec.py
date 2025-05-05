import os
import sys
import cv2
import numpy as np
import easyocr
import imutils
import serial
import time
import tkinter as tk
from tkinter import filedialog
from PIL import Image, ImageTk
import json
import serial.tools.list_ports

os.chdir(os.path.dirname(sys.executable if getattr(sys, 'frozen', False) else __file__))

def resource_path(relative_path):
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.abspath("."), relative_path)

spz_file = resource_path("spravne_spz.json")
history_file = resource_path("spz_history.json")

class SPZApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Aplikace pro rozpoznávání SPZ")
        self.root.geometry("600x740")
        self.center_window()
        self.root.resizable(False, False)
        self.root.configure(bg="#1e1e1e")

        self.spravne_spz_list = self.load_spravne_spz()
        self.spz_history = self.load_spz_history()

        common_btn_style = {
            "width": 30,
            "height": 2,
            "bg": "#333",
            "fg": "white",
            "font": ("Arial", 10, "bold"),
            "relief": "raised",
            "bd": 2
        }

        self.title_label = tk.Label(root, text="Aplikace pro rozpoznávání SPZ", font=("Arial", 16, "bold"), bg="#1e1e1e", fg="white")
        self.title_label.pack(pady=5)

        self.button_frame = tk.Frame(root, bg="#1e1e1e")
        self.button_frame.pack(pady=5)

        self.buttons = [
            tk.Button(self.button_frame, text="Vyber obrázek", command=self.process_file_image, **common_btn_style),
            tk.Button(self.button_frame, text="Použij webkameru", command=self.process_camera_image, **common_btn_style),
            tk.Button(self.button_frame, text="Náhled webkamery", command=self.toggle_camera_preview, **common_btn_style),
            tk.Button(self.button_frame, text="Zobraz SPZ seznam", command=self.show_spz_list, **common_btn_style),
            tk.Button(self.button_frame, text="Zobraz Historii SPZ", command=self.show_spz_history, **common_btn_style),
            tk.Button(self.button_frame, text="Přidat SPZ", command=self.add_spz, **common_btn_style),
            tk.Button(self.button_frame, text="Odebrat SPZ (index)", command=self.remove_spz, **common_btn_style),
            tk.Button(self.button_frame, text="Smazat Historii SPZ", command=self.clear_spz_history, **common_btn_style)
        ]

        for btn in self.buttons:
            btn.pack(pady=4)

        self.image_label = tk.Label(root, bg="#1e1e1e")
        self.image_label.pack(pady=10)

        self.result_label = tk.Label(root, text="", font=("Arial", 12), bg="#1e1e1e", fg="white")
        self.result_label.pack(pady=5)

        self.cap = None
        self.previewing = False
        
        arduino_port = self.find_arduino_port()
        if arduino_port:
            try:
                self.arduino = serial.Serial(arduino_port, 9600, timeout=1)
                time.sleep(2)
            except serial.SerialException:
                self.arduino = None
                self.custom_messagebox("Upozornění", f"Port {arduino_port} nalezen, ale nepodařilo se připojit k Arduinu.")
        else:
            self.arduino = None
            self.custom_messagebox("Upozornění", "Nepodařilo se automaticky najít Arduino port.")

        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

    def center_window(self):
        self.root.update_idletasks()
        width = self.root.winfo_width()
        height = self.root.winfo_height()
        x = (self.root.winfo_screenwidth() // 2) - (width // 2)
        y = (self.root.winfo_screenheight() // 2) - (height // 2)
        self.root.geometry(f'{width}x{height}+{x}+{y}')

    def find_arduino_port(self):
        ports = serial.tools.list_ports.comports()
        for port in ports:
            try:
                test_serial = serial.Serial(port.device, 9600, timeout=1)
                test_serial.close()
                return port.device
            except (serial.SerialException, OSError):
                continue
        return None

    def process_file_image(self):
        file_path = filedialog.askopenfilename(filetypes=[("Obrázky", "*.jpg *.jpeg *.png")])
        if file_path:
            img = cv2.imread(file_path)
            self.show_image(img)
            self.detect_spz(img)

    def process_camera_image(self):
        cap = cv2.VideoCapture(0)
        if not cap.isOpened():
            self.custom_messagebox("Chyba", "Nelze otevřít webkameru.")
            return
        ret, frame = cap.read()
        cap.release()
        if not ret:
            self.custom_messagebox("Chyba", "Nepodařilo se načíst snímek z kamery.")
        else:
            self.show_image(frame)
            self.detect_spz(frame)

    def toggle_camera_preview(self):
        if not self.previewing:
            self.previewing = True
            self.start_camera_preview()
        else:
            self.previewing = False
            self.stop_camera_preview()

    def start_camera_preview(self):
        self.cap = cv2.VideoCapture(0)
        if not self.cap.isOpened():
            self.custom_messagebox("Chyba", "Nelze otevřít webkameru.")
            return
        self.update_preview()

    def stop_camera_preview(self):
        if self.cap and self.cap.isOpened():
            self.cap.release()
        self.image_label.config(image="")
        self.result_label.config(text="")
        self.previewing = False

    def update_preview(self):
        if self.cap and self.cap.isOpened():
            ret, frame = self.cap.read()
            if not ret:
                return
            self.show_image(frame)
            if self.previewing:
                self.root.after(10, self.update_preview)

    def show_image(self, img):
        img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        img_pil = Image.fromarray(img_rgb).resize((300, 200))
        img_tk = ImageTk.PhotoImage(image=img_pil)
        self.image_label.imgtk = img_tk
        self.image_label.config(image=img_tk)

    def detect_spz(self, img):
        try:
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            bfilter = cv2.bilateralFilter(gray, 11, 17, 17)
            edged = cv2.Canny(bfilter, 30, 200)
            keypoints = cv2.findContours(edged.copy(), cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
            contours = imutils.grab_contours(keypoints)
            contours = sorted(contours, key=cv2.contourArea, reverse=True)[:10]

            location = None
            for contour in contours:
                approx = cv2.approxPolyDP(contour, 10, True)
                if len(approx) == 4:
                    location = approx
                    break

            if location is None:
                raise ValueError("Nepodařilo se najít SPZ.")

            mask = np.zeros(gray.shape, np.uint8)
            cv2.drawContours(mask, [location], 0, 255, -1)
            (x, y) = np.where(mask == 255)
            cropped_image = gray[np.min(x):np.max(x)+1, np.min(y):np.max(y)+1]

            reader = easyocr.Reader(['en'], gpu=False)
            result = reader.readtext(cropped_image)
            if not result:
                raise ValueError("OCR nerozpoznalo žádný text.")
            text = result[0][-2].replace(" ", "")
            
            font = cv2.FONT_HERSHEY_SIMPLEX
            text_position = (10, img.shape[0] - 10)
            cv2.putText(img, f"SPZ: {text}", text_position, font, 1, (0, 255, 0), 2, cv2.LINE_AA)

            if text in self.spravne_spz_list:
                self.result_label.config(text=f"✅ SPZ '{text}' je správná!", fg="green")
                if self.arduino:
                    self.arduino.write(b'1')
            else:
                self.result_label.config(text=f"❌ SPZ '{text}' není v seznamu.", fg="red")
                if self.arduino:
                    self.arduino.write(b'0')

            self.update_spz_history(text)
            self.show_image(img)

        except Exception as e:
            self.custom_messagebox("Chyba", str(e))

    def load_spravne_spz(self):
        if os.path.exists(spz_file):
            try:
                with open(spz_file, "r") as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError) as e:
                self.custom_messagebox("Chyba", f"Chyba při načítání souboru SPZ: {e}")
        return []

    def save_spravne_spz(self):
        try:
            with open(spz_file, "w") as f:
                json.dump(self.spravne_spz_list, f)
        except IOError as e:
            self.custom_messagebox("Chyba", f"Chyba při ukládání souboru SPZ: {e}")

    def load_spz_history(self):
        if os.path.exists(history_file):
            try:
                with open(history_file, "r") as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError) as e:
                self.custom_messagebox("Chyba", f"Chyba při načítání historie SPZ: {e}")
        return []

    def save_spz_history(self):
        try:
            with open(history_file, "w") as f:
                json.dump(self.spz_history, f)
        except IOError as e:
            self.custom_messagebox("Chyba", f"Chyba při ukládání historie SPZ: {e}")

    def update_spz_history(self, spz):
        if spz not in [entry['spz'] for entry in self.spz_history]:
            self.spz_history.append({'spz': spz, 'star': '*' if spz in self.spravne_spz_list else ''})
            self.save_spz_history()

    def clear_spz_history(self):
        self.spz_history = []
        self.save_spz_history()
        self.custom_messagebox("Hotovo", "Historie SPZ byla smazána.")

    def show_spz_list(self):
        text = "\n".join([f"{i+1}. {spz}" for i, spz in enumerate(self.spravne_spz_list)])
        self.show_scrollable_popup("Seznam správných SPZ", text)

    def show_spz_history(self):
        text = "\n".join([f"{entry['spz']} {entry.get('star', '')}" for entry in self.spz_history])
        self.show_scrollable_popup("Historie SPZ", text)

    def show_scrollable_popup(self, title, content):
        top = tk.Toplevel(self.root, bg="#1e1e1e")
        top.title(title)
        top.geometry("400x300")

        frame = tk.Frame(top, bg="#1e1e1e")
        frame.pack(fill="both", expand=True, padx=10, pady=10)

        scrollbar = tk.Scrollbar(frame)
        scrollbar.pack(side="right", fill="y")

        text_widget = tk.Text(frame, wrap="word", yscrollcommand=scrollbar.set, bg="#2e2e2e", fg="white", font=("Arial", 11))
        text_widget.insert("1.0", content)
        text_widget.config(state="disabled")
        text_widget.pack(fill="both", expand=True)
        scrollbar.config(command=text_widget.yview)

        top.transient(self.root)
        top.grab_set()
        self.root.wait_window(top)

    def add_spz(self):
        spz = self.custom_input_dialog("Přidat SPZ", "Zadejte novou SPZ:")
        if spz and spz not in self.spravne_spz_list:
            self.spravne_spz_list.append(spz)
            self.save_spravne_spz()

    def remove_spz(self):
        index_str = self.custom_input_dialog("Odebrat SPZ", "Zadejte číslo SPZ k odebrání (od 1):")
        if index_str:
            try:
                index = int(index_str) - 1
                if 0 <= index < len(self.spravne_spz_list):
                    removed_spz = self.spravne_spz_list.pop(index)
                    self.save_spravne_spz()
                    self.custom_messagebox("Úspěch", f"SPZ '{removed_spz}' byla odebrána.")
                else:
                    self.custom_messagebox("Chyba", "Neplatné číslo SPZ.")
            except ValueError:
                self.custom_messagebox("Chyba", "Zadejte platné číslo.")

    def custom_messagebox(self, title, message):
        top = tk.Toplevel(self.root, bg="#1e1e1e")
        top.title(title)
        top.geometry("400x200")
        label = tk.Label(top, text=message, bg="#1e1e1e", fg="white", wraplength=380, font=("Arial", 12))
        label.pack(padx=20, pady=30)
        button = tk.Button(top, text="OK", command=top.destroy, bg="#333", fg="white", font=("Arial", 10, "bold"))
        button.pack(pady=10)
        top.transient(self.root)
        top.grab_set()
        self.root.wait_window(top)

    def custom_input_dialog(self, title, prompt):
        top = tk.Toplevel(self.root, bg="#1e1e1e")
        top.title(title)
        top.geometry("400x150")
        tk.Label(top, text=prompt, bg="#1e1e1e", fg="white", font=("Arial", 12)).pack(pady=10)
        entry = tk.Entry(top, font=("Arial", 12))
        entry.pack(pady=5)

        result = []

        def on_ok():
            result.append(entry.get())
            top.destroy()

        tk.Button(top, text="OK", command=on_ok, bg="#333", fg="white", font=("Arial", 10, "bold")).pack(pady=10)
        entry.focus()
        top.transient(self.root)
        top.grab_set()
        self.root.wait_window(top)
        return result[0] if result else None

    def on_close(self):
        if self.arduino:
            self.arduino.close()
        self.save_spravne_spz()
        self.save_spz_history()
        self.root.quit()

if __name__ == "__main__":
    root = tk.Tk()
    app = SPZApp(root)
    root.mainloop()
