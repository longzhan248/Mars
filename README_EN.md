# Mars Log Analyzer System - Professional Edition

A powerful Mars/WeChat xlog file parsing and analysis tool with batch processing, advanced filtering, module grouping, and data visualization features.

## 🌟 Key Features

### Core Features
- ✅ **Batch Processing**: Support folder and single file selection with smart file grouping
- ✅ **Parallel Processing**: Multi-threaded parsing for significant speed improvement
- ✅ **Module Grouping**: Auto-detect and group different modules (mars::stn, HY-Default, etc.)
- ✅ **Advanced Filtering**: Combine keyword, regex, time range, and log level filters
- ✅ **Data Visualization**: Pie charts, bar charts, time distribution graphs
- ✅ **Lazy Loading**: Optimized for large files, smooth display of millions of logs
- ✅ **Export Functions**: Export current view, module reports, filtered results

### Supported Log Levels
- FATAL
- ERROR
- WARNING
- INFO
- DEBUG
- VERBOSE

### Time Filter Formats
- Full format: `YYYY-MM-DD HH:MM:SS`
- Time only: `HH:MM:SS` (compares time portion only)
- Date only: `YYYY-MM-DD` (auto-expands to full day)

## 🚀 Quick Start

### System Requirements

#### macOS
- macOS 10.12 or higher
- Python 3.6+
- ~100MB available disk space

#### Windows
- Windows 10/11
- Python 3.6+
- ~100MB available disk space

#### Linux
- Ubuntu 18.04+ / CentOS 7+
- Python 3.6+
- tkinter support

### Installation

#### Method 1: Using Launch Scripts (Recommended)

**Mac/Linux:**
```bash
# 1. Clone or download the project
git clone <repository-url>
cd mars-log-analyzer

# 2. Add execute permission
chmod +x run_analyzer.sh

# 3. Run (auto-installs dependencies)
./run_analyzer.sh
```

**Windows:**
```cmd
# 1. Clone or download the project
git clone <repository-url>
cd mars-log-analyzer

# 2. Double-click run_analyzer.bat
# Or run in command line:
run_analyzer.bat
```

#### Method 2: Cross-platform Python Script
```bash
python3 run_analyzer.py
```

## 📖 User Guide

### 1. Load Log Files

#### Select Folder
- Click "Select Folder" button
- Choose directory containing `.xlog` files
- System auto-scans and groups similar files

#### Select Single File
- Click "Select File" button
- Choose specific `.xlog` file to analyze

### 2. Parse Logs

Click "Start Parsing":
- Progress bar shows parsing status
- Supports parallel processing
- Auto-loads first file group when complete

### 3. Log Viewing

#### Global Filtering
- **Keyword Search**: Support text and regex
- **Time Range**: Enter start and end times
- **Log Level**: Select levels to display
- **Module Filter**: Choose specific modules

Click "Apply Filter" for combined filtering.

### 4. Module Grouping

Switch to "Module Grouping" tab:
- Left panel shows all modules
- Shows log count and error/warning stats
- Click module to view detailed logs

### 5. Statistics

View charts and analytics:
- Log level distribution pie chart
- Module distribution statistics
- File parsing statistics
- Error/warning trends

### 6. Export Functions

#### Log View Page
- **Export Current View**: Export filtered logs
- **Export Group Report**: Export by modules
- **Export Full Report**: Export all analysis

#### Module Group Page
- **Export Current Module**: Export selected module logs
- **Export Filtered Results**: Export filtered logs
- **Export All Modules**: Batch export to directory

## 🎯 Use Cases

### Case 1: Find Errors in Time Range
1. Enter time range: `10:00:00` to `11:00:00`
2. Select log level: `ERROR`
3. Click "Apply Filter"

### Case 2: Analyze Module Issues
1. Switch to "Module Grouping"
2. Select problematic module (e.g., `mars::stn`)
3. Search keywords like "timeout" or "failed"

### Case 3: Export Error Report
1. Select `ERROR` and `FATAL` levels
2. Apply filter
3. Click "Export Current View"

## ⚙️ Advanced Features

### Regular Expression Search
Select "Regex" mode for complex pattern matching:
- `error.*timeout` - Find lines with both error and timeout
- `\d{3,}ms` - Find response times over 100ms
- `(failed|error|exception)` - Find any of these keywords

### Flexible Time Formats
- `2025-01-15 10:30:00` - Exact timestamp
- `10:30:00` - Today at 10:30
- `2025-01-15` - Full day's logs

## 🔧 Troubleshooting

### Program Won't Start

**Mac/Linux:**
```bash
# Check Python version
python3 --version

# Install tkinter
# Mac: brew install python-tk
# Linux: sudo apt-get install python3-tk
```

**Windows:**
- Ensure Python installation included "Add to PATH"
- Reinstall Python with "Install for all users" option

### Parse Failures or Garbled Text

Possible causes:
1. xlog file is encrypted (requires key)
2. File is corrupted
3. Unsupported format version

### Memory Issues

For very large files (>1GB):
1. Close other programs to free memory
2. Process files in batches
3. Use filters to reduce displayed content

## 📊 Performance Metrics

- Parse speed: ~50-100MB/sec (CPU dependent)
- Memory usage: ~2-3x file size
- Parallel processing: Up to 4 concurrent files
- UI response: Smooth display of millions of logs

## 📄 License

MIT License - See LICENSE file for details

## 📮 Contact

- Issues: [GitHub Issues](https://github.com/your-repo/issues)
- Email: your-email@example.com

---

**Version:** 1.0.0
**Last Updated:** January 2024