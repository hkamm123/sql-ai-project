# AI + SQL Experiment Report

## Overview

This report evaluates two natural-language questions generated through the AI-to-SQL application. The first query produced a useful and apparently correct percentage. The second query executed successfully but answered a different question than the one the user asked.

The results demonstrate an important limitation of natural-language SQL systems: a query can be syntactically valid and return plausible data while still using the wrong interpretation of the question.

## Question That Worked

### Question

> What percentage of Jordan Rivera's total money has been spent?

### Generated SQL

```sql
WITH jordan_categories AS (
    SELECT c.category_id, c.max_amount
    FROM category AS c
    JOIN budget AS b ON b.budget_id = c.budget_id
    JOIN user AS u ON u.user_id = b.owner_id
    WHERE u.name = 'Jordan Rivera'
)
SELECT
    100.0 * (
        SELECT COALESCE(SUM(e.amount), 0)
        FROM expense AS e
        JOIN jordan_categories AS c ON c.category_id = e.category_id
    ) / NULLIF(
        (SELECT SUM(max_amount) FROM jordan_categories),
        0
    ) AS percentage_spent;
```

### Query Result

```text
[(95.13752045826514,)]
```

### Generated Friendly Response

> Jordan Rivera has spent approximately 95.14% of their total money.

### Evaluation

This query worked because it consistently calculated one overall percentage:

```text
total expenses for Jordan Rivera
-------------------------------- × 100
total budget amount for Jordan Rivera
```

The result was approximately **95.14%**. The SQL correctly:

- Found Jordan Rivera's budget categories.
- Added expenses across those categories.
- Added the maximum amounts for those categories.
- Divided total spending by total budget.
- Used `NULLIF` to avoid division by zero.
- Used `COALESCE` to treat missing expenses as zero.

### Important Clarification

The phrase “total money” is somewhat ambiguous. In this query, it means Jordan's total budget limit, not Jordan's income, bank balance, or available cash. A more precise response would be:

> Jordan Rivera has spent approximately 95.14% of the combined budget limits represented in the database.

## Question That Did Not Work Correctly

### Question

> Who has spent all of their money?

### Generated SQL

```sql
SELECT DISTINCT u.user_id, u.name
FROM user AS u
JOIN budget AS b ON b.owner_id = u.user_id
JOIN category AS c ON c.budget_id = b.budget_id
LEFT JOIN (
    SELECT category_id, SUM(amount) AS total_spent
    FROM expense
    GROUP BY category_id
) AS e ON e.category_id = c.category_id
GROUP BY u.user_id, u.name, b.budget_id
HAVING SUM(COALESCE(e.total_spent, 0)) >= SUM(c.max_amount);
```

### Query Result

```text
[(1, 'Jordan Rivera')]
```

### Generated Friendly Response

> Jordan Rivera has spent all of their money.

### Why This Result Is Misleading

The query groups by `b.budget_id`:

```sql
GROUP BY u.user_id, u.name, b.budget_id
```

That means the `HAVING` condition is evaluated separately for each budget. It does **not** compare Jordan Rivera's total spending across all budgets with Jordan Rivera's total budget amount.

Jordan's budget results were:

| Budget | Spent | Limit | Percentage |
|---|---:|---:|---:|
| June | $5,567.33 | $6,110.00 | 91.12% |
| July | $6,222.41 | $6,110.00 | 101.84% |
| August | $5,489.63 | $6,110.00 | 89.85% |
| September | $5,972.24 | $6,110.00 | 97.75% |

Jordan exceeded the budget limit in July. Therefore, the query returns Jordan because **at least one budget was exhausted**, not because Jordan spent 100% of all available money across every budget.

The `DISTINCT` keyword hides the fact that the query may have found only one qualifying budget. It makes the output look like a user-level answer even though the grouping happens at the budget level.

### More Accurate Interpretation

The generated SQL actually answers this question:

> Who has exceeded the limit for at least one individual budget?

A more accurate friendly response would be:

> Jordan Rivera exceeded the limit for the July budget, spending approximately 101.84% of that budget.

## Corrected Version for the Original Question

If “spent all of their money” means total spending across all budgets is greater than or equal to the combined budget limits, the query should aggregate at the user level:

```sql
WITH user_categories AS (
    SELECT
        u.user_id,
        u.name,
        c.category_id,
        c.max_amount
    FROM user AS u
    JOIN budget AS b ON b.owner_id = u.user_id
    JOIN category AS c ON c.budget_id = b.budget_id
),
user_totals AS (
    SELECT
        uc.user_id,
        uc.name,
        SUM(uc.max_amount) AS total_budget,
        COALESCE(SUM(e.total_spent), 0) AS total_spent
    FROM user_categories AS uc
    LEFT JOIN (
        SELECT
            category_id,
            SUM(amount) AS total_spent
        FROM expense
        GROUP BY category_id
    ) AS e ON e.category_id = uc.category_id
    GROUP BY uc.user_id, uc.name
)
SELECT
    user_id,
    name,
    total_spent,
    total_budget,
    100.0 * total_spent / NULLIF(total_budget, 0) AS percentage_spent
FROM user_totals
WHERE total_spent >= total_budget;
```

This version first totals each category, then aggregates those category totals by user. It does not group by an individual budget, so it evaluates the user's complete budget portfolio.

## What This Experiment Demonstrates

The successful query shows that the model can generate useful multi-table SQL involving common table expressions, joins, aggregation, and arithmetic.

The unsuccessful query shows that SQL execution success is not the same as semantic success. The model understood the general idea of budget limits, but it chose the wrong grouping level. It interpreted “all of their money” as “all of one budget” rather than “all budgets owned by that person.”

The friendly-response stage made the problem worse by repeating the model's interpretation without checking whether the SQL actually matched the wording of the question.

## Lessons for Improving the Application

1. Require the model to state the intended grouping level before generating SQL.
2. Include examples that distinguish user-level totals from budget-level totals.
3. Provide column names and SQL results to the friendly-response prompt.
4. Ask the friendly-response model to describe the exact scope of the calculation.
5. Have the application display the generated SQL so users can inspect it.
6. Test semantic correctness separately from whether the SQL executes.

## Conclusion

The AI-to-SQL system performed well on the percentage question because the requested calculation had a clear overall aggregation. It struggled with the “spent all of their money” question because the wording was ambiguous and the generated query grouped data at the wrong level.

This is a useful example of why natural-language database systems require query validation and human review. A successful SQL execution only proves that the query is valid—not that it answered the intended question.
