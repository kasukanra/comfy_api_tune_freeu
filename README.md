# ComfyUI API example

This repository is the companion code for the video here:

[![Kasucast #21 - Improving Stable Diffusion images with FreeU (SDXL, LCM, Turbo ) and ComfyUI API](https://img.youtube.com/vi/WwsJ_QIgsG8/maxresdefault.jpg
)](https://youtu.be/WwsJ_QIgsG8)

## Overview
The objective of this project is to perform grid search to determine the optimal parameters for the FreeU node in ComfyUI.

The entrypoint for the code is `finetune_freeu.py`.

The corresponding workflows are in the `workflows` directory.

A sample `video_creation.py` file is enclosed to stitch images from the output folders into a short video.