import unittest
import pandas as pd
from silicon_calculator import calculate_project_materials

class TestSiliconeCalculator(unittest.TestCase):
    def test_split_calculation(self):
        # Setup
        data = {
            "Width": [1.0],
            "Height": [1.0],
            "Quantity": [1] # Perimeter = 4m
        }
        df = pd.DataFrame(data)
        
        # EXT: 10x10mm gap, 100ml can (Just for easy math) -> 100 mm^2 -> 100ml/m -> 1m/can
        ext_w, ext_d, ext_vol = 10.0, 10.0, 100.0
        
        # INT: 5x5mm gap, 50ml can -> 25 mm^2 -> 25ml/m -> 2m/can
        int_w, int_d, int_vol = 5.0, 5.0, 50.0
        
        screw_spacing = 40.0 # 40cm = 0.4m
        waste_factor = 0.0

        # Ext Length = 4m. Cans = 4 / 1 = 4.
        # Int Length = 4m. Cans = 4 / 2 = 2.
        # Screws = 4m / 0.4m = 10 screws.

        (
            _, 
            total_perimeter, 
            ext_len, 
            int_len, 
            ext_cans, 
            int_cans,
            total_screws,
            total_rubber
        ) = calculate_project_materials(
            df, 
            ext_w, ext_d, ext_vol,
            int_w, int_d, int_vol,
            screw_spacing,
            waste_factor
        )

        self.assertEqual(total_perimeter, 4.0)
        self.assertEqual(ext_len, 4.0)
        self.assertEqual(int_len, 4.0)
        self.assertEqual(ext_cans, 4)
        self.assertEqual(int_cans, 2)
        self.assertEqual(total_screws, 10)
        # Rubber = 4 * 3 = 12
        self.assertEqual(total_rubber, 12.0)

    def test_waste_factor(self):
        data = {
            "Width": [1.0],
            "Height": [1.0],
            "Quantity": [1] # Perimeter = 4m
        }
        df = pd.DataFrame(data)
        
        # Same params as above
        ext_w, ext_d, ext_vol = 10.0, 10.0, 100.0 # 1m/can
        int_w, int_d, int_vol = 5.0, 5.0, 50.0   # 2m/can
        
        screw_spacing = 20.0 # 20cm = 0.2m. Screws = 4 / 0.2 = 20.
        waste_factor = 50.0 # 50% waste

        # Length w/ Waste = 4 * 1.5 = 6m.
        # Ext Cans = 6 / 1 = 6.
        # Int Cans = 6 / 2 = 3.
        # Screws should affect by RAW perimeter? Usually yes.
        # 4m / 0.2 = 20 screws.
        # Rubber = 12 * 1.5 = 18m.

        (
            _, 
            _, 
            ext_len, 
            int_len, 
            ext_cans, 
            int_cans,
            total_screws,
            total_rubber
        ) = calculate_project_materials(
            df, 
            ext_w, ext_d, ext_vol,
            int_w, int_d, int_vol,
            screw_spacing,
            waste_factor
        )

        self.assertEqual(ext_len, 6.0)
        self.assertEqual(int_len, 6.0)
        self.assertEqual(ext_cans, 6)
        self.assertEqual(int_cans, 3)
        self.assertEqual(total_screws, 20)
        self.assertEqual(total_rubber, 18.0)

    def test_multiple_rows(self):
        data = {
            "Width": [1.0, 2.0],
            "Height": [1.0, 2.0],
            "Quantity": [1, 2]
        }
        # Row 1: 4m. 
        # Row 2: 8m * 2 = 16m.
        # Total Perimeter = 20m.
        
        df = pd.DataFrame(data)
        
        # EXT: 1m/can
        ext_w, ext_d, ext_vol = 10.0, 10.0, 100.0
        # INT: 5m/can  (10x2=20ml/m. 100ml can. 100/20=5)
        int_w, int_d, int_vol = 10.0, 2.0, 100.0
        
        screw_spacing = 100.0 # 1m. 20m/1m = 20 screws.
        waste_factor = 0.0

        # Ext Cans = 20 / 1 = 20.
        # Int Cans = 20 / 5 = 4.
        # Rubber = 20 * 3 = 60.

        (
            _, 
            total_perimeter, 
            _, 
            _, 
            ext_cans, 
            int_cans,
            total_screws,
            total_rubber
        ) = calculate_project_materials(
            df, 
            ext_w, ext_d, ext_vol,
            int_w, int_d, int_vol,
            screw_spacing,
            waste_factor
        )

        self.assertEqual(total_perimeter, 20.0)
        self.assertEqual(ext_cans, 20)
        self.assertEqual(int_cans, 4)
        self.assertEqual(total_screws, 20)
        self.assertEqual(total_rubber, 60.0)

if __name__ == '__main__':
    unittest.main()
