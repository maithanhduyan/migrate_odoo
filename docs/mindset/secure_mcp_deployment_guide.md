# Secure MCP Deployment & Monitoring Guide

## 🚀 Quick Start Deployment

### 1. Chạy Setup Script

```bash
# Cài đặt môi trường secure
python setup_secure_mcp.py

# Load environment variables
source .env.secure  # Linux/Mac
# hoặc
Get-Content .env.secure | ForEach-Object {
    $name, $value = $_.split('=')
    Set-Item -Path "env:$name" -Value $value
}  # Windows PowerShell
```

### 2. Docker Deployment

```bash
# Build secure containers
docker-compose -f docker-compose.secure.yml build

# Start services
docker-compose -f docker-compose.secure.yml up -d

# Verify deployment
docker-compose -f docker-compose.secure.yml ps
docker-compose -f docker-compose.secure.yml logs -f
```

### 3. Production Deployment với systemd

```bash
# Copy service file
sudo cp secure-mcp.service /etc/systemd/system/

# Enable and start service
sudo systemctl daemon-reload
sudo systemctl enable secure-mcp
sudo systemctl start secure-mcp

# Check status
sudo systemctl status secure-mcp
```

## 🔧 Configuration Management

### Environment Variables

```bash
# Security keys
export MCP_SECRET_KEY="your-secret-key"
export JWT_SECRET="your-jwt-secret"

# Resource limits
export MCP_MAX_MEMORY="256m"
export MCP_MAX_CPU="0.5"
export MCP_TIMEOUT="30"

# Security settings
export MCP_AUTH_REQUIRED="true"
export MCP_SANDBOX_ENABLED="true"
export MCP_INPUT_VALIDATION="true"
```

### Runtime Configuration

```json
{
  "security": {
    "authentication": {
      "required": true,
      "method": "jwt"
    },
    "sandbox": {
      "enabled": true,
      "timeout": 30
    }
  }
}
```

## 📊 Monitoring & Alerting

### 1. Health Checks

```bash
# Container health
docker-compose -f docker-compose.secure.yml ps

# Application health
curl -f http://localhost:8000/health

# Service status
systemctl status secure-mcp
```

### 2. Log Monitoring

```bash
# Security events
tail -f logs/mcp_security_events.log

# Application logs
tail -f logs/mcp_server.log

# Container logs
docker-compose -f docker-compose.secure.yml logs -f secure-mcp-server
```

### 3. Resource Monitoring

```bash
# Container stats
docker stats

# System resources
htop
free -h
df -h

# Network connections
netstat -tulpn | grep :8000
```

### 4. Security Monitoring

```bash
# Failed authentication attempts
grep "Unauthorized access" logs/mcp_security_events.log

# Suspicious input patterns
grep "Invalid inputs detected" logs/mcp_security_events.log

# Resource usage anomalies
grep "Resource limit exceeded" logs/mcp_security_events.log
```

## 🔍 Log Analysis Examples

### Security Event Patterns

```bash
# Authentication failures
grep -E "Authentication|Unauthorized" logs/mcp_security_events.log | tail -20

# Input validation failures
grep "Invalid inputs" logs/mcp_security_events.log | tail -20

# Rate limiting events
grep "Rate limit" logs/mcp_security_events.log | tail -20

# Suspicious patterns
grep -E "injection|traversal|exec|eval" logs/mcp_security_events.log
```

### Performance Analysis

```bash
# Request response times
grep -E "Tool completed|Tool failed" logs/mcp_server.log | awk '{print $1, $2, $NF}'

# Resource usage
grep "Resource usage" logs/mcp_server.log | tail -20

# Error patterns
grep "ERROR" logs/mcp_server.log | tail -20
```

## 📈 Alerting Setup

### 1. Prometheus + Grafana

```yaml
# prometheus.yml
global:
  scrape_interval: 15s

scrape_configs:
  - job_name: 'secure-mcp'
    static_configs:
      - targets: ['localhost:8000']
    metrics_path: '/metrics'
    scrape_interval: 30s
```

### 2. Log-based Alerts

```bash
#!/bin/bash
# alert_script.sh

# Check for security events
SECURITY_EVENTS=$(grep -c "SECURITY" logs/mcp_security_events.log)
if [ $SECURITY_EVENTS -gt 10 ]; then
    echo "ALERT: High security events detected: $SECURITY_EVENTS"
    # Send notification
fi

# Check for failed authentications
FAILED_AUTH=$(grep -c "Unauthorized access" logs/mcp_security_events.log)
if [ $FAILED_AUTH -gt 5 ]; then
    echo "ALERT: Multiple failed authentications: $FAILED_AUTH"
    # Send notification
fi
```

### 3. Container Health Monitoring

```bash
#!/bin/bash
# health_check.sh

# Check container health
CONTAINER_STATUS=$(docker-compose -f docker-compose.secure.yml ps -q secure-mcp-server | xargs docker inspect -f '{{.State.Health.Status}}')

if [ "$CONTAINER_STATUS" != "healthy" ]; then
    echo "ALERT: Container unhealthy: $CONTAINER_STATUS"
    # Restart container
    docker-compose -f docker-compose.secure.yml restart secure-mcp-server
fi
```

## 🛠️ Maintenance Tasks

### Daily Tasks

```bash
#!/bin/bash
# daily_maintenance.sh

# Rotate logs
find logs/ -name "*.log" -size +100M -exec gzip {} \;

# Clean temp files
find temp/ -type f -mtime +1 -delete

# Check disk space
df -h | awk '$5 > 80 {print "ALERT: Disk usage high on " $6}'

# Backup configuration
tar -czf backup/config_$(date +%Y%m%d).tar.gz *.json *.yml .env.secure
```

### Weekly Tasks

```bash
#!/bin/bash
# weekly_maintenance.sh

# Update container images
docker-compose -f docker-compose.secure.yml pull

# Security audit
python security_audit.py

# Performance report
python performance_report.py

# Clean old backups
find backup/ -name "*.tar.gz" -mtime +30 -delete
```

### Monthly Tasks

```bash
#!/bin/bash
# monthly_maintenance.sh

# Rotate secrets
python rotate_secrets.py

# Security assessment
python security_assessment.py

# Update dependencies
pip install --upgrade -r requirements.txt

# Full system backup
tar -czf backup/full_backup_$(date +%Y%m%d).tar.gz --exclude=logs --exclude=temp .
```

## 🔐 Security Hardening Checklist

### ✅ Container Security
- [ ] Non-root user execution
- [ ] Read-only file system
- [ ] Capability dropping
- [ ] Security profiles (AppArmor/SELinux)
- [ ] Resource limits
- [ ] Network isolation

### ✅ Application Security
- [ ] Input validation
- [ ] SQL injection protection
- [ ] Path traversal protection
- [ ] Command injection protection
- [ ] Authentication enabled
- [ ] Authorization configured

### ✅ Network Security
- [ ] Bind to localhost only
- [ ] TLS/SSL enabled
- [ ] Rate limiting active
- [ ] Firewall rules
- [ ] VPN access (if needed)

### ✅ Data Security
- [ ] Encryption at rest
- [ ] Encryption in transit
- [ ] Secure key management
- [ ] Regular backups
- [ ] Access logging

## 🚨 Incident Response

### Security Incident Detected

1. **Immediate Response**
   ```bash
   # Stop services
   docker-compose -f docker-compose.secure.yml stop
   
   # Preserve logs
   cp -r logs/ incident_logs_$(date +%Y%m%d_%H%M%S)/
   
   # Block suspicious IPs
   iptables -A INPUT -s SUSPICIOUS_IP -j DROP
   ```

2. **Investigation**
   ```bash
   # Analyze logs
   grep -E "SECURITY|ERROR" logs/mcp_security_events.log > incident_analysis.log
   
   # Check system integrity
   find . -type f -name "*.py" -exec sha256sum {} \; > current_hashes.txt
   diff known_good_hashes.txt current_hashes.txt
   ```

3. **Recovery**
   ```bash
   # Restore from backup if needed
   tar -xzf backup/latest_backup.tar.gz
   
   # Rotate all secrets
   python rotate_secrets.py --force
   
   # Update and restart
   docker-compose -f docker-compose.secure.yml up -d --force-recreate
   ```

## 📋 Performance Tuning

### Resource Optimization

```bash
# Monitor resource usage
docker stats --format "table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}"

# Adjust limits based on usage
# Edit docker-compose.secure.yml:
#   deploy:
#     resources:
#       limits:
#         memory: 512M  # Increase if needed
#         cpus: '0.5'   # Adjust based on load
```

### Database Tuning

```sql
-- PostgreSQL optimization
-- Edit postgresql.conf:
-- shared_buffers = 256MB
-- effective_cache_size = 1GB
-- work_mem = 4MB
-- maintenance_work_mem = 64MB
```

### Application Tuning

```python
# Adjust MCP server settings
MCP_CONFIG = {
    'max_concurrent_requests': 20,  # Increase for high load
    'request_timeout': 60,          # Adjust based on operations
    'connection_pool_size': 10,     # Database connections
    'cache_ttl': 300               # Cache timeout
}
```

## 📚 Troubleshooting Guide

### Common Issues

1. **Authentication Failures**
   ```bash
   # Check token expiry
   grep "ExpiredSignatureError" logs/mcp_security_events.log
   
   # Verify secret key
   echo $MCP_SECRET_KEY | wc -c  # Should be > 32
   ```

2. **Performance Issues**
   ```bash
   # Check resource usage
   docker stats
   
   # Analyze slow queries
   grep "slow query" logs/mcp_server.log
   ```

3. **Connection Issues**
   ```bash
   # Check port binding
   netstat -tulpn | grep :8000
   
   # Test connectivity
   curl -v http://localhost:8000/health
   ```

### Recovery Procedures

```bash
# Complete reset (emergency)
./emergency_reset.sh

# Gradual restart
docker-compose -f docker-compose.secure.yml restart

# Config reload
kill -HUP $(pgrep -f secure_mcp_server)
```

Theo hướng dẫn này, bạn sẽ có một MCP server hoàn toàn an toàn và đáng tin cậy, loại bỏ hoàn toàn cảnh báo bảo mật ban đầu!
