-- Execute once for existing environments before deploying the idempotent chat API.
alter table public.mentor_consultation_messages
  add column if not exists client_message_id text;

create unique index if not exists uq_mentor_messages_client_delivery
  on public.mentor_consultation_messages (order_id, sender_user_id, client_message_id);
