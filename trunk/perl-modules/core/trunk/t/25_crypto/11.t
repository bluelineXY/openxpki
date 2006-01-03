use strict;
use warnings;
use Test;
BEGIN { plan tests => 12 };

print STDERR "OpenXPKI::Crypto::Command: Create a user cert and issue a CRL\n";

use OpenXPKI::Crypto::TokenManager;
use OpenXPKI::Crypto::Profile::Certificate;
use OpenXPKI::Crypto::Profile::CRL;

our $cache;
our $basedir;
eval `cat t/25_crypto/common.pl`;

ok(1);

## parameter checks for TokenManager init

my $mgmt = OpenXPKI::Crypto::TokenManager->new (DEBUG => 0, CONFIG => $cache);
ok (1);

## parameter checks for get_token

my $token = $mgmt->get_token (TYPE => "CA", NAME => "INTERNAL_CA_1", PKI_REALM => "Test Root CA");
ok (1);

## create PIN (128 bit == 16 byte)
my $passwd = $token->command ("create_random", RANDOM_LENGTH => 16);
ok (1);
print STDERR "passwd: $passwd\n" if ($ENV{DEBUG});
OpenXPKI->write_file (FILENAME => "$basedir/ca1/passwd.txt", CONTENT => $passwd);

## create DSA key
my $key = $token->command ("create_key",
                           TYPE       => "DSA",
                           KEY_LENGTH => "1024",
                           ENC_ALG    => "aes256",
                           PASSWD     => $passwd);
ok (1);
print STDERR "DSA: $key\n" if ($ENV{DEBUG});
OpenXPKI->write_file (FILENAME => "$basedir/ca1/dsa.pem", CONTENT => $key);

## create EC key
$key = $token->command ("create_key",
                        TYPE       => "EC",
                        CURVE_NAME => "sect571r1",
                        ENC_ALG    => "aes256",
                        PASSWD     => $passwd);
ok (1);
print STDERR "EC: $key\n" if ($ENV{DEBUG});
OpenXPKI->write_file (FILENAME => "$basedir/ca1/ec.pem", CONTENT => $key);

## create RSA key
$key = $token->command ("create_key",
                        TYPE       => "RSA",
                        KEY_LENGTH => "1024",
                        ENC_ALG    => "aes256",
                        PASSWD     => $passwd);
ok (1);
print STDERR "RSA: $key\n" if ($ENV{DEBUG});
OpenXPKI->write_file (FILENAME => "$basedir/ca1/rsa.pem", CONTENT => $key);

## create CSR
my $subject = "cn=John Doe,dc=OpenCA,dc=info";
my $csr = $token->command ("create_pkcs10",
                           KEY     => $key,
                           PASSWD  => $passwd,
                           SUBJECT => $subject);
ok (1);
print STDERR "CSR: $csr\n" if ($ENV{DEBUG});
OpenXPKI->write_file (FILENAME => "$basedir/ca1/pkcs10.pem", CONTENT => $csr);

## create profile
my $profile = OpenXPKI::Crypto::Profile::Certificate->new (
                  DEBUG     => 0,
                  CONFIG    => $cache,
                  PKI_REALM => "Test Root CA",
                  CA        => "INTERNAL_CA_1",
                  ROLE      => "User");
$profile->set_serial  (1);
$profile->set_subject ($subject);
ok(1);

## create cert
my $cert = $token->command ("issue_cert",
                            CSR     => $csr,
                            PROFILE => $profile);
ok (1);
print STDERR "cert: $cert\n" if ($ENV{DEBUG});
OpenXPKI->write_file (FILENAME => "$basedir/ca1/cert.pem", CONTENT => $cert);

## build the PKCS#12 file
my $pkcs12 = $token->command ("create_pkcs12",
                              PASSWD  => $passwd,
                              KEY     => $key,
                              CERT    => $cert,
                              CHAIN   => $token->get_certfile());
ok (1);
print STDERR "PKCS#12 length: ".length ($pkcs12)."\n" if ($ENV{DEBUG});

## create CRL
$profile = OpenXPKI::Crypto::Profile::CRL->new (
                  DEBUG     => 0,
                  CONFIG    => $cache,
                  PKI_REALM => "Test Root CA",
                  CA        => "INTERNAL_CA_1");
## otherwise test 34 fails
## $profile->set_serial (1);
my $crl = $token->command ("issue_crl",
                           REVOKED => [$cert],
                           PROFILE => $profile);
print STDERR "CRL: $crl\n" if ($ENV{DEBUG});
OpenXPKI->write_file (FILENAME => "$basedir/ca1/crl.pem", CONTENT => $crl);
ok (1);

1;
