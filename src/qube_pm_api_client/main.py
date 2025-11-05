from dataclasses import dataclass
import uuid
import requests
import xml.etree.ElementTree as ET

##############################################
# SOAP client for Qube PM Purchase Ledger API
##############################################

# Data class representing an invoice to be posted.

@dataclass
class QubePMPLInvoice:
    def __init__(
        self,
        supplier_ref: str,
        invoice_number: str,
        nett: float,
        vat: float,
        gross: float,
        invoice_date: str,
        period_start: str,
        period_finish: str,
        prompt_payment_due: str,
        payment_due: str,
        vat_code: str,
        invoice_link: str = "",
    ):
        self.supplier_ref = supplier_ref
        self.invoice_number = invoice_number
        self.invoice_link = invoice_link
        self.invoice_date = invoice_date
        self.period_start = period_start
        self.period_finish = period_finish
        self.prompt_payment_due = prompt_payment_due
        self.payment_due = payment_due
        self.nett = nett
        self.vat = vat
        self.gross = gross
        self.vat_code = vat_code

# Common base class for client and session, holds shared methods and attributes.


class QubePMPLAPICommon:
    def __init__(self, base_url: str = ""):
        self.base_url = base_url
        self.headers = {
            "Content-Type": "text/xml; charset=utf-8",
            "xmlns": "http://qube.qubeglobal.com/ns/webservice",
        }

    def add_soap_envelope(self, body: str) -> str:
        envelope: str = f"""<soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/" xmlns:web="http://qube.qubeglobal.com/ns/webservice/">
   <soapenv:Header/>
   <soapenv:Body>
      {body}
   </soapenv:Body>
</soapenv:Envelope>"""
        return envelope

    def make_request(self, soap_action: str, body: str) -> requests.Response:
        headers = self.headers.copy()
        headers["SOAPAction"] = soap_action
        response = requests.post(self.base_url, data=body, headers=headers)
        return response


# Session class, holds the client session key and has methods that require a valid session.
# Defaults to partner portal base URL, which is our sandbox/test environment.


class QubePMPLAPISession(QubePMPLAPICommon):

    def __init__(
        self,
        client_session_key: str = str(uuid.uuid4()),
        base_url: str = "https://partner-portals.qubeglobalcloud.com/qubews/",
    ):
        self.client_session_key: str = client_session_key
        super().__init__(base_url=base_url)

    # destructor, calls logout on deletion
    def __del__(self):
        self.logout()

    # Ends the session by calling the Logout API method.
    def logout(self) -> requests.Response:
        body = f"""<web:Logout>
    <!--Optional:-->
    <web:ClientSessionKey>{self.client_session_key}</web:ClientSessionKey>
</web:Logout>"""
        data = self.add_soap_envelope(body)
        response = self.make_request(
            "http://qube.qubeglobal.com/ns/webservice/Logout", data
        )
        return response

    # Close the current report. Must be called before making another lookups call, or posting a new transaction.
    # If not called, subsequent calls will fail. And the session may need to be thrown away and restarted.
    def close_report(self) -> requests.Response:
        body = f"""<web:CloseReport>
    <web:ClientSessionKey>{self.client_session_key}</web:ClientSessionKey>
</web:CloseReport>"""
        data = self.add_soap_envelope(body)
        response = self.make_request(
            "http://qube.qubeglobal.com/ns/webservice/CloseReport", data
        )
        return response

    # User lookup method. Looks up users by reference.
    # ref: reference to look up, exact: whether to match exactly or not.
    # Calling without args returns all users.
    def get_users(self, ref: str = "?", exact: bool = False) -> requests.Response:
        exact_str = "true" if exact else "false"
        body = f"""<web:QubeProcess-1ia>
<web:ClientSessionKey>{self.client_session_key}</web:ClientSessionKey>
<web:QubeProcessName>PURAPI:webAPI</web:QubeProcessName>
<web:Data>
        <request-to-qube>
          <user-lookup>
            <reference exact="{exact_str}">{ref}</reference>
          </user-lookup>
        </request-to-qube>
    </web:Data>
    </web:QubeProcess-1ia>"""
        data = self.add_soap_envelope(body)

        response = self.make_request(
            "http://qube.qubeglobal.com/ns/webservice/QubeProcess-1ia", data
        )
        return response

    # Property lookup method. Looks up properties by reference.
    # ref: reference to look up, exact: whether to match exactly or not.
    # Calling without args returns all properties. '?' is a wildcard character.
    def get_properties(self, ref: str = "?", exact: bool = False) -> requests.Response:
        exact_str = "true" if exact else "false"
        body = f"""<web:QubeProcess-1ia>
<web:ClientSessionKey>{self.client_session_key}</web:ClientSessionKey>
<web:QubeProcessName>PURAPI:webAPI</web:QubeProcessName>
<web:Data>
        <request-to-qube>
          <property-lookup>
            <reference exact="{exact_str}">{ref}</reference>
          </property-lookup>
        </request-to-qube>
    </web:Data>
    </web:QubeProcess-1ia>"""
        data = self.add_soap_envelope(body)

        response = self.make_request(
            "http://qube.qubeglobal.com/ns/webservice/QubeProcess-1ia", data
        )
        return response

    # Fund lookup method. Looks up funds by various parameters.
    # At least one ref/uid parameter should be provided to the lookup.

    def get_fund(
        self,
        property_ref: str = "",
        fund_uid: str = "",
        owner_ref: str = "",
        description: str = "",
    ) -> requests.Response:

        if not (property_ref or fund_uid or owner_ref):
            raise ValueError(
                "You must provide at least one of property_ref, fund_uid, or owner_ref to lookup a fund."
            )

        body = f"""<web:QubeProcess-1ia>
<web:ClientSessionKey>{self.client_session_key}</web:ClientSessionKey>
<web:QubeProcessName>PURAPI:webAPI</web:QubeProcessName>
<web:Data>
        <request-to-qube>
          <fund-lookup>
            <owner-reference>{owner_ref}</owner-reference>
            <property-reference>{property_ref}</property-reference>
            <description>{description}</description>
            <unique-id>{fund_uid}</unique-id>
          </fund-lookup>
        </request-to-qube>
    </web:Data>
    </web:QubeProcess-1ia>"""

        data = self.add_soap_envelope(body)
        response = self.make_request(
            "http://qube.qubeglobal.com/ns/webservice/QubeProcess-1ia", data
        )
        return response

    def get_fund_heading(
        self, property_ref: str, fund_type: str
    ) -> requests.Response:
        body = f"""<web:QubeProcess-1ia>
    <web:ClientSessionKey>{self.client_session_key}</web:ClientSessionKey>
    <web:QubeProcessName>PURAPI:webAPI</web:QubeProcessName>
    <web:Data>
        <request-to-qube>
            <heading-lookup>
                <property-reference>{property_ref}</property-reference>
                <fund-type>{fund_type}</fund-type>
            </heading-lookup>
        </request-to-qube>
    </web:Data>
</web:QubeProcess-1ia>"""
        data = self.add_soap_envelope(body)

        response = self.make_request(
            "http://qube.qubeglobal.com/ns/webservice/QubeProcess-1ia", data
        )
        return response

    # Invoice docs cannot be posted directly.
    # Invoice docs need to be hosted on a web server accessible by Qube and a link passed via this method.
    # Invoices will always be posted to the draft register for manual review.
    # Only supports header level details. A single line item contains the invoice totals.

    def post_invoice(
        self,
        invoice: QubePMPLInvoice,
        property_ref: str,
        user_id: str,
        fund_heading_uid: str,
    ) -> requests.Response:
        
        if invoice.invoice_link:
            document_string = f"<document shortcut=\"false\" saveas=\"{invoice.invoice_number}\">{invoice.invoice_link}</document>"
        else:
            document_string = f"<!-- document -->"

        body = f"""<web:QubeProcess-1ia>
    <web:ClientSessionKey>{self.client_session_key}</web:ClientSessionKey>
    <web:QubeProcessName>PUR:Invoice.ws</web:QubeProcessName>
    <web:Data>
        <request-to-qube>
            <version>1</version>
            <pass-register-warnings>true</pass-register-warnings>
            <pass-ledger-warnings>false</pass-ledger-warnings>
            <post-journal>
                <to-register>true</to-register>
                <type>invoice</type>
                <user-id>{user_id}</user-id>
                {document_string}
                <supplier-reference>{invoice.supplier_ref}</supplier-reference>
                <invoice-number>{invoice.invoice_number}</invoice-number>
                <invoice-date>{invoice.invoice_date}</invoice-date>
                <period-start>{invoice.period_start}</period-start>
                <period-finish>{invoice.period_finish}</period-finish>
                <prompt-payment-due>{invoice.prompt_payment_due}</prompt-payment-due>
                <payment-due>{invoice.payment_due}</payment-due>
                <nett>{invoice.nett:.2f}</nett>
                <vat>{invoice.vat:.2f}</vat>
                <gross>{invoice.gross:.2f}</gross>
                <vat-on-pay>false</vat-on-pay>
                <detail>
                    <line-type>Property expenditure</line-type>
                    <vat-code>{invoice.vat_code}</vat-code>
                    <nett>{invoice.nett:.2f}</nett>
                    <vat>{invoice.vat:.2f}</vat>
                    <gross>{invoice.gross:.2f}</gross>
                    <property-reference>{property_ref}</property-reference>
                    <heading-unique-id>{fund_heading_uid}</heading-unique-id>
                </detail>
            </post-journal>
        </request-to-qube>
    </web:Data>
</web:QubeProcess-1ia>"""
        data = self.add_soap_envelope(body)

        response = self.make_request(
            "http://qube.qubeglobal.com/ns/webservice/QubeProcess-1ia", data
        )
        return response


# Client authenticates and generates a session


class QubePMPLAPIClient(QubePMPLAPICommon):
    def __init__(
        self,
        base_url: str,
        username: str,
        password: str,
        group: str,
    ):
        self.username = username
        self.password = password
        self.group = group
        super().__init__(base_url=base_url)

    # Login method, authenticates and returns a session object.

    def login(self, client_session_key: str = str(uuid.uuid4())):
        body: str = f"""<web:Login-Overload-4>
    <!--Optional:-->
    <web:LoginData>
        <logondata userdirectory="" xmlns="">
            <clientsessionkey>{client_session_key}</clientsessionkey>
            <username>{self.username}</username>
            <password>{self.password}</password>
            <group>{self.group}</group>
            <application>Purchase Ledger</application>
            <timeoutinterval>1000</timeoutinterval>
        </logondata>
    </web:LoginData>
</web:Login-Overload-4>"""

        data = self.add_soap_envelope(body)

        response = self.make_request(
            "http://qube.qubeglobal.com/ns/webservice/Login-Overload-4", data
        )
        return response

    def get_session(self) -> QubePMPLAPISession:
        client_session_key = str(uuid.uuid4())
        login_response = self.login(client_session_key=client_session_key)
        # Check response xml for <status error-message=""> & raise exception if login failed
        root = ET.fromstring(login_response.content)
        status = root.find(".//status")
        if status is not None and status.get("error-message"):
            raise Exception(
                f"Session creation failed: ErrorCode[{status.get('error-code')}] {status.get('error-message')}"
            )
        session = QubePMPLAPISession(
            client_session_key=client_session_key, base_url=self.base_url
        )
        return session
