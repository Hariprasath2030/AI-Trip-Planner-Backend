/*
# Trip Planner tables: profiles, trips, trip_itinerary_items

1. Plain-English summary
   Creates the core data for the AI Trip Planner backend. Each signed-in user
   gets a profile, can create trips, and attach day-by-day itinerary items to
   their trips. Every user can only see and change their own data.

2. New Tables
   - `profiles`
     - `id` (uuid, primary key, matches the auth user's id)
     - `email` (text)
     - `full_name` (text)
     - `avatar_url` (text)
     - `created_at` (timestamptz, defaults to now)
     - `updated_at` (timestamptz, defaults to now, auto-updated on change)
   - `trips`
     - `id` (uuid, primary key)
     - `user_id` (uuid, foreign key to auth.users, cascades on delete, defaults to the authenticated user)
     - `title`, `destination`, `source` (text)
     - `start_date`, `end_date` (date)
     - `budget` (numeric)
     - `interests` (text array)
     - `travelers` (integer, default 1)
     - `description` (text)
     - `status` (text: 'Planning' | 'Upcoming' | 'Completed', default 'Planning')
     - `cover_image_path` (text)
     - `created_at`, `updated_at` (timestamptz)
   - `trip_itinerary_items`
     - `id` (uuid, primary key)
     - `trip_id` (uuid, foreign key to trips, cascades on delete)
     - `day_number` (integer)
     - `title` (text)
     - `category` (text: 'flight' | 'hotel' | 'car' | 'activity' | 'meal' | 'extra')
     - `start_time` (text, e.g. '09:30')
     - `description` (text)
     - `metadata` (jsonb)
     - `created_at`, `updated_at` (timestamptz)

3. Modified Tables
   - None. `auth.users` is referenced read-only via foreign keys.

4. Security
   - Row Level Security is ENABLED on all three tables.
   - Policies are scoped `TO authenticated` and check `auth.uid()`:
     each user can SELECT, INSERT, UPDATE, DELETE only their own profile,
     trips, and itinerary items (itinerary ownership is checked through the
     parent trip).
   - Grants: authenticated gets the CRUD verbs it uses; service_role gets full
     access for the backend server (creating profile rows at sign-up).
   - The API verifies JWTs itself and rejects unauthenticated requests with
     401 before any database call, so `anon` has no privileges at all.

5. Important notes
   - `trips.user_id` defaults to `auth.uid()` so inserts omitting it still
     satisfy the ownership check.
   - `updated_at` is kept fresh by triggers on all three tables.
   - Indexes on `trips.user_id`, `trip_itinerary_items.trip_id`, and
     `trip_itinerary_items.day_number` support the API's query patterns.
   - `delete_own_itinerary_items` / `update_own_itinerary_items` use EXISTS
     subqueries against `trips`; these are safe because RLS on `trips` also
     applies for non-service roles.
*/

CREATE TABLE IF NOT EXISTS profiles (
  id uuid PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
  email text,
  full_name text,
  avatar_url text,
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS trips (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id uuid NOT NULL DEFAULT auth.uid() REFERENCES auth.users(id) ON DELETE CASCADE,
  title text NOT NULL,
  destination text NOT NULL,
  source text,
  start_date date,
  end_date date,
  budget numeric,
  interests text[] NOT NULL DEFAULT '{}',
  travelers integer NOT NULL DEFAULT 1,
  description text,
  status text NOT NULL DEFAULT 'Planning'
    CHECK (status IN ('Planning', 'Upcoming', 'Completed')),
  cover_image_path text,
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS trip_itinerary_items (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  trip_id uuid NOT NULL REFERENCES trips(id) ON DELETE CASCADE,
  day_number integer NOT NULL,
  title text NOT NULL,
  category text NOT NULL
    CHECK (category IN ('flight', 'hotel', 'car', 'activity', 'meal', 'extra')),
  start_time text,
  description text,
  metadata jsonb,
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS trips_user_id_idx ON trips (user_id);
CREATE INDEX IF NOT EXISTS trip_itinerary_items_trip_id_idx ON trip_itinerary_items (trip_id);
CREATE INDEX IF NOT EXISTS trip_itinerary_items_day_idx ON trip_itinerary_items (trip_id, day_number);

-- Keep updated_at fresh automatically.
CREATE OR REPLACE FUNCTION set_updated_at() RETURNS trigger
LANGUAGE plpgsql AS $$
BEGIN
  NEW.updated_at = now();
  RETURN NEW;
END;
$$;

DROP TRIGGER IF EXISTS profiles_set_updated_at ON profiles;
CREATE TRIGGER profiles_set_updated_at
BEFORE UPDATE ON profiles
FOR EACH ROW EXECUTE FUNCTION set_updated_at();

DROP TRIGGER IF EXISTS trips_set_updated_at ON trips;
CREATE TRIGGER trips_set_updated_at
BEFORE UPDATE ON trips
FOR EACH ROW EXECUTE FUNCTION set_updated_at();

DROP TRIGGER IF EXISTS trip_itinerary_items_set_updated_at ON trip_itinerary_items;
CREATE TRIGGER trip_itinerary_items_set_updated_at
BEFORE UPDATE ON trip_itinerary_items
FOR EACH ROW EXECUTE FUNCTION set_updated_at();

ALTER TABLE profiles ENABLE ROW LEVEL SECURITY;
ALTER TABLE trips ENABLE ROW LEVEL SECURITY;
ALTER TABLE trip_itinerary_items ENABLE ROW LEVEL SECURITY;

-- profiles
DROP POLICY IF EXISTS "Users can read own profile" ON profiles;
CREATE POLICY "Users can read own profile"
ON profiles FOR SELECT
TO authenticated
USING (auth.uid() = id);

DROP POLICY IF EXISTS "Users can insert own profile" ON profiles;
CREATE POLICY "Users can insert own profile"
ON profiles FOR INSERT
TO authenticated
WITH CHECK (auth.uid() = id);

DROP POLICY IF EXISTS "Users can update own profile" ON profiles;
CREATE POLICY "Users can update own profile"
ON profiles FOR UPDATE
TO authenticated
USING (auth.uid() = id)
WITH CHECK (auth.uid() = id);

DROP POLICY IF EXISTS "Users can delete own profile" ON profiles;
CREATE POLICY "Users can delete own profile"
ON profiles FOR DELETE
TO authenticated
USING (auth.uid() = id);

-- trips
DROP POLICY IF EXISTS "Users can read own trips" ON trips;
CREATE POLICY "Users can read own trips"
ON trips FOR SELECT
TO authenticated
USING (auth.uid() = user_id);

DROP POLICY IF EXISTS "Users can insert own trips" ON trips;
CREATE POLICY "Users can insert own trips"
ON trips FOR INSERT
TO authenticated
WITH CHECK (auth.uid() = user_id);

DROP POLICY IF EXISTS "Users can update own trips" ON trips;
CREATE POLICY "Users can update own trips"
ON trips FOR UPDATE
TO authenticated
USING (auth.uid() = user_id)
WITH CHECK (auth.uid() = user_id);

DROP POLICY IF EXISTS "Users can delete own trips" ON trips;
CREATE POLICY "Users can delete own trips"
ON trips FOR DELETE
TO authenticated
USING (auth.uid() = user_id);

-- trip_itinerary_items (ownership via parent trip)
DROP POLICY IF EXISTS "Users can read own itinerary items" ON trip_itinerary_items;
CREATE POLICY "Users can read own itinerary items"
ON trip_itinerary_items FOR SELECT
TO authenticated
USING (
  EXISTS (
    SELECT 1 FROM trips
    WHERE trips.id = trip_itinerary_items.trip_id
      AND trips.user_id = auth.uid()
  )
);

DROP POLICY IF EXISTS "Users can insert own itinerary items" ON trip_itinerary_items;
CREATE POLICY "Users can insert own itinerary items"
ON trip_itinerary_items FOR INSERT
TO authenticated
WITH CHECK (
  EXISTS (
    SELECT 1 FROM trips
    WHERE trips.id = trip_itinerary_items.trip_id
      AND trips.user_id = auth.uid()
  )
);

DROP POLICY IF EXISTS "Users can update own itinerary items" ON trip_itinerary_items;
CREATE POLICY "Users can update own itinerary items"
ON trip_itinerary_items FOR UPDATE
TO authenticated
USING (
  EXISTS (
    SELECT 1 FROM trips
    WHERE trips.id = trip_itinerary_items.trip_id
      AND trips.user_id = auth.uid()
  )
)
WITH CHECK (
  EXISTS (
    SELECT 1 FROM trips
    WHERE trips.id = trip_itinerary_items.trip_id
      AND trips.user_id = auth.uid()
  )
);

DROP POLICY IF EXISTS "Users can delete own itinerary items" ON trip_itinerary_items;
CREATE POLICY "Users can delete own itinerary items"
ON trip_itinerary_items FOR DELETE
TO authenticated
USING (
  EXISTS (
    SELECT 1 FROM trips
    WHERE trips.id = trip_itinerary_items.trip_id
      AND trips.user_id = auth.uid()
  )
);

-- Grants: authenticated uses the API-scoped CRUD verbs; service_role backs the
-- Python server (profile creation at sign-up, bypasses RLS).
GRANT SELECT, INSERT, UPDATE, DELETE ON profiles TO authenticated;
GRANT SELECT, INSERT, UPDATE, DELETE ON trips TO authenticated;
GRANT SELECT, INSERT, UPDATE, DELETE ON trip_itinerary_items TO authenticated;
GRANT ALL ON profiles TO service_role;
GRANT ALL ON trips TO service_role;
GRANT ALL ON trip_itinerary_items TO service_role;