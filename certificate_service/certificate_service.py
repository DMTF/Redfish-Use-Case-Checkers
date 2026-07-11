# Copyright Notice:
# Copyright 2017-2023 Distributed Management Task Force, Inc. All rights reserved.
# License: BSD 3-Clause License. For full text see link: https://github.com/DMTF/Redfish-Usecase-Checkers/blob/main/LICENSE.md

"""
Certificate Service Usecase Test

File : certificate_service.py

Brief : This file contains the definitions and functionalities for performing
        the usecase test for the certificate service
"""

import argparse
import sys

import redfish
import redfish_utilities

import toolspath
from usecase.results import Results

if __name__ == "__main__":

    # Get the input arguments
    argget = argparse.ArgumentParser( description = "Usecase checker for account management" )
    argget.add_argument( "--user", "-u", type = str, required = True, help = "The user name for authentication" )
    argget.add_argument( "--password", "-p",  type = str, required = True, help = "The password for authentication" )
    argget.add_argument( "--rhost", "-r", type = str, required = True, help = "The address of the Redfish service" )
    argget.add_argument( "--Secure", "-S", type = str, default = "Always", help = "When to use HTTPS (Always, IfSendingCredentials, IfLoginOrAuthenticatedApi, Never)" )
    argget.add_argument( "--directory", "-d", type = str, default = None, help = "Output directory for results.json" )
    args = argget.parse_args()

    # Set up the Redfish object
    base_url = "https://" + args.rhost
    if args.Secure == "Never":
        base_url = "http://" + args.rhost
    with redfish.redfish_client( base_url = base_url, username = args.user, password = args.password ) as redfish_obj:
        # Create the results object
        service_root = redfish_obj.get( "/redfish/v1/" )
        results = Results( "Certificate Service", service_root.dict )
        if args.directory is not None:
            results.set_output_dir( args.directory )

        if "CertificateService" not in service_root.dict:
            # Nothing to test; skip everything
            results.update_test_results( "Certificate Locations", 0, "Certificate service not supported.", skipped = True )
            results.update_test_results( "Generate CSR Info", 0, "Certificate service not supported.", skipped = True )
            results.update_test_results( "Generate CSR Algorithms", 0, "Certificate service not supported.", skipped = True )
            results.update_test_results( "Generate CSR", 0, "Certificate service not supported.", skipped = True )
        else:
            csr_parameters = None
            manager_https_cert_col = None
            skip_gen_csr = False

            # Find all certificates
            try:
                certificates = redfish_utilities.get_all_certificates( redfish_obj )
                if len( certificates ) == 0:
                    results.update_test_results( "Certificate Locations", 1, "CertificateLocations resource does not contain any certificates." )
                else:
                    results.update_test_results( "Certificate Locations", 0, None )

                # Find a manager certificate for testing later
                for cert in certificates:
                    if "/NetworkProtocol/HTTPS/Certificates/" in cert["URI"]:
                        manager_https_cert_col = cert["URI"].rsplit( "/", 1 )[0]
            except Exception as err:
                results.update_test_results( "Certificate Locations", 1, "Could not get certificates from the CertificatesLocation resource ({}).".format( err ) )

            # Find the GenerateCSR action info
            try:
                csr_uri, csr_parameters = redfish_utilities.get_generate_csr_info( redfish_obj )
                if csr_parameters is None:
                    results.update_test_results( "Generate CSR Info", 1, "GenerateCSR does not contain any action info." )
                else:
                    results.update_test_results( "Generate CSR Info", 0, None )
            except Exception as err:
                results.update_test_results( "Generate CSR Info", 0, "GenerateCSR action not found.", skipped = True )
                skip_gen_csr = True

            # Inspect the supported algorithms in the GenerateCSR action
            if csr_parameters is None:
                results.update_test_results( "Generate CSR Algorithms", 0, "No GenerateCSR parameters to check", skipped = True )
            else:
                key_pair_alg_found = False
                key_pair_alg_pass = True
                for param in csr_parameters:
                    if param["Name"] == "KeyPairAlgorithm":
                        key_pair_alg_found = True
                        if "AllowableValues" not in param:
                            results.update_test_results( "Generate CSR Algorithms", 1, "No allowable values listed for the KeyPairAlgorithm parameter" )
                            key_pair_alg_pass = False
                        else:
                            for value in param["AllowableValues"]:
                                if value not in [ "TPM_ALG_RSA", "TPM_ALG_ECDSA" ]:
                                    results.update_test_results( "Generate CSR Algorithms", 1, "KeyPairAlgorithm allows for non-recommended algorithm {}".format( value ) )
                                    key_pair_alg_pass = False
                        break
                if not key_pair_alg_found:
                    results.update_test_results( "Generate CSR Algorithms", 0, "GenerateCSR does not support specifying KeyPairAlgorithm", skipped = True )
                elif key_pair_alg_pass:
                    results.update_test_results( "Generate CSR Algorithms", 0, None )

            # Test the GenerateCSR action
            if skip_gen_csr:
                results.update_test_results( "Generate CSR", 0, "GenerateCSR action not found.", skipped = True )
            elif manager_https_cert_col is None:
                results.update_test_results( "Generate CSR", 0, "Could not find manager HTTPS certificate collection for testing the GenerateCSR action.", skipped = True )
            else:
                try:
                    response = redfish_utilities.generate_csr( redfish_obj, "Contoso Common Name", "Contoso", "Contoso Unit", "Portland", "OR", "US", manager_https_cert_col )
                    response = redfish_utilities.poll_task_monitor( redfish_obj, response )
                    redfish_utilities.verify_response( response )
                    if "CSRString" in response.dict:
                        if "-----BEGIN CERTIFICATE REQUEST-----" not in response.dict["CSRString"] and "-----END CERTIFICATE REQUEST-----" not in response.dict["CSRString"]:
                            results.update_test_results( "Generate CSR", 1, "GenerateCSR response does not contains a PEM-encoded CSR" )
                        else:
                            results.update_test_results( "Generate CSR", 0, None )
                    else:
                        results.update_test_results( "Generate CSR", 1, "GenerateCSR response does not contain the property CSRString" )
                except Exception as err:
                    results.update_test_results( "Generate CSR", 1, "Could not produce a CSR for the manager HTTPS certificate collection {} ({}).".format( manager_https_cert_col, err ) )

    # Save the results
    results.write_results()

    sys.exit( results.get_return_code() )
