#pset6.py


import sys, os
sys.path.insert(0, os.path.abspath('..'))

from common.core import BaseWidget, run, lookup
from common.audio import Audio
from common.mixer import Mixer
from common.wavegen import WaveGenerator
from common.wavesrc import WaveBuffer, WaveFile
from common.gfxutil import topleft_label, resize_topleft_label, CEllipse, CLabelRect, KFAnim

from kivy.graphics.instructions import InstructionGroup
from kivy.graphics import Color, Ellipse, Line, Rectangle
from kivy.core.window import Window

import numpy as np



class MainWidget(BaseWidget) :
    def __init__(self):
        super(MainWidget, self).__init__()

        song_base_name = '../data/ZiggyStardust_TRKS5.wav' # todo: fill in your song

        self.song_data  = SongData(song_base_name)
        self.audio_ctrl = AudioController(song_base_name)
        self.display    = GameDisplay(self.song_data)
        self.player     = Player(self.song_data, self.audio_ctrl, self.display)

        self.canvas.add(self.display)

        self.info = topleft_label()
        self.add_widget(self.info)

    def on_key_down(self, keycode, modifiers):
        # play / pause toggle
        if keycode[1] == 'p':
            self.audio_ctrl.toggle()

        # button down
        button_idx = lookup(keycode[1], '31245', (0,1,2,3,4))
        if button_idx != None:
            print('down', button_idx)
            self.player.on_button_down(button_idx)

    def on_key_up(self, keycode):
        # button up
        button_idx = lookup(keycode[1], '31245', (0,1,2,3,4))
        if button_idx != None:
            print('up', button_idx)
            self.player.on_button_up(button_idx)

    # handle changing displayed elements when window size changes
    def on_layout(self, win_size):
        resize_topleft_label(self.info)
        self.display.on_layout(win_size)

    def on_update(self):
        self.audio_ctrl.on_update()

        now = self.audio_ctrl.get_time()
        self.player.on_update(now)
        self.display.on_update(now)

        self.info.text = 'p: pause/unpause song\n'
        self.info.text += 'time: {:.2f}\n'.format(now)
        self.info.text += 'score: ' + str(self.player.score)


# Handles everything about Audio.
#   creates the main Audio object
#   load and plays solo and bg audio tracks
#   creates audio buffers for sound-fx (miss sound)
#   functions as the clock (returns song time elapsed)
class AudioController(object):
    def __init__(self, song_path):
        super(AudioController, self).__init__()
        self.audio = Audio(2)
        self.mixer = Mixer()

        self.audio.set_generator(self.mixer)

        self.track = WaveGenerator(WaveFile(song_path))

        self.mixer.add(self.track)
        self.track.play()

        self.mute = False

    # start / stop the song
    def toggle(self):
        self.track.play_toggle()

    # mute / unmute the solo track
    def set_mute(self, mute):
        if not self.mute:
            self.track.set_gain(0)
        else:
            self.track.set_gain(1)

    # play a sound-fx (miss sound)
    def play_miss(self):
        pass

    # return current time (in seconds) of song
    def get_time(self):
        if self.track:
            return self.track.frame / self.audio.sample_rate

    # needed to update audio
    def on_update(self):
        self.audio.on_update()


# Holds data for gems and barlines.
class SongData(object):
    def __init__(self, song_base):
        super(SongData, self).__init__()
        self.gems = []
        self.barlines =[]

        # TODO: read in gem and barline data

    def get_gems(self):
        with open("../data/ziggy_gem_annotation.txt") as f:
            lines = f.readlines()
            print(lines)
            for line in lines:
                new_gem = line.replace("\n", "").replace(" ", "").split("\t")
                print(new_gem)
                self.gems.append(new_gem)

        return self.gems

    def get_barlines(self):
        with open("../data/ziggy_barlines_annotation.txt") as f:
            lines = f.readlines()
            for line in lines:
                barline = line.replace("\n", "").replace(" ", "").split("\t")
                self.barlines.append(barline[0])

        return self.barlines


# Display for a single gem at a position with a hue or color
class GemDisplay(InstructionGroup):
    def __init__(self, lane, time, color=None):
        super(GemDisplay, self).__init__()
        self.lane = lane
        self.time = time
        # self.color = color

        lane_width = Window.width / 7
        lane_all = [2*lane_width, 3*lane_width, 4*lane_width]

        self.lane_pos = lane_all[int(lane)-1]

        self.pos = (self.lane_pos, Window.height)

        self.gem = Rectangle(pos = self.pos, size=(110,130), source ="../data/gem_hit.png")
        self.add(self.gem)

    # change to display this gem being hit
    def on_hit(self):
        file = np.random.choice(['gem_LARGE', 'gem_LARGE1', 'gem_LARGE2', 'gem_LARGE3'])
        self.gem.source = "../data/" + file + ".png"
        self.gem.size = (200, 1.18 * 200)
        self.gem.pos = (self.pos[0] - 50, Window.height)

    # change to display a passed or missed gem
    def on_pass(self):
        self.gem.source = "../data/gem_sad.png"

    # animate gem (position and animation) based on current time
    def on_update(self, now_time):
        def time_to_ypos(time):
            time_span = 2.0
            return Window.height * time / time_span + 0.2*Window.height

        y_pos = time_to_ypos(float(self.time) - float(now_time))
        # x_pos = beat_marker_len * self.time - now_time

        beat_marker_len = 0.2
        scaled_beat_marker_len = beat_marker_len * Window.width
        start = (Window.width - scaled_beat_marker_len) / 2

        self.gem.pos = (self.lane_pos + 10, y_pos)

        if y_pos < 0 or y_pos > Window.height:
            return False
        else:
            return True


# Displays a single barline on screen
class BarlineDisplay(InstructionGroup):
    def __init__(self, time):
        super(BarlineDisplay, self).__init__()

        self.time = time
        # self.line = Line(points=(.1*Window.width, .2*Window.height, 0.9*Window.width, .2*Window.height), width=3)
        # self.add(self.line)


        # self.color = Color(hsv=(255,255,255))
        self.line = Line(width = 0.5) # actual points of line to be set in on_update()

        # self.add(self.color)
        self.add(self.line)

    # animate barline (position) based on current time
    def on_update(self, now_time):
        
        def time_to_ypos(time):
            time_span = 2.0
            return Window.height * time / time_span + 0.2*Window.height

        y_pos = time_to_ypos(float(self.time) - float(now_time))
        # x_pos = beat_marker_len * self.time - now_time

        self.line.points = [0, y_pos, Window.width, y_pos]

        if y_pos < 0 or y_pos > Window.height:
            return False
        else:
            return True


# Displays one button on the nowbar
class ButtonDisplay(InstructionGroup):
    def __init__(self, lane, color=None):
        super(ButtonDisplay, self).__init__()
        # self.color = Color(hsv=color)
        # self.add(self.color)

        lane_width = Window.width / 7
        lane_all = [lane_width*2, 3*lane_width, 4*lane_width]
        self.lane_pos = lane_all[int(lane)-1]
        pos = (self.lane_pos, Window.height * 0.16)

        self.button = Rectangle(pos = pos, size=(100,100), source="../data/red_star.png")
        self.add(self.button)

    # displays when button is pressed down
    def on_down(self, hit=False):
        if hit:
            self.button.size = (150,150)

    # back to normal state
    def on_up(self):
        self.button.size = (100,100)

    # modify object positions based on new window size
    def on_layout(self, win_size):
        pass


# Displays all game elements: nowbar, buttons, barlines, gems
class GameDisplay(InstructionGroup):
    def __init__(self, song_data):
        super(GameDisplay, self).__init__()

        self.song = SongData(song_data)

        #adds background of nicholas cage
        Window.size = (1500, 1050)
        self.background = Rectangle(pos=(0,0), size=(Window.width, Window.height), source ="../data/stardust.jpg")
        self.add(self.background)


        # self.barlines = self.song.get_barlines()
        # print(self.barlines)

        self.beats = [BarlineDisplay(b) for b in self.song.get_barlines()]
        for b in self.beats:
            self.add(b)

        self.line = Line(points=(.1*Window.width, .2*Window.height, 0.9*Window.width, .2*Window.height), width=1)
        self.color = Color(1,1,1)
        self.add(self.color)
        self.add(self.line)

        # self.gems = self.song.get_gems()
        self.gems = [GemDisplay(g[2], g[0]) for g in self.song.get_gems()]
        for g in self.gems:
            self.add(g)

        self.lanes = [ButtonDisplay(l) for l in range(3)]
        for l in self.lanes:
            self.add(l)

        self.gem_indices = []

        # print("selfgems", self.gems)
        # print("selfgems", self.gems)
        # print(self.barlines)

    # called by Player when succeeded in hitting this gem.
    def gem_hit(self, gem_idx):
        print("BURp")
        self.gems[gem_idx].on_hit()

    def gem_location(self, gem_idx):
        test_gem = self.gems[gem_idx]
        # print(test_gem.gem.pos)
        return test_gem.gem.pos[1]

    # called by Player on pass or miss.
    def gem_pass(self, gem_idx):
        self.gems[gem_idx].on_pass()

    # called by Player on button down
    def on_button_down(self, lane, hit=False):
        self.lanes[lane].on_down(hit)

        if len(self.gem_indices):
            gem_index = self.gem_indices[0]

            print(self.gem_location(gem_index))
            top_satisfied = self.gem_location(gem_index) <= (.2*Window.height + 50)
            bottom_satisfied = self.gem_location(gem_index) >= (.2*Window.height - 50)

            if top_satisfied and bottom_satisfied:
                self.gem_hit(gem_index)
                self.gem_indices[1::]


        # add logic to see if gem hit

    # called by Player on button up
    def on_button_up(self, lane):
        self.lanes[lane].on_up()

    # called by Player to update score
    def set_score(self, score):
        pass
        
    # for when the window size changes (if needed)
    def on_layout(self, win_size):
        pass

    # call every frame to handle animation needs
    def on_update(self, now_time):
        for b in self.beats:
            visible = b.on_update(now_time)

            if visible:
                if b not in self.children:
                    self.add(b)
            else:
                if b in self.children:
                    self.remove(b)


        for idx, g in enumerate(self.gems):
            visible = g.on_update(now_time)

            if visible:
                if g not in self.children:
                    self.add(g)
                    self.gem_indices.append(idx)

                # can't press if under bar anymore
                if g.gem.pos[1] < .2*Window.height-60:
                    if idx in self.gem_indices:
                        self.gem_indices.remove(idx)
            else:
                if g in self.children:
                    self.remove(g)
                    if idx in self.gem_indices:
                        self.gem_indices.remove(idx)


# Handles game logic and keeps track of score.
# Controls the GameDisplay and AudioCtrl based on what happens
class Player(object):
    def __init__(self, song_data, audio_ctrl, display):
        super(Player, self).__init__()
        self.song_data = song_data
        self.audio_ctrl = audio_ctrl
        self.display = display

        self.score = 0


    # called by MainWidget
    def on_button_down(self, lane):
        self.display.on_button_down(lane, True)

        # if gem_hit(lane):

    # called by MainWidget
    def on_button_up(self, lane):
        self.display.on_button_up(lane)

    # needed to check for pass gems (ie, went past the slop window)
    def on_update(self, time) :
        pass


if __name__ == "__main__":
    run(MainWidget)
