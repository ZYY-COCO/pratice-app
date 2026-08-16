-- One-time cleanup for the retired community demo posts.
-- Related comments, likes, views, and comment likes are removed by foreign-key cascades.
begin;

delete from public.circle_community_posts
where id in (
  '0b46a665-7b7d-4e0c-a62c-f42282f4e101',
  '2fd58d9c-7c70-4d90-9d88-3a261c4847af',
  '423377f8-7fcf-4ddb-a34d-6ea7e25504da',
  'f7cd37cc-bf32-4873-b954-ffa5522d6e0b',
  '7aa84b22-9b9d-4d28-9ef8-7a09d42b0101',
  '7aa84b22-9b9d-4d28-9ef8-7a09d42b0102',
  '7aa84b22-9b9d-4d28-9ef8-7a09d42b0103',
  '7aa84b22-9b9d-4d28-9ef8-7a09d42b0104',
  '7aa84b22-9b9d-4d28-9ef8-7a09d42b0105'
);

commit;
