# MIT License

# Copyright (c) 2021 David Rice

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

Screen class

https://github.com/davidsmakerworks/media-display
"""


from typing import Optional

import pygame


class Screen:
    """
    Class representing a pyhsical screen where a surface is displayed.

    Initializes the pygame display and gets the corresponding surface.

    Properties:
    width -- screen width in pixels
    height -- screen height in pixels
    bg_color -- pygame Color object representing the background color to use
    fullscreen -- boolean representing whether full-screen display
        should be used
    """
    def __init__(
            self, width: int, height: int, bg_color: pygame.Color,
            fullscreen: Optional[bool] = False) -> None:
        self.width = width
        self.height = height

        if fullscreen:
            flags = pygame.FULLSCREEN
        else:
            flags = None

        self.surface = pygame.display.set_mode(
                (self.width, self.height), flags)

        self.surface.fill(bg_color)

        pygame.display.update()


if __name__ == '__main__':
    print('This file should not be run directly. Run main.py instead.')
