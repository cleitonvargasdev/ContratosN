from app.services.whatsapp_chatbot_service import WhatsAppChatbotService


def build_service() -> WhatsAppChatbotService:
    return WhatsAppChatbotService.__new__(WhatsAppChatbotService)


def test_extract_event_from_legacy_quepasa_payload() -> None:
    service = build_service()
    payload = {
        "event": "message",
        "type": "message",
        "data": {
            "id": "ABCD123456",
            "from": "5567992858638@s.whatsapp.net",
            "to": "5599999999999@s.whatsapp.net",
            "message": {
                "type": "conversation",
                "text": "Ola, quero segunda via do boleto",
            },
        },
    }

    event = service._extract_event(payload)

    assert event == {
        "text": "Ola, quero segunda via do boleto",
        "chat_id": "5567992858638@s.whatsapp.net",
        "phone": "67992858638",
    }


def test_extract_event_from_current_quepasa_payload() -> None:
    service = build_service()
    payload = {
        "event": "message",
        "device_id": "5599999999999@s.whatsapp.net",
        "payload": {
            "id": "ABCD123456",
            "chat_id": "5567992858638@s.whatsapp.net",
            "from": "5567992858638@s.whatsapp.net",
            "from_name": "Cleiton",
            "is_from_me": False,
            "type": "text",
            "body": "Ola",
        },
    }

    event = service._extract_event(payload)

    assert event == {
        "text": "Ola",
        "chat_id": "5567992858638@s.whatsapp.net",
        "phone": "67992858638",
    }


def test_extract_event_ignores_outgoing_current_quepasa_payload() -> None:
    service = build_service()
    payload = {
        "event": "message",
        "payload": {
            "chat_id": "5567992858638@s.whatsapp.net",
            "from": "5599999999999@s.whatsapp.net",
            "is_from_me": True,
            "type": "text",
            "body": "Resposta enviada",
        },
    }

    assert service._extract_event(payload) is None
