import os
import re
import io
import sys
import dropbox
import dropbox.exceptions
import requests
import httpx
import logging

from typing import Union
from tqdm import tqdm
from dropbox import files
from datetime import datetime
from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP
from typing import Any, Dict, List, Optional
from dropbox.sharing import SharedLinkSettings, RequestedVisibility

logger = logging.getLogger(__name__)
load_dotenv()
mcp = FastMCP("dropbox-service")
dbx = dropbox.Dropbox(os.getenv("DROPBOX_ACCESS_TOKEN"))

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

@mcp.tool()
def create_text_file(file_name, content, folder_path=""):
    """
    Creates a text file with specified content in Dropbox.

    :param file_name: Name of the file (e.g., "mydoc.txt")
    :param content: String content to write in the file
    :param folder_path: Path to the folder where the file will be stored (default is root)
    :return: Dropbox response metadata
    """

    if not file_name.endswith(".txt"):
        file_name += ".txt"

    if folder_path and not folder_path.endswith("/"):
        folder_path += "/"

    full_path = f"{folder_path}{file_name}" if folder_path else f"/{file_name}"

    try:
        res = dbx.files_upload(
            content.encode("utf-8"), path=full_path, mode=files.WriteMode.add, mute=True
        )

        print(f"✅ File successfully created: `{file_name}` at {full_path}")
        return {
            "status": "success",
            "message": "Text File Created ✅",
            "path": f"{full_path}",
        }
    except dropbox.exceptions.ApiError as err:
        logger.error(f"Failed creating text file: {err}")
        return {"error": str(err)}


@mcp.tool()
def create_folder(folder_name, parent_path="", autorename=True):
    """
    Creates a folder in Dropbox.

    :param folder_name: Name of the new folder to be created
    :param parent_path: Path where the folder should be created (default is root)
    :param autorename: If True, Dropbox will rename in case of conflict
    :return: Dropbox response metadata
    """

    if parent_path and not parent_path.endswith("/"):
        parent_path += "/"

    full_path = f"{parent_path}{folder_name}" if parent_path else f"/{folder_name}"

    try:
        res = dbx.files_create_folder_v2(path=full_path, autorename=autorename)

        print(f"✅ Folder successfully created: `{res.metadata.name}` at {full_path}")
        return {
            "status": "success",
            "message": "📁 Folder Created ✅",
            "path": f"{full_path}",
        }

    except dropbox.exceptions.ApiError as err:
        logger.error(f"Failed creating folder: {err}")
        return {"error": str(err)}


def get_file_info(path, new_content):
    """
    Check if the file exists and return its existing content + new content.
    """
    try:
        metadata, res = dbx.files_download(path)
        existing_content = res.content.decode("utf-8")
        return True, f"{existing_content}\n{new_content}"
    except dropbox.exceptions.ApiError as e:
        if e.error.is_path() and e.error.get_path().is_not_found():
            return False, new_content
        else:
            raise


@mcp.tool()
def create_or_append_to_text_file(file_name, content, folder_path=""):
    """
    Create or append to a text file in Dropbox.
    """
    if not file_name.endswith(".txt"):
        file_name += ".txt"

    if folder_path and not folder_path.endswith("/"):
        folder_path += "/"

    full_path = f"{folder_path}{file_name}" if folder_path else f"/{file_name}"

    # Check file existence and prepare content
    file_exists, final_content = get_file_info(full_path, content)

    try:
        res = dbx.files_upload(
            final_content.encode("utf-8"),
            full_path,
            mode=files.WriteMode.overwrite,  # Always overwrite with new content
            autorename=not file_exists,  # Autorename only if it's a new file
            mute=True,
        )
        if file_exists:
            print(f"✅ Text successfully appended to the file: {file_name}")
        else:
            print(f"✅ Text file successfully created at: {full_path}")
        return {
            "status": "success",
            "message": "Text successfully appended / created to the file ✅",
            "path": f"{full_path}",
        }

    except dropbox.exceptions.ApiError as err:
        logger.error(f"Failed to create or append to file: {err}")
        return {"error": str(err)}


def get_account_type():
    """
    Returns the Dropbox account type: 'basic', 'plus', 'business', etc.
    """
    res = dbx.users_get_current_account()
    return res.account_type.tag


@mcp.tool()
def create_or_update_share_link(
    path,
    require_password=False,
    link_password=None,
    expires=None,
    access=None,
    allow_download=True,
):
    """
    Creates or updates a share link for a file or folder, with optional password protection and expiration.
    Restrictions are applied based on account type.
    """
    account_type = get_account_type()

    if require_password and not link_password:
        raise ValueError(
            "Since password protection is required, link_password must be provided."
        )

    if account_type == "basic":
        if require_password:
            raise ValueError(
                "Password-protected links are not supported for Basic accounts."
            )
        if expires:
            raise ValueError("Link expiration is not supported for Basic accounts.")

    # Parse expiration date if provided
    if expires:
        expire_dt = datetime.fromisoformat(expires.replace("Z", "+00:00"))
        if expire_dt < datetime.utcnow():
            raise ValueError("Expiration date must be in the future.")
    else:
        expire_dt = None

    settings = SharedLinkSettings(
        requested_visibility=RequestedVisibility.public,
        allow_download=allow_download,
        expires=expire_dt,
        link_password=link_password if require_password else None,
    )

    try:
        response = dbx.sharing_create_shared_link_with_settings(path, settings)
        print(f"✅ Shared link created: {response.url}")
        return {
            "status": "success",
            "message": "Shared link created ✅",
            "path": f"{response.url}",
        }

    except dropbox.exceptions.ApiError as err:
        logger.error(f"Error creating shared link: {err}")
        return {"error": str(err)}


@mcp.tool()
def delete_file_or_folder(path):
    """
    Deletes a file or folder permanently from Dropbox.
    """
    try:
        response = dbx.files_delete_v2(path)
        print(f'✅ "{path}" successfully deleted.')
        return {
            "status": "success",
            "message": "File / Folder Deleted ✅",
            "path": f"{path}",
        }
    except dropbox.exceptions.ApiError as e:
        logger.error(f"❌ Failed to delete '{path}': {e}")
        return {"error": str(e)}


@mcp.tool()
def download_file_to_tmp(path, name=None):
    try:
        metadata, res = dbx.files_download(path)
        ext = os.path.splitext(metadata.name)[1]
        filename = name if name else f"tmp_{metadata.name}"
        tmp_path = os.path.join("/tmp", filename)

        with open(tmp_path, "wb") as f:
            f.write(res.content)

        return {
            "message": f"📥 File downloaded to: {tmp_path}",
            "tmp_path": tmp_path,
            "metadata": metadata,
        }
    except Exception as e:
        return {"error": str(e)}


@mcp.tool()
def list_files_and_folders(
    path,
    recursive=True,
    include_deleted=False,
    include_has_explicit_shared_members=False,
    include_mounted_folders=False,
    include_non_downloadable_files=True,
    limit=None,
):
    try:
        res = dbx.files_list_folder(
            path=path,
            recursive=recursive,
            include_deleted=include_deleted,
            include_has_explicit_shared_members=include_has_explicit_shared_members,
            include_mounted_folders=include_mounted_folders,
            include_non_downloadable_files=include_non_downloadable_files,
            limit=limit,
        )
        return {
            "message": f"📂 Listed contents of {path}",
            "entries": res.entries,
            "has_more": res.has_more,
        }
    except Exception as e:
        return {"error": str(e)}


@mcp.tool()
def list_file_revisions(
    path: str,
    mode: Optional[str] = None,
    limit: Optional[int] = None,
):
    """
    Retrieves a list of file revisions needed to recover previous content.

    Args:
        client (dbx.Dropbox): Authenticated Dropbox client.
        path (str): The file path to list revisions for.
        mode (Optional[str]): 'path' or 'id' mode. Default is 'path'.
        limit (Optional[int]): Maximum number of revisions to return.

    Returns:
        List of file revisions metadata.
    """
    try:
        res = dbx.files_list_revisions(
            path=path,
            mode=mode,
            limit=limit,
        )
        return res.entries
    except dropbox.exceptions.ApiError as e:
        print(f"API error: {e}")
        return {"error": str(e)}


@mcp.tool()
def move_file_folder(
    path_from: str,
    path_to: str,
    autorename: Optional[bool] = False,
    allow_ownership_transfer: Optional[bool] = False,
):
    """
    Moves a file or folder to a different location in the user's Dropbox.

    Args:
        client (dbx.Dropbox): Authenticated Dropbox client.
        path_from (str): The original file/folder path.
        path_to (str): The destination folder path.
        autorename (bool, optional): Automatically rename if there is a conflict. Default False.
        allow_ownership_transfer (bool, optional): Allow ownership transfer on move. Default False.

    Returns:
        The metadata of the moved file/folder on success, None on failure.
    """
    # Extract filename from path_from
    file_name = path_from.rstrip("/").split("/")[-1]
    destination_path = path_to.rstrip("/") + "/" + file_name

    try:
        res = dbx.files_move_v2(
            from_path=path_from,
            to_path=destination_path,
            autorename=autorename,
            allow_ownership_transfer=allow_ownership_transfer,
        )
        print(f'"{path_from}" successfully moved to "{destination_path}"')
        return res.metadata
    except dropbox.exceptions.ApiError as e:
        print(f"Failed to move file/folder: {e}")
        return {"error": str(e)}


@mcp.tool()
def rename_file_folder(
    path_from: str,
    new_name: str,
    autorename: Optional[bool] = False,
    allow_ownership_transfer: Optional[bool] = False,
):
    """
    Renames a file or folder in the user's Dropbox by moving it to the same directory with a new name.

    Args:
        client (dropbox.Dropbox): Authenticated Dropbox client.
        path_from (str): Original file/folder path.
        new_name (str): New name for the file or folder (include extension for files).
        autorename (bool, optional): Auto-rename if there is a conflict. Default False.
        allow_ownership_transfer (bool, optional): Allow ownership transfer on move. Default False.

    Returns:
        Metadata of the renamed file/folder or dict with error if failed.
    """

    # Validate new_name: it should not contain slashes or be empty
    if "/" in new_name or "\\" in new_name or new_name.strip() == "":
        return {
            "error": "Invalid new_name: It must not contain '/' or '\\' and cannot be empty."
        }

    # Optional: Allow only safe characters (alphanumeric, dash, underscore, dot, space)
    if not re.match(r"^[\w\-. ]+$", new_name):
        return {
            "error": "Invalid new_name: Only alphanumeric characters, dashes, underscores, dots, and spaces are allowed."
        }

    # Replace the last segment of the path with the new name
    parts = path_from.rstrip("/").split("/")
    parts[-1] = new_name
    path_to = "/".join(parts)

    try:
        res = dbx.files_move_v2(
            from_path=path_from,
            to_path=path_to,
            autorename=autorename,
            allow_ownership_transfer=allow_ownership_transfer,
        )
        print(f'"{path_from}" successfully renamed to "{new_name}"')
        return {
            "status": "success",
            "message": "Renaming successful ✅",
            "metadata": res.metadata,
        }
    except dropbox.exceptions.ApiError as e:
        return {"status": "error", "message": f"Dropbox API error: {str(e)}"}
    except Exception as e:
        return {"status": "error", "message": f"Unexpected error: {str(e)}"}


@mcp.tool()
def restore_file(
    path: str,
    rev: str | None,
) -> dict | dropbox.files.FileMetadata:
    """
    Restore a previous version of a file in Dropbox.

    Args:
        client (dropbox.Dropbox): Authenticated Dropbox client.
        path (str): The path of the file to restore.
        rev (str or None): The revision ID to restore.

    Returns:
        Metadata of the restored file or an error dictionary.
    """
    if not rev:
        return {"error": "Missing revision ID to restore."}
    try:
        res = dbx.files_restore(path=path, rev=rev)
        print(f"✅ File restored to revision: {rev}")
        return res
    except dropbox.exceptions.ApiError as e:
        print(f"❌ Failed to restore file: {e}")
        return {"error": str(e)}


@mcp.tool()
def search_files_folders(query: str, max_results: int = 10):
    try:
        results = dbx.files_search_v2(
            query, options=dropbox.files.SearchOptions(max_results=max_results)
        )

        matches = (
            results.matches if hasattr(results, "matches") and results.matches else []
        )

        formatted_results = []
        for match in matches:
            metadata = match.metadata.get_metadata()
            formatted_results.append(
                {
                    "name": metadata.name,
                    "path_display": metadata.path_display,
                    "type": (
                        "folder"
                        if isinstance(metadata, dropbox.files.FolderMetadata)
                        else "file"
                    ),
                }
            )

        return {
            "matches": formatted_results,
            "total_matches": len(formatted_results),
            "query": query,
        }

    except dropbox.exceptions.ApiError as e:
        print("❌ Search error:", e)
        return {"matches": [], "total_matches": 0, "query": query, "error": str(e)}


@mcp.tool()
def upload_file_to_dropbox(
    file_url: Optional[str] = None,
    file_path: Optional[str] = None,
    dropbox_folder_path: str = "",
    file_name: str = "",
    autorename: bool = False,
    mute: bool = False,
    strict_conflict: bool = False,
    mode: Optional[str] = None,
    client_modified: Optional[str] = None,  # ISO format string if needed
):
    """
    Uploads a file to Dropbox from a URL or local path.

    Args:
        client (dropbox.Dropbox): Authenticated Dropbox client.
        file_url (str, optional): URL of the file to download and upload.
        file_path (str, optional): Local path to the file to upload.
        dropbox_folder_path (str): Dropbox folder path to upload into (e.g. "/docs/").
        file_name (str): The name for the uploaded file, with extension.
        autorename (bool): If True, auto-renames on conflict.
        mute (bool): If True, suppresses notifications.
        strict_conflict (bool): If True, be strict about conflict.
        mode (str, optional): Write mode ('add', 'overwrite', 'update').
        client_modified (str, optional): Client-modified timestamp in ISO 8601.

    Returns:
        dict: Metadata of the uploaded file or error info.
    """
    if not file_url and not file_path:
        raise ValueError("Must specify either file_url or file_path.")

    try:
        # Get file content
        if file_url:
            response = requests.get(file_url, stream=True)
            response.raise_for_status()
            contents = response.content
        else:
            with open(file_path, "rb") as f:
                contents = f.read()

        # Ensure Dropbox path formatting
        dropbox_path = f"{dropbox_folder_path.rstrip('/')}/{file_name}"

        # Prepare mode tag
        mode_tag = {"add", "overwrite", "update"}
        upload_mode = (
            {"mode": dropbox.files.WriteMode(mode)} if mode in mode_tag else {}
        )

        # Upload the file
        res = dbx.files_upload(
            contents,
            dropbox_path,
            autorename=autorename,
            mute=mute,
            strict_conflict=strict_conflict,
            client_modified=client_modified,
            **upload_mode,
        )

        print(f"✅ File successfully uploaded to '{dropbox_path}'")
        return res

    except dropbox.exceptions.ApiError as e:
        print("❌ Dropbox API error:", e)
        return {"error": str(e)}
    except Exception as e:
        print("❌ Error:", e)
        return {"error": str(e)}


@mcp.tool()
def upload_multiple_files_to_dropbox(
    file_urls: Optional[List[str]] = None,
    file_paths: Optional[List[str]] = None,
    filenames: Optional[List[str]] = None,
    dropbox_folder_path: str = "/",
    autorename: bool = False,
    mute: bool = False,
    strict_conflict: bool = False,
    mode: Optional[str] = None,
):
    """
    Uploads multiple files to a Dropbox folder from URLs and/or local paths.

    Args:
        client (dropbox.Dropbox): Dropbox client instance.
        file_urls (List[str], optional): List of file URLs to upload.
        file_paths (List[str], optional): List of local file paths to upload.
        filenames (List[str]): Filenames for the uploaded files (must match total number of files).
        dropbox_folder_path (str): Dropbox folder path (e.g. "/uploads").
        autorename (bool): Auto-rename on conflict.
        mute (bool): Suppress notifications.
        strict_conflict (bool): Be strict about conflict detection.
        mode (str, optional): Write mode ('add', 'overwrite', 'update').

    Returns:
        List[dropbox.files.FileMetadata]: Uploaded file metadata list or error info.
    """

    file_urls = file_urls or []
    file_paths = file_paths or []
    if not file_urls and not file_paths:
        raise ValueError("Must specify either file_urls or file_paths.")

    total_files = len(file_urls) + len(file_paths)
    if not filenames or len(filenames) != total_files:
        raise ValueError(
            f"Number of filenames ({len(filenames)}) must match total files ({total_files})."
        )

    responses = []
    index = 0

    try:
        # Upload from URLs
        for url in file_urls:
            response = requests.get(url)
            response.raise_for_status()
            content = response.content

            dropbox_path = f"{dropbox_folder_path.rstrip('/')}/{filenames[index]}"
            result = dbx.files_upload(
                content,
                dropbox_path,
                autorename=autorename,
                mute=mute,
                strict_conflict=strict_conflict,
                mode=dropbox.files.WriteMode(mode) if mode else None,
            )
            responses.append(result)
            index += 1

        # Upload from local file paths
        for path in file_paths:
            with open(path, "rb") as f:
                content = f.read()

            dropbox_path = f"{dropbox_folder_path.rstrip('/')}/{filenames[index]}"
            result = dbx.files_upload(
                content,
                dropbox_path,
                autorename=autorename,
                mute=mute,
                strict_conflict=strict_conflict,
                mode=dropbox.files.WriteMode(mode) if mode else None,
            )
            responses.append(result)
            index += 1

        print("✅ Files successfully uploaded to Dropbox.")
        return responses

    except Exception as e:
        print("❌ Upload error:", e)
        return [{"error": str(e)}]


if __name__ == "__main__":
    mcp.run()
