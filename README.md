Notes Management System

A production-level notes management application built using Streamlit and MySQL, designed to help users efficiently create, organize, and manage notes with advanced features like reminders, tagging, version control, and analytics.

Features:
 Notes Management (CRUD) – Create, read, update, and delete notes
 Tagging System – Organize notes using customizable tags
 Reminders – Schedule and track important tasks
 Event Management – Manage general and scheduled events
 Version Control – Maintain history and restore previous versions
 Soft Delete & Trash – Recover deleted notes safely
 Dashboard Analytics – View statistics and insights
 Location-Based Notes – Google Maps integration for location tracking

 
 System Architecture:

The system follows a modular 3-tier architecture:

Presentation Layer – Streamlit UI for user interaction
Application Layer – Python logic handling workflows and operations
Database Layer – MySQL for structured data storage

Tech Stack:
Frontend/UI: Streamlit
Backend: Python
Database: MySQL
Integration: Google Maps API


Project Structure:
Smart-Notes/
│── app.py          # Main Streamlit application (UI + routing)
│── db.py           # Database layer (CRUD + queries)
│── requirements.txt
│── README.md


Installation & Setup:
1)Clone the Repository
git clone https://github.com/your-username/smart-notes.git
cd smart-notes
2)Install Dependencies
pip install -r requirements.txt
3)Setup MySQL Database
CREATE DATABASE smart_notes_db;
USE smart_notes_db;
Tables will be automatically created when the app runs.
4)Configure Database Connection
Update credentials in db.py:
conn = mysql.connector.connect(
    host="localhost",
    user="root",
    password="your_password",
    database="smart_notes_db"
)
5)Run the Application
streamlit run app.py

Database Design:
The system uses a relational schema with the following tables:

notes – Stores note details
tags – Stores tag names
note_tags – Many-to-many mapping
reminders – Stores reminders
versions – Stores note history
events – Stores event details

Core Functionalities:

Modular database operations using db.py
Dynamic UI rendering using Streamlit
Efficient querying with filtering and search
Data recovery using soft delete mechanism
Version tracking for audit and rollback

Future Enhancements:

Multi-user authentication system
Cloud deployment (AWS/GCP)
AI-based note suggestions
Mobile application version
Advanced analytics dashboard

Use Cases:

Personal productivity management
Task and reminder tracking
Event planning and scheduling
Organized note-taking system

Conclusion:

The Smart Notes Management System demonstrates the practical implementation of DBMS concepts, including relational design, normalization, and modular architecture, combined with a modern web interface for enhanced usability.

👨‍💻 Author
Janani V R
Student | Developer | Tech Enthusiast
