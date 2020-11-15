DROP TABLE IF EXISTS BankUser;
DROP TABLE IF EXISTS Loan;
DROP TABLE IF EXISTS Deposit;
DROP TABLE IF EXISTS Account;


CREATE TABLE BankUser (
    Id INTEGER PRIMARY KEY AUTOINCREMENT,
    UserId VARCHAR NOT NULL UNIQUE,
    CreatedAt TIMESTAMP NOT NULL,
    ModifiedAt TIMESTAMP
);

CREATE TABLE Loan (
    Id INTEGER PRIMARY KEY AUTOINCREMENT,
    UserId VARCHAR NOT NULL UNIQUE,
    CreatedAt TIMESTAMP NOT NULL,
    ModifiedAt TIMESTAMP,
    Amount DECIMAL NOT NULL,
    FOREIGN KEY (UserId)
      REFERENCES BankUser (UserId)
      ON DELETE CASCADE
);

CREATE TABLE Deposit (
    Id INTEGER PRIMARY KEY AUTOINCREMENT,
    BankUserId INTEGER NOT NULL,
    CreatedAt TIMESTAMP NOT NULL,
    Amount DECIMAL NOT NULL,
    FOREIGN KEY (BankUserId)
      REFERENCES BankUser (Id)
      ON DELETE CASCADE
);

CREATE TABLE Account(
    Id INTEGER PRIMARY KEY AUTOINCREMENT,
    BankUserId INTEGER NOT NULL UNIQUE,
    AccountNo VARCHAR NOT NULL,
    IsStudent BOOLEAN NOT NULL,
    CreatedAt TIMESTAMP NOT NULL,
    ModifiedAt TIMESTAMP,
    InterestRate NUMBER NOT NULL,
    Amount DECIMAL NOT NULL,
    FOREIGN KEY (BankUserId)
      REFERENCES BankUser (Id)
      ON DELETE CASCADE
);