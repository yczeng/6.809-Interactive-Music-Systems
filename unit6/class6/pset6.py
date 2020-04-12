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
        button_idx = lookup(keycode[1], '12345', (0,1,2,3,4))
        if button_idx != None:
            print('down', button_idx)
            self.player.on_button_down(button_idx)

    def on_key_up(self, keycode):
        # button up
        button_idx = lookup(keycode[1], '12345', (0,1,2,3,4))
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
            for line in lines:
                new_gem = line.replace("\n", "").replace(" ", "").split("\t")
                self.gems.append(new_gem)

        return self.gems

    def get_barlines(self):
        for bar in self.barlines:
            with open("../data/ziggy_barlines_annotation.txt") as f:
                lines = f.readlines()
                for line in lines:
                    barline = line.replace("\n", "").replace(" ", "").split("\t")
                    self.barlines.append(barline[0])

        return self.barlines


# Display for a single gem at a position with a hue or color
class GemDisplay(InstructionGroup):
    def __init__(self, lane, time, color):
        super(GemDisplay, self).__init__()
        self.lane = lane
        self.time = time
        self.color = color

        lane_width = Window.width / 4
        lane_pos = [lane_width, 2*lane_width, 3*lane_width]

        pos = (lane_pos[lane], Window.height - 10)

        self.gem = Rectangle(pos = pos, size=(100,100), source ="../data/gem.png")
        self.add(self.shape)

    # change to display this gem being hit
    def on_hit(self):
        self.gem.source = "../data/gem_hit.png"

    # change to display a passed or missed gem
    def on_pass(self):
        self.gem.source = "../data/gem_opaque.png"

    # animate gem (position and animation) based on current time
    def on_update(self, now_time):
        pass


# Displays a single barline on screen
class BarlineDisplay(InstructionGroup):
    def __init__(self, time):
        super(BarlineDisplay, self).__init__()

        self.time = time
        self.line = Line(points=(.1*Window.width, .2*Window.height, 0.9*Window.width, .2*Window.height), width=3)
        self.add(self.line)

    # animate barline (position) based on current time
    def on_update(self, now_time):
        pass


# Displays one button on the nowbar
class ButtonDisplay(InstructionGroup):
    def __init__(self, lane, color):
        super(ButtonDisplay, self).__init__()
        self.color = Color(hsv=color)
        self.add(self.color)
        self.source = "../data/red_star.png"

    # displays when button is pressed down
    def on_down(self):
        self.shape.size(250,250)

    # back to normal state
    def on_up(self):
        self.shape.size(200,200)

    # modify object positions based on new window size
    def on_layout(self, win_size):
        pass


# Displays all game elements: nowbar, buttons, barlines, gems
class GameDisplay(InstructionGroup):
    def __init__(self, song_data):
        super(GameDisplay, self).__init__()

    # called by Player when succeeded in hitting this gem.
    def gem_hit(self, gem_idx):
        pass

    # called by Player on pass or miss.
    def gem_pass(self, gem_idx):
        pass

    # called by Player on button down
    def on_button_down(self, lane):
        pass

    # called by Player on button up
    def on_button_up(self, lane):
        pass

    # called by Player to update score
    def set_score(self, score):
        pass
        
    # for when the window size changes (if needed)
    def on_layout(self, win_size):
        pass

    # call every frame to handle animation needs
    def on_update(self, now_time):
        pass


# Handles game logic and keeps track of score.
# Controls the GameDisplay and AudioCtrl based on what happens
class Player(object):
    def __init__(self, song_data, audio_ctrl, display):
        super(Player, self).__init__()
        self.song_data = song_data
        self.audio_ctrl = audio_ctrl
        self.display = display

    # called by MainWidget
    def on_button_down(self, lane):
        self.display.on_button_down(lane)
        # TODO add code to figure out hit or miss

    # called by MainWidget
    def on_button_up(self, lane):
        self.display.on_button_down(lane)

    # needed to check for pass gems (ie, went past the slop window)
    def on_update(self, time) :
        pass


if __name__ == "__main__":
    run(MainWidget)
