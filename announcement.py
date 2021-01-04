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

Classes related to announcements

https://github.com/davidsmakerworks/media-display

TODO: Move announcement parsing to Announcement class

TODO: Better format to store announcements(?)
"""


class AnnouncementLine:
    """
    Class representing one line of an announcement after it has
    been parsed from JSON file

    Properties:
    text -- text of the line, or None if it is a blank line
    size -- size of text or height of the blank line
    color -- text color as a PyGame color object
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


if __name__ == '__main__':
    print('This file should not be run directly. Run main.py instead.')