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
    def __init__(self, ):
        super(String, self).__init__()

    # if the string is going to animate (say, when it is plucked), on_update is
    # necessary
    def on_update(self, dt):
        pass


# This class monitors the location of the hand and determines if a pluck of
# the string happened. Each PluckGesture is associated with a string (one-to-one
# correspondence). The PluckGesture also controls controls the movement of the
# String it is connected to (to show the string bending)
class PluckGesture(object):
    def __init__(self, string, idx, callback):
        super(PluckGesture, self).__init__()



# The Harp class combines the above classes into a fully working harp. It
# instantiates the strings and pluck gestures as well as a hand cursor display
class Harp(InstructionGroup):
    def __init__(self):
        super(Harp, self).__init__()

        kMargin = Window.width * 0.05
        kCursorSize = Window.width - 2 * kMargin, Window.height - 2 * kMargin
        self.kCursorPos = kMargin, kMargin

        self.hand = Cursor3D(kCursorSize, self.kCursorPos, (.6, .6, .6))
        # self.canvas.add(self.hand)

        self.active_color = (0,255,0)
        self.inactive_color = (255,0,0)

        self.add(Color(self.inactive_color))

        self.string = Line(points=(Window.width/2, Window.height, Window.width/2, 0), width=3)
        self.add(self.string)

        self.win_size = Window.size


    # will get called when the window size changes.
    def on_layout(self, win_size):
        self.win_size = win_size
        self.hand.set_boundary(win_size, self.kCursorPos)

        self.remove(self.string)

        self.string = Line(points=(win_size[0]/2, win_size[1], win_size[0]/2, 0), width=3)
        self.add(self.string)

    # set the hand position as a normalized 3D vector ranging from [0,0,0] to [1,1,1]
    def set_hand_pos(self, pos):

        print(pos)

        z = pos[2]
        print(z)
        self.hand.set_pos(pos)

        active_color = (0,255,0)
        inactive_color = (255,0,0)

        if z >= 0.2:
            self.hand.set_color(active_color)
        else:
            self.hand.set_color(inactive_color)

    # callback to be called from a PluckGesture when a pluck happens
    def on_pluck(self, idx):
        print('pluck:', idx)

    # this might be needed if Harp's internal objects need on_update()
    def on_update(self):
        pass


class MainWidget(BaseWidget) :
    def __init__(self):
        super(MainWidget, self).__init__()

        self.label = topleft_label()
        self.add_widget(self.label)

        self.harp = Harp()
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

# for use with scale_point
# x, y, and z ranges to define a 3D bounding box
kLeapRange   = ( (-250, 250), (100, 500), (-200, 250) )

if __name__ == "__main__":
    # pass in which MainWidget to run as a command-line arg
    run(MainWidget)
