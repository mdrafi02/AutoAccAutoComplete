# Cron Job Setup for Weekly Training

This guide explains how to set up a cron job to run weekly model training as a backup to Jenkins.

## 📋 Overview

The cron job runs `run_weekly_training.sh` which executes the complete training pipeline:
1. Extract keywords from XML files
2. Clean the dataset
3. Train the LSTM model
4. Save model and tokenizer
5. (Optional) Convert to TensorFlow.js format

## 🚀 Quick Setup

### 1. Make the script executable

```bash
chmod +x run_weekly_training.sh
```

### 2. Configure environment variables

Edit `run_weekly_training.sh` and set these variables at the top:

```bash
# Required
XML_FOLDER="/path/to/your/xml/files"

# Optional (defaults are provided)
PROJECT_DIR="/path/to/project"  # Default: script directory
LOG_DIR="/path/to/logs"         # Default: PROJECT_DIR/logs
MODEL_DIR="/path/to/models"     # Default: PROJECT_DIR/models
NOTIFICATION_EMAIL="your-email@example.com"
```

Or export them before running:

```bash
export XML_FOLDER="/path/to/xml/files"
export NOTIFICATION_EMAIL="your-email@example.com"
./run_weekly_training.sh
```

### 3. Test the script manually

Before setting up cron, test the script manually:

```bash
# Test with default paths
./run_weekly_training.sh

# Or with custom paths
XML_FOLDER="/path/to/xml" ./run_weekly_training.sh
```

### 4. Set up cron job

#### Option A: Edit crontab directly

```bash
crontab -e
```

Add one of these lines:

```bash
# Run every Sunday at 2:00 AM
0 2 * * 0 /path/to/run_weekly_training.sh >> /path/to/logs/cron.log 2>&1

# Run every Sunday at 2:00 AM with environment variables
0 2 * * 0 cd /path/to/project && XML_FOLDER=/path/to/xml /path/to/run_weekly_training.sh >> /path/to/logs/cron.log 2>&1

# Run every Monday at 3:00 AM
0 3 * * 1 /path/to/run_weekly_training.sh >> /path/to/logs/cron.log 2>&1
```

#### Option B: Use the provided cron configuration file

1. Edit `cron_weekly_training` and update the paths:

```bash
# Edit the file
nano cron_weekly_training

# Update these paths:
PROJECT_DIR="/home/administrator/RafiWork/ML_copy/robot_keyword_model2"
XML_FOLDER="/path/to/your/xml/files"
```

2. Install the cron job:

```bash
# Make sure paths are correct in cron_weekly_training
crontab cron_weekly_training

# Verify it was added
crontab -l
```

## 📅 Cron Schedule Examples

| Schedule | Cron Expression | Description |
|----------|----------------|-------------|
| Every Sunday 2 AM | `0 2 * * 0` | Weekly on Sunday |
| Every Monday 3 AM | `0 3 * * 1` | Weekly on Monday |
| Every Sunday 2 AM (random minute) | `H 2 * * 0` | Jenkins-style random minute |
| First day of month 1 AM | `0 1 1 * *` | Monthly |
| Every day at 2 AM | `0 2 * * *` | Daily (for testing) |

## 📁 Directory Structure

The script creates this structure:

```
project/
├── run_weekly_training.sh
├── models/
│   ├── keyword_predictor_v20241208_020000.keras
│   ├── keyword_predictor_latest.keras
│   ├── tokenizer_v20241208_020000.json
│   └── tokenizer_latest.json
├── logs/
│   ├── training_20241208_020000.log
│   └── training_20241208_020000_error.log
├── tfjs_model/          # Optional
└── venv/                # Virtual environment
```

## 🔍 Monitoring and Logs

### View recent logs

```bash
# List all training logs
ls -lht logs/training_*.log

# View latest log
tail -f logs/training_*.log | head -1

# View specific log
cat logs/training_20241208_020000.log
```

### Check cron execution

```bash
# View cron logs (if configured)
tail -f /var/log/cron

# Check if cron job is running
ps aux | grep run_weekly_training

# Verify cron job is scheduled
crontab -l
```

### Test cron job manually

```bash
# Run the exact command cron would run
/path/to/run_weekly_training.sh

# Or with full environment
cd /path/to/project && XML_FOLDER=/path/to/xml /path/to/run_weekly_training.sh
```

## 📧 Email Notifications

The script sends email notifications if:
1. `NOTIFICATION_EMAIL` is set
2. `mail` command is available on the system

To enable email notifications:

```bash
# Install mail utility (if not available)
sudo apt-get install mailutils  # Ubuntu/Debian
sudo yum install mailx          # CentOS/RHEL

# Set email in script or environment
export NOTIFICATION_EMAIL="your-email@example.com"
```

## 🔧 Troubleshooting

### Script fails with "command not found"

**Problem:** Python or other commands not found in cron environment.

**Solution:** Use full paths in the script or set PATH in cron:

```bash
# In crontab, add PATH at the top
PATH=/usr/local/bin:/usr/bin:/bin
0 2 * * 0 /path/to/run_weekly_training.sh
```

### Virtual environment not activating

**Problem:** `source` command doesn't work in cron.

**Solution:** The script uses full paths to venv binaries, so this shouldn't be an issue. If it is, ensure the venv path is correct.

### Permission denied

**Problem:** Script or directories not writable.

**Solution:**
```bash
# Make script executable
chmod +x run_weekly_training.sh

# Ensure directories are writable
chmod -R 755 models/ logs/
```

### XML folder not found

**Problem:** Cron job can't find XML files.

**Solution:** Use absolute paths in environment variables:

```bash
# In crontab
XML_FOLDER=/absolute/path/to/xml /path/to/run_weekly_training.sh
```

### Logs not being created

**Problem:** Log directory doesn't exist or isn't writable.

**Solution:** The script creates the directory automatically, but ensure the parent directory exists and is writable.

## 🔄 Integration with Jenkins

This cron job is designed as a **backup** to Jenkins. Best practices:

1. **Disable cron when Jenkins is available:**
   ```bash
   # Comment out the cron line
   # 0 2 * * 0 /path/to/run_weekly_training.sh
   ```

2. **Use different model directories** to avoid conflicts:
   ```bash
   # In cron script
   MODEL_DIR="${PROJECT_DIR}/models_cron"
   ```

3. **Monitor both systems** to ensure training happens regularly.

## 📝 Example Complete Setup

```bash
# 1. Navigate to project directory
cd /home/administrator/RafiWork/ML_copy/robot_keyword_model2

# 2. Make script executable
chmod +x run_weekly_training.sh

# 3. Test manually first
XML_FOLDER="/path/to/xml/files" ./run_weekly_training.sh

# 4. Edit crontab
crontab -e

# 5. Add this line (runs every Sunday at 2 AM)
0 2 * * 0 cd /home/administrator/RafiWork/ML_copy/robot_keyword_model2 && XML_FOLDER=/path/to/xml/files /home/administrator/RafiWork/ML_copy/robot_keyword_model2/run_weekly_training.sh >> /home/administrator/RafiWork/ML_copy/robot_keyword_model2/logs/cron.log 2>&1

# 6. Verify
crontab -l

# 7. Check logs after first run
ls -lht logs/
```

## 🆘 Support

If you encounter issues:

1. Check the log files in `logs/` directory
2. Verify all paths are absolute and correct
3. Test the script manually before relying on cron
4. Ensure all dependencies are installed
5. Check system logs: `journalctl -u cron` or `/var/log/cron`

