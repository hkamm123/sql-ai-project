import json
from openai import OpenAI
import os
import sqlite3
from time import time

print("Running db_bot.py!")

models = ["gpt-5.6-luna", "gpt-4o", "gpt-6-astra"]
chosen_model = models[0]

fdir = os.path.dirname(__file__)
def getPath(fname):
    return os.path.join(fdir, fname)

# SQLITE
sqliteDbPath = getPath("aidb.sqlite")
setupSqlPath = getPath("setup.sql")
setupSqlDataPath = getPath("setupData.sql")

# Erase previous db
if os.path.exists(sqliteDbPath):
    os.remove(sqliteDbPath)

# create new db
sqliteCon = sqlite3.connect(sqliteDbPath) 
sqliteCursor = sqliteCon.cursor()

# read in setup files
with (
        open(setupSqlPath) as setupSqlFile,
        open(setupSqlDataPath) as setupSqlDataFile
    ):

    setupSqlScript = setupSqlFile.read()
    setupSQlDataScript = setupSqlDataFile.read()

# execute setup files
sqliteCursor.executescript(setupSqlScript) # setup tables and keys
sqliteCursor.executescript(setupSQlDataScript) # setup tables and keys
sqliteCursor.execute("PRAGMA query_only = ON") # reject any generated SQL that would change the data

def runSql(query):
    result = sqliteCursor.execute(query).fetchall()
    columnNames = [column[0] for column in sqliteCursor.description]
    return columnNames, result

# show a few distinct values from each column, in the paper's "SelectCol" format
def getExampleColumnValues(cursor, valueCount = 3):
    tableNames = [row[0] for row in cursor.execute("SELECT name FROM sqlite_master WHERE type = 'table' ORDER BY rowid").fetchall()]
    examples = []
    for tableName in tableNames:
        columnNames = [row[1] for row in cursor.execute(f"PRAGMA table_info({tableName})").fetchall()]
        lines = [f"Columns in {tableName} and {valueCount} distinct examples in each column:"]
        for columnName in columnNames:
            values = cursor.execute(f"SELECT DISTINCT {columnName} FROM {tableName} LIMIT {valueCount}").fetchall()
            formatted = [f'"{value}"' if isinstance(value, str) else str(value) for (value,) in values]
            lines.append(f"{columnName}: " + ", ".join(formatted))
        examples.append("/*\n" + "\n".join(lines) + "\n*/")
    return "\n".join(examples)

exampleColumnValues = getExampleColumnValues(sqliteCursor)

# other databases whose question/SQL pairs are shown as demonstrations in the cross-domain strategy
crossDomainDatabases = [
    {
        "setupPath": getPath("crossDomain/dogshow_setup.sql"),
        "dataPath": getPath("crossDomain/dogshow_data.sql"),
        "examples": [
            ("Who doesn't have a way for us to text them?",
             "select p.person_id, p.name\nfrom person p\nleft join phone ph on p.person_id = ph.person_id and ph.can_recieve_sms = 1\nwhere ph.phone_id is null;"),
            ("Which dogs have more than one owner?",
             "select d.name, count(*) as owner_count\nfrom dog d\njoin person_dog pd on d.dog_id = pd.dog_id\ngroup by d.dog_id\nhaving owner_count > 1;"),
        ],
    },
    {
        "setupPath": getPath("crossDomain/library_setup.sql"),
        "dataPath": getPath("crossDomain/library_data.sql"),
        "examples": [
            ("Which books are checked out right now, and who has them?",
             "select b.title, m.name\nfrom loan l\njoin book b on l.book_id = b.book_id\njoin member m on l.member_id = m.member_id\nwhere l.return_date is null;"),
            ("How many books has each member borrowed in September 2026?",
             "select m.name, count(l.loan_id) as loan_count\nfrom member m\nleft join loan l on m.member_id = l.member_id\nand l.loan_date between '2026-09-01' and '2026-09-30'\ngroup by m.member_id;"),
        ],
    },
]

# each demonstration database gets its own schema, column values and question/SQL pairs
def getCrossDomainDemonstrations():
    demonstrations = []
    for database in crossDomainDatabases:
        with open(database["setupPath"]) as setupFile, open(database["dataPath"]) as dataFile:
            demoSetupScript = setupFile.read()
            demoDataScript = dataFile.read()
        demoConnection = sqlite3.connect(":memory:")
        demoCursor = demoConnection.cursor()
        demoCursor.executescript(demoSetupScript)
        demoCursor.executescript(demoDataScript)
        examples = "\n\n".join(f"Question: {question}\n{sql}" for question, sql in database["examples"])
        demonstrations.append(demoSetupScript + "\n" + getExampleColumnValues(demoCursor) + "\n\n" + examples)
        demoConnection.close()
    return "\n\n".join(demonstrations)

crossDomainDemonstrations = getCrossDomainDemonstrations()

# OPENAI
configPath = getPath("config.json")
print(configPath)
with open(configPath) as configFile:
    config = json.load(configFile)

openAiClient = OpenAI(api_key = config["openaiKey"])
openAiClient.models.list() # check if the key is valid (update in config.json)
# chosen_model = "gpt-5.6-luna"

def getChatGptResponse(content):
    stream = openAiClient.chat.completions.create(
        model=chosen_model,
        messages=[{"role": "user", "content": content}],
        stream=True,
    )

    responseList = []
    for chunk in stream:
        if chunk.choices[0].delta.content is not None:
            responseList.append(chunk.choices[0].delta.content)

    result = "".join(responseList)
    return result


# strategies
commonSqlOnlyRequest = """ Give me a sqlite select statement that answers the question.
Only respond with sqlite syntax. If there is an error do not explain it!"""

# question/SQL pairs for this database; keep them different from the test questions below
singleDomainExamples = [
    ("Who has logged the most expenses?",
     "select u.name, count(*) as expense_count\nfrom expense e\njoin user u on e.user_id = u.user_id\ngroup by u.user_id\norder by expense_count desc\nlimit 1;"),
    ("Which budgets does Casey Nguyen own?",
     "select b.name, b.start_date, b.end_date\nfrom budget b\njoin user u on b.owner_id = u.user_id\nwhere u.name = 'Casey Nguyen';"),
    ("What was the most expensive Costco trip?",
     "select e.name, e.amount, e.expense_date\nfrom expense e\nwhere e.name like '%costco%'\norder by e.amount desc\nlimit 1;"),
    ("How much was spent on eating out in July?",
     "select sum(e.amount)\nfrom expense e\njoin category c on e.category_id = c.category_id\nwhere c.name = 'Eating Out'\nand e.expense_date between '2026-07-01' and '2026-07-31';"),
]
singleDomainDemonstrations = "\n\n".join(f"Question: {question}\n{sql}" for question, sql in singleDomainExamples)

strategies = {
    "zero_shot": setupSqlScript + "\n" + exampleColumnValues + "\n" + commonSqlOnlyRequest,
    "single_domain_few_shot": (setupSqlScript + "\n" + exampleColumnValues + "\n\n" +
                   singleDomainDemonstrations + "\n\n" +
                   commonSqlOnlyRequest),
    "cross_domain_few_shot": (crossDomainDemonstrations + "\n\n" +
                   setupSqlScript + "\n" + exampleColumnValues + "\n" +
                   commonSqlOnlyRequest)
}

questions = [
    "who likes to shop at Costco?",
    "What percentage of Jordan Rivera's total money has been spent?",
    "Who has spent all of their money?",
    "Who doesn't have any money?",
    "who has the most money?"
]


# use the markdown for the sql syntax to find the SQL query
def sanitizeForJustSql(value):
    gptStartSqlMarker = "```"
    gptEndSqlMarker = "```"
    if gptStartSqlMarker in value:
        # Split at the first ``` and take everything after it
        value = value.split(gptStartSqlMarker, 1)[1]
        # Find the newline after the language identifier (sql, sqlite, etc.)
        newline_index = value.find("\n")
        if newline_index != -1:
            value = value[newline_index + 1:]
    if gptEndSqlMarker in value:
        # Split at the closing ``` and take everything before it
        value = value.split(gptEndSqlMarker, 1)[0]

    return value.strip()

for strategy in strategies:
    responses = {"strategy": strategy, "prompt_prefix": strategies[strategy]}
    questionResults = []
    print("########################################################################")
    print(f"Running strategy: {strategy}")
    for question in questions:

        print("~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~")
        print("Question:")
        print(question)
        error = "None"
        sqlSyntaxResponse = None
        queryRawResponse = None
        friendlyResponse = None
        try:
            getSqlFromQuestionEngineeredPrompt = strategies[strategy] + " " + question
            sqlSyntaxResponse = getChatGptResponse(getSqlFromQuestionEngineeredPrompt)
            sqlSyntaxResponse = sanitizeForJustSql(sqlSyntaxResponse)
            print("SQL Syntax Response:")
            print(sqlSyntaxResponse)
            columnNames, rows = runSql(sqlSyntaxResponse)
            queryRawResponse = str(rows)
            print("Query Raw Response:")
            print(queryRawResponse)

            # include the SQL and column names so GPT knows what the raw values mean
            friendlyResultsPrompt = (
                f"I asked the question \"{question}\".\n"
                f"This SQL was run against a household budgeting database (amounts are in dollars):\n{sqlSyntaxResponse}\n"
                f"Columns: {columnNames}\n"
                f"Rows: {queryRawResponse}\n"
                "Answer my question in one or two friendly sentences using only these results. "
                "If the results are empty or don't actually answer the question, say so instead of guessing. "
                "Please do not give any other suggestions or chatter."
            )
            friendlyResponse = getChatGptResponse(friendlyResultsPrompt)
            print("Friendly Response:")
            print(friendlyResponse)
        except Exception as err:
            error = str(err)
            print(err)

        questionResults.append({
            "question": question,
            "sql": sqlSyntaxResponse,
            "queryRawResponse": queryRawResponse,
            "friendlyResponse": friendlyResponse,
            "error": error
        })

    responses["questionResults"] = questionResults

    with open(getPath(f"response_{strategy}_{time()}.json"), "w") as outFile:
        json.dump(responses, outFile, indent = 2)


sqliteCursor.close()
sqliteCon.close()
print("Done!")
