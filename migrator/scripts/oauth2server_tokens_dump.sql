COPY (
    SELECT
        row_to_json(tokens)
    FROM
        (
            SELECT
                id,
                client_id,
                user_id,
                token_type,
                access_token,
                refresh_token,
                expires,
                _scopes,
                is_personal,
                is_internal
            FROM
                oauth2server_token
        ) as tokens
) TO STDOUT;
