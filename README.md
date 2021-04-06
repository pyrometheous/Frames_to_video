# Frames_to_video
Python Tool that compiles frames from Video Enhance AI using audio/sub tracks from original video

# Prerequisites
1. Download [FFMPEG](https://ffmpeg.org/download.html) and extract files to a directory you have access to.

2. Update the [Windows PATH Variable](https://www.computerhope.com/issues/ch000549.htm) to include the directory
you saved FFMPEG to.

3. Download and install [MKVToolNix](https://mkvtoolnix.download/downloads.html).
4. Update the [Windows PATH Variable](https://www.computerhope.com/issues/ch000549.htm) to include the MKVToolNix
installation directory (typically C:\Program Files\MKVToolNix\)
5. If desired, you can change the extension of the Python script to '.pyw' to prevent the terminal window from showing,
however it does provide useful information in regards to tracking the progress of the compilation.

# How to use:
1. Select the desired encoder from the dropdown menu.<br>
![Encoder Dropdown](https://imgur.com/jB1kC1R.png)<br>
2. Click the <b>Browse</b> button next to the <b>Image Sequence Directory</b>
textbox.<br>
![Browse Image Sequence](https://imgur.com/IxSg2NE.png)<br>
3. Navigate to the directory your image sequence is in and select the first image in the sequence.<br>
![First Image In Sequence](https://imgur.com/uJv9RDq.png)<br>
4. Click the <b>Browse</b> button next to the <b>Original File</b>
textbox.<br>
![Browse Original File](https://imgur.com/1eg7mDP.png)<br>
5. Navigate to the directory of the original video file and select it.
6. Click the <b>Convert</b> button.
7. Once completed a pop up window will come up saying
> Completed in: X amount of time.
8. There will be two new files in the original video file's directory
- videoFileName_temp.mkv<br>
- videoFileName_final.mkv<br>
<br><b>videoFileName_final.mkv</b> should be the image sequence with the audio/subtitle tracks from the original video file.
The <b>videoFileName_temp.mkv</b> can be deleted once you verify the final file is okay.

# Note:
- In some rare circumstances (mostly older AVI files) the script won't create the final file, and will instead prompt
you to use the MKVToolNix GUI application to merge the video/audio/subtitle tracks into a new file.<br>
- You may want to re-encode the final video in [Handbrake](https://handbrake.fr/downloads.php) to reduce file size, 
not a requirement, but may be needed o playback video on some players, depending on the resulting file size.
