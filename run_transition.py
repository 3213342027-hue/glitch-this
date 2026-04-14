#!/usr/bin/env python3
"""
Standalone script to create glitch transitions between images.
Usage: python run_transition.py [image1] [image2] [glitch_level] [output_file]
Example: python run_transition.py img1.jpg img2.jpg 5 output.gif
"""

import os
import sys
import gc
import shutil
from pathlib import Path
from decimal import Decimal, getcontext
from PIL import Image, ImageSequence
import numpy as np
import random

# Add glitch_this to path
sys.path.insert(0, str(Path(__file__).parent / 'glitch_this'))
from glitch_this import ImageGlitcher


def create_glitch_transition(img_paths, glitch_level=5, output_path='transition.gif'):
    """
    Create a glitch transition GIF between multiple images.
    Each image starts clean, glitches intensify, then transitions to next image.
    """
    if len(img_paths) < 2:
        raise ValueError('At least 2 images required')

    # Settings
    hold_frames = 15       # Clean display at start
    glitch_frames = 25     # Glitch intensifies
    transition_frames = 12 # High glitch transition
    per_frame_duration = 100  # ms per frame (~10fps)

    # Calculate total frames and duration
    total_frames_per_img = hold_frames + glitch_frames + transition_frames
    total_frames = total_frames_per_img * len(img_paths)
    estimated_duration = (total_frames * per_frame_duration) / 1000  # in seconds

    print(f'Creating glitch transition...')
    print(f'  Images: {len(img_paths)}')
    print(f'  Frames per image: {total_frames_per_img}')
    print(f'  Total frames: {total_frames}')
    print(f'  Estimated duration: {estimated_duration:.1f} seconds')

    glitcher = ImageGlitcher()
    glitched_imgs = []

    # Temp directory
    temp_dir = Path('temp_glitch')
    if temp_dir.exists():
        shutil.rmtree(temp_dir)
    temp_dir.mkdir()

    try:
        for img_idx, img_path in enumerate(img_paths):
            print(f'Processing image {img_idx + 1}/{len(img_paths)}: {img_path}')

            # Load and convert image
            img = Image.open(img_path)
            if img.format == 'GIF':
                img = next(ImageSequence.Iterator(img))

            if img.mode == 'P':
                img = img.convert('RGBA')
            elif img.mode not in ('RGB', 'RGBA'):
                img = img.convert('RGB')

            # Resize to first image's size
            if img_idx == 0:
                target_size = img.size
            img = img.resize(target_size, Image.Resampling.LANCZOS)

            # Set up glitcher state
            glitcher.pixel_tuple_len = len(img.getbands())
            glitcher.img_width, glitcher.img_height = img.size
            glitcher.img_mode = img.mode
            glitcher.inputarr = np.asarray(img)
            glitcher.outputarr = np.array(img)
            glitcher.seed = None

            # Phase 1: Hold clean image
            for _ in range(hold_frames):
                glitched_imgs.append(img.copy())

            # Phase 2: Glitch intensifies
            current_glitch = 0.1
            glitch_step = (glitch_level - 0.1) / glitch_frames
            for i in range(glitch_frames):
                glitched_img = glitcher._ImageGlitcher__get_glitched_img(
                    current_glitch, True, True)
                temp_path = temp_dir / f'frame_{img_idx}_{i}.png'
                glitched_img.save(str(temp_path), compress_level=3)
                with Image.open(str(temp_path)) as temp_img:
                    glitched_imgs.append(temp_img.copy())
                current_glitch = min(current_glitch + glitch_step, glitch_level)

            # Phase 3: High glitch transition
            for i in range(transition_frames):
                if i < transition_frames // 2:
                    g_level = glitch_level
                else:
                    g_level = glitch_level * 0.5
                glitched_img = glitcher._ImageGlitcher__get_glitched_img(
                    g_level, True, True)
                temp_path = temp_dir / f'trans_{img_idx}_{i}.png'
                glitched_img.save(str(temp_path), compress_level=3)
                with Image.open(str(temp_path)) as temp_img:
                    glitched_imgs.append(temp_img.copy())

            gc.collect()

        # Save GIF
        print(f'Saving GIF to {output_path}...')
        glitched_imgs[0].save(
            output_path,
            format='GIF',
            append_images=glitched_imgs[1:],
            save_all=True,
            duration=per_frame_duration,
            loop=0,
            compress_level=3
        )

        print(f'Done! Created {output_path}')
        print(f'Duration: {estimated_duration:.1f} seconds')

    finally:
        # Cleanup
        gc.collect()
        try:
            shutil.rmtree(temp_dir)
        except:
            pass


if __name__ == '__main__':
    # Default paths for testing
    if len(sys.argv) < 3:
        # Use default test images
        img1 = '111.JPG'
        img2 = '222.JPG'
        glitch_level = 5
        output = 'transition_output.gif'
    else:
        img1 = sys.argv[1]
        img2 = sys.argv[2]
        glitch_level = float(sys.argv[3]) if len(sys.argv) > 3 else 5
        output = sys.argv[4] if len(sys.argv) > 4 else 'transition_output.gif'

    create_glitch_transition([img1, img2], glitch_level, output)
