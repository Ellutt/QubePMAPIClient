import pytest
import os
import uuid
import requests
from dotenv import load_dotenv

load_dotenv()

from src.qube_pm_api_client.main import QubePMPLAPIClient, QubePMPLAPISession

@pytest.fixture
def base_url() -> str:
    # fetch from .env
    return os.getenv("KTS_URL")

@pytest.fixture
def session(base_url: str) -> QubePMPLAPISession:
    client = QubePMPLAPIClient(base_url=base_url, username=os.getenv("KTS_USERNAME"), password=os.getenv("KTS_PASSWORD"), group=os.getenv("KTS_GROUP"))
    return client.get_session()

def test_get_users(session: QubePMPLAPISession):
    session.close_report()  # Ensure no open reports
    response = session.get_users()
    assert response is not None
    assert response.status_code == 200
    assert b"<user-lookup success=\"true\">" in response.content

def test_get_properties(session: QubePMPLAPISession):
    response = session.get_properties()
    assert response is not None
    assert response.status_code == 200
    assert b"<property-lookup success=\"true\">" in response.content

def test_get_fund_by_property_ref(session: QubePMPLAPISession):
    response = session.get_fund(property_ref="001/01")
    assert response is not None
    assert response.status_code == 200
    assert b"<fund-lookup success=\"true\">" in response.content

def test_get_fund_without_refs_raises(session: QubePMPLAPISession):
    with pytest.raises(ValueError):
        session.get_fund()

def test_get_fund_with_fund_uid(session: QubePMPLAPISession):
    response = session.get_fund(fund_uid="77")
    assert response is not None
    assert response.status_code == 200
    assert b"<fund-lookup success=\"true\">" in response.content

def test_get_fund_heading(session: QubePMPLAPISession):
    response = session.get_fund_heading(property_ref="001/01", fund_type="Admin Charge")
    assert response is not None
    assert response.status_code == 200
    assert b"<heading-lookup success=\"true\">" in response.content

def test_post_invoice(session: QubePMPLAPISession):
    from src.qube_pm_api_client.main import QubePMPLInvoice
    invoice = QubePMPLInvoice(
        invoice_number="INV-" + str(uuid.uuid4())[:8],
        invoice_date="2024-06-01",
        supplier_ref="ZGARDENING12",
        period_start="2024-05-01",
        period_finish="2024-05-31",
        prompt_payment_due="2024-06-01",
        payment_due="2024-06-01",
        nett=100.00,
        vat=20.00,
        gross=120.00,
        vat_code="1"
    )
    response = session.post_invoice(
        invoice=invoice,
        property_ref="001/01",
        user_id="Stratas Integration User Account",
        fund_heading_uid="1181"
    )
    #save response for debugging
    with open("invoice_response_debug.xml", "wb") as f:
        f.write(response.content)
    assert response is not None
    assert response.status_code == 200
    assert b"<success>true</success>" in response.content

def test_close_report(session: QubePMPLAPISession):
    response = session.close_report()
    assert response is not None
    assert response.status_code == 200
    assert b"CloseReportResponse" in response.content

def test_logout(session: QubePMPLAPISession):
    response = session.logout()
    assert response is not None
    assert response.status_code == 200
    assert b"LogoutResponse" in response.content