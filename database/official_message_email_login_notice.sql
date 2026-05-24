-- Seed/update the official notice shown from the home-page message bell.
-- Safe to run more than once in Supabase SQL editor.

do $$
begin
  if exists (
    select 1
    from public.official_messages
    where title = '登录方式提醒'
  ) then
    update public.official_messages
    set
      content = '目前港研通优先支持邮箱注册和邮箱登录。手机号、微信登录等方式仍在适配中，建议先使用邮箱完成注册和学习数据同步。',
      status = 'published',
      published_at = coalesce(published_at, now()),
      expires_at = null,
      updated_at = now()
    where title = '登录方式提醒';
  else
    insert into public.official_messages (
      title,
      content,
      status,
      published_at,
      expires_at
    )
    values (
      '登录方式提醒',
      '目前港研通优先支持邮箱注册和邮箱登录。手机号、微信登录等方式仍在适配中，建议先使用邮箱完成注册和学习数据同步。',
      'published',
      now(),
      null
    );
  end if;
end $$;
