#!/bin/sh
trap exit TERM

while :; do
    certbot renew --webroot --webroot-path=/var/www/certbot --quiet
    sleep 12h & wait ${!}
done
