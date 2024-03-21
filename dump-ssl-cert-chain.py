#!/usr/bin/env python3

import socket
import ssl
import sys
import tempfile

import certifi
import OpenSSL
import requests
from cryptography.hazmat.primitives import serialization
from cryptography.x509 import (
    DNSName,
    load_der_x509_certificate,
    load_der_x509_crl,
    load_pem_x509_certificate,
    load_pem_x509_certificates,
    load_pem_x509_crl,
)
from cryptography.x509.extensions import CRLDistributionPoints
from cryptography.x509.verification import PolicyBuilder, Store
from rich import print

session = requests.Session()


def get_certificate_chain(host, port: int = 443):
    # Create a socket and wrap it in an SSL context
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    context = OpenSSL.SSL.Context(OpenSSL.SSL.TLS_METHOD)
    connection = OpenSSL.SSL.Connection(context, sock)

    # Connect and perform the handshake to retrieve the certificate chain
    connection.connect((host, port))
    connection.do_handshake()
    chain = connection.get_peer_cert_chain()
    certs = [cert.to_cryptography() for cert in chain]
    chain_crls = []
    for cert in certs:
        for ext in cert.extensions:
            if isinstance(ext.value, CRLDistributionPoints):
                for dist_point in ext.value:
                    for crl_url in dist_point.full_name:
                        resp = session.get(crl_url.value)
                        crl_blob = resp.content
                        try:
                            crl = load_der_x509_crl(crl_blob)
                        except Exception:
                            try:
                                crl = load_pem_x509_crl(crl_blob)
                            except Exception:
                                continue
                        pem_crl = crl.public_bytes(encoding=serialization.Encoding.PEM).decode()
                        chain_crls.append(pem_crl)

    # Convert the chain to PEM format
    pem_chain = [cert.public_bytes(serialization.Encoding.PEM).decode() for cert in certs]

    # Close the connection
    connection.shutdown()
    connection.close()

    return pem_chain, chain_crls


hostname = sys.argv[1]

with open(certifi.where(), "rb") as pems:
    store = Store(load_pem_x509_certificates(pems.read()))

builder = PolicyBuilder().store(store)
verifier = builder.build_server_verifier(DNSName(hostname))

context = ssl.create_default_context()
context.load_verify_locations(cafile=certifi.where())
print(f"context cert store stats: {context.cert_store_stats()}")
chain_certs, chain_crls = get_certificate_chain(hostname)
for cert in chain_certs:
    context.load_verify_locations(cadata=cert)
for pem_crl in chain_crls:
    with tempfile.NamedTemporaryFile(mode="w", suffix=".pem") as f:
        f.write(pem_crl)
        f.flush()
        context.load_verify_locations(cafile=f.name)
print(f"context cert store stats: {context.cert_store_stats()}")

with socket.create_connection((hostname, 443)) as sock:
    with context.wrap_socket(sock, server_hostname=hostname) as ssock:
        tls_version = ssock.version()
        cert_dict = ssock.getpeercert()
        cert_bin = ssock.getpeercert(binary_form=True)

print(f"TLS version: {tls_version}")
print("Certificate:")
print(cert_dict)

# NOTE: peer and untrusted_intermediates are Certificate and
# list[Certificate] respectively, and should be loaded from the
# application context that needs them verified, such as a
# TLS socket.
peer = load_der_x509_certificate(cert_bin)
untrusted_intermediates = [load_pem_x509_certificate(cert.encode()) for cert in chain_certs[1:]]
chain = verifier.verify(peer, untrusted_intermediates)
print(chain)
for i, cert in enumerate(chain):
    with open(f"ssl-cert-chain-{i}.pem", "w") as f:
        f.write(cert.public_bytes(serialization.Encoding.PEM).decode())
