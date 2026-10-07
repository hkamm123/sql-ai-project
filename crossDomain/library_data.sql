INSERT INTO author (author_id, name) VALUES
(1, 'Ursula K. Le Guin'),
(2, 'Octavia E. Butler'),
(3, 'Terry Pratchett'),
(4, 'Mary Shelley');

INSERT INTO book (book_id, title, author_id, genre, published_year) VALUES
(1, 'A Wizard of Earthsea', 1, 'Fantasy', 1968),
(2, 'The Left Hand of Darkness', 1, 'Science Fiction', 1969),
(3, 'Kindred', 2, 'Science Fiction', 1979),
(4, 'Parable of the Sower', 2, 'Science Fiction', 1993),
(5, 'Guards! Guards!', 3, 'Fantasy', 1989),
(6, 'Small Gods', 3, 'Fantasy', 1992),
(7, 'Frankenstein', 4, 'Horror', 1818);

INSERT INTO member (member_id, name, join_date) VALUES
(1, 'Avery Chen', '2024-01-15'),
(2, 'Riley Patel', '2024-06-02'),
(3, 'Quinn Okafor', '2025-03-20'),
(4, 'Drew Martinez', '2025-09-11');

INSERT INTO loan (loan_id, book_id, member_id, loan_date, return_date) VALUES
(1, 1, 1, '2026-08-01', '2026-08-15'),
(2, 3, 1, '2026-08-20', '2026-09-03'),
(3, 5, 2, '2026-09-01', NULL),
(4, 7, 3, '2026-09-05', '2026-09-19'),
(5, 2, 1, '2026-09-10', NULL),
(6, 6, 2, '2026-09-22', '2026-10-01'),
(7, 3, 3, '2026-10-02', NULL);
