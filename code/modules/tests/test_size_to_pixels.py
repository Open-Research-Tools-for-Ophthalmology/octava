import os
import sys
import unittest

current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.abspath(os.path.join(current_dir, os.pardir))
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

from resize_image import size_to_pixels


class TestSizeToPixels(unittest.TestCase):
    def test_canonical_values(self):
        self.assertEqual(size_to_pixels(3.0), 1000)
        self.assertEqual(size_to_pixels(5.5), 1833)
        self.assertEqual(size_to_pixels(6.0), 2000)
        self.assertEqual(size_to_pixels(8.0), 2667)

    def test_invalid_input_defaults_to_200(self):
        self.assertEqual(size_to_pixels(None), 200)
        self.assertEqual(size_to_pixels("not_a_number"), 200)

    def test_proportional_values(self):
        self.assertEqual(size_to_pixels(1.0), 333)
        self.assertEqual(size_to_pixels(2.0), 667)
        self.assertEqual(size_to_pixels(4.0), 1333)
        self.assertEqual(size_to_pixels(4.5), 1500)
        self.assertEqual(size_to_pixels(7.2), 2400)


if __name__ == "__main__":
    sample_values = [
        None,
        "not_a_number",
        -1,
        0,
        1,
        2,
        3,
        4,
        5.5,
        6,
        7.2,
        8,
        10,
    ]

    print("size_value -> pixels")
    for value in sample_values:
        print(f"{value!r} -> {size_to_pixels(value)}")

    unittest.main(argv=["first-arg-is-ignored"], exit=False)
