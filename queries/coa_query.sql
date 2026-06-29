-- Uygulamanin okudugu COA sorgusu
-- Bu dosyayi istediginiz gibi duzenleyin; uygulama her calistirmada buradan okur.
-- Sorgu en az su iki kolonu dondurmeli: Ledgercode, Ledgername

SELECT
    Ledgercode,
    Ledgername
FROM TDUTIL.dbo.CoaLedger
ORDER BY Ledgercode;
