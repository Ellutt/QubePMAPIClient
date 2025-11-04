import uuid
import requests
import xml.etree.ElementTree as ET

##############################################
# SOAP client for Qube PM Purchase Ledger API
##############################################

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

    def __init__(self, client_session_key: str = str(uuid.uuid4()), base_url: str = "https://partner-portals.qubeglobalcloud.com/qubews/"):
        self.client_session_key: str = client_session_key
        super().__init__(base_url=base_url)

    # destructor, calls logout on deletion
    def __del__(self):
        self.logout()

    # Ends the session by calling the Logout API method.
    def logout(self):
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
    def close_report(self):
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
    def get_users(self, ref: str = "?", exact: bool = False):
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
            raise Exception(f"Session creation failed: ErrorCode[{status.get('error-code')}] {status.get('error-message')}")
        session = QubePMPLAPISession(client_session_key=client_session_key, base_url=self.base_url)
        return session
