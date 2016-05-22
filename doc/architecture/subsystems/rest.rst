RESTful Server
===============

The builtin REST Server provides methods to request, renew and revoke 
certificates. The service is implemented using a cgi-wrapper script with 
a rewrite module (e.g. mod_rewrite).

t.b.d. rewrite


Wrapper Configuration
---------------------

The default wrapper looks for its config file at ``/etc/openxpki/rest/default.conf``.
The config uses plain ini format, a default is deployed by the package::

  [global]
  log_config = /etc/openxpki/rest/log.conf
  log_facility = client.rest
  socket = /var/openxpki/openxpki.socket

  [auth]
  stack = _System
  pki_realm = ca-one


Endpoint Configuration
----------------------

Based on the given servername, a rules file is loaded for the server.
You can define the rules for the signer authorization here::

  authorized_signer:
      rule1:
          subject: CN=.+:soapclient,.*
      rule2:    
          subject: CN=.+:pkiclient,.*

Authentication
--------------

The default configuration exposes the API without enforcing authentication,
but evaluates the apache environment variables for traces of HTTP Basic 
Authentication (HTTP_USER) or TLS Client Authentication (SSL_CLIENT_S_DN).

Ressource updates are always turned into OpenXPKI workflows, with the found
authentication information passed to them.

@todo: Explain how auth works for SOAP and REST in new chapter


Exposed Methods
---------------

The default is to expect/return JSON formatted data but some methods will
accept/return other formats, too. The REST API mostly follows the ideas
from the "RESTful Web Services Cookbook" published by O'Reilly.

Retrieve/Update Information on existing Certificates
#####################################################

Each certificate is identified by the URI::

    /restapi/certificate/<serialnumber>

where serialnumber is in lowercased, hexadecimal notation without colons. 
Requests with uppercased letters and/or colons will result in a redirection
header to the normalized form, so you might use this notation if your client
supports internal redirection.
 
Basic Request
+++++++++++++

A GET request to above URI returns the basic certificate information::

  GET /restapi/certificate/<serialnumber>

  {
      
  }

Retrieve Certificate
++++++++++++++++++++

Append /pem to the base URI to receive the certificate in PEM encoding::

  GET /restapi/certificate/<serialnumber>/pem

  Content-Type: application/pkcs10
  -----BEGIN CERTIFICATE-----
  MIIDYDCCAkigAwIBAgIJAJt0TR1VxElUMA0GCSqGSIb3DQEBCwUAMDcxITAfBgoJ
  ......
  GQ6Q==
  -----END CERTIFICATE-----

Use /binary to get the DER encoded certificate, the Content-Type of the
response will be application/x-x509-user-cert.

Certificate Revocation Status
++++++++++++++++++++++++++++++

Append /revocation_status to the base URI to determine the revocation 
status of a certificate::

  GET /restapi/certificate/<serialnumber>/revocation_status

If the certificate was not revoked, you will receive a "204 No Content" 
return code, which reads as: There is no revocation information, so the
certificate is still valid.

If the certificate is revoked, you will get the reason code and revocation
time::

  {
    "crr_serial": 7167,
    "invalidity_time": "2016-07-22 23:42:26Z",
    "reason_code": "cessationOfOperation",
    "comment": "A verbose comment"
  }

Note: This represents the internal state of the PKI, if no CRL was issued
after handling the revocation request, the certificate obviously wont be on
the current CRL.

To request the revocation of a certificate, use a POST request to update the 
revocation status information::

  POST /restapi/certificate/<serialnumber>/revocation_status
  {
    "invalidity_time": "2016-07-22 23:42:26Z",
    "reason_code": "cessationOfOperation",
    "comment": "A verbose comment"
  }

You can send an empty body or empty JSON array, which will create a 
revocation request using the default reason_code "unspecified" and set the
invalidity_time to now.

If the revocation request can be completed instantly, you will receive the
new revocation status as stated above. If the request can not be completed,
e.g. due to required approvals, you will receive a "202 Accepted" code with
a transaction id (see asynchronous tasks below).


Request a Certificate
+++++++++++++++++++++

You can create a certificate signing request sending your pem encoded PKCS10
request via POST, Content-Type must be set to application/pkcs10::

  POST /restapi/certificate/
  Content-Type: application/pkcs10
  -----BEGIN CERTIFICATE REQUEST-----
  MIIDYDCCAkigAwIBAgIJAJt0TR1VxElUMA0GCSqGSIb3DQEBCwUAMDcxITAfBgoJ
  ......
  GQ6Q==
  -----END CERTIFICATE REQUEST-----

All mandatory information must be contained in the CSR, no additonal 
information is processed. If you need to pass additional information, you 
can send your request with the following JSON array::

  {
  }


As JSON does not support multiline strings, the header/footer lines and line
endings need to be removed.
 
If the certificate is issued instantly, you will receive a 302 redirect to
the new certificate status location (/restapi/certificate/<serialnumber>).
If the requests is send into a pending state, you will receive a 
"202 Accepted" with a transaction id (see asynchronous tasks below).



Handling of Asynchronous Tasks
------------------------------
 








