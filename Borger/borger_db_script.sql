DROP TABLE IF EXISTS BorgerUser;
DROP TABLE IF EXISTS Address;


CREATE TABLE BorgerUser(
Id INTEGER PRIMARY KEY AUTOINCREMENT,
UserId VARCHAR UNIQUE NOT NULL,
CreatedAt TIMESTAMP NOT NULL
);

CREATE TABLE Address(
Id INTEGER PRIMARY KEY AUTOINCREMENT,
BorgerUserId VARCHAR,
CreatedAt TIMESTAMP NOT NULL,
IsValid BIT NOT NULL,
FOREIGN KEY (BorgerUserId) REFERENCES BorgerUser(Id) ON DELETE CASCADE
);
