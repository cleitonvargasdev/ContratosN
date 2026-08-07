import unittest

from app.services.whatsapp_service import WhatsAppService


class WhatsAppServiceStatusTests(unittest.TestCase):
    def test_connected_status_is_true_when_provider_reports_connected_without_phone(self) -> None:
        service = WhatsAppService.__new__(WhatsAppService)
        payload = {
            "status": "Ready",
            "data": {
                "success": True,
                "connected": True,
                "server": {"verified": True},
            },
        }

        connected = service._is_connected(
            payload,
            ["5511999999999"],
            "55",
            [],
            None,
            True,
        )

        self.assertTrue(connected)

    def test_connected_status_is_true_when_provider_reports_connected_flag_without_ready_status(self) -> None:
        service = WhatsAppService.__new__(WhatsAppService)
        payload = {
            "status": "ok",
            "connected": True,
        }

        connected = service._is_connected(
            payload,
            ["5511999999999"],
            "55",
            [],
            None,
            False,
        )

        self.assertTrue(connected)

    def test_connected_status_is_false_when_provider_reports_not_ready(self) -> None:
        service = WhatsAppService.__new__(WhatsAppService)
        payload = {
            "status": "offline",
            "data": {
                "success": False,
                "connected": False,
                "server": {"verified": False},
            },
        }

        connected = service._is_connected(
            payload,
            ["5511999999999"],
            "55",
            [],
            None,
            False,
        )

        self.assertFalse(connected)


if __name__ == "__main__":
    unittest.main()
