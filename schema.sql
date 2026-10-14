CREATE DATABASE IF NOT EXISTS baggage_db;
USE baggage_db;

CREATE TABLE users (
    user_id       INT AUTO_INCREMENT PRIMARY KEY,
    name          VARCHAR(100) NOT NULL,
    username      VARCHAR(50)  NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    role          VARCHAR(20)  NOT NULL DEFAULT 'staff'
);

CREATE TABLE baggage (
    baggage_id     INT AUTO_INCREMENT PRIMARY KEY,
    reference_no   VARCHAR(30)  NOT NULL UNIQUE,
    rfid_tag_id    VARCHAR(64)  NOT NULL UNIQUE,
    passenger_name VARCHAR(100) NOT NULL,
    flight_no      VARCHAR(20)  NOT NULL,
    current_status VARCHAR(20)  NOT NULL DEFAULT 'Checked in'
);

CREATE TABLE scan_event (
    scan_id    INT AUTO_INCREMENT PRIMARY KEY,
    baggage_id INT         NOT NULL,
    checkpoint VARCHAR(30) NOT NULL,
    status     VARCHAR(20) NOT NULL,
    timestamp  DATETIME    NOT NULL,
    FOREIGN KEY (baggage_id) REFERENCES baggage(baggage_id)
);

CREATE TABLE audit_log (
    audit_id  INT AUTO_INCREMENT PRIMARY KEY,
    user_id   INT         NULL,
    action    VARCHAR(40) NOT NULL,
    record_id VARCHAR(64) NULL,
    timestamp DATETIME    NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users(user_id)
);
