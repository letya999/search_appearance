from PIL import Image
try:
    import imagehash
except ImportError:
    imagehash = None

class ImageHasher:
    @staticmethod
    def compute_phash(image_path: str) -> str:
        """
        Compute perceptual hash of an image.
        Uses imagehash library if available, otherwise falls back to simple dhash implementation.
        """
        try:
            with Image.open(image_path) as img:
                if imagehash:
                    return str(imagehash.phash(img))
                else:
                    return ImageHasher._dhash(img)
        except Exception as e:
            print(f"Error computing hash: {e}")
            return ""

    @staticmethod
    def _dhash(image: Image.Image, hash_size: int = 8) -> str:
        # Grayscale and resize
        image = image.convert('L').resize(
            (hash_size + 1, hash_size),
            Image.Resampling.LANCZOS,
        )
        
        diff = []
        for row in range(hash_size):
            for col in range(hash_size):
                pixel_left = image.getpixel((col, row))
                pixel_right = image.getpixel((col + 1, row))
                diff.append(pixel_left > pixel_right)
                
        decimal_value = 0
        hex_string = []
        for index, value in enumerate(diff):
            if value:
                decimal_value += 2**(index % 8)
            if (index % 8) == 7:
                hex_string.append(hex(decimal_value)[2:].rjust(2, '0'))
                decimal_value = 0
        return ''.join(hex_string)
