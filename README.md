
# StartOffseter.app
# Add Silence to Track - User Guide for DJs and Music Producers

## Purpose of the Application

Tired of messing your arrange just to add some silence at the beginning? This tool will add the specified beats of silence at the beginning of your track to prevent "clicks" & "pops" when your tracks are uploaded to streaming services, also it helps Rekordbox to quantize more accurate your track. The first second could even be clipped In some music players.

This application is designed to help **DJs and music producers** automate and simplify the process of adding silence to the beginning of audio tracks. Whether you're working with **mixes, masters, or loops**, the tool enables you to add precise beats of silence based on the **BPM** (Beats Per Minute) of your track.

Additionally, the tool can **edit WAV file headers (HEX values)** to fix compatibility issues with professional hardware, such as **Pioneer CDJs**, which may sometimes display errors like *E-8305: Unsupported File Format* due to improper WAV file formatting.

### Why Add Silence? 

Adding silence to the beginning of a track is useful for:
- **Playback issues**: Adding a beat or two of silence prevents some playback issues in some stremaing services when audio strats at 0:00 seconds. This happens with Soundcloud, Spotify, car audio systems, and some media players. It prevents getting the first second clipped or audible "clicks" & "pops".
- **Rekorbox Analysis**: Sometimes when audio strats at 0:00 seconds, Rekordbox fails matching the beat grid of your track with your actual beat hits
- **Dont mess up your arrangement**: Inserting the silence direclty in your DAW arrangement will mess your original proyect abras and compass, it will also mess up coordinated LFO start times & synced effects like delays, even some plugins and VSTis have this internally

## Main Features

- **Add Silence by Beats**: Automatically calculates and adds silence at the beginning of the track based on the BPM you specify. it 
- **WAV HEX Fixing**: Ensures compatibility with Pioneer CDJs by correcting the HEX values of WAV files, preventing errors during playback. Since 
- **Customizable Number of Silent Beats**: You can specify the number of beats to add, allowing for tailored silence additions to suit your mixing style.
- **File Renaming**: Optionally, rename files with key specifications such as BPM, key, bit rate, sample rate, etc.
  
## Warnings

- This applition will preserve your track quality it won't downgrade the waves neither the phse your track. It uses FFMPEG to encode the final WAV file in PCM Signed 24-bit little-endian (pcm_s24le)
  - It will respect your WAV sample rate
  - It will respect your WAV channels
  - Result WAV will be 24 bits of Bit Rate
- If the option "WAV HEX Fixing" is unchecked, Pionner players wont be able to playback the final WAV file (Pionner's fault... not mine...) [See "The Infamous "E-8305: Unsupported File Format"](https://www.reddit.com/r/Rekordbox/comments/jfs7dd/the_infamous_e8305_unsupported_file_format_almost/)
- This project has been only tested in MAC OS

## Tools Behind the Scenes

- **FFMPEG**: This powerful open-source tool handles all audio processing, including adding silence and fixing file headers. It works seamlessly in the background to perform operations without needing any technical input from the user.
  
- **Python**: The underlying programming language for the application, but you don’t need to worry about the technical details. It’s all built into an easy-to-use graphical interface.

## How to Use the Application (DEV MODE)

### If you dont have tech background



### If you have Python and FFMPEG already installed
Just rename the "StartOffseter.py" to "StartOffseter.app" drag it into your MAC OS dock, re-name it again to "StartOffseter.command". This will make the app executable from your dock. You can set up later icon in the folder

### Step 1: Install FFMPEG

Before running the application, ensure that **FFMPEG** is installed on your system. You can download it from [ffmpeg.org](https://ffmpeg.org/download.html).

### Step 2: Open the Application

- Launch the application (just double-click the app if it's packaged or run the Python script if you're familiar with that process).
  
### Step 3: Select Your Audio File

- Click on the **"Open File"** button.
- A file dialog will appear, allowing you to select your audio file. The file should be in **WAV** format.

### Step 4: Customize Your Options

- **Number of Beats of Silence**: Enter the number of beats you want to add as silence at the beginning of the track.
- **BPM**: Specify the BPM of your track. For example, if your track is 120 BPM, enter `120BPM` in the field. The app will calculate the correct amount of silence based on this BPM.
  
### Step 5: Optional Settings

- **Fix WAV HEX Values**: Check this box if you want the app to automatically fix the WAV file headers to ensure compatibility with Pioneer CDJs and other similar hardware.
- **Rename File**: You can choose to rename the output file by selecting this option and filling out fields such as the track’s key, bit rate, sample rate, etc.

### Step 6: Execute the Process

- Once you've customized your settings, click **"Open File"** to start the process. The application will calculate the required silence, add it to the beginning of the track, and optionally fix the WAV file if needed.
  
### Step 7: Review and Save

- After processing, the application will confirm that the silence has been successfully added and provide a path to the newly saved file.
- Check the log messages for details and potential issues. The log area will indicate whether the process was successful.

### Step 8: Use in Your Set

- Once your track is processed, it's ready for your next live set, DJ mix, or production session. No more worrying about compatibility errors with your hardware!

---

## Dependencies

To run this application, you will need the following dependencies installed:

1. **FFMPEG**: Handles the audio processing and file manipulation. Download it from [ffmpeg.org](https://ffmpeg.org/download.html).
2. **Python 3.x**: The programming language used to build the application. You can download it from [python.org](https://www.python.org/downloads/).
3. **Tkinter**: A built-in Python library that provides the graphical interface. It comes pre-installed with most Python distributions.
4. **Subprocess**: A Python module used to interact with system-level commands (used for calling FFMPEG).
5. **ScrolledText**: Part of Tkinter, it is used to create scrollable text areas within the application.
6. You can use [Hexed.IT](https://hexed.it/) to monitor the hex values
  
---

## ChatGPT participation

This project was developed with the assistance of **ChatGPT**, an AI language model created by OpenAI. It helped streamline the design of the application, making it more accessible for DJs and music producers. I provided guidance on integrating silence insertion logic based on BPM, fixing WAV HEX values, and improving the user experience by refining the user interface and ensuring compatibility with professional audio equipment like Pioneer CDJs.

---

**Enjoy creating and performing with fewer technical hiccups! 🎧**
