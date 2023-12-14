"""
UCS CIMC Certificate Renewal Tool
Author: Ugo Emekauwa
Contact: uemekauw@cisco.com, uemekauwa@gmail.com
Summary: The UCS CIMC Certificate Renewal Tool automates the process of
         generating a new standard or self-signed certificate signing request
         for the Cisco Integrated Management Controller (CIMC) of Cisco UCS
         C-Series and HyperFlex servers.
GitHub Repository: https://github.com/ugo-emekauwa/ucs-cimc-csr-tool
"""


########################
# MODULE REQUIREMENT 1 #
########################
"""
Provide the required configuration settings. Remove the sample
values and replace them with your own, where applicable.
"""

####### Start Configuration Settings - Provide values for the variables listed below. #######

# General Settings
## Provide a list of IP addresses or hostnames for all UCS CIMCs that need a new certificate signing request (standard or self-signed).
ucs_cimc_server_list = ["hx-edge-cimc-01","hx-edge-cimc-02","hx-edge-cimc-03",]

## Provide the authentication credentials for the UCS CIMCs.
## If providing more than one UCS CIMC, the credentials must be the same.
ucs_cimc_username = "admin"
ucs_cimc_password = "C1sco12345"

# General Certificate Settings
request_self_signed_certificate = True
replace_common_name_with_ucs_cimc_server_list_entries = True

# Self-Signed Certificate Signing Request Settings
self_signed_csr_common_name = "localhost"
self_signed_csr_organization = "Cisco (Self-Signed)"
self_signed_csr_organizational_unit = "Sales"
self_signed_csr_locality = "San Jose"
self_signed_csr_state = "California"
self_signed_csr_country_code = "United States"

# Standard Certificate Signing Request Settings
## NOTE: Creates CSR file/s for later submission to a certificate authority.
## Ensure that the variable 'self_signed' is set to False in 'General Certificate Settings' above.
csr_common_name = "localhost"
csr_organization = "Cisco"
csr_organizational_unit = "Sales"
csr_locality = "San Jose"
csr_state = "California"
csr_country_code = "United States"
csr_email = ""
csr_remote_server = "198.18.133.94"
csr_remote_server_protocol = "scp"       # Options: ftp, sftp, tftp, scp, none
csr_remote_server_user = "root"
csr_remote_server_password = "C1sco12345"
csr_remote_server_filepath = "/root/tmp/"     # Example: /root/sample_folder/
csr_remote_server_file_extension = ".txt"
csr_signature_algorithm = "sha384"       # Options: sha1, sha256, sha384, sha512

####### Finish Configuration Settings - The required value entries are complete. #######


#############################################################################################################################
#############################################################################################################################


import sys
import traceback
import json
import copy
import re
import requests
import urllib3
import time
import xml.etree.ElementTree as et

# Suppress InsecureRequestWarning error messages
urllib3.disable_warnings()

# Establish function to login to UCS CIMC
def _request_ucs_cimc_login(
    ucs_cimc_server,
    ucs_cimc_username,
    ucs_cimc_password
    ):
    """This is a function to request an HTTP response for a login to a UCS
    CIMC.

    Args:
        ucs_cimc_server (str):
            The hostname or IP address of the UCS CIMC.
        ucs_cimc_username (str):
            The admin username of the UCS CIMC.
        ucs_cimc_password (str):
            The admin password of the UCS CIMC.

    Returns:
        A Response class instance for the UCS CIMC Device
        Console login HTTP request.

    Raises:
        Exception:
            An exception occurred due to an issue with the UCS CIMC
            login HTTP request.
    """
    # Login to UCS CIMC
    ucs_cimc_headers = {
        "Content-Type": "application/xml"
        }
    ucs_cimc_url = f"https://{ucs_cimc_server}/nuova"
    ucs_cimc_post_body = f"""<aaaLogin inName='{ucs_cimc_username}' inPassword='{ucs_cimc_password}'></aaaLogin>"""
    try:
        ucs_cimc_login_request = requests.post(
            ucs_cimc_url,
            headers=ucs_cimc_headers,
            data=ucs_cimc_post_body,
            verify=False
            )
        return ucs_cimc_login_request
    except Exception as exception_message:
        print("\nA configuration error has occurred!\n")
        print(f"Unable to login to the UCS CIMC for "
              f"{ucs_cimc_server}.\n")
        print("Exception Message: ")
        print(exception_message)
         

# Establish function to obtain UCS CIMC login cookie
def _obtain_ucs_cimc_login_cookie(
    ucs_cimc_server,
    ucs_cimc_username,
    ucs_cimc_password
    ):
    """This is a function to login to a UCS CIMC and obtain the cookies for
    the login session.

    Args:
        ucs_cimc_server (str):
            The hostname or IP address of the UCS CIMC.
        ucs_cimc_username (str):
            The admin username of the UCS CIMC.
        ucs_cimc_password (str):
            The admin password of the UCS CIMC.

    Returns:
        A string of the cookie from a Response class instance of a UCS CIMC 
        login HTTP request.

    Raises:
        Exception:
            An exception occurred due to an issue with accessing the provided
            UCS CIMC.
    """
    try:
        # Login to UCS CIMC
        print(f"\nLogging in to {ucs_cimc_server}...")
        ucs_cimc_login = _request_ucs_cimc_login(
            ucs_cimc_server,
            ucs_cimc_username,
            ucs_cimc_password
            )
        ucs_cimc_login_text = ucs_cimc_login.text
        ucs_cimc_login_xml_string_response = et.fromstring(ucs_cimc_login_text)
        ucs_cimc_login_cookie = ucs_cimc_login_xml_string_response.attrib.get("outCookie")
        if ucs_cimc_login_cookie:
            return ucs_cimc_login_cookie
        else:
            print("\nA configuration error has occurred!\n")
            print("Unable to retrieve the login cookie for "
                  f"{ucs_cimc_server}.\n")
            print("Exception Message: ")
            print(ucs_cimc_login_xml_string_response.attrib)
    except Exception:
        print("\nA configuration error has occurred!\n")
        print(f"Unable to login to {ucs_cimc_server}.\n")
        print("Exception Message: ")
        traceback.print_exc()
         

# Establish function to logout of UCS CIMC
def _request_ucs_cimc_logout(
    ucs_cimc_server,
    ucs_cimc_login_cookie
    ):
    """This is a function to logout of a UCS CIMC.

    Args:
        ucs_cimc_server (str):
            The hostname or IP address of the UCS CIMC.
        ucs_cimc_login_cookie (str):
            A string of the cookie from a Response class instance of a UCS CIMC 
            login HTTP request.
            
    Returns:
        A Response class instance for the UCS CIMC logout HTTP request.

    Raises:
        Exception:
            An exception occurred due to an issue with the UCS CIMC
            logout HTTP request.
    """
    # Logout of UCS CIMC
    ucs_cimc_headers = {
        "Content-Type": "application/xml"
        }
    ucs_cimc_url = f"https://{ucs_cimc_server}/nuova"
    ucs_cimc_post_body = f"""<aaaLogout cookie='{ucs_cimc_login_cookie}' inCookie='{ucs_cimc_login_cookie}'></aaaLogout>"""
    try:
        ucs_cimc_logout_request = requests.post(
            ucs_cimc_url,
            headers=ucs_cimc_headers,
            data=ucs_cimc_post_body,
            verify=False
            )
        return ucs_cimc_logout_request
    except Exception as exception_message:
        print("\nA configuration error has occurred!\n")
        print(f"Unable to logout of the UCS CIMC for "
              f"{ucs_cimc_server}.\n")
        print("Exception Message: ")
        print(exception_message)
         

# Establish function to generate UCS CIMC self-signed certificate
def generate_ucs_cimc_self_signed_certificate(
    ucs_cimc_server,
    ucs_cimc_username,
    ucs_cimc_password,
    common_name="localhost",
    organization="Cisco (Self-Signed)",
    organizational_unit="Sales",
    locality="San Jose",
    state="California",
    country_code="United States"
    ):
    """"This is a function to generate a self-signed certificate for the UCS
    CIMC.

    Args:
        ucs_cimc_server (str):
            The hostname or IP address of the UCS CIMC.
        ucs_cimc_username (str):
            The admin username of the UCS CIMC.
        ucs_cimc_password (str):
            The admin password of the UCS CIMC.
        common_name (str):
            The common name (CN) for the certificate signing request. The
            default value is "localhost".
        organization (str):
            The organization for the certificate signing request. The
            default value is "Cisco (Self-Signed)".
        organizational_unit (str):
            The organizational unit for the certificate signing request. The
            default value is "Sales".
        locality (str):
            The locality for the certificate signing request. The
            default value is "San Jose".
        state (str):
            The state for the certificate signing request. The
            default value is "California".
        country_code (str):
            The country code for the certificate signing request. The
            default value is "United States".

    Returns:
        A Response class instance for the UCS CIMC self-signed certificate
        HTTP request.

    Raises:
        Exception:
            An exception occurred due to an issue with the UCS CIMC
            self-signed certificate HTTP request.
    """
    # Login to UCS CIMC and retrieve login cookie
    ucs_cimc_login_cookie = _obtain_ucs_cimc_login_cookie(
        ucs_cimc_server,
        ucs_cimc_username,
        ucs_cimc_password
        )
    
    # Generate a Self-Signed Certificate
    ucs_cimc_headers = {
        "Content-Type": "application/xml"
        }
    ucs_cimc_url = f"https://{ucs_cimc_server}/nuova"
    ucs_cimc_post_body = f"""<configConfMo cookie='{ucs_cimc_login_cookie}' dn='sys/cert-mgmt/gen-csr-req' inHierarchical='false'>
<inConfig>
<generateCertificateSigningRequest
commonName='{common_name}'
organization='{organization}'
organizationalUnit='{organizational_unit}'
locality='{locality}'
state='{state}'
countryCode='{country_code}'
dn='sys/cert-mgmt/gen-csr-req'
selfSigned='yes'
/>
</inConfig>
</configConfMo>"""
    print("\nGenerating the self-signed certificate...")
    try:
        ucs_cimc_self_signed_certificate_generation_request = requests.post(
            ucs_cimc_url,
            headers=ucs_cimc_headers,
            data=ucs_cimc_post_body,
            verify=False
            )
        print(f"- Self-Signed Certificate Signing Request Status Code: {ucs_cimc_self_signed_certificate_generation_request.status_code}")
        print(f"- Self-Signed Certificate Signing Request Response: {ucs_cimc_self_signed_certificate_generation_request.text}")

        # Logout of UCS CIMC
        print(f"Logging out of {ucs_cimc_server}...")
        _request_ucs_cimc_logout(
            ucs_cimc_server,
            ucs_cimc_login_cookie
            )
        
        return ucs_cimc_self_signed_certificate_generation_request
    except Exception as exception_message:
        print("\nA configuration error has occurred!\n")
        print(f"Unable to complete generating a self-signed certificate for "
              f"{ucs_cimc_server}.\n")
        print("Exception Message: ")
        traceback.print_exc()


# Establish function to generate UCS CIMC certificate signing request
def generate_ucs_cimc_certificate_signing_request(
    ucs_cimc_server,
    ucs_cimc_username,
    ucs_cimc_password,
    common_name="localhost",
    organization="Cisco",
    organizational_unit="Sales",
    locality="San Jose",
    state="California",
    country_code="United States",
    email="",
    remote_server="",
    remote_server_protocol="none",
    remote_server_user="",
    remote_server_password="",
    remote_server_filepath="",
    remote_server_file_extension=".txt",
    signature_algorithm="sha384"
    ):
    """"This is a function to generate a certificate signing request (CSR) for
    the UCS CIMC.

    Args:
        ucs_cimc_server (str):
            The hostname or IP address of the UCS CIMC.
        ucs_cimc_username (str):
            The admin username of the UCS CIMC.
        ucs_cimc_password (str):
            The admin password of the UCS CIMC.
        common_name (str):
            The common name (CN) for the certificate signing request. The
            default value is "localhost".
        organization (str):
            The organization for the certificate signing request. The
            default value is "Cisco (Self-Signed)".
        organizational_unit (str):
            The organizational unit for the certificate signing request. The
            default value is "Sales".
        locality (str):
            The locality for the certificate signing request. The
            default value is "San Jose".
        state (str):
            The state for the certificate signing request. The
            default value is "California".
        country_code (str):
            The country code for the certificate signing request. The
            default value is "United States".
        email (str):
            The email address for the certificate signing request. The
            default value is an empty string ("").
        remote_server (str):
            The IP address or hostname of the remote server to store the
            certificate signing request. The default value is an empty string
            ("").
        remote_server_protocol (str):
            The protocol used to access the remote server when storing the
            certificate signing request. The options are ftp, sftp, tftp, scp
            and none. The default value is "none".
        remote_server_user (str):
            The username for the remote server. The default value is an empty
            string ("").
        remote_server_password (str):
            The password for the remote server. The default value is an empty
            string ("").
        remote_server_filepath (str):
            The filepath on the remote server for storing the certificate
            signing request. An example is "/root/sample_folder/". The default
            value is an empty string ("").
        remote_server_file_extension (str):
            The file extension for the certificate signing request when stored
            on the remote server. The default value is ".txt".
        signature_algorithm (str):
            The signature algorithm for the certificate signing request. The
            options are sha1, sha256, sha384 and sha512. The default value is
            "sha384".

    Returns:
        A Response class instance for the UCS CIMC CSR HTTP request.

    Raises:
        Exception:
            An exception occurred due to an issue with the UCS CIMC CSR HTTP
            request.
    """
    # Login to UCS CIMC and retrieve login cookie
    ucs_cimc_login_cookie = _obtain_ucs_cimc_login_cookie(
        ucs_cimc_server,
        ucs_cimc_username,
        ucs_cimc_password
        )
    
    # Generate a Self-Signed Certificate
    ucs_cimc_headers = {
        "Content-Type": "application/xml"
        }
    ucs_cimc_url = f"https://{ucs_cimc_server}/nuova"
    ucs_cimc_post_body = f"""<configConfMo cookie='{ucs_cimc_login_cookie}' dn='sys/cert-mgmt/gen-csr-req' inHierarchical='false'>
<inConfig>
<generateCertificateSigningRequest
commonName='{common_name}'
organization='{organization}'
organizationalUnit='{organizational_unit}'
locality='{locality}'
state='{state}'
countryCode='{country_code}'
email='{email}'
protocol='{remote_server_protocol}'
remoteServer='{remote_server}'
user='{remote_server_user}'
pwd='{remote_server_password}'
remoteFile='{remote_server_filepath}{common_name}-csr{remote_server_file_extension}'
signatureAlgorithm='{signature_algorithm}'
dn='sys/cert-mgmt/gen-csr-req'
/>
</inConfig>
</configConfMo>"""
    if not email:
        ucs_cimc_post_body = ucs_cimc_post_body.replace("\nemail=''", "")
    if not remote_server:
        ucs_cimc_post_body = ucs_cimc_post_body.replace("\nremoteServer=''", "")
    if not remote_server_filepath:
        ucs_cimc_post_body = ucs_cimc_post_body.replace("\nremoteFile=''", "")
    print("\nGenerating the certificate signing request...")
    try:
        ucs_cimc_certificate_signing_request = requests.post(
            ucs_cimc_url,
            headers=ucs_cimc_headers,
            data=ucs_cimc_post_body,
            verify=False
            )
        print(f"- Certificate Signing Request Status Code: {ucs_cimc_certificate_signing_request.status_code}")
        print(f"- Certificate Signing Request Response: {ucs_cimc_certificate_signing_request.text}")

        # Logout of UCS CIMC
        print(f"Logging out of {ucs_cimc_server}...")
        _request_ucs_cimc_logout(
            ucs_cimc_server,
            ucs_cimc_login_cookie
            )
        
        return ucs_cimc_certificate_signing_request
    except Exception as exception_message:
        print("\nA configuration error has occurred!\n")
        print(f"Unable to complete the certificate signing request for "
              f"{ucs_cimc_server}.\n")
        print("Exception Message: ")
        traceback.print_exc()


def main():
    # Starting the UCS CIMC Certificate Renewal Tool
    print(f"\nStarting the UCS CIMC Certificate Renewal Tool.")

    # Cycle through the provided UCS CIMC server list and perform the certificate signing requests
    if ucs_cimc_server_list:
        for ucs_cimc_server in ucs_cimc_server_list:
            if request_self_signed_certificate:
                if replace_common_name_with_ucs_cimc_server_list_entries:
                    self_signed_csr_common_name = ucs_cimc_server
                try:
                    generate_ucs_cimc_self_signed_certificate(
                        ucs_cimc_server=ucs_cimc_server,
                        ucs_cimc_username=ucs_cimc_username,
                        ucs_cimc_password=ucs_cimc_password,
                        common_name=self_signed_csr_common_name,
                        organization=self_signed_csr_organization,
                        organizational_unit=self_signed_csr_organizational_unit,
                        locality=self_signed_csr_locality,
                        state=self_signed_csr_state,
                        country_code=self_signed_csr_country_code
                        )   
                except Exception:
                    print("\nA configuration error has occurred!\n")
                    print("There was an issue creating the self-signed "
                          f"certificate for {ucs_cimc_server}.\n")
                    print("Exception Message: ")
                    traceback.print_exc()
            else:
                if replace_common_name_with_ucs_cimc_server_list_entries:
                    csr_common_name = ucs_cimc_server
                try:
                    generate_ucs_cimc_certificate_signing_request(
                        ucs_cimc_server=ucs_cimc_server,
                        ucs_cimc_username=ucs_cimc_username,
                        ucs_cimc_password=ucs_cimc_password,
                        common_name=csr_common_name,
                        organization=csr_organization,
                        organizational_unit=csr_organizational_unit,
                        locality=csr_locality,
                        state=csr_state,
                        country_code=csr_country_code,
                        email=csr_email,
                        remote_server=csr_remote_server,
                        remote_server_protocol=csr_remote_server_protocol,
                        remote_server_user=csr_remote_server_user,
                        remote_server_password=csr_remote_server_password,
                        remote_server_filepath=csr_remote_server_filepath,
                        remote_server_file_extension=csr_remote_server_file_extension,
                        signature_algorithm=csr_signature_algorithm
                        )   
                except Exception:
                    print("\nA configuration error has occurred!\n")
                    print("There was an issue creating the certificate signing "
                          f"request for {ucs_cimc_server}.\n")
                    print("Exception Message: ")
                    traceback.print_exc()
    else:
        print("\nThere are no certificate signing requests to perform.")
        print("There were no UCS CIMC servers provided.")

    # UCS CIMC Certificate Renewal Tool completion
    print(f"\nThe UCS CIMC Certificate Renewal Tool has completed.\n")


if __name__ == "__main__":
    main()

# Exiting the UCS CIMC Certificate Renewal Tool
sys.exit(0)
