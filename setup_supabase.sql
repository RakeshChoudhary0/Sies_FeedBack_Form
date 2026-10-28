-- =============================================================================
-- Syllabus Feedback System - Supabase / PostgreSQL Database Setup Script
-- Compatible with Supabase SQL Editor and standard PostgreSQL 14+
-- =============================================================================

-- 1. Drop existing tables and types if re-initializing (in dependency order)
DROP TABLE IF EXISTS feedback_answers CASCADE;
DROP TABLE IF EXISTS stakeholder_personal_info CASCADE;
DROP TABLE IF EXISTS syllabus_question CASCADE;
DROP TABLE IF EXISTS admin_user CASCADE;
DROP TABLE IF EXISTS feedback_session CASCADE;
DROP TABLE IF EXISTS stakeholders CASCADE;
DROP TABLE IF EXISTS system_settings CASCADE;

-- Create enum type safely
DO $$ BEGIN
    CREATE TYPE question_category AS ENUM ('DEMOGRAPHIC', 'SYLLABUS', 'SUGGESTION');
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

-- 2. Create Tables

-- Table: stakeholders
CREATE TABLE IF NOT EXISTS stakeholders (
    stakeholder_id SERIAL PRIMARY KEY,
    stakeholder_type VARCHAR(50) NOT NULL UNIQUE
);

-- Table: feedback_session
CREATE TABLE IF NOT EXISTS feedback_session (
    session_id SERIAL PRIMARY KEY,
    session_name VARCHAR(100) NOT NULL,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

-- Table: stakeholder_personal_info
CREATE TABLE IF NOT EXISTS stakeholder_personal_info (
    person_id SERIAL PRIMARY KEY,
    session_id INT NOT NULL REFERENCES feedback_session(session_id) ON DELETE CASCADE,
    stakeholder_id INT NOT NULL REFERENCES stakeholders(stakeholder_id) ON DELETE CASCADE,
    name VARCHAR(100) NOT NULL,
    association_name VARCHAR(100)
);

-- Table: syllabus_question
CREATE TABLE IF NOT EXISTS syllabus_question (
    id SERIAL PRIMARY KEY,
    text TEXT NOT NULL,
    stakeholder_type VARCHAR(50) NOT NULL,
    category question_category NOT NULL
);

-- Table: admin_user
CREATE TABLE IF NOT EXISTS admin_user (
    admin_id SERIAL PRIMARY KEY,
    username VARCHAR(50) NOT NULL UNIQUE,
    password VARCHAR(255) NOT NULL
);

-- Table: feedback_answers
CREATE TABLE IF NOT EXISTS feedback_answers (
    answer_id SERIAL PRIMARY KEY,
    person_id INT NOT NULL REFERENCES stakeholder_personal_info(person_id) ON DELETE CASCADE,
    question_id INT NOT NULL REFERENCES syllabus_question(id) ON DELETE CASCADE,
    answer_text TEXT NOT NULL
);

-- Table: system_settings
CREATE TABLE IF NOT EXISTS system_settings (
    id INT PRIMARY KEY,
    is_active BOOLEAN DEFAULT TRUE
);

-- 3. Performance Indexes
CREATE INDEX IF NOT EXISTS idx_answers_person_id ON feedback_answers(person_id);
CREATE INDEX IF NOT EXISTS idx_answers_question_id ON feedback_answers(question_id);
CREATE INDEX IF NOT EXISTS idx_questions_stakeholder_type ON syllabus_question(stakeholder_type);
CREATE INDEX IF NOT EXISTS idx_questions_category ON syllabus_question(category);
CREATE INDEX IF NOT EXISTS idx_personal_info_stakeholder ON stakeholder_personal_info(stakeholder_id);
CREATE INDEX IF NOT EXISTS idx_personal_info_session ON stakeholder_personal_info(session_id);

-- 4. Initial Seed Data

-- System settings & default session
INSERT INTO system_settings (id, is_active) VALUES (1, TRUE) ON CONFLICT (id) DO NOTHING;
INSERT INTO feedback_session (session_id, session_name) VALUES (1, 'Default Session') ON CONFLICT (session_id) DO NOTHING;

-- Stakeholder Types
INSERT INTO stakeholders (stakeholder_type) VALUES
('TEACHER'),
('STUDENT'),
('ALUMNI'),
('EMPLOYER'),
('OUTSIDE_TEACHER'),
('PARENT')
ON CONFLICT (stakeholder_type) DO NOTHING;

-- ================= TEACHER =================
INSERT INTO syllabus_question (text, stakeholder_type, category) VALUES
-- DEMOGRAPHIC
('Name', 'TEACHER', 'DEMOGRAPHIC'),
('Email ID (Enter SIES edu ID only)', 'TEACHER', 'DEMOGRAPHIC'),
('Course', 'TEACHER', 'DEMOGRAPHIC'),
('Class', 'TEACHER', 'DEMOGRAPHIC'),

-- SYLLABUS
('Relevance of Syllabus Content : How well does the syllabus align with industry trends, technological advancements, and current academic standards?', 'TEACHER', 'SYLLABUS'),
('Depth and Coverage : Does the syllabus provide a balanced mix of fundamental and advanced topics?', 'TEACHER', 'SYLLABUS'),
('Practical Application : To what extent does the syllabus integrate hands on learning and real-world problem-solving?', 'TEACHER', 'SYLLABUS'),
('Assessment Methods : How effectively do assessments align with learning outcomes?', 'TEACHER', 'SYLLABUS'),
('Teaching Pedagogies : How effective are the teaching methodologies?', 'TEACHER', 'SYLLABUS'),
('How would you rate the Overall Syllabus?', 'TEACHER', 'SYLLABUS'),

-- SUGGESTION
('Suggestions for improvement based on your teaching experience.', 'TEACHER', 'SUGGESTION');

-- ================= STUDENT =================
INSERT INTO syllabus_question (text, stakeholder_type, category) VALUES
-- DEMOGRAPHIC
('Student Name', 'STUDENT', 'DEMOGRAPHIC'),
('Roll Number / PRN', 'STUDENT', 'DEMOGRAPHIC'),
('Email ID (Enter SIES edu ID only)', 'STUDENT', 'DEMOGRAPHIC'),
('Program / Course', 'STUDENT', 'DEMOGRAPHIC'),
('Class', 'STUDENT', 'DEMOGRAPHIC'),
('Academic Year', 'STUDENT', 'DEMOGRAPHIC'),

-- SYLLABUS
('How well does the syllabus align with current industry trends?', 'STUDENT', 'SYLLABUS'),
('Does the syllabus provide a balanced mix of fundamental and advanced topics?', 'STUDENT', 'SYLLABUS'),
('How effective are the teaching methodologies?', 'STUDENT', 'SYLLABUS'),
('How well does the syllabus prepare you for employment or higher studies?', 'STUDENT', 'SYLLABUS'),

-- SUGGESTION
('Any other feedback or suggestions regarding curriculum or NEP implementation?', 'STUDENT', 'SUGGESTION');

-- ================= ALUMNI =================
INSERT INTO syllabus_question (text, stakeholder_type, category) VALUES
-- DEMOGRAPHIC
('Student Name', 'ALUMNI', 'DEMOGRAPHIC'),
('Email ID', 'ALUMNI', 'DEMOGRAPHIC'),
('Course', 'ALUMNI', 'DEMOGRAPHIC'),

-- SYLLABUS
('Relevance of syllabus content with industry trends and academic standards', 'ALUMNI', 'SYLLABUS'),
('Depth and coverage of syllabus topics', 'ALUMNI', 'SYLLABUS'),
('Practical application and real-world problem solving', 'ALUMNI', 'SYLLABUS'),
('Effectiveness of assessment methods', 'ALUMNI', 'SYLLABUS'),
('Effectiveness of teaching pedagogies', 'ALUMNI', 'SYLLABUS'),
('Overall satisfaction with the syllabus learned', 'ALUMNI', 'SYLLABUS'),

-- SUGGESTION
('Suggestions for improving syllabus, teaching methods, or learning experience', 'ALUMNI', 'SUGGESTION');

-- ================= EMPLOYER =================
INSERT INTO syllabus_question (text, stakeholder_type, category) VALUES
-- DEMOGRAPHIC
('Name of Employer', 'EMPLOYER', 'DEMOGRAPHIC'),
('Name of Institution / Organization', 'EMPLOYER', 'DEMOGRAPHIC'),
('Designation', 'EMPLOYER', 'DEMOGRAPHIC'),
('Email Address', 'EMPLOYER', 'DEMOGRAPHIC'),
('Stream from which students are employed', 'EMPLOYER', 'DEMOGRAPHIC'),

-- SYLLABUS
('Curriculum relevance for employability', 'EMPLOYER', 'SYLLABUS'),
('Curriculum effectiveness in developing innovative thinking', 'EMPLOYER', 'SYLLABUS'),
('Effectiveness of syllabus in developing skill-oriented human resources', 'EMPLOYER', 'SYLLABUS'),
('Need-based nature of the current syllabus as per industry requirements', 'EMPLOYER', 'SYLLABUS'),
('Effectiveness of curriculum in developing entrepreneurship skills', 'EMPLOYER', 'SYLLABUS'),
('Student sensitivity towards ethics, values, sustainability, and social issues', 'EMPLOYER', 'SYLLABUS'),
('Students are equipped with latest developments in their field', 'EMPLOYER', 'SYLLABUS'),

-- SUGGESTION
('Topics that should be included in the curriculum', 'EMPLOYER', 'SUGGESTION'),
('Opinion on implementation of NEP and Autonomy in the college', 'EMPLOYER', 'SUGGESTION');

-- ================= OUTSIDE COLLEGE TEACHER =================
INSERT INTO syllabus_question (text, stakeholder_type, category) VALUES
-- DEMOGRAPHIC
('Name of Respondent', 'OUTSIDE_TEACHER', 'DEMOGRAPHIC'),
('College of Respondent', 'OUTSIDE_TEACHER', 'DEMOGRAPHIC'),
('Subject Name', 'OUTSIDE_TEACHER', 'DEMOGRAPHIC'),
('Email', 'OUTSIDE_TEACHER', 'DEMOGRAPHIC'),
('Program Name', 'OUTSIDE_TEACHER', 'DEMOGRAPHIC'),
('Years / Semester taught', 'OUTSIDE_TEACHER', 'DEMOGRAPHIC'),

-- SYLLABUS
('Entrepreneurship skill development through course content', 'OUTSIDE_TEACHER', 'SYLLABUS'),
('Employability relevance of course content', 'OUTSIDE_TEACHER', 'SYLLABUS'),
('Contribution of course content to skill development', 'OUTSIDE_TEACHER', 'SYLLABUS'),
('Alignment of course content with recent trends and advancements', 'OUTSIDE_TEACHER', 'SYLLABUS');

-- ================= PARENTS =================
INSERT INTO syllabus_question (text, stakeholder_type, category) VALUES
-- DEMOGRAPHIC
('Name of Parent', 'PARENT', 'DEMOGRAPHIC'),
('Name of Ward', 'PARENT', 'DEMOGRAPHIC'),
('Wards Stream', 'PARENT', 'DEMOGRAPHIC'),

-- SYLLABUS
('Overall satisfaction with NEP implementation', 'PARENT', 'SYLLABUS'),
('Flexibility of curriculum for diverse subject exploration', 'PARENT', 'SYLLABUS'),
('Employability focus of the curriculum', 'PARENT', 'SYLLABUS'),
('Support for industry-relevant skill development', 'PARENT', 'SYLLABUS'),
('Inclusion of practical learning opportunities', 'PARENT', 'SYLLABUS'),
('Holistic development through co-curricular activities under NEP', 'PARENT', 'SYLLABUS'),
('Collaboration and teamwork opportunities in syllabus', 'PARENT', 'SYLLABUS'),
('Overall impact of NEP on educational quality', 'PARENT', 'SYLLABUS'),

-- SUGGESTION
('Suggestions for new topics to be included in the syllabus', 'PARENT', 'SUGGESTION'),
('Additional comments or suggestions regarding NEP implementation', 'PARENT', 'SUGGESTION');

-- 5. Supabase Row Level Security (RLS) Configuration
-- Direct PostgreSQL / SQLAlchemy connections bypass RLS automatically.
-- The following policies configure access if querying via Supabase Client / PostgREST APIs:

ALTER TABLE stakeholders ENABLE ROW LEVEL SECURITY;
ALTER TABLE feedback_session ENABLE ROW LEVEL SECURITY;
ALTER TABLE stakeholder_personal_info ENABLE ROW LEVEL SECURITY;
ALTER TABLE syllabus_question ENABLE ROW LEVEL SECURITY;
ALTER TABLE admin_user ENABLE ROW LEVEL SECURITY;
ALTER TABLE feedback_answers ENABLE ROW LEVEL SECURITY;
ALTER TABLE system_settings ENABLE ROW LEVEL SECURITY;

-- Public can read questions, stakeholders, and system settings
CREATE POLICY "Public read syllabus questions" ON syllabus_question FOR SELECT USING (true);
CREATE POLICY "Public read stakeholders" ON stakeholders FOR SELECT USING (true);
CREATE POLICY "Public read system settings" ON system_settings FOR SELECT USING (true);

-- Public can submit feedback
CREATE POLICY "Public insert feedback sessions" ON feedback_session FOR INSERT WITH CHECK (true);
CREATE POLICY "Public select feedback sessions" ON feedback_session FOR SELECT USING (true);
CREATE POLICY "Public insert stakeholder info" ON stakeholder_personal_info FOR INSERT WITH CHECK (true);
CREATE POLICY "Public insert feedback answers" ON feedback_answers FOR INSERT WITH CHECK (true);

-- Admin table is restricted to service_role by default (no public access)

