-- COA tablosu olusturma
-- SSMS'te calistirin

IF OBJECT_ID(N'dbo.CoaLedger', N'U') IS NULL
BEGIN
    CREATE TABLE dbo.CoaLedger
    (
        Id           INT IDENTITY(1, 1) NOT NULL PRIMARY KEY,
        Ledgercode   NVARCHAR(20)       NOT NULL,
        Ledgername   NVARCHAR(500)      NOT NULL,
        LoadedAt     DATETIME2(0)       NOT NULL CONSTRAINT DF_CoaLedger_LoadedAt DEFAULT (SYSUTCDATETIME())
    );

    CREATE INDEX IX_CoaLedger_Ledgercode ON dbo.CoaLedger (Ledgercode);
END
GO
