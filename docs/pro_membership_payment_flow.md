# Pro Membership Payment Flow

## Current skeleton

- Apply `database/membership.sql` in Supabase before enabling payment callbacks.
- `public.users` stores the effective membership state:
  - `membership_status`: `inactive`, `active`, `expired`, `cancelled`
  - `membership_plan`
  - `membership_started_at`
  - `membership_expires_at`
  - `membership_updated_at`
- `public.membership_orders` stores provider order records and webhook payloads.
- `GET /membership/status` returns the current user's effective membership status.
- Frontend pages refresh membership status on show and update cached `authUser`.

## Real payment flow

1. Frontend selects a plan and asks backend to create a membership order.
2. Backend creates a `membership_orders` row with `status = pending`.
3. Backend calls the payment provider and returns provider checkout data to the frontend.
4. Payment provider sends a signed webhook to the backend.
5. Backend verifies the webhook signature and provider order id.
6. Backend marks the matching order as `paid` and stores `raw_payload`.
7. Backend updates `public.users` with:
   - `membership_status = active`
   - `membership_plan = selected plan`
   - `membership_started_at = now()`
   - `membership_expires_at = calculated expiry`
   - `membership_updated_at = now()`
8. Frontend calls `GET /membership/status` and unlocks Pro UI.

## Security notes

- Do not let the frontend update membership fields directly.
- Use backend service role only for membership updates.
- Verify webhook signatures before changing order or user membership state.
- Keep real payment secrets only in backend deployment environment variables.
