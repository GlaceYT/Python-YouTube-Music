import tkinter as tk
from tkinter import ttk, messagebox
import pygame
import pytube
import io
import subprocess
from googleapiclient.discovery import build
import threading
import time
import os

class MusicPlayerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Music Player")
        self.root.geometry("1280x720")
        
        # Define glassmorphism colors
        self.glassmorphism_colors = {
            "bg_color": "#1E1E1E",
            "glass_color": "#1E1E1E",
            "glass_intensity": 0.4,
            "glass_blur": 20,
            "glass_border_color": "#FFFFFF",
            "glass_border_width": 2,
        }

        # Apply glassmorphism colors to the style
        self.style = ttk.Style()
        self.style.theme_use("arc")  # Use the "arc" theme for ttk widgets
        self.configure_styles()

        # Apply glassmorphism effect to the root window
        self.root.configure(bg=self.glassmorphism_colors["bg_color"])
        self.root.overrideredirect(True)
        self.root.attributes("-alpha", self.glassmorphism_colors["glass_intensity"])
        self.root.attributes("-transparentcolor", self.glassmorphism_colors["bg_color"])

        # Create frames and widgets
        self.create_widgets()

        # Initialize variables
        self.current_song_index = -1
        self.playing = False
        self.song_urls = []
        self.queue = []

        # Initialize Pygame mixer
        pygame.mixer.init()

        # Start thread for updating progress bar and song playback
        self.update_thread = threading.Thread(target=self.update_thread_function, daemon=True)
        self.update_thread.start()

    def configure_styles(self):
        self.style.configure("TLabel", background=self.glassmorphism_colors["bg_color"])
        self.style.configure("TButton", background=self.glassmorphism_colors["bg_color"])
        self.style.configure("TPanedwindow", background=self.glassmorphism_colors["bg_color"])
        self.style.configure("TFrame", background=self.glassmorphism_colors["bg_color"])
        self.style.configure("TEntry", background=self.glassmorphism_colors["bg_color"])
        self.style.configure("TProgressbar", background=self.glassmorphism_colors["bg_color"])
        self.style.configure("Custom.Horizontal.TScale", troughcolor=self.glassmorphism_colors["bg_color"], background="#1DB954", sliderthickness=20)

    def create_widgets(self):
        # Create a glassmorphism frame
        self.frame = ttk.Frame(self.root, width=1280, height=720, style="Custom.TFrame")
        self.frame.place(relx=0.5, rely=0.5, anchor=tk.CENTER)

        # Create a glassmorphism panel
        self.panel = ttk.Panedwindow(self.frame, orient=tk.VERTICAL, style="Custom.TPanedwindow")
        self.panel.place(relx=0.5, rely=0.5, anchor=tk.CENTER)

        # Create a glassmorphism frame for the top panel
        self.top_frame = ttk.Frame(self.panel, width=1280, height=100, style="Custom.TFrame")
        self.top_frame.place(relx=0.5, rely=0.5, anchor=tk.CENTER)

        # Create a glassmorphism frame for the bottom panel
        self.bottom_frame = ttk.Frame(self.panel, width=1280, height=620, style="Custom.TFrame")
        self.bottom_frame.place(relx=0.5, rely=0.5, anchor=tk.CENTER)

        # Add the top and bottom frames to the panel
        self.panel.add(self.top_frame)
        self.panel.add(self.bottom_frame)

        # Define GUI elements for the music player
        self.label_username_top_right = ttk.Label(self.top_frame, text="", background=self.glassmorphism_colors["bg_color"],
                                                  font=("Helvetica", 12))
        self.label_username_top_right.place(x=999, y=20, width=120, height=25)

        # Add other GUI elements here...

    def search_song(self):
        query = self.entry_song.get()
        self.listbox_songs.delete(0, tk.END)
        # Show loading animation
        self.button_search.config(text="Searching...", state=tk.DISABLED)
        self.root.update()

        try:
            self.song_urls = self.search_youtube(query)
            if self.song_urls:
                for i, song in enumerate(self.song_urls):
                    self.listbox_songs.insert(i, song['title'])
            else:
                messagebox.showinfo("Information", "No songs found.")
        except Exception as e:
            messagebox.showerror("Error", f"Error searching for song: {e}")
        finally:
            # Reset button state and text
            self.button_search.config(text="Search", state=tk.NORMAL)

    def search_youtube(self, query):
        api_key = "AIzaSyB70-LdaZbmcqWX_GlknBloDhfweO4xJRc"
        youtube = build('youtube', 'v3', developerKey=api_key)
        request = youtube.search().list(
            q=query,
            part='snippet',
            type='video',
            maxResults=5
        )
        response = request.execute()
        results = []
        for item in response.get('items', []):
            video_id = item['id']['videoId']
            title = item['snippet']['title']
            results.append({'title': title, 'video_id': video_id})
        return results

    def add_to_queue(self, event):
        selected_index = self.listbox_songs.curselection()
        if selected_index:
            selected_index = int(selected_index[0])
            if 0 <= selected_index < len(self.song_urls):
                video_id = self.song_urls[selected_index]['video_id']
                self.queue.append(self.song_urls[selected_index])
                self.update_queue_text()
                messagebox.showinfo("Queue", f"Added '{self.song_urls[selected_index]['title']}' to the queue.")
            else:
                messagebox.showwarning("Warning", "Invalid selection.")
        else:
            messagebox.showwarning("Warning", "No song selected.")

    def update_queue_text(self):
        self.text_queue.config(state=tk.NORMAL)  # Enable editing
        self.text_queue.delete("1.0", tk.END)
        for song in self.queue:
            self.text_queue.insert(tk.END, f"{song['title']}\n")
        self.text_queue.config(state=tk.DISABLED)  # Disable editing

    def play_pause_song(self):
        if not self.queue:
            messagebox.showerror("Error", "No songs in the queue.")
            return

        if self.playing:
            pygame.mixer.music.pause()
            self.button_play_pause.config(text="▶️ Play")
        else:
            if self.current_song_index != -1:
                pygame.mixer.music.unpause()
                self.button_play_pause.config(text="⏸️ Pause")
            else:
                if self.queue:
                    self.current_song_index = 0
                    video_id = self.queue[0]['video_id']
                    self.play_song(video_id)
                    self.button_play_pause.config(text="⏸️ Pause")
        self.playing = not self.playing

    def play_song(self, video_id):
        url = f"https://www.youtube.com/watch?v={video_id}"
        try:
            yt = pytube.YouTube(url)
            audio_stream = yt.streams.filter(only_audio=True).first()
            audio_stream_bytes = io.BytesIO()
            audio_stream.stream_to_buffer(audio_stream_bytes)
            ffmpeg_process = subprocess.Popen(
                [self.ffmpeg_path, "-i", "pipe:", "-f", "wav", "pipe:"],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            stdout, stderr = ffmpeg_process.communicate(input=audio_stream_bytes.getvalue())

            if ffmpeg_process.returncode == 0:
                pygame.mixer.music.load(io.BytesIO(stdout))
                pygame.mixer.music.set_volume(self.volume_var.get() / 100)  # Set volume
                pygame.mixer.music.play()
                self.label_current_song.config(text=self.queue[self.current_song_index]['title'])
                self.label_playing.config(
                    text=f"Currently Playing: {self.queue[self.current_song_index]['title']}")
                self.song_length = pygame.mixer.Sound(io.BytesIO(stdout)).get_length()
            else:
                print("Error converting audio stream to WAV format:", stderr.decode("utf-8"))
        except Exception as e:
            messagebox.showerror("Error", f"Error playing song: {e}")

    def skip_song(self):
        if self.current_song_index < len(self.queue) - 1:
            self.current_song_index += 1
            video_id = self.queue[self.current_song_index]['video_id']
            self.play_song(video_id)
            self.button_play_pause.config(text="⏸️ Pause")

    def previous_song(self):
        if not self.queue:
            messagebox.showerror("Error", "No songs in the queue.")
            return

        if self.current_song_index > 0:
            self.current_song_index -= 1
            video_id = self.queue[self.current_song_index]['video_id']
            self.play_song(video_id)
            self.button_play_pause.config(text="⏸️ Pause")
        else:
            messagebox.showinfo("Information", "No previous song in the queue.")

    def update_thread_function(self):
        while True:
            if self.playing:
                current_position = pygame.mixer.music.get_pos() / 1000
                self.progress_value = (current_position / self.song_length) * 100
                self.progress_var.set(self.progress_value)

                if self.progress_value >= 95:
                    self.skip_song()

            time.sleep(1)

    def update_volume(self, event=None):
        pygame.mixer.music.set_volume(self.volume_var.get() / 100)


root = tk.Tk()
style = ttk.Style()
style.theme_use("clam")  # Use the "clam" theme for ttk widgets
style.configure("Thin.Horizontal.TProgressbar", troughcolor="white", background="#1DB954", thickness=4)  # Customize progress bar
style.configure("Custom.Horizontal.TScale", troughcolor="white", background="#1DB954", sliderthickness=20)  # Customize scale/slider

app = MusicPlayerApp(root)
root.mainloop()
