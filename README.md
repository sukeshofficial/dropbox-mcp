# 🗂️ Dropbox File Management Tool

A powerful Python-based Dropbox file manager using the [`mcp`](https://pypi.org/project/mcp/) agent framework. Easily manage, upload, download, delete, move, rename, and restore files and folders from your Dropbox account.

---

## 🚀 Features

- ✅ Upload single or multiple files (from URL or local path)
- 📥 Download any file to a temporary path
- ❌ Delete files or folders
- ✏️ Rename files or folders
- 📂 Move files or folders across directories
- ♻️ Restore previous file revisions
- 🔍 Search files and folders
- 🕵️‍♂️ List files, folders, and file revisions

---

## 📦 Tech Stack

- Python 3.8+
- [Dropbox SDK](https://github.com/dropbox/dropbox-sdk-python)
- [mcp](https://pypi.org/project/mcp/)

---

## ⚙️ Setup

1. **Clone the repository**
   ```bash
   git clone https://github.com/your-username/dropbox-mcp-tool.git
   cd dropbox-mcp-tool
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Authenticate Dropbox**

You must authenticate your Dropbox using OAuth2 and save the token securely.

Create a `.env` file (or however you store tokens securely)

```env
DROPBOX_ACCESS_TOKEN=your_access_token_here
```

---

## 🛠️ Available Tools

Each method is defined using `@mcp.tool()` decorator. Here are the tools:

### 🔽 Download
```python
download_file_to_tmp(path: str, name: Optional[str])
```

### 🗑️ Delete
```python
delete_file_or_folder(path: str)
```

### 📃 List Contents
```python
list_files_and_folders(path: str, recursive=True, ...)
```

### 🔍 Search
```python
search_files_folders(query: str, max_results=10)
```

### 🕰️ Revisions
```python
list_file_revisions(path: str, mode: Optional[str], limit: Optional[int])
```

### ♻️ Restore File
```python
restore_file(path: str, rev: str)
```

### ✏️ Rename
```python
rename_file_folder(path_from: str, new_name: str, ...)
```

### 📁 Move
```python
move_file_folder(path_from: str, path_to: str, ...)
```

### 📤 Upload (Single)
```python
upload_file_to_dropbox(file_url=None, file_path=None, ...)
```

### 📤 Upload (Multiple)
```python
upload_multiple_files_to_dropbox(file_urls=[], file_paths=[], filenames=[], ...)
```

---

## 🧪 Example Usage

```python
res = upload_file_to_dropbox(
    file_path="/home/user/report.pdf",
    dropbox_folder_path="/reports",
    file_name="report.pdf",
)
print(res)
```

---

## 📌 Notes

- All exceptions are gracefully handled and return structured error responses.
- File validation (e.g., renaming rules) is enforced to avoid API rejections.
- Requires valid Dropbox API access token.

---

## 🧾 License

MIT License © 2025 [@sukeshofficial]

---

## 🤝 Contributions

Pull requests are welcome! Please open an issue first for major changes.
