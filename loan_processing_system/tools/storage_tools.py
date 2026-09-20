from __future__ import annotations

import io
import os
from typing import Any

import PyPDF2


SESSION_STORAGE: dict[str, dict[str, Any]] = {"users": {}, "documents": {}}


def store_user_info(user: dict[str, Any]) -> str:
    """Store a validated loan applicant in in-memory session storage."""
    required_fields = {
        "name", "email", "income", "employment_length", "loan_intent",
        "loan_amount", "current_debt", "loan_default",
    }
    missing = sorted(required_fields - user.keys())
    if missing:
        return f"Error: Missing required fields: {', '.join(missing)}"
    email = str(user["email"])
    SESSION_STORAGE["users"][email] = dict(user)
    return f"User information for {user['name']} stored successfully."


def upload_file(files: dict[str, dict[str, str]] | None = None) -> str:
    """Store local loan documents in session storage for agent review."""
    if not files:
        return "No files provided."
    supported = {"identity_proof", "income_document", "bank_statement", "credit_report"}
    uploaded: list[str] = []
    for document_type, file_info in files.items():
        if document_type not in supported:
            return f"Error: Unsupported document type '{document_type}'."
        if not all(key in file_info for key in ("filename", "path", "user_email")):
            return f"Error: Invalid file information for {document_type}."
        path = file_info["path"]
        if not os.path.exists(path):
            return f"Error: File not found at path '{path}'."
        with open(path, "rb") as document_file:
            content = document_file.read()
        email = file_info["user_email"]
        SESSION_STORAGE["documents"].setdefault(email, {})[document_type] = {
            "filename": file_info["filename"],
            "raw_content": content,
            "file_path": path,
            "size": len(content),
            "document_type": document_type,
        }
        uploaded.append(f"{email}/{document_type}/{file_info['filename']}")
    return f"Stored {len(uploaded)} document(s): {', '.join(uploaded)}"


def _extract_pdf_text(content: bytes) -> str:
    reader = PyPDF2.PdfReader(io.BytesIO(content))
    return "\n".join(page.extract_text() or "" for page in reader.pages).strip()


def fetch_documents_from_session(user_email: str) -> dict[str, Any]:
    """Fetch all uploaded documents and extract text for an applicant."""
    documents = SESSION_STORAGE["documents"].get(user_email, {})
    processed: dict[str, Any] = {}
    for document_type, document in documents.items():
        filename = document["filename"]
        content = document["raw_content"]
        if filename.lower().endswith(".pdf"):
            text = _extract_pdf_text(content)
        else:
            text = content.decode("utf-8", errors="replace")
        processed[document_type] = {
            "filename": filename,
            "text_content": text,
            "size": document["size"],
            "document_type": document_type,
        }
    return {"status": "success", "user_email": user_email, "documents": processed,
            "document_count": len(processed)}


def fetch_user_from_session(user_email: str) -> dict[str, Any]:
    """Fetch stored applicant data by email address."""
    user = SESSION_STORAGE["users"].get(user_email)
    if user is None:
        return {"status": "not_found", "user_email": user_email, "user_data": {}}
    return {"status": "success", "user_email": user_email, "user_data": user}


def get_session_status() -> dict[str, Any]:
    """Return counts and identifiers in the current session store."""
    return {
        "status": "success",
        "users_count": len(SESSION_STORAGE["users"]),
        "documents_count": sum(len(items) for items in SESSION_STORAGE["documents"].values()),
        "users": list(SESSION_STORAGE["users"]),
    }


def clear_session_storage() -> str:
    """Clear all in-memory applicant and document data."""
    SESSION_STORAGE["users"].clear()
    SESSION_STORAGE["documents"].clear()
    return "Session storage cleared successfully."
