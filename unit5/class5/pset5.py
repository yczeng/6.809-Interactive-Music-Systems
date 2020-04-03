#pset5: Magic Harp

# common imports
import sys, os
sys.path.insert(0, os.path.abspath('..'))

from common.core import BaseWidget, run
from common.gfxutil import topleft_label, resize_topleft_label, Cursor3D, AnimGroup, KFAnim, scale_point, CEllipse
from common.synth import Synth
from common.audio import Audio
from common.leap import getLeapInfo, getLeapFrame

from kivy.core.window import Window
from kivy.graphics import Color, Line
from kivy.graphics.instructions import InstructionGroup
from kivy.clock import Clock as kivyClock
import numpy as np


# This class displays a single string on screen. It knows how to draw the
# string and how to bend it, and animate it
class String(InstructionGroup):
    def __init__(self, string_id, pitch, x, y_top, y_bottom):
        super(String, self).__init__()

        self.string_id = string_id

        self.x_pos = x
        self.y_top = y_top
        self.y_bottom = y_bottom
        self.mid = (y_top + y_bottom)/2

        self.line = Line(points=[x, y_top, x, self.mid, x, y_bottom])
        self.add(self.line)

        self.plucked = False
        self.grabbed = False

        self.total_time = 0.2
        self.time = 0

        self.moved_string = None

    def pluck(self, old_x):
        self.moved_string = KFAnim((0, old_x), (self.total_time, 0)) 
        self.time = 0
        self.on_update(0)

    # if the string is going to animate (say, when it is plucked), on_update is
    # necessary
    def on_update(self, dt):
        self.time += dt
        if self.moved_string:
            dx = self.moved_string.eval(self.time)
            self.line.points = [self.x_pos, self.y_top, self.x_pos + dx, self.mid, self.x_pos, self.y_bottom]
        return True


# This class monitors the location of the hand and determines if a pluck of
# the string happened. Each PluckGesture is associated with a string (one-to-one
# correspondence). The PluckGesture also controls controls the movement of the
# String it is connected to (to show the string bending)
class PluckGesture(object):
    def __init__(self, string, idx, callback):
        super(PluckGesture, self).__init__()
        self.string = string
        self.idx = idx
        self.callback = callback

        self.pluck_thres = .30
        self.grab_thres = .10

    def set_hand_pos(self, pos):

        diff = abs(pos[0] - self.string.x_pos/Window.width)
        print(diff)

        if diff < self.pluck_thres:
            if diff < self.grab_thres and not self.string.grabbed:
                self.string.grabbed = True
        elif self.string.grabbed:
            self.callback(self.idx)
            self.string.grabbed = False

# The Harp class combines the above classes into a fully working harp. It
# instantiates the strings and pluck gestures as well as a hand cursor display
class Harp(InstructionGroup):
    def __init__(self, synth):
        super(Harp, self).__init__()

        self.synth = synth

        kMargin = Window.width * 0.05
        kCursorSize = Window.width - 2 * kMargin, Window.height - 2 * kMargin
        self.kCursorPos = kMargin, kMargin

        self.hand = Cursor3D(kCursorSize, self.kCursorPos, (.6, .6, .6))

        self.x_pos = Window.size[0]/2
        self.y_top = Window.size[1]
        self.y_bottom = 0
        self.mid = (self.y_top + self.y_bottom)/2


        # # this is from part a
        # self.string = Line(points=[self.x_pos, self.y_top, self.x_pos, self.mid, self.x_pos, self.y_bottom])
        # self.add(self.string)

        # # make string white
        self.add(Color((255,0,0)))

        # put 5 strings
        num_strings = 6
        self.num_strings = num_strings

        # figure out notes / same thing as tuning
        self.notes = [60 + i for i in range(num_strings)]

        # this just happens on on_layout later
        self.strings = []
        self.pluck_gestures = []

        self.win_size = Window.size

        self.moved_point = (0,0)


    # will get called when the window size changes.
    def on_layout(self, win_size):
        self.win_size = win_size
        self.hand.set_boundary(win_size, self.kCursorPos)

        for string in self.strings:
            self.objects.remove(string)

        self.x_pos = win_size[0]/2
        self.y_top = win_size[1]
        self.y_bottom = 0
        self.mid = (self.y_top + self.y_bottom)/2

        # put 5 strings
        num_strings = self.num_strings

        x_positions = [Window.width/num_strings * i for i in range(num_strings)]

        print(x_positions)

        self.strings = [String(i, self.notes[i], x_positions[i], self.y_top, self.y_bottom) for i in range(num_strings)]

        self.objects = AnimGroup()
        for string in self.strings:
            self.objects.add(string)
        self.add(self.objects)

        self.pluck_gestures = [PluckGesture(string, string.string_id, self.on_pluck) for string in self.strings]

    # set the hand position as a normalized 3D vector ranging from [0,0,0] to [1,1,1]
    def set_hand_pos(self, pos):
        norm_pt = pos
        self.hand.set_pos(norm_pt)

        # inactive (not plucking is red)
        active = (0,150,0)
        # active is green
        inactive_color = (150,0,0)

        # not active
        if norm_pt[2] >= 0.5:
            self.hand.set_color(inactive_color)
        # is active
        else:
            for pluck_gesture in self.pluck_gestures:
                pluck_gesture.set_hand_pos(norm_pt)
            self.hand.set_color(active)

    # callback to be called from a PluckGesture when a pluck happens
    def on_pluck(self, idx):
        #plays a note
        pitch = self.notes[idx]

        self.synth.noteon(0, pitch, 100)
        # print('pluck:', idx)

    # this might be needed if Harp's internal objects need on_update()
    def on_update(self, pos):
        self.objects.on_update()

class MainWidget(BaseWidget) :
    def __init__(self):
        super(MainWidget, self).__init__()

        self.label = topleft_label()
        self.add_widget(self.label)

        self.audio = Audio(2)
        self.synth = Synth("../data/FluidR3_GM.sf2")
        self.audio.set_generator(self.synth)

        self.harp = Harp(self.synth)
        self.canvas.add(self.harp.hand)
        self.canvas.add(self.harp)

    # will get called when the window size changes. Pass this information down
    # to Harp so that you appropriately resize it and its subcomponents.
    def on_layout(self, win_size):
        # update self.label
        resize_topleft_label(self.label)
        self.harp.on_layout(win_size)

    def on_update(self) :
        leap_frame = getLeapFrame()
        hand = leap_frame.hands[0]
        norm_pt = scale_point(hand.palm_pos, kLeapRange)

        self.harp.hand.set_pos(norm_pt)

        self.label.text = str(getLeapInfo()) + '\n'
        self.harp.set_hand_pos(norm_pt)
        self.audio.on_update()


# for use with scale_point
# x, y, and z ranges to define a 3D bounding box
kLeapRange   = ( (-250, 250), (100, 500), (-200, 250) )

if __name__ == "__main__":
    # pass in which MainWidget to run as a command-line arg
    run(MainWidget)
