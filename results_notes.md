# Results Notes

Questions from `raw_results.txt` where the answer changed a lot between models and/or prompting strategies. Each section groups the runs by the result they returned, then lists every run's SQL.

Models: gpt-5.6-luna, gpt-4o, gpt-6-astra. Strategies: zero-shot, single-domain few-shot, cross-domain few-shot.

## Contents

1. who likes to shop at Costco?
2. What percentage of Jordan Rivera's total money has been spent?
3. Who has spent all of their money?
4. Who doesn't have any money?
5. who has the most money?
6. who has the least money?
7. In which of Jordan Rivera's expense catagories has he saved the most money?

## who likes to shop at Costco?

Most runs found the same four people. The differences are in how the SQL matched Costco and whether it removed duplicates.

### Notes

- gpt-4o zero-shot used `e.name = "Costco"` instead of `LIKE '%Costco%'`. That missed Casey and returned duplicate rows.
- gpt-4o cross-domain matched correctly but didn't use `DISTINCT`, so it returned all 20 rows.
- The single-domain runs on luna and astra counted trips per person. That's arguably the best answer to "likes to shop."
- Reference: Jordan has 9 Costco trips, Sam 5, Casey 4 and Taylor 2.

### Results

- **Jordan Rivera; Sam Rivera; Casey Nguyen; Taylor Brooks**: gpt-5.6-luna zero-shot, gpt-5.6-luna cross-domain, gpt-4o single-domain, gpt-6-astra zero-shot, gpt-6-astra cross-domain
- **Jordan Rivera, 9; Sam Rivera, 5; Casey Nguyen, 4; Taylor Brooks, 2**: gpt-5.6-luna single-domain, gpt-6-astra single-domain
- **Jordan Rivera ×3; Sam Rivera ×3; Taylor Brooks ×2**: gpt-4o zero-shot
- **Jordan Rivera ×9; Sam Rivera ×5; Casey Nguyen ×4; Taylor Brooks ×2**: gpt-4o cross-domain

#### gpt-5.6-luna, zero-shot: Jordan Rivera; Sam Rivera; Casey Nguyen; Taylor Brooks

```sql
SELECT DISTINCT u.name
FROM user AS u
JOIN expense AS e ON e.user_id = u.user_id
WHERE e.name LIKE '%Costco%';
```

> Jordan Rivera, Sam Rivera, Casey Nguyen, and Taylor Brooks like to shop at Costco.

#### gpt-5.6-luna, single-domain: Jordan Rivera, 9; Sam Rivera, 5; Casey Nguyen, 4; Taylor Brooks, 2

```sql
SELECT u.name, COUNT(*) AS costco_trip_count
FROM expense e
JOIN user u ON e.user_id = u.user_id
WHERE LOWER(e.name) LIKE '%costco%'
GROUP BY u.user_id, u.name
ORDER BY costco_trip_count DESC;
```

> Jordan Rivera shops at Costco most often, with 9 trips, followed by Sam Rivera with 5, Casey Nguyen with 4, and Taylor Brooks with 2.

#### gpt-5.6-luna, cross-domain: Jordan Rivera; Sam Rivera; Casey Nguyen; Taylor Brooks

```sql
SELECT DISTINCT u.name
FROM user AS u
JOIN expense AS e ON e.user_id = u.user_id
WHERE e.name LIKE '%Costco%';
```

> Jordan Rivera, Sam Rivera, Casey Nguyen, and Taylor Brooks like to shop at Costco.

#### gpt-4o, zero-shot: Jordan Rivera ×3; Sam Rivera ×3; Taylor Brooks ×2

```sql
SELECT u.name
FROM user u
JOIN expense e ON u.user_id = e.user_id
WHERE e.name = "Costco";
```

> Jordan Rivera, Sam Rivera, and Taylor Brooks like to shop at Costco based on the expenses recorded in your database.

#### gpt-4o, single-domain: Jordan Rivera; Sam Rivera; Casey Nguyen; Taylor Brooks

```sql
select u.name
from expense e
join user u on e.user_id = u.user_id
where e.name like '%Costco%'
group by u.user_id;
```

> Jordan Rivera, Sam Rivera, Casey Nguyen, and Taylor Brooks like to shop at Costco.

#### gpt-4o, cross-domain: Jordan Rivera ×9; Sam Rivera ×5; Casey Nguyen ×4; Taylor Brooks ×2

```sql
select u.name
from expense e
join user u on e.user_id = u.user_id
where e.name like '%Costco%';
```

> Based on the results, Jordan Rivera, Sam Rivera, Casey Nguyen, and Taylor Brooks like to shop at Costco, with Jordan Rivera making the most visits.

#### gpt-6-astra, zero-shot: Jordan Rivera; Sam Rivera; Casey Nguyen; Taylor Brooks

```sql
SELECT DISTINCT u.user_id, u.name
FROM user AS u
JOIN expense AS e ON e.user_id = u.user_id
WHERE e.name LIKE '%Costco%';
```

> Jordan Rivera, Sam Rivera, Casey Nguyen, and Taylor Brooks have Costco-related expenses. These results don’t tell us whether they actually like shopping there.

#### gpt-6-astra, single-domain: Jordan Rivera, 9; Sam Rivera, 5; Casey Nguyen, 4; Taylor Brooks, 2

```sql
select u.name, count(*) as costco_trips
from expense e
join user u on e.user_id = u.user_id
where e.name like '%costco%'
group by u.user_id, u.name
order by costco_trips desc;
```

> Jordan Rivera has the most recorded Costco trips (9), followed by Sam Rivera (5), Casey Nguyen (4), and Taylor Brooks (2). These results show who shops there, but not whether they like it.

#### gpt-6-astra, cross-domain: Jordan Rivera; Sam Rivera; Casey Nguyen; Taylor Brooks

```sql
select distinct u.user_id, u.name
from user u
join expense e on e.user_id = u.user_id
where e.name like '%Costco%';
```

> Jordan Rivera, Sam Rivera, Casey Nguyen, and Taylor Brooks have Costco-related expenses. These results don’t tell us whether they like shopping there, though.

## What percentage of Jordan Rivera's total money has been spent?

Five different answers. This question varied the most.

### Notes

- Reference: 95.14%. That's all spending in Jordan's budgets, including Sam's, divided by the total `max_amount` of those budgets. It's 97.14% if the Income category is left out.
- 42.35% (luna zero-shot): Joining budget → category → expense repeats each category's `max_amount` once per expense, which inflates the denominator.
- 36.91% (single-domain on luna and astra): The numerator only counts expenses where `user_id` is Jordan. Sam logs his expenses in Jordan's budgets, so they're left out. The single-domain examples join on `user_id`, which may have encouraged this.
- 12,027% (gpt-4o zero-shot): Divides the total by a single category's `max_amount`.
- 100% (gpt-4o single-domain): Divides Jordan's spending by itself.

### Results

- **42.35**: gpt-5.6-luna zero-shot
- **36.91**: gpt-5.6-luna single-domain, gpt-6-astra single-domain
- **95.14**: gpt-5.6-luna cross-domain, gpt-4o cross-domain, gpt-6-astra zero-shot, gpt-6-astra cross-domain
- **12,027.16**: gpt-4o zero-shot
- **100.00**: gpt-4o single-domain

#### gpt-5.6-luna, zero-shot: 42.35

```sql
SELECT
    100.0 * COALESCE(SUM(e.amount), 0) / NULLIF(SUM(c.max_amount), 0) AS percentage_spent
FROM budget b
JOIN user u ON u.user_id = b.owner_id
JOIN category c ON c.budget_id = b.budget_id
LEFT JOIN expense e ON e.category_id = c.category_id
WHERE u.name = 'Jordan Rivera';
```

> Jordan Rivera has spent approximately **42.35%** of their total budget.

#### gpt-5.6-luna, single-domain: 36.91

```sql
SELECT
    100.0 * COALESCE((
        SELECT SUM(e.amount)
        FROM expense e
        JOIN user u ON e.user_id = u.user_id
        WHERE u.name = 'Jordan Rivera'
    ), 0) / NULLIF((
        SELECT SUM(c.max_amount)
        FROM category c
        JOIN budget b ON c.budget_id = b.budget_id
        JOIN user u ON b.owner_id = u.user_id
        WHERE u.name = 'Jordan Rivera'
    ), 0) AS percentage_spent;
```

> Jordan Rivera has spent approximately **36.91%** of their total budgeted money.

#### gpt-5.6-luna, cross-domain: 95.14

```sql
WITH jordan_budgets AS (
    SELECT b.budget_id
    FROM budget b
    JOIN user u ON u.user_id = b.owner_id
    WHERE u.name = 'Jordan Rivera'
),
total_budget AS (
    SELECT COALESCE(SUM(c.max_amount), 0) AS total_amount
    FROM category c
    JOIN jordan_budgets jb ON jb.budget_id = c.budget_id
),
total_spent AS (
    SELECT COALESCE(SUM(e.amount), 0) AS spent_amount
    FROM expense e
    JOIN category c ON c.category_id = e.category_id
    JOIN jordan_budgets jb ON jb.budget_id = c.budget_id
)
SELECT 100.0 * spent_amount / NULLIF(total_amount, 0) AS percentage_spent
FROM total_budget, total_spent;
```

> Jordan Rivera has spent approximately **95.14%** of their total budget.

#### gpt-4o, zero-shot: 12,027.16

```sql
SELECT 
    (SUM(e.amount) / c.max_amount) * 100 AS percentage_spent
FROM 
    expense e
JOIN 
    user u ON e.user_id = u.user_id
JOIN 
    category c ON e.category_id = c.category_id
WHERE 
    u.name = "Jordan Rivera";
```

> Jordan Rivera has spent approximately 12027.16% of their total allocated money.

#### gpt-4o, single-domain: 100.00

```sql
select (sum(e.amount) / (select sum(e.amount) from expense e2 where e2.user_id = (select user_id from user where name = 'Jordan Rivera'))) * 100 as percentage_spent
from expense e
join user u on e.user_id = u.user_id
where u.name = 'Jordan Rivera';
```

> Jordan Rivera has spent 100% of their total money.

#### gpt-4o, cross-domain: 95.14

```sql
select 
    (select sum(e.amount) 
     from expense e 
     join category c on e.category_id = c.category_id 
     join budget b on c.budget_id = b.budget_id 
     where b.owner_id = 1) 
    /
    (select sum(c.max_amount) 
     from budget b 
     join category c on b.budget_id = c.budget_id 
     where b.owner_id = 1) 
    * 100 as percentage_spent;
```

> Jordan Rivera has spent approximately 95.14% of their total money.

#### gpt-6-astra, zero-shot: 95.14

```sql
WITH category_totals AS (
    SELECT
        c.category_id,
        c.max_amount,
        COALESCE(SUM(e.amount), 0) AS spent
    FROM category AS c
    JOIN budget AS b ON b.budget_id = c.budget_id
    JOIN user AS u ON u.user_id = b.owner_id
    LEFT JOIN expense AS e ON e.category_id = c.category_id
    WHERE u.name = 'Jordan Rivera'
    GROUP BY c.category_id, c.max_amount
)
SELECT 100.0 * SUM(spent) / NULLIF(SUM(max_amount), 0) AS percentage_spent
FROM category_totals;
```

> Jordan Rivera has spent approximately 95.14% of their total budgeted money.

#### gpt-6-astra, single-domain: 36.91

```sql
select
    100.0 * (
        select coalesce(sum(e.amount), 0)
        from expense e
        join user u on e.user_id = u.user_id
        where u.name = 'Jordan Rivera'
    ) / nullif((
        select sum(c.max_amount)
        from category c
        join budget b on c.budget_id = b.budget_id
        join user u on b.owner_id = u.user_id
        where u.name = 'Jordan Rivera'
    ), 0) as percentage_spent;
```

> Jordan Rivera has spent approximately 36.91% of their total money.

#### gpt-6-astra, cross-domain: 95.14

```sql
with category_totals as (
    select c.category_id,
           c.max_amount,
           coalesce(sum(e.amount), 0) as spent
    from category c
    join budget b on c.budget_id = b.budget_id
    join user u on b.owner_id = u.user_id
    left join expense e on e.category_id = c.category_id
    where u.name = 'Jordan Rivera'
    group by c.category_id, c.max_amount
)
select 100.0 * sum(spent) / nullif(sum(max_amount), 0) as percentage_spent
from category_totals;
```

> Jordan Rivera has spent approximately 95.14% of their total budgeted money.

## Who has spent all of their money?

Some runs returned Jordan and others returned no rows.

### Notes

- Reference: Jordan Rivera. His July 2026 budget is over its limit (3,077.94 spent against 2,910, not counting Income).
- The runs that returned no rows compared each user's expenses to the `max_amount` of the categories they personally logged in, instead of comparing per-budget totals.
- Every gpt-4o run returned no rows.

### Results

- **(no rows)**: gpt-5.6-luna zero-shot, gpt-4o zero-shot, gpt-4o single-domain, gpt-4o cross-domain
- **Jordan Rivera**: gpt-5.6-luna single-domain, gpt-5.6-luna cross-domain, gpt-6-astra zero-shot, gpt-6-astra single-domain, gpt-6-astra cross-domain

#### gpt-5.6-luna, zero-shot: (no rows)

```sql
SELECT u.name
FROM user AS u
JOIN expense AS e
  ON e.user_id = u.user_id
JOIN category AS c
  ON c.category_id = e.category_id
GROUP BY u.user_id, u.name
HAVING SUM(e.amount) >= SUM(c.max_amount);
```

> No one was identified as having spent all of their money.

#### gpt-5.6-luna, single-domain: Jordan Rivera

```sql
WITH category_totals AS (
    SELECT
        c.budget_id,
        c.category_id,
        c.max_amount,
        COALESCE(SUM(e.amount), 0) AS spent
    FROM category c
    LEFT JOIN expense e ON e.category_id = c.category_id
    GROUP BY c.budget_id, c.category_id, c.max_amount
)
SELECT u.name
FROM budget b
JOIN user u ON u.user_id = b.owner_id
JOIN category_totals ct ON ct.budget_id = b.budget_id
GROUP BY b.budget_id, u.name
HAVING SUM(ct.spent) >= SUM(ct.max_amount);
```

> Jordan Rivera has spent all of their budgeted money.

#### gpt-5.6-luna, cross-domain: Jordan Rivera

```sql
WITH budget_totals AS (
    SELECT
        b.budget_id,
        b.owner_id,
        SUM(c.max_amount) AS total_budget
    FROM budget b
    JOIN category c
        ON c.budget_id = b.budget_id
    GROUP BY b.budget_id, b.owner_id
),
spending_totals AS (
    SELECT
        b.budget_id,
        COALESCE(SUM(e.amount), 0) AS total_spent
    FROM budget b
    JOIN category c
        ON c.budget_id = b.budget_id
    LEFT JOIN expense e
        ON e.category_id = c.category_id
       AND e.expense_date BETWEEN b.start_date AND b.end_date
    GROUP BY b.budget_id
)
SELECT DISTINCT u.name
FROM budget_totals bt
JOIN spending_totals st
    ON st.budget_id = bt.budget_id
JOIN "user" u
    ON u.user_id = bt.owner_id
WHERE st.total_spent >= bt.total_budget;
```

> Jordan Rivera has spent all of their money.

#### gpt-4o, zero-shot: (no rows)

```sql
SELECT u.user_id, u.name
FROM user u
JOIN expense e ON u.user_id = e.user_id
JOIN category c ON e.category_id = c.category_id
GROUP BY u.user_id
HAVING SUM(e.amount) >= SUM(c.max_amount)
```

> The results are empty, which indicates that there is no one in the database who has spent all of their money according to the query.

#### gpt-4o, single-domain: (no rows)

```sql
select u.name
from (
    select b.budget_id, b.owner_id
    from budget b
    join category c on b.budget_id = c.budget_id
    join expense e on c.category_id = e.category_id
    group by b.budget_id, b.owner_id
    having sum(e.amount) >= sum(c.max_amount)
) as budgets_exceeding
join user u on budgets_exceeding.owner_id = u.user_id;
```

> The results indicate that no one has spent all of their money according to the data in the household budgeting database.

#### gpt-4o, cross-domain: (no rows)

```sql
select u.name
from user u
join expense e on u.user_id = e.user_id
join category c on e.category_id = c.category_id
group by u.user_id
having sum(e.amount) >= sum(c.max_amount);
```

> The results are empty, so there is no information available to answer your question about who has spent all of their money.

#### gpt-6-astra, zero-shot: Jordan Rivera

```sql
WITH budget_limits AS (
    SELECT budget_id, SUM(max_amount) AS total_available
    FROM category
    GROUP BY budget_id
),
budget_spending AS (
    SELECT c.budget_id, SUM(e.amount) AS total_spent
    FROM category AS c
    JOIN expense AS e ON e.category_id = c.category_id
    GROUP BY c.budget_id
)
SELECT DISTINCT u.user_id, u.name
FROM user AS u
JOIN budget AS b ON b.owner_id = u.user_id
JOIN budget_limits AS bl ON bl.budget_id = b.budget_id
JOIN budget_spending AS bs ON bs.budget_id = b.budget_id
WHERE ROUND(bs.total_spent, 2) >= ROUND(bl.total_available, 2);
```

> Jordan Rivera has spent all the money allocated to at least one of their budgets, or more.

#### gpt-6-astra, single-domain: Jordan Rivera

```sql
select distinct u.name
from user u
join budget b on b.owner_id = u.user_id
where (
    select coalesce(sum(e.amount), 0)
    from expense e
    join category c on e.category_id = c.category_id
    where c.budget_id = b.budget_id
) >= (
    select sum(c.max_amount)
    from category c
    where c.budget_id = b.budget_id
);
```

> Jordan Rivera has spent all the money allocated to at least one of their budgets, or more.

#### gpt-6-astra, cross-domain: Jordan Rivera

```sql
with category_spending as (
    select c.category_id, c.budget_id, c.max_amount,
           coalesce(sum(e.amount), 0) as spent
    from category c
    join budget b on b.budget_id = c.budget_id
    left join expense e
        on e.category_id = c.category_id
        and e.expense_date between b.start_date and b.end_date
    group by c.category_id, c.budget_id, c.max_amount
),
exhausted_budgets as (
    select budget_id
    from category_spending
    group by budget_id
    having sum(spent) >= sum(max_amount)
)
select distinct u.user_id, u.name
from user u
join budget b on b.owner_id = u.user_id
join exhausted_budgets eb on eb.budget_id = b.budget_id;
```

> Jordan Rivera has spent all or more of the money allocated to at least one of their budgets.

## Who doesn't have any money?

The question is ambiguous. Models read "no money" as either "no expenses" or "no budget / nothing left."

### Notes

- Morgan Lee: has no expenses and owns no budget.
- Sam Rivera: owns no budget but logs expenses in Jordan's budgets, including paychecks.
- astra single-domain returned no rows because it only looked at users who own budgets.
- This may be worth rewording the question or adding an "income" concept to the schema.

### Results

- **Morgan Lee**: gpt-5.6-luna zero-shot, gpt-5.6-luna single-domain, gpt-5.6-luna cross-domain, gpt-4o zero-shot
- **Sam Rivera; Morgan Lee**: gpt-4o single-domain, gpt-4o cross-domain, gpt-6-astra zero-shot, gpt-6-astra cross-domain
- **(no rows)**: gpt-6-astra single-domain

#### gpt-5.6-luna, zero-shot: Morgan Lee

```sql
SELECT u.name
FROM user AS u
LEFT JOIN expense AS e
  ON e.user_id = u.user_id
GROUP BY u.user_id, u.name
HAVING COALESCE(SUM(e.amount), 0) = 0;
```

> Morgan Lee doesn’t have any money.

#### gpt-5.6-luna, single-domain: Morgan Lee

```sql
SELECT u.name
FROM user AS u
LEFT JOIN expense AS e ON e.user_id = u.user_id
GROUP BY u.user_id, u.name
HAVING COUNT(e.expense_id) = 0;
```

> Morgan Lee doesn't have any recorded expenses.

#### gpt-5.6-luna, cross-domain: Morgan Lee

```sql
SELECT u.user_id, u.name
FROM user AS u
WHERE NOT EXISTS (
    SELECT 1
    FROM expense AS e
    WHERE e.user_id = u.user_id
);
```

> Morgan Lee doesn’t have any expenses recorded, so they’re the one without any money.

#### gpt-4o, zero-shot: Morgan Lee

```sql
SELECT u.user_id, u.name
FROM user u
LEFT JOIN expense e ON u.user_id = e.user_id
WHERE e.user_id IS NULL;
```

> According to the results, Morgan Lee doesn't have any expenses recorded, which might suggest they don't have any money.

#### gpt-4o, single-domain: Sam Rivera; Morgan Lee

```sql
select u.name
from user u
left join budget b on u.user_id = b.owner_id
where b.owner_id is null;
```

> Based on the database query results, Sam Rivera and Morgan Lee don't have any money.

#### gpt-4o, cross-domain: Sam Rivera; Morgan Lee

```sql
select u.user_id, u.name
from user u
left join budget b on u.user_id = b.owner_id
where b.budget_id is null;
```

> Sam Rivera and Morgan Lee currently don't have any money in their budgets.

#### gpt-6-astra, zero-shot: Sam Rivera; Morgan Lee

```sql
WITH category_balances AS (
    SELECT
        c.budget_id,
        c.max_amount - COALESCE(SUM(e.amount), 0) AS remaining
    FROM category AS c
    LEFT JOIN expense AS e ON e.category_id = c.category_id
    GROUP BY c.category_id, c.budget_id, c.max_amount
)
SELECT u.user_id, u.name
FROM user AS u
LEFT JOIN budget AS b ON b.owner_id = u.user_id
LEFT JOIN category_balances AS cb ON cb.budget_id = b.budget_id
GROUP BY u.user_id, u.name
HAVING COALESCE(SUM(cb.remaining), 0) <= 0;
```

> Sam Rivera and Morgan Lee have 0 or less remaining in their category budgets. These results don’t tell us whether they have any money outside those budgets.

#### gpt-6-astra, single-domain: (no rows)

```sql
SELECT u.user_id, u.name
FROM user AS u
JOIN budget AS b ON b.owner_id = u.user_id
JOIN category AS c ON c.budget_id = b.budget_id
LEFT JOIN (
    SELECT category_id, SUM(amount) AS spent
    FROM expense
    GROUP BY category_id
) AS e ON e.category_id = c.category_id
GROUP BY u.user_id, u.name
HAVING SUM(c.max_amount) - SUM(COALESCE(e.spent, 0)) <= 0;
```

> No one matched this query’s criteria, but these results don’t tell us who has no money.

#### gpt-6-astra, cross-domain: Sam Rivera; Morgan Lee

```sql
select u.user_id, u.name
from user u
left join budget b on b.owner_id = u.user_id
left join category c on c.budget_id = b.budget_id
left join (
    select category_id, sum(amount) as spent
    from expense
    group by category_id
) e on e.category_id = c.category_id
group by u.user_id, u.name
having coalesce(sum(c.max_amount - coalesce(e.spent, 0)), 0) <= 0;
```

> The results show no positive remaining budget for Sam Rivera and Morgan Lee, but they don’t tell us whether either person actually has any money.

## who has the most money?

Most runs answered "who spent the most" instead. astra zero-shot and cross-domain calculated remaining budget instead.

### Notes

- Sam Rivera at 14,231.24 is Sam's total expenses. That's the same answer as "who has spent the most money?", and it includes 7,297.92 of paychecks logged under Income.
- Jordan Rivera at 1,188.39 is the money remaining across his budgets. That's a more sensible reading.
- astra's friendly response on the Sam result said the query only shows expenses.

### Results

- **Sam Rivera, 14,231.24**: gpt-5.6-luna zero-shot, gpt-5.6-luna single-domain, gpt-5.6-luna cross-domain, gpt-4o zero-shot, gpt-4o single-domain, gpt-4o cross-domain, gpt-6-astra single-domain
- **Jordan Rivera, 1,188.39**: gpt-6-astra zero-shot, gpt-6-astra cross-domain

#### gpt-5.6-luna, zero-shot: Sam Rivera, 14,231.24

```sql
SELECT u.name, SUM(e.amount) AS total_amount
FROM user AS u
JOIN expense AS e ON e.user_id = u.user_id
GROUP BY u.user_id, u.name
ORDER BY total_amount DESC
LIMIT 1;
```

> Sam Rivera has the most money, with a total of 14,231.24.

#### gpt-5.6-luna, single-domain: Sam Rivera, 14,231.24

```sql
SELECT u.name, SUM(e.amount) AS total_amount
FROM user AS u
JOIN expense AS e ON e.user_id = u.user_id
GROUP BY u.user_id, u.name
ORDER BY total_amount DESC
LIMIT 1;
```

> Sam Rivera has the most money, with a total of 14,231.24.

#### gpt-5.6-luna, cross-domain: Sam Rivera, 14,231.24

```sql
WITH user_totals AS (
    SELECT
        u.user_id,
        u.name,
        COALESCE(SUM(e.amount), 0) AS total_amount
    FROM user AS u
    LEFT JOIN expense AS e ON e.user_id = u.user_id
    GROUP BY u.user_id, u.name
)
SELECT name, total_amount
FROM user_totals
WHERE total_amount = (SELECT MAX(total_amount) FROM user_totals);
```

> Sam Rivera has the most money, with a total of 14,231.24.

#### gpt-4o, zero-shot: Sam Rivera, 14,231.24

```sql
SELECT u.name, SUM(e.amount) AS total_spent
FROM user u
JOIN expense e ON u.user_id = e.user_id
GROUP BY u.name
ORDER BY total_spent DESC
LIMIT 1;
```

> Based on the results, Sam Rivera has the highest total spending of 14,231.24.

#### gpt-4o, single-domain: Sam Rivera, 14,231.24

```sql
select u.name, sum(e.amount) as total_expense
from expense e
join user u on e.user_id = u.user_id
group by u.user_id
order by total_expense desc
limit 1;
```

> Based on the expenses, it seems Sam Rivera has the most money spent with a total of 14,231.24.

#### gpt-4o, cross-domain: Sam Rivera, 14,231.24

```sql
select u.name, sum(e.amount) as total_amount
from user u
join expense e on u.user_id = e.user_id
group by u.user_id
order by total_amount desc
limit 1;
```

> According to the results from the database, Sam Rivera has the most money with a total amount of 14,231.24 in expenses.

#### gpt-6-astra, zero-shot: Jordan Rivera, 1,188.39

```sql
SELECT u.user_id, u.name,
       SUM(c.max_amount - COALESCE(e.total_spent, 0)) AS remaining_money
FROM user AS u
JOIN budget AS b ON b.owner_id = u.user_id
JOIN category AS c ON c.budget_id = b.budget_id
LEFT JOIN (
    SELECT category_id, SUM(amount) AS total_spent
    FROM expense
    GROUP BY category_id
) AS e ON e.category_id = c.category_id
GROUP BY u.user_id, u.name
ORDER BY remaining_money DESC
LIMIT 1;
```

> Jordan Rivera has the most money remaining in their budgets: 1,188.39. These results don’t show who has the most money overall.

#### gpt-6-astra, single-domain: Sam Rivera, 14,231.24

```sql
SELECT u.name, SUM(e.amount) AS total_amount
FROM user AS u
JOIN expense AS e ON e.user_id = u.user_id
GROUP BY u.user_id, u.name
ORDER BY total_amount DESC
LIMIT 1;
```

> These results don’t tell us who has the most money—only who has the highest total expenses. Sam Rivera has the highest total expenses at 14,231.24.

#### gpt-6-astra, cross-domain: Jordan Rivera, 1,188.39

```sql
SELECT u.user_id, u.name,
       SUM(c.max_amount - COALESCE((
           SELECT SUM(e.amount)
           FROM expense e
           WHERE e.category_id = c.category_id
             AND e.expense_date BETWEEN b.start_date AND b.end_date
       ), 0)) AS money_remaining
FROM user u
JOIN budget b ON b.owner_id = u.user_id
JOIN category c ON c.budget_id = b.budget_id
GROUP BY u.user_id, u.name
ORDER BY money_remaining DESC
LIMIT 1;
```

> Jordan Rivera has the most money remaining in their budgets: 1,188.39. These results don’t show who has the most money overall.

## who has the least money?

Three different answers, one per model. Each model interpreted the question the same way across all three strategies.

### Notes

- luna: Morgan Lee with 0 spent. It used a `LEFT JOIN`, so people with no expenses were included.
- gpt-4o: Taylor Brooks with 418.12 spent. It used an inner join, which dropped Morgan.
- astra: Taylor Brooks with 181.88 remaining in their budget. That's budget minus spending.

### Results

- **Morgan Lee**: gpt-5.6-luna zero-shot
- **Morgan Lee, 0**: gpt-5.6-luna single-domain, gpt-5.6-luna cross-domain
- **Taylor Brooks, 418.12**: gpt-4o zero-shot, gpt-4o single-domain, gpt-4o cross-domain
- **Taylor Brooks, 181.88**: gpt-6-astra zero-shot, gpt-6-astra single-domain, gpt-6-astra cross-domain

#### gpt-5.6-luna, zero-shot: Morgan Lee

```sql
SELECT u.name
FROM "user" AS u
LEFT JOIN expense AS e ON e.user_id = u.user_id
GROUP BY u.user_id, u.name
ORDER BY COALESCE(SUM(e.amount), 0) ASC
LIMIT 1;
```

> Morgan Lee has the least money based on the household’s recorded expenses.

#### gpt-5.6-luna, single-domain: Morgan Lee, 0

```sql
SELECT u.name, COALESCE(SUM(e.amount), 0) AS total_spent
FROM user AS u
LEFT JOIN expense AS e ON e.user_id = u.user_id
GROUP BY u.user_id, u.name
ORDER BY total_spent ASC
LIMIT 1;
```

> Morgan Lee has the least money spent, with a total of 0.

#### gpt-5.6-luna, cross-domain: Morgan Lee, 0

```sql
SELECT u.name, COALESCE(SUM(e.amount), 0) AS total_spent
FROM "user" AS u
LEFT JOIN expense AS e ON e.user_id = u.user_id
GROUP BY u.user_id, u.name
ORDER BY total_spent ASC
LIMIT 1;
```

> Morgan Lee has the least money spent, with a total of 0.

#### gpt-4o, zero-shot: Taylor Brooks, 418.12

```sql
SELECT u.name, SUM(e.amount) AS total_expenses
FROM user u
JOIN expense e ON u.user_id = e.user_id
GROUP BY u.user_id
ORDER BY total_expenses ASC
LIMIT 1;
```

> Based on the results, Taylor Brooks has spent the least amount on expenses, totaling 418.12.

#### gpt-4o, single-domain: Taylor Brooks, 418.12

```sql
select u.name, sum(e.amount) as total_spent
from expense e
join user u on e.user_id = u.user_id
group by u.user_id
order by total_spent asc
limit 1;
```

> Based on the results, Taylor Brooks has spent the least amount of money, totaling 418.12.

#### gpt-4o, cross-domain: Taylor Brooks, 418.12

```sql
select u.name, sum(e.amount) as total_expense
from user u
join expense e on u.user_id = e.user_id
group by u.user_id
order by total_expense asc
limit 1;
```

> Based on the results, Taylor Brooks has the least money, with total expenses amounting to 418.12.

#### gpt-6-astra, zero-shot: Taylor Brooks, 181.88

```sql
WITH category_balances AS (
    SELECT
        c.budget_id,
        c.max_amount - COALESCE(SUM(e.amount), 0) AS remaining_money
    FROM category AS c
    LEFT JOIN expense AS e ON e.category_id = c.category_id
    GROUP BY c.category_id
),
user_balances AS (
    SELECT
        u.user_id,
        u.name,
        SUM(cb.remaining_money) AS remaining_money
    FROM user AS u
    JOIN budget AS b ON b.owner_id = u.user_id
    JOIN category_balances AS cb ON cb.budget_id = b.budget_id
    GROUP BY u.user_id, u.name
)
SELECT name, remaining_money
FROM user_balances
WHERE remaining_money = (SELECT MIN(remaining_money) FROM user_balances);
```

> Taylor Brooks has the least money remaining in their budget, with 181.88.

#### gpt-6-astra, single-domain: Taylor Brooks, 181.88

```sql
SELECT u.name,
       SUM(c.max_amount - COALESCE(s.total_spent, 0)) AS money_remaining
FROM user AS u
JOIN budget AS b ON b.owner_id = u.user_id
JOIN category AS c ON c.budget_id = b.budget_id
LEFT JOIN (
    SELECT category_id, SUM(amount) AS total_spent
    FROM expense
    GROUP BY category_id
) AS s ON s.category_id = c.category_id
GROUP BY u.user_id, u.name
ORDER BY money_remaining ASC
LIMIT 1;
```

> Taylor Brooks has the least money remaining in their budgets, with 181.88 left.

#### gpt-6-astra, cross-domain: Taylor Brooks, 181.88

```sql
SELECT u.user_id, u.name,
       SUM(c.max_amount - COALESCE(e.total_spent, 0)) AS money_remaining
FROM user AS u
JOIN budget AS b ON b.owner_id = u.user_id
JOIN category AS c ON c.budget_id = b.budget_id
LEFT JOIN (
    SELECT category_id, SUM(amount) AS total_spent
    FROM expense
    GROUP BY category_id
) AS e ON e.category_id = c.category_id
GROUP BY u.user_id, u.name
ORDER BY money_remaining ASC
LIMIT 1;
```

> Taylor Brooks has the least money remaining in their budgets, with 181.88 left.

## In which of Jordan Rivera's expense catagories has he saved the most money?

Every run that worked answered "Income," but with different amounts. One run failed with an error.

### Notes

- Reference: Misc in September 2026, 114.58 under budget (the next best is Eating Out in September 2026 at 94.03). Income is paychecks, so it isn't an expense category, and no query left it out.
- 1,806.97: only counts expenses Jordan personally logged (joined on `expense.user_id`), so Sam's paychecks in the same Income category aren't subtracted.
- 464.96: scoped to categories in Jordan's budgets (joined on `budget.owner_id`), counting everyone's expenses. 388.56: categories Jordan logged anything in, counting everyone's expenses.
- gpt-4o cross-domain nested `max(... sum(...))`, which SQLite rejects.
- astra's friendly responses noticed Income isn't an expense category in 2 of 3 runs.

### Results

- **Income, 1,806.97**: gpt-5.6-luna zero-shot, gpt-5.6-luna cross-domain, gpt-4o single-domain, gpt-6-astra zero-shot
- **Income, 388.56**: gpt-5.6-luna single-domain
- **Income, 464.96**: gpt-4o zero-shot, gpt-6-astra single-domain
- **Error: `misuse of aggregate function sum()`**: gpt-4o cross-domain
- **Income, August 2026, 464.96**: gpt-6-astra cross-domain

#### gpt-5.6-luna, zero-shot: Income, 1,806.97

```sql
SELECT
    c.name,
    c.max_amount - SUM(e.amount) AS money_saved
FROM user AS u
JOIN expense AS e ON e.user_id = u.user_id
JOIN category AS c ON c.category_id = e.category_id
WHERE u.name = 'Jordan Rivera'
GROUP BY c.category_id, c.name, c.max_amount
ORDER BY money_saved DESC
LIMIT 1;
```

> Jordan Rivera has saved the most money in the Income category, with 1,806.97 saved.

#### gpt-5.6-luna, single-domain: Income, 388.56

```sql
SELECT
    c.name,
    c.max_amount - SUM(e.amount) AS amount_saved
FROM category AS c
JOIN expense AS e
    ON e.category_id = c.category_id
WHERE EXISTS (
    SELECT 1
    FROM expense AS je
    JOIN user AS u
        ON u.user_id = je.user_id
    WHERE je.category_id = c.category_id
      AND u.name = 'Jordan Rivera'
)
GROUP BY c.category_id, c.name, c.max_amount
ORDER BY amount_saved DESC
LIMIT 1;
```

> Jordan Rivera saved the most in the **Income** category, with **388.56** saved.

#### gpt-5.6-luna, cross-domain: Income, 1,806.97

```sql
SELECT
    c.name AS category,
    c.max_amount - SUM(e.amount) AS amount_saved
FROM category AS c
JOIN expense AS e
    ON e.category_id = c.category_id
JOIN "user" AS u
    ON u.user_id = e.user_id
WHERE u.name = 'Jordan Rivera'
GROUP BY c.category_id, c.name, c.max_amount
ORDER BY amount_saved DESC
LIMIT 1;
```

> Jordan Rivera saved the most in the **Income** category, with **1,806.97** saved.

#### gpt-4o, zero-shot: Income, 464.96

```sql
SELECT c.name, (c.max_amount - SUM(e.amount)) AS saved_amount
FROM user u
JOIN budget b ON u.user_id = b.owner_id
JOIN category c ON b.budget_id = c.budget_id
JOIN expense e ON c.category_id = e.category_id
WHERE u.name = 'Jordan Rivera'
GROUP BY c.category_id
ORDER BY saved_amount DESC
LIMIT 1;
```

> Jordan Rivera has saved the most money in the “Income” category, with a total savings of approximately 464.96.

#### gpt-4o, single-domain: Income, 1,806.97

```sql
select c.name, c.max_amount - sum(e.amount) as amount_saved
from expense e
join category c on e.category_id = c.category_id
join user u on e.user_id = u.user_id
where u.name = 'Jordan Rivera'
group by c.category_id, c.max_amount
order by amount_saved desc
limit 1;
```

> Jordan Rivera has saved the most money in the "Income" category, with a total of 1,806.97 saved.

#### gpt-4o, cross-domain: Error: `misuse of aggregate function sum()`

```sql
select c.name, max(c.max_amount - sum(e.amount)) as saved_money
from category c
join expense e on c.category_id = e.category_id
join budget b on c.budget_id = b.budget_id
where b.owner_id = 1
group by c.category_id
having saved_money = (
    select max(c.max_amount - sum(e.amount))
    from category c
    join expense e on c.category_id = e.category_id
    join budget b on c.budget_id = b.budget_id
    where b.owner_id = 1
    group by c.category_id
);
```

Error: `misuse of aggregate function sum()`

#### gpt-6-astra, zero-shot: Income, 1,806.97

```sql
SELECT
    c.name,
    c.max_amount - SUM(e.amount) AS money_saved
FROM category AS c
JOIN expense AS e ON e.category_id = c.category_id
JOIN user AS u ON u.user_id = e.user_id
WHERE u.name = 'Jordan Rivera'
GROUP BY c.category_id, c.name, c.max_amount
ORDER BY money_saved DESC
LIMIT 1;
```

> The result shows “Income” with 1,806.97 saved, but it doesn’t identify an expense category, so it doesn’t answer which expense category Jordan Rivera saved the most in.

#### gpt-6-astra, single-domain: Income, 464.96

```sql
SELECT c.name, c.max_amount - COALESCE(SUM(e.amount), 0) AS money_saved
FROM category c
JOIN budget b ON c.budget_id = b.budget_id
JOIN user u ON b.owner_id = u.user_id
LEFT JOIN expense e ON e.category_id = c.category_id
WHERE u.name = 'Jordan Rivera'
GROUP BY c.category_id
ORDER BY money_saved DESC
LIMIT 1;
```

> The result shows “Income” with 464.96 saved, but it doesn’t identify which expense category Jordan Rivera saved the most money in.

#### gpt-6-astra, cross-domain: Income, August 2026, 464.96

```sql
SELECT c.name, b.name AS budget_name,
       c.max_amount - COALESCE(SUM(e.amount), 0) AS money_saved
FROM category c
JOIN budget b ON c.budget_id = b.budget_id
JOIN user u ON b.owner_id = u.user_id
LEFT JOIN expense e ON c.category_id = e.category_id
WHERE u.name = 'Jordan Rivera'
GROUP BY c.category_id
ORDER BY money_saved DESC
LIMIT 1;
```

> The result shows 464.96 saved in “Income” for August 2026. Since “Income” isn’t an expense category, this doesn’t answer which expense category Jordan saved the most in.

## Consistent across every run, but still suspicious

- **who has spent the most money?** Every run returned Sam Rivera at 14,231.24. That includes 7,297.92 of paychecks in the Income category. Sam is still the top spender without them, but the real total is 6,933.32.
- **which of Casey Nguyen's expenses was the most expensive?** Every run said Rent at 850, but there's a three-way tie (July 5, August 3 and September 3). Only the astra zero-shot and cross-domain runs returned all three.
- **Who spends the most money on eating out?** Every run returned Casey Nguyen at 284.48. No issues found.
