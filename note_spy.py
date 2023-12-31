import cv2
import numpy
import screeninfo
from pynput import keyboard, mouse
from mss import mss
from midiutil.MidiFile import MIDIFile


def get_monitor(mon_num, primary=True):
    monitors = screeninfo.get_monitors()
    target_monitor = monitors[mon_num]
    return target_monitor.width, target_monitor.height


class Paparatsy:
    def __init__(self, top_left_x, top_left_y_from_top, width, height, monitor_number=1):
        self.contasted_screenshot = None
        self.mouse_coords = None
        self.listener = None
        self.k_listener = None
        self.screenshot = None

        with mss() as sct:
            monitor = sct.monitors[monitor_number]
            self.monitor = {
                "top": monitor["top"] + top_left_y_from_top,
                "left": monitor["left"] + top_left_x,
                "width": width,
                "height": height,
                "monitor": monitor
            }

    def screengrab(self, grayscale=True):
        mon = self.monitor
        with mss() as sct:
            img_grab = sct.grab(mon)
            # noinspection PyTypeChecker
            self.screenshot = numpy.array(img_grab)
            if grayscale:
                self.screenshot = cv2.cvtColor(self.screenshot, cv2.COLOR_BGRA2GRAY)

    def screen_save(self):
        cv2.imwrite('screenshots/image.jpg', self.screenshot)

    @staticmethod
    def display_setup(output_mon_num, out_win_pos_offset_x, out_win_pos_offset_y):
        monitor_list = screeninfo.get_monitors()
        target_monitor = monitor_list[output_mon_num]

        cv2.namedWindow("Display", cv2.WINDOW_NORMAL)
        cv2.moveWindow("Display", target_monitor.x + out_win_pos_offset_x, target_monitor.y + out_win_pos_offset_y)

    @staticmethod
    def display_screen_grab(img, width, height, scale=80):
        cv2.resizeWindow("Display", (int(width * scale / 100), int(height * scale / 100)))
        cv2.imshow("Display", img)
        cv2.waitKey(1)

    def thresholder(self, key_chart, scan_line):
        for i in range(0, 20):
            selfie_line = self.screenshot_segment(key_chart[0], scan_line, key_chart[2], scan_line + 2)
            selfie_line = self.adjust_brightness(selfie_line, i)
            contour_list = []

            _, thresh = cv2.threshold(selfie_line, 127, 255, cv2.THRESH_BINARY)
            contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

            for contour in contours:
                m = cv2.moments(contour)
                if m["m00"] != 0:
                    cx = int(m["m10"] / m["m00"])
                    contour_list.append(cx)

            print(len(contour_list))
            if len(contour_list) == 52:
                return contour_list

    def keyboard_getter(self):
        coordinates = []
        for i in range(2):
            x, y = self.get_mouse_coordinates()
            coordinates.append(x)
            coordinates.append(y)
            print(f"mouse position: {x}, {y}")

        keyboard_width = abs(coordinates[0] - coordinates[2])
        keyboard_height = abs(coordinates[1] - coordinates[3])
        return keyboard_height, keyboard_width, coordinates

    def grab_pixel(self, y_val, x_val):
        if y_val > 2559:
            y_val = 2559
        return self.screenshot[x_val][y_val]

    @staticmethod
    def adjust_brightness(img, gamma=1.0):
        gamma_corrected = numpy.power(img / 255.0, gamma) * 255.0
        return gamma_corrected.astype(numpy.uint8)

    def add_contrast(self, added_contrast):
        self.screenshot = cv2.convertScaleAbs(self.screenshot, alpha=added_contrast)

    def screenshot_segment(self, top_left_x, top_left_y, bot_right_x, bot_right_y):
        segment = self.screenshot[top_left_y:bot_right_y, top_left_x:bot_right_x]
        return segment

    # Keyboard cords shenanigans
    def get_mouse_coordinates(self):
        self.listener = mouse.Listener(on_move=self.on_move)
        self.k_listener = keyboard.Listener(on_press=self.on_press)
        self.listener.start()
        self.k_listener.start()
        self.k_listener.join()
        return self.mouse_coords

    def on_press(self, key):
        if key == keyboard.Key.ctrl_r:
            # print("Ctrl+R pressed. Retrieving mouse coordinates...")
            self.listener.stop()
            self.k_listener.stop()

    def on_move(self, x, y):
        self.mouse_coords = (abs(x), abs(y))


class Converter:
    piano_notes_midi_dict = {
        "A0": 21, "A#0": 22, "B0": 23,
        "C1": 24, "C#1": 25, "D1": 26, "D#1": 27, "E1": 28, "F1": 29, "F#1": 30, "G1": 31, "G#1": 32,
        "A1": 33, "A#1": 34, "B1": 35,
        "C2": 36, "C#2": 37, "D2": 38, "D#2": 39, "E2": 40, "F2": 41, "F#2": 42, "G2": 43, "G#2": 44,
        "A2": 45, "A#2": 46, "B2": 47,
        "C3": 48, "C#3": 49, "D3": 50, "D#3": 51, "E3": 52, "F3": 53, "F#3": 54, "G3": 55, "G#3": 56,
        "A3": 57, "A#3": 58, "B3": 59,
        "C4": 60, "C#4": 61, "D4": 62, "D#4": 63, "E4": 64, "F4": 65, "F#4": 66, "G4": 67, "G#4": 68,
        "A4": 69, "A#4": 70, "B4": 71,
        "C5": 72, "C#5": 73, "D5": 74, "D#5": 75, "E5": 76, "F5": 77, "F#5": 78, "G5": 79, "G#5": 80,
        "A5": 81, "A#5": 82, "B5": 83,
        "C6": 84, "C#6": 85, "D6": 86, "D#6": 87, "E6": 88, "F6": 89, "F#6": 90, "G6": 91, "G#6": 92,
        "A6": 93, "A#6": 94, "B6": 95,
        "C7": 96, "C#7": 97, "D7": 98, "D#7": 99, "E7": 100, "F7": 101, "F#7": 102, "G7": 103, "G#7": 104,
        "A7": 105, "A#7": 106, "B7": 107,
        "C8": 108
    }
    ticks_per_beat = 480

    def __init__(self):
        print("input song name:")
        song_name = input()
        self.song_name = song_name + ".mid"

        print("\ninput song tempo:")
        tempo = int(input())
        self.mf = MIDIFile(1)  # only 1 track
        self.track = 0  # the only track

        time = 0  # start at the beginning
        self.mf.addTrackName(self.track, time, "Sample Track")
        self.mf.addTempo(self.track, time, tempo)

    def apply_notes(self, note_dict):
        channel = 0
        volume = 70

        pitch = self.piano_notes_midi_dict[note_dict['key']]
        duration = note_dict['duration']
        time = note_dict['time']

        controller_number = 64  # Sustain pedal controller number

        controller_value = 0
        self.mf.addControllerEvent(self.track, channel, time, controller_number, controller_value)

        self.mf.addNote(self.track, channel, pitch, time, duration, volume)

        controller_value = 127  # Maximum value (on)
        self.mf.addControllerEvent(self.track, channel, time, controller_number, controller_value)

    def finish_song(self):
        print("finished song")
        with open(f"{self.song_name}", 'wb') as outf:
            self.mf.writeFile(outf)
