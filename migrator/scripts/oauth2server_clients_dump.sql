COPY (
    SELECT
        row_to_json(clients)
    FROM
        (
            SELECT
                name,
                description,
                website,
                user_id,
                client_id,
                client_secret,
                is_confidential,
                is_internal,
                _redirect_uris,
                _default_scopes
            FROM
                oauth2server_client
        ) as clients
) TO STDOUT;
