#!/usr/bin/perl

use strict;
use warnings;

use CGI;
use CGI::Fast;
use Data::Dumper;
use English;

use JSON;
use MIME::Base64;
use OpenXPKI::Exception;
use OpenXPKI::Client::Simple;
use OpenXPKI::Client::Config;
use OpenXPKI::Serialization::Simple;

use Log::Log4perl;

our $config = OpenXPKI::Client::Config->new('rest');
my $conf = $config->default();
my $log = $config->logger();

$log->info("REST handler initialized");

my $json = new JSON();

while (my $cgi = CGI::Fast->new()) {
    
    my $error = '';

    my @keys = $cgi->multi_param();
    my $params;
    foreach my $key (@keys) {
       $params->{$key} = $cgi->param($key); 
    }

    print $cgi->header( -type => 'application/json' );
    print $json->encode( { result => { 'error' => $error,  }, params => $params, config => $conf });

}
