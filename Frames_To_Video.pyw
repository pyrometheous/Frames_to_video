import subprocess
import sys
required_packages = ['WxPython', 'opencv-python', 'moviepy', 'progress', 'ffmpeg-python', 'datetime', 'pymkv']
req = subprocess.check_output([sys.executable, '-m', 'pip', 'freeze'])
installed_packages = [r.decode().split('==')[0] for r in req.split()]
for package in required_packages:
    if package not in installed_packages:
        subprocess.call([sys.executable, '-m', 'pip', 'install', '--trusted-host', 'pypi.org', '--trusted-host',
                         'files.pythonhosted.org', package])
import wx
import os
import cv2
import ffmpeg
import threading
import time
from datetime import timedelta
import pymkv


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
    formated = time.strftime("%I:%M:%S %p %Z", t)
    return formated


def update_status_bar(window, text):
    status = str(text)
    window.statusbar.SetStatusText(status, i=1)
    write_to_log(text)
    window.Refresh()
    window.Update()
    wx.SafeYield(win=None, onlyIfNeeded=False)


def write_to_log(text):
    text = str(text)
    logfile = 'C:\\Temp\\frames_to_video.log'
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
    window.proc = subprocess.Popen(['ping', '127.0.0.1', '-i', '0.2'], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
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


    def ffmpeg_image_sequence(self, image_sequence, video, fps):
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
            'c:v': 'hevc_nvenc',
            #'c:v': 'h264_nvenc',
            'an': None,
            #'tune': 'film',
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
        except IndexError as e:
            warning(str(e))
            information('You will need to use the MKVToolNix GUI\n'
                        'to replace the video track')
        task = True


class MainWindow(wx.Frame):

    def __init__(self, parent, title):
        window_height = 200
        window_width = 600
        wx.Frame.__init__(self, parent, style=wx.DEFAULT_FRAME_STYLE ^ wx.MAXIMIZE_BOX ^ wx.RESIZE_BORDER,
                          title='Tiff to Mkv', size=(window_width, window_height))
    #       Global Window Ref
        global main_window
        main_window = self
        panel = wx.Panel(self)
        self.currentDirectory = os.getcwd()
    #       Draw Static Text
        wx.StaticText(panel, pos=(10, 5), label='Image Sequence Directory')
        wx.StaticText(panel, pos=(10, 60), label='Original File')
    #       Draw Text Boxes
        self.text_image_sequence_dir = wx.TextCtrl(panel, pos=(5, 25), size=(300, 25))
        self.text_original_video_dir = wx.TextCtrl(panel, pos=(5, 80), size=(300, 25))
    #       Create Progress Bar
        self.statusbar = self.CreateStatusBar(2)
        self.progress_bar = wx.Gauge(self.statusbar, -1, size=(280,25), style=wx.GA_PROGRESS)
        #self.progress_bar_active = False
        self.Show()
        self.progress_bar.SetRange(50)
        self.progress_bar.SetValue(0)
    #       Create Buttons
        convert_btn = wx.Button(panel, label='Convert', pos=(window_width - 110, 21))
        open_image_sequence_btn = wx.Button(panel, label="Browse", pos=(325, 25))
        open_orignal_file_btn = wx.Button(panel, label='Browse', pos=(325, 80))
    #       Create Button Triggers
        convert_btn.Bind(wx.EVT_BUTTON, self.convert)
        open_image_sequence_btn.Bind(wx.EVT_BUTTON, self.browse_image_sequence)
        open_orignal_file_btn.Bind(wx.EVT_BUTTON, self.browse_video)
        self.Bind(wx.EVT_CLOSE, self.close_window)
    #       Create worker object and a thread
        self.worker = Worker()
        self.worker_thread = threading.Thread()
    #       Assign the worker to the thread and start the thread
        #self.worker.moveToThead(self.worker_thread)
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
        #dlg.Destroy()

    def convert(self, event):
        start_busy_statusbar(main_window)
        global task
        task = False
        start = time.time()
        update_status_bar(main_window, 'Verifying Files...')
        image_sequence = str(self.text_image_sequence_dir.GetValue())
        original_video = str(self.text_original_video_dir.GetValue())
        if image_sequence.endswith('.tiff') or image_sequence.endswith('.tif') or image_sequence.endswith('.png') or image_sequence.endswith('.jpg') and \
                original_video.endswith('.mkv') or original_video.endswith('.mp4') or original_video.endswith('.avi'):
            try:
                update_status_bar(self, 'Setting Up Variables...')
                new_video = str(original_video)[:-4] + '_1080p.mkv'
                temp_video = str(original_video)[:-4] + '_temp.mkv'
                fps = get_frame_rate(original_video)
                write_to_log('Original: ' + original_video +
                             '\nTemp: ' + temp_video + '\nFPS: ' + str(fps))
            #       Set Up Worker To Compile Frames
                update_status_bar(self, 'Setting Up Compile Frames Thread...')
                args = [Worker, image_sequence, temp_video, fps]
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
            warning('You must enter valid paths for both an sequence and a video.')
        stop_busy_statusbar(main_window)
        finish_time = round(time.time() - start)
        information('Completed in: ' + seconds_to_str(finish_time))
        update_status_bar(self, 'Finished')

    def close_window(self, event):
        write_to_log('Application Closed')
        frame.Destroy()
        sys.exit()


write_to_log('Application Opened')
app = wx.App(False)
frame = MainWindow(None, "jpg to png")
app.MainLoop()
wx.CallAfter(frame.Destroy)