import base64
import pytest

from email_tracker.gmail_service import GmailService


class DummyModify:
    def __init__(self):
        self.calls = []

    def execute(self):
        # simulate successful call
        self.calls.append(True)
        return {}


class DummyUsers:
    def __init__(self, modify_obj):
        self.modify_obj = modify_obj

    def messages(self):
        return self

    def modify(self, userId, id, body):
        # record parameters and return dummy object
        self.modify_obj.calls.append((userId, id, body))
        return self.modify_obj


class DummyService:
    def __init__(self, modify_obj):
        self._modify = modify_obj

    def users(self):
        return DummyUsers(self._modify)


@pytest.fixture(autouse=True)
def patch_service(monkeypatch):
    # create a fake GmailService instance without real auth
    dummy = GmailService.__new__(GmailService)
    dummy.service = DummyService(DummyModify())
    return dummy


def test_mark_as_unread_adds_label(patch_service):
    gmail = patch_service
    result = gmail.mark_as_unread("12345")
    assert result is True
    # ensure the body requested to add UNREAD
    calls = gmail.service._modify.calls
    assert calls[0] == ("me", "12345", {"addLabelIds": ["UNREAD"]})


def test_mark_as_read_removes_label(patch_service):
    gmail = patch_service
    result = gmail.mark_as_read("xyz")
    assert result is True
    calls = gmail.service._modify.calls
    assert calls[0] == ("me", "xyz", {"removeLabelIds": ["UNREAD"]})


def test_send_reply_constructs_message(monkeypatch, patch_service):
    gmail = patch_service

    sent = {}

    def fake_send(userId, body):
        sent['userId'] = userId
        sent['body'] = body
        class R:
            def execute(self):
                return {}
        return R()

    monkeypatch.setattr(gmail.service.users(), 'messages', lambda : gmail.service.users())
    monkeypatch.setattr(gmail.service.users(), 'send', fake_send)

    success = gmail.send_reply(
        to_email="foo@example.com",
        subject="Hello",
        body="Hi there",
        in_reply_to_id="ABC123",
    )

    assert success
    assert sent['userId'] == 'me'
    raw = sent['body']['raw']
    decoded = base64.urlsafe_b64decode(raw).decode('utf-8')
    assert "Re: Hello" in decoded
    assert "Hi there" in decoded
    assert "In-Reply-To: ABC123" in decoded
