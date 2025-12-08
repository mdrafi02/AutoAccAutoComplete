# How Jenkins Automatically Runs Weekly Training

This document explains how Jenkins automatically schedules and runs the weekly training pipeline.

## 🔄 How It Works

Jenkins uses **cron triggers** to automatically start builds at scheduled times. Here's how the weekly training is configured:

### 1. Cron Trigger Configuration

In the `Jenkinsfile`, the cron trigger is defined in the `properties` block:

```groovy
properties([
    parameters([...]),
    pipelineTriggers([
        cron('H 2 * * 0')  // Every Sunday at 2 AM
    ])
])
```

**Cron Expression Breakdown:**
- `H` = Hash (random minute between 0-59) - Jenkins spreads load across builds
- `2` = Hour (2 AM)
- `*` = Day of month (any day)
- `*` = Month (any month)
- `0` = Day of week (Sunday, where 0=Sunday, 1=Monday, etc.)

### 2. Build Detection

The pipeline checks if the build was triggered by a timer:

```groovy
if (params.RUN_TRAINING == true || env.BUILD_CAUSE == 'TIMERTRIGGER') {
    stage('Weekly Training') {
        // Run training pipeline
    }
}
```

**Two ways to trigger training:**
1. **Automatic (Timer)**: When `BUILD_CAUSE == 'TIMERTRIGGER'` - Jenkins automatically starts the build
2. **Manual**: When `RUN_TRAINING == true` - User manually triggers with the parameter

### 3. Complete Flow

```
┌─────────────────────────────────────────────────────────┐
│ 1. Jenkins Cron Scheduler (Every Sunday 2 AM)           │
│    Checks if it's time to run the pipeline              │
└────────────────────┬────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────┐
│ 2. Jenkins Starts Build                                  │
│    Sets BUILD_CAUSE = 'TIMERTRIGGER'                    │
│    Sets RUN_TRAINING = false (default)                  │
└────────────────────┬────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────┐
│ 3. Pipeline Checks Condition                             │
│    if (RUN_TRAINING == true || BUILD_CAUSE == 'TIMERTRIGGER') │
│    ✅ Condition is TRUE → Run Training Stage            │
└────────────────────┬────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────┐
│ 4. Training Pipeline Executes                            │
│    - Extract keywords                                    │
│    - Clean dataset                                      │
│    - Train model                                        │
│    - Save model and tokenizer                           │
└─────────────────────────────────────────────────────────┘
```

## 📅 Setting Up Weekly Schedule

### Method 1: In Jenkinsfile (Recommended)

The cron trigger is already defined in the `Jenkinsfile`:

```groovy
pipelineTriggers([
    cron('H 2 * * 0')  // Every Sunday at 2 AM
])
```

**After adding this to Jenkinsfile:**
1. Commit and push the changes
2. Jenkins will automatically detect the new trigger
3. The schedule will be active on the next build

### Method 2: Via Jenkins UI

If you prefer to configure via UI:

1. Go to your Jenkins job
2. Click **Configure**
3. Scroll to **Build Triggers** section
4. Check **Build periodically**
5. Enter cron expression: `H 2 * * 0`
6. Click **Save**

**Note:** If both are configured, the Jenkinsfile takes precedence.

## 🕐 Cron Expression Examples

| Schedule | Cron Expression | Description |
|----------|----------------|-------------|
| Every Sunday 2 AM | `H 2 * * 0` | Weekly (recommended) |
| Every Monday 3 AM | `H 3 * * 1` | Weekly on Monday |
| Every day at 2 AM | `H 2 * * *` | Daily |
| Every Sunday 2 AM (fixed minute) | `0 2 * * 0` | Fixed at 2:00 AM (not recommended - causes load spikes) |
| First day of month 1 AM | `H 1 1 * *` | Monthly |
| Every 12 hours | `H */12 * * *` | Twice daily |

**Why use `H` instead of fixed minutes?**
- `H` = Hash (random minute)
- Spreads load across multiple Jenkins jobs
- Prevents all jobs from starting at exactly the same time
- Example: `H 2 * * 0` might run at 2:17 AM one week, 2:43 AM the next

## 🔍 Verifying the Schedule

### Check if Trigger is Active

1. Go to your Jenkins job
2. Click **Configure**
3. Look for **Build Triggers** section
4. You should see: **Build periodically** with the cron expression

### View Next Scheduled Build

1. Go to your Jenkins job
2. Look at the left sidebar
3. You should see: **Next build scheduled for: [date/time]**

### Check Build History

1. Go to **Build History**
2. Look for builds with **Timer** icon
3. These are automatically triggered builds

### View Build Cause

1. Click on any build
2. Look at **Build Information**
3. You should see: **Started by timer** or **Started by user [name]**

## 🧪 Testing the Schedule

### Test Immediately

You can test if the trigger works without waiting:

1. **Trigger manually with timer simulation:**
   ```bash
   # Via Jenkins CLI
   jenkins-cli build AutoAccKeywordModel -p RUN_TRAINING=true
   ```

2. **Or modify the condition temporarily:**
   ```groovy
   // Temporarily change to always run
   if (true) {  // Change back after testing!
       stage('Weekly Training') { ... }
   }
   ```

### Verify Build Cause

After a build runs, check the console output:

```
Started by timer
```

This confirms the build was triggered by the cron schedule.

## 🔧 Troubleshooting

### Build Not Running Automatically

**Problem:** Builds aren't starting on schedule.

**Solutions:**
1. **Check Jenkins is running:**
   ```bash
   sudo systemctl status jenkins
   ```

2. **Verify cron trigger is configured:**
   - Go to job → Configure → Build Triggers
   - Ensure "Build periodically" is checked
   - Verify cron expression is correct

3. **Check Jenkins logs:**
   ```bash
   sudo tail -f /var/log/jenkins/jenkins.log
   ```

4. **Verify Jenkinsfile syntax:**
   - The `pipelineTriggers` must be in the `properties` block
   - Cron expression must be valid

### Build Runs But Training Doesn't Execute

**Problem:** Build starts but training stage is skipped.

**Check:**
1. Verify `BUILD_CAUSE == 'TIMERTRIGGER'` in build logs
2. Check the condition in Jenkinsfile:
   ```groovy
   if (params.RUN_TRAINING == true || env.BUILD_CAUSE == 'TIMERTRIGGER')
   ```

3. Add debug output:
   ```groovy
   echo "BUILD_CAUSE: ${env.BUILD_CAUSE}"
   echo "RUN_TRAINING: ${params.RUN_TRAINING}"
   ```

### Schedule Not Taking Effect

**Problem:** Changed cron expression but it's not working.

**Solutions:**
1. **Save Jenkinsfile changes and push to repository**
2. **Trigger a manual build** - Jenkins will reload the Jenkinsfile
3. **Or restart Jenkins:**
   ```bash
   sudo systemctl restart jenkins
   ```

## 📧 Notifications

When a build is triggered by timer:
- Email notifications are sent (if configured)
- Build status is tracked in Jenkins
- Model artifacts are archived

## 🔄 Comparison: Jenkins vs Cron Job

| Feature | Jenkins Cron | System Cron |
|---------|--------------|-------------|
| **Scheduling** | Built into Jenkins | Requires crontab setup |
| **Visibility** | Visible in Jenkins UI | Requires log checking |
| **Notifications** | Jenkins email plugin | Requires mail setup |
| **Artifact Storage** | Jenkins archive | Manual file management |
| **Build History** | Tracked in Jenkins | Manual logging |
| **Dependencies** | Requires Jenkins running | Independent |

**Recommendation:** Use Jenkins for production CI/CD, use system cron as backup.

## 📝 Summary

**How Jenkins runs weekly training automatically:**

1. ✅ **Cron trigger** in Jenkinsfile: `cron('H 2 * * 0')`
2. ✅ **Jenkins scheduler** checks every minute if it's time to run
3. ✅ **Build starts** automatically when schedule matches
4. ✅ **BUILD_CAUSE** is set to `'TIMERTRIGGER'`
5. ✅ **Pipeline condition** detects timer trigger
6. ✅ **Training stage** executes automatically
7. ✅ **Model is trained** and saved with timestamp

No manual intervention needed! 🎉

