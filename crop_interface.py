
import sys
import os
from PIL import Image as pilImage

from kivy.app import App
from kivy.core.window import Window
from kivy.uix.widget import Widget
from kivy.clock import Clock

from util_interface import *
from util import *




class BaseWidget(Widget):

    def __init__(self, img_size, img_path):
        super(BaseWidget, self).__init__()

        self.img_path = img_path

        Clock.schedule_interval(self.on_update, 0)

        self.t = 0.0
        self.objects = []
        self.interactables = []
        self.rotation_state = False # True = 180 degree rotation

        self.main_img = CRect(pos=(img_size[0]/2.0, img_size[1]/2.0), size=img_size, texture_path=img_path)
        self.objects.append(self.main_img)

        self.button_rotate = Button(((img_size[0]/2.0), img_size[1]+60.0), text="Rotate Image", stateful=False, width=315.0, callback=self.rotate_image)
        self.interactables.append(self.button_rotate)

        self.button_enable_resizing = Button(((img_size[0]/2.0)-336.0, img_size[1]+60.0), text="Enable Auto-Rescaling", stateful=True, width=315.0)
        self.interactables.append(self.button_enable_resizing)

        self.button_batch_transform = Button(((img_size[0]/2.0)+336.0, img_size[1]+60.0), text="Batch Transform", stateful=False, width=315.0, callback=self.batch_transform)
        self.interactables.append(self.button_batch_transform)

        self.crop_corner_a = ImageButton(((img_size[0]/2.0)-100.0, (img_size[1]/2.0)+100.0), (140, 140), "graphics/template_guide_a.png", draggable=True, drag_callback=self.corner_a_drag)
        self.interactables.append(self.crop_corner_a)

        self.crop_corner_b = ImageButton(((img_size[0]/2.0)-100.0, (img_size[1]/2.0)-100.0), (140, 140), "graphics/template_guide_b.png", draggable=True, drag_callback=self.corner_b_drag)
        self.interactables.append(self.crop_corner_b)

        self.crop_corner_c = ImageButton(((img_size[0]/2.0)+100.0, (img_size[1]/2.0)-100.0), (140, 140), "graphics/template_guide_c.png", draggable=True, drag_callback=self.corner_c_drag)
        self.interactables.append(self.crop_corner_c)

        self.crop_corner_d = ImageButton(((img_size[0]/2.0)+100.0, (img_size[1]/2.0)+100.0), (140, 140), "graphics/template_guide_d.png", draggable=True, drag_callback=self.corner_d_drag)
        self.interactables.append(self.crop_corner_d)

        for obj in self.objects:
            self.canvas.add(obj)
        for obj in self.interactables:
            self.canvas.add(obj)

    # callbacks

    def rotate_image(self):
        self.rotation_state = not self.rotation_state

        if self.rotation_state:
            self.main_img.angle = 180.0
        else:
            self.main_img.angle = 0.0

    def batch_transform(self):
        auto_rescaling_enabled = self.button_enable_resizing.state == 2
        rotation_state = self.rotation_state

        batch_path = "/".join(self.img_path.split("/")[:-1])
        output_path = batch_path+"_cropped"
        prepare_path(output_path)

        x_min, x_max, y_min, y_max = self.calculate_crop_bounds_normalized()

        print(" ** Starting batch transform...")
        for path in os.listdir(batch_path):
            if ".jpeg" in path.lower() or ".jpg" in path.lower() or ".png" in path.lower():
                img = np.array(pilImage.open(os.path.join(batch_path, path)))

                if rotation_state:
                    img[:, :, :] = img[::-1, ::-1, :]

                if auto_rescaling_enabled:
                    max_size = max(img.shape[1], img.shape[0])

                    if max_size > 1400:
                        ratio = 1400.0 / max_size
                        img_channels = [
                            rescale(img[:, :, 0].astype(float), scale_factor=ratio),
                            rescale(img[:, :, 1].astype(float), scale_factor=ratio),
                            rescale(img[:, :, 2].astype(float), scale_factor=ratio),
                        ]
                        img = np.stack(img_channels, axis=-1)

                # performs actual cropping
                x_min_ind = min(int((x_min*img.shape[1])+0.5), img.shape[1]-1)
                x_max_ind = min(max(int((x_max*img.shape[1])+0.5), x_min_ind+1), img.shape[1]-1)
                y_min_ind = min(int((y_min*img.shape[0])+0.5), img.shape[0]-1)
                y_max_ind = min(max(int((y_max*img.shape[0])+0.5), y_min_ind+1), img.shape[0]-1)
                img = img[img.shape[0]-1-y_max_ind: img.shape[0]-1-y_min_ind, x_min_ind: x_max_ind, :]

                pilImg = pilImage.fromarray(img.astype(np.uint8))
                pilImg.save(os.path.join(output_path, path))

        print(" ** Batch transform complete")

    def corner_a_drag(self):
        current_corner_pos = self.crop_corner_a.pos
        self.crop_corner_d.set_pos((self.crop_corner_d.pos[0], current_corner_pos[1]))
        self.crop_corner_b.set_pos((current_corner_pos[0], self.crop_corner_b.pos[1]))

    def corner_b_drag(self):
        current_corner_pos = self.crop_corner_b.pos
        self.crop_corner_c.set_pos((self.crop_corner_c.pos[0], current_corner_pos[1]))
        self.crop_corner_a.set_pos((current_corner_pos[0], self.crop_corner_a.pos[1]))

    def corner_c_drag(self):
        current_corner_pos = self.crop_corner_c.pos
        self.crop_corner_b.set_pos((self.crop_corner_b.pos[0], current_corner_pos[1]))
        self.crop_corner_d.set_pos((current_corner_pos[0], self.crop_corner_d.pos[1]))

    def corner_d_drag(self):
        current_corner_pos = self.crop_corner_d.pos
        self.crop_corner_a.set_pos((self.crop_corner_a.pos[0], current_corner_pos[1]))
        self.crop_corner_c.set_pos((current_corner_pos[0], self.crop_corner_c.pos[1]))

    # user input/interaction

    def on_touch_down(self, touch):
        touch_overlap_idcs = []
        for i in range(len(self.interactables)):
            obj = self.interactables[i]
            if hasattr(obj.__class__, 'on_click_down'):
                if touch.pos[0] >= obj.pos[0]-(obj.size[0]*0.5) and touch.pos[0] <= obj.pos[0]+(obj.size[0]*0.5) and touch.pos[1] >= obj.pos[1]-(obj.size[1]*0.5) and touch.pos[1] <= obj.pos[1]+(obj.size[1]*0.5):
                    touch_overlap_idcs.append(i)

        if len(touch_overlap_idcs) > 0:
            obj = self.interactables[touch_overlap_idcs[-1]]
            obj.on_click_down(touch.pos)

        self.corner_a_drag()
        self.corner_b_drag()
        self.corner_c_drag()
        self.corner_d_drag()

    def calculate_crop_bounds_normalized(self):
        x_start = min(max(self.crop_corner_a.pos[0] / self.main_img.size[0], 0.0), 1.0)
        x_end = min(max(self.crop_corner_d.pos[0] / self.main_img.size[0], x_start), 1.0)
        y_start = min(max(self.crop_corner_b.pos[1] / self.main_img.size[1], 0.0), 1.0)
        y_end = min(max(self.crop_corner_a.pos[1] / self.main_img.size[1], y_start), 1.0)

        return x_start, x_end, y_start, y_end

    def on_touch_move(self, touch):
        for obj in self.interactables:
            if hasattr(obj.__class__, 'on_click_move'):
                obj.on_click_move(touch.pos)

    def on_touch_up(self, touch):
        for obj in self.interactables:
            if hasattr(obj.__class__, 'on_click_up'):
                obj.on_click_up(touch.pos)

    def on_update(self, dt):
        self.t += dt
        
        for obj in self.objects:
            obj.on_update(dt)

        for obj in self.interactables:
            obj.on_update(dt)


if __name__ == "__main__":

    ## determines size of specified photo

    img_path = sys.argv[1].strip("/")
    img = np.array(pilImage.open(img_path))
    img_shape = (img.shape[1]/2.0, img.shape[0]/2.0)

    ## launches interface with correct size for specified photo

    Window.size = (img_shape[0], img_shape[1] + 120.0)

    class MainApp(App):
        def build(self):
            self.title = 'Cropping Interface'
            return BaseWidget(img_shape, img_path)

    app = MainApp()
    app.run()

