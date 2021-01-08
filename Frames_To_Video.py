# MKVToolNix Must be installed and included in the system PATH variable.
# FFMPEG Must be downloaded and included in the system PATH variable.
import subprocess
import sys
import wx
import os
import cv2
import ffmpeg
import threading
import time
from datetime import timedelta
import pymkv
import numpy as np

encoders = {
    "libx264 H.264 / AVC / MPEG-4 AVC / MPEG-4 part 10 (codec h264)": 'libx264',
    "libx264 H.264 / AVC / MPEG-4 AVC / MPEG-4 part 10 RGB (codec h264)": 'libx264rgb',
    "AMD AMF H.264 Encoder (codec h264)": 'h264_amf',
    "NVIDIA NVENC H.264 encoder (codec h264)": 'h264_nvenc',
    "H.264 / AVC / MPEG-4 AVC / MPEG-4 (Intel Quick Sync Video acceleration) (codec h264)": 'h264_qsv',
    "libx265 H.265 / HEVC (codec hevc)": 'libx265',
    "NVIDIA NVENC hevc encoder (codec hevc)": 'nvenc_hevc',
    "AMD AMF HEVC encoder (codec hevc)": 'hevc_amf',
    "HEVC (Intel Quick Sync Video acceleration) (codec hevc)": 'hevc_qsv'
}


def test_video_encoders(encoder):
    if os.path.isfile("./test.mkv"):
        os.remove("./test.mkv")
    if os.path.isfile('./test.avi'):
        output_options = {
            'crf': 20,
            'preset': 'fast',
            'movflags': 'faststart',
            'pix_fmt': 'yuv420p',
            'c:v': encoder,
            'b:v': '20M'
        }
        try:
            (
                ffmpeg
                .input('./test.avi')
                .output('./test.mkv', **output_options)
            ).run()
        except ffmpeg.Error as e:
            # print(e)
            return False
        return True


def create_dummy_video_file():
    width = 480
    height = 320
    fps = 10
    seconds = 1
    fourcc = cv2.VideoWriter_fourcc(*'MP42')
    video = cv2.VideoWriter('./test.avi', fourcc, float(fps), (width, height))
    for _ in range(fps * seconds):
        video_frame = np.random.randint(0, 256,
                                        (height, width, 3),
                                        dtype=np.uint8)
        video.write(video_frame)
    video.release()


def seconds_to_str(elapsed=None):
    if elapsed is None:
        return time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
    else:
        return str(timedelta(seconds=elapsed))


def warning(e):
    print('Warning:\n' + e)
    wx.MessageBox(e, 'Warning', wx.OK | wx.ICON_WARNING)
    write_to_log(e)


def information(i):
    print('Note:\n' + i)
    wx.MessageBox(i, 'Note', wx.OK | wx.ICON_INFORMATION)
    write_to_log(i)


def wait(start, text):
    time.sleep(.05)
    time_running = round(time.time() - start)
    update_status_bar(main_window, text + ' (Time Elapsed: ' + seconds_to_str(time_running) + ')')


def get_date():
    return str(time.strftime("%m/%d/%Y"))


def get_time():
    t = time.localtime()
    formatted = time.strftime("%I:%M:%S %p %Z", t)
    return formatted


def update_status_bar(window, text):
    status = str(text)
    window.statusbar.SetStatusText(status, i=1)
    write_to_log(text)
    window.Refresh()
    window.Update()
    wx.SafeYield(win=None, onlyIfNeeded=False)


def write_to_log(text):
    text = str(text)
    logfile = 'C:/Temp/frames_to_video.log'
    if not os.path.exists('C:/Temp/'):
        os.makedirs('C:/Temp/')
    if os.path.isfile(logfile):
        f = open(logfile, 'a')
    else:
        f = open(logfile, 'w')
    if 'Time Elapsed' not in text:
        log = '[' + get_date() + ' ' + get_time() + ']\n' + text + '\n\n'
        f.write(log)
        print(log)


def get_frame_rate(video):
    cap = cv2.VideoCapture(video)
    fps = cap.get(cv2.CAP_PROP_FPS)
    return fps


def start_busy_statusbar(window):
    window.count = 0
    window.proc = subprocess.Popen(['ping', '127.0.0.1', '-i', '0.2'], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                   stderr=subprocess.PIPE)
    while True:
        wx.Yield()
        try:
            list_data = window.proc.stdout.readline()
            wx.Yield()
        except:
            break
        if len(list_data) == 0:
            break
        window.progress_bar.Pulse()
        wx.Yield()
        window.count += 1


def stop_busy_statusbar(window):
    window.progress_bar.Destroy()
    window.progress_bar = wx.Gauge(window.statusbar, -1, size=(280, 25), style=wx.GA_PROGRESS)


class Worker(object):

    def ffmpeg_image_sequence(self, image_sequence, video, fps, encoder):
        global task
        task = False
        path = os.path.dirname(os.path.realpath(image_sequence))
        image_format = {
            'png': '\%06d.png',
            'iff': '\%06d.tiff',
            'tif': '\%06d.tif',
            'jpg': '\%06d.jpg'
        }
        sequence = path + image_format[image_sequence[-3:]]
        output_options = {
            'crf': 20,
            'preset': 'slow',
            'movflags': 'faststart',
            'pix_fmt': 'yuv420p',
            'c:v': encoder,
            # 'an': None,
            # 'tune': 'film',
            'b:v': '20M'
        }
        try:
            (
                ffmpeg
                    .input(sequence, framerate=fps)
                    .output(video, **output_options)
            ).run()
        except ffmpeg.Error as e:
            warning(str(e))
        task = True

    def merge_mkv(self, original, temp, final):
        global task
        task = False
        write_to_log('Original: ' + original + '\nTemp: ' + temp + '\nFinal: ' + final)
        mkv1 = pymkv.MKVFile(original)
        track1 = pymkv.MKVTrack(temp)
        track2 = pymkv.MKVTrack(original)
        try:
            mkv1.replace_track(0, track1)
            mkv1.mux(final)
        except IndexError or Exception as e:
            warning(str(e))
            information('You will need to use the MKVToolNix GUI\n'
                        'to replace the video track')
        task = True


class MainWindow(wx.Frame):

    def __init__(self, parent, title):
        window_height = 250
        window_width = 600
        wx.Frame.__init__(self, parent, style=wx.DEFAULT_FRAME_STYLE ^ wx.MAXIMIZE_BOX ^ wx.RESIZE_BORDER,
                          title='Image Sequence to Video Converter', size=(window_width, window_height))
        #       Global Window Ref
        global main_window
        main_window = self
        panel = wx.Panel(self)
        self.currentDirectory = os.getcwd()
        #       Draw Static Text
        wx.StaticText(panel, pos=(10, 5), label='Select Encoder')
        wx.StaticText(panel, pos=(10, 60), label='Image Sequence Directory')
        wx.StaticText(panel, pos=(10, 115), label='Original File')
        #       Draw Text Boxes
        self.text_image_sequence_dir = wx.TextCtrl(panel, pos=(5, 80), size=(window_width - 125, 25))
        self.text_original_video_dir = wx.TextCtrl(panel, pos=(5, 135), size=(window_width - 125, 25))
        #       Draw Dropdown Menu
        self.choice = wx.Choice(panel, pos=(5, 25), style=wx.CB_SORT, size=(window_width - 125, 25),
                                choices=encoder_list)
        #       Create Progress Bar
        self.statusbar = self.CreateStatusBar(2)
        self.progress_bar = wx.Gauge(self.statusbar, -1, size=(280, 25), style=wx.GA_PROGRESS)
        #       self.progress_bar_active = False
        self.Show()
        self.progress_bar.SetRange(50)
        self.progress_bar.SetValue(0)
        #       Create Buttons
        convert_btn = wx.Button(panel, label='Convert', pos=(window_width - 105, 25))
        open_image_sequence_btn = wx.Button(panel, label="Browse", pos=(window_width - 105, 80))
        open_original_file_btn = wx.Button(panel, label='Browse', pos=(window_width - 105, 135))
        #       Create Button Triggers
        convert_btn.Bind(wx.EVT_BUTTON, self.convert)
        open_image_sequence_btn.Bind(wx.EVT_BUTTON, self.browse_image_sequence)
        open_original_file_btn.Bind(wx.EVT_BUTTON, self.browse_video)
        self.Bind(wx.EVT_CLOSE, self.close_window)
        #       Create worker object and a thread
        self.worker = Worker()
        self.worker_thread = threading.Thread()
        #       Assign the worker to the thread and start the thread
        # self.worker.moveToThead(self.worker_thread)
        self.worker_thread.start()

    def browse_image_sequence(self, event):
        try:
            path = self.open_dialog('*.tif; *.tiff; *.png; *.jpg')
            self.text_image_sequence_dir.SetValue(path)
        except UnboundLocalError as e:
            return

    def browse_video(self, event):
        try:
            path = self.open_dialog('*.mkv; *.mp4; *.avi; *.wmv')
            self.text_original_video_dir.SetValue(path)
        except UnboundLocalError as e:
            return

    def open_dialog(self, wildcard):
        dlg = wx.FileDialog(
            self, message="Choose a file",
            defaultDir=self.currentDirectory,
            defaultFile="",
            wildcard=wildcard,
            style=wx.FD_OPEN | wx.FD_MULTIPLE | wx.FD_CHANGE_DIR
        )
        if dlg.ShowModal() == wx.ID_OK:
            paths = dlg.GetPaths()
            for path in paths:
                path
        return path
        # dlg.Destroy()

    def convert(self, event):
        start_busy_statusbar(main_window)
        global task
        task = False
        start = time.time()
        update_status_bar(main_window, 'Verifying Files...')
        image_sequence = str(self.text_image_sequence_dir.GetValue())
        original_video = str(self.text_original_video_dir.GetValue())
        choice = self.choice.GetSelection()
        if choice == -1:
            update_status_bar(main_window, 'Invalid: No Encoder Selected')
            warning("Please select a valid encoder from the DropDown.")
            stop_busy_statusbar(main_window)
            update_status_bar(main_window, '')
        else:
            encoder_choice = self.choice.GetString(choice)
            update_status_bar(main_window, 'Encoder ' + encoders[encoder_choice] + ' selected')
            encoder_to_use = encoders[encoder_choice]
            if image_sequence.endswith('.tiff') or image_sequence.endswith('.tif') or image_sequence.endswith('.png') \
                    or image_sequence.endswith('.jpg') and \
                    original_video.endswith('.mkv') or original_video.endswith('.mp4') \
                    or original_video.endswith('.avi'):
                try:
                    update_status_bar(self, 'Setting Up Variables...')
                    new_video = str(original_video)[:-4] + '_final.mkv'
                    temp_video = str(original_video)[:-4] + '_temp.mkv'
                    fps = get_frame_rate(original_video)
                    write_to_log('Original: ' + original_video +
                                 '\nTemp: ' + temp_video + '\nFPS: ' + str(fps))
                    #       Set Up Worker To Compile Frames
                    update_status_bar(self, 'Setting Up Compile Frames Thread...')
                    args = [Worker, image_sequence, temp_video, fps, encoder_to_use]
                    compile_frames = threading.Thread(target=Worker.ffmpeg_image_sequence,
                                                      args=args)
                    update_status_bar(self, "Starting Thread...")
                    compile_frames.start()
                    while not task:
                        wait(start, 'Merging Frames Into Video...')
                    update_status_bar(main_window, 'Merging Frames Into Video Complete')
                    #       Set Up Worker To Mux Video
                    update_status_bar(self, 'Setting Up Muxing Thread...')
                    args = [Worker, original_video, temp_video, new_video]
                    mkv_mux = threading.Thread(target=Worker.merge_mkv, args=args)
                    update_status_bar(self, "Starting Thread...")
                    mkv_mux.start()
                    while not task:
                        wait(start, 'Muxing MKV Files...')
                    update_status_bar(main_window, 'Muxing Complete')
                except FileNotFoundError as e:
                    e = str(e).replace('Errno 2] ', '')
                    e = e.replace('directory:', 'directory:\n')
                    warning(e)
            else:
                update_status_bar(main_window, 'Invalid: No Item(s) Selected')
                warning('You must enter valid paths for both an sequence and a video.')
                stop_busy_statusbar(main_window)
                update_status_bar(main_window, '')
                return
            stop_busy_statusbar(main_window)
            finish_time = round(time.time() - start)
            information('Completed in: ' + seconds_to_str(finish_time))
            update_status_bar(self, 'Finished')

    def close_window(self, event):
        write_to_log('Application Closed')
        frame.Destroy()
        sys.exit()


create_dummy_video_file()
encoder_list = list()
for enc in encoders:
    if test_video_encoders(encoders[enc]):
        encoder_list.append(enc)
    os.system('cls')
if os.path.isfile("./test.avi"):
    os.remove("./test.avi")
if os.path.isfile("./test.mkv"):
    os.remove("./test.mkv")
write_to_log('Application Opened')
app = wx.App(False)
frame = MainWindow(None, "Main Window")
app.MainLoop()
wx.CallAfter(frame.Destroy)
