create table author (
    author_id integer primary key,
    name varchar(50) not null
);

create table book (
    book_id integer primary key,
    title varchar(100) not null,
    author_id integer not null,
    genre varchar(20),
    published_year integer,
    foreign key (author_id) references author (author_id)
);

create table member (
    member_id integer primary key,
    name varchar(50) not null,
    join_date date not null
);

-- return_date is null while the book is still checked out
create table loan (
    loan_id integer primary key,
    book_id integer not null,
    member_id integer not null,
    loan_date date not null,
    return_date date,
    foreign key (book_id) references book (book_id),
    foreign key (member_id) references member (member_id)
);
