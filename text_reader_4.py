import os
import json
import customtkinter as ctk
from tkinter import filedialog, StringVar


# 설정 파일 경로
SETTINGS_FILE = "settings.json"


class EbookReader(ctk.CTk):
    def __init__(self):
        super().__init__()

        # 창 설정
        self.title("eBook Reader")
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

        # UI 생성
        self.create_ui()

        # 설정 로드
        self.load_settings()

    def create_ui(self):
        # 버튼 프레임
        self.button_frame = ctk.CTkFrame(self)
        self.button_frame.pack(pady=10, padx=10, fill="x")

        # 파일 열기 버튼
        self.open_button = ctk.CTkButton(
            self.button_frame, text="Open File", command=self.open_file
        )
        self.open_button.pack(side="left", padx=5)

        # 글씨 크기 확대 버튼
        self.increase_font_button = ctk.CTkButton(
            self.button_frame, text="+", width=30, command=self.increase_font
        )
        self.increase_font_button.pack(side="left", padx=5)

        # 글씨 크기 축소 버튼
        self.decrease_font_button = ctk.CTkButton(
            self.button_frame, text="-", width=30, command=self.decrease_font
        )
        self.decrease_font_button.pack(side="left", padx=5)

        # 검색 입력창
        self.search_entry = ctk.CTkEntry(
            self.button_frame, textvariable=self.search_query, placeholder_text="Search..."
        )
        self.search_entry.pack(side="left", padx=5, fill="x", expand=True)
        self.search_entry.bind("<Return>", lambda event: self.search_word())  # 엔터 키 바인딩

        # 스크롤 가능한 텍스트 위젯
        self.text_frame = ctk.CTkFrame(self, width=380, height=600)
        self.text_frame.pack(expand=True, fill="both")

        self.text_widget = ctk.CTkTextbox(self.text_frame, wrap="word")
        self.text_widget.pack(side="left", fill="both", expand=True)
        self.text_widget.bind("<MouseWheel>", self.track_scroll_position)

        # 방향키 및 ESC 키 이벤트 바인딩
        self.text_widget.bind("<Up>", lambda event: self.scroll_up())
        self.text_widget.bind("<Down>", lambda event: self.scroll_down())
        self.text_widget.bind("<Escape>", lambda event: self.clear_highlight())

    def open_file(self):
        file_path = filedialog.askopenfilename(filetypes=[("Text files", "*.txt")])
        if file_path:
            self.filepath = file_path
            self.load_text(file_path)

    def load_text(self, file_path):
        try:
            with open(file_path, "r", encoding="utf-8") as file:
                content = file.read()

            self.text_widget.configure(state="normal")  # 편집 가능 상태로 설정
            self.text_widget.delete("1.0", "end")
            self.text_widget.insert("1.0", content)

            # 스크롤 복원
            if 0.0 <= self.current_position <= 1.0:
                self.text_widget.yview_moveto(self.current_position)
            else:
                print(f"Invalid scroll position: {self.current_position}")

            self.text_widget.configure(state="disabled")  # 다시 읽기 전용으로 설정
            self.update_font()

        except Exception as e:
            print(f"Error loading file: {e}")

    def track_scroll_position(self, event=None):
        # 현재 스크롤 위치 저장 (비율 기반)
        if self.text_widget:
            self.current_position = self.text_widget.yview()[0]
            self.save_settings()

    def increase_font(self):
        """글씨 크기를 키우는 함수"""
        if self.font_size < 30:  # 최대 글씨 크기 제한
            self.font_size += 1
            self.update_font()

    def decrease_font(self):
        """글씨 크기를 줄이는 함수"""
        if self.font_size > 8:  # 최소 글씨 크기 제한
            self.font_size -= 1
            self.update_font()

    def update_font(self):
        """텍스트 위젯의 글씨 크기를 업데이트"""
        self.text_widget.configure(font=("Arial", self.font_size))

    def search_word(self):
        """검색어로 텍스트 위젯에서 단어 검색"""
        query = self.search_query.get().strip()
        if not query:
            return

        if self.search_results:  # 이미 검색된 결과가 있으면 다음 결과로 이동
            self.current_search_index = (self.current_search_index + 1) % len(self.search_results)
            self.move_to_search_result()
            return

        # 검색 결과 초기화
        self.text_widget.tag_remove("highlight", "1.0", "end")
        self.search_results.clear()
        self.current_search_index = -1

        # 텍스트 검색
        start_pos = "1.0"
        while True:
            start_pos = self.text_widget.search(query, start_pos, stopindex="end")
            if not start_pos:
                break
            end_pos = f"{start_pos}+{len(query)}c"
            self.text_widget.tag_add("highlight", start_pos, end_pos)
            self.search_results.append(start_pos)
            start_pos = end_pos

        # 하이라이트 스타일
        self.text_widget.tag_config("highlight", background="yellow", foreground="black")

        if self.search_results:
            self.current_search_index = 0
            self.move_to_search_result()

    def move_to_search_result(self):
        """검색된 단어로 이동"""
        if self.search_results and self.current_search_index != -1:
            pos = self.search_results[self.current_search_index]
            self.text_widget.see(pos)
            self.text_widget.mark_set("insert", pos)

    def scroll_up(self):
        """위로 스크롤"""
        self.text_widget.yview_scroll(-1, "units")
        return "break"  # 기본 동작 방지

    def scroll_down(self):
        """아래로 스크롤"""
        self.text_widget.yview_scroll(1, "units")
        return "break"  # 기본 동작 방지

    def clear_highlight(self):
        """ESC 키로 하이라이트 제거"""
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
        # 현재 설정 저장
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
