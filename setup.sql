create table category (
    category_id integer primary key,
    name varchar(30) not null unique
);

create table expense (
    expense_id integer primary key,
    name varchar(100) not null,
    amount real not null,
    expense_date date not null,
    category_id integer not null,
    foreign key (category_id) references category (category_id)
);
