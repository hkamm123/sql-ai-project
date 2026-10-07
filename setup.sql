create table user (
    user_id integer primary key,
    name varchar(50) not null
);

-- A budget covers one period (usually a month) and is shared by its members
create table budget (
    budget_id integer primary key,
    name varchar(50) not null,
    owner_id integer not null,
    start_date date not null,
    end_date date not null,
    foreign key (owner_id) references user (user_id)
);

-- Each budget has its own categories; max_amount is the spending limit in dollars
create table category (
    category_id integer primary key,
    budget_id integer not null,
    name varchar(30) not null,
    max_amount real not null,
    unique (budget_id, name),
    foreign key (budget_id) references budget (budget_id)
);

-- amount is in dollars; user_id is the member who logged the expense
create table expense (
    expense_id integer primary key,
    name varchar(100) not null,
    amount real not null,
    expense_date date not null,
    category_id integer not null,
    user_id integer not null,
    foreign key (category_id) references category (category_id),
    foreign key (user_id) references user (user_id)
);
