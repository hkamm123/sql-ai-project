Explain the discrepancy between theses results:



Question:
What percentage of Jordan Rivera's total money has been spent?
SQL Syntax Response:
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
Query Raw Response:
[(95.13752045826514,)]
Friendly Response:
Jordan Rivera has spent approximately 95.14% of their total money.
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Question:
Who has spent all of their money?
SQL Syntax Response:
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
Query Raw Response:
[(1, 'Jordan Rivera')]
Friendly Response:
Jordan Rivera has spent all of their money.




Because the two queries measure different things.
The “all of their money” query groups expenses by individual budget:
GROUP BY c.budget_id
HAVING spent >= budget_limit
Jordan’s budgets are:
- June: $5,567.33 / $6,110 — 91.12%
- July: $6,222.41 / $6,110 — 101.84%
- August: $5,489.63 / $6,110 — 89.85%
- September: $5,972.24 / $6,110 — 97.75%
July is over its limit, so Jordan appears in the result. The query means:
Jordan has exhausted at least one budget.

It does not mean Jordan has spent 100% across all four budgets. The friendly response is misleading; a more accurate version would be:
Jordan Rivera has exceeded the limit for their July 2026 budget.