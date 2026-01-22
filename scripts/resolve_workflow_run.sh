#!/usr/bin/env bash
# Resolve the latest successful workflow run ID
#
# Usage:
#   resolve_workflow_run.sh WORKFLOW_FILE [BRANCH]
#
# Arguments:
#   WORKFLOW_FILE - Workflow filename (e.g., "scrape.yml")
#   BRANCH        - (Optional) Specific branch to search. If omitted, uses current branch with master fallback.
#
# Output:
#   Prints the workflow run ID to stdout
#
# Exit codes:
#   0 - Success
#   1 - No successful run found
#   2 - Invalid arguments

set -euo pipefail

# Check arguments
if [ $# -lt 1 ]; then
    echo "Usage: $0 WORKFLOW_FILE [BRANCH]" >&2
    exit 2
fi

WORKFLOW_FILE="$1"
DEFAULT_BRANCH="master"

# Determine branch to search
if [ $# -ge 2 ]; then
    # Branch explicitly provided
    CURRENT_BRANCH="$2"
    echo "Searching for workflow runs on specified branch: $CURRENT_BRANCH" >&2
else
    # Detect current branch
    CURRENT_BRANCH=$(git rev-parse --abbrev-ref HEAD 2>/dev/null || echo "$DEFAULT_BRANCH")
    echo "Current branch: $CURRENT_BRANCH" >&2
    echo "Looking for scrape workflow runs on branch: $CURRENT_BRANCH" >&2
fi

# Try current branch first
RUN_ID=$(gh run list \
    --workflow "$WORKFLOW_FILE" \
    --branch "$CURRENT_BRANCH" \
    --status success \
    --limit 1 \
    --json databaseId \
    --jq '.[0].databaseId' 2>/dev/null || echo "")

# Fallback to default branch if no run found and not already on default branch
if [ -z "$RUN_ID" ] && [ "$CURRENT_BRANCH" != "$DEFAULT_BRANCH" ]; then
    echo "No successful run found on $CURRENT_BRANCH, falling back to $DEFAULT_BRANCH" >&2
    RUN_ID=$(gh run list \
        --workflow "$WORKFLOW_FILE" \
        --branch "$DEFAULT_BRANCH" \
        --status success \
        --limit 1 \
        --json databaseId \
        --jq '.[0].databaseId' 2>/dev/null || echo "")
    
    if [ -n "$RUN_ID" ]; then
        echo "✅ Found latest successful run from $DEFAULT_BRANCH: $RUN_ID" >&2
    fi
elif [ -n "$RUN_ID" ]; then
    echo "✅ Found latest successful run from $CURRENT_BRANCH: $RUN_ID" >&2
fi

# Check if we found a run
if [ -z "$RUN_ID" ]; then
    echo "❌ No successful workflow runs found for $WORKFLOW_FILE" >&2
    exit 1
fi

# Output the run ID
echo "$RUN_ID"
