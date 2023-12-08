import os
import json
import random
from urllib import request
import datetime
from PIL import Image, ImageDraw, ImageFont
import time

from dotenv import load_dotenv
load_dotenv()

# Timeout settings
directory_creation_timeout = 300  # Timeout for directory creation in seconds
image_generation_timeout = 30000    # Timeout for image generation in seconds

fixed_seed = 133772
random.seed(fixed_seed)

max_seed_value = 184467440737095520
random_seed = random.randint(1, max_seed_value)

# Save the random_seed value to a text file
with open("random_seed.txt", "w") as file:
    file.write(str(random_seed))

api_workflow_dir = os.getenv("API_WORKFLOW_DIR")
api_workflow_file = os.getenv("API_WORKFLOW_FILE")
api_endpoint = os.getenv("API_ENDPOINT")
image_output_dir = os.getenv("IMAGE_OUTPUT_DIR")
font_ttf_path = os.getenv("FONT_TTF_PATH")
bold_font_ttf_path = os.getenv("BOLD_FONT_TTF_PATH")

# String interpolation on api_endpoint
api_endpoint = f"{api_endpoint}/prompt"

workflow_file_path = os.path.join(api_workflow_dir, api_workflow_file)

# Workflow is a global variable
workflow = json.load(open(workflow_file_path))

# Nodes
freeU = workflow["51"]
ksampler = workflow["41"]
save_image = workflow["63"]
random_number = workflow["34"]

# Format the current date and time
current_datetime = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
# test_dir = "2023-11-27_15-55-52"
# current_datetime = test_dir
relative_output_path = current_datetime
absolute_output_path = os.path.join(image_output_dir, current_datetime)

# Define the filename for the output grid image
output_grid_filename = os.path.join(absolute_output_path, "output_image_grid.png")

def process_values(b1, b2, s1, s2, freeU, ksampler, save_image, random_seed):
    b1_range = b1 if isinstance(b1, list) else [b1]
    b2_range = b2 if isinstance(b2, list) else [b2]
    s1_range = s1 if isinstance(s1, list) else [s1]
    s2_range = s2 if isinstance(s2, list) else [s2]

    for b1_val in b1_range:
        for b2_val in b2_range:
            for s1_val in s1_range:
                for s2_val in s2_range:
                    freeU["inputs"]["b1"] = b1_val
                    freeU["inputs"]["b2"] = b2_val
                    freeU["inputs"]["s1"] = s1_val
                    freeU["inputs"]["s2"] = s2_val

                    # can't use this because it doesn't exist!
                    # ksampler["inputs"]["seed"] = random_seed

                    # instead of changing noise_seed, i will change the random number node
                    random_number["inputs"]["seed"] = random_seed
                    # instead, change the seed inside random
                    filename_prefix = f"{b1_val:.2f}_{b2_val:.2f}_{s1_val:.2f}_{s2_val:.2f}"

                    save_image["inputs"]["output_path"] = relative_output_path
                    save_image["inputs"]["filename_prefix"] = filename_prefix

                    queue_prompt(workflow)

def queue_prompt(workflow):
    p = {"prompt": workflow}
    data = json.dumps(p).encode('utf-8')
    req =  request.Request(api_endpoint, data=data)
    request.urlopen(req) 

def create_image_grid(x_range, y_range, image_folder, output_filename, static_values):
    first_image_size = None
    is_b1_b2_dynamic = static_values and 'b1' not in static_values and 'b2' not in static_values

    print("Searching for the first valid image to determine size...")
    for y_val in y_range:
        for x_val in x_range:
            if is_b1_b2_dynamic:
                filename = os.path.join(
                    image_folder, f"{x_val:.2f}_{y_val:.2f}_{static_values['s1']:.2f}_{static_values['s2']:.2f}_0001.png"
                )
            else:
                filename = os.path.join(
                    image_folder, f"{static_values['b1']:.2f}_{static_values['b2']:.2f}_{x_val:.2f}_{y_val:.2f}_0001.png"
                )
            if os.path.exists(filename):
                try:
                    first_image = Image.open(filename)
                    first_image_size = first_image.size
                    print(f"Found first valid image: {filename} with size {first_image_size}")
                    break
                except IOError:
                    print(f"Cannot open image: {filename}")
        if first_image_size:
            break

    if not first_image_size:
        print("No valid images found to determine the size.")
        return

    # Increase margin space for axis labels and title
    axis_label_space = max(first_image_size[0] // 6, 150)
    title_space = max(first_image_size[1] // 8, 100)

    # Adjust total_height to include space for top x-axis labels
    total_width = first_image_size[0] * len(x_range) + axis_label_space * 2
    total_height = first_image_size[1] * len(y_range) + title_space * 2 + axis_label_space

    grid_image = Image.new('RGB', (total_width, total_height), 'white')

    # Define path to your .ttf file and set dynamic font size
    font_size = max(first_image_size[1] // 25, 15)
    draw = ImageDraw.Draw(grid_image)
    font = ImageFont.truetype(font_ttf_path, font_size)

    # Title with static values
    if is_b1_b2_dynamic:
        x_title = f"s1: {static_values['s1']:.2f}, s2: {static_values['s2']:.2f} (dynamic b1, b2)"
    else:
        x_title = f"b1: {static_values['b1']:.2f}, b2: {static_values['b2']:.2f} (dynamic s1, s2)"

    # Bold font for the title
    bold_font_size = max(first_image_size[1] // 25, 15)
    bold_font = ImageFont.truetype(bold_font_ttf_path, bold_font_size)

    title_x = total_width // 2 - draw.textlength(x_title, font=bold_font) // 2
    title_y = 10  # Positioning title further up
    draw.text((title_x, title_y), x_title, fill="black", font=bold_font)

    # Add centered ticks on x axes (top and bottom)
    for i, x_val in enumerate(x_range):
        x_label = f"b1: {x_val:.2f}" if is_b1_b2_dynamic else f"s1: {x_val:.2f}"
        x_label_x = axis_label_space + (i + 0.5) * first_image_size[0] - draw.textlength(x_label, font=font) // 2
        x_label_y_bottom = total_height - axis_label_space // 2
        x_label_y_top = title_space + axis_label_space // 2  # Adjusted position for top x-axis labels
        draw.text((x_label_x, x_label_y_bottom), x_label, fill="black", font=font)
        draw.text((x_label_x, x_label_y_top), x_label, fill="black", font=font)

    # Add y-axis labels
    for j, y_val in enumerate(y_range):
        y_label = f"b2: {y_val:.2f}" if is_b1_b2_dynamic else f"s2: {y_val:.2f}"
        y_label_x = 10  # Adjusted x position for y labels
        y_label_y = title_space + axis_label_space + (j + 0.5) * first_image_size[1] - draw.textlength(y_label, font=font) // 2
        draw.text((y_label_x, y_label_y), y_label, fill="black", font=font)

    # Paste images into grid
    for i, y_val in enumerate(y_range):
        for j, x_val in enumerate(x_range):
            filename = os.path.join(
                image_folder, 
                f"{x_val:.2f}_{y_val:.2f}_{static_values['s1']:.2f}_{static_values['s2']:.2f}_0001.png" if is_b1_b2_dynamic else
                f"{static_values['b1']:.2f}_{static_values['b2']:.2f}_{x_val:.2f}_{y_val:.2f}_0001.png"
            )
            if os.path.exists(filename):
                try:
                    img = Image.open(filename)
                    grid_image.paste(img, (j * first_image_size[0] + axis_label_space, i * first_image_size[1] + title_space + axis_label_space))  # Adjusted y position for images
                except IOError as e:
                    print(f"Cannot open image: {filename}")
                    print(f"Error: {e}")

    grid_image.save(output_filename)
    print(f"Grid image saved to: {output_filename}")

def wait_for_directory_creation(directory, timeout):
    print(f"Waiting for directory {directory} to be created...")
    start_time = time.time()
    while time.time() - start_time < timeout:
        if os.path.exists(directory):
            print(f"Directory {directory} found.")
            return True
        time.sleep(5)  # Check every 5 seconds
    print(f"Timeout waiting for directory {directory} to be created.")
    return False

def wait_for_images(image_folder, expected_count, timeout):
    print("Waiting for images to be generated...")
    start_time = time.time()
    while time.time() - start_time < timeout:
        if os.path.exists(image_folder):
            image_files = [f for f in os.listdir(image_folder) if f.endswith('.png')]
            if len(image_files) >= expected_count:
                print(f"Found all {expected_count} images.")
                return True
        time.sleep(5)  # Check every 5 seconds
    print("Timeout waiting for images to be generated.")
    return False

def generate_incremental_values(start, end, step):
    values = []
    value = start
    while value < end:  # Continue until the value is just less than 'end'
        values.append(round(value, 2))  # Round to 2 decimal places
        value += step
    values.append(round(end, 2))  # Append the 'end' value, rounded to 2 decimal places
    return values

def run_image_creation_process(x_range, y_range, output_path, grid_filename, static_values):
    expected_image_count = len(x_range) * len(y_range)

    if wait_for_directory_creation(output_path, directory_creation_timeout):
        if wait_for_images(output_path, expected_image_count, image_generation_timeout):
            create_image_grid(x_range, y_range, output_path, grid_filename, static_values)
        else:
            print("Failed to generate all images in time.")
    else:
        print("Output directory was not created.")

# Static values for b1 and b2
b1_static = 1.5
b2_static = 1.3

# Static values for s1 and s2
s1_static = 1.1
s2_static = 0.2

# s1_static = 1.0
# s2_static = 1.0

# b_range pass 1
b1_range = generate_incremental_values(0.4, 1.7, 0.1)
b2_range = generate_incremental_values(0.4, 1.7, 0.1)

# b_range pass 2
# b1_range = generate_incremental_values(1.3, 1.7, 0.05)
# b2_range = generate_incremental_values(1.1, 1.7, 0.05)

# s_range pass 1
s1_range = generate_incremental_values(0.0, 1.6, 0.1)
s2_range = generate_incremental_values(0.0, 1.6, 0.1)

if __name__ == "__main__":
    # Determine dynamic values and call the image creation process accordingly
    # dynamic_values_type = 's'  # Set to 'b' if b1 and b2 are ranges
    # dynamic_values_type = "b"
    dynamic_values_type = "s"

    if dynamic_values_type == 's':
        # First, generate images with dynamic s1, s2 and static b1, b2 values
        process_values(b1_static, b2_static, s1_range, s2_range, freeU, ksampler, save_image, random_seed)
        
        # Then, create an image grid from the generated images
        static_values = {'b1': b1_static, 'b2': b2_static}
        run_image_creation_process(s1_range, s2_range, absolute_output_path, output_grid_filename, static_values)
    
    elif dynamic_values_type == 'b':
        # First, generate images with dynamic b1, b2 and static s1, s2 values
        process_values(b1_range, b2_range, s1_static, s2_static, freeU, ksampler, save_image, random_seed)
        
        # Then, create an image grid from the generated images
        static_values = {'s1': s1_static, 's2': s2_static}
        run_image_creation_process(b1_range, b2_range, absolute_output_path, output_grid_filename, static_values)