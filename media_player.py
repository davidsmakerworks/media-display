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

https://github.com/davidsmakerworks/media-display

TODO: General cleanup

TODO: Move announcement parsing to Announcement class

TODO: Better format to store announcements(?)

TODO: Make display routines non-blocking for faster response to quit command
"""


import datetime
import glob
import json
import os
import random
import subprocess
import time

from typing import Optional

import pygame

# Wildcard import used here based on standard pygame code style
from pygame.locals import *

from announcement import Announcement, AnnouncementLine
from button import Button


class MediaPlayer:
    """
    Initializes full-screen display and provides methods to show photos,
    videos, and announcements.
    """
    def __init__(
            self, surface: pygame.Surface, config: dict,
            surface_is_display: Optional[bool] = True) -> None:
        self._surface = surface
        self._config = config
        self._surface_is_display = surface_is_display

        # This will be used later for photo scaling
        self._width = surface.get_width()
        self._height = surface.get_height()

        self._date_fmt = config['date_fmt']

        self._photo_path = config['photos']['path']
        self._photo_files = [item.strip() for item in config['photos']['files']]
        self._photo_time = config['photos']['time']

        self._video_path = config['videos']['path']
        self._video_files = [item.strip() for item in config['videos']['files']]
        self._video_probability = config['videos']['probability']

        self._announcement_file = config['announcements']['file']
        self._announcement_font = config['announcements']['font']
        self._announcement_time = config['announcements']['time']
        self._announcement_probability = config['announcements']['probability']
        self._announcement_line_spacing = config['announcements']['spacing']

        if not pygame.get_init():
            pygame.init()

        if pygame.joystick.get_count():
            self._joystick = pygame.joystick.Joystick(0)
            self._joystick.init()

    def _show_image(self, filename: str) -> None:
        """
        Loads an image from the specified file and displays it on the screen.
        
        Image is scaled to fill as much of screen as possible.
        """
        img = pygame.image.load(filename)

        img_height = img.get_height()
        img_width = img.get_width()

        # If the image isn't already the same size as the screen,
        # it needs to be scaled
        if (img_width != self._width
                or img_height != self._height):
            # Determine what the height will be if we expand the image to
            # fill the whole width
            scaled_height = int(
                (float(self._width) / img_width) * img_height)

            # If the scaled image is going to be taller than the screen,
            # then limit the maximum height and scale the width instead
            if scaled_height > self.screen_height:
                scaled_height = self.screen_height
                scaled_width = int(
                    (float(self._height) / img_height) * img_width)
            else:
                scaled_width = self._width

            img_bitsize = img.get_bitsize()

            # transform.smoothscale() can only be used for 24-bit and
            # 32-bit images. If this is not a 24-bit or 32-bit image,
            # use transform.scale() instead which will be ugly
            # but at least will work
            if img_bitsize in [24, 32]:
                img = pygame.transform.smoothscale(
                    img, (scaled_width, scaled_height))
            else:
                img = pygame.transform.scale(
                    img, (scaled_width, scaled_height))

            # Determine where to place the image so it will appear
            # centered on the screen
            display_x = (self._width - scaled_width) / 2
            display_y = (self._height - scaled_height) / 2
        else:
            # No scaling was applied, so image is already full-screen
            display_x = 0
            display_y = 0

        # Blank screen before showing photo in case it
        # doesn't fill the whole screen
        self._surface.fill(pygame.Color('black'))
        self._surface.blit(img, (display_x, display_y))

        if self._surface_is_display:
            pygame.display.update()

    def _show_video(self, filename: str) -> None:
        """
        Play a video from the specified file using the external omxplayer
        utility.
        """
        # Videos will not be scaled - this needs to be done during transcoding
        # Blank screen before showing video in case it doesn't fill the whole
        # screen
        self._surface.fill(pygame.Color('black'))

        if self._surface_is_display:
            pygame.display.update()

        subprocess.call(
                ['/usr/bin/omxplayer', '-o', 'hdmi', filename], shell=False)
        # This might not be necessary, but it's there in case any stray copies
        # of omxplayer.bin are somehow left running
        subprocess.call(['/usr/bin/killall', 'omxplayer.bin'], shell=False)

    def _show_announcement(
            self, announcement: Announcement,
            text_font: str, line_spacing: int) -> None:
        """
        Show a text announcement on the screen.

        TODO: Modify to use a Font object instead

        Parameters:
        announcement -- an instance of the Announcement class
        text_font -- name of the font file to use for rendering
        line_spacing -- space in pixels to place between each line
        """

        # Pre-calculate total height of message for centering
        total_height = 0

        for line in announcement.lines:
            text = line.text
            size = line.size

            # Only count lines with text to be rendered
            if text:
                fnt = pygame.font.Font(text_font, size)

                # Calculate size of text to be rendered
                (line_width, line_height) = fnt.size(text)

                total_height = total_height + line_height + line_spacing
            else:
                # Directly add up "space" elements without using Font object
                total_height = total_height + size

        # Start at proper position to center whole message on screen
        current_y = (self._height - total_height) / 2
        if current_y < 0:
            current_y = 0

        # Blank screen
        self._surface.fill(pygame.Color('black'))

        if self._surface_is_display:
            pygame.display.update()

        # Render each line of text
        for line in announcement.lines:
            text = line.text
            size = line.size
            color = line.color
            center = line.center

            # Only render text if there is text to be rendered
            if text:
                # Create Font object of given size
                fnt = pygame.font.Font(text_font, size)

                (line_width, line_height) = fnt.size(text)

                if center:
                    disp_x = (self._width - line_width) / 2
                else:
                    # TODO: allow for arbitrary X position to be specified in
                    # announcements file
                    disp_x = 0 

                disp_y = current_y

                # Render line of text to a surface and blit it to the
                # screen buffer
                line_surface = fnt.render(text, True, color)
                self._surface.blit(line_surface, (disp_x, disp_y))

                # Allow for spacing between each line
                current_y = current_y + line_height + line_spacing
            else:
                # If line is blank (a "space" element in the XML file) then
                # just advance the position on the screen
                current_y = current_y + size

        # If the class's surface is a pygame display, update display after
        # all lines have been rendered and blitted
        if self._surface_is_display:
            pygame.display.update()
    
    def _check_for_quit(self) -> bool:
        """Temporary workaround until main loop is made non-blocking."""
        for event in pygame.event.get():
            if event.type == pygame.KEYDOWN:
                if event.key == K_ESCAPE:
                    return True
            elif event.type == pygame.JOYBUTTONDOWN:
                if event.button == Button.BTN_START:
                    return True

        return False

    def run(self) -> bool:
        while True:
            # Create 2 empty lists for photo and video filenames
            photos = []
            videos = []

            # Create empty list for annoucement data
            announcements = []

            # Get current datetime
            current_date = datetime.datetime.today().date()

            with open(self._announcement_file, 'r') as f:
                announcement_data = json.load(f)

            # Iterate through all root elements
            for item in announcement_data:
                # Get start date and end date for announcement
                ann_start_date = datetime.datetime.strptime(
                            item['start_date'], self._date_fmt).date()
                ann_end_date = datetime.datetime.strptime(
                            item['end_date'], self._date_fmt).date()

                # Only show announcements that are within the
                # specified date range
                if (ann_start_date <= current_date 
                        and ann_end_date >= current_date):
                    ann_temp = Announcement(ann_start_date, ann_end_date)
                    # Iterate through all "line" elements
                    for line in item['lines']:
                        # "hspace" elements represent blank vertical spaces
                        if 'hspace' in line:
                            ann_temp.lines.append(
                                AnnouncementLine(
                                    "", line['hspace'], (0, 0, 0), False))
                        else:
                            # Append each line to the list that represents
                            # the lines of the announcement
                            ann_temp.lines.append(
                                AnnouncementLine(
                                    line['text'], line['size'],
                                    pygame.Color(line['color']),
                                    line['center']))

                    # Append each complete announcement to the master list
                    # of announcements
                    announcements.append(ann_temp)

            # Find all photos in designated folder based on the
            # list of extensions. Allow for both uppercase and lowercase
            # extensions, but not mixed case
            for wildcard in self._photo_files:
                photos.extend(
                    glob.glob(os.path.join(self._photo_path, wildcard.upper())))
                photos.extend(
                    glob.glob(os.path.join(self._photo_path, wildcard.lower())))

            # Find all videos in designated folder based on the
            # list of extensions. Allow for both uppercase and lowercase
            # extensions, but not mixed case
            for wildcard in self._video_files:
                videos.extend(
                    glob.glob(os.path.join(self._video_path, wildcard.upper())))
                videos.extend(
                    glob.glob(os.path.join(self._video_path, wildcard.lower())))

            # Display photos in alphabetical order by filename
            photos.sort()

            # Loop through all photos and insert videos at random. Note that the
            # contents of the folder will be reparsed each time all of the photos
            # are displayed, so this provides an opportunity to add/change the
            # contents without restarting the script.
            for photo in photos:
                # Check to see if user has requested to quit
                if self._check_for_quit():
                    return False

                self._show_image(photo)
                time.sleep(self._photo_time)

                # Check to see if user has requested to quit
                if self._check_for_quit():
                    return False

                # Display announcements based on the specified probability.
                # Check to be sure we have any announcements to display before
                # we try to display one.
                if (random.random() <= self._announcement_probability
                        and announcements):
                    self._show_announcement(
                        random.choice(announcements),
                        self._announcement_font,
                        self._announcement_line_spacing)
                    time.sleep(self._announcement_time)

                # Check to see if user has requested to quit
                if self._check_for_quit():
                    return False

                # Play videos based on the specified probability.
                # Check to be sure we have any videos to play before we try
                # to play one.
                if (random.random() <= self._video_probability
                        and videos):
                    self._show_video(random.choice(videos))
            
            return True


if __name__ == '__main__':
    print('This file should not be run directly. Run main.py instead.')