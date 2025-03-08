# Nginx Configuration for ArenaPadel

This directory contains the Nginx configuration for the ArenaPadel application.

## Installation

1. Copy the configuration file to the Nginx sites-available directory:
```bash
sudo cp arenapadel /etc/nginx/sites-available/arenapadel
```

2. Create a symbolic link in sites-enabled:
```bash
sudo ln -s /etc/nginx/sites-available/arenapadel /etc/nginx/sites-enabled/
```

3. Test the configuration:
```bash
sudo nginx -t
```

4. If the test is successful, restart Nginx:
```bash
sudo systemctl restart nginx
```

## Configuration Details

The configuration includes:
- SSL/HTTPS setup with Let's Encrypt certificates
- Static files serving with caching
- Media files serving
- HTTP to HTTPS redirection
- Proxy configuration for Gunicorn
