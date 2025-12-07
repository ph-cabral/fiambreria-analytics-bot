#!/bin/bash
DATE=$(date +%Y%m%d_%H%M%S)
tar -czf backup_fiambreria_$DATE.tar.gz db/ .env credentials.json
echo "Backup creado: backup_fiambreria_$DATE.tar.gz"
