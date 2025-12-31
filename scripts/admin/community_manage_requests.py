"""Script to handle community manage record requests for any community.

For legacy records (with can_community_manage_record flag) in a community:
- Members: removes the permission flag (they already manage their records)
- Non-members: creates requests asking them to allow community curation

Usage (in Flask shell):
    from scripts.admin.community_manage_requests import create_community_manage_requests

    # Dry run first (default)
    create_community_manage_requests("community-slug")

    # Actually process
    results = create_community_manage_requests("community-slug", dry_run=False)
"""

import json
from datetime import datetime, timezone

from invenio_access.permissions import system_identity
from invenio_communities.proxies import current_communities
from invenio_db import db
from invenio_rdm_records.proxies import current_community_records_service
from invenio_rdm_records.records import RDMRecord
from invenio_requests import current_requests_service
from invenio_search.engine import dsl
from zenodo_rdm.legacy.requests.community_manage_record import CommunityManageRecord
from zenodo_rdm.legacy.requests.utils import submit_community_manage_record_request


def has_open_community_manage_request(user_id):
    """Check if user already has an open community-manage-record request."""
    results = current_requests_service.search(
        system_identity,
        extra_filter=dsl.query.Bool(
            "must",
            must=[
                dsl.Q("term", **{"receiver.user": user_id}),
                dsl.Q("term", **{"type": CommunityManageRecord.type_id}),
                dsl.Q("term", **{"is_open": True}),
            ],
        ),
    )
    return results.total > 0


def get_community_member_user_ids(community_id):
    """Get all user IDs that are members of the community."""
    member_ids = set()

    # Search all members (paginate through results)
    page = 1
    page_size = 100
    while True:
        results = current_communities.service.members.search(
            system_identity,
            community_id,
            params={"size": page_size, "page": page},
        )

        for hit in results.hits:
            # Members can be users or groups; we only care about users
            member = hit.get("member", {})
            if member.get("type") == "user":
                member_ids.add(int(member["id"]))

        if page * page_size >= results.total:
            break
        page += 1

    return member_ids


def get_legacy_records_by_membership(community_id, member_user_ids):
    """Partition legacy records (with permission flag) by owner membership."""
    member_records = []
    non_member_owners = {}

    # Search for records with the permission flag set (legacy records)
    results = current_community_records_service.search(
        system_identity,
        community_id,
        extra_filter=dsl.Q(
            "exists", field="parent.permission_flags.can_community_manage_record"
        ),
        params={"size": 100},
        scan=True,
    )

    for hit in results.hits:
        record_id = hit["id"]

        # Get owner from parent
        parent = hit.get("parent", {})
        access = parent.get("access", {})
        owned_by = access.get("owned_by", {})
        owner_id = owned_by.get("user")

        if owner_id is None:
            continue

        owner_id = int(owner_id)

        if owner_id in member_user_ids:
            # Owner is a member - collect for flag removal
            member_records.append(record_id)
        else:
            # Owner is not a member - collect for request creation
            if owner_id not in non_member_owners:
                non_member_owners[owner_id] = []
            non_member_owners[owner_id].append(record_id)

    return member_records, non_member_owners


def remove_permission_flags(record_ids):
    """Remove can_community_manage_record flag from records."""
    for record_id in record_ids:
        record = RDMRecord.get_record(record_id)
        parent = record.parent
        flags = parent.get("permission_flags", {})
        if "can_community_manage_record" in flags:
            flags.pop("can_community_manage_record")
            parent.permission_flags = flags if flags else None
            parent.commit()
    db.session.commit()


def create_community_manage_requests(community_slug, dry_run=True, output_dir="/ops"):
    """Create community manage record requests for a community.

    For members: removes permission flags from their records.
    For non-members: creates requests to allow community curation.
    """
    operation_results = {
        "flags_removed": 0,  # count of records with flags removed (members)
        "created": [],
        "skipped_existing": [],  # users with existing open requests
        "errors": [],
    }

    # Get community
    community = current_communities.service.read(system_identity, community_slug)
    community_id = community.id
    print(f"Processing community: {community['metadata']['title']} ({community_id})")

    # Get member user IDs
    member_ids = get_community_member_user_ids(community_id)
    print(f"Found {len(member_ids)} community members")

    # Partition legacy records by membership
    member_records, non_member_owners = get_legacy_records_by_membership(
        community_id, member_ids
    )
    print(
        f"Found {len(member_records)} legacy records owned by members (flags to remove)"
    )
    print(f"Found {len(non_member_owners)} non-member owners (requests to create)")

    if dry_run:
        print("\n[DRY RUN] Would process:")
        print(f"  Remove flags from {len(member_records)} member-owned records")
        for user_id, record_ids in non_member_owners.items():
            has_existing = has_open_community_manage_request(user_id)
            status = "(SKIP - has existing request)" if has_existing else ""
            print(f"  User {user_id}: {len(record_ids)} records {status}")
        return operation_results

    # Remove flags from member-owned records
    if member_records:
        print(f"Removing flags from {len(member_records)} member-owned records...")
        remove_permission_flags(member_records)
        operation_results["flags_removed"] = len(member_records)
        print(f"Removed flags from {len(member_records)} records")

    # Create requests for each non-member owner
    for user_id, record_ids in non_member_owners.items():
        try:
            # Check for existing open request
            if has_open_community_manage_request(user_id):
                operation_results["skipped_existing"].append(
                    {
                        "user_id": user_id,
                        "record_count": len(record_ids),
                    }
                )
                print(f"Skipped user {user_id} - already has open request")
                continue

            # Create and submit request for this user
            request_item = submit_community_manage_record_request(user_id)
            operation_results["created"].append(
                {
                    "user_id": user_id,
                    "record_count": len(record_ids),
                    "request_id": str(request_item.id),
                }
            )
            print(f"Created request for user {user_id} ({len(record_ids)} records)")

        except Exception as e:
            operation_results["errors"].append(
                {
                    "user_id": user_id,
                    "error": str(e),
                }
            )
            print(f"Error creating request for user {user_id}: {e}")

    print("\nSummary:")
    print(f"  Flags removed: {operation_results['flags_removed']} records")
    print(f"  Requests created: {len(operation_results['created'])}")
    print(f"  Skipped (existing request): {len(operation_results['skipped_existing'])}")
    print(f"  Errors: {len(operation_results['errors'])}")

    # Save results to JSON file
    output_file = f"{output_dir}/{community_slug}-manager-record-requests.json"
    output = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "community": community_slug,
        "dry_run": dry_run,
        **operation_results,
    }
    with open(output_file, "w") as f:
        json.dump(output, f, indent=2)
    print(f"\nResults saved to {output_file}")

    return operation_results
