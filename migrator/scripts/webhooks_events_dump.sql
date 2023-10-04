COPY (
  SELECT
    id,
    created,
    updated,
    receiver_id,
    user_id,
    payload,
    payload_headers,
    response,
    response_headers,
    response_code
  FROM webhooks_events
) TO STDOUT WITH (FORMAT binary);
