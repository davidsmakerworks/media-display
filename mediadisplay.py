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

TODO: Implement graceful shutdown

"""

import datetime
import glob
import json
import os
import random
import subprocess
import sys
import time

import pygame


class AnnouncementLine:
    """
    Class representing one line of an announcement after it has
    been parsed from JSON file

    Properties:
    text -- text of the line, or None if it is a blank line
    size -- size of text or height of the blank line
    color -- text color as a tuple of (red, green, blue)
    center -- determines if line should be centered on the screen
    """
    def __init__(self, text=None, size=0, color=None, center=False):
        self.text = text
        self.size = size
        self.color = color
        self.center = center


class Announcement:
    """
    Class representing an announcement after it has been parsed from the
    JSON file.

    Properties:
    start_date -- earliest date to show announcement
    end_date -- latest date to show announcement
    lines -- list of AnnouncementLine objects representing the individual
        lines of the announcement
    """
    def __init__(self, start_date, end_date, lines=None):
        self.start_date = start_date
        self.end_date = end_date
        
        if lines:
            self.lines = lines
        else:
            self.lines = []


class MediaPlayer:
    """
    Initializes full-screen display and provides methods to show photos,
    videos, and announcements.
    """
    def __init__(self):
        pygame.init()

        # This will be used later for photo scaling
        self.screen_height = pygame.display.Info().current_h
        self.screen_width = pygame.display.Info().current_w

        self.screen = pygame.display.set_mode(
                (self.screen_width, self.screen_height),
                pygame.FULLSCREEN)
        self.screen.fill(pygame.Color('black'))

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
            if img_bitsize in [24, 32]:
                img = pygame.transform.smoothscale(
                        img, (scaled_width, scaled_height))
            else:
                img = pygame.transform.scale(
                        img, (scaled_width, scaled_height))

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
        self.screen.fill(pygame.Color('black'))
        self.screen.blit(img, (display_x, display_y))
        pygame.display.update()

    def show_video(self, filename):
        """
        Play a video from the specified file using the external omxplayer
        utility.
        """
        # Videos will not be scaled - this needs to be done during transcoding
        # Blank screen before showing video in case it doesn't fill the whole
        # screen
        self.screen.fill(pygame.Color('black'))
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
        current_y = (self.screen_height - total_height) / 2
        if current_y < 0:
            current_y = 0

        # Blank screen
        self.screen.fill(pygame.Color('black'))
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


def main():
    if len(sys.argv) > 1:
        config_file_name = sys.argv[1]
    else:
        config_file_name = 'config.json'

    with open(config_file_name, 'r') as f:
        config = json.load(f)

    date_fmt = config['date_fmt']

    photo_path = config['photos']['path']
    photo_files = [item.strip() for item in config['photos']['files']]
    photo_time = config['photos']['time']

    video_path = config['videos']['path']
    video_files = [item.strip() for item in config['videos']['files']]
    video_probability = config['videos']['probability']

    announcement_file = config['announcements']['file']
    announcement_font = config['announcements']['font']
    announcement_time = config['announcements']['time']
    announcement_probability = config['announcements']['probability']
    announcement_line_spacing = config['announcements']['spacing']

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

        with open(announcement_file, 'r') as f:
            announcement_data = json.load(f)

        # Iterate through all root elements
        for item in announcement_data:
            # Get start date and end date for announcement
            ann_start_date = datetime.strptime(
                        item['start_date'], date_fmt).date()
            ann_end_date = datetime.strptime(
                        item['end_date'], date_fmt).date()

            # Only show announcements that are within the specified date range
            if ann_start_date <= current_date and ann_end_date >= current_date:
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

        # Find all photos in designated folder based on the list of extensions.
        # Allow for both uppercase and lowercase extensions, but not mixed case
        for wildcard in photo_files:
            photos.extend(glob.glob(os.path.join(photo_path, wildcard.upper())))
            photos.extend(glob.glob(os.path.join(photo_path, wildcard.lower())))

        # Find all videos in designated folder based on the list of extensions.
        # Allow for both uppercase and lowercase extensions, but not mixed case
        for wildcard in video_files:
            videos.extend(glob.glob(os.path.join(video_path, wildcard.upper())))
            videos.extend(glob.glob(os.path.join(video_path, wildcard.lower())))

        # Display photos in alphabetical order by filename
        photos.sort()

        # Loop through all photos and insert videos at random. Note that the
        # contents of the folder will be reparsed each time all of the photos
        # are displayed, so this provides an opportunity to add/change the
        # contents without restarting the script.
        for photo in photos:
            player.show_image(photo)
            time.sleep(photo_time)

            # Display announcements based on the specified probability.
            # Check to be sure we have any announcements to display before
            # we try to display one.
            if random.random() <= announcement_probability and announcements:
                player.show_announcement(
                    random.choice(announcements),
                    announcement_font, announcement_line_spacing)
                time.sleep(announcement_time)

            # Play videos based on the specified probability.
            # Check to be sure we have any videos to play before we try
            # to play one.
            if random.random() <= video_probability and videos:
                player.show_video(random.choice(videos))


if __name__ == '__main__':
    main()