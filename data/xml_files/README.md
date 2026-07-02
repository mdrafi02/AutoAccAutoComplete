# XML Files Directory

## Purpose
Store all Robot Framework `output.xml` files here for training ML models. The system automatically finds and trains on all XML files in this directory and subdirectories.

## How to Add XML Files

### Single File
```bash
# Copy your output.xml file here
cp /path/to/output.xml data/xml_files/my_test_run.xml
```

### Multiple Files
```bash
# Copy multiple files with descriptive names
cp /path/to/test1/output.xml data/xml_files/test_run_001.xml
cp /path/to/test2/output.xml data/xml_files/test_run_002.xml
```

### Subdirectories (Automatically Detected)
```bash
# Files in subdirectories are automatically found
cp /path/to/output.xml data/xml_files/CLS_ROBOTS_RBAC_XML_FILES/test.xml
```

The training system automatically searches all subdirectories for XML files.

## Training

After adding XML files, the model will automatically train:

**Option 1: Automatic (when starting web server)**
```bash
python3 web/web_recommender.py
# Automatically finds and trains on all XML files
```

**Option 2: Manual Training**
```bash
python3 train_with_new_data.py
# Explicitly trains on all XML files
```

## Organization Tips

1. **Subdirectories are supported**: Organize files in subdirectories as needed
   ```
   data/xml_files/
   ├── file1.xml
   ├── CLS_ROBOTS_RBAC_XML_FILES/
   │   ├── file1.xml
   │   └── file2.xml
   └── other_directory/
       └── file3.xml
   ```

2. **Use descriptive names**: Include date, test scenario, or run number
   - `test_run_20240115_001.xml`
   - `smoke_test_001.xml`

3. **No limit**: Add as many XML files as needed - the more, the better the model!

## Notes

- All XML files in this directory and subdirectories are automatically detected
- The more XML files you have, the better your ML model will be
- Training happens automatically when the web server starts (if no model exists)
- Consider using `.gitignore` to exclude large XML files from version control
