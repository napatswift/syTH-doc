import random
from PIL import ImageFont
import os

def get_font():
    """Return a randomly selected TrueType font with a random size in the range"""
    # get the paths of all the font files in the fonts directory
    font_paths = [os.path.join('fonts', f) for f in os.listdir('fonts') if f.endswith('.ttf')]
    # randomly choose a font file path
    fpaths = random.choice(font_paths)
    
    # return an instance of the ImageFont class with the randomly chosen font file path and size
    return ImageFont.truetype(fpaths, size=random.randrange(26, 40))
