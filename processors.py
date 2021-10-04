import numpy as np
import shutil
import random
import scipy
from util import *

class PictureVectorizer(object):
    def __init__(self, threshold=0.725, coeff=10.0, target_size=860, stroke_width=1.2, color='black', min_dist_threshold=3.85, close_trace_threshold=2.25):
        self.threshold = threshold
        self.coeff = coeff
        self.target_size = target_size
        self.stroke_width = stroke_width
        self.color = color
        self.min_dist_threshold = min_dist_threshold
        self.close_trace_threshold = close_trace_threshold

    def traverse_to_point(self, contour_pixels, new_pixel, min_dist_threshold=3.0, force_traverse=False):

        # adds new point to contour if exceeds min_dist_threshold
        dist = np.linalg.norm(np.array(new_pixel) - np.array(contour_pixels[-1]))
        if dist > min_dist_threshold or force_traverse:
            contour_pixels.append(new_pixel)

        return contour_pixels

    def find_direction_to_parent(self, offsets, parent_pixel, current_pixel):

        # safety check
        if parent_pixel is None:
            return 1

        diff = ((parent_pixel[0] - current_pixel[0]), (parent_pixel[1] - current_pixel[1]))
        for i in range(len(offsets)):
            if offsets[i] == diff:
                return i
        return 1

    def trace_cluster(self, offsets, starting_pixel, cluster_pixels_img, min_dist_threshold=3.85, close_trace_threshold=2.0, debug_prefix="0"): # returns list of pixels in cluster contour
        contour_pixels = [starting_pixel]

        debug_img = np.zeros(cluster_pixels_img.shape)

        heads = [[starting_pixel]]
        previous_head = None
        explored_pixels_hash = {}
        active_heads_hash = {str(starting_pixel[0])+" "+str(starting_pixel[1]): 1}
        tries = 0
        while len(heads) > 0:

            current_head = heads.pop(0)
            current_pixel = current_head[-1]
            tries += 1

            cluster_pixels_img[0, current_pixel[0], current_pixel[1]] = 0.0
            cluster_pixels_img[1, current_pixel[0], current_pixel[1]] = 1.0
            cluster_pixels_img[2, current_pixel[0], current_pixel[1]] = 0.0
            debug_img[:, current_pixel[0], current_pixel[1]] = 1.0

            # TODO: replace with better algorithm
            # tracks last point/head and traverse to current point if huge gap
            if previous_head is not None and previous_head[-1] not in current_head:

                # traverses to common ancestor, then up to current pixel's parent
                previous_ancestor_idx = 0
                for j in range(len(previous_head)):
                    i = len(previous_head)-1-j

                    contour_pixels = self.traverse_to_point(contour_pixels, previous_head[i], min_dist_threshold=min_dist_threshold)

                    if previous_head[i] in current_head:
                        previous_ancestor_idx = i
                        break
                passed_ancestor = False
                for i in range(len(current_head)-1):
                    if current_head[i] == previous_head[previous_ancestor_idx]:
                        passed_ancestor = True

                    if passed_ancestor:
                        contour_pixels = self.traverse_to_point(contour_pixels, current_head[i], min_dist_threshold=min_dist_threshold)

            # traverses to next point
            contour_pixels = self.traverse_to_point(contour_pixels, current_pixel, min_dist_threshold=min_dist_threshold)

            # marks current pixel as explored
            explored_pixels_hash[str(current_pixel[0])+" "+str(current_pixel[1])] = 1
            if str(current_pixel[0])+" "+str(current_pixel[1]) in active_heads_hash:
                del active_heads_hash[str(current_pixel[0])+" "+str(current_pixel[1])]

            # constructs 3x-length list of neighbor pixels
            neighbors = []
            proto_neighbors = self.get_neighbors(offsets, cluster_pixels_img, current_pixel, {}, include_white_pixels=True, include_corners=True)[0]
            for nbr in proto_neighbors:
                neighbors.append(nbr)
            for nbr in proto_neighbors:
                neighbors.append(nbr)
            for nbr in proto_neighbors:
                neighbors.append(nbr)

            # iterates through neighbors clockwise starting from direction back to parent
            parent_pixel = None
            if len(current_head) > 1:
                parent_pixel = current_head[-2]
            starting_neighbors_idx = self.find_direction_to_parent(offsets, parent_pixel, current_pixel)
            num_new_heads = 0

            # print(" * "+str(tries)+": "+str(len(current_head)))
            for i in range(starting_neighbors_idx, starting_neighbors_idx+len(proto_neighbors)):
                neighbor = neighbors[i]
                prev_neighbor = neighbors[i-1]

                # if neighboring pixel is a valid border pixel/head...
                if str(neighbor[0])+" "+str(neighbor[1]) not in explored_pixels_hash and str(neighbor[0])+" "+str(neighbor[1]) not in active_heads_hash and cluster_pixels_img[0, neighbor[0], neighbor[1]] <= 0.5 and cluster_pixels_img[0, prev_neighbor[0], prev_neighbor[1]] > 0.5:

                    # starts new head for each valid border pixel
                    new_head = current_head[:]
                    new_head.append(neighbor)

                    heads.insert(num_new_heads, new_head)
                    active_heads_hash[str(neighbor[0])+" "+str(neighbor[1])] = 1
                    num_new_heads += 1

                elif str(neighbor[0])+" "+str(neighbor[1]) in active_heads_hash and str(neighbor[0])+" "+str(neighbor[1]) not in explored_pixels_hash:

                    # finds corresponding head
                    neighbor_head = None
                    neighbor_head_idx = None
                    for i in range(len(heads)):
                        head = heads[i]
                        if head[-1] == neighbor:
                            neighbor_head = head
                            neighbor_head_idx = i
                            break

                    # clears existing head from exploration
                    heads = heads[:neighbor_head_idx] + heads[neighbor_head_idx:]

                    # starts new head for each valid border pixel
                    new_head = current_head[:]
                    new_head.append(neighbor)

                    heads.insert(num_new_heads, new_head)
                    active_heads_hash[str(neighbor[0])+" "+str(neighbor[1])] = 1
                    num_new_heads += 1
                elif neighbor == current_head[0] and len(current_head) > 11: # TODO: remove? might not be doing anything
                    num_new_heads = 0
                    heads = []
                    active_heads_hash = {}

                    break

            if num_new_heads == 0:

                if len(heads) > 0:
                    # trace back to common ancestor of next head
                    for j in range(len(heads[0])):
                        i = len(heads[0])-j-1

                        # traverse
                        contour_pixels = self.traverse_to_point(contour_pixels, heads[0][i], min_dist_threshold=min_dist_threshold)

                        if heads[0][i] in current_head:
                            break
                else:

                    # tracing finished, close shape if within distance threshold
                    dist = np.linalg.norm(np.array(current_pixel) - np.array(current_head[0]))
                    if dist < close_trace_threshold:

                        # traverse back to origin
                        contour_pixels = self.traverse_to_point(contour_pixels, current_head[0], min_dist_threshold=min_dist_threshold, force_traverse=True)
                    else:

                        # walks back through head to origin
                        for j in range(len(current_head)):
                            i = len(current_head)-j-1

                            # traverse
                            contour_pixels = self.traverse_to_point(contour_pixels, current_head[i], min_dist_threshold=min_dist_threshold)
            # try:
            #     cluster_pixels_img_copy = np.copy(cluster_pixels_img)
            #     cluster_pixels_img_copy[0, current_pixel[0], current_pixel[1]] = 1.0
            #     cluster_pixels_img_copy[1, current_pixel[0], current_pixel[1]] = 0.0
            #     cluster_pixels_img_copy[2, current_pixel[0], current_pixel[1]] = 0.0
            #     preview_np_image(cluster_pixels_img_copy[:, current_pixel[0]-10:current_pixel[0]+11, current_pixel[1]-10:current_pixel[1]+11], "test_debug/"+debug_prefix+"_"+str(tries)+".png")
            # except:
            #     pass

            previous_head = current_head

        return contour_pixels, debug_img

    def get_neighbors(self, offsets, contrasted_img, parent_pixel, cluster_pixels_hash, include_white_pixels=False, include_corners=True):
        valid_neighbors = []

        for offset in offsets:
            i = offset[0]
            j = offset[1]

            if not include_corners and (i != 0 and j != 0):
                continue

            if i != 0 or j != 0: # safety check, not explicitly necessary
                pixel = (parent_pixel[0]+i, parent_pixel[1]+j)

                # marks valid neighbors that are within image bounds, infilled
                if str(pixel[0])+" "+str(pixel[1]) not in cluster_pixels_hash and pixel[0] >= 0 and pixel[0] < contrasted_img.shape[1] and pixel[1] >= 0 and pixel[1] < contrasted_img.shape[2]:
                    if not include_white_pixels and contrasted_img[0, pixel[0], pixel[1]] < 0.5:
                        valid_neighbors.append(pixel)
                    elif include_white_pixels:
                        valid_neighbors.append(pixel)

        return valid_neighbors, len(valid_neighbors) <= 7

    def explore_cluster(self, offsets, contrasted_img, starting_pixel): # returns list of pixels in cluster
        cluster_pixels = []
        exterior_pixels_img = np.ones(contrasted_img.shape)
        cluster_pixels_hash = {}
        queue = [starting_pixel]

        # BFS, finds all infilled pixels connected to a start pixel
        while len(queue) > 0:
            start_pixel = queue.pop(0)

            if str(start_pixel[0])+" "+str(start_pixel[1]) not in cluster_pixels_hash:
                cluster_pixels.append(start_pixel)
                cluster_pixels_hash[str(start_pixel[0])+" "+str(start_pixel[1])] = 1

                neighbors, is_exterior = self.get_neighbors(offsets, contrasted_img, start_pixel, cluster_pixels_hash, include_corners=True)
                for neighbor in neighbors:
                    queue.append(neighbor)

                # also constructs outline/exterior of cluster
                # if is_exterior:
                exterior_pixels_img[:, start_pixel[0], start_pixel[1]] = 0.0

        return cluster_pixels, exterior_pixels_img

    def find_clusters(self, contrasted_img):
        clusters = []

        # creates neighborhood of pixels to search for each central pixel
        offsets = [] # must be sorted by outward spiral
        for i in range(-1, 2):
            for j in range(-1, 2):
                if i != 0 or j != 0:
                    offsets.append((i, j))
        offsets.sort(key=lambda x: np.arctan2(x[0], x[1]))

        # debug_img = np.zeros(contrasted_img.shape)
        # debug_img_b = np.zeros(contrasted_img.shape)

        # explores clusters once a filled pixel is reached
        clustered_pixels = {}
        debug_count = 0
        # prepare_path("test_debug")
        for x in range(contrasted_img.shape[1]):
            for y in range(contrasted_img.shape[2]):

                if contrasted_img[0, x, y] < 0.5 and str(x)+" "+str(y) not in clustered_pixels:

                    # rand_color = [random.random(), random.random(), random.random()]
                    pixels_in_cluster, exterior_pixels_img = self.explore_cluster(offsets, contrasted_img, (x, y))

                    # marks pixels in cluster as previously visited, won't be revisited for cluster exploration
                    for pixel in pixels_in_cluster:
                        clustered_pixels[str(pixel[0])+" "+str(pixel[1])] = 1

                    # debug_img += (1.0 - exterior_pixels_img) * np.expand_dims(np.expand_dims(rand_color, axis=-1), axis=-1)

                    # finds points in trace of cluster exterior
                    pixels_in_cluster_contour, debug_img_b_component = self.trace_cluster(offsets, (x, y), exterior_pixels_img, debug_prefix=str(debug_count), min_dist_threshold=self.min_dist_threshold, close_trace_threshold=self.close_trace_threshold)
                    # debug_img_b += debug_img_b_component * np.expand_dims(np.expand_dims(rand_color, axis=-1), axis=-1)

                    # adds cluster outline to output list
                    current_pixels_in_cluster_contour = []
                    for i in range(len(pixels_in_cluster_contour)):
                        current_pixels_in_cluster_contour.append(pixels_in_cluster_contour[i])
                    clusters.append((current_pixels_in_cluster_contour, self.color))

                    debug_count += 1
                elif y >= 1 and contrasted_img[0, x, y] >= 0.5 and contrasted_img[0, x, y-1] < 0.5 and str(x)+" "+str(y) not in clustered_pixels:

                    # if on any given horiz line, we go from cluster black pixel to white, explore white region
                    pixels_in_cluster, exterior_pixels_img = self.explore_cluster(offsets, 1.0 - contrasted_img, (x, y))

                    # marks pixels in cluster as previously visited, won't be revisited for cluster exploration
                    includes_border = False
                    for pixel in pixels_in_cluster:
                        clustered_pixels[str(pixel[0])+" "+str(pixel[1])] = 1

                        if pixel[0] <= 0 or pixel[0] >= contrasted_img.shape[1]-1 or pixel[1] <= 0 or pixel[1] >= contrasted_img.shape[2]-1:
                            includes_border = True # if white region connects to border, keep memorized but ignore

                    # if white region does not connect to border, draw white region
                    if not includes_border:
                        pixels_in_cluster_contour, debug_img_b_component = self.trace_cluster(offsets, (x, y), exterior_pixels_img, debug_prefix=str(debug_count), min_dist_threshold=self.min_dist_threshold, close_trace_threshold=self.close_trace_threshold)

                        # adds cluster outline to output list
                        current_pixels_in_cluster_contour = []
                        for i in range(len(pixels_in_cluster_contour)):
                            current_pixels_in_cluster_contour.append(pixels_in_cluster_contour[i])
                        clusters.append((current_pixels_in_cluster_contour, "white"))

                        debug_count += 1

        # preview_np_image(debug_img, "debug.png")
        # preview_np_image(debug_img_b, "debug_b.png")

        return clusters

    def vectorize_to_path(self, img, path):
        header = "<?xml version='1.0' encoding='UTF-8' standalone='no'?>\n<!DOCTYPE svg PUBLIC '-//W3C//DTD SVG 1.1//EN' 'http://www.w3.org/Graphics/SVG/1.1/DTD/svg11.dtd'>\n"
        footer = "</g>\n</svg>"

        header += "<svg width='"+str(img.shape[2])+"' height='"+str(img.shape[1])+"' viewBox='0.0 0.0 "+str(img.shape[2])+" "+str(img.shape[1])+"' xmlns='http://www.w3.org/2000/svg' xmlns:xlink='http://www.w3.org/1999/xlink'>\n"
        header += "<rect fill='none' stroke='#000' x='0' y='0' width='"+str(img.shape[2])+"' height='"+str(img.shape[1])+"'/>\n"
        header += "<g>\n"

        # finds clusters (list of points in cluster trace) and draws each
        for cluster_obj in self.find_clusters(img):
            cluster = cluster_obj[0]
            cluster_color = cluster_obj[1]
            cluster_path = ""

            if len(cluster) >= 6:
                if len(cluster) > 0:
                    cluster_path += "M"+str(cluster[0][1])+" "+str(cluster[0][0])+" "
                if len(cluster) > 1:
                    for point in cluster[1:]:
                        cluster_path += "L"+str(point[1])+" "+str(point[0])+" "
                #     for i in range(1, len(cluster)):
                #         cluster_path += "S"+str(cluster[i][1])+" "+str(cluster[i][0])+", "+str(cluster[i-1][1])+" "+str(cluster[i-1][0])+" "
                    cluster_path += "Z"

            header += "<path d='"+cluster_path+"' fill='"+cluster_color+"' stroke-width='"+str(self.stroke_width)+"' stroke='"+self.color+"'/>\n"

        header = header + footer

        # file cleanup
        if os.path.exists(path):
            os.remove(path)

        f = open(path, 'w')
        f.write(header)
        f.close()

    def extract_dark_points(self, img, threshold=0.75):
        img = img > threshold
        return img

    def adjust_exposure(self, img, coeff=10.0):
        return 1./(1. + np.exp(-coeff * (img - 0.5)))

    def process_numpy_img(self, img):

        # rescales img if needed
        ratio = 1.0
        if img.shape[1] > img.shape[2]:
            ratio = self.target_size / img.shape[1]
        else:
            ratio = self.target_size / img.shape[2]
        # print(" * Rescaling img from "+str(img.shape[1:])+"...")
        img = rescale(img, scale_factor=ratio)
        # print(" ...to "+str(img.shape[1:]))
        
        # black & white-ifies img
        img = np.expand_dims(np.mean(img, axis=0), axis=0)
        
        # adjusts exposure & other processing
        img = self.adjust_exposure(img, coeff=self.coeff)
        img = self.extract_dark_points(img, threshold=self.threshold)

        # dilates pixels to prevent channel traversal issues
        img = 1.0 - img
        img = np.clip(img[:, :-1, :-1] + img[:, :-1, 1:] + img[:, 1:, :-1] + img[:, 1:, 1:], 0.0, 1.0)
        img = 1.0 - img

        # expands image with small white pixel border
        img = np.pad(img, ((0,0),(2,2),(2,2)), 'constant', constant_values=((1,1),(1,1),(1,1)))

        # expands sharp corners to prevent corner jumping
        corner_mask_a = np.logical_and(np.logical_and(np.logical_and(1.0 - img[:, :-1, :-1], 1.0 - img[:, 1:, 1:]), img[:, 1:, :-1]), img[:, :-1, 1:])
        corner_mask_b = np.logical_and(np.logical_and(np.logical_and(img[:, :-1, :-1], img[:, 1:, 1:]), 1.0 - img[:, 1:, :-1]), 1.0 - img[:, :-1, 1:])
        img[:, 1:, :-1] = img[:, 1:, :-1] * (1.0 - corner_mask_a)
        img[:, :-1, 1:] = img[:, :-1, 1:] * (1.0 - corner_mask_a)
        img[:, 1:, 1:] = img[:, 1:, 1:] * (1.0 - corner_mask_b)
        img[:, :-1, :-1] = img[:, :-1, :-1] * (1.0 - corner_mask_b)

        img = np.tile(img, [3, 1, 1])
        return img

    def process_img_at_path(self, path, output_path="test.svg", include_inputs=True):
        img = load_np_image(path)
        img = self.process_numpy_img(img)
        if include_inputs:
            preview_np_image(img, output_path.replace("_out", "").replace(".svg", "_in_processed.png"))

        self.vectorize_to_path(img, output_path)

    def process_batch(self, batch_path, output_path="test"):
        prepare_path(output_path)

        for filename in os.listdir(batch_path):
            if ".jpg" in filename.lower() or ".jpeg" in filename.lower() or ".png" in filename.lower():
                print(" * Processing "+filename+"...")
                self.process_img_at_path(os.path.join(batch_path, filename), os.path.join(output_path, filename.split(".")[0]+".svg"), include_inputs=False)



