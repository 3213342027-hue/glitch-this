#!/usr/bin/env python3
"""
Quick glitch transition - minimal frames for fast processing
"""
import os
import sys
import gc
import shutil
from pathlib import Path
from datetime import datetime
from PIL import Image, ImageSequence
import numpy as np

sys.path.insert(0, str(Path(__file__).parent / 'glitch_this'))
from glitch_this import ImageGlitcher


def generate_unique_filename(prefix='glitch_transition', ext='gif'):
    """Generate unique filename with timestamp"""
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    return f'{prefix}_{timestamp}.{ext}'


def quick_transition(img_paths, glitch_level=4, output=None):
    if len(img_paths) < 2:
        print('Need at least 2 images')
        return

    # Auto-generate unique filename if not specified
    if output is None:
        output = generate_unique_filename()

    # Minimal frames for 10+ seconds: 50 frames at 200ms = 10s
    hold_frames = 8
    glitch_frames = 15
    trans_frames = 7
    per_frame = 200  # ms

    total = (hold_frames + glitch_frames + trans_frames) * len(img_paths)
    print(f'Frames: {total}, Duration: ~{total*per_frame/1000:.0f}s')
    print(f'Output: {output}')

    glitcher = ImageGlitcher()
    result = []

    temp_dir = Path('qt_temp')
    if temp_dir.exists():
        for f in temp_dir.glob('*'):
            f.unlink()
    else:
        temp_dir.mkdir()

    try:
        for idx, path in enumerate(img_paths):
            img = Image.open(path)
            if img.format == 'GIF':
                img = next(ImageSequence.Iterator(img))
            img = img.convert('RGB' if img.mode not in ('RGB', 'RGBA') else img.mode)
            if idx == 0:
                size = img.size
            img = img.resize(size, Image.Resampling.LANCZOS)

            glitcher.pixel_tuple_len = len(img.getbands())
            glitcher.img_width, glitcher.img_height = img.size
            glitcher.img_mode = img.mode
            glitcher.inputarr = np.asarray(img)
            glitcher.outputarr = np.array(img)
            glitcher.seed = None

            # Clean frames
            for _ in range(hold_frames):
                result.append(img.copy())

            # Glitch up
            step = (glitch_level - 0.1) / glitch_frames
            level = 0.1
            for i in range(glitch_frames):
                g = glitcher._ImageGlitcher__get_glitched_img(level, True, True)
                p = temp_dir / f'{idx}_{i}.png'
                g.save(str(p), compress_level=3)
                with Image.open(str(p)) as tmp:
                    result.append(tmp.copy())
                level = min(level + step, glitch_level)

            # Transition
            for i in range(trans_frames):
                g = glitcher._ImageGlitcher__get_glitched_img(glitch_level, True, True)
                p = temp_dir / f'{idx}_t{i}.png'
                g.save(str(p), compress_level=3)
                with Image.open(str(p)) as tmp:
                    result.append(tmp.copy())

            gc.collect()

        print('Saving...')
        result[0].save(output, format='GIF', append_images=result[1:],
                      save_all=True, duration=per_frame, loop=0)
        print(f'Done: {output}')

    finally:
        gc.collect()
        try:
            for f in temp_dir.glob('*'):
                f.unlink()
            temp_dir.rmdir()
        except:
            pass

if __name__ == '__main__':
    # Default test with project images - will auto-generate unique filename
    quick_transition(['111.JPG', '222.JPG'], glitch_level=4)
