CREATE DATABASE IF NOT EXISTS campus_complaints CHARACTER SET utf8mb4;
USE campus_complaints;

CREATE TABLE admins (
	admin_id INTEGER NOT NULL AUTO_INCREMENT, 
	name VARCHAR(100) NOT NULL, 
	email VARCHAR(150) NOT NULL, 
	password_hash VARCHAR(255) NOT NULL, 
	created_at DATETIME, 
	updated_at DATETIME, 
	PRIMARY KEY (admin_id), 
	UNIQUE (email)
);
CREATE TABLE departments (
	department_id INTEGER NOT NULL AUTO_INCREMENT, 
	department_name VARCHAR(100) NOT NULL, 
	description VARCHAR(255), 
	created_at DATETIME, 
	updated_at DATETIME, 
	PRIMARY KEY (department_id), 
	UNIQUE (department_name)
);
CREATE TABLE students (
	student_id INTEGER NOT NULL AUTO_INCREMENT, 
	name VARCHAR(100) NOT NULL, 
	email VARCHAR(150) NOT NULL, 
	password_hash VARCHAR(255) NOT NULL, 
	academic_department VARCHAR(100) NOT NULL, 
	year_of_study INTEGER NOT NULL, 
	created_at DATETIME, 
	updated_at DATETIME, 
	PRIMARY KEY (student_id), 
	UNIQUE (email)
);
CREATE TABLE complaints (
	complaint_id INTEGER NOT NULL AUTO_INCREMENT, 
	reference VARCHAR(20), 
	student_id INTEGER NOT NULL, 
	department_id INTEGER, 
	title VARCHAR(150) NOT NULL, 
	category VARCHAR(40) NOT NULL, 
	location VARCHAR(150) NOT NULL, 
	description TEXT NOT NULL, 
	status VARCHAR(20) NOT NULL, 
	priority VARCHAR(10) NOT NULL, 
	assigned_at DATETIME, 
	resolved_at DATETIME, 
	resolution_details TEXT, 
	created_at DATETIME, 
	updated_at DATETIME, 
	PRIMARY KEY (complaint_id), 
	UNIQUE (reference), 
	FOREIGN KEY(student_id) REFERENCES students (student_id) ON DELETE CASCADE, 
	FOREIGN KEY(department_id) REFERENCES departments (department_id) ON DELETE SET NULL
);
CREATE INDEX ix_complaints_category ON complaints (category);
CREATE INDEX ix_complaints_created_at ON complaints (created_at);
CREATE INDEX ix_complaints_department_id ON complaints (department_id);
CREATE INDEX ix_complaints_priority ON complaints (priority);
CREATE INDEX ix_complaints_status ON complaints (status);
CREATE INDEX ix_complaints_student_id ON complaints (student_id);
CREATE TABLE complaint_updates (
	update_id INTEGER NOT NULL AUTO_INCREMENT, 
	complaint_id INTEGER NOT NULL, 
	admin_id INTEGER NOT NULL, 
	old_status VARCHAR(20), 
	new_status VARCHAR(20), 
	old_department_id INTEGER, 
	new_department_id INTEGER, 
	remarks TEXT, 
	created_at DATETIME, 
	PRIMARY KEY (update_id), 
	FOREIGN KEY(complaint_id) REFERENCES complaints (complaint_id) ON DELETE CASCADE, 
	FOREIGN KEY(admin_id) REFERENCES admins (admin_id), 
	FOREIGN KEY(old_department_id) REFERENCES departments (department_id) ON DELETE SET NULL, 
	FOREIGN KEY(new_department_id) REFERENCES departments (department_id) ON DELETE SET NULL
);
CREATE INDEX ix_complaint_updates_complaint_id ON complaint_updates (complaint_id);

INSERT IGNORE INTO departments (department_name) VALUES ('IT Support'),('Electrical Maintenance'),('Civil Maintenance'),('Hostel Administration'),('Library Administration'),('Housekeeping'),('General Administration');
