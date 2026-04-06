-- Record each graded quiz attempt: log user_activity and, when XP > 0, update user_stats + streak
-- (same streak rules as apply_activity). Unlike apply_activity, this is NOT idempotent per day—each
-- attempt creates a row and awards XP when earned.

create or replace function public.apply_quiz_attempt_record(
  p_user_id uuid,
  p_xp_awarded integer,
  p_occurred_at timestamptz default now(),
  p_metadata jsonb default '{}'::jsonb
)
returns jsonb
language plpgsql
security definer
set search_path = public
as $$
declare
  day_start timestamptz;
  s public.user_stats%rowtype;
  new_current integer;
  new_longest integer;
  last_day_start timestamptz;
begin
  if p_xp_awarded < 0 then
    raise exception 'p_xp_awarded must be >= 0';
  end if;

  day_start := (date_trunc('day', p_occurred_at at time zone 'utc') at time zone 'utc');

  perform pg_advisory_xact_lock(
    hashtextextended(p_user_id::text || ':apply_quiz_attempt_record', 0)
  );

  insert into public.user_activity (user_id, activity_type, xp_awarded, metadata, occurred_at)
  values (p_user_id, 'quiz_attempt', p_xp_awarded, p_metadata, p_occurred_at);

  if p_xp_awarded = 0 then
    select * into s from public.user_stats where user_id = p_user_id;
    if not found then
      return jsonb_build_object('xp_awarded', 0, 'user_stats', 'null'::jsonb);
    end if;
    return jsonb_build_object('xp_awarded', 0, 'user_stats', to_jsonb(s));
  end if;

  insert into public.user_stats (user_id)
  values (p_user_id)
  on conflict (user_id) do nothing;

  select *
  into s
  from public.user_stats
  where user_id = p_user_id
  for update;

  if s.user_id is null then
    raise exception 'user_stats row missing for %', p_user_id;
  end if;

  if s.last_active_at is null then
    new_current := 1;
  else
    last_day_start := (date_trunc('day', s.last_active_at at time zone 'utc') at time zone 'utc');
    if last_day_start = day_start then
      new_current := greatest(s.current_streak_days, 1);
    elsif last_day_start = (day_start - interval '1 day') then
      new_current := greatest(s.current_streak_days, 0) + 1;
    else
      new_current := 1;
    end if;
  end if;

  new_longest := greatest(s.longest_streak_days, new_current);

  update public.user_stats
  set
    xp_total = xp_total + p_xp_awarded,
    level = public.xp_to_level(xp_total + p_xp_awarded),
    current_streak_days = new_current,
    longest_streak_days = new_longest,
    last_active_at = greatest(coalesce(last_active_at, p_occurred_at), p_occurred_at),
    updated_at = now()
  where user_id = p_user_id
  returning *
  into s;

  return jsonb_build_object(
    'xp_awarded', p_xp_awarded,
    'user_stats', to_jsonb(s)
  );
end;
$$;

comment on function public.apply_quiz_attempt_record(uuid, integer, timestamptz, jsonb) is
  'Log a quiz_attempt activity and award XP + streak when xp > 0; always appends user_activity.';

revoke all on function public.apply_quiz_attempt_record(uuid, integer, timestamptz, jsonb) from public;
grant execute on function public.apply_quiz_attempt_record(uuid, integer, timestamptz, jsonb) to service_role;
