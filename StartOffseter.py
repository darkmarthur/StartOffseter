#!/usr/bin/env python3

import tkinter as tk
from tkinter import filedialog, ttk, scrolledtext
import subprocess
import os
import librosa
import numpy as np
from threading import Thread
from scipy.signal import butter, lfilter


# Utility Class
class Utility:
    @staticmethod
    def log_message(log_text, message, color="white"):
        log_text.configure(state='normal')
        log_text.tag_configure("info", foreground=color, font=("Helvetica", 12, "bold"))
        log_text.insert(tk.END, "\n" + message + "\n", "info")
        log_text.configure(state='disabled')
        log_text.yview(tk.END)

    @staticmethod
    def start_loading(loading_label):
        loading_label.grid()

    @staticmethod
    def stop_loading(loading_label):
        loading_label.grid_remove()

    @staticmethod
    def check_ffmpeg_installed():
        try:
            subprocess.run(['ffmpeg', '-version'], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            subprocess.run(['ffprobe', '-version'], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        except subprocess.CalledProcessError:
            return False
        return True


# Audio Processing Class
class AudioProcessor:
    @staticmethod
    def butter_bandpass(lowcut, highcut, fs, order=4):
        nyq = 0.5 * fs
        low = lowcut / nyq
        high = highcut / nyq
        b, a = butter(order, [low, high], btype='band')
        return b, a

    @staticmethod
    def bandpass_filter(data, lowcut, highcut, fs, order=4):
        b, a = AudioProcessor.butter_bandpass(lowcut, highcut, fs, order=order)
        return lfilter(b, a, data)

    @staticmethod
    def prepare_audio(y, sr):
        if y.ndim > 1:
            y = np.mean(y, axis=1)
        y = AudioProcessor.bandpass_filter(y, lowcut=30, highcut=160, fs=sr, order=4)
        y = np.nan_to_num(y, nan=0.0, posinf=0.0, neginf=0.0)
        if not np.all(np.isfinite(y)):
            y = y[np.isfinite(y)]
        max_abs_value = np.max(np.abs(y)) if np.max(np.abs(y)) != 0 else 1.0
        y = y / max_abs_value
        return y

    @staticmethod
    def calculate_bpm_robust(file_path, log_text):
        try:
            y, sr = librosa.load(file_path, sr=None)
            y = AudioProcessor.prepare_audio(y, sr)
            onset_env = librosa.onset.onset_strength(y=y, sr=sr, aggregate=np.median)
            tempo, _ = librosa.beat.beat_track(onset_envelope=onset_env, sr=sr)
            if tempo is not None and tempo.size > 0:
                tempo = float(tempo.item())  # Extract scalar value and convert to float
                Utility.log_message(log_text, f"Detected tempo (BPM): {tempo:.2f}", "blue")
                return tempo
            else:
                Utility.log_message(log_text, "Failed to detect BPM. Defaulting to 120 BPM.", "red")
                return 120.0
        except Exception as e:
            Utility.log_message(log_text, f"Error calculating BPM: {str(e)}", "red")
            return 120.0


# File Handling Class
class FileHandler:
    @staticmethod
    def fix_wav_hex(output_file, log_text):
        with open(output_file, "rb+") as f:
            f.seek(20, 0)
            format_id = f.read(2)
            bint = int.from_bytes(format_id, byteorder='little', signed=False)
            if bint == 65534:
                Utility.log_message(log_text, f"Fixing Hex for: {output_file}")
                f.seek(-2, 1)
                f.write(b'\x01\x00')

    @staticmethod
    def generate_output_filename(input_file, rename_file_var, entries, track_type_var, log_text):
        if rename_file_var.get():
            key = entries["Key"].get()
            master_limit = entries["Master Limit"].get()
            bpm_value = entries["BPM"].get()
            bit_rate = entries["Bit Rate"].get()
            sample_rate = entries["Sample Rate"].get()
            dither = entries["Dither"].get()
            dedicated_to = entries["Dedicated To"].get()
            track_type = track_type_var.get()

            base_name = input_file.rsplit('.', 1)[0]
            output_file_name = f"{base_name} | {track_type} {key} {master_limit} {bpm_value} {bit_rate} {sample_rate} {dither} | {dedicated_to}.wav"
        else:
            base_name = input_file.rsplit('.', 1)[0]
            output_file_name = f"{base_name} - Offseted.wav"

        if os.path.exists(output_file_name):
            Utility.log_message(log_text, f"Output file {output_file_name} already exists. Replacing it.", "orange")

        return output_file_name

    @staticmethod
    def process_file(file_path, log_text, rename_file_var, bpm_option, beats_entry, entries, fix_wav_hex_var, track_type_var):
        try:
            bpm_value = None
            if bpm_option.get() == 'auto':
                bpm_value = AudioProcessor.calculate_bpm_robust(file_path, log_text)
            else:
                bpm_value = float(entries["BPM"].get().strip().upper().replace("BPM", ""))

            if bpm_value is not None and bpm_value > 0:
                entries["BPM"].delete(0, tk.END)
                entries["BPM"].insert(0, f"{bpm_value:.2f} BPM")
            else:
                Utility.log_message(log_text, "Failed to detect BPM. Defaulting to 120 BPM.", "red")
                entries["BPM"].delete(0, tk.END)
                entries["BPM"].insert(0, "120 BPM")

            output_file_path = FileHandler.generate_output_filename(file_path, rename_file_var, entries, track_type_var, log_text)
            FileHandler.execute_ffmpeg_command(file_path, output_file_path, bpm_value, beats_entry, entries, log_text)
            if fix_wav_hex_var.get():
                FileHandler.fix_wav_hex(output_file_path, log_text)
        except Exception as e:
            Utility.log_message(log_text, f"Error during processing: {str(e)}", "red")

    @staticmethod
    def execute_ffmpeg_command(input_file, output_file, bpm_value, beats_entry, entries, log_text):
        probe_command = [
            'ffprobe', '-v', 'error',
            '-select_streams', 'a:0', '-show_entries', 'stream=sample_rate,channels',
            '-of', 'default=noprint_wrappers=1:nokey=1',
            input_file
        ]
        probe_result = subprocess.run(probe_command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        sample_rate, channels = probe_result.stdout.split('\n')[:2]
        sample_rate, channels = sample_rate.strip(), channels.strip()

        beat_duration = 60 / bpm_value
        number_of_beats = float(beats_entry.get())
        silence_duration = beat_duration * number_of_beats

        # Log the silence duration
        Utility.log_message(log_text, f"Adding {silence_duration:.4f} seconds of silence to the beginning of the track.", "blue")

        command = [
            'ffmpeg',
            '-f', 'lavfi',
            '-t', f'{silence_duration:.4f}',
            '-i', f'anullsrc=r={sample_rate}:cl={channels}',
            '-i', input_file,
            '-filter_complex', '[0][1]concat=n=2:v=0:a=1[out]',
            '-map', '[out]',
            '-ar', sample_rate,
            '-ac', channels,
            '-c:a', 'pcm_s24le',
            output_file
        ]
        result = subprocess.run(command, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        if result.returncode == 0:
            Utility.log_message(log_text, "Successfully added silence to the track beginning!", "green")
            Utility.log_message(log_text, f"Output file saved as: {output_file}", "green")
        else:
            Utility.log_message(log_text, f"FFmpeg output:\n{result.stdout}", "black")
            Utility.log_message(log_text, f"FFmpeg errors:\n{result.stderr}", "red")
            Utility.log_message(log_text, "OPERATION FAILED", "red")

    @staticmethod
    def convert_to_mp3(input_file, log_text):
        try:
            output_file = input_file.rsplit('.', 1)[0] + ".mp3"
            command = [
                'ffmpeg',
                '-i', input_file,
                '-codec:a', 'libmp3lame',
                '-b:a', '320k',
                output_file
            ]
            result = subprocess.run(command, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            if result.returncode == 0:
                Utility.log_message(log_text, "Successfully converted to MP3 format!", "green")
                Utility.log_message(log_text, f"MP3 file saved as: {output_file}", "green")
            else:
                Utility.log_message(log_text, f"FFmpeg output:\n{result.stdout}", "black")
                Utility.log_message(log_text, f"FFmpeg errors:\n{result.stderr}", "red")
                Utility.log_message(log_text, "MP3 CONVERSION FAILED", "red")
        except subprocess.CalledProcessError as e:
            Utility.log_message(log_text, f"MP3 conversion failed: {str(e)}", "red")
        except Exception as e:
            Utility.log_message(log_text, f"Unexpected error during MP3 conversion: {str(e)}", "red")


# Main Application Class
class StartOffseterApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("StartOffseter.app")
        self.setup_ui()

        if not Utility.check_ffmpeg_installed():
            self.quit()

    def setup_ui(self):
        style = ttk.Style()
        style.configure('TButton', font=('Helvetica', 12))
        style.configure('TCheckbutton', font=('Helvetica', 12))
        style.configure('TRadiobutton', font=('Helvetica', 12))
        style.configure('TLabel', font=('Helvetica', 12))
        style.configure('TEntry', font=('Helvetica', 12))
        style.configure('TFrame', padding=10)

        self.main_frame = ttk.Frame(self)
        self.main_frame.pack(padx=10, pady=10, fill='both', expand=True)

        # Number of Beats of Silence at the Beginning
        ttk.Label(self.main_frame, text="Number of Beats of Silence at the Beginning:").grid(row=0, column=0, sticky='w', pady=2)
        self.beats_entry = ttk.Entry(self.main_frame)
        self.beats_entry.insert(0, "1")
        self.beats_entry.grid(row=0, column=1, pady=2, sticky='ew')

        # Checkbox to rename file
        self.rename_file_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(self.main_frame, text="Rename File With Specifications", variable=self.rename_file_var, command=self.toggle_fields).grid(row=1, column=0, columnspan=2, sticky='w', pady=5)

        # Radio buttons for BPM selection
        self.bpm_option = tk.StringVar(value='manual')
        ttk.Radiobutton(self.main_frame, text="Specify BPM", variable=self.bpm_option, value='manual').grid(row=2, column=0, sticky='w', pady=2)
        ttk.Radiobutton(self.main_frame, text="Auto-detect BPM", variable=self.bpm_option, value='auto').grid(row=2, column=1, sticky='w', pady=2)

        # Input fields
        self.fields = {
            "Key": "Cmin",
            "Master Limit": "-0.3db",
            "BPM": "120BPM",
            "Bit Rate": "24Bits",
            "Sample Rate": "48Khz",
            "Dither": "Triangular",
            "Dedicated To": "Family & Friends"
        }

        self.entries = {}
        row_index = 3
        for field, default_value in self.fields.items():
            ttk.Label(self.main_frame, text=field + ":").grid(row=row_index, column=0, sticky='w', pady=2)
            entry = ttk.Entry(self.main_frame)
            entry.insert(0, default_value)
            entry.grid(row=row_index, column=1, pady=2, sticky='ew')
            self.entries[field] = entry
            row_index += 1

        # Dropdown menu for track type
        self.track_type_var = tk.StringVar(value="DEMO")
        ttk.Label(self.main_frame, text="Track Type:").grid(row=row_index, column=0, sticky='w', pady=2)
        track_type_dropdown = ttk.Combobox(self.main_frame, textvariable=self.track_type_var, values=["DEMO", "MASTER", "MIX", "LOOP", "IDEA", "JAM", "LIVE"])
        track_type_dropdown.grid(row=row_index, column=1, pady=2, sticky='ew')
        row_index += 1

        # Checkbox to fix WAV HEX values
        self.fix_wav_hex_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(self.main_frame, text="Fix WAV HEX Values (Pioneer Error E-8305)", variable=self.fix_wav_hex_var).grid(row=row_index, column=0, columnspan=2, sticky='w', pady=5)

        # Unified Log Area with dark background and white text
        self.log_text = scrolledtext.ScrolledText(self.main_frame, wrap=tk.WORD, height=15, state='disabled')
        self.log_text.grid(row=row_index+2, column=0, columnspan=2, pady=10, sticky='nsew')
        self.log_text.configure(foreground="white", background="#2e2e2e")

        # Open File and Exit Buttons in a single row
        button_frame = ttk.Frame(self.main_frame)
        button_frame.grid(row=row_index+3, column=0, columnspan=2, pady=10)

        ttk.Button(button_frame, text="Open File", command=self.open_file_dialog).pack(side=tk.LEFT, padx=10)
        ttk.Button(button_frame, text="Convert to MP3", command=self.convert_to_mp3).pack(side=tk.LEFT, padx=10)
        ttk.Button(button_frame, text="Exit", command=self.quit).pack(side=tk.RIGHT, padx=10)

        # Loading label (spinner)
        self.loading_label = ttk.Label(self.main_frame, text="Processing...", font=('Helvetica', 12))
        self.loading_label.grid(row=row_index+4, column=0, columnspan=2, pady=10)
        self.loading_label.grid_remove()

        self.main_frame.columnconfigure(0, weight=1)
        self.main_frame.columnconfigure(1, weight=1)

    def toggle_fields(self):
        state = tk.NORMAL if self.rename_file_var.get() else tk.DISABLED
        for entry in self.entries.values():
            entry.config(state=state)

    def open_file_dialog(self):
        file_path = filedialog.askopenfilename(title="Select a File", filetypes=[("WAV files", "*.wav")])
        if file_path:
            Utility.log_message(self.log_text, f"Selected File: {file_path}")
            Utility.start_loading(self.loading_label)
            Thread(target=FileHandler.process_file, args=(file_path, self.log_text, self.rename_file_var, self.bpm_option, self.beats_entry, self.entries, self.fix_wav_hex_var, self.track_type_var)).start()

    def convert_to_mp3(self):
        file_path = filedialog.askopenfilename(title="Select a WAV File to Convert", filetypes=[("WAV files", "*.wav")])
        if file_path:
            Utility.log_message(self.log_text, f"Converting File: {file_path}")
            Thread(target=FileHandler.convert_to_mp3, args=(file_path, self.log_text)).start()


if __name__ == "__main__":
    app = StartOffseterApp()
    app.mainloop()
