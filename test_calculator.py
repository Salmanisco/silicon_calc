import unittest
import pandas as pd
from silicon_calculator import calculate_silicone_needs

class TestSiliconeCalculator(unittest.TestCase):
    def test_basic_calculation(self):
        # Setup
        data = {
            "Width": [1.0],
            "Height": [1.0],
            "Quantity": [1]
        }
        df = pd.DataFrame(data)
        meters_per_can = 10.0
        waste_factor = 0.0

        # Calculate
        # Perimeter = (1+1)*2 = 4
        # Total Perimeter = 4 * 1 = 4
        # Both sides = 4 * 2 = 8
        # Waste = 0
        # Cans = 8 / 10 = 0.8 -> 1 can
        
        _, total_perimeter, total_silicone, total_with_waste, cans = calculate_silicone_needs(
            df, meters_per_can, waste_factor
        )

        self.assertEqual(total_perimeter, 4.0)
        self.assertEqual(total_silicone, 8.0)
        self.assertEqual(total_with_waste, 8.0)
        self.assertEqual(cans, 1)

    def test_waste_factor(self):
        data = {
            "Width": [1.0],
            "Height": [1.0],
            "Quantity": [1]
        }
        df = pd.DataFrame(data)
        meters_per_can = 10.0
        waste_factor = 50.0 # 50% waste

        # Both sides = 8
        # With waste = 8 * 1.5 = 12
        # Cans = 12 / 10 = 1.2 -> 2 cans

        _, _, _, total_with_waste, cans = calculate_silicone_needs(
            df, meters_per_can, waste_factor
        )

        self.assertEqual(total_with_waste, 12.0)
        self.assertEqual(cans, 2)

    def test_multiple_rows(self):
        data = {
            "Width": [1.0, 2.0],
            "Height": [1.0, 2.0],
            "Quantity": [1, 2]
        }
        df = pd.DataFrame(data)
        meters_per_can = 10.0
        waste_factor = 0.0

        # Row 1: (1+1)*2 = 4. Total = 4.
        # Row 2: (2+2)*2 = 8. Total = 8*2 = 16.
        # Project Perimeter = 4 + 16 = 20.
        # Both sides = 40.
        # Cans = 40 / 10 = 4.

        _, total_perimeter, total_silicone, _, cans = calculate_silicone_needs(
            df, meters_per_can, waste_factor
        )

        self.assertEqual(total_perimeter, 20.0)
        self.assertEqual(total_silicone, 40.0)
        self.assertEqual(cans, 4)

if __name__ == '__main__':
    unittest.main()
