import httpx
payload = {
    "event": "message",
    "type": "message",
    "timestamp": "2026-08-06T22:30:10Z",
    "data": {
        "id": "ABCD123456",
        "from": "5567992858638@s.whatsapp.net",
        "to": "5599999999999@s.whatsapp.net",
        "pushName": "Cleiton",
        "message": {
            "type": "conversation",
            "text": "Olá, quero segunda via do boleto"
        }
    }
}
url = 'http://127.0.0.1:8007/webhooks/webhook'
with httpx.Client(timeout=30.0) as client:
    response = client.post(url, json=payload)
    print('status:', response.status_code)
    print(response.text)
