#!/usr/bin/env python3
import argparse
import json
import os
from datetime import datetime
from pathlib import Path
from time import time
from typing import Dict

from glitch_this import ImageGlitcher

version_filepath = ''


def generate_unique_filename(prefix='glitched', ext='gif'):
    """Generate unique filename with timestamp"""
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    return f'{prefix}_{timestamp}.{ext}'


def read_version() -> str:
    with open(version_filepath, 'r') as version_file:
        content = version_file.read()
    return content.strip()


def write_version(version: str):
    with open(version_filepath, 'w') as version_file:
        version_file.write(version + '\n')


def is_expired(filepath: str) -> bool:
    # Check if the file has been created 2 weeks prior
    file_creation = datetime.fromtimestamp(os.stat(filepath).st_mtime)
    now = datetime.now()
    return (now - file_creation).days > 14


def is_latest(version: str) -> bool:
    # Check pypi for the latest version number
    from urllib import request
    if os.path.isfile(version_filepath) and not is_expired(version_filepath):
        # If a version log already exists and it's not more than 14 days old
        latest_version = read_version()
    else:
        # Either version log does not exist or is outdated
        try:
            contents = request.urlopen(
                'https://pypi.org/pypi/glitch-this/json').read()
        except (OSError, ValueError):
            # Connection issue
            # Silenty return True, update check failed
            return True
        data = json.loads(contents)
        latest_version = data['info']['version']
        write_version(latest_version)

    print(f'Current version: {version} | Latest version: {latest_version}')
    return version == latest_version


def get_help(glitch_min: float, glitch_max: float) -> Dict:
    help_text = dict()
    help_text['path'] = 'Relative or Absolute string path to source image'
    help_text['level'] = f'Number between {glitch_min} and {glitch_max}, inclusive, representing amount of glitchiness'
    help_text['color'] = 'Include if you want to add color offset'
    help_text['scan'] = 'Include if you want to add scan lines effect\nDefaults to False'
    help_text['seed'] = 'Set a random seed for generating similar images across runs'
    help_text['gif'] = 'Include if you want output to be a GIF'
    help_text['frames'] = 'Number of frames to include in output GIF, default - 23'
    help_text['step'] = 'Glitch every step\'th frame of output GIF, default - 1 (every frame)'
    help_text['increment'] = 'Increment glitch_amount by given value after glitching every frame of output GIF'
    help_text['cycle'] = f'Include if glitch_amount should be cycled back to {glitch_min} or {glitch_max} if it over/underflows'
    help_text['duration'] = 'How long to display each frame (in centiseconds), default - 200'
    help_text['relative_duration'] = 'Multiply given value to input GIF\'s original duration and use that as duration'
    help_text['loop'] = 'How many times the glitched GIF should loop, default - 0 (infinite loop)'
    help_text['inputgif'] = 'Include if input image is GIF'
    help_text['force'] = 'Forcefully overwrite output file'
    help_text['out'] = 'Explcitly supply full/relative path to output file'
    help_text["output_frames"] = "Output individual frames of the glitched GIF as separate images"
    help_text['all_effects'] = 'Include to enable all glitch effects (color offset + scan lines)'
    help_text['seconds'] = 'Target total duration of output GIF in seconds (overrides frames count)'
    help_text['multi'] = 'Multiple images mode: space-separated list of image paths to combine into one GIF'
    help_text['frames_per'] = 'Number of frames per image in multi-image mode, default - 10'
    help_text['transition'] = 'Transition mode: glitch intensifies then jump to next image'
    help_text['fps'] = 'Duration per frame in centiseconds for transition mode, default - 80 (~12fps)'

    return help_text


def main():
    glitch_min, glitch_max = 0.1, 10.0
    current_version = ImageGlitcher.__version__
    help_text = get_help(glitch_min, glitch_max)
    # Add commandline arguments parser
    argparser = argparse.ArgumentParser(description='glitch_this: Glitchify images and GIFs, with highly customizable options!\n\n'
                                        '* Website: https://github.com/TotallyNotChase/glitch-this \n'
                                        f'* Version: {current_version}\n'
                                        '* Changelog: https://github.com/TotallyNotChase/glitch-this/blob/master/CHANGELOG.md',
                                        formatter_class=argparse.RawTextHelpFormatter)
    argparser.add_argument('--version', action='version',
                           version=f'glitch_this {current_version}')
    argparser.add_argument('src_img_path', metavar='Image_Path', type=str,
                           help=help_text['path'])
    argparser.add_argument('glitch_level', metavar='Glitch_Level', type=float,
                           help=help_text['level'])
    argparser.add_argument('-c', '--color', dest='color', action='store_true',
                           help=help_text['color'])
    argparser.add_argument('-s', '--scan', dest='scan_lines', action='store_true',
                           help=help_text['scan'])
    argparser.add_argument('-g', '--gif', dest='gif', action='store_true',
                           help=help_text['gif'])
    argparser.add_argument('-ig', '--inputgif', dest='input_gif', action='store_true',
                           help=help_text['inputgif'])
    argparser.add_argument('-f', '--force', dest='force', action='store_true',
                           help=help_text['force'])
    argparser.add_argument('-sd', '--seed', dest='seed', metavar='Seed', type=float, default=None,
                           help=help_text['seed'])
    argparser.add_argument('-fr', '--frames', dest='frames', metavar='Frames', type=int, default=23,
                           help=help_text['frames'])
    argparser.add_argument('-st', '--step', dest='step', metavar='Step', type=int, default=1,
                           help=help_text['step'])
    argparser.add_argument('-i', '--increment', dest='increment', metavar='Increment', type=float, default=0.0,
                           help=help_text['increment'])
    argparser.add_argument('-cy', '--cycle', dest='cycle', action='store_true',
                           help=help_text['cycle'])
    argparser.add_argument('-d', '--duration', dest='duration', metavar='Duration', type=int, default=200,
                           help=help_text['duration'])
    argparser.add_argument('-rd', '--relative_duration', dest='rel_duration', metavar='Relative_Duration', type=float,
                           help=help_text['relative_duration'])
    argparser.add_argument('-l', '--loop', dest='loop', metavar='Loop_Count', type=int, default=0,
                           help=help_text['loop'])
    argparser.add_argument('-o', '--outfile', dest='outfile', metavar='Outfile_path', type=str,
                           help=help_text['out'])
    argparser.add_argument("-of", "--output-frames", dest="output_frames",
                           action="store_true", help=help_text["output_frames"])
    argparser.add_argument("-ae", "--all-effects", dest="all_effects", action="store_true",
                           help=help_text['all_effects'])
    argparser.add_argument("-sec", "--seconds", dest="seconds", metavar="Seconds", type=float,
                           help=help_text['seconds'])
    argparser.add_argument("-m", "--multi", dest="multi", metavar="Image1 Image2 ...", type=str, nargs='+',
                           help=help_text['multi'])
    argparser.add_argument("-fp", "--frames-per", dest="frames_per", metavar="Frames_Per_Image", type=int, default=10,
                           help=help_text['frames_per'])
    argparser.add_argument("-t", "--transition", dest="transition", action="store_true",
                           help=help_text['transition'])
    args = argparser.parse_args()

    # Sanity check inputs
    if not args.duration > 0:
        raise ValueError('Duration must be greater than 0')
    if not args.loop >= 0:
        raise ValueError('Loop must be greater than or equal to 0')
    if not args.frames > 0:
        raise ValueError('Frames must be greater than 0')
    if not os.path.isfile(args.src_img_path):
        raise FileNotFoundError('No image found at given path')
    if args.output_frames and not args.gif:
        raise ValueError("Cannot output frames without GIF output enabled")
    if args.seconds is not None and args.seconds <= 0:
        raise ValueError('Seconds must be greater than 0')

    # Apply all effects if requested
    if args.all_effects:
        args.color = True
        args.scan_lines = True

    # Calculate frames from target duration (in centiseconds)
    # duration is in centiseconds, so: frames = seconds * 100 / duration_per_frame
    if args.seconds is not None and args.seconds > 0:
        # Use minimum frames of 5 or calculated value
        calculated_frames = int(args.seconds * 100 / args.duration)
        args.frames = max(5, calculated_frames)
        print(f'Target duration: {args.seconds}s -> Using {args.frames} frames at {args.duration}cs ({args.duration/100:.2f}s) per frame')

    # Set up full_path, for output saving location
    out_path, out_file = os.path.split(Path(args.src_img_path))
    out_filename, out_fileex = out_file.rsplit('.', 1)
    # Output file extension should be '.gif' if output file is going to be a gif
    if args.gif:
        out_fileex = "gif"
    elif args.output_frames:
        out_fileex = "png"
    else:
        out_fileex = out_fileex

    if args.outfile:
        # If output file path is already given
        # Overwrite the previous values
        out_path, out_file = os.path.split(Path(args.outfile))
        if out_path != "" and not os.path.exists(out_path):
            raise Exception("Given outfile path, " +
                            out_path + ", does not exist")
        # The extension in user provided outfile path is ignored
        out_filename = out_file.rsplit(".", 1)[0]
    else:
        # Auto-generate unique filename with timestamp
        out_filename = generate_unique_filename(
            prefix='glitched',
            ext=out_fileex
        )
        out_path = ""  # Save in current directory

    # Now create the full path
    full_path = os.path.join(out_path, f"{out_filename}.{out_fileex}")

    # If output type is frames and user specified output path, check for conflicts
    # (Unique filenames don't need this check)
    if args.outfile and args.output_frames:
        for i in range(args.frames):
            frame_path = os.path.join(
                out_path, (f"{out_filename}_{i}.{out_fileex}"))
            if os.path.exists(frame_path) and not args.force:
                raise Exception(
                    frame_path + " already exists\nCannot overwrite "
                    "existing file unless -f or --force is included\nProgram Aborted"
                )
    elif args.outfile and os.path.exists(full_path) and not args.force:
        # Only check when user explicitly specified output path
        raise Exception(
            full_path + " already exists\nCannot overwrite "
            "existing file unless -f or --force is included\nProgram Aborted"
        )

    # Actual work begins here
    glitcher = ImageGlitcher()
    global version_filepath
    version_filepath = os.path.join(glitcher.lib_path, 'version.info')
    t0 = time()

    # Multi-image mode (check transition first if both are set)
    if args.multi and args.transition:
        # Transition mode: glitch intensifies then jump to next image
        if len(args.multi) < 2:
            raise ValueError('Transition mode requires at least 2 images')

        # Optimized for faster processing: ~5.2s per image at 100cs/frame
        hold_frames = 10
        glitch_frames = 20
        transition_frames = 10
        per_frame_duration = 120  # centiseconds, ~8fps for smooth playback

        total_frames_per_img = hold_frames + glitch_frames + transition_frames
        estimated_seconds = (total_frames_per_img * len(args.multi) * per_frame_duration) / 100

        print(f'Transition mode: {len(args.multi)} images')
        print(f'Estimated duration: {estimated_seconds:.1f} seconds ({total_frames_per_img} frames per image)')

        glitch_img = glitcher.glitch_transition(
            args.multi,
            glitch_amount_start=0.1,
            glitch_amount_end=args.glitch_level,
            glitch_change=0.4,
            color_offset=True,
            scan_lines=True,
            frames_per_transition=glitch_frames,
            transition_frames=transition_frames,
            hold_frames=hold_frames
        )
        args.frames = len(glitch_img)
        args.gif = True
        args.duration = per_frame_duration
        t1 = time()
    elif args.multi:
        # Validate all image paths exist
        for img_path in args.multi:
            if not os.path.isfile(img_path):
                raise FileNotFoundError(f'No image found at given path: {img_path}')
        print(f'Multi-image mode: processing {len(args.multi)} images with {args.frames_per} frames each')
        glitch_img = glitcher.glitch_multi_images(
            args.multi,
            args.glitch_level,
            glitch_change=args.increment,
            cycle=args.cycle,
            scan_lines=args.scan_lines,
            color_offset=args.color,
            seed=args.seed,
            frames_per_image=args.frames_per
        )
        args.frames = len(glitch_img)
        args.gif = True
        t1 = time()
    elif not args.input_gif:
        # Get glitched image or GIF (from image)
        glitch_img = glitcher.glitch_image(args.src_img_path, args.glitch_level,
                                           glitch_change=args.increment,
                                           cycle=args.cycle,
                                           scan_lines=args.scan_lines,
                                           color_offset=args.color,
                                           seed=args.seed,
                                           gif=args.gif,
                                           frames=args.frames,
                                           step=args.step)
    else:
        # Get glitched image or GIF (from GIF)
        glitch_img, src_duration, args.frames = glitcher.glitch_gif(args.src_img_path, args.glitch_level,
                                                                    glitch_change=args.increment,
                                                                    cycle=args.cycle,
                                                                    scan_lines=args.scan_lines,
                                                                    color_offset=args.color,
                                                                    seed=args.seed,
                                                                    step=args.step)
        # Set args.gif to true if it isn't already in this case
        args.gif = True
        # Set args.duration to src_duration * relative duration, if one was given
        args.duration = args.duration if not args.rel_duration else int(
            args.rel_duration * src_duration)
    t1 = time()
    # End of glitching
    t2 = time()
    # Save the image
    if not args.gif:
        glitch_img.save(full_path, compress_level=3)
        t3 = time()
        print('Glitched Image saved in "{}"'.format(full_path))
    elif not args.output_frames:
        glitch_img[0].save(
            full_path,
            format="GIF",
            append_images=glitch_img[1:],
            save_all=True,
            duration=args.duration,
            loop=args.loop,
            compress_level=3,
        )
        t3 = time()
        print(
            f'Glitched GIF saved in "{full_path}"\nFrames = {args.frames}, Duration = {args.duration}, Loop = {args.loop}'
        )
    else:
        for i, frame in enumerate(glitch_img):
            frame_path = os.path.join(
                out_path, (f"{out_filename}_{i}.{out_fileex}"))
            frame.save(frame_path, compress_level=3)
        t3 = time()
        print(f'Glitched frames saved in "{out_filename}_*.png"')
    print(f"Time taken to glitch: {t1 - t0}")
    print(f"Time taken to save: {t3 - t2}")
    print(f"Total Time taken: {t3 - t0}")

    # Let the user know if new version is available
    if not is_latest(current_version):
        print('A new version of "glitch-this" is available. Please consider upgrading via `pip3 install --upgrade glitch-this`')


if __name__ == '__main__':
    main()
