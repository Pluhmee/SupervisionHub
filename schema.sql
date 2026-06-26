-- =============================================================
-- supervision_db — Full Schema DDL
-- Implements Chapter 3 specification exactly.
-- Clarifications applied: Issues 01-10
-- =============================================================

CREATE DATABASE IF NOT EXISTS supervision_db
    CHARACTER SET utf8mb4
    COLLATE utf8mb4_unicode_ci;

USE supervision_db;

-- ---------------------------------------------------------------
-- TABLE 1: users
-- ---------------------------------------------------------------
CREATE TABLE IF NOT EXISTS users (
    user_id      INT(11)       NOT NULL AUTO_INCREMENT,
    first_name   VARCHAR(50)   NOT NULL,
    last_name    VARCHAR(50)   NOT NULL,
    email        VARCHAR(100)  NOT NULL,
    matric_no    VARCHAR(20)   NULL,
    staff_id     VARCHAR(20)   NULL,
    department   VARCHAR(100)  NOT NULL,
    faculty      VARCHAR(100)  NOT NULL,
    password     VARCHAR(255)  NOT NULL,
    user_type    ENUM('student','supervisor','admin') NOT NULL,
    phone        VARCHAR(20)   NULL,
    status       ENUM('active','inactive') NOT NULL DEFAULT 'active',
    created_at   TIMESTAMP     DEFAULT CURRENT_TIMESTAMP,

    PRIMARY KEY (user_id),
    UNIQUE KEY uq_users_email     (email),
    UNIQUE KEY uq_users_matric_no (matric_no),
    UNIQUE KEY uq_users_staff_id  (staff_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;


-- ---------------------------------------------------------------
-- TABLE 2: projects
-- ---------------------------------------------------------------
CREATE TABLE IF NOT EXISTS projects (
    project_id          INT(11)      NOT NULL AUTO_INCREMENT,
    student_id          INT(11)      NOT NULL,
    supervisor_id       INT(11)      NULL,                       -- nullable: assigned post-creation
    project_title       VARCHAR(255) NOT NULL,
    project_description TEXT         NULL,
    category            VARCHAR(100) NULL,
    status              ENUM('draft','active','completed') NOT NULL DEFAULT 'draft',
    overall_progress    INT(3)       NOT NULL DEFAULT 0,
    created_at          TIMESTAMP    DEFAULT CURRENT_TIMESTAMP,
    updated_at          TIMESTAMP    DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    PRIMARY KEY (project_id),
    CONSTRAINT fk_projects_student
        FOREIGN KEY (student_id)    REFERENCES users(user_id) ON DELETE RESTRICT,
    CONSTRAINT fk_projects_supervisor
        FOREIGN KEY (supervisor_id) REFERENCES users(user_id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;


-- ---------------------------------------------------------------
-- TABLE 3: documents  (append-only versioning)
-- ---------------------------------------------------------------
CREATE TABLE IF NOT EXISTS documents (
    document_id     INT(11)      NOT NULL AUTO_INCREMENT,
    project_id      INT(11)      NOT NULL,
    uploaded_by     INT(11)      NOT NULL,
    document_name   VARCHAR(255) NOT NULL,
    document_path   VARCHAR(255) NOT NULL,
    document_type   VARCHAR(50)  NOT NULL,
    document_size   INT(11)      NOT NULL,
    version_number  INT(3)       NOT NULL DEFAULT 1,
    milestone_type  VARCHAR(100) NULL,
    upload_date     TIMESTAMP    DEFAULT CURRENT_TIMESTAMP,

    PRIMARY KEY (document_id),
    CONSTRAINT uq_project_version
        UNIQUE (project_id, version_number),               -- enforces append-only
    CONSTRAINT fk_documents_project
        FOREIGN KEY (project_id)  REFERENCES projects(project_id) ON DELETE CASCADE,
    CONSTRAINT fk_documents_uploader
        FOREIGN KEY (uploaded_by) REFERENCES users(user_id) ON DELETE RESTRICT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;


-- ---------------------------------------------------------------
-- TABLE 4: messages
-- ---------------------------------------------------------------
CREATE TABLE IF NOT EXISTS messages (
    message_id   INT(11)      NOT NULL AUTO_INCREMENT,
    sender_id    INT(11)      NOT NULL,
    receiver_id  INT(11)      NOT NULL,
    project_id   INT(11)      NULL,
    subject      VARCHAR(255) NULL,
    message_body TEXT         NOT NULL,
    is_read      BOOLEAN      NOT NULL DEFAULT FALSE,
    sent_at      TIMESTAMP    DEFAULT CURRENT_TIMESTAMP,

    PRIMARY KEY (message_id),
    CONSTRAINT fk_messages_sender
        FOREIGN KEY (sender_id)   REFERENCES users(user_id)    ON DELETE RESTRICT,
    CONSTRAINT fk_messages_receiver
        FOREIGN KEY (receiver_id) REFERENCES users(user_id)    ON DELETE RESTRICT,
    CONSTRAINT fk_messages_project
        FOREIGN KEY (project_id)  REFERENCES projects(project_id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;


-- ---------------------------------------------------------------
-- TABLE 5: milestones
-- ---------------------------------------------------------------
CREATE TABLE IF NOT EXISTS milestones (
    milestone_id          INT(11)      NOT NULL AUTO_INCREMENT,
    project_id            INT(11)      NOT NULL,
    milestone_name        VARCHAR(100) NOT NULL,
    milestone_description TEXT         NULL,
    deadline              DATE         NULL,
    status                ENUM('pending','submitted','approved','rejected') NOT NULL DEFAULT 'pending',
    submitted_date        TIMESTAMP    NULL,
    feedback              TEXT         NULL,
    created_at            TIMESTAMP    DEFAULT CURRENT_TIMESTAMP,

    PRIMARY KEY (milestone_id),
    CONSTRAINT fk_milestones_project
        FOREIGN KEY (project_id) REFERENCES projects(project_id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;


-- ---------------------------------------------------------------
-- TABLE 6: meetings  (created_at added per clarification #4)
-- ---------------------------------------------------------------
CREATE TABLE IF NOT EXISTS meetings (
    meeting_id    INT(11)      NOT NULL AUTO_INCREMENT,
    student_id    INT(11)      NOT NULL,
    supervisor_id INT(11)      NOT NULL,
    project_id    INT(11)      NOT NULL,
    meeting_date  DATE         NOT NULL,
    meeting_time  TIME         NOT NULL,
    location      VARCHAR(255) NULL,
    agenda        TEXT         NULL,
    notes         TEXT         NULL,
    status        ENUM('requested','confirmed','completed','cancelled') NOT NULL DEFAULT 'requested',
    created_at    TIMESTAMP    DEFAULT CURRENT_TIMESTAMP,

    PRIMARY KEY (meeting_id),
    CONSTRAINT fk_meetings_student
        FOREIGN KEY (student_id)    REFERENCES users(user_id)       ON DELETE RESTRICT,
    CONSTRAINT fk_meetings_supervisor
        FOREIGN KEY (supervisor_id) REFERENCES users(user_id)       ON DELETE RESTRICT,
    CONSTRAINT fk_meetings_project
        FOREIGN KEY (project_id)    REFERENCES projects(project_id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;


-- ---------------------------------------------------------------
-- TABLE 7: notifications
-- ---------------------------------------------------------------
CREATE TABLE IF NOT EXISTS notifications (
    notification_id   INT(11)      NOT NULL AUTO_INCREMENT,
    user_id           INT(11)      NOT NULL,
    notification_type VARCHAR(50)  NOT NULL,
    title             VARCHAR(255) NOT NULL,
    message           TEXT         NOT NULL,
    link              VARCHAR(255) NULL,
    is_read           BOOLEAN      NOT NULL DEFAULT FALSE,
    created_at        TIMESTAMP    DEFAULT CURRENT_TIMESTAMP,

    PRIMARY KEY (notification_id),
    CONSTRAINT fk_notifications_user
        FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;


-- =============================================================
-- DOCUMENT VERSION INSERT PROCEDURE  (clarification #6)
-- Usage: CALL insert_document_version(project_id, uploader_id,
--            doc_name, doc_path, doc_type, doc_size, milestone_type);
-- =============================================================
DELIMITER $$

CREATE PROCEDURE IF NOT EXISTS insert_document_version(
    IN  p_project_id    INT,
    IN  p_uploaded_by   INT,
    IN  p_document_name VARCHAR(255),
    IN  p_document_path VARCHAR(255),
    IN  p_document_type VARCHAR(50),
    IN  p_document_size INT,
    IN  p_milestone_type VARCHAR(100)
)
BEGIN
    DECLARE next_version INT;

    SELECT COALESCE(MAX(version_number), 0) + 1
    INTO   next_version
    FROM   documents
    WHERE  project_id = p_project_id;

    INSERT INTO documents
        (project_id, uploaded_by, document_name, document_path,
         document_type, document_size, version_number, milestone_type)
    VALUES
        (p_project_id, p_uploaded_by, p_document_name, p_document_path,
         p_document_type, p_document_size, next_version, p_milestone_type);
END$$

DELIMITER ;


-- =============================================================
-- PROGRESS RECALCULATION VIEW  (clarification #7)
-- =============================================================
CREATE OR REPLACE VIEW vw_project_progress AS
SELECT
    p.project_id,
    p.project_title,
    COUNT(m.milestone_id)                                              AS total_milestones,
    SUM(CASE WHEN m.status = 'approved' THEN 1 ELSE 0 END)            AS approved_milestones,
    CASE
        WHEN COUNT(m.milestone_id) = 0 THEN 0
        ELSE ROUND(
            SUM(CASE WHEN m.status = 'approved' THEN 1 ELSE 0 END) * 100.0
            / COUNT(m.milestone_id)
        )
    END                                                                AS calculated_progress
FROM   projects  p
LEFT   JOIN milestones m ON m.project_id = p.project_id
GROUP  BY p.project_id, p.project_title;
