#!/usr/bin/env bash
# Update GitHub repo metadata after: gh auth login -h github.com
set -euo pipefail

OWNER="${OWNER:-amulyavarshney}"
REPO="${REPO:-AI-Enhanced-Attendance-Operations-Platform}"
NEW_NAME="${NEW_NAME:-AI-Enhanced-Attendance-Operations-Platform}"
DESCRIPTION="${DESCRIPTION:-Production-ready attendance platform with JWT/RBAC, self check-in, audit logs, Azure OpenAI insights, and Docker Compose.}"
HOMEPAGE="${HOMEPAGE:-https://amulyavarshney.github.io/AI-Enhanced-Attendance-Operations-Platform/}"

gh api -X PATCH "repos/${OWNER}/${REPO}" \
  -f name="$NEW_NAME" \
  -f description="$DESCRIPTION" \
  -f homepage="$HOMEPAGE" \
  -F has_pages=true

echo "Updated ${OWNER}/${NEW_NAME}"
echo "Enable Pages: Settings → Pages → Source = GitHub Actions"
echo "Force-push rewritten history only if intentional:"
echo "  git push --force-with-lease origin main"
