-- SQL Server destination for FX (reference schema; not yet deployed)
CREATE TABLE dbo.FxRates (
    api_timestamp DATETIME2(0) NOT NULL,
    currency CHAR(3) NOT NULL,
    rate DECIMAL(20, 8) NOT NULL,
    s3_key NVARCHAR(512) NOT NULL,
    loaded_at DATETIME2(0) NOT NULL DEFAULT SYSUTCDATETIME(),
    CONSTRAINT PK_FxRates PRIMARY KEY (api_timestamp, currency)
);
