"""Admin routes: document CRUD, import, index maintenance, dashboards."""

from __future__ import annotations

import math
import os

from flask import (Blueprint, current_app, flash, jsonify, redirect, render_template,
                   request, session, url_for)

from core.seed_data import import_text_file
from indexing.graph_builder import related_documents

bp = Blueprint("admin", __name__, url_prefix="/admin")

ALLOWED_UPLOAD_EXTENSIONS = {".txt", ".md", ".text"}
MAX_UPLOAD_BYTES = 2 * 1024 * 1024      # 2 MB per file
MAX_UPLOAD_FILES = 20
MAX_TITLE = 200
MAX_CONTENT = 200_000


def service():
    return current_app.extensions["nexasearch"]


def _clean(value, limit=MAX_TITLE) -> str:
    if value is None:
        return ""
    return " ".join(str(value).split())[:limit]


def _admin_required(view):
    """Session gate for mutating admin actions (demo authentication)."""
    def wrapper(*args, **kwargs):
        if not session.get("admin_logged_in"):
            flash("Please sign in with the demo admin account to make changes.", "warning")
            return redirect(url_for("admin.login", next=request.path))
        return view(*args, **kwargs)
    wrapper.__name__ = view.__name__
    return wrapper


@bp.route("/")
def admin_home():
    svc = service()
    page = max(1, request.args.get("page", 1, type=int) or 1)
    category = _clean(request.args.get("category", "all"), 60) or "all"
    sort = _clean(request.args.get("sort", "newest"), 30) or "newest"
    search_term = _clean(request.args.get("q", ""), 120)
    per_page = 8
    documents, total = svc.db.list_documents(per_page, (page - 1) * per_page,
                                            category, sort, "desc", search_term)
    return render_template(
        "admin.html",
        title="Admin Dashboard",
        documents=documents,
        total=total, page=page,
        pages=math.ceil(total / per_page) if total else 0,
        categories=svc.db.categories(),
        category=category, sort=sort, search_term=search_term,
        dashboard=svc.dashboard(),
        recent=svc.db.recent_searches(8),
        logged_in=session.get("admin_logged_in", False),
    )


@bp.route("/login", methods=["GET", "POST"])
def login():
    svc = service()
    if request.method == "POST":
        username = _clean(request.form.get("username", ""), 60)
        password = str(request.form.get("password", ""))[:200]
        user = svc.db.authenticate(username, password)
        if user and user.get("role") == "admin":
            session["admin_logged_in"] = True
            session["admin_username"] = user["username"]
            flash("Signed in as admin.", "success")
            return redirect(url_for("admin.admin_home"))
        flash("Invalid credentials. Demo login: admin / nexasearch123", "error")
    return render_template("login.html", title="Admin Sign In",
                           next=request.args.get("next", ""))


@bp.route("/logout")
def logout():
    session.pop("admin_logged_in", None)
    session.pop("admin_username", None)
    flash("Signed out.", "info")
    return redirect(url_for("admin.admin_home"))


@bp.route("/document/new", methods=["GET", "POST"])
@_admin_required
def new_document():
    svc = service()
    if request.method == "POST":
        title = _clean(request.form.get("title", ""))
        content = str(request.form.get("content", "") or "")[:MAX_CONTENT]
        category = _clean(request.form.get("category", "Uncategorised"), 80) or "Uncategorised"
        author = _clean(request.form.get("author", "NexaSearch Editorial"), 120)
        url = _clean(request.form.get("url", ""), 400)
        keywords = request.form.get("keywords", "")
        duplicate = svc.db.duplicate_count(title)
        try:
            if not title:
                raise ValueError("A title is required.")
            if len(content.strip()) < 10:
                raise ValueError("Content must be at least 10 characters long.")
            doc_id = svc.db.add_document(title, content, category, author, url, keywords)
            svc.reindex_document(doc_id)
            message = f"Document '{title}' added and indexed."
            if duplicate:
                message += " Note: a document with this title already existed."
            flash(message, "success")
            return redirect(url_for("admin.admin_home"))
        except ValueError as exc:
            flash(str(exc), "error")
        except Exception as exc:  # pragma: no cover - defensive
            current_app.logger.exception("add document failed")
            flash(f"Could not save the document: {exc}", "error")
    return render_template("document_form.html", title="Add Document",
                           doc=None, categories=svc.db.categories(),
                           logged_in=True, recent=svc.db.recent_searches(6))


@bp.route("/document/<int:doc_id>/edit", methods=["GET", "POST"])
@_admin_required
def edit_document(doc_id: int):
    svc = service()
    doc = svc.db.get_document(doc_id)
    if not doc:
        flash("That document no longer exists.", "error")
        return redirect(url_for("admin.admin_home"))
    if request.method == "POST":
        try:
            updated = svc.db.update_document(
                doc_id,
                title=_clean(request.form.get("title", "")),
                content=str(request.form.get("content", "") or "")[:MAX_CONTENT],
                category=_clean(request.form.get("category", "Uncategorised"), 80),
                author=_clean(request.form.get("author", ""), 120),
                url=_clean(request.form.get("url", ""), 400),
                keywords=request.form.get("keywords", ""),
            )
            if updated:
                svc.reindex_document(doc_id)
                flash(f"Document #{doc_id} updated and re-indexed.", "success")
                return redirect(url_for("admin.admin_home"))
            flash("Nothing to update.", "warning")
        except Exception as exc:  # pragma: no cover - defensive
            current_app.logger.exception("update failed")
            flash(f"Could not update the document: {exc}", "error")
    return render_template("document_form.html", title="Edit Document",
                           doc=doc, categories=svc.db.categories(),
                           logged_in=True, recent=svc.db.recent_searches(6))


@bp.route("/document/<int:doc_id>/delete", methods=["POST"])
@_admin_required
def delete_document(doc_id: int):
    svc = service()
    if svc.db.delete_document(doc_id):
        svc.remove_document(doc_id)
        flash(f"Document #{doc_id} deleted and removed from the index.", "success")
    else:
        flash("Document not found.", "error")
    return redirect(url_for("admin.admin_home"))


@bp.route("/document/<int:doc_id>")
def preview_document(doc_id: int):
    svc = service()
    doc = svc.db.get_document(doc_id)
    if not doc:
        flash("Document not found.", "error")
        return redirect(url_for("admin.admin_home"))
    return render_template("document.html", title=doc["title"], doc=doc,
                           node=next((n for n in svc.graph["nodes"] if n["id"] == doc_id), None),
                           related=related_documents(svc.graph, doc_id, 6),
                           recent=svc.db.recent_searches(6))


@bp.route("/import", methods=["GET", "POST"])
@_admin_required
def import_documents():
    svc = service()
    if request.method == "POST":
        imported = failed = 0
        messages: list[str] = []
        files = request.files.getlist("documents")
        if not files:
            flash("Choose at least one .txt file to import.", "error")
            return redirect(url_for("admin.import_documents"))
        if len(files) > MAX_UPLOAD_FILES:
            flash(f"Import at most {MAX_UPLOAD_FILES} files at a time.", "error")
            return redirect(url_for("admin.import_documents"))
        for storage in files:
            name = storage.filename or ""
            extension = os.path.splitext(name)[1].lower()
            if extension not in ALLOWED_UPLOAD_EXTENSIONS:
                failed += 1
                messages.append(f"{name}: unsupported extension (allowed: .txt, .md)")
                continue
            raw = storage.read(MAX_UPLOAD_BYTES + 1)
            if len(raw) > MAX_UPLOAD_BYTES:
                failed += 1
                messages.append(f"{name}: larger than 2 MB")
                continue
            try:
                content = raw.decode("utf-8", errors="replace")
                if len(content.strip()) < 10:
                    failed += 1
                    messages.append(f"{name}: file is empty")
                    continue
                doc_id = import_text_file(svc.db, os.path.basename(name), content)
                svc.reindex_document(doc_id)
                imported += 1
            except Exception as exc:  # pragma: no cover - defensive
                current_app.logger.exception("import failed for %s", name)
                failed += 1
                messages.append(f"{name}: {exc}")
        if imported:
            flash(f"Imported {imported} document(s); {failed} skipped.", "success")
        else:
            flash(f"Nothing imported. {failed} file(s) skipped.", "error")
        for message in messages[:8]:
            flash(message, "warning")
        return redirect(url_for("admin.admin_home"))
    return render_template("import.html", title="Import Documents",
                           categories=svc.db.categories(), logged_in=True,
                           recent=svc.db.recent_searches(6),
                           sample_dir=os.path.relpath(
                               os.path.join(os.path.dirname(os.path.dirname(
                                   os.path.abspath(__file__))), "data", "sample_documents")))


@bp.route("/reindex", methods=["POST"])
@_admin_required
def reindex():
    svc = service()
    info = svc.rebuild(reason="admin-triggered")
    flash(f"Full re-index finished in {info['total_time_ms']} ms "
          f"({info['documents']} documents, {info['vocabulary']} terms).", "success")
    return redirect(url_for("admin.admin_home"))


@bp.route("/history/clear", methods=["POST"])
@_admin_required
def clear_history():
    removed = service().db.clear_history()
    flash(f"Cleared {removed} search history entr{'y' if removed == 1 else 'ies'}.", "success")
    return redirect(url_for("search.home"))


@bp.route("/history/<int:entry_id>/delete", methods=["POST"])
@_admin_required
def delete_history(entry_id: int):
    service().db.delete_search(entry_id)
    flash("History entry removed.", "info")
    return redirect(request.referrer or url_for("search.home"))


@bp.route("/stats")
def stats():
    svc = service()
    dashboard = svc.dashboard()
    if request.args.get("format") == "json":
        return jsonify(dashboard)
    return render_template("stats.html", title="System Statistics",
                           dashboard=dashboard, recent=svc.db.recent_searches(6))
