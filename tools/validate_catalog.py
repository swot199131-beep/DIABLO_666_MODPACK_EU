from pathlib import Path
from urllib.parse import urlparse
import json
import sys

ROOT = Path(__file__).resolve().parents[1]
catalog = json.loads((ROOT / "catalog.json").read_text(encoding="utf-8"))
errors = []
seen = set()

for module in catalog.get("modules", []):
    mid = module.get("id")
    if not mid or mid in seen:
        errors.append(f"Missing or duplicate module id: {mid!r}")
    seen.add(mid)

    preview = module.get("preview")
    if not preview or not (ROOT / "assets" / preview).is_file():
        errors.append(f"{mid}: missing preview file {preview!r}")

    status = module.get("status")
    if module.get("manual_import_enabled"):
        source = module.get("source_url", "")
        host = urlparse(source).hostname or ""
        allowed = module.get("manual_import_domains", [])
        if not source.startswith("https://") or not any(
            host == domain or host.endswith("." + domain) for domain in allowed
        ):
            errors.append(f"{mid}: local import source host is not in its allowed HTTPS domain list")
        if not allowed:
            errors.append(f"{mid}: local import has no allowed source domains")
        if not module.get("manual_import_patterns"):
            errors.append(f"{mid}: local import has no primary filename patterns")
    if module.get("blocked_reason") and module.get("manual_import_enabled"):
        errors.append(f"{mid}: blocked module must not allow local import")
    if status in ("ready", "upstream_release"):
        if module.get("redistribution_permission") not in ("confirmed", "license_allows_redistribution"):
            errors.append(f"{mid}: ready package has no confirmed redistribution permission")
        if not module.get("source_url", "").startswith("https://"):
            errors.append(f"{mid}: ready package has no HTTPS source URL")
        if status == "ready" and not module.get("sha256"):
            errors.append(f"{mid}: ready package has no SHA-256 manifest")
        if status == "upstream_release":
            if not module.get("release_api", "").startswith("https://api.github.com/repos/"):
                errors.append(f"{mid}: upstream release API URL is missing")
            if not module.get("release_tag"):
                errors.append(f"{mid}: upstream release tag is not pinned")
            if not module.get("dependencies"):
                errors.append(f"{mid}: upstream package dependencies are not declared")
        else:
            package_dir = ROOT / "packages" / module.get("package_dir", "")
            if not package_dir.is_dir() or not any(package_dir.iterdir()):
                errors.append(f"{mid}: ready package directory is missing or empty")

if errors:
    print("CATALOG VALIDATION FAILED")
    for err in errors:
        print(" -", err)
    sys.exit(1)

print(f"Catalog OK: {len(catalog.get('modules', []))} modules")
print("No placeholder or external-only module is treated as an installable package.")
