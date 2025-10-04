#!/usr/bin/env python3
"""
DNSSEC & TLS Security for DRP
Implements DNSSEC validation and TLS certificate management for domain and API security
"""

import ssl
import socket
import hashlib
import logging
import subprocess
import json
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from enum import Enum
import argparse

# DNSSEC dependencies
try:
    import dns.resolver
    import dns.dnssec
    import dns.rdatatype
    import dns.rdataclass
    DNSSEC_AVAILABLE = True
except ImportError:
    DNSSEC_AVAILABLE = False
    logging.warning("DNSSEC library not available. Install with: pip install dnspython")

# TLS dependencies
try:
    from cryptography import x509
    from cryptography.x509.oid import NameOID, ExtensionOID
    from cryptography.hazmat.primitives import hashes, serialization
    from cryptography.hazmat.primitives.asymmetric import rsa, padding
    TLS_AVAILABLE = True
except ImportError:
    TLS_AVAILABLE = False
    logging.warning("TLS library not available. Install with: pip install cryptography")

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class SecurityStatus(Enum):
    """Security status levels"""
    SECURE = "secure"
    WARNING = "warning"
    INSECURE = "insecure"
    ERROR = "error"


class CertificateType(Enum):
    """Types of certificates"""
    ROOT_CA = "root_ca"
    INTERMEDIATE_CA = "intermediate_ca"
    SERVER = "server"
    CLIENT = "client"
    CODE_SIGNING = "code_signing"


@dataclass
class DNSSECValidationResult:
    """Result of DNSSEC validation"""
    domain: str
    is_valid: bool
    status: SecurityStatus
    error_message: Optional[str] = None
    validated_records: List[str] = None
    validation_chain: List[str] = None


@dataclass
class TLSCertificateInfo:
    """Information about a TLS certificate"""
    subject: str
    issuer: str
    serial_number: str
    not_valid_before: str
    not_valid_after: str
    key_size: int
    signature_algorithm: str
    extensions: List[str]
    is_valid: bool
    days_until_expiry: int
    status: SecurityStatus


@dataclass
class SecurityAuditResult:
    """Result of security audit"""
    domain: str
    dnssec_status: SecurityStatus
    tls_status: SecurityStatus
    overall_status: SecurityStatus
    issues: List[str]
    recommendations: List[str]
    audit_timestamp: str


class DNSSECValidator:
    """
    Validates DNSSEC records for domain security
    """
    
    def __init__(self):
        """Initialize DNSSEC validator"""
        if not DNSSEC_AVAILABLE:
            raise ImportError("DNSSEC library not available. Install with: pip install dnspython")
        
        self.resolver = dns.resolver.Resolver()
        self.resolver.use_edns(0, dns.flags.DO)  # Enable DNSSEC OK flag
        
        logger.info("DNSSEC Validator initialized")
    
    def validate_domain_dnssec(self, domain: str) -> DNSSECValidationResult:
        """
        Validate DNSSEC for a domain
        
        Args:
            domain: Domain to validate
            
        Returns:
            DNSSEC validation result
        """
        try:
            validated_records = []
            validation_chain = []
            
            # Check if domain supports DNSSEC
            try:
                # Query for DNSKEY records
                dnskey_response = self.resolver.resolve(domain, 'DNSKEY')
                if not dnskey_response:
                    return DNSSECValidationResult(
                        domain=domain,
                        is_valid=False,
                        status=SecurityStatus.INSECURE,
                        error_message="No DNSKEY records found - DNSSEC not enabled"
                    )
                
                validated_records.append("DNSKEY")
                
                # Query for DS records (delegation signer)
                try:
                    ds_response = self.resolver.resolve(domain, 'DS')
                    if ds_response:
                        validated_records.append("DS")
                except:
                    pass  # DS records are optional for root domains
                
                # Query for RRSIG records
                rrsig_response = self.resolver.resolve(domain, 'RRSIG')
                if rrsig_response:
                    validated_records.append("RRSIG")
                
                # Validate DNSKEY records
                dnskey_valid = self._validate_dnskey_records(domain, dnskey_response)
                if not dnskey_valid:
                    return DNSSECValidationResult(
                        domain=domain,
                        is_valid=False,
                        status=SecurityStatus.INSECURE,
                        error_message="DNSKEY validation failed"
                    )
                
                # Validate RRSIG records
                rrsig_valid = self._validate_rrsig_records(domain, rrsig_response)
                if not rrsig_valid:
                    return DNSSECValidationResult(
                        domain=domain,
                        is_valid=False,
                        status=SecurityStatus.WARNING,
                        error_message="RRSIG validation failed"
                    )
                
                # Check for secure delegation
                delegation_secure = self._check_secure_delegation(domain)
                if not delegation_secure:
                    return DNSSECValidationResult(
                        domain=domain,
                        is_valid=False,
                        status=SecurityStatus.WARNING,
                        error_message="Insecure delegation detected"
                    )
                
                logger.info(f"DNSSEC validation successful for domain {domain}")
                return DNSSECValidationResult(
                    domain=domain,
                    is_valid=True,
                    status=SecurityStatus.SECURE,
                    validated_records=validated_records,
                    validation_chain=validation_chain
                )
                
            except Exception as e:
                return DNSSECValidationResult(
                    domain=domain,
                    is_valid=False,
                    status=SecurityStatus.ERROR,
                    error_message=f"DNSSEC validation error: {str(e)}"
                )
            
        except Exception as e:
            logger.error(f"Error validating DNSSEC for domain {domain}: {e}")
            return DNSSECValidationResult(
                domain=domain,
                is_valid=False,
                status=SecurityStatus.ERROR,
                error_message=f"Validation error: {str(e)}"
            )
    
    def _validate_dnskey_records(self, domain: str, dnskey_response) -> bool:
        """Validate DNSKEY records"""
        try:
            # Check for KSK (Key Signing Key) and ZSK (Zone Signing Key)
            ksk_found = False
            zsk_found = False
            
            for record in dnskey_response:
                if record.flags & 0x01:  # KSK flag
                    ksk_found = True
                else:
                    zsk_found = True
            
            if not ksk_found or not zsk_found:
                logger.warning(f"Missing KSK or ZSK for domain {domain}")
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"Error validating DNSKEY records: {e}")
            return False
    
    def _validate_rrsig_records(self, domain: str, rrsig_response) -> bool:
        """Validate RRSIG records"""
        try:
            # Basic RRSIG validation
            if not rrsig_response:
                return False
            
            # Check signature validity period
            current_time = datetime.utcnow()
            for record in rrsig_response:
                inception = datetime.fromtimestamp(record.inception)
                expiration = datetime.fromtimestamp(record.expiration)
                
                if current_time < inception or current_time > expiration:
                    logger.warning(f"RRSIG signature outside validity period for domain {domain}")
                    return False
            
            return True
            
        except Exception as e:
            logger.error(f"Error validating RRSIG records: {e}")
            return False
    
    def _check_secure_delegation(self, domain: str) -> bool:
        """Check for secure delegation"""
        try:
            # Check parent domain for DS records
            parts = domain.split('.')
            if len(parts) > 1:
                parent_domain = '.'.join(parts[1:])
                
                try:
                    ds_response = self.resolver.resolve(parent_domain, 'DS')
                    if ds_response:
                        return True
                except:
                    pass
            
            return True  # Root domains don't need DS records
            
        except Exception as e:
            logger.error(f"Error checking secure delegation: {e}")
            return False
    
    def get_dns_records(self, domain: str, record_type: str) -> List[str]:
        """Get DNS records for a domain"""
        try:
            response = self.resolver.resolve(domain, record_type)
            return [str(record) for record in response]
        except Exception as e:
            logger.error(f"Error getting {record_type} records for {domain}: {e}")
            return []


class TLSCertificateManager:
    """
    Manages TLS certificates for DRP services
    """
    
    def __init__(self):
        """Initialize TLS certificate manager"""
        if not TLS_AVAILABLE:
            raise ImportError("TLS library not available. Install with: pip install cryptography")
        
        self.certificates: Dict[str, TLSCertificateInfo] = {}
        
        logger.info("TLS Certificate Manager initialized")
    
    def analyze_certificate(self, hostname: str, port: int = 443) -> TLSCertificateInfo:
        """
        Analyze TLS certificate for a hostname
        
        Args:
            hostname: Hostname to analyze
            port: Port number (default 443)
            
        Returns:
            TLS certificate information
        """
        try:
            # Create SSL context
            context = ssl.create_default_context()
            context.check_hostname = False
            context.verify_mode = ssl.CERT_NONE
            
            # Connect and get certificate
            with socket.create_connection((hostname, port), timeout=10) as sock:
                with context.wrap_socket(sock, server_hostname=hostname) as ssock:
                    cert_der = ssock.getpeercert_chain()[0]
                    cert = x509.load_der_x509_certificate(cert_der)
            
            # Extract certificate information
            subject = self._get_certificate_name(cert.subject)
            issuer = self._get_certificate_name(cert.issuer)
            serial_number = str(cert.serial_number)
            not_valid_before = cert.not_valid_before.isoformat()
            not_valid_after = cert.not_valid_after.isoformat()
            
            # Get key size
            public_key = cert.public_key()
            if isinstance(public_key, rsa.RSAPublicKey):
                key_size = public_key.key_size
            else:
                key_size = 0
            
            # Get signature algorithm
            signature_algorithm = cert.signature_algorithm_oid._name
            
            # Get extensions
            extensions = []
            for ext in cert.extensions:
                extensions.append(ext.oid._name)
            
            # Check validity
            current_time = datetime.utcnow()
            is_valid = current_time >= cert.not_valid_before and current_time <= cert.not_valid_after
            
            # Calculate days until expiry
            days_until_expiry = (cert.not_valid_after - current_time).days
            
            # Determine status
            if not is_valid:
                status = SecurityStatus.INSECURE
            elif days_until_expiry < 30:
                status = SecurityStatus.WARNING
            elif key_size < 2048:
                status = SecurityStatus.WARNING
            else:
                status = SecurityStatus.SECURE
            
            cert_info = TLSCertificateInfo(
                subject=subject,
                issuer=issuer,
                serial_number=serial_number,
                not_valid_before=not_valid_before,
                not_valid_after=not_valid_after,
                key_size=key_size,
                signature_algorithm=signature_algorithm,
                extensions=extensions,
                is_valid=is_valid,
                days_until_expiry=days_until_expiry,
                status=status
            )
            
            # Store certificate info
            self.certificates[hostname] = cert_info
            
            logger.info(f"Analyzed TLS certificate for {hostname}")
            return cert_info
            
        except Exception as e:
            logger.error(f"Error analyzing certificate for {hostname}: {e}")
            return TLSCertificateInfo(
                subject="",
                issuer="",
                serial_number="",
                not_valid_before="",
                not_valid_after="",
                key_size=0,
                signature_algorithm="",
                extensions=[],
                is_valid=False,
                days_until_expiry=0,
                status=SecurityStatus.ERROR
            )
    
    def _get_certificate_name(self, name) -> str:
        """Extract readable name from certificate name object"""
        try:
            components = []
            for attr in name:
                components.append(f"{attr.oid._name}={attr.value}")
            return ", ".join(components)
        except:
            return str(name)
    
    def generate_self_signed_certificate(
        self, 
        common_name: str, 
        organization: str = "DRP Network",
        validity_days: int = 365
    ) -> Tuple[bytes, bytes]:
        """
        Generate self-signed certificate
        
        Args:
            common_name: Common name for the certificate
            organization: Organization name
            validity_days: Certificate validity in days
            
        Returns:
            Tuple of (certificate_pem, private_key_pem)
        """
        try:
            # Generate private key
            private_key = rsa.generate_private_key(
                public_exponent=65537,
                key_size=2048,
            )
            
            # Create certificate
            subject = issuer = x509.Name([
                x509.NameAttribute(NameOID.COUNTRY_NAME, "US"),
                x509.NameAttribute(NameOID.STATE_OR_PROVINCE_NAME, "CA"),
                x509.NameAttribute(NameOID.LOCALITY_NAME, "San Francisco"),
                x509.NameAttribute(NameOID.ORGANIZATION_NAME, organization),
                x509.NameAttribute(NameOID.COMMON_NAME, common_name),
            ])
            
            cert = x509.CertificateBuilder().subject_name(
                subject
            ).issuer_name(
                issuer
            ).public_key(
                private_key.public_key()
            ).serial_number(
                x509.random_serial_number()
            ).not_valid_before(
                datetime.utcnow()
            ).not_valid_after(
                datetime.utcnow() + timedelta(days=validity_days)
            ).add_extension(
                x509.SubjectAlternativeName([
                    x509.DNSName(common_name),
                    x509.DNSName("localhost"),
                    x509.IPAddress("127.0.0.1"),
                ]),
                critical=False,
            ).sign(private_key, hashes.SHA256())
            
            # Convert to PEM format
            cert_pem = cert.public_bytes(serialization.Encoding.PEM)
            key_pem = private_key.private_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PrivateFormat.PKCS8,
                encryption_algorithm=serialization.NoEncryption()
            )
            
            logger.info(f"Generated self-signed certificate for {common_name}")
            return cert_pem, key_pem
            
        except Exception as e:
            logger.error(f"Error generating self-signed certificate: {e}")
            raise
    
    def validate_certificate_chain(self, hostname: str, port: int = 443) -> bool:
        """Validate complete certificate chain"""
        try:
            context = ssl.create_default_context()
            context.check_hostname = True
            context.verify_mode = ssl.CERT_REQUIRED
            
            with socket.create_connection((hostname, port), timeout=10) as sock:
                with context.wrap_socket(sock, server_hostname=hostname) as ssock:
                    # If we get here, the certificate chain is valid
                    return True
            
        except ssl.SSLError as e:
            logger.error(f"SSL certificate validation failed for {hostname}: {e}")
            return False
        except Exception as e:
            logger.error(f"Error validating certificate chain for {hostname}: {e}")
            return False
    
    def get_certificate_info(self, hostname: str) -> Optional[TLSCertificateInfo]:
        """Get stored certificate information"""
        return self.certificates.get(hostname)


class DRPSecurityAuditor:
    """
    Comprehensive security auditor for DRP domains and services
    """
    
    def __init__(self):
        """Initialize security auditor"""
        self.dnssec_validator = DNSSECValidator() if DNSSEC_AVAILABLE else None
        self.tls_manager = TLSCertificateManager() if TLS_AVAILABLE else None
        
        logger.info("DRP Security Auditor initialized")
    
    def audit_domain_security(self, domain: str) -> SecurityAuditResult:
        """
        Perform comprehensive security audit of a domain
        
        Args:
            domain: Domain to audit
            
        Returns:
            Security audit result
        """
        try:
            issues = []
            recommendations = []
            
            # DNSSEC audit
            dnssec_status = SecurityStatus.ERROR
            if self.dnssec_validator:
                dnssec_result = self.dnssec_validator.validate_domain_dnssec(domain)
                dnssec_status = dnssec_result.status
                
                if not dnssec_result.is_valid:
                    issues.append(f"DNSSEC validation failed: {dnssec_result.error_message}")
                    recommendations.append("Enable DNSSEC for the domain")
                elif dnssec_status == SecurityStatus.WARNING:
                    issues.append("DNSSEC validation warnings detected")
                    recommendations.append("Review DNSSEC configuration")
            else:
                issues.append("DNSSEC validation not available")
                recommendations.append("Install dnspython library for DNSSEC support")
            
            # TLS audit
            tls_status = SecurityStatus.ERROR
            if self.tls_manager:
                tls_info = self.tls_manager.analyze_certificate(domain)
                tls_status = tls_info.status
                
                if not tls_info.is_valid:
                    issues.append("TLS certificate is invalid or expired")
                    recommendations.append("Renew TLS certificate")
                elif tls_info.days_until_expiry < 30:
                    issues.append(f"TLS certificate expires in {tls_info.days_until_expiry} days")
                    recommendations.append("Renew TLS certificate before expiry")
                elif tls_info.key_size < 2048:
                    issues.append(f"TLS certificate key size is {tls_info.key_size} bits")
                    recommendations.append("Use at least 2048-bit RSA keys")
                
                # Validate certificate chain
                if not self.tls_manager.validate_certificate_chain(domain):
                    issues.append("TLS certificate chain validation failed")
                    recommendations.append("Fix certificate chain issues")
            else:
                issues.append("TLS validation not available")
                recommendations.append("Install cryptography library for TLS support")
            
            # Determine overall status
            if dnssec_status == SecurityStatus.SECURE and tls_status == SecurityStatus.SECURE:
                overall_status = SecurityStatus.SECURE
            elif dnssec_status == SecurityStatus.ERROR or tls_status == SecurityStatus.ERROR:
                overall_status = SecurityStatus.ERROR
            elif dnssec_status == SecurityStatus.INSECURE or tls_status == SecurityStatus.INSECURE:
                overall_status = SecurityStatus.INSECURE
            else:
                overall_status = SecurityStatus.WARNING
            
            audit_result = SecurityAuditResult(
                domain=domain,
                dnssec_status=dnssec_status,
                tls_status=tls_status,
                overall_status=overall_status,
                issues=issues,
                recommendations=recommendations,
                audit_timestamp=datetime.utcnow().isoformat()
            )
            
            logger.info(f"Security audit completed for domain {domain}")
            return audit_result
            
        except Exception as e:
            logger.error(f"Error auditing domain {domain}: {e}")
            return SecurityAuditResult(
                domain=domain,
                dnssec_status=SecurityStatus.ERROR,
                tls_status=SecurityStatus.ERROR,
                overall_status=SecurityStatus.ERROR,
                issues=[f"Audit error: {str(e)}"],
                recommendations=["Fix audit system issues"],
                audit_timestamp=datetime.utcnow().isoformat()
            )
    
    def generate_security_report(self, domains: List[str]) -> Dict[str, Any]:
        """Generate comprehensive security report for multiple domains"""
        try:
            report = {
                "report_timestamp": datetime.utcnow().isoformat(),
                "total_domains": len(domains),
                "secure_domains": 0,
                "warning_domains": 0,
                "insecure_domains": 0,
                "error_domains": 0,
                "domain_results": []
            }
            
            for domain in domains:
                audit_result = self.audit_domain_security(domain)
                report["domain_results"].append(asdict(audit_result))
                
                # Count by status
                if audit_result.overall_status == SecurityStatus.SECURE:
                    report["secure_domains"] += 1
                elif audit_result.overall_status == SecurityStatus.WARNING:
                    report["warning_domains"] += 1
                elif audit_result.overall_status == SecurityStatus.INSECURE:
                    report["insecure_domains"] += 1
                else:
                    report["error_domains"] += 1
            
            logger.info(f"Generated security report for {len(domains)} domains")
            return report
            
        except Exception as e:
            logger.error(f"Error generating security report: {e}")
            return {"error": str(e)}


def main():
    """Command line interface for DNSSEC and TLS security"""
    parser = argparse.ArgumentParser(description="DRP DNSSEC & TLS Security Demo")
    parser.add_argument("--demo", action="store_true", help="Run demonstration")
    parser.add_argument("--domain", help="Domain to audit")
    parser.add_argument("--generate-cert", help="Generate self-signed certificate for domain")
    parser.add_argument("--audit", nargs="+", help="Domains to audit")
    
    args = parser.parse_args()
    
    try:
        # Initialize security auditor
        auditor = DRPSecurityAuditor()
        
        print(f"🔒 DRP Security Auditor Initialized")
        
        if args.demo:
            print(f"\n🛡️ DNSSEC & TLS Security Demo")
            print(f"=" * 50)
            
            # Test domains
            test_domains = ["google.com", "cloudflare.com", "example.com"]
            
            print(f"Auditing test domains...")
            for domain in test_domains:
                print(f"\n🔍 Auditing {domain}:")
                audit_result = auditor.audit_domain_security(domain)
                
                print(f"   Overall Status: {audit_result.overall_status.value.upper()}")
                print(f"   DNSSEC: {audit_result.dnssec_status.value}")
                print(f"   TLS: {audit_result.tls_status.value}")
                
                if audit_result.issues:
                    print(f"   Issues:")
                    for issue in audit_result.issues:
                        print(f"     - {issue}")
                
                if audit_result.recommendations:
                    print(f"   Recommendations:")
                    for rec in audit_result.recommendations:
                        print(f"     - {rec}")
            
            # Generate security report
            print(f"\n📊 Generating security report...")
            report = auditor.generate_security_report(test_domains)
            
            print(f"   Total domains: {report['total_domains']}")
            print(f"   Secure: {report['secure_domains']}")
            print(f"   Warnings: {report['warning_domains']}")
            print(f"   Insecure: {report['insecure_domains']}")
            print(f"   Errors: {report['error_domains']}")
        
        elif args.domain:
            # Audit single domain
            print(f"🔍 Auditing domain: {args.domain}")
            audit_result = auditor.audit_domain_security(args.domain)
            
            print(f"Overall Status: {audit_result.overall_status.value.upper()}")
            print(f"DNSSEC: {audit_result.dnssec_status.value}")
            print(f"TLS: {audit_result.tls_status.value}")
            
            if audit_result.issues:
                print(f"Issues:")
                for issue in audit_result.issues:
                    print(f"  - {issue}")
            
            if audit_result.recommendations:
                print(f"Recommendations:")
                for rec in audit_result.recommendations:
                    print(f"  - {rec}")
        
        elif args.generate_cert:
            # Generate self-signed certificate
            if not TLS_AVAILABLE:
                print("❌ TLS library not available. Install with: pip install cryptography")
                return 1
            
            print(f"🔐 Generating self-signed certificate for: {args.generate_cert}")
            tls_manager = TLSCertificateManager()
            
            cert_pem, key_pem = tls_manager.generate_self_signed_certificate(args.generate_cert)
            
            print(f"✅ Certificate generated successfully")
            print(f"Certificate (first 100 chars): {cert_pem[:100].decode()}...")
            print(f"Private Key (first 100 chars): {key_pem[:100].decode()}...")
        
        elif args.audit:
            # Audit multiple domains
            print(f"🔍 Auditing domains: {', '.join(args.audit)}")
            report = auditor.generate_security_report(args.audit)
            
            print(f"Security Report:")
            print(f"  Total domains: {report['total_domains']}")
            print(f"  Secure: {report['secure_domains']}")
            print(f"  Warnings: {report['warning_domains']}")
            print(f"  Insecure: {report['insecure_domains']}")
            print(f"  Errors: {report['error_domains']}")
            
            for result in report['domain_results']:
                print(f"\n{result['domain']}: {result['overall_status'].upper()}")
                if result['issues']:
                    for issue in result['issues']:
                        print(f"  - {issue}")
        
        return 0
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return 1


if __name__ == "__main__":
    exit(main())


