import os
import re
from dotenv import load_dotenv
import uuid
import pytest
from unittest.mock import patch, MagicMock

load_dotenv()

from src.qube_pm_api_client.main import (
    QubePMPLAPIClient,
    QubePMPLAPISession,
    QubePMPLInvoice,
)


@pytest.fixture
def base_url():
    # fetch from .env for tests that rely on env; tests mock network calls
    return os.getenv("SANDBOX_API_URL", "https://example.test/")


@pytest.fixture
def client(base_url):
    # Load a sandbox connection from .env (values may be dummy in CI)
    return QubePMPLAPIClient(
        base_url=base_url,
        username=os.getenv("SANDBOX_USERNAME", "user"),
        password=os.getenv("SANDBOX_PASSWORD", "pass"),
        group=os.getenv("SANDBOX_GROUP", "group"),
    )


@pytest.fixture(autouse=True)
def disable_session_destructor():
    # Temporarily disable the session destructor during tests to avoid network calls during GC
    original = getattr(QubePMPLAPISession, "__del__", None)
    QubePMPLAPISession.__del__ = lambda self: None
    yield
    if original is not None:
        QubePMPLAPISession.__del__ = original


def test_add_soap_envelope_includes_body(client):
    body = "<test>payload</test>"
    envelope = client.add_soap_envelope(body)
    assert "<soapenv:Envelope" in envelope
    assert body in envelope


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


@patch("src.qube_pm_api_client.main.requests.post")
def test_get_properties_calls_post(mock_post):
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_post.return_value = mock_resp

    session = QubePMPLAPISession(client_session_key="s1", base_url="https://api.test/")

    resp = session.get_properties(ref="PROP1", exact=True)
    assert resp is mock_resp
    mock_post.assert_called()
    data = mock_post.call_args.kwargs.get("data") or mock_post.call_args.args[1]
    assert "property-lookup" in data
    assert "PROP1" in data
    assert 'exact="true"' in data


def test_get_fund_requires_params():
    session = QubePMPLAPISession(client_session_key="s2", base_url="https://api.test/")
    with pytest.raises(ValueError):
        session.get_fund()


@patch("src.qube_pm_api_client.main.requests.post")
def test_get_fund_calls_post(mock_post):
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_post.return_value = mock_resp

    session = QubePMPLAPISession(client_session_key="s3", base_url="https://api.test/")

    resp = session.get_fund(property_ref="P1")
    assert resp is mock_resp
    data = mock_post.call_args.kwargs.get("data") or mock_post.call_args.args[1]
    assert "fund-lookup" in data
    assert "P1" in data


@patch("src.qube_pm_api_client.main.requests.post")
def test_get_fund_heading_calls_post(mock_post):
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_post.return_value = mock_resp

    session = QubePMPLAPISession(client_session_key="s4", base_url="https://api.test/")

    resp = session.get_fund_heading(property_ref="P1", fund_type="FT")
    assert resp is mock_resp
    data = mock_post.call_args.kwargs.get("data") or mock_post.call_args.args[1]
    assert "heading-lookup" in data
    assert "FT" in data


@patch("src.qube_pm_api_client.main.requests.post")
def test_post_invoice_with_and_without_link(mock_post):
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_post.return_value = mock_resp

    session = QubePMPLAPISession(client_session_key="s5", base_url="https://api.test/")

    invoice_with_link = QubePMPLInvoice(
        supplier_ref="SUP1",
        invoice_number="INV123",
        nett=100.0,
        vat=20.0,
        gross=120.0,
        invoice_date="2025-01-01",
        period_start="2025-01-01",
        period_finish="2025-01-31",
        prompt_payment_due="2025-02-01",
        payment_due="2025-02-15",
        vat_code="V1",
        invoice_link="https://docs/test.pdf",
    )

    resp = session.post_invoice(invoice_with_link, property_ref="P1", user_id="u1", fund_heading_uid="h1")
    assert resp is mock_resp
    data = mock_post.call_args.kwargs.get("data") or mock_post.call_args.args[1]
    assert "document" in data
    assert "INV123" in data
    assert "https://docs/test.pdf" in data

    # Now without a link
    mock_post.reset_mock()
    invoice_no_link = QubePMPLInvoice(
        supplier_ref="SUP2",
        invoice_number="INV456",
        nett=50.0,
        vat=10.0,
        gross=60.0,
        invoice_date="2025-02-01",
        period_start="2025-02-01",
        period_finish="2025-02-28",
        prompt_payment_due="2025-03-01",
        payment_due="2025-03-15",
        vat_code="V2",
        invoice_link="",
    )

    resp2 = session.post_invoice(invoice_no_link, property_ref="P2", user_id="u2", fund_heading_uid="h2")
    assert resp2 is mock_resp
    data2 = mock_post.call_args.kwargs.get("data") or mock_post.call_args.args[1]
    assert "<!-- document -->" in data2


@patch("src.qube_pm_api_client.main.requests.post")
def test_client_get_session_parses_login_response(mock_post, base_url):
    # Successful login (no error-message)
    success_xml = """<soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/"><soapenv:Body><LoginResponse><status error-code="" error-message=""/></LoginResponse></soapenv:Body></soapenv:Envelope>"""
    mock_success = MagicMock()
    mock_success.content = success_xml.encode()
    mock_post.return_value = mock_success

    client = QubePMPLAPIClient(base_url=base_url, username="u", password="p", group="g")
    session = client.get_session()
    assert isinstance(session, QubePMPLAPISession)


@patch("src.qube_pm_api_client.main.requests.post")
def test_client_get_session_raises_on_login_error(mock_post, base_url):
    error_xml = """<soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/"><soapenv:Body><LoginResponse><status error-code="123" error-message="Bad creds"/></LoginResponse></soapenv:Body></soapenv:Envelope>"""
    mock_error = MagicMock()
    mock_error.content = error_xml.encode()
    mock_post.return_value = mock_error

    client = QubePMPLAPIClient(base_url=base_url, username="u", password="p", group="g")
    with pytest.raises(Exception) as exc:
        client.get_session()
    assert "Session creation failed" in str(exc.value)
