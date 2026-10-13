-- Read-only verification on the final recorded S08B synthetic database.
-- Each ordered row_to_json stream is SHA256 hashed locally; raw rows stay private.
SELECT row_to_json(t)::text FROM ydental_supply_slot t ORDER BY id;
SELECT row_to_json(t)::text FROM ydental_intake_referral t ORDER BY id;
SELECT row_to_json(t)::text FROM ydental_intake_price t ORDER BY id;
SELECT count(*) FROM ydental_supply_slot
 WHERE ydental_total < 0 OR ydental_reservation_free < 0
    OR ydental_walkin_free < 0 OR ydental_unavailable < 0;
SELECT sum(ydental_total), sum(ydental_reservation_free),
       sum(ydental_walkin_free), sum(ydental_unavailable)
 FROM ydental_supply_slot;
