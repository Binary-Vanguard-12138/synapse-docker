#!/bin/sh
trap exit TERM

while :; do
    certbot renew --webroot --webroot-path=/var/www/certbot --quiet
    chmod -R a+rX /etc/letsencrypt/archive /etc/letsencrypt/live
    sleep 12h & wait ${!}
done
