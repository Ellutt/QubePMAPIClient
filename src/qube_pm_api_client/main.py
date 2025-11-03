import requests

# SOAP client for Qube PM Purchase Ledger API

class QubePMPLAPIClient:
    def __init__(
        self,
        base_url: str,
        client_session_key: str,
        username: str,
        password: str,
        group: str,
    ):
        self.base_url = base_url
        self.client_session_key = client_session_key
        self.username = username
        self.password = password
        self.group = group
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

    def make_request(self, soap_action: str, body: str):
        headers = self.headers.copy()
        headers["SOAPAction"] = soap_action
        response = requests.post(self.base_url, data=body, headers=headers)
        return response
    
    def login(self):
        body: str = f"""<web:Login-Overload-4>
    <!--Optional:-->
    <web:LoginData>
        <logondata userdirectory="" xmlns="">
            <clientsessionkey>{self.client_session_key}</clientsessionkey>
            <username>{self.username}</username>
            <password>{self.password}</password>
            <group>{self.group}</group>
            <application>Purchase Ledger</application>
            <timeoutinterval>1000</timeoutinterval>
        </logondata>
    </web:LoginData>
</web:Login-Overload-4>"""
        
        data = self.add_soap_envelope(body)

        response = self.make_request("http://qube.qubeglobal.com/ns/webservice/Login-Overload-4", data)
        return response
    
    def logout(self, client_session_key: str):
        body = f"""<web:Logout>
    <!--Optional:-->
    <web:ClientSessionKey>{client_session_key}</web:ClientSessionKey>
    </web:Logout>"""
        data = self.add_soap_envelope(body)
        response = self.make_request("http://qube.qubeglobal.com/ns/webservice/Logout", data)
        return response
