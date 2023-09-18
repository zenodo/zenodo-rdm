COPY (
  SELECT
    id,
    user_id,
    client_id,
    extra_data,
    created,
    updated
  FROM oauthclient_remoteaccount
) TO STDOUT WITH (FORMAT csv);
