# AI SQL Expense Database

## Description
This database tracks shared household budgets, modeled on the expense-tracking app nononcents. Users own monthly budgets, each budget has its own spending categories with a limit, and members log expenses against those categories. Ask it questions in plain English, like "How much did we spend on groceries in August?" and it answers using the data.

All data is fake: five users, eight budgets, 68 categories and 193 expenses from June to September 2026. The data includes a few traps that real budgeting apps run into. Paychecks are logged as expenses in an "Income" category, budget names aren't consistent ("September 2026", "September", "my budget"), and the same category names repeat across budgets.

## Schema
![Schema](schema.jpg)

* **user**: The people using the app.
* **budget**: A spending period, usually one month, owned by one user.
* **category**: A spending category inside one budget, with a `max_amount` limit in dollars.
* **expense**: A single purchase (or paycheck), with its amount in dollars, the date, its category and the user who logged it.

## Overview of the Files
* **db_bot.py**: Builds the database, creates the prompt for each strategy, sends each question to OpenAI, runs the SQL it returns, then asks OpenAI to turn the results into a friendly answer.
* **setup.sql**: Creates the tables and keys.
* **setupData.sql**: Fills the tables with the fake data.
* **crossDomain/**: Schemas and data for two other databases, a dog show and a library. The cross-domain strategy uses their example questions.
* **config.json**: Holds the OpenAI API key. **Don't share or commit yours.** Copy `config.template.json` to get started.
* **response_\<strategy>_\<time>.json**: Output logs with the prompt, the questions, the generated SQL and the answers. These files aren't committed.
* **[results_notes.md](results_notes.md)**: The questions we asked, the SQL that came back, the answers, and how the models and strategies compared.
* **[raw_results.txt](raw_results.txt)**: The full output from running every question with each model and strategy.

## Prompting Strategies
These three strategies come from the paper [How to Prompt LLMs for Text-to-SQL](https://arxiv.org/abs/2305.11853) (Chang & Fosler-Lussier).

* **Zero-shot**: The prompt has the `CREATE TABLE` statements plus 3 distinct sample values from each column. The paper calls this format "CreateTable + SelectCol 3", and it was the paper's best zero-shot format.
* **Single-domain few-shot**: Zero-shot plus four example questions about this database, each with its correct SQL. In the paper, accuracy went up as more examples were added.
* **Cross-domain few-shot**: Before this database's schema, the prompt shows the schema, sample values and example question/SQL pairs from two other databases (a dog show and a library). This teaches the model the task without giving away answers about this database.

See [results_notes.md](results_notes.md) for example questions that worked and failed, and how the strategies compared, and [raw_results.txt](raw_results.txt) for the actual output of the program.

## Running It
1. `pip install openai`
2. Copy `config.template.json` to `config.json` and add your OpenAI API key.
3. `python db_bot.py`
## Query we thought it did well on

**Question**: "Who likes to shop at Costco?"

We chose this question because we thought it would be a good baseline.

### gpt-5.6-luna, Zero-shot

**GPT SQL Response**:
```sql
SELECT DISTINCT u.name
FROM user AS u
JOIN expense AS e ON e.user_id = u.user_id
WHERE e.name LIKE '%Costco%';
```

**Friendly Response**: Jordan Rivera, Sam Rivera, Casey Nguyen, and Taylor Brooks like to shop at Costco.

### gpt-5.6-luna, Single-domain few-shot

**GPT SQL Response**:
```sql
SELECT u.name, COUNT(*) AS costco_trip_count
FROM expense e
JOIN user u ON e.user_id = u.user_id
WHERE LOWER(e.name) LIKE '%costco%'
GROUP BY u.user_id, u.name
ORDER BY costco_trip_count DESC;
```

**Friendly Response**: Jordan Rivera shops at Costco most often, with 9 trips, followed by Sam Rivera with 5, Casey Nguyen with 4, and Taylor Brooks with 2.

### gpt-5.6-luna, Cross-domain few-shot

**GPT SQL Response**:
```sql
SELECT DISTINCT u.name
FROM user AS u
JOIN expense AS e ON e.user_id = u.user_id
WHERE e.name LIKE '%Costco%';
```

**Friendly Response**: Jordan Rivera, Sam Rivera, Casey Nguyen, and Taylor Brooks like to shop at Costco.

### gpt-4o, Zero-shot

**GPT SQL Response**:
```sql
SELECT u.name
FROM user u
JOIN expense e ON u.user_id = e.user_id
WHERE e.name = "Costco";
```

**Friendly Response**: Jordan Rivera, Sam Rivera, and Taylor Brooks like to shop at Costco based on the expenses recorded in your database.

### gpt-4o, Single-domain few-shot

**GPT SQL Response**:
```sql
select u.name
from expense e
join user u on e.user_id = u.user_id
where e.name like '%Costco%'
group by u.user_id;
```

**Friendly Response**: Jordan Rivera, Sam Rivera, Casey Nguyen, and Taylor Brooks like to shop at Costco.

### gpt-4o, Cross-domain few-shot

**GPT SQL Response**:
```sql
select u.name
from expense e
join user u on e.user_id = u.user_id
where e.name like '%Costco%';
```

**Friendly Response**: Based on the results, Jordan Rivera, Sam Rivera, Casey Nguyen, and Taylor Brooks like to shop at Costco, with Jordan Rivera making the most visits.

### gpt-6-astra, Zero-shot

**GPT SQL Response**:
```sql
SELECT DISTINCT u.user_id, u.name
FROM user AS u
JOIN expense AS e ON e.user_id = u.user_id
WHERE e.name LIKE '%Costco%';
```

**Friendly Response**: Jordan Rivera, Sam Rivera, Casey Nguyen, and Taylor Brooks have Costco-related expenses. These results don’t tell us whether they actually like shopping there.

### gpt-6-astra, Single-domain few-shot

**GPT SQL Response**:
```sql
select u.name, count(*) as costco_trips
from expense e
join user u on e.user_id = u.user_id
where e.name like '%costco%'
group by u.user_id, u.name
order by costco_trips desc;
```

**Friendly Response**: Jordan Rivera has the most recorded Costco trips (9), followed by Sam Rivera (5), Casey Nguyen (4), and Taylor Brooks (2). These results show who shops there, but not whether they like it.

### gpt-6-astra, Cross-domain few-shot

**GPT SQL Response**:
```sql
select distinct u.user_id, u.name
from user u
join expense e on e.user_id = u.user_id
where e.name like '%Costco%';
```

**Friendly Response**: Jordan Rivera, Sam Rivera, Casey Nguyen, and Taylor Brooks have Costco-related expenses. These results don’t tell us whether they like shopping there, though.


## Question that it tripped up on

**Question**: "Who has the least money?"

We chose this question because we thought it would be interesting to see how different models interpret it with different strategies. We found that the question was interpreted the same within one model, regardless of strategy. Different models interpreted the question very differently. Luna saw this question as "who has spent the least money?" and thus did a left join on users and found a user with no expenses. GPT-4o had a similar interpretation but didn't do the left join, so it reported the next user who had spent the least money. It also included its interpretation of the question in its response, which is nice. Astra got closest to what we actually meant by the question, which is finding the user who has the least allocated money left in their budget after subtracting all expenses.

### gpt-5.6-luna, Zero-shot

**GPT SQL Response**:
```sql
SELECT u.name
FROM "user" AS u
LEFT JOIN expense AS e ON e.user_id = u.user_id
GROUP BY u.user_id, u.name
ORDER BY COALESCE(SUM(e.amount), 0) ASC
LIMIT 1;
```

**SQL Result**: `[('Morgan Lee',)]`

**Friendly Response**: Morgan Lee has the least money based on the household’s recorded expenses.

### gpt-5.6-luna, Single-domain few-shot

**GPT SQL Response**:
```sql
SELECT u.name, COALESCE(SUM(e.amount), 0) AS total_spent
FROM user AS u
LEFT JOIN expense AS e ON e.user_id = u.user_id
GROUP BY u.user_id, u.name
ORDER BY total_spent ASC
LIMIT 1;
```

**SQL Result**: `[('Morgan Lee', 0)]`

**Friendly Response**: Morgan Lee has the least money spent, with a total of $0.

### gpt-5.6-luna, Cross-domain few-shot

**GPT SQL Response**:
```sql
SELECT u.name, COALESCE(SUM(e.amount), 0) AS total_spent
FROM "user" AS u
LEFT JOIN expense AS e ON e.user_id = u.user_id
GROUP BY u.user_id, u.name
ORDER BY total_spent ASC
LIMIT 1;
```

**SQL Result**: `[('Morgan Lee', 0)]`

**Friendly Response**: Morgan Lee has the least money spent, with a total of $0.

### gpt-4o, Zero-shot

**GPT SQL Response**:
```sql
SELECT u.name, SUM(e.amount) AS total_expenses
FROM user u
JOIN expense e ON u.user_id = e.user_id
GROUP BY u.user_id
ORDER BY total_expenses ASC
LIMIT 1;
```

**SQL Result**: `[('Taylor Brooks', 418.12)]`

**Friendly Response**: Based on the results, Taylor Brooks has spent the least amount on expenses, totaling $418.12.

### gpt-4o, Single-domain few-shot

**GPT SQL Response**:
```sql
select u.name, sum(e.amount) as total_spent
from expense e
join user u on e.user_id = u.user_id
group by u.user_id
order by total_spent asc
limit 1;
```

**SQL Result**: `[('Taylor Brooks', 418.12)]`

**Friendly Response**: Based on the results, Taylor Brooks has spent the least amount of money, totaling $418.12.

### gpt-4o, Cross-domain few-shot

**GPT SQL Response**:
```sql
select u.name, sum(e.amount) as total_expense
from user u
join expense e on u.user_id = e.user_id
group by u.user_id
order by total_expense asc
limit 1;
```

**SQL Result**: `[('Taylor Brooks', 418.12)]`

**Friendly Response**: Based on the results, Taylor Brooks has the least money, with total expenses amounting to $418.12.

### gpt-6-astra, Zero-shot

**GPT SQL Response**:
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

**SQL Result**: `[('Taylor Brooks', 181.88)]`

**Friendly Response**: Taylor Brooks has the least money remaining in their budget, with $181.88.

### gpt-6-astra, Single-domain few-shot

**GPT SQL Response**:
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

**SQL Result**: `[('Taylor Brooks', 181.88)]`

**Friendly Response**: Taylor Brooks has the least money remaining in their budgets, with $181.88 left.

### gpt-6-astra, Cross-domain few-shot

**GPT SQL Response**:
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

**SQL Result**: `[(5, 'Taylor Brooks', 181.88)]`

**Friendly Response**: Taylor Brooks has the least money remaining in their budgets, with $181.88 left.

## Conclusion

The cost of running this program once was between 50 cents and 1 dollar. Most of that cost was due to Astra.

Interestingly, there are many examples in our results of the single-domain strategy working much better than the cross-domain strategy. Also, not surprisingly, we found GPT Astra to have exceptionally good responses, even going so far as to explain the empirical results and how they may or may not answer the original question (see the Astra responses for "Who likes to shop at Costco?" above). Of course, GPT Astra was much more expensive than the other models, and it often wrote similar queries depending on the strategy that was used.
