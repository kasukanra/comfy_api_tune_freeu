import os
import glob
import ffmpeg

from dotenv import load_dotenv
load_dotenv()

video_images_dir = os.getenv("VIDEO_IMAGES_DIR")

# Replace 'path_to_images' with the path to the folder containing your images.
path_to_images = video_images_dir 
output_video_path = f"{path_to_images}/output_video.mp4"

# Get all image files from the directory, sorted by creation date.
image_files = sorted(glob.glob(f"{path_to_images}/*"), key=os.path.getmtime)

# Create a temporary FFmpeg input file with the correct duration for each frame
with open('ffmpeg_input.txt', 'w') as file:
    for image_file in image_files:
        file.write(f"file '{image_file}'\n")
        file.write(f"duration {1/30}\n")
    
    # The last image won't have a set duration, as the duration of the last image is determined by the length of the video
    # This line must be within the 'with' block
    file.write(f"file '{image_files[-1]}'\n")

# Use ffmpeg to convert the images to a video
ffmpeg.input('ffmpeg_input.txt', format='concat', safe=0).output(output_video_path, vcodec='libx264', pix_fmt='yuv420p', r=30).run()

# Remove the temporary input file
os.remove('ffmpeg_input.txt')