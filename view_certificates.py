#!/usr/bin/env python3
"""
Digital Certificate Viewer
===========================
Displays detailed information about SSL/TLS certificates used in the project.
"""

import subprocess
import os
from datetime import datetime
from pathlib import Path

# Certificate locations - detect if running in WSL or Windows
import platform
if 'microsoft' in platform.uname().release.lower() or os.path.exists('/mnt/c'):
    # Running in WSL
    CERT_DIR = Path("/mnt/c/Users/iperr/TestZippr/ssl_certs")
else:
    # Running in Windows
    CERT_DIR = Path("C:/Users/iperr/TestZippr/ssl_certs")

CERT_FILE = CERT_DIR / "streamlit.crt"
KEY_FILE = CERT_DIR / "streamlit.key"


def run_openssl_command(args: list) -> str:
    """Run an OpenSSL command and return the output."""
    try:
        result = subprocess.run(
            ["openssl"] + args,
            capture_output=True,
            text=True,
            timeout=30
        )
        return result.stdout if result.returncode == 0 else result.stderr
    except FileNotFoundError:
        return "Error: OpenSSL not found. Please ensure OpenSSL is installed."
    except Exception as e:
        return f"Error: {str(e)}"


def print_header(title: str):
    """Print a formatted header."""
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70)


def print_section(title: str):
    """Print a section header."""
    print(f"\n📋 {title}")
    print("-" * 50)


def get_certificate_info():
    """Get and display certificate information."""
    
    print_header("🔐 DIGITAL CERTIFICATE DETAILS")
    print(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Check if certificates exist
    if not CERT_FILE.exists():
        print(f"\n❌ Certificate not found at: {CERT_FILE}")
        print("   Run 'bash generate_ssl_certs.sh' to create certificates.")
        return
    
    if not KEY_FILE.exists():
        print(f"\n❌ Private key not found at: {KEY_FILE}")
        return
    
    print(f"\n📁 Certificate Location: {CERT_DIR}")
    print(f"   📜 Certificate: {CERT_FILE.name}")
    print(f"   🔑 Private Key: {KEY_FILE.name}")
    
    # Get file stats
    cert_stat = CERT_FILE.stat()
    key_stat = KEY_FILE.stat()
    
    print_section("File Information")
    print(f"  Certificate Size: {cert_stat.st_size} bytes")
    print(f"  Private Key Size: {key_stat.st_size} bytes")
    print(f"  Certificate Modified: {datetime.fromtimestamp(cert_stat.st_mtime).strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"  Private Key Modified: {datetime.fromtimestamp(key_stat.st_mtime).strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Certificate subject and issuer
    print_section("Certificate Subject & Issuer")
    subject = run_openssl_command(["x509", "-in", str(CERT_FILE), "-noout", "-subject"])
    issuer = run_openssl_command(["x509", "-in", str(CERT_FILE), "-noout", "-issuer"])
    print(f"  {subject.strip()}")
    print(f"  {issuer.strip()}")
    
    # Validity period
    print_section("Validity Period")
    dates = run_openssl_command(["x509", "-in", str(CERT_FILE), "-noout", "-dates"])
    for line in dates.strip().split('\n'):
        if line:
            print(f"  {line}")
    
    # Check if expired
    end_date = run_openssl_command(["x509", "-in", str(CERT_FILE), "-noout", "-enddate"])
    if "notAfter=" in end_date:
        date_str = end_date.split("=")[1].strip()
        try:
            # Parse the date (format: Mon DD HH:MM:SS YYYY GMT)
            expiry = datetime.strptime(date_str, "%b %d %H:%M:%S %Y %Z")
            days_remaining = (expiry - datetime.now()).days
            if days_remaining < 0:
                print(f"  ⚠️  STATUS: EXPIRED ({abs(days_remaining)} days ago)")
            elif days_remaining < 30:
                print(f"  ⚠️  STATUS: Expiring soon ({days_remaining} days remaining)")
            else:
                print(f"  ✅ STATUS: Valid ({days_remaining} days remaining)")
        except:
            pass
    
    # Serial number
    print_section("Serial Number")
    serial = run_openssl_command(["x509", "-in", str(CERT_FILE), "-noout", "-serial"])
    print(f"  {serial.strip()}")
    
    # Signature algorithm
    print_section("Signature Algorithm")
    sig_alg = run_openssl_command(["x509", "-in", str(CERT_FILE), "-noout", "-text"])
    for line in sig_alg.split('\n'):
        if "Signature Algorithm:" in line:
            print(f"  {line.strip()}")
            break
    
    # Public key info
    print_section("Public Key Information")
    pubkey = run_openssl_command(["x509", "-in", str(CERT_FILE), "-noout", "-text"])
    in_pubkey_section = False
    for line in pubkey.split('\n'):
        if "Public Key Algorithm:" in line or "Public-Key:" in line:
            print(f"  {line.strip()}")
            in_pubkey_section = True
        elif in_pubkey_section and ("Modulus:" in line or "RSA Public-Key:" in line):
            print(f"  {line.strip()}")
            break
    
    # Fingerprints
    print_section("Certificate Fingerprints")
    sha256 = run_openssl_command(["x509", "-in", str(CERT_FILE), "-noout", "-fingerprint", "-sha256"])
    sha1 = run_openssl_command(["x509", "-in", str(CERT_FILE), "-noout", "-fingerprint", "-sha1"])
    print(f"  SHA-256: {sha256.strip().replace('sha256 Fingerprint=', '').replace('SHA256 Fingerprint=', '')}")
    print(f"  SHA-1:   {sha1.strip().replace('sha1 Fingerprint=', '').replace('SHA1 Fingerprint=', '')}")
    
    # Key verification
    print_section("Key Verification")
    cert_modulus = run_openssl_command(["x509", "-in", str(CERT_FILE), "-noout", "-modulus"])
    key_modulus = run_openssl_command(["rsa", "-in", str(KEY_FILE), "-noout", "-modulus"])
    
    if cert_modulus.strip() == key_modulus.strip():
        print("  ✅ Certificate and private key MATCH")
    else:
        print("  ❌ Certificate and private key DO NOT MATCH")
    
    # Extensions
    print_section("Certificate Extensions")
    text_output = run_openssl_command(["x509", "-in", str(CERT_FILE), "-noout", "-text"])
    in_extensions = False
    for line in text_output.split('\n'):
        if "X509v3 extensions:" in line:
            in_extensions = True
            continue
        if in_extensions:
            if line.strip() and not line.startswith(' ' * 16):
                if "Signature Algorithm:" in line:
                    break
                print(f"  {line.strip()}")
    
    # Certificate purpose
    print_section("Certificate Purpose")
    purpose = run_openssl_command(["x509", "-in", str(CERT_FILE), "-noout", "-purpose"])
    for line in purpose.strip().split('\n')[:6]:  # Show first 6 purposes
        if line.strip():
            print(f"  {line.strip()}")
    
    # Full certificate (PEM format preview)
    print_section("Certificate (PEM Format Preview)")
    with open(CERT_FILE, 'r') as f:
        lines = f.readlines()
        print(f"  {lines[0].strip()}")
        print(f"  ... ({len(lines) - 2} lines of base64 encoded data) ...")
        print(f"  {lines[-1].strip()}")
    
    print("\n" + "=" * 70)
    print("  Certificate analysis complete!")
    print("=" * 70 + "\n")


def main():
    """Main entry point."""
    get_certificate_info()
    
    print("\n💡 Useful Commands:")
    print("-" * 50)
    print("  View full certificate text:")
    print("    openssl x509 -in ssl_certs/streamlit.crt -text -noout")
    print("")
    print("  Verify certificate:")
    print("    openssl verify ssl_certs/streamlit.crt")
    print("")
    print("  Check certificate expiration:")
    print("    openssl x509 -in ssl_certs/streamlit.crt -checkend 86400")
    print("")
    print("  Generate new certificate:")
    print("    bash generate_ssl_certs.sh")
    print("")


if __name__ == "__main__":
    main()

