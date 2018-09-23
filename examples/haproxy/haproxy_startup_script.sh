#! /bin/bash

{% if cloudless_test_framework_ssh_key %}
adduser "{{ cloudless_test_framework_ssh_username }}" --disabled-password --gecos "Cloudless Test User"
echo "{{ cloudless_test_framework_ssh_username }} ALL=(ALL) NOPASSWD:ALL" >> /etc/sudoers
mkdir /home/{{ cloudless_test_framework_ssh_username }}/.ssh/
echo "{{ cloudless_test_framework_ssh_key }}" >> /home/{{ cloudless_test_framework_ssh_username }}/.ssh/authorized_keys
{% endif %}

apt-get update
apt-get install -y haproxy
cat <<EOF > /etc/haproxy/haproxy.cfg
global
  log /dev/log local0
  log /dev/log local1 notice
  chroot /var/lib/haproxy
  stats socket /run/haproxy/admin.sock mode 660 level admin
  stats timeout 30s
  user haproxy
  group haproxy
  daemon

  # Default SSL material locations
  ca-base /etc/ssl/certs
  crt-base /etc/ssl/private

  # Default ciphers to use on SSL-enabled listening sockets.
  # For more information, see ciphers(1SSL). This list is from:
  #  https://hynek.me/articles/hardening-your-web-servers-ssl-ciphers/
  ssl-default-bind-ciphers ECDH+AESGCM:DH+AESGCM:ECDH+AES256:DH+AES256:ECDH+AES128:DH+AES:ECDH+3DES:DH+3DES:RSA+AESGCM:RSA+AES:RSA+3DES:!aNULL:!MD5:!DSS
  ssl-default-bind-options no-sslv3

defaults
  log global
  mode http
  option httplog
  option dontlognull
        timeout connect 5000
        timeout client  50000
        timeout server  50000
  errorfile 400 /etc/haproxy/errors/400.http
  errorfile 403 /etc/haproxy/errors/403.http
  errorfile 408 /etc/haproxy/errors/408.http
  errorfile 500 /etc/haproxy/errors/500.http
  errorfile 502 /etc/haproxy/errors/502.http
  errorfile 503 /etc/haproxy/errors/503.http
  errorfile 504 /etc/haproxy/errors/504.http

frontend localnodes
    bind *:80
    mode http
    default_backend nodes

backend nodes
    mode http
    balance roundrobin
    option forwardfor
    http-request set-header X-Forwarded-Port %[dst_port]
    http-request add-header X-Forwarded-Proto https if { ssl_fc }
    option httpchk HEAD / HTTP/1.1\r\nHost:localhost{% for PrivateIp in PrivateIps %}
    server web0{{ loop.index }} {{ PrivateIp }}:80 check{% endfor %}
EOF
service haproxy restart
