import os
import shutil
import numpy as np
import skimage.transform
from PIL import Image


def prepare_path(path):
    if os.path.exists(path):
        shutil.rmtree(path)
    os.mkdir(path)

def load_np_image(path):
    img = Image.open(path)
    np_img = np.array(img).astype(float) / 256.0
    np_img = np.transpose(np_img, [2, 0, 1])

    return np_img

def preview_np_image(np_img, path):
    np_img = np.transpose(np_img, [1, 2, 0])
    np_img = (np_img * 255.99).astype(np.uint8)
    img = Image.fromarray(np_img)

    if "." not in path:
        path = path + ".png"
    img.save(path)

def rescale(np_img, scale_factor=0.5):
    img = skimage.transform.rescale(np_img, scale_factor, anti_aliasing=True)
    return img

