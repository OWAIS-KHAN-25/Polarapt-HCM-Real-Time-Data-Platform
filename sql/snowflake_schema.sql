-- Snowflake destination for USAJOBS (reference schema; not yet deployed)
CREATE TABLE IF NOT EXISTS JOB_POSTINGS (
    POSITION_ID VARCHAR(255) PRIMARY KEY,
    TITLE VARCHAR(1000),
    ORGANIZATION VARCHAR(1000),
    URL VARCHAR(4000),
    SALARY_MIN FLOAT,
    SALARY_MAX FLOAT,
    LOADED_AT TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP()
);
-- Snowflake standard tables do not enforce primary-key uniqueness.
-- MERGE in the Glue job provides application-level upsert semantics.
