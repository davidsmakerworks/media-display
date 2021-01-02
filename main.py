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


import json
import random
import sys

import pygame

from media_player import MediaPlayer
from screen import Screen


def main():
    if len(sys.argv) > 1:
        config_file_name = sys.argv[1]
    else:
        config_file_name = 'config.json'

    with open(config_file_name, 'r') as f:
        config = json.load(f)

    pygame.init()

    random.seed()

    # Need to hide mouse pointer here since the MediaPlayer class
    # might be used to render on a surface instead of a display
    pygame.mouse.set_visible(False)

    screen = Screen(
        width=config['display']['width'],
        height=config['display']['height'],
        bg_color=pygame.Color('black'),
        fullscreen=config['display']['fullscreen'])

    screen_surface = screen.surface
    play_again = True

    while play_again:
        player = MediaPlayer(
            surface=screen_surface,
            config=config,
            surface_is_display=True)

        play_again = player.run()

    pygame.quit()


if __name__ == '__main__':
    main()