import random
from PIL import ImageFont

def get_font():
    """Return a randomly selected TrueType font with a random size in the range"""
    
    # randomly choose a font file path from a list of available fonts
    fpaths = random.choice(['fonts/THSarabun.ttf', 'fonts/THSarabun Bold.ttf'])
    
    # return an instance of the ImageFont class with the randomly chosen font file path and size
    return ImageFont.truetype(fpaths, size=random.randrange(26, 28))