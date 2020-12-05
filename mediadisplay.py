# MIT License

# Copyright (c) 2020 David Rice

# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:

# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.

# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

"""
Media Player and Announcement Board

Displays pictures, videos, and announcements on a television or
computer monitor

Designed to run on Raspberry Pi 3 or Raspberry Pi 4

Requires PyGame with Python 3 (tested on Python 3.7.3)

github.com/davidsmakerworks/media-display

TODO: General cleanup

TODO: Migrate to run inside windowing system for future integration with
other projects

TODO: Research native video playback without using omxplayer

TODO: Migrate configuration and announcements to use JSON files
"""

import os
import sys
import pygame
import time as tm # Avoid conflict with datetime.time class
import subprocess
import random
import glob
import xml.etree.ElementTree as ET
import configparser

from datetime import *


# Some useful constants
CONFIG_FILE = '/home/falcons/mediadisplay.cfg'
DATE_FMT = '%Y-%m-%d'


class MediaPlayer:
    """
    Initializes frame buffer and provides methods to show photos,
    videos, and announcements.
    """
    def __init__(self):
        # Assume we're using fbcon on Raspberry Pi
        os.putenv('SDL_VIDEODRIVER', 'fbcon')

        try:
            pygame.display.init()
            pygame.font.init()
        except:
            print('Unable to initialize frame buffer!')
            sys.exit()

        # This will be used later for photo scaling
        self.screen_height = pygame.display.Info().current_h
        self.screen_width = pygame.display.Info().current_w

        self.screen = pygame.display.set_mode(
                (self.screen_width, self.screen_height),
                flags=pygame.FULLSCREEN)
        self.screen.fill([0, 0, 0])

        # This hides the mouse pointer which is unwanted in this application
        pygame.mouse.set_visible(False)
        pygame.display.update()


    def show_image(self, filename):
        """
        Loads an image from the specified file and displays it on the screen.
        
        Image is scaled to fill as much of screen as possible.
        """
        img = pygame.image.load(filename)

        img_height = img.get_height()
        img_width = img.get_width()

        # If the image isn't already the same size as the screen,
        # it needs to be scaled
        if (img_height != self.screen_height
            or img_width != self.screen_width):
            # Determine what the height will be if we expand the image to
            # fill the whole width
            scaled_height = int(
                    (float(self.screen_width) / img_width) * img_height)

            # If the scaled image is going to be taller than the screen,
            # then limit the maximum height and scale the width instead
            if scaled_height > self.screen_height:
                scaled_height = self.screen_height
                scaled_width = int(
                        (float(self.screen_height) / img_height) * img_width)
            else:
                scaled_width = self.screen_width

            img_bitsize = img.get_bitsize()

            # transform.smoothscale() can only be used for 24-bit and
            # 32-bit images. If this is not a 24-bit or 32-bit image,
            # use transform.scale() instead which will be ugly
            # but at least will work
            if img_bitsize == 24 or img_bitsize == 32:
                img = pygame.transform.smoothscale(
                        img, [scaled_width, scaled_height])
            else:
                img = pygame.transform.scale(
                        img, [scaled_width, scaled_height])

            # Determine where to place the image so it will appear
            # centered on the screen
            display_x = (self.screen_width - scaled_width) / 2
            display_y = (self.screen_height - scaled_height) / 2
        else:
            # No scaling was applied, so image is already full-screen
            display_x = 0
            display_y = 0

        # Blank screen before showing photo in case it
        # doesn't fill the whole screen
        self.screen.fill([0, 0, 0])
        self.screen.blit(img, [display_x, display_y])
        pygame.display.update()


    def show_video(self, filename):
        """
        Play a video from the specified file using the external omxplayer
        utility.
        """
        # Videos will not be scaled - this needs to be done during transcoding
        # Blank screen before showing video in case it doesn't fill the whole
        # screen
        self.screen.fill([0, 0, 0])
        pygame.display.update()
        subprocess.call(
                ['/usr/bin/omxplayer', '-o', 'hdmi', filename], shell=False)
        # This might not be necessary, but it's there in case any stray copies
        # of omxplayer.bin are somehow left running
        subprocess.call(['/usr/bin/killall', 'omxplayer.bin'], shell=False)


    def show_announcement(self, announcement, text_font, line_spacing):
        """
        Show a text announcement on the screen.

        Parameters:
        announcement -- a list of display lines in the format:
                        ['text', size, (R,G,B), center]
        text_font -- name of the font file to use for rendering
        line_spacing -- space in pixels to place between each line
        """

        # Pre-calculate total height of message for centering
        total_height = 0

        for line in announcement:
            text = line[0]
            size = line[1]

            # Only count lines with text to be rendered
            if text.strip:
                fnt = pygame.font.Font(text_font, size)

                # Calculate size of text to be rendered
                (line_width, line_height) = fnt.size(text)

                total_height = total_height + line_height + line_spacing
            else:
                # Directly add up "space" elements without using Font object
                total_height = total_height + size

        # Start at proper position to center whole message on screen
        current_y = (self.screen_height - total_height) / 2
        if current_y < 0:
            current_y = 0

        # Blank screen
        self.screen.fill([0, 0, 0])
        pygame.display.update()

        # Render each line of text
        for line in announcement:
            text = line[0]
            size = line[1]
            color = line[2]
            center = line[3]

            # Only render text if there is text to be rendered
            if text.strip() != "":
                # Create Font object of given size
                fnt = pygame.font.Font(text_font, size)

                (line_width, line_height) = fnt.size(text)

                if center:
                    disp_x = (self.screen_width - line_width) / 2
                else:
                    # TODO: allow for arbitrary X position to be specified in
                    # XML file
                    disp_x = 0 

                disp_y = current_y

                # Render line of text to a surface and blit it to the
                # screen buffer
                line_surface = fnt.render(text, True, color)
                self.screen.blit(line_surface, (disp_x, disp_y))

                # Allow for spacing between each line
                current_y = current_y + line_height + line_spacing
            else:
                # If line is blank (a "space" element in the XML file) then
                # just advance the position on the screen
                current_y = current_y + size

        # Update display after all lines have been rendered and blitted
        pygame.display.update()


def hex_to_rgb(value):
    """
    Utility function to translate hex color values into tuples
    From http://stackoverflow.com/a/214657/3787376
    """
    value = value.lstrip('#')
    lv = len(value)
    return tuple(int(value[i:i + lv // 3], 16) for i in range(0, lv, lv // 3))


def fixpath(path_name):
    """
    Utility function to ensure path names are in the format needed for use
    with glob
    """
    if not path_name.endswith('/'):
        path_name = path_name + '/'

    return path_name


def main():
    # Parse config information
    config = configparser.ConfigParser()
    config.read_file(open(CONFIG_FILE))

    PHOTO_PATH = config.get('photos', 'path')
    PHOTO_FILES = [item.strip()
            for item in config.get('photos', 'files').split(',')]
    PHOTO_TIME = config.getint('photos', 'time')

    VIDEO_PATH = config.get('videos', 'path')
    VIDEO_FILES = [item.strip()
            for item in config.get('videos', 'files').split(',')]
    VIDEO_PROBABILITY = config.getfloat('videos', 'probability')

    ANNOUNCEMENT_FILE = config.get('announcements', 'file')
    ANNOUNCEMENT_FONT = config.get('announcements', 'font')
    ANNOUNCEMENT_TIME = config.getint('announcements', 'time')
    ANNOUNCEMENT_PROBABILITY = config.getfloat('announcements', 'probability')
    ANNOUNCEMENT_LINE_SPACING = config.getint('announcements', 'spacing')

    # Make sure paths end with slashes
    PHOTO_PATH = fixpath(PHOTO_PATH)
    VIDEO_PATH = fixpath(VIDEO_PATH)

    # Create an instance of the MediaPlayer class
    player = MediaPlayer()

    # Run forever
    while True:
        # Create 2 empty lists for photo and video filenames
        photos = []
        videos = []

        # Create empty list for annoucement data
        announcements = []

        # Get current datetime
        current_date = datetime.today().date()

        # TODO: Wrap this in a try/catch block
        ann_tree = ET.parse(ANNOUNCEMENT_FILE)
        ann_root = ann_tree.getroot()

        # Iterate through all "announcement" elements
        for item in ann_root.iter('announcement'):
            # Get start date and end date for announcement
            ann_start_date = datetime.strptime(
                        item.get('startdate'), DATE_FMT).date()
            ann_end_date = datetime.strptime(
                        item.get('enddate'), DATE_FMT).date()

            # Only show announcements that are within the specified date range
            if ann_start_date <= current_date and ann_end_date >= current_date:
                # Each announcement is a separate list of lines
                ann_temp = []

                # Iterate through all "line" elements
                for line in item.iter('line'):
                    # Elements with no text represent blank vertical spaces
                    if not line.text:
                        ann_temp.append(
                                ["", int(line.get('size')), (0, 0, 0), False])
                    else:
                        # Check to see if line should be centered
                        if int(line.get('center')) == 1:
                            center = True
                        else:
                            center = False

                        # Append each line to the list that represents
                        # the announcement
                        ann_temp.append(
                                [line.text, int(line.get('size')),
                                hex_to_rgb(line.get('color')), center])

                # Append each complete announcement to the master list
                # of announcements
                announcements.append(ann_temp)

        # Find all photos in designated folder based on the list of extensions.
        # Allow for both uppercase and lowercase extensions, but not mixed case
        for wildcard in PHOTO_FILES:
            photos = photos + glob.glob(PHOTO_PATH + wildcard.upper())
            photos = photos + glob.glob(PHOTO_PATH + wildcard.lower())

        # Find all videos in designated folder based on the list of extensions.
        # Allow for both uppercase and lowercase extensions, but not mixed case
        for wildcard in VIDEO_FILES:
            videos = videos + glob.glob(VIDEO_PATH + wildcard.upper())
            videos = videos + glob.glob(VIDEO_PATH + wildcard.lower())

        current_photo = 0

        # Display photos in alphabetical order by filename
        photos.sort()

        # Loop through all photos and insert videos at random. Note that the
        # contents of the folder will be reparsed each time all of the photos
        # are displayed, so this provides an opportunity to add/change the
        # contents without restarting the script.
        while current_photo < len(photos):
            player.show_image(photos[current_photo])
            tm.sleep(PHOTO_TIME)
            current_photo = current_photo + 1

            # Display announcements based on the specified probability.
            # Check to be sure we have any announcements to display before
            # we try to display one.
            if random.random() <= ANNOUNCEMENT_PROBABILITY and announcements:
                player.show_announcement(
                    random.choice(announcements),
                    ANNOUNCEMENT_FONT, ANNOUNCEMENT_LINE_SPACING)
                tm.sleep(ANNOUNCEMENT_TIME)

            # Play videos based on the specified probability.
            # Check to be sure we have any videos to play before we try
            # to play one.
            if random.random() <= VIDEO_PROBABILITY and videos:
                player.show_video(random.choice(videos))

if __name__ == '__main__':
    main()