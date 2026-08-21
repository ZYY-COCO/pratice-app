-- 前辈咨询真实聚合数据。
-- 执行位置：Supabase SQL Editor。
-- 前置依赖：database/mentor_consultation.sql。

create or replace function public.refresh_mentor_profile_aggregates(target_mentor_id uuid)
returns void
language plpgsql
security definer
set search_path = public
as $$
begin
  update public.mentor_profiles profile
  set consult_count = (
        select count(*)::integer
        from public.mentor_consultation_orders consultation_order
        where consultation_order.mentor_id = target_mentor_id
          and consultation_order.order_status = 'completed'
      ),
      rating_count = (
        select count(*)::integer
        from public.mentor_reviews review
        where review.mentor_id = target_mentor_id
          and review.is_published = true
      ),
      rating = coalesce((
        select round(avg(review.rating), 1)
        from public.mentor_reviews review
        where review.mentor_id = target_mentor_id
          and review.is_published = true
      ), 0),
      updated_at = now()
  where profile.id = target_mentor_id;
end;
$$;

create or replace function public.refresh_mentor_aggregates_from_order()
returns trigger
language plpgsql
security definer
set search_path = public
as $$
begin
  if tg_op <> 'DELETE' then
    perform public.refresh_mentor_profile_aggregates(new.mentor_id);
  end if;
  if tg_op = 'DELETE' then
    perform public.refresh_mentor_profile_aggregates(old.mentor_id);
  elsif tg_op = 'UPDATE' and old.mentor_id is distinct from new.mentor_id then
    perform public.refresh_mentor_profile_aggregates(old.mentor_id);
  end if;
  if tg_op = 'DELETE' then
    return old;
  end if;
  return new;
end;
$$;

create or replace function public.refresh_mentor_aggregates_from_review()
returns trigger
language plpgsql
security definer
set search_path = public
as $$
begin
  if tg_op <> 'DELETE' then
    perform public.refresh_mentor_profile_aggregates(new.mentor_id);
  end if;
  if tg_op = 'DELETE' then
    perform public.refresh_mentor_profile_aggregates(old.mentor_id);
  elsif tg_op = 'UPDATE' and old.mentor_id is distinct from new.mentor_id then
    perform public.refresh_mentor_profile_aggregates(old.mentor_id);
  end if;
  if tg_op = 'DELETE' then
    return old;
  end if;
  return new;
end;
$$;

drop trigger if exists refresh_mentor_aggregates_after_order on public.mentor_consultation_orders;
create trigger refresh_mentor_aggregates_after_order
after insert or delete or update of mentor_id, order_status
on public.mentor_consultation_orders
for each row execute function public.refresh_mentor_aggregates_from_order();

drop trigger if exists refresh_mentor_aggregates_after_review on public.mentor_reviews;
create trigger refresh_mentor_aggregates_after_review
after insert or delete or update of mentor_id, rating, is_published
on public.mentor_reviews
for each row execute function public.refresh_mentor_aggregates_from_review();

update public.mentor_profiles profile
set consult_count = (
      select count(*)::integer
      from public.mentor_consultation_orders consultation_order
      where consultation_order.mentor_id = profile.id
        and consultation_order.order_status = 'completed'
    ),
    rating_count = (
      select count(*)::integer
      from public.mentor_reviews review
      where review.mentor_id = profile.id
        and review.is_published = true
    ),
    rating = coalesce((
      select round(avg(review.rating), 1)
      from public.mentor_reviews review
      where review.mentor_id = profile.id
        and review.is_published = true
    ), 0),
    updated_at = now();
