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
    my $param;
    foreach my $key (@keys) {
       $param->{$key} = $cgi->param($key);
    }
    
    # prepare response header
    print $cgi->header( -type => 'application/json', charset => 'utf8' );
    
    
    if ( !$param->{'method'} ) {
        $log->error("REST no method set in request");
        print $json->encode( { error => { 
            code => 42, 
            message=> "REST no method set in request",
            data => { pid => $$ }
        }});
        next;
    }
          
    # Methodname is always used lowercased as some users are 
    # not smart enough for CamelCasing
    my $method = lc($param->{'method'});
    delete $param->{'method'};
    delete $param->{'id'}; # to stay compatible with JSON RPC
    
    # Gather data from transport and TLS session    
    my $client_ip = $ENV{REMOTE_ADDR};    # dotted quad
   
    my $auth_dn = '';
    my $auth_pem = '';
    if ( defined $ENV{HTTPS} && lc( $ENV{HTTPS} ) eq 'on' ) {

        $log->debug("calling context is https");
        $auth_dn = $ENV{SSL_CLIENT_S_DN};
        $auth_pem = $ENV{SSL_CLIENT_CERT};        
        if ( defined $auth_dn ) {
            $log->info("REST authenticated client DN: $auth_dn");
        }
        else {
            $log->debug("REST unauthenticated (no cert)");
        }
    } else {
        $log->debug("REST unauthenticated (plain http)");
    }
    
    my $workflow_type = $conf->{$method}->{workflow};
    # might be empty
    my $servername = $conf->{$method}->{servername} || '';
    
    if ( !defined $workflow_type ) {
        $log->error("REST no workflow_type set for requested method $method");
        print $json->encode( { error => { 
            code => 42, 
            message=> "REST no workflow_type set for requested method $method",
            data => { pid => $$ }
        }});
        next;
    }
     
    $log->debug( "WF parameters: " . Dumper $param );
        
    my $workflow;
    my $client;
    eval {
        
        # create the client object
        $client = OpenXPKI::Client::Simple->new({
            logger => $log,
            config => $conf->{global}, # realm and locale
            auth => $conf->{auth}, # auth config
        });
        
        if ( !$client ) {
            $log->error("Could not instantiate client object");
            print $json->encode( { error => { 
                code => 42, 
                message=> "Could not instantiate client object",
                data => { pid => $$ }
            }});
            next;
        }
        
        $workflow = $client->handle_workflow({
            TYPE => $workflow_type,
            PARAMS => $param
        });
        
        $log->debug( 'Workflow info '  . Dumper $workflow );
    };
  
    my $res;
    if ( my $exc = OpenXPKI::Exception->caught() ) {
        $log->error("Unable to create workflow: ". $exc->message );
        $res = { error => { code => 42, message => $exc->message, data => { pid => $$ } } };
    } elsif ($EVAL_ERROR) {
        
        my $error = $client->last_error();
        if ($error) {
            $log->error("Unable to create workflow: ". $error );
        } else {
            $log->error("Unable to create workflow: ". $EVAL_ERROR );
            $error = 'uncaught error';
        }        
        $res = { error => { code => 42, message => $error, data => { pid => $$ } } };                
    } elsif (!$workflow->{ID} || $workflow->{'PROC_STATE'} eq 'exception' || $workflow->{'STATE'} eq 'FAILURE') {
        $log->error("workflow terminated in unexpected state" );
        $res = { error => { code => 42, message => 'workflow terminated in unexpected state', data => { pid => $$, id => $workflow->{id}, 'state' => $workflow->{'STATE'} } } };        
    } else {
        $log->info(sprintf("Revocation request was processed properly (Workflow: %01d, State: %s", 
            $workflow->{ID}, $workflow->{STATE}) );
        $res = { result => { id => $workflow->{ID}, 'state' => $workflow->{'STATE'},  pid => $$ }};
    }

    print $json->encode( $res );
    

}
