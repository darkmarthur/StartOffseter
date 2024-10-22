#!/usr/bin/env python3

import tkinter as tk
from tkinter import filedialog, ttk, scrolledtext
import subprocess
import os

def check_ffmpeg_installed():
    try:
        subprocess.run(['ffmpeg', '-version'], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        subprocess.run(['ffprobe', '-version'], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    except subprocess.CalledProcessError:
        log_message("FFmpeg or FFprobe is not installed or not found in the system PATH.", "red")
        return False
    return True

def fixWavHex(output_file):
    with open(output_file, "rb+") as f:
        f.seek(20, 0)
        formatID = f.read(2)
        bint = int.from_bytes(formatID, byteorder='little', signed=False)
        if bint == 65534:
            log_message(f"Fixing Hex for: {output_file}")
            f.seek(-2, 1)
            f.write(b'\x01\x00')

def open_file_dialog():
    file_path = filedialog.askopenfilename(title="Select a File", filetypes=[("WAV files", "*.wav")])
    if file_path:
        log_message(f"Selected File: {file_path}")
        output_file_path = generate_output_filename(file_path)
        process_file(file_path, output_file_path)
        if fix_wav_hex_var.get():
            fixWavHex(output_file_path)

def generate_output_filename(input_file):
    if rename_file_var.get():
        key = key_entry.get()
        master_limit = master_limit_entry.get()
        bpm = bpm_entry.get()
        bit_rate = bit_rate_entry.get()
        sample_rate = sample_rate_entry.get()
        dither = dither_entry.get()
        dedicated_to = dedicated_to_entry.get()
        track_type = track_type_var.get()

        base_name = input_file.rsplit('.', 1)[0]
        output_file_name = f"{base_name} | {track_type} {key} {master_limit} {bpm} {bit_rate} {sample_rate} {dither} | {dedicated_to}.wav"
    else:
        base_name = input_file.rsplit('.', 1)[0]
        output_file_name = f"{base_name} - Offseted.wav"
    
    return output_file_name

def process_file(input_file, output_file):
    try:
        probe_command = [
            'ffprobe', '-v', 'error',
            '-select_streams', 'a:0', '-show_entries', 'stream=sample_rate,channels',
            '-of', 'default=noprint_wrappers=1:nokey=1',
            input_file
        ]
        probe_result = subprocess.run(probe_command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        sample_rate, channels = probe_result.stdout.split('\n')[:2]
        sample_rate = sample_rate.strip()
        channels = channels.strip()

        # Extract the BPM value from the bpm_entry text field
        bpm_text = bpm_entry.get().strip().upper()  # Get the text and make it uppercase to handle variations like "bpm"
        try:
            # Remove non-digit characters to extract the numeric BPM value
            bpm_value = float(''.join(filter(str.isdigit, bpm_text)))
            if bpm_value <= 0:
                raise ValueError("BPM must be a positive number.")
        except ValueError:
            log_message("Invalid BPM value. Defaulting to 120 BPM.", "red")
            bpm_value = 120  # Default to 120 BPM if input is invalid

        # Calculate beat duration in seconds
        beat_duration = 60 / bpm_value

        # Get the number of beats of silence to add
        try:
            number_of_beats = float(beats_entry.get())
            if number_of_beats <= 0:
                raise ValueError("Number of beats must be positive.")
        except ValueError:
            log_message("Invalid number of beats. Defaulting to 1 beat.", "red")
            number_of_beats = 1  # Default to 1 beat if input is invalid

        # Calculate total silence duration based on the number of beats
        silence_duration = beat_duration * number_of_beats

        # Log the calculated silence duration
        log_message(f"Silence added to the beginning of the track: {silence_duration:.4f} seconds", "blue")

        if not sample_rate or not channels:
            log_message("Could not determine sample rate or channels. Please select a valid WAV file.", "red")
            return

        # FFmpeg command to add silence
        command = [
            'ffmpeg',
            '-f', 'lavfi',
            '-t', f'{silence_duration:.4f}',  # Dynamically set duration based on number of beats
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
            log_message("Successfully added silence to the track beginning!", "green")
            log_message(f"Output file saved as: {output_file}", "green")
        else:
            log_message(f"FFmpeg output:\n{result.stdout}", "black")
            log_message(f"FFmpeg errors:\n{result.stderr}", "red")
            log_message("OPERATION FAILED", "red")
    except subprocess.CalledProcessError as e:
        log_message(f"Error: {e.stderr}", "red")
        log_message("OPERATION FAILED", "red")
    except Exception as e:
        log_message(f"Error: {str(e)}", "red")
        log_message("OPERATION FAILED", "red")

def toggle_fields():
    state = tk.NORMAL if rename_file_var.get() else tk.DISABLED
    for entry in entries.values():
        entry.config(state=state)

def log_message(message, color="white"):  # Default text color is white
    log_text.configure(state='normal')
    log_text.tag_configure("info", foreground=color, font=("Helvetica", 12, "bold"))
    log_text.insert(tk.END, "\n" + message + "\n", "info")
    log_text.configure(state='disabled')
    log_text.yview(tk.END)  # Auto-scroll to the end

root = tk.Tk()
root.title("StartOffseter.app")

if not check_ffmpeg_installed():
    root.quit()

style = ttk.Style()
style.configure('TButton', font=('Helvetica', 12))
style.configure('TCheckbutton', font=('Helvetica', 12))
style.configure('TLabel', font=('Helvetica', 12))
style.configure('TEntry', font=('Helvetica', 12))
style.configure('TFrame', padding=10)

main_frame = ttk.Frame(root)
main_frame.pack(padx=10, pady=10, fill='both', expand=True)

# Text field for Number of Beats of Silence at the Beginning
beats_label = ttk.Label(main_frame, text="Number of Beats of Silence at the Beginning:")
beats_label.grid(row=0, column=0, sticky='w', pady=2)
beats_entry = ttk.Entry(main_frame)
beats_entry.insert(0, "1")  # Default to 1 beat
beats_entry.grid(row=0, column=1, pady=2, sticky='ew')

# Checkbox to rename file
rename_file_var = tk.BooleanVar(value=True)
rename_file_check = ttk.Checkbutton(main_frame, text="Rename File With Specifications", variable=rename_file_var, command=toggle_fields)
rename_file_check.grid(row=1, column=0, columnspan=2, sticky='w', pady=5)

# Input fields
fields = {
    "Key": "Cmin",
    "Master Limit": "-0.3db",
    "BPM": "120BPM",
    "Bit Rate": "24Bits",
    "Sample Rate": "48Khz",
    "Dither": "Triangular",
    "Dedicated To": "LABEL"
}

entries = {}
row_index = 2
for field, default_value in fields.items():
    label = ttk.Label(main_frame, text=field + ":")
    label.grid(row=row_index, column=0, sticky='w', pady=2)
    entry = ttk.Entry(main_frame)
    entry.insert(0, default_value)
    entry.grid(row=row_index, column=1, pady=2, sticky='ew')
    entries[field] = entry
    row_index += 1

# Save entries to variables
key_entry = entries["Key"]
master_limit_entry = entries["Master Limit"]
bpm_entry = entries["BPM"]
bit_rate_entry = entries["Bit Rate"]
sample_rate_entry = entries["Sample Rate"]
dither_entry = entries["Dither"]
dedicated_to_entry = entries["Dedicated To"]

# Dropdown menu for track type
track_type_var = tk.StringVar(value="DEMO")
track_type_label = ttk.Label(main_frame, text="Track Type:")
track_type_label.grid(row=row_index, column=0, sticky='w', pady=2)
track_type_dropdown = ttk.Combobox(main_frame, textvariable=track_type_var, values=["DEMO", "MASTER", "MIX", "LOOP", "IDEA", "JAM", "LIVE"])
track_type_dropdown.grid(row=row_index, column=1, pady=2, sticky='ew')
row_index += 1

# Checkbox to fix WAV HEX values
fix_wav_hex_var = tk.BooleanVar(value=True)
fix_wav_hex_check = ttk.Checkbutton(main_frame, text="Fix WAV HEX Values (Pioneer Error E-8305)", variable=fix_wav_hex_var)
fix_wav_hex_check.grid(row=row_index, column=0, columnspan=2, sticky='w', pady=5)

# Unified Log Area with dark background and white text
log_text = scrolledtext.ScrolledText(main_frame, wrap=tk.WORD, height=15, state='disabled')
log_text.grid(row=row_index+2, column=0, columnspan=2, pady=10, sticky='nsew')
log_text.configure(foreground="white", background="#2e2e2e")  # Set text color to white and background to dark

# Open File and Exit Buttons in a single row
button_frame = ttk.Frame(main_frame)
button_frame.grid(row=row_index+3, column=0, columnspan=2, pady=10)

open_button = ttk.Button(button_frame, text="Open File", command=open_file_dialog)
open_button.pack(side=tk.LEFT, padx=10)

exit_button = ttk.Button(button_frame, text="Exit", command=root.quit)
exit_button.pack(side=tk.RIGHT, padx=10)

# Configure column weights for resizing
main_frame.columnconfigure(0, weight=1)
main_frame.columnconfigure(1, weight=1)

root.mainloop()
