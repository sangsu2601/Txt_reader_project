import os
import json
import customtkinter as ctk
from tkinter import filedialog, StringVar

SETTINGS_FILE = "settings.json"

class EbookReader(ctk.CTk):
    def __init__(self):
        super().__init__()

        # 창 설정
        self.title("SimpleText")
        self.geometry("400x700")  # 핸드폰과 유사한 세로로 긴 창
        self.resizable(True, True)  # 사용자 창 크기 조정 허용

        # 기본 변수
        self.text_widget = None
        self.scrollbar = None
        self.filepath = None
        self.current_position = 0.0
        self.font_size = 12  # 기본 글씨 크기
        self.search_query = StringVar()  # 검색어 저장
        self.search_results = []  # 검색 결과 위치 저장
        self.current_search_index = -1  # 현재 검색 위치

        self.window_opacity = 1.0  # 기본 투명도 (1.0)

        # UI 생성
        self.create_ui()

        # 설정 로드
        self.load_settings()

    def create_ui(self):
        # 버튼 프레임
        self.button_frame = ctk.CTkFrame(self)
        self.button_frame.pack(pady=10, padx=10, fill="x")

        self.open_button = ctk.CTkButton(
            self.button_frame, text="Open File", command=self.open_file
        )
        self.open_button.pack(side="left", padx=5)

        self.increase_font_button = ctk.CTkButton(
            self.button_frame, text="+", width=30, command=self.increase_font
        )
        self.increase_font_button.pack(side="left", padx=5)

        self.decrease_font_button = ctk.CTkButton(
            self.button_frame, text="-", width=30, command=self.decrease_font
        )
        self.decrease_font_button.pack(side="left", padx=5)

        self.search_entry = ctk.CTkEntry(
            self.button_frame, textvariable=self.search_query, placeholder_text="Search..."
        )
        self.search_entry.pack(side="left", padx=5, fill="x", expand=True)
        self.search_entry.bind("<Return>", lambda event: self.search_word())

        self.text_frame = ctk.CTkFrame(self, width=380, height=600)
        self.text_frame.pack(expand=True, fill="both")

        self.text_widget = ctk.CTkTextbox(self.text_frame, wrap="word")
        self.text_widget.pack(side="left", fill="both", expand=True)
        self.text_widget.bind("<MouseWheel>", self.track_scroll_position)

        self.text_widget.bind("<Up>", lambda event: self.scroll_up())
        self.text_widget.bind("<Down>", lambda event: self.scroll_down())
        self.text_widget.bind("<Escape>", lambda event: self.clear_highlight())

        self.slider_frame = ctk.CTkFrame(self)
        self.slider_frame.pack(pady=10, padx=10, fill="x")

        self.opacity_label = ctk.CTkLabel(self.slider_frame, text="")
        self.opacity_label.pack(side="left", padx=5)

        self.opacity_slider = ctk.CTkSlider(
            self.slider_frame,
            from_=0.3,
            to=1.0,
            number_of_steps=70,
            command=self.change_opacity,
        )
        self.opacity_slider.set(self.window_opacity)
        self.opacity_slider.pack(side="left", fill="x", expand=True, padx=5)

    def change_opacity(self, value):
        """슬라이더 값에 따라 창의 투명도를 변경"""
        self.window_opacity = float(value)
        self.attributes("-alpha", self.window_opacity)

    def open_file(self):
        file_path = filedialog.askopenfilename(filetypes=[("Text files", "*.txt")])
        if file_path:
            self.filepath = file_path
            self.load_text(file_path)

    def load_text(self, file_path):
        try:
            with open(file_path, "r", encoding="utf-8") as file:
                content = file.read()

            self.text_widget.configure(state="normal")
            self.text_widget.delete("1.0", "end")
            self.text_widget.insert("1.0", content)

            if 0.0 <= self.current_position <= 1.0:
                self.text_widget.yview_moveto(self.current_position)
            else:
                print(f"Invalid scroll position: {self.current_position}")

            self.text_widget.configure(state="disabled")
            self.update_font()

        except Exception as e:
            print(f"Error loading file: {e}")

    def track_scroll_position(self, event=None):
        if self.text_widget:
            self.current_position = self.text_widget.yview()[0]
            self.save_settings()

    def increase_font(self):
        if self.font_size < 30:
            self.font_size += 1
            self.update_font()

    def decrease_font(self):
        if self.font_size > 8:
            self.font_size -= 1
            self.update_font()

    def update_font(self):
        self.text_widget.configure(font=("Arial", self.font_size))

    def search_word(self):
        query = self.search_query.get().strip()
        if not query:
            return

        if self.search_results:
            self.current_search_index = (self.current_search_index + 1) % len(self.search_results)
            self.move_to_search_result()
            return

        self.text_widget.tag_remove("highlight", "1.0", "end")
        self.search_results.clear()
        self.current_search_index = -1

        start_pos = "1.0"
        while True:
            start_pos = self.text_widget.search(query, start_pos, stopindex="end")
            if not start_pos:
                break
            end_pos = f"{start_pos}+{len(query)}c"
            self.text_widget.tag_add("highlight", start_pos, end_pos)
            self.search_results.append(start_pos)
            start_pos = end_pos

        self.text_widget.tag_config("highlight", background="yellow", foreground="black")

        if self.search_results:
            self.current_search_index = 0
            self.move_to_search_result()

    def move_to_search_result(self):
        if self.search_results and self.current_search_index != -1:
            pos = self.search_results[self.current_search_index]
            self.text_widget.see(pos)
            self.text_widget.mark_set("insert", pos)

    def scroll_up(self):
        self.text_widget.yview_scroll(-1, "units")
        return "break"

    def scroll_down(self):
        self.text_widget.yview_scroll(1, "units")
        return "break"

    def clear_highlight(self):
        self.text_widget.tag_remove("highlight", "1.0", "end")
        self.search_results.clear()
        self.current_search_index = -1

    def load_settings(self):
        if os.path.exists(SETTINGS_FILE):
            try:
                with open(SETTINGS_FILE, "r") as file:
                    settings = json.load(file)
                self.filepath = settings.get("filepath", None)
                self.current_position = settings.get("current_position", 0.0)
                self.font_size = settings.get("font_size", 12)

                if self.filepath and os.path.exists(self.filepath):
                    self.load_text(self.filepath)
                else:
                    print("No file found to restore.")
            except Exception as e:
                print(f"Error loading settings: {e}")

    def save_settings(self):
        
        settings = {
            "filepath": self.filepath,
            "current_position": self.current_position,
            "font_size": self.font_size,
        }
        try:
            with open(SETTINGS_FILE, "w") as file:
                json.dump(settings, file)
        except Exception as e:
            print(f"Error saving settings: {e}")

if __name__ == "__main__":
    ctk.set_appearance_mode("System")
    ctk.set_default_color_theme("blue")

    app = EbookReader()
    app.mainloop()
