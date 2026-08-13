# Reviewer Role Setup

For the MVP, users cannot change their own roles.

After the reviewer's account has been created, assign a role from the trusted Supabase SQL editor:

```sql
update public.profiles
set role = 'reviewer'
where id = (
  select id from auth.users where email = 'reviewer@example.com'
);
```

For a research administrator:

```sql
update public.profiles
set role = 'researcher'
where id = (
  select id from auth.users where email = 'researcher@example.com'
);
```

Do not expose role assignment as a public browser API without a separate authorization design.
