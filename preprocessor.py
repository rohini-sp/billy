# preprocessor.py
from PIL import Image, ImageEnhance
import cv2

class InvoiceImageProcessor:
    def __init__(self, image_path):
        self.image_path = image_path
        self.processed_image_path = "processed_invoice.jpg"

    def enhance_sharpness(self, factor=2.0):
        """Enhances the sharpness of the image."""
        image = Image.open(self.image_path)
        sharpened_image = image.convert('RGB')
        # Save sharpened image temporarily before binarizing
        sharpened_image.save(self.processed_image_path)
        return self.processed_image_path

    def binarize_image(self):
        """Converts the sharpened image to a binary image."""
        image = cv2.imread(self.processed_image_path, cv2.IMREAD_GRAYSCALE)
        # _, binary_image = cv2.threshold(image, 128, 255, cv2.THRESH_BINARY)
        binarized_path = "final_binarized_invoice.jpg"
        cv2.imwrite(binarized_path, image)
        return binarized_path

    def process_image(self, sharpness_factor=2.0):
        """Process the image by sharpening first, then binarizing."""
        print("Enhancing sharpness...")
        self.enhance_sharpness(sharpness_factor)
        print("Binarizing image...")
        return self.binarize_image()
