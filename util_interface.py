from kivy.graphics import Color, Line, Rectangle, RoundedRectangle, Ellipse, PushMatrix, PopMatrix, Rotate
from kivy.core.image import Image
from kivy.core.window import Window
from kivy.uix.label import Label
from kivy.graphics.instructions import InstructionGroup

from util import *

import random
import numpy as np

global_snap_coefficient = 22.0




class ImageButton(InstructionGroup):
    def __init__(self, pos, size, texture_path, draggable=True, callback=None, drag_callback=None):
        super(ImageButton, self).__init__()

        self.pos = pos
        self.size = size
        self.callback = callback
        self.drag_callback = drag_callback
       
        self.draggable = draggable
        self.state = 0 # 0=off, 1,3=being clicked, 2=on

        self.bg_rect = CRect(self.pos, self.size, texture_path=texture_path)
        self.add(self.bg_rect)

    def on_update(self, dt):
        self.bg_rect.on_update(dt)

    def set_pos(self, new_target_pos):
        self.pos = new_target_pos
        self.bg_rect.target_pos = new_target_pos

    def on_click_down(self, touch_pos):
        if touch_pos[0] > self.pos[0]-(self.size[0]/2.0) and touch_pos[0] < self.pos[0]+(self.size[0]/2.0) and touch_pos[1] > self.pos[1]-(self.size[1]/2.0) and touch_pos[1] < self.pos[1]+(self.size[1]/2.0):
            if self.state == 0:
                self.state = 1
            elif self.state == 2:
                self.state = 3

            if self.draggable:
                self.pos = touch_pos
                self.bg_rect.target_pos = touch_pos

    def on_click_move(self, touch_pos):
        if self.draggable and (self.state == 1 or self.state == 3):
            self.pos = touch_pos
            self.bg_rect.target_pos = touch_pos

            if self.drag_callback is not None:
                self.drag_callback()

    def on_click_up(self, touch_pos):
        if self.state == 1 or self.state == 3:
            self.state = 0

            if self.draggable:
                self.pos = touch_pos
                self.bg_rect.target_pos = touch_pos

            if self.callback is not None:
                self.callback()

class Button(InstructionGroup):
    def __init__(self, pos, text="Button", stateful=False, draggable=False, initial_state=0, width=300.0, callback=None):
        super(Button, self).__init__()

        self.pos = pos
        self.size = (width, 65.0)
        self.callback = callback

        self.text = text
        self.stateful = stateful
        self.draggable = draggable
        self.state = initial_state # 0=off, 1,3=being clicked, 2=on

        self.bg_rect = CRoundedRect(self.pos, self.size, corner_radius = 20.0, color = (0.8, 0.3, 0.3))
        self.add(self.bg_rect)

        self.label = LabelRect(self.text, self.pos, size=(1.0, 1.0), font_size = 25, color = (0, 0, 0))
        self.add(self.label)

    def on_update(self, dt):

        if self.state == 0:
            self.bg_rect.target_color_components = [0.8, 0.3, 0.3]
        elif self.state == 1 or self.state == 3:
            self.bg_rect.target_color_components = [0.8, 0.8, 0.8]
        elif self.state == 2:
            self.bg_rect.target_color_components = [0.3, 0.3, 0.8]

        self.bg_rect.on_update(dt)
        self.label.on_update(dt)

    def on_click_down(self, touch_pos):
        if touch_pos[0] > self.pos[0]-(self.size[0]/2.0) and touch_pos[0] < self.pos[0]+(self.size[0]/2.0) and touch_pos[1] > self.pos[1]-(self.size[1]/2.0) and touch_pos[1] < self.pos[1]+(self.size[1]/2.0):
            if self.state == 0:
                self.state = 1
            elif self.state == 2:
                self.state = 3

            if self.draggable:
                self.pos = touch_pos
                self.bg_rect.target_pos = touch_pos
                self.label.target_pos = touch_pos

    def on_click_move(self, touch_pos):
        if self.draggable and (self.state == 1 or self.state == 3):
            self.pos = touch_pos
            self.bg_rect.target_pos = touch_pos
            self.label.target_pos = touch_pos

    def on_click_up(self, touch_pos):
        if self.state == 1 and self.stateful:
            self.state = 2

            if self.draggable:
                self.pos = touch_pos
                self.bg_rect.target_pos = touch_pos
                self.label.target_pos = touch_pos

            if self.callback is not None:
                self.callback()
        elif self.state == 1 or self.state == 3:
            self.state = 0

            if self.draggable:
                self.pos = touch_pos
                self.bg_rect.target_pos = touch_pos
                self.label.target_pos = touch_pos

            if self.callback is not None:
                self.callback()

class CRect(InstructionGroup):
    def __init__(self, pos, size, color = (1.0, 1.0, 1.0), texture_path = "", snap_coefficient = global_snap_coefficient):
        super(CRect, self).__init__()

        self.uuid = unique_identifier()
        self.pos = pos
        self.size = size
        self.target_pos = self.pos
        self.target_size = self.size
        self.snap_coefficient = snap_coefficient
        self.angle = 0.0

        self.shape = Rectangle(pos=(pos[0]-(size[0]*0.5), pos[1]-(size[1]*0.5)), size=size)
        self.color = Color(color[0], color[1], color[2])
        self.rotate_instruction = Rotate(origin=self.pos, angle=self.angle)
        self.add(PushMatrix())
        self.add(self.rotate_instruction)
        self.add(self.color)
        self.add(self.shape)
        self.add(PopMatrix())

        # rectangles only
        self.texture_path = texture_path
        if isinstance(self.shape, Rectangle) and self.texture_path != "":
            self.shape.texture = Image(self.texture_path).texture

    def on_update(self, dt):
        self.rotate_instruction.angle = self.angle

        shape_needs_update = False
        if self.target_pos != self.pos:
            self.pos = (self.pos[0] + (self.snap_coefficient * dt * (self.target_pos[0] - self.pos[0])), self.pos[1] + (self.snap_coefficient * dt * (self.target_pos[1] - self.pos[1])))
            shape_needs_update = True
        if self.target_size != self.size:
            self.size = (self.size[0] + (self.snap_coefficient * dt * (self.target_size[0] - self.size[0])), self.size[1] + (self.snap_coefficient * dt * (self.target_size[1] - self.size[1])))
            shape_needs_update = True

        if shape_needs_update:
            self.shape.pos = (self.pos[0]-(self.size[0]*0.5), self.pos[1]-(self.size[1]*0.5))
            self.shape.size = self.size

    def change_texture(self, new_texture_path):
        if isinstance(self.shape, Rectangle):
            if new_texture_path != self.texture_path:
                self.texture_path = new_texture_path
                if self.texture_path != "":
                    self.shape.texture = Image(self.texture_path).texture

    def set_pos(self, new_pos):
        self.pos = new_pos
        self.target_pos = new_pos
        self.shape.pos = (self.pos[0]-(self.size[0]*0.5), self.pos[1]-(self.size[1]*0.5))

class CCircle(InstructionGroup):
    def __init__(self, pos, size, color = (1.0, 1.0, 1.0), snap_coefficient = global_snap_coefficient):
        super(CCircle, self).__init__()

        self.uuid = unique_identifier()
        self.pos = pos
        self.size = size
        self.target_pos = self.pos
        self.target_size = self.size
        self.snap_coefficient = snap_coefficient

        self.shape = Ellipse(pos=(pos[0]-(size[0]*0.5), pos[1]-(size[1]*0.5)), size=size)
        self.color = Color(color[0], color[1], color[2])
        self.add(self.color)
        self.add(self.shape)

    def on_update(self, dt):
        shape_needs_update = False
        if self.target_pos != self.pos:
            self.pos = (self.pos[0] + (self.snap_coefficient * dt * (self.target_pos[0] - self.pos[0])), self.pos[1] + (self.snap_coefficient * dt * (self.target_pos[1] - self.pos[1])))
            shape_needs_update = True
        if self.target_size != self.size:
            self.size = (self.size[0] + (self.snap_coefficient * dt * (self.target_size[0] - self.size[0])), self.size[1] + (self.snap_coefficient * dt * (self.target_size[1] - self.size[1])))
            shape_needs_update = True

        if shape_needs_update:
            self.shape.pos = (self.pos[0]-(self.size[0]*0.5), self.pos[1]-(self.size[1]*0.5))
            self.shape.size = self.size

    def set_pos(self, new_pos):
        self.pos = new_pos
        self.target_pos = new_pos
        self.shape.pos = (self.pos[0]-(self.size[0]*0.5), self.pos[1]-(self.size[1]*0.5))

class CRoundedRect(InstructionGroup):
    def __init__(self, pos, size, corner_radius = 20.0, color = (1.0, 1.0, 1.0), snap_coefficient = global_snap_coefficient):
        super(CRoundedRect, self).__init__()

        self.uuid = unique_identifier()
        self.pos = pos
        self.size = size
        self.target_pos = self.pos
        self.target_size = self.size
        self.snap_coefficient = snap_coefficient
        self.corner_radius = corner_radius
        self.force_update = False

        self.shape = RoundedRectangle(pos=(pos[0]-(size[0]*0.5), pos[1]-(size[1]*0.5)), size=size, radius=[self.corner_radius])
        self.color_components = list(color)
        self.target_color_components = list(color)
        self.color = Color(self.color_components[0], self.color_components[1], self.color_components[2])
        self.add(self.color)
        self.add(self.shape)

    def on_update(self, dt, force_update=False):
        shape_needs_update = False
        if self.target_pos != self.pos:
            self.pos = (self.pos[0] + (self.snap_coefficient * dt * (self.target_pos[0] - self.pos[0])), self.pos[1] + (self.snap_coefficient * dt * (self.target_pos[1] - self.pos[1])))
            shape_needs_update = True
        if self.target_size != self.size:
            self.size = (self.size[0] + (self.snap_coefficient * dt * (self.target_size[0] - self.size[0])), self.size[1] + (self.snap_coefficient * dt * (self.target_size[1] - self.size[1])))
            shape_needs_update = True

        if shape_needs_update or force_update or self.force_update:
            if self.force_update:
                self.force_update = False
            self.shape.pos = (self.pos[0]-(self.size[0]*0.5), self.pos[1]-(self.size[1]*0.5))
            self.shape.size = self.size

        # color separately
        if self.target_color_components != self.color_components:
            self.color_components[0] = self.color_components[0] + (self.snap_coefficient * dt * (self.target_color_components[0] - self.color_components[0]))
            self.color_components[1] = self.color_components[1] + (self.snap_coefficient * dt * (self.target_color_components[1] - self.color_components[1]))
            self.color_components[2] = self.color_components[2] + (self.snap_coefficient * dt * (self.target_color_components[2] - self.color_components[2]))
            self.color.r = self.color_components[0]
            self.color.g = self.color_components[1]
            self.color.b = self.color_components[2]

    def set_color(self, new_color, dont_set_target=False):
        self.color_components = list(new_color)
        if not dont_set_target:
            self.target_color_components = list(new_color)
        self.color.r = self.color_components[0]
        self.color.g = self.color_components[1]
        self.color.b = self.color_components[2]

    def set_pos(self, new_pos):
        self.pos = new_pos
        self.target_pos = new_pos
        self.shape.pos = (self.pos[0]-(self.size[0]*0.5), self.pos[1]-(self.size[1]*0.5))

class CLine(InstructionGroup):
    def __init__(self, points, color = (1.0, 1.0, 1.0), line_width = 2.0, line_type = 'straight'):
        super(CLine, self).__init__()

        self.uuid = unique_identifier()
        self.points = points
        self.middle = self.compute_middle()
        self.initial_middle = self.middle

        self.color = Color(color[0], color[1], color[2])
        self.line_width = line_width
        self.line = None
        self.line_type = line_type
        if self.line_type == "straight":
            self.line = Line(points=self.interlace_points(), width=self.line_width)
        elif self.line_type == "bezier" or self.line_type == "curved":
            self.line = Line(bezier=self.interlace_points(), width=self.line_width)
        self.add(self.color)
        self.add(self.line)

    def interlace_points(self):
        interlaced_points = []
        for point in self.points:
            interlaced_points.append(point[0])
            interlaced_points.append(point[1])
        return interlaced_points

    def compute_middle(self):
        return ( ((self.points[-1][0] + self.points[0][0]) * 0.5), ((self.points[-1][1] + self.points[0][1]) * 0.5) )

    def on_update(self, dt):
        # self.remove(self.color)
        # self.remove(self.line)

        # self.add(self.color)
        # if self.line_type == "straight":
        #     self.line = Line(points=self.interlace_points(), width=self.line_width)
        # elif self.line_type == "bezier" or self.line_type == "curved":
        #     self.line = Line(bezier=self.interlace_points(), width=self.line_width)
        # self.add(self.line)

        # if self.line_type == "straight":
        #     self.line.points = self.interlace_points()
        # elif self.line_type == "bezier" or self.line_type == "curved":
        #     self.line.bezier = self.interlace_points()

        pass

class LabelRect(InstructionGroup):
    def __init__(self, text, pos, size=(1.0, 1.0), font_size = 21, color = (1, 1, 1), snap_coefficient = global_snap_coefficient):
        super(LabelRect, self).__init__()

        self.uuid = unique_identifier()
        self.pos = pos
        self.size = size
        self.target_pos = pos
        self.target_size = size
        self.snap_coefficient = snap_coefficient
        self.font_size = font_size

        self.color_components = list(color)
        self.target_color_components = list(color)
        self.color = Color(self.color_components[0], self.color_components[1], self.color_components[2], 1.0)
        self.add(self.color)

        self.label = Label(text=text, font_size=str(self.font_size)+"sp", font_name="fonts/Righteous.ttf")
        self.label.texture_update()
        self.rect = Rectangle(pos=(pos[0]-(self.label.texture_size[0]*0.5*self.size[0]), pos[1]-(self.label.texture_size[1]*0.5*self.size[1])), size=(self.label.texture_size[0]*self.size[0], self.label.texture_size[1]*self.size[1]), texture=self.label.texture)
        self.add(self.rect)

    def on_update(self, dt):
        shape_needs_update = False
        if self.target_pos != self.pos:
            self.pos = (self.pos[0] + (self.snap_coefficient * dt * (self.target_pos[0] - self.pos[0])), self.pos[1] + (self.snap_coefficient * dt * (self.target_pos[1] - self.pos[1])))
            shape_needs_update = True
        if self.target_size != self.size:
            self.size = (self.size[0] + (self.snap_coefficient * dt * (self.target_size[0] - self.size[0])), self.size[1] + (self.snap_coefficient * dt * (self.target_size[1] - self.size[1])))
            shape_needs_update = True

        if shape_needs_update:
            self.rect.pos = (self.pos[0]-(self.label.texture_size[0]*0.5*self.size[0]), self.pos[1]-(self.label.texture_size[1]*0.5*self.size[1]))
            self.rect.size = (self.label.texture_size[0]*self.size[0], self.label.texture_size[1]*self.size[1])

        # color separately
        if self.target_color_components != self.color_components:
            self.color_components[0] = self.color_components[0] + (self.snap_coefficient * dt * (self.target_color_components[0] - self.color_components[0]))
            self.color_components[1] = self.color_components[1] + (self.snap_coefficient * dt * (self.target_color_components[1] - self.color_components[1]))
            self.color_components[2] = self.color_components[2] + (self.snap_coefficient * dt * (self.target_color_components[2] - self.color_components[2]))
            self.color.r = self.color_components[0]
            self.color.g = self.color_components[1]
            self.color.b = self.color_components[2]

    def set_color(self, new_color, dont_set_target=False):
        self.color_components = list(new_color)
        if not dont_set_target:
            self.target_color_components = list(new_color)
        self.color.r = self.color_components[0]
        self.color.g = self.color_components[1]
        self.color.b = self.color_components[2]

    def set_pos(self, new_pos):
        self.pos = new_pos
        self.target_pos = new_pos
        self.rect.pos = (self.pos[0]-(self.label.texture_size[0]*0.5*self.size[0]), self.pos[1]-(self.label.texture_size[1]*0.5*self.size[1]))

    def set_text(self, next_text):
        self.label = Label(text=next_text, font_size=str(self.font_size)+"sp", font_name="./fonts/Righteous.ttf")
        self.label.texture_update()

        # self.rect = Rectangle(pos=, size=self.label.texture_size, texture=self.label.texture)
        self.rect.pos = (self.pos[0]-(self.label.texture_size[0]*0.5*self.size[0]), self.pos[1]-(self.label.texture_size[1]*0.5*self.size[1]))
        self.rect.size = (self.label.texture_size[0]*self.size[0], self.label.texture_size[1]*self.size[1])
        self.rect.texture = self.label.texture




