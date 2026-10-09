#!/usr/bin/env bash
# Hosts the booth site on your AWS account: one small EC2 instance (Ubuntu 24.04, arm64) running
# booth_site.py as a service. The site needs nothing from the camera's network: telemetry and commands
# go through /IOTCONNECT's REST API and the video through KVS WebRTC, so this is the "cloud" deployment.
#
#   AWS_PROFILE=... AWS_REGION=us-east-1 ./deploy_ec2.sh            # create (idempotent on the name tag)
#   DOMAIN=booth.example.com ./deploy_ec2.sh                         # + HTTPS via Caddy (point the DNS A record at the IP first)
#   ./deploy_ec2.sh destroy                                          # remove instance, key pair and security group
#
# Needs: aws CLI v2 with credentials that can manage EC2 (the AmazonEC2FullAccess policy is enough),
# and a filled booth-site env file (default: /etc/default/booth-site on this host, or BOOTH_ENV=path).
set -euo pipefail
HERE=$(cd "$(dirname "$0")/.." && pwd)
NAME=${NAME:-iotc-booth-site}
REGION=${AWS_REGION:-${AWS_DEFAULT_REGION:-us-east-1}}
TYPE=${INSTANCE_TYPE:-t4g.micro}
DOMAIN=${DOMAIN:-}
BOOTH_ENV=${BOOTH_ENV:-/etc/default/booth-site}
KEYFILE=${KEYFILE:-$HOME/.ssh/$NAME.pem}
export AWS_PAGER=""

aws_() { aws --region "$REGION" --output text "$@"; }
find_instance() { aws_ ec2 describe-instances --filters "Name=tag:Name,Values=$NAME" "Name=instance-state-name,Values=pending,running,stopping,stopped" --query 'Reservations[0].Instances[0].InstanceId' 2>/dev/null | grep -v None || true; }

if [ "${1:-}" = "destroy" ]; then
  ID=$(find_instance)
  [ -n "$ID" ] && aws_ ec2 terminate-instances --instance-ids "$ID" >/dev/null && echo "terminating $ID" && aws_ ec2 wait instance-terminated --instance-ids "$ID"
  EIP=$(aws_ ec2 describe-addresses --filters "Name=tag:Name,Values=$NAME" --query 'Addresses[0].AllocationId' | grep -v None || true)
  [ -n "$EIP" ] && aws_ ec2 release-address --allocation-id "$EIP" && echo "released elastic ip"
  SG=$(aws_ ec2 describe-security-groups --filters "Name=group-name,Values=$NAME" --query 'SecurityGroups[0].GroupId' | grep -v None || true)
  [ -n "$SG" ] && aws_ ec2 delete-security-group --group-id "$SG" && echo "deleted security group"
  aws_ ec2 delete-key-pair --key-name "$NAME" >/dev/null 2>&1 || true
  echo "done"; exit 0
fi

[ -f "$BOOTH_ENV" ] || { echo "booth env file $BOOTH_ENV not found (credentials for /IOTCONNECT)"; exit 1; }

# key pair
if ! aws_ ec2 describe-key-pairs --key-names "$NAME" >/dev/null 2>&1; then
  aws_ ec2 create-key-pair --key-name "$NAME" --key-type ed25519 --query KeyMaterial > "$KEYFILE"; chmod 600 "$KEYFILE"; echo "key pair saved to $KEYFILE"
fi
[ -f "$KEYFILE" ] || { echo "key pair $NAME exists in AWS but $KEYFILE is missing; delete the key pair or set KEYFILE"; exit 1; }

# security group: ssh from here, http/https from anywhere
VPC=$(aws_ ec2 describe-vpcs --filters Name=is-default,Values=true --query 'Vpcs[0].VpcId')
SG=$(aws_ ec2 describe-security-groups --filters "Name=group-name,Values=$NAME" --query 'SecurityGroups[0].GroupId' | grep -v None || true)
if [ -z "$SG" ]; then
  SG=$(aws_ ec2 create-security-group --group-name "$NAME" --description "booth site" --vpc-id "$VPC" --query GroupId)
  MYIP=$(curl -s https://checkip.amazonaws.com)/32
  aws_ ec2 authorize-security-group-ingress --group-id "$SG" --protocol tcp --port 22 --cidr "$MYIP" >/dev/null
  aws_ ec2 authorize-security-group-ingress --group-id "$SG" --protocol tcp --port 80 --cidr 0.0.0.0/0 >/dev/null
  aws_ ec2 authorize-security-group-ingress --group-id "$SG" --protocol tcp --port 443 --cidr 0.0.0.0/0 >/dev/null
fi

ID=$(find_instance)
if [ -z "$ID" ]; then
  # newest Canonical Ubuntu 24.04 arm64 image (owner 099720109477 is Canonical); needs only ec2:DescribeImages
  AMI=$(aws_ ec2 describe-images --owners 099720109477 --filters "Name=name,Values=ubuntu/images/hvm-ssd-gp3/ubuntu-noble-24.04-arm64-server-*" "Name=state,Values=available" \
        --query 'sort_by(Images,&CreationDate)[-1].ImageId')
  ID=$(aws_ ec2 run-instances --image-id "$AMI" --instance-type "$TYPE" --key-name "$NAME" --security-group-ids "$SG" \
        --tag-specifications "ResourceType=instance,Tags=[{Key=Name,Value=$NAME}]" \
        --block-device-mappings 'DeviceName=/dev/sda1,Ebs={VolumeSize=12,VolumeType=gp3}' \
        --user-data file://"$HERE/aws/user-data.sh" --query 'Instances[0].InstanceId')
  echo "launched $ID ($TYPE, $AMI)"
fi
aws_ ec2 wait instance-running --instance-ids "$ID"
# a stable address: an Elastic IP, free while it stays attached to a running instance
EIP=$(aws_ ec2 describe-addresses --filters "Name=tag:Name,Values=$NAME" --query 'Addresses[0].AllocationId' | grep -v None || true)
[ -n "$EIP" ] || EIP=$(aws_ ec2 allocate-address --domain vpc --tag-specifications "ResourceType=elastic-ip,Tags=[{Key=Name,Value=$NAME}]" --query AllocationId)
aws_ ec2 associate-address --instance-id "$ID" --allocation-id "$EIP" --allow-reassociation >/dev/null
IP=$(aws_ ec2 describe-addresses --allocation-ids "$EIP" --query 'Addresses[0].PublicIp')
echo "instance $ID at $IP; waiting for ssh"
for i in $(seq 1 30); do ssh -i "$KEYFILE" -o StrictHostKeyChecking=accept-new -o ConnectTimeout=5 -o BatchMode=yes ubuntu@"$IP" true 2>/dev/null && break; sleep 10; done

# ship the site and its settings
scp -q -i "$KEYFILE" "$HERE/booth_site.py" "$HERE/booth_site.html" ubuntu@"$IP":/tmp/
scp -q -i "$KEYFILE" "$BOOTH_ENV" ubuntu@"$IP":/tmp/booth-site.env
ssh -i "$KEYFILE" ubuntu@"$IP" DOMAIN="$DOMAIN" 'bash -s' <<'REMOTE'
set -e
sudo mkdir -p /opt/booth && sudo mv /tmp/booth_site.py /tmp/booth_site.html /opt/booth/ && sudo chmod 755 /opt/booth/booth_site.py
sudo install -m 600 -o root -g root /tmp/booth-site.env /etc/default/booth-site && rm -f /tmp/booth-site.env
# no camera on this network: video comes through KVS only
sudo sed -i 's#^BOOTH_LIVE_VIEW=.*#BOOTH_LIVE_VIEW=#' /etc/default/booth-site; grep -q '^BOOTH_LIVE_VIEW=' /etc/default/booth-site || echo 'BOOTH_LIVE_VIEW=' | sudo tee -a /etc/default/booth-site >/dev/null
sudo sed -i 's#^BOOTH_PORT=.*#BOOTH_PORT=8090#' /etc/default/booth-site
sudo tee /etc/systemd/system/booth-site.service >/dev/null <<EOF2
[Unit]
Description=Ask the camera: booth web site fed by /IOTCONNECT
After=network-online.target
Wants=network-online.target
[Service]
Type=simple
DynamicUser=yes
WorkingDirectory=/opt/booth
EnvironmentFile=/etc/default/booth-site
Environment=PYTHONUNBUFFERED=1
ExecStart=/usr/bin/python3 /opt/booth/booth_site.py
Restart=always
RestartSec=10
[Install]
WantedBy=multi-user.target
EOF2
sudo systemctl daemon-reload && sudo systemctl enable --now booth-site
# front door: Caddy (HTTPS with a domain, plain HTTP on the IP otherwise)
if ! command -v caddy >/dev/null; then
  # Ubuntu's own caddy package (universe); Caddy's third-party apt repository is not always reachable
  export DEBIAN_FRONTEND=noninteractive
  sudo apt-get update -qq >/dev/null 2>&1 || true
  sudo apt-get install -y -qq caddy >/dev/null
fi
if [ -n "$DOMAIN" ]; then printf '%s {\n\treverse_proxy 127.0.0.1:8090\n}\n' "$DOMAIN" | sudo tee /etc/caddy/Caddyfile >/dev/null
else printf ':80 {\n\treverse_proxy 127.0.0.1:8090\n}\n' | sudo tee /etc/caddy/Caddyfile >/dev/null; fi
sudo systemctl restart caddy
sleep 3; systemctl is-active booth-site caddy | paste -sd' '
REMOTE
echo
if [ -n "$DOMAIN" ]; then echo "booth site: https://$DOMAIN/   (DNS A record for $DOMAIN must point at $IP)"; else echo "booth site: http://$IP/"; fi
echo "ssh: ssh -i $KEYFILE ubuntu@$IP     logs: sudo journalctl -u booth-site -f"
