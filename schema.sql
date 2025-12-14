-- ADK Session Service Schema for PostgreSQL
-- These tables are auto-created by DatabaseSessionService, but can be pre-created manually.

-- =============================================================================
-- APP STATES: Global state shared across ALL sessions for an application
-- =============================================================================
CREATE TABLE IF NOT EXISTS app_states (
    app_name             VARCHAR(255) NOT NULL PRIMARY KEY,
    state                JSONB NOT NULL DEFAULT '{}'::jsonb,
    update_time          TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- =============================================================================
-- USER STATES: State shared across sessions for a specific user
-- =============================================================================
CREATE TABLE IF NOT EXISTS user_states (
    app_name             VARCHAR(255) NOT NULL,
    user_id              VARCHAR(255) NOT NULL,
    state                JSONB NOT NULL DEFAULT '{}'::jsonb,
    update_time          TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (app_name, user_id)
);

-- =============================================================================
-- SESSIONS: Per-session state and metadata
-- =============================================================================
CREATE TABLE IF NOT EXISTS sessions (
    app_name             VARCHAR(255) NOT NULL,
    user_id              VARCHAR(255) NOT NULL,
    id                   VARCHAR(255) NOT NULL PRIMARY KEY,
    state                JSONB NOT NULL DEFAULT '{}'::jsonb,
    create_time          TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    update_time          TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Index for fast user-app lookups
CREATE INDEX IF NOT EXISTS idx_sessions_user_app ON sessions(user_id, app_name);

-- =============================================================================
-- EVENTS: Complete event history for each session
-- =============================================================================
CREATE TABLE IF NOT EXISTS events (
    id                   VARCHAR(255) NOT NULL PRIMARY KEY,
    app_name             VARCHAR(255) NOT NULL,
    user_id              VARCHAR(255) NOT NULL,
    session_id           VARCHAR(255) NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,
    invocation_id        VARCHAR(255) NOT NULL,
    author               VARCHAR(255) NOT NULL,
    actions              BYTEA NOT NULL,
    timestamp            TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    
    -- Content and metadata (nullable)
    content              JSONB,
    branch               VARCHAR(255),
    partial              BOOLEAN,
    turn_complete        BOOLEAN,
    interrupted          BOOLEAN,
    
    -- Error handling
    error_code           VARCHAR(255),
    error_message        VARCHAR(255),
    
    -- Tool execution
    long_running_tool_ids_json TEXT,
    
    -- Metadata objects
    grounding_metadata   JSONB,
    custom_metadata      JSONB,
    usage_metadata       JSONB,
    citation_metadata    JSONB,
    
    -- Transcription (for audio/voice)
    input_transcription  JSONB,
    output_transcription JSONB
);

-- Index for fast session event retrieval
CREATE INDEX IF NOT EXISTS idx_events_session ON events(session_id);
CREATE INDEX IF NOT EXISTS idx_events_invocation ON events(invocation_id);
