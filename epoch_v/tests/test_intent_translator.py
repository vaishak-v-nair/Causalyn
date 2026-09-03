import unittest
from epoch_v.intent_translator import IntentTranslator

class IntentTranslatorTests(unittest.TestCase):
    def test_matrix_metadata_and_symmetry(self):
        result = IntentTranslator().encode("revoke token")
        self.assertEqual(result.shape, (3, 3))
        matrix = result.tensor.tolist() if hasattr(result.tensor, "tolist") else result.tensor
        for i in range(3):
            for j in range(3):
                self.assertAlmostEqual(matrix[i][j], matrix[j][i])

if __name__ == "__main__":
    unittest.main()
