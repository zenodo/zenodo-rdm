COPY (
  SELECT
    id_remote_account,
    token_type,
    access_token,
    secret,
    created,
    updated
  FROM
    oauthclient_remotetoken
) TO STDOUT WITH (FORMAT csv);
