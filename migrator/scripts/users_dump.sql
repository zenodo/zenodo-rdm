COPY (
    SELECT row_to_json(users)
    FROM (
        SELECT
            u.*,
            up.*,
            coalesce(se.created, null) as safelisted_at,
            coalesce(se.notes, null) as safelisted_notes,
            coalesce(user_i.identities, null) AS identities,
            coalesce(user_sa.session_activity, null) AS session_activity
        FROM accounts_user AS u
        LEFT JOIN userprofiles_userprofile up ON u.id = up.user_id
        LEFT JOIN safelist_entries se ON u.id = se.user_id
        LEFT JOIN LATERAL (
            SELECT json_agg(row_to_json(i)) AS identities
            FROM oauthclient_useridentity AS i
            WHERE i.id_user = u.id
        ) AS user_i ON true
        LEFT JOIN LATERAL (
            SELECT json_agg(row_to_json(sa)) AS session_activity
            FROM accounts_user_session_activity AS sa
            WHERE sa.user_id = u.id
        ) AS user_sa ON true
    ) as users
) TO STDOUT;
