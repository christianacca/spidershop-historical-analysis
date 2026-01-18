#!/usr/bin/env bash
# Download and extract a GitHub Actions artifact
#
# Usage:
#   download_artifact.sh REPO_OWNER REPO_NAME ARTIFACT_NAME OUTPUT_DIR [RUN_ID]
#
# Arguments:
#   REPO_OWNER    - GitHub repository owner (e.g., "christianacca")
#   REPO_NAME     - GitHub repository name (e.g., "spidershop-historical-analysis")
#   ARTIFACT_NAME - Name of the artifact to download
#   OUTPUT_DIR    - Directory where artifact contents will be extracted
#   RUN_ID        - (Optional) Specific workflow run ID. If omitted, searches all artifacts.
#
# Exit codes:
#   0 - Success
#   1 - Artifact not found
#   2 - Download failed
#   3 - Extraction failed
#   4 - Invalid arguments

set -euo pipefail

# Check arguments
if [ $# -lt 4 ]; then
    echo "Usage: $0 REPO_OWNER REPO_NAME ARTIFACT_NAME OUTPUT_DIR [RUN_ID]" >&2
    exit 4
fi

REPO_OWNER="$1"
REPO_NAME="$2"
ARTIFACT_NAME="$3"
OUTPUT_DIR="$4"
RUN_ID="${5:-}"

# Ensure output directory exists
mkdir -p "$OUTPUT_DIR"

# Find the artifact ID
if [ -n "$RUN_ID" ]; then
    # Search within a specific run
    echo "Finding artifact '$ARTIFACT_NAME' in run $RUN_ID..." >&2
    ARTIFACT_ID=$(gh api \
        "repos/$REPO_OWNER/$REPO_NAME/actions/runs/$RUN_ID/artifacts" \
        -q ".artifacts[] | select(.name == \"$ARTIFACT_NAME\") | .id" || true)
else
    # Search all artifacts (paginated)
    echo "Finding artifact '$ARTIFACT_NAME' across all runs..." >&2
    ARTIFACT_ID=$(gh api \
        "repos/$REPO_OWNER/$REPO_NAME/actions/artifacts" \
        --paginate \
        -q '.artifacts[]' \
        | jq -s "map(select(.name == \"$ARTIFACT_NAME\" and .expired == false))
            | sort_by(.created_at)
            | last
            | .id // empty" || true)
fi

if [ -z "$ARTIFACT_ID" ]; then
    echo "❌ Artifact '$ARTIFACT_NAME' not found" >&2
    exit 1
fi

echo "✅ Found artifact ID: $ARTIFACT_ID" >&2

# Download the artifact as a zip file
TEMP_ZIP="$(mktemp -t artifact-XXXXXX.zip)"
trap "rm -f '$TEMP_ZIP'" EXIT

echo "Downloading artifact..." >&2
if ! gh api "repos/$REPO_OWNER/$REPO_NAME/actions/artifacts/$ARTIFACT_ID/zip" > "$TEMP_ZIP"; then
    echo "❌ Failed to download artifact" >&2
    exit 2
fi

# Extract the zip file
echo "Extracting to $OUTPUT_DIR..." >&2
if ! unzip -o -q "$TEMP_ZIP" -d "$OUTPUT_DIR"; then
    echo "❌ Failed to extract artifact" >&2
    exit 3
fi

echo "✅ Successfully downloaded and extracted '$ARTIFACT_NAME'" >&2
exit 0
