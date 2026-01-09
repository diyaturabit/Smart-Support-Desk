❓ Can users self-register? → NO

❓ Who creates users? → Admin only

❓ Roles → admin, staff

❓ Login method → email + password

❓ Auth type → JWT


# 🛠 Smart Support System

Smart Support System is a role-based support ticket management application built using Flask, MySQL, JWT authentication, Redis caching, and Streamlit frontend. The system allows admins to manage users and staff to manage customers and tickets securely.

---

## 🚀 Features

### 🔐 Authentication & Authorization
- Login using email and password
- JWT token-based authentication
- Role-based access control (Admin / Staff)
- Secure password hashing

### 👤 User Management (Admin Only)
- Create new users (admin or staff)
- Control system access through roles
- Track user login activity

### 👥 Customer Management
- Create, view, update, and delete customers
- Accessible to authenticated users

### 🎫 Ticket Management
- Create support tickets
- Update ticket details and status
- Delete tickets
- Filter tickets by status and priority

### 📊 Dashboard
- View ticket statistics:
  - Open tickets
  - High, Medium, Low priority tickets
- Dashboard data is cached using Redis for performance

### ⚡ Performance Optimization
- Redis caching used for dashboard APIs
- Faster Streamlit loading and reduced database calls

### 🖥 Frontend
- Streamlit-based UI
- Role-based navigation
- Admin-only pages visible only to admins

---

## 🧰 Tech Stack

- Backend: Flask (Python)
- Frontend: Streamlit
- Database: MySQL
- Authentication: JWT
- Caching: Redis
- Validation: Pydantic

---

## 📂 Project Structure

## 🔑 Roles & Permissions

| Feature | Admin | Staff |
|------|------|------|
Login | Yes | Yes
Create Users | Yes | No
Manage Customers | Yes | Yes
Manage Tickets | Yes | Yes
View Dashboard | Yes | Yes


Diya Bosamiya
Project: Smart Support System