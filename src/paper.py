from PIL import Image

def create_paper(
    width: int=None,
    height: int=None,
    color: str=None
):
    """Create a new Image object with the specified dimensions and background color"""
    if width is None:
        width = 1156
    if height is None:
        height = 1636
    if color is None:
        color = '#fff'
    return Image.new('RGB', (width, height,), color)
