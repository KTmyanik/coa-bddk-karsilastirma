-- Daha once 01_create_table.sql calistirildiysa ve unique index hatasi aliyorsaniz
-- once bunu calistirin, sonra 02_insert_data.sql

IF EXISTS (
    SELECT 1
    FROM sys.indexes
    WHERE name = N'UX_CoaLedger_Ledgercode'
      AND object_id = OBJECT_ID(N'dbo.CoaLedger')
)
BEGIN
    DROP INDEX UX_CoaLedger_Ledgercode ON dbo.CoaLedger;
END
GO

IF NOT EXISTS (
    SELECT 1
    FROM sys.indexes
    WHERE name = N'IX_CoaLedger_Ledgercode'
      AND object_id = OBJECT_ID(N'dbo.CoaLedger')
)
BEGIN
    CREATE INDEX IX_CoaLedger_Ledgercode ON dbo.CoaLedger (Ledgercode);
END
GO
