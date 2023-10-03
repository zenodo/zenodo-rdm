COPY (
  SELECT
    id,
    created,
    updated,
    github_id,
    name,
    user_id,
    hook
FROM github_repositories
) TO STDOUT WITH (FORMAT binary);
