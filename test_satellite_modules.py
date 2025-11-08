import unittest
from satellite_modules import (
    estimate_satellite_lifetime,
    satellite_age_and_EOL,
    debris_collision_risk,
    solar_storm_risk,
    predict_deorbit_location
)

class TestSatelliteModules(unittest.TestCase):

    def test_estimate_satellite_lifetime(self):
        self.assertAlmostEqual(estimate_satellite_lifetime(250), 0.5)
        self.assertAlmostEqual(estimate_satellite_lifetime(400), 7.0)
        self.assertAlmostEqual(estimate_satellite_lifetime(600), 20.0)
        self.assertAlmostEqual(estimate_satellite_lifetime(900), 70.0)

    def test_satellite_age_and_EOL(self):
        result = satellite_age_and_EOL("2020-01-01", 500)
        self.assertIn("age_years", result)
        self.assertIn("estimated_EOL_year", result)
        self.assertIn("lifetime_years", result)
        self.assertGreater(result["estimated_EOL_year"], 2020)

    def test_debris_collision_risk(self):
        result = debris_collision_risk(500, 51.6, 6)
        self.assertEqual(result["debris_zone"], "Medium")
        self.assertIn(result["collision_risk_level"], ["Low", "Moderate", "High"])

    def test_solar_storm_risk(self):
        result = solar_storm_risk(2025, 2030)
        self.assertIn("solar_storm_risk", result)
        self.assertIn(result["solar_storm_risk"], ["Low", "Moderate", "High"])

    def test_predict_deorbit_location(self):
        result = predict_deorbit_location(51.6, 2031)
        self.assertIn("predicted_latitude", result)
        self.assertIn("predicted_longitude", result)
        self.assertEqual(result["predicted_deorbit_year"], 2031)

if __name__ == "__main__":
    unittest.main()
