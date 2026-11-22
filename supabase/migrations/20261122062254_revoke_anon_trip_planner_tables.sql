/*
# Revoke anon privileges on trip planner tables

1. Plain-English summary
   The backend API verifies user tokens itself and only talks to the database
   as signed-in users or the service role. Anonymous (not signed-in) callers
   should have no direct database access at all.

2. Modified Tables
   - `profiles`, `trips`, `trip_itinerary_items`: removes default table
     privileges from the anonymous role. No data is changed.

3. Security
   - Signed-in users keep full owner-scoped access via RLS policies.
   - The service role (used by the backend server) keeps full access.
   - Anonymous callers now get "permission denied" before RLS is even
     evaluated, an extra layer of defense on top of RLS.

4. Important notes
   - This is a hardening step only; no rows are read, added, or removed.
*/

REVOKE ALL ON profiles FROM anon;
REVOKE ALL ON trips FROM anon;
REVOKE ALL ON trip_itinerary_items FROM anon;