import unittest
from datetime import date
from backend.app.services.importer import importer_service

class TestImporterService(unittest.TestCase):
    def test_parse_amount(self):
        self.assertEqual(importer_service._parse_amount("$1,234.56"), 1234.56)
        self.assertEqual(importer_service._parse_amount("-500.00"), -500.0)
        self.assertEqual(importer_service._parse_amount(""), 0.0)
        self.assertEqual(importer_service._parse_amount(None), 0.0)

    def test_parse_date(self):
        self.assertEqual(importer_service._parse_date("01/15/2026"), date(2026, 1, 15))
        self.assertEqual(importer_service._parse_date("01/15/2026 as of 03:45 PM"), date(2026, 1, 15))
        self.assertEqual(importer_service._parse_date("2026-01-15"), date(2026, 1, 15))
        self.assertIsNone(importer_service._parse_date("invalid"))

    def test_get_account_hash_from_filename(self):
        # 測試檔名識別邏輯 (基於我們已知的 323 帳號)
        filename = "yuang_XXX323_Transactions_20260115.csv"
        # 由於此測試環境可能沒有真實 API 連線，我們主要測試它是否能回傳 fallback 或正確解析
        h = importer_service._get_account_hash_from_filename(filename)
        self.assertIsNotNone(h)
        self.assertEqual(h, "0BE26F441D89A19F6355BB0D093751CE9B176408561BBD9FEB09A83634FBD991")

if __name__ == '__main__':
    unittest.main()
