import sys
from processors import *

if __name__ == "__main__":
    processor = PictureVectorizer(threshold=0.825, coeff=10.0, target_size=1400, stroke_width=0.5, color='#000', min_dist_threshold=3.2, close_trace_threshold=2.1)

    if "." in sys.argv[1]:
        processor.process_img_at_path(sys.argv[1], output_path='test_out.svg')
        preview_np_image(load_np_image(sys.argv[1]), "test_in.png")
    else:
        processor.process_batch(sys.argv[1], output_path="test")
