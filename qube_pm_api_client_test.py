import os
import re
from dotenv import load_dotenv
import uuid
import pytest
from unittest.mock import patch, MagicMock

load_dotenv()

from src.qube_pm_api_client.main import QubePMPLAPIClient, QubePMPLAPISession


@pytest.fixture
def base_url():
    # fetch from .env
    return os.getenv("SANDBOX_API_URL")


@pytest.fixture
def client(base_url):
    # Load a sandbox connection from .env
    return QubePMPLAPIClient(base_url=base_url, username=os.getenv("SANDBOX_USERNAME"), password=os.getenv("SANDBOX_PASSWORD"), group=os.getenv("SANDBOX_GROUP"))


def test_add_soap_envelope_includes_body(client):
    body = "<test>payload</test>"
    envelope = client.add_soap_envelope(body)
    assert "<soapenv:Envelope" in envelope
    assert body in envelope


def test_get_session_returns_session(base_url, client):
    session = client.get_session()
    assert isinstance(session, QubePMPLAPISession)
    # client_session_key should be a UUID string
    uuid_obj = uuid.UUID(session.client_session_key)
    assert session.base_url == base_url


@patch("src.qube_pm_api_client.main.requests.post")
def test_login_calls_requests_post(mock_post, client):
    # Arrange
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_post.return_value = mock_response

    # Act
    resp = client.login(client_session_key="fixed-key-123")

    # Assert
    assert resp is mock_response
    # Ensure requests.post was called once and with expected base_url
    mock_post.assert_called_once()
    called_url = mock_post.call_args.args[0]
    called_data = mock_post.call_args.kwargs.get("data") or mock_post.call_args.args[1]
    called_headers = mock_post.call_args.kwargs.get("headers") or mock_post.call_args.args[2]

    assert called_url == client.base_url
    # SOAPAction header is set
    assert any(k.lower() == "soapaction" for k in called_headers)
    # client_session_key in body
    assert "fixed-key-123" in called_data


@patch("src.qube_pm_api_client.main.requests.post")
def test_session_methods_call_requests_post(mock_post):
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_post.return_value = mock_response

    session = QubePMPLAPISession(client_session_key="sess-abc-1", base_url="https://api.test/")

    # logout
    r1 = session.logout()
    assert r1 is mock_response
    # close_report
    r2 = session.close_report()
    assert r2 is mock_response
    # get_users default
    r3 = session.get_users()
    assert r3 is mock_response

    # Check that requests.post was called three times
    assert mock_post.call_count == 3

    # Inspect last call (get_users) for presence of client session key and QubeProcess action
    last_call = mock_post.call_args_list[-1]
    called_url = last_call.args[0]
    called_data = last_call.kwargs.get("data") or last_call.args[1]
    called_headers = last_call.kwargs.get("headers") or last_call.args[2]

    assert called_url == session.base_url
    assert "sess-abc-1" in called_data
    assert "QubeProcess-1ia" in called_headers.get("SOAPAction", "")
