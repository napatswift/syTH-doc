from PIL import Image


def create_paper(width: int = None, height: int = None, color: str = None):
    """
    Create a new Image object with the specified dimensions and background color

    Args:
        width (int): The width of the new image.
        height (int): The height of the new image.
        color (str): The background color of the new image.

    Returns:
        Image: A new Image object with
            the specified dimensions and background color.
    """

    if width is None:
        width = 1156
    if height is None:
        height = 1636
    if color is None:
        color = "#fff"
    return Image.new(
        "RGB",
        (
            width,
            height,
        ),
        color,
    )
