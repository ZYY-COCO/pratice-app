  -- 考研圈互动性能与幂等增量。
  -- 在 Supabase SQL Editor 执行一次；执行前应已完成 circle_community.sql、
  -- circle_community_comment_likes.sql、circle_community_experience_review.sql
  -- 和 circle_community_experience_stages_and_idempotency.sql。

  begin;

  alter table public.circle_community_comments
    add column if not exists client_request_id uuid;

  create unique index if not exists uq_circle_community_comments_author_client_request
    on public.circle_community_comments (author_id, client_request_id)
    where author_id is not null and client_request_id is not null;

  create index if not exists idx_circle_community_comments_visible_post_created
    on public.circle_community_comments (post_id, created_at desc, id desc)
    where is_published = true;

  create or replace function public.circle_community_comment_previews(
    p_post_ids uuid[],
    p_limit_per_post integer default 3
  )
  returns table (
    id uuid,
    post_id uuid,
    author_name text,
    content text,
    created_at timestamptz
  )
  language sql
  stable
  security definer
  set search_path = public
  as $$
    with ranked as (
      select
        comment.id,
        comment.post_id,
        comment.author_name,
        comment.content,
        comment.created_at,
        row_number() over (
          partition by comment.post_id
          order by comment.created_at desc, comment.id desc
        ) as position
      from public.circle_community_comments as comment
      where comment.post_id = any(coalesce(p_post_ids, '{}'::uuid[]))
        and comment.is_published = true
    )
    select ranked.id, ranked.post_id, ranked.author_name, ranked.content, ranked.created_at
    from ranked
    where ranked.position <= greatest(1, least(coalesce(p_limit_per_post, 3), 3))
    order by ranked.post_id, ranked.created_at desc, ranked.id desc;
  $$;

  create or replace function public.circle_community_create_comment(
    p_post_id uuid,
    p_user_id uuid,
    p_content text,
    p_client_request_id uuid
  )
  returns table (
    comment_id uuid,
    post_id uuid,
    author_id uuid,
    author_name text,
    author_avatar text,
    author_avatar_url text,
    content text,
    created_at timestamptz,
    like_count integer,
    comment_count integer,
    post_author_id uuid,
    post_title text,
    post_type text,
    created boolean
  )
  language plpgsql
  security definer
  set search_path = public
  as $$
  #variable_conflict use_column
  declare
    selected_post public.circle_community_posts%rowtype;
    selected_comment public.circle_community_comments%rowtype;
    selected_user public.users%rowtype;
    public_name text;
    inserted_now boolean := false;
  begin
    if p_user_id is null or p_client_request_id is null then
      raise exception 'Comment identity is required';
    end if;
    if char_length(btrim(coalesce(p_content, ''))) not between 1 and 500 then
      raise exception 'Comment content length is invalid';
    end if;

    select post.*
    into selected_post
    from public.circle_community_posts as post
    where post.id = p_post_id
      and post.is_published = true
    for update;
    if not found then
      raise exception 'Circle post not found';
    end if;

    select app_user.*
    into selected_user
    from public.users as app_user
    where app_user.id = p_user_id;
    public_name := coalesce(
      nullif(btrim(selected_user.nickname), ''),
      nullif(split_part(coalesce(selected_user.email, ''), '@', 1), ''),
      '研友'
    );

    select comment.*
    into selected_comment
    from public.circle_community_comments as comment
    where comment.author_id = p_user_id
      and comment.client_request_id = p_client_request_id
    limit 1;

    if found then
      if selected_comment.post_id <> p_post_id
         or selected_comment.content <> btrim(p_content) then
        raise exception 'Comment request id conflicts with another payload';
      end if;
    else
      insert into public.circle_community_comments (
        post_id,
        author_id,
        author_name,
        author_avatar,
        content,
        client_request_id
      )
      values (
        p_post_id,
        p_user_id,
        public_name,
        left(public_name, 1),
        btrim(p_content),
        p_client_request_id
      )
      on conflict (author_id, client_request_id)
        where author_id is not null and client_request_id is not null
      do nothing
      returning * into selected_comment;

      inserted_now := found;
      if not inserted_now then
        select comment.*
        into selected_comment
        from public.circle_community_comments as comment
        where comment.author_id = p_user_id
          and comment.client_request_id = p_client_request_id
        limit 1;
      end if;
    end if;

    if selected_comment.id is null then
      raise exception 'Circle comment create failed';
    end if;

    return query
    select
      selected_comment.id,
      selected_comment.post_id,
      selected_comment.author_id,
      selected_comment.author_name,
      selected_comment.author_avatar,
      nullif(btrim(selected_user.avatar_url), ''),
      selected_comment.content,
      selected_comment.created_at,
      greatest(coalesce(selected_comment.like_count, 0), 0),
      greatest(coalesce(post.comment_count, 0), 0),
      selected_post.author_id,
      selected_post.title,
      selected_post.post_type,
      inserted_now
    from public.circle_community_posts as post
    where post.id = p_post_id;
  end;
  $$;

  create or replace function public.circle_community_set_like(
    p_post_id uuid,
    p_user_id uuid,
    p_is_liked boolean
  )
  returns table (is_liked boolean, like_count integer, changed boolean)
  language plpgsql
  security definer
  set search_path = public
  as $$
  declare
    liked_before boolean;
    liked_after boolean;
    current_count integer;
  begin
    perform 1
    from public.circle_community_posts as post
    where post.id = p_post_id and post.is_published = true
    for update;
    if not found then
      raise exception 'Circle post not found';
    end if;

    select exists(
      select 1 from public.circle_community_likes as item
      where item.post_id = p_post_id and item.user_id = p_user_id
    ) into liked_before;

    if p_is_liked then
      insert into public.circle_community_likes (post_id, user_id)
      values (p_post_id, p_user_id)
      on conflict (post_id, user_id) do nothing;
    else
      delete from public.circle_community_likes as item
      where item.post_id = p_post_id and item.user_id = p_user_id;
    end if;

    select exists(
      select 1 from public.circle_community_likes as item
      where item.post_id = p_post_id and item.user_id = p_user_id
    ) into liked_after;
    select count(*)::integer into current_count
    from public.circle_community_likes as item
    where item.post_id = p_post_id;

    update public.circle_community_posts as post
    set like_count = current_count
    where post.id = p_post_id;

    return query select liked_after, current_count, liked_before is distinct from liked_after;
  end;
  $$;

  create or replace function public.circle_community_set_comment_like(
    p_post_id uuid,
    p_comment_id uuid,
    p_user_id uuid,
    p_is_liked boolean
  )
  returns table (is_liked boolean, like_count integer, changed boolean)
  language plpgsql
  security definer
  set search_path = public
  as $$
  declare
    liked_before boolean;
    liked_after boolean;
    current_count integer;
  begin
    perform 1
    from public.circle_community_comments as comment
    join public.circle_community_posts as post on post.id = comment.post_id
    where comment.id = p_comment_id
      and comment.post_id = p_post_id
      and comment.is_published = true
      and post.is_published = true
    for update of comment;
    if not found then
      raise exception 'Circle comment not found';
    end if;

    select exists(
      select 1 from public.circle_community_comment_likes as item
      where item.comment_id = p_comment_id and item.user_id = p_user_id
    ) into liked_before;

    if p_is_liked then
      insert into public.circle_community_comment_likes (comment_id, user_id)
      values (p_comment_id, p_user_id)
      on conflict (comment_id, user_id) do nothing;
    else
      delete from public.circle_community_comment_likes as item
      where item.comment_id = p_comment_id and item.user_id = p_user_id;
    end if;

    select exists(
      select 1 from public.circle_community_comment_likes as item
      where item.comment_id = p_comment_id and item.user_id = p_user_id
    ) into liked_after;
    select count(*)::integer into current_count
    from public.circle_community_comment_likes as item
    where item.comment_id = p_comment_id;

    update public.circle_community_comments as comment
    set like_count = current_count
    where comment.id = p_comment_id;

    return query select liked_after, current_count, liked_before is distinct from liked_after;
  end;
  $$;

  create or replace view public.circle_community_feed_rows
  with (security_invoker = true)
  as
  select
    post.id,
    post.author_id,
    post.author_name,
    post.author_avatar,
    post.author_tone,
    post.post_type,
    post.category,
    post.experience_stages,
    post.title,
    left(post.content, 320) as content,
    case jsonb_array_length(coalesce(post.media, '[]'::jsonb))
      when 0 then '[]'::jsonb
      when 1 then jsonb_build_array(post.media -> 0)
      else jsonb_build_array(post.media -> 0, post.media -> 1)
    end as media,
    jsonb_array_length(coalesce(post.media, '[]'::jsonb))::integer as media_count,
    post.like_count,
    post.comment_count,
    post.view_count,
    post.is_published,
    post.is_featured,
    post.review_status,
    post.review_version,
    post.review_reason_code,
    post.review_note,
    post.reviewed_at,
    post.submitted_at,
    post.created_at,
    lower(concat_ws(' ', post.author_name, post.category, post.title, post.content)) as search_text
  from public.circle_community_posts as post;

  revoke all on function public.circle_community_comment_previews(uuid[], integer)
    from public, anon, authenticated;
  revoke all on function public.circle_community_create_comment(uuid, uuid, text, uuid)
    from public, anon, authenticated;
  revoke all on function public.circle_community_set_like(uuid, uuid, boolean)
    from public, anon, authenticated;
  revoke all on function public.circle_community_set_comment_like(uuid, uuid, uuid, boolean)
    from public, anon, authenticated;
  grant execute on function public.circle_community_comment_previews(uuid[], integer) to service_role;
  grant execute on function public.circle_community_create_comment(uuid, uuid, text, uuid) to service_role;
  grant execute on function public.circle_community_set_like(uuid, uuid, boolean) to service_role;
  grant execute on function public.circle_community_set_comment_like(uuid, uuid, uuid, boolean) to service_role;

  revoke all on public.circle_community_feed_rows from public, anon, authenticated;
  grant select on public.circle_community_feed_rows to service_role;

  commit;

  notify pgrst, 'reload schema';
